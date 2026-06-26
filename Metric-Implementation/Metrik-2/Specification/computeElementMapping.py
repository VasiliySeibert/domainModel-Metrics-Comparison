import sys
from pathlib import Path

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
    ...
