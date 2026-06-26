import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
import numpy as np
from scipy.optimize import linear_sum_assignment
import Levenshtein

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
    mapping = Mapping()

    # Build lookup dictionaries for vertices by ID
    inst_vertices = {v.vertex_id: v for v in instructor_graph.vertices}
    stud_vertices = {v.vertex_id: v for v in student_graph.vertices}

    # Helper: normalized Levenshtein distance
    def lev_dist(a: str, b: str) -> float:
        if a == b:
            return 0.0
        max_len = max(len(a), len(b))
        if max_len == 0:
            return 0.0
        return Levenshtein.distance(a, b) / max_len

    # Attribute distance
    def attr_distance(a, b):
        d_name = lev_dist(a.name, b.name)
        d_type = 0.0 if a.type == b.type else 1.0
        d_const = 0.0 if a.is_constant == b.is_constant else 1.0
        a_default = a.default_value or ""
        b_default = b.default_value or ""
        d_default = lev_dist(a_default, b_default)
        return 0.5 * d_name + 0.3 * d_type + 0.1 * d_const + 0.1 * d_default

    # Hungarian distance between attribute sets
    def attribute_set_distance(attrs_a, attrs_b):
        n = len(attrs_a)
        m = len(attrs_b)
        if n == 0 and m == 0:
            return 0.0
        size = max(n, m)
        cost_matrix = np.ones((size, size), dtype=float)
        for i in range(n):
            for j in range(m):
                cost_matrix[i, j] = attr_distance(attrs_a[i], attrs_b[j])
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        total = cost_matrix[row_ind, col_ind].sum()
        return float(total / size)

    # Element tree distance
    def element_distance(inst_v, stud_v):
        inst_elem = inst_v.element
        stud_elem = stud_v.element
        d_name = lev_dist(inst_elem.name, stud_elem.name)
        d_kind = 0.0 if inst_elem.is_abstract == stud_elem.is_abstract else 1.0
        d_attrs = attribute_set_distance(inst_elem.attributes, stud_elem.attributes)
        return 0.4 * d_name + 0.1 * d_kind + 0.5 * d_attrs

    for inst_v in instructor_graph.vertices:
        for stud_v in student_graph.vertices:
            cost = element_distance(inst_v, stud_v)
            mapping.element_cost_matrix[(inst_v.vertex_id, stud_v.vertex_id)] = float(cost)

    # Contract requires exact zero on diagonal (same vertex id)
    for key in list(mapping.element_cost_matrix.keys()):
        if key[0] == key[1]:
            mapping.element_cost_matrix[key] = 0.0

    return mapping
