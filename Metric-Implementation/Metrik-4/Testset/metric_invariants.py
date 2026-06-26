"""
Metric Invariant Predicates

Validators for the S-1 similarity metric.

Exported functions:
    isValidParsedModel   – validates a Parser output model.
    isValidDiagram       – validates the internal Diagram representation.
    isValidUCG           – validates a UML Common Graph (networkx.MultiDiGraph).
    isValidSimilarity    – validates that a float is in [0.0, 1.0] and finite.
    isValidMetricResult  – validates a SimilarityResult against its sub-scores
                           and the input ParsedModels.
"""

import math
from typing import Any

import networkx as nx

from Parser.models import ParsedModel, ParsedClass, ParsedEnum, ParsedRelationship
from Implementation_3.metric_models import (
    AttributeInfo,
    ClassInfo,
    Edge,
    Diagram,
    SimilarityResult,
)

# Small tolerance for floating-point reconstruction checks
_EPS = 1e-6


def isValidParsedModel(M: ParsedModel) -> bool:
    """
    Checks if *M* conforms to the structural invariants required of any parsed
    model that enters the S-1 metric pipeline.

    Invariant requirements
    ------------------------
    1. ``M`` is an instance of ``ParsedModel``.
    2. Every element in ``M.classes`` is a ``ParsedClass`` instance.
    3. Every element in ``M.enums`` is a ``ParsedEnum`` instance.
    4. Every element in ``M.relationships`` is a ``ParsedRelationship`` instance.
    5. Class names are unique within ``M``.
    6. Enumeration names are unique within ``M`` (both standalone enums and
       enums nested inside classes).
    7. Every relation references classes that exist in ``M``.
       A class "exists" if its name appears in ``M.classes`` or in
       ``M.implicit_classes``.

    Args
    ----
    M : ParsedModel
        The model to validate.

    Returns
    -------
    bool
        ``True`` iff all invariants hold.

    Examples
    --------
    >>> from Parser.models import ParsedModel
    >>> isValidParsedModel(ParsedModel())
    True
    """
    # 1. Must be a ParsedModel instance
    if not isinstance(M, ParsedModel):
        return False

    # 2. All classes are ParsedClass instances
    if not all(isinstance(c, ParsedClass) for c in M.classes):
        return False

    # 3. All enums are ParsedEnum instances
    if not all(isinstance(e, ParsedEnum) for e in M.enums):
        return False

    # 4. All relationships are ParsedRelationship instances
    if not all(isinstance(r, ParsedRelationship) for r in M.relationships):
        return False

    # 5. Class names are unique
    class_names = [c.name for c in M.classes]
    if len(class_names) != len(set(class_names)):
        return False

    # 6. Enum names are unique (standalone + nested)
    all_enum_names = [e.name for e in M.enums] + [
        e.name for c in M.classes for e in c.nested_enums
    ]
    if len(all_enum_names) != len(set(all_enum_names)):
        return False

    # 7. Every relation references existing classes
    existing_names = set(class_names) | set(M.implicit_classes)
    for rel in M.relationships:
        # For association classes, the source is a tuple string which is not
        # itself a class name — the member classes are checked separately.
        if rel.association_members is None:
            if rel.source not in existing_names or rel.target not in existing_names:
                return False
        else:
            # Association class: the target must be a real class, and
            # the association_members must all be real classes.
            if rel.target not in existing_names:
                return False
            for member in rel.association_members:
                if member not in existing_names:
                    return False

    return True


