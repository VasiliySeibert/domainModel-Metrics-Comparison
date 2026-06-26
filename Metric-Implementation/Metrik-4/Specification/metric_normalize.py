"""
Diagram Normalisation

Converts a ``ParsedModel`` produced by the PlantUML parser into the internal
``Diagram`` representation used by the S-1 similarity metric.

The normaliser performs three principal transformations:

1. **Class normalisation** – ``ParsedClass`` objects are converted to
   ``ClassInfo`` with lower-cased types and constant modifiers. Standalone
   and nested ``ParsedEnum`` objects are flattened into ``ClassInfo``
   instances so they compete in the same similarity pool as regular classes.
   Implicit classes (mentioned in relationships but never explicitly defined)
   are materialised as empty ``ClassInfo`` stubs.
2. **Relationship decomposition** – each ``ParsedRelationship`` is broken into
   one or more ``Edge`` objects. ``ASSOCIATION_CLASS`` edges are 
   expanded into two plain association edges.
3. **Edge routing** – generated ``Edge`` objects are routed into one of three
   buckets: *associations*, *dependencies*, or *generalizations*.

Exported functions:
    normalize    – ParsedModel → Diagram (enums-as-classes, association-class
                   expansion, implicit-class materialisation).
    enumToClass  – ParsedEnum → ClassInfo.
    toEdges      – ParsedRelationship → list of (Edge, kind) tuples.
"""

import icontract
from typing import List, Tuple

from ..Parser.models import ParsedModel, ParsedEnum, ParsedRelationship, RelationshipType
from .metric_models import AttributeInfo, ClassInfo, Edge, Diagram
from ..Testset.metric_invariants import isValidParsedModel, isValidDiagram


