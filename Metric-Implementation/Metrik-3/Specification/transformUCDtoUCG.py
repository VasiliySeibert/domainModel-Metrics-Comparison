import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidModel import isValidModel
from Testset.isValidUCG import isValidUCG
from Testset.s1_types import UCG, UCGVertex, UCGEdge


# Mapping from ParsedRelationship.relationship_type to UCG relationship edge tag.
# Direction convention (source -> target) is defined in the transformation spec.
_REL_TYPE_TO_TAG = {
    "association":           "e1",
    "directed":              "e1",   # directed association -> same tag as plain association
    "inheritance":           "e2",
    "aggregation":           "e3",
    "composition":           "e4",
    "dependency":            "e5",
    # "association_class" is not covered by the paper's UCG definition and is ignored.
}


@icontract.require(lambda model: isValidModel(model))
@icontract.ensure(lambda result: isValidUCG(result))
def transformUCDtoUCG(model) -> UCG:
    r"""
    Transform a parsed PlantUML model into a UML Class Graph (UCG).

    This is a deterministic, single-pass transformation that produces a UCG
    consisting only of classes (including enumerations), attributes, and
    relationships.  The parser in this project does not extract operations or
    parameters; therefore Rule 3 (operation/parameter vertices and edges) is
    intentionally omitted from the scope of this transformation.

    --------------------------------------------------------------------------
    Input schema  (guaranteed by ``isValidModel``)
    --------------------------------------------------------------------------
    ``model`` is a ``ParsedModel`` dataclass with the following fields:

      * ``classes`` — ``List[ParsedClass]``.  Each ``ParsedClass`` has:
        - ``name``            : ``str`` (non-empty, unique within the model)
        - ``is_abstract``     : ``bool`` (ignored by the transformation)
        - ``attributes``      : ``List[ParsedAttribute]``.  Each attribute has:
          · ``name``          : ``str`` (non-empty)
          · ``type``          : ``Optional[str]`` (may be ``None``)
          · ``default_value`` : ``Optional[str]`` (ignored)
          · ``is_constant``   : ``bool`` (ignored)
        - ``nested_enums``    : ``List[ParsedEnum]`` (ignored as separate objects;
          their names are treated as class names if the enum is referenced)

      * ``enums`` — ``List[ParsedEnum]`` (standalone enumerations).
        Each ``ParsedEnum`` has ``name`` (non-empty, unique).

      * ``relationships`` — ``List[ParsedRelationship]``.  Each relationship has:
        - ``source``          : ``str`` (class or enum name that exists in the model)
        - ``target``          : ``str`` (class or enum name that exists in the model)
        - ``relationship_type``: ``RelationshipType`` (see mapping table below)
        - ``source_cardinality``, ``target_cardinality`` : ignored
        - ``label``           : ignored
        - ``association_members`` : ignored

      * ``implicit_classes`` — ``List[str]`` (class names mentioned only in
        relationships, without an explicit ``class`` block).  Treated exactly
        like explicitly defined classes.

      * ``raw_source``, ``notes`` — ignored.

    --------------------------------------------------------------------------
    Vertex and edge identifiers  (deterministic)
    --------------------------------------------------------------------------
    Every vertex and edge receives a deterministic string ID so that two
    invocations with the same input produce the same graph.

    Vertex IDs:
      class vertex for class ``Person``        → ``cv:Person``
      attribute vertex ``name`` in ``Person``  → ``av:Person:name``

    Edge IDs:
      attribute edge from ``cv:Person`` to ``av:Person:name``
                                               → ``ae:Person:name``
      relationship edge ``Person`` → ``Address`` (association)
                                               → ``re:Person:Address:e1``

    If a class name contains characters that are not safe in an ID, the
    implementer may escape them; uniqueness within the returned graph is the
    only hard requirement.

    --------------------------------------------------------------------------
    Transformation rules  (ordered, deterministic)
    --------------------------------------------------------------------------
    The algorithm proceeds in four sequential phases.  Phases 1–2 create
    vertices; phases 3–4 create edges.

    **Phase 1 — Classes and enumerations → class vertices**
    For every name in ``model.all_class_names`` (which merges explicit classes,
    implicit classes, and standalone enums):
      * create one ``UCGVertex`` with:
        - ``vertex_type = "class"``
        - ``tag``         — omitted; class vertices have no tag field in ``UCGVertex``.
                          Their type is identified by ``vertex_type == "class"``.
        - ``label``       = the class/enum name
        - ``vertex_id``   = ``f"cv:{name}"``

    Enumerations are treated as ordinary classes because the paper does not
    define a dedicated vertex type for enumerations.

    **Phase 2 — Attributes → attribute vertices**
    For each ``ParsedClass`` in ``model.classes`` (implicit classes have no
    attributes):
      For each ``ParsedAttribute`` ``a`` in that class's ``attributes`` list:
        * create one ``UCGVertex`` with:
          - ``vertex_type = "attribute"``
          - ``label``       = ``a.name``
          - ``vertex_id``   = ``f"av:{class_name}:{a.name}"``

    **Phase 3 — Attribute edges**
    For each attribute vertex created in Phase 2:
      * create one ``UCGEdge`` with:
        - ``edge_type = "attribute"``
        - ``tag``           = ``"ea"`` (attribute edge tag per Table 1)
        - ``source_vertex_id`` = the class vertex ID of the owning class
        - ``target_vertex_id`` = the attribute vertex ID
        - ``edge_id``       = ``f"ae:{class_name}:{attr_name}"``

    The attribute data type (``a.type``) is **not stored** on the edge, because
    the structural-similarity algorithm only inspects edge tags and vertex
    labels, not types.  This follows the paper's statement that permissions
    and multiplicity are ignored.

    **Phase 4 — Relationships → relationship edges**
    For each ``ParsedRelationship`` ``r`` in ``model.relationships``:
      * look up ``tag = _REL_TYPE_TO_TAG[r.relationship_type.value]``.
        If ``r.relationship_type`` is ``ASSOCIATION_CLASS``, skip the
        relationship (no corresponding tag exists in the UCG definition).
      * create one ``UCGEdge`` with:
        - ``edge_type = "relationship"``
        - ``tag``           = the looked-up tag
        - ``source_vertex_id`` = class vertex ID of ``r.source``
        - ``target_vertex_id`` = class vertex ID of ``r.target``
        - ``edge_id``       = ``f"re:{source}:{target}:{tag}"``

    Direction convention (source → target):
    +---------------------------+----------+------------------------------------+
    | ParsedRelationship type   | Tag      | Direction rule                     |
    +---------------------------+----------+------------------------------------+
    | ASSOCIATION               | e1       | source = first class in line,      |
    |                           |          | target = second class in line      |
    | DIRECTED_ASSOCIATION      | e1       | source = tail of arrow,            |
    |                           |          | target = head of arrow             |
    | INHERITANCE               | e2       | source = parent class,             |
    |                           |          | target = child class               |
    | COMPOSITION               | e4       | source = composite / whole,        |
    |                           |          | target = part                      |
    | AGGREGATION               | e3       | source = whole,                    |
    |                           |          | target = part                      |
    | DEPENDENCY                | e5       | source = dependent,                |
    |                           |          | target = target                    |
    | ASSOCIATION_CLASS         | —        | ignored (not in UCG definition)    |
    +---------------------------+----------+------------------------------------+

    The parser already normalizes ``INHERITANCE``, ``COMPOSITION``,
    ``AGGREGATION``, and ``DIRECTED_ASSOCIATION`` so that the semantic
    "source" (parent, whole, tail) is in ``r.source`` and the semantic
    "target" (child, part, head) is in ``r.target``.  Therefore the
    transformation simply copies ``r.source`` and ``r.target`` into the edge
    endpoints without further swapping.

    --------------------------------------------------------------------------
    Output
    --------------------------------------------------------------------------
    A ``UCG`` instance with:
      * ``vertices`` — all class vertices (Phase 1) plus all attribute vertices
        (Phase 2).
      * ``edges``    — all attribute edges (Phase 3) plus all relationship edges
        (Phase 4).

    The returned graph satisfies ``isValidUCG``.

    --------------------------------------------------------------------------
    Preconditions (requires)
    --------------------------------------------------------------------------
    * ``isValidModel(model)`` — the parsed model satisfies structural invariants
      (unique class names, valid relationship references, etc.).

    Postconditions (ensures)
    --------------------------------------------------------------------------
    * ``isValidUCG(ucg)`` — the returned UCG satisfies all UCG invariants
      (typed vertices/edges, valid tags, unique IDs, correct endpoints,
      no orphaned non-class vertices, etc.).
    """
    ...
    return UCG()