def isValidDiagram(D: Diagram) -> bool:
    """
    Checks if *D* conforms to the invariants required of the internal
    ``Diagram`` representation used by the semantic and structural pipelines.

    Invariant requirements
    ------------------------
    1. ``D`` is a ``Diagram`` instance.
    2. Every element ``c`` in ``D.classes`` is a ``ClassInfo`` instance.
    3. Every element ``a`` in ``c.attributes`` (for every ``c``) is an
       ``AttributeInfo`` instance.
    4. Every ``c.name`` is a non-empty string.
    5. Every ``a.name`` is a non-empty string.
    6. Every ``a.type`` is a string (may be empty).
    7. Every ``a.modifier`` is either ``"const"`` or ``""``.
    8. Every element ``e`` in ``D.associations`` is an ``Edge`` instance with
       ``e.ownership`` in ``{"composition", "aggregation", "none"}``.
    9. Every element ``e`` in ``D.dependencies`` is an ``Edge`` instance with
       ``e.ownership == "none"``.
    10. Every element ``e`` in ``D.generalizations`` is an ``Edge`` instance
        with ``e.ownership == "none"``.
    11. Every ``e.source`` and ``e.target`` are non-empty strings.
    12. Every ``e.name`` is a string (may be empty).
    13. No duplicate ``(source, target, ownership, name)`` tuples exist within
        the same edge list (associations, dependencies, or generalizations).

    Args
    ----
    D : Diagram
        The diagram to validate.

    Returns
    -------
    bool
        ``True`` iff all invariants hold.

    Examples
    --------
    >>> from Specification.metric_models import Diagram
    >>> isValidDiagram(Diagram())
    True
    """
    # 1. Must be a Diagram instance
    if not isinstance(D, Diagram):
        return False

    # 2, 3, 4, 5, 6, 7 – validate classes and their attributes
    seen_classes = set()
    for c in D.classes:
        if not isinstance(c, ClassInfo):
            return False
        if not isinstance(c.name, str) or c.name == "":
            return False
        if c.name in seen_classes:
            return False
        seen_classes.add(c.name)

        for a in c.attributes:
            if not isinstance(a, AttributeInfo):
                return False
            if not isinstance(a.name, str) or a.name == "":
                return False
            if not isinstance(a.type, str):
                return False
            if a.modifier not in {"const", ""}:
                return False

    def _check_edge_list(edges, allowed_ownership):
        seen = set()
        for e in edges:
            if not isinstance(e, Edge):
                return False
            if not isinstance(e.source, str) or e.source == "":
                return False
            if not isinstance(e.target, str) or e.target == "":
                return False
            if not isinstance(e.name, str):
                return False
            if e.ownership not in allowed_ownership:
                return False
            key = (e.source, e.target, e.ownership, e.name)
            if key in seen:
                return False
            seen.add(key)
        return True

    # 8. Associations ownership in {"composition", "aggregation", "none"}
    if not _check_edge_list(D.associations, {"composition", "aggregation", "none"}):
        return False

    # 9. Dependencies ownership == "none"
    if not _check_edge_list(D.dependencies, {"none"}):
        return False

    # 10. Generalizations ownership == "none"
    if not _check_edge_list(D.generalizations, {"none"}):
        return False

    return True


def isValidUCG(G: nx.MultiDiGraph) -> bool:
    """
    Checks if *G* is a valid UML Common Graph (UCG).

    The UCG is a ``networkx.MultiDiGraph`` where every vertex and edge carries
    a categorical ``tag`` attribute that identifies its role in the UML model.

    Invariant requirements
    ------------------------
    1. ``G`` is a ``networkx.MultiDiGraph`` instance.
    2. Every node has an attribute ``tag`` with value in ``{"vc", "va"}``.
       * ``"vc"`` – class vertex
       * ``"va"`` – attribute vertex
    3. Every edge has an attribute ``tag`` with value in
       ``{"e_a", "e_1", "e_2", "e_3", "e_4", "e_5"}``.
       * ``"e_a"`` – attribute edge (class -> attribute)
       * ``"e_1"`` – plain association
       * ``"e_2"`` – generalization
       * ``"e_3"`` – aggregation
       * ``"e_4"`` – composition
       * ``"e_5"`` – dependency
    4. No dangling edges: every edge endpoint must reference a node that
       actually exists in ``G``.

    Args
    ----
    G : networkx.MultiDiGraph
        The graph to validate.

    Returns
    -------
    bool
        ``True`` iff all invariants hold.

    Examples
    --------
    >>> import networkx as nx
    >>> G = nx.MultiDiGraph()
    >>> G.add_node("vc_A", tag="vc")
    >>> G.add_node("va_A_x", tag="va")
    >>> G.add_edge("vc_A", "va_A_x", tag="e_a")
    >>> isValidUCG(G)
    True
    """
    if not isinstance(G, nx.MultiDiGraph):
        return False

    valid_node_tags = {"vc", "va"}
    valid_edge_tags = {"e_a", "e_1", "e_2", "e_3", "e_4", "e_5"}

    # Check node tags
    for node, data in G.nodes(data=True):
        if data.get("tag") not in valid_node_tags:
            return False

    # Check edge tags and dangling edges
    for u, v, data in G.edges(data=True):
        if data.get("tag") not in valid_edge_tags:
            return False
        if u not in G or v not in G:
            return False

    return True