# ----------------------------------------------------------------------
# Normalise model
# ----------------------------------------------------------------------
@icontract.require(lambda model: isValidParsedModel(model))
@icontract.ensure(lambda result: isValidDiagram(result))
def normalize(model: ParsedModel) -> Diagram:
    """
    Normalise a ``ParsedModel`` into the internal ``Diagram`` representation.

    This function is the mandatory first step of the metric pipeline.
    It guarantees that every downstream component (semantic similarity,
    structural similarity, UCG construction) receives a single, uniform
    data model free of parser-specific quirks (enums, association classes,
    implicit classes).

    Algorithm
    ---------
    1. **Classes**

       a. Iterate over ``model.classes``. For each ``ParsedClass``:

          * Build a list of ``AttributeInfo`` from its attributes:

                AttributeInfo(
                    name   = attr.name,
                    type   = (attr.type or "").lower(),
                    modifier = "const" if attr.is_constant else ""
                )

          * Wrap the class and its attributes in ``ClassInfo``.
          * Append the ``ClassInfo`` to the working ``classes`` list.
          * For each nested ``ParsedEnum`` inside the class, call
            ``enumToClass`` and append the result.

       b. Iterate over standalone ``model.enums``. For each ``ParsedEnum``,
          call ``enumToClass`` and append the result.

       c. Iterate over ``model.implicit_classes``. For each implicit class
          name, append ``ClassInfo(name, is_abstract=False, attributes=[])``.

    2. **Relationships**

       a. Create three empty buckets: ``associations``, ``dependencies``,
          ``generalizations``.

       b. Iterate over ``model.relationships``. For each
          ``ParsedRelationship rel``:

          * Call ``toEdges(rel)`` to obtain a list of *(Edge, kind)* tuples.
          * Route each ``Edge`` into the correct bucket based on ``kind``:

            + ``kind == "association"``    → ``associations.append(edge)``
            + ``kind == "dependency"``     → ``dependencies.append(edge)``
            + ``kind == "generalization"`` → ``generalizations.append(edge)``

          * ``ASSOCIATION_CLASS`` relationships produce two plain association
            edges pointing from each member to the association-class target.

    3. **Return** ``Diagram(classes, associations, dependencies, generalizations)``.

    Args
    ----
    model : ParsedModel
        Parser output representing a PlantUML class diagram. Must satisfy
        ``isValidParsedModel(model)`` (enforced by the ``@require`` contract).

    Returns
    -------
    Diagram
        A fully normalised diagram in which enums are classes, association
        classes are expanded, implicit classes are materialised, and every
        relationship edge is typed and routed.

    Raises
    ------
    icontract.ViolationError
        If *model* fails ``isValidParsedModel`` (pre-condition) or the
        constructed diagram fails ``isValidDiagram`` (post-condition).

    Notes
    -----
    * **Type lower-casing** – Attribute types are normalised to lower case so
      that ``String`` and ``string`` are treated identically during similarity.
    * **Enums as classes** – A ``ParsedEnum`` named *Status* with values
      ``[Active, Inactive]`` becomes a ``ClassInfo`` with two attributes
      ``(Active, "enum_value", "const")`` and ``(Inactive, "enum_value", "const")``.
      This allows the enum to participate in the same bipartite matching pool
      as regular classes.
    * **Association-class expansion** – The parser emits a single
      ``ASSOCIATION_CLASS`` relationship with ``association_members = (x, y)``
      and ``target = z``. The normaliser explodes this into two ``Edge``
      objects: ``(x → z)`` and ``(y → z)``, both with ``ownership="none"``
      and ``kind="association"``.
    * **Implicit classes** – PlantUML allows classes to be mentioned only
      inside relationship arrows (e.g. ``Person -- Address`` without a
      ``class Address`` block). The parser collects these names in
      ``implicit_classes``. The normaliser materialises each one as an
      empty ``ClassInfo`` so that structural similarity has a vertex to
      anchor on.

    Examples
    --------
    >>> from Parser.models import ParsedModel, ParsedClass, ParsedAttribute
    >>> model = ParsedModel(
    ...     classes=[
    ...         ParsedClass(name="Person", attributes=[
    ...             ParsedAttribute(name="name", type="String")
    ...         ])
    ...     ]
    ... )
    >>> diagram = normalize(model)
    >>> diagram.classes[0].name
    'Person'
    >>> diagram.classes[0].attributes[0].type
    'string'

    See Also
    --------
    enumToClass, toEdges, isValidParsedModel, isValidDiagram
    """
    ...


# ----------------------------------------------------------------------
# Enum helper
# ----------------------------------------------------------------------
def enumToClass(enum: ParsedEnum) -> ClassInfo:
    """
    Convert a ``ParsedEnum`` into a ``ClassInfo`` so that enumerations
    participate fully in semantic and structural similarity.

    The conversion is straightforward: every enum value becomes an
    ``AttributeInfo`` with ``type="enum_value"`` and ``modifier="const"``.
    The resulting ``ClassInfo`` is never abstract and carries the original
    enum name.

    Algorithm
    ---------
    1. For each value ``v`` in ``enum.values``:

       Create ``AttributeInfo(name=v, type="enum_value", modifier="const")``.

    2. Return ``ClassInfo(name=enum.name, is_abstract=False, attributes=attrs)``.

    Args
    ----
    enum : ParsedEnum
        The parsed enumeration (standalone or nested). Must expose
        ``name`` (str) and ``values`` (list of str).

    Returns
    -------
    ClassInfo
        A class-like representation of the enumeration.

    Raises
    ------
    AttributeError
        If *enum* does not have ``name`` or ``values`` attributes.

    Notes
    -----
    * The ``type="enum_value"`` tag allows downstream similarity functions
      (e.g. ``daSim``) to distinguish enum constants from regular attributes,
      although the current pipeline does not assign a special penalty.
    * Because the returned ``ClassInfo`` is not abstract, it will be treated
      exactly like any other concrete class during ``propSim`` matching.

    Examples
    --------
    >>> from Parser.models import ParsedEnum
    >>> enum = ParsedEnum(name="Status", values=["Active", "Inactive"])
    >>> cls = enumToClass(enum)
    >>> cls.name
    'Status'
    >>> [(a.name, a.type, a.modifier) for a in cls.attributes]
    [('Active', 'enum_value', 'const'), ('Inactive', 'enum_value', 'const')]

    See Also
    --------
    normalize, AttributeInfo, ClassInfo
    """
    ...


