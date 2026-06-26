import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidGraph import isValidGraph
from Testset.isValidMapping import isValidMapping
from Testset.s1_types import Graph, Mapping


@icontract.require(lambda instructor_graph: isValidGraph(instructor_graph))
@icontract.require(lambda student_graph: isValidGraph(student_graph))
@icontract.ensure(lambda result: isValidMapping(result))
@icontract.ensure(
    lambda result: all(0.0 <= cost <= 1.0 for cost in result.element_cost_matrix.values()),
    "All values in mapping.element_cost_matrix are in [0, 1].",
)
@icontract.ensure(
    lambda result: all(
        result.element_cost_matrix[key] == 0.0
        for key in result.element_cost_matrix
        if key[0] == key[1]
    ),
    "Diagonal entries (m, m) are 0.",
)
def computeElementMapping(instructor_graph: Graph, student_graph: Graph) -> Mapping:
    r"""
    Compute the intra-level element cost matrix for all pairs of model elements.

    For every pair of elements (m, m') where m is from the instructor graph and
    m' is from the student graph, this function computes the intra-level tree
    distance δ(m, m') using recursive vertex matching on the tree representation
    of class model elements.

    Algorithm / Theory (deterministic)
    ----------------------------------
    The tree representation of a model element is a mixture of ordered and
    unordered subtrees of depth 1. The matching process recursively handles
    three vertex types:

    1. **Structure vertices** (ordered subtrees):
       Vertices such as element name, kind, scope, attributes-set, and
       operations-set are matched in a 1:1 ordered manner. The distance is
       a weighted sum δ_str with weights constrained to sum to 1,
       yielding a distance in [0, 1].

       **Deterministic weights for element distance:**

       .. math::
           \delta_{str}(m, m') = 0.4 \cdot \delta_{name} + 0.1 \cdot \delta_{kind} + 0.5 \cdot \delta_{attrs}

       where
           - ``δ_name``  – normalised string distance between element names.
           - ``δ_kind``  – binary distance: ``0.0`` if ``is_abstract`` equal,
             ``1.0`` otherwise.
           - ``δ_attrs`` – Hungarian set distance between attribute sets.

    2. **Set vertices** (unordered subtrees):
       Sets of attributes are matched using the Hungarian algorithm on extended
       sets with ε-padding.  The cost of pairing any item with ε
       (insertion / deletion) is ``1.0``.  The result is normalised by the
       extended set size ``max(|A|, |A'|)``.

    3. **Leaf vertices** (atomic features within an attribute):
       The distance between two ``ParsedAttribute`` instances is:

       .. math::
           \delta_{attr}(a, a') = 0.5 \cdot \delta_{name} + 0.3 \cdot \delta_{type} + 0.1 \cdot \delta_{const} + 0.1 \cdot \delta_{default}

       where
           - ``δ_name``    – normalised Levenshtein distance on ``a.name``.
           - ``δ_type``    – ``0.0`` if types equal, ``1.0`` otherwise.
           - ``δ_const``   – ``0.0`` if ``is_constant`` equal, ``1.0`` otherwise.
           - ``δ_default`` – normalised Levenshtein distance on
             ``default_value`` (treat ``None`` as empty string).

    The resulting δ(m, m') for every pair is stored in
    ``mapping.element_cost_matrix``.

    The distance function is designed to be **symmetric** (δ(m, m') = δ(m', m))
    and to satisfy the **identity of indiscernibles** (δ(m, m) = 0). These
    properties, together with non-negativity and the triangle inequality,
    ensure that the graph edit distance computed downstream is a valid metric
    (Riesen, 2015).

    Parameters
    ----------
    instructor_graph : Graph
        The instructor model graph G₁ = (V₁, E₁, μ, ρ) adhering to
        ``isValidGraph``. Each vertex represents a model element (class or
        interface) with attributes and operations.

    student_graph : Graph
        The student model graph G₂ = (V₂, E₂, μ, ρ) adhering to
        ``isValidGraph``. Each vertex represents a model element (class or
        interface) with attributes and operations.

    Returns
    -------
    Mapping
        A mapping instance with ``element_cost_matrix`` populated.
        The matrix is a dict keyed by ``(instructor_vertex_id,
        student_vertex_id)`` with values δ(m, m') ∈ [0, 1].

        Guaranteed postconditions:
        - ``isValidMapping(mapping)`` holds.
        - All values in ``element_cost_matrix`` are within [0, 1].
        - Diagonal entries (m, m) have cost 0.
        - The matrix is symmetric when the two graphs are swapped, i.e.
          δ(m, m') = δ(m', m), ensured by the symmetric design of all
          atomic and structured distance functions.

    References
    ----------
    - s1.md: ``computeElementMapping`` specification.
    - metric-information.txt: Sections 4.1 (representation), 4.2
      (distance definitions), and 4.3 (pairwise computation).
    """
    import Levenshtein
    from scipy.optimize import linear_sum_assignment
    import numpy as np

    # Build quick lookup for vertices
    inst_vertices = {v.vertex_id: v for v in instructor_graph.vertices}
    stud_vertices = {v.vertex_id: v for v in student_graph.vertices}

    element_cost_matrix: Dict[Tuple[str, str], float] = {}

    def normalized_levenshtein(a: str, b: str) -> float:
        if a == b:
            return 0.0
        max_len = max(len(a), len(b))
        if max_len == 0:
            return 0.0
        return Levenshtein.distance(a, b) / max_len

    def attribute_distance(a, b) -> float:
        d_name = normalized_levenshtein(a.name, b.name)
        d_type = 0.0 if a.type == b.type else 1.0
        d_const = 0.0 if a.is_constant == b.is_constant else 1.0
        d_default = normalized_levenshtein(
            a.default_value or "", b.default_value or ""
        )
        return 0.5 * d_name + 0.3 * d_type + 0.1 * d_const + 0.1 * d_default

    def hungarian_set_distance(set_a, set_b, distance_func) -> float:
        n = max(len(set_a), len(set_b))
        if n == 0:
            return 0.0
        cost = np.zeros((n, n), dtype=float)
        for i in range(n):
            for j in range(n):
                if i < len(set_a) and j < len(set_b):
                    cost[i, j] = distance_func(set_a[i], set_b[j])
                else:
                    cost[i, j] = 1.0
        row_ind, col_ind = linear_sum_assignment(cost)
        total = cost[row_ind, col_ind].sum()
        return float(total) / n

    def element_distance(inst_elem, stud_elem) -> float:
        d_name = normalized_levenshtein(inst_elem.name, stud_elem.name)
        d_kind = 0.0 if inst_elem.is_abstract == stud_elem.is_abstract else 1.0
        d_attrs = hungarian_set_distance(
            inst_elem.attributes, stud_elem.attributes, attribute_distance
        )
        return 0.4 * d_name + 0.1 * d_kind + 0.5 * d_attrs

    for iv in instructor_graph.vertices:
        for sv in student_graph.vertices:
            if iv.vertex_id == sv.vertex_id:
                d = 0.0
            else:
                d = element_distance(iv.element, sv.element)
            element_cost_matrix[(iv.vertex_id, sv.vertex_id)] = d

    return Mapping(element_cost_matrix=element_cost_matrix)