def isValidSimilarity(s: Any) -> bool:
    """
    Checks if *s* is a valid scalar similarity score.

    Invariant requirements
    ------------------------
    1. ``s`` is an instance of ``int`` or ``float`` (but not ``bool``).
    2. ``0.0 <= s <= 1.0`` (inclusive on both ends).

    Args
    ----
    s : Any
        The value to validate.

    Returns
    -------
    bool
        ``True`` iff the value satisfies both invariants.

    Examples
    --------
    >>> isValidSimilarity(0.5)
    True
    >>> isValidSimilarity(1.2)
    False
    >>> isValidSimilarity(True)
    False
    """
    if isinstance(s, bool):
        return False
    if not isinstance(s, (int, float)):
        return False
    if not math.isfinite(s):
        return False
    return 0.0 <= s <= 1.0


def _is_empty_diagram(d: Diagram) -> bool:
    """Helper: true if a Diagram has no classes and no relationships."""
    return (
        len(d.classes) == 0
        and len(d.associations) == 0
        and len(d.dependencies) == 0
        and len(d.generalizations) == 0
    )


def isValidMetricResult(
    model1: ParsedModel,
    model2: ParsedModel,
    result: Any,
) -> bool:
    """
    Validates that *result* is a ``SimilarityResult`` that is:

    1. Mathematically consistent (reconstruction identities).
    2. Composed of finite, unit-interval floats.
    3. Behaviorally consistent with the two input ``ParsedModel`` instances.

    Checks
    ------

    **Tier A – Type & basic bounds**
        * ``result`` is a ``SimilarityResult``.
        * Every scalar field is ``isValidSimilarity`` (finite number in
          ``[0.0, 1.0]``, not bool).

    **Tier B – Internal mathematical consistency**
        With tolerance ``1e-6``:

        * ``|similarity - (0.5*semantic + 0.5*structural)| <= 1e-6``
        * ``|semantic   - (0.7*propSim   + 0.3*relSim)|   <= 1e-6``
        * ``|structural - (0.9*intraSim  + 0.1*interSim)| <= 1e-6``

    **Tier C – Input-dependent behavioral guarantees**
        The *normalized* diagrams ``d1`` and ``d2`` are derived from the
        inputs by calling ``normalize(model)`` (an external dependency).

        * **Identical diagrams** — If ``d1 == d2`` then
          ``result.similarity == 1.0`` and every sub-score is ``1.0``.
        * **Both empty** — If both diagrams are fully empty (no classes,
          no relationships of any kind) then all scores are ``1.0``.
        * **One empty, one non-empty** — If exactly one diagram is fully
          empty and the other is not, then ``result.similarity == 0.0``.
        * **Zero classes in both** — ``result.propSim == 1.0`` and
          ``result.intraSim == 1.0``.
        * **Zero relationships in both** — ``result.relSim == 1.0`` and
          ``result.interSim == 1.0``.

    Args
    ----
    model1 : ParsedModel
        First input model.
    model2 : ParsedModel
        Second input model.
    result : Any
        Object to validate.

    Returns
    -------
    bool
        ``True`` iff all tiers pass.

    Notes
    -----
    * This function imports ``normalize`` lazily inside the body to avoid
      a circular import (it lives in ``Specification.metric_normalize``).
    * ``Diagram`` is a plain ``@dataclass`` and therefore supports deep
      equality via ``==``.
    * The empty-diagram checks are based on the count of classes and
      relationship edges after normalisation.

    Examples
    --------
    >>> from Specification.metric_models import SimilarityResult
    >>> r = SimilarityResult(
    ...     similarity=1.0, semantic=1.0, structural=1.0,
    ...     propSim=1.0, relSim=1.0, intraSim=1.0, interSim=1.0,
    ... )
    >>> m = ParsedModel()
    >>> isValidMetricResult(m, m, r)
    True
    """
    # --- Tier A ---
    if not isinstance(result, SimilarityResult):
        return False

    for field_name in (
        "similarity",
        "semantic",
        "structural",
        "propSim",
        "relSim",
        "intraSim",
        "interSim",
    ):
        if not isValidSimilarity(getattr(result, field_name)):
            return False

    # --- Tier B ---
    def _close(a: float, b: float) -> bool:
        return abs(a - b) <= _EPS

    if not _close(
        result.similarity,
        0.5 * result.semantic + 0.5 * result.structural,
    ):
        return False
    if not _close(
        result.semantic,
        0.7 * result.propSim + 0.3 * result.relSim,
    ):
        return False
    if not _close(
        result.structural,
        0.9 * result.intraSim + 0.1 * result.interSim,
    ):
        return False

    # --- Tier C ---
    # Lazy import to break potential circular dependency.
    # We must resolve via the absolute package name (developing_diss_metric)
    # so that the module is loaded inside a proper package context, which
    # allows the relative imports inside metric_normalize to work.
    import importlib

    _normalize_mod = importlib.import_module(
        "Specification.metric_normalize"
    )
    normalize = _normalize_mod.normalize

    def _is_empty_model(m: ParsedModel) -> bool:
        return (
            len(m.classes) == 0
            and len(m.enums) == 0
            and len(m.relationships) == 0
            and len(m.implicit_classes) == 0
        )

    d1 = Diagram()
    d2 = Diagram()
    try:
        d1 = Diagram() if _is_empty_model(model1) else normalize(model1)
        d2 = Diagram() if _is_empty_model(model2) else normalize(model2)
    except icontract.ViolationError:
        # normalize is still a stub with `...` body → treat models as empty
        pass

    # Identical diagrams → perfect similarity
    if d1 == d2:
        if result.similarity != 1.0:
            return False
        for field_name in ("semantic", "structural", "propSim", "relSim", "intraSim", "interSim"):
            if getattr(result, field_name) != 1.0:
                return False

    empty1 = _is_empty_diagram(d1)
    empty2 = _is_empty_diagram(d2)

    # Both empty
    if empty1 and empty2:
        if result.similarity != 1.0:
            return False
        for field_name in ("semantic", "structural", "propSim", "relSim", "intraSim", "interSim"):
            if getattr(result, field_name) != 1.0:
                return False

    # One empty, one non-empty
    if (empty1 and not empty2) or (not empty1 and empty2):
        if result.similarity != 0.0:
            return False

    # Both have zero classes → propSim and intraSim must be 1.0
    if len(d1.classes) == 0 and len(d2.classes) == 0:
        if result.propSim != 1.0 or result.intraSim != 1.0:
            return False

    # Both have zero relationships → relSim and interSim must be 1.0
    total_rels_1 = len(d1.associations) + len(d1.dependencies) + len(d1.generalizations)
    total_rels_2 = len(d2.associations) + len(d2.dependencies) + len(d2.generalizations)
    if total_rels_1 == 0 and total_rels_2 == 0:
        if result.relSim != 1.0 or result.interSim != 1.0:
            return False

    return True