# ----------------------------------------------------------------------
# Edge decomposition
# ----------------------------------------------------------------------
def toEdges(rel: ParsedRelationship) -> List[Tuple[Edge, str]]:
    """
    Decompose a single ``ParsedRelationship`` into one or more ``(Edge, kind)``
    tuples.

    The parser uses a single ``ParsedRelationship`` object for every arrow
    in the PlantUML source. This function maps each arrow to the normalised
    ``Edge`` internal model and tags it with a high-level *kind* so that
    ``normalize`` can route it into the correct bucket.

    Mapping table
    -------------
    The mapping follows the decomposition rules defined in the S-1
    specification. Each row shows the parser ``RelationshipType``,
    the resulting ``Edge`` ``ownership`` field, and the ``kind`` string.

    +------------------------------+------------------+--------------+
    | RelationshipType             | ownership        | kind         |
    +==============================+==================+==============+
    | INHERITANCE                  | "none"           | generalization |
    +------------------------------+------------------+--------------+
    | DEPENDENCY                   | "none"           | dependency   |
    +------------------------------+------------------+--------------+
    | COMPOSITION                  | "composition"    | association  |
    +------------------------------+------------------+--------------+
    | AGGREGATION                  | "aggregation"    | association  |
    +------------------------------+------------------+--------------+
    | ASSOCIATION                  | "none"           | association  |
    +------------------------------+------------------+--------------+
    | DIRECTED_ASSOCIATION         | "none"           | association  |
    +------------------------------+------------------+--------------+
    | ASSOCIATION_CLASS (x, y) → z | "none" (×2)      | association  |
    +------------------------------+------------------+--------------+

    For ``ASSOCIATION_CLASS`` the function produces *two* tuples:

        ``(Edge(x, z, label, "none"), "association")``
        ``(Edge(y, z, label, "none"), "association")``

    Unrecognised relationship types (future extensions) return an empty list.

    Args
    ----
    rel : ParsedRelationship
        A single relationship parsed from PlantUML. Must expose
        ``source``, ``target``, ``relationship_type`` (a ``RelationshipType``
        enum member), ``label`` (Optional[str]), and optionally
        ``association_members`` (tuple of two class names).

    Returns
    -------
    List[Tuple[Edge, str]]
        Zero or more ``(Edge, kind)`` pairs. ``kind`` is always one of
        ``{"association", "dependency", "generalization"}``.

    Raises
    ------
    AttributeError
        If *rel* lacks any of the required attributes above.

    Notes
    -----
    * **Ownership translation** – The PlantUML parser distinguishes
      composition (``*--``) and aggregation (``o--``) by relationship type,
      not by an ownership field. This function translates the type into the
      ``ownership`` string used by the ``Edge`` dataclass.
    * **Label handling** – If ``rel.label`` is ``None``, the resulting
      ``Edge.name`` is empty (``""``).
    * **Association-class expansion** – The parser stores the two classes
      being associated in ``rel.association_members`` and the association
      class itself in ``rel.target``. The expansion is performed here so
      that downstream components never see ``ASSOCIATION_CLASS`` edges.

    Examples
    --------
    >>> from Parser.models import ParsedRelationship, RelationshipType
    >>> rel = ParsedRelationship(
    ...     source="Car", target="Wheel",
    ...     relationship_type=RelationshipType.COMPOSITION
    ... )
    >>> edges = toEdges(rel)
    >>> len(edges)
    1
    >>> edges[0][0].ownership
    'composition'
    >>> edges[0][1]
    'association'

    See Also
    --------
    normalize, Edge, RelationshipType
    """
    ...
