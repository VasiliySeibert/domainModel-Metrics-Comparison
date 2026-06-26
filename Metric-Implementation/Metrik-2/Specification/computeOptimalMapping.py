import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidGraph import isValidGraph
from Testset.isValidMapping import isValidMapping
from Testset.s1_types import Graph, Mapping


@icontract.require(
    lambda instructor_graph, student_graph, element_mapping, relation_mapping: (
        isValidGraph(instructor_graph)
        and isValidGraph(student_graph)
        and isValidMapping(element_mapping)
        and isValidMapping(relation_mapping)
    )
)
@icontract.ensure(lambda result: isValidMapping(result))
@icontract.ensure(
    lambda result, instructor_graph: (
        len(result.vertex_mappings)
        + len(result.unmapped_instructor_vertices)
        == len(instructor_graph.vertices)
    )
)
@icontract.ensure(
    lambda result, student_graph: (
        len(result.vertex_mappings)
        + len(result.unmapped_student_vertices)
        == len(student_graph.vertices)
    )
)
@icontract.ensure(
    lambda result, instructor_graph: (
        len(result.edge_mappings)
        + len(result.unmapped_instructor_edges)
        == len(instructor_graph.edges)
    )
)
@icontract.ensure(
    lambda result, student_graph: (
        len(result.edge_mappings)
        + len(result.unmapped_student_edges)
        == len(student_graph.edges)
    )
)
def computeOptimalMapping(
    instructor_graph: Graph,
    student_graph: Graph,
    element_mapping: Mapping,
    relation_mapping: Mapping,
) -> Mapping:
    r"""
    Compute the optimal vertex and edge mapping between two attributed
    undirected multigraphs using the Hungarian algorithm on ε-padded cost
    matrices.

    This function bridges the **inter-level** distance computation step of the
    DISS metric pipeline.  It receives pairwise intra-level substitution costs
    (produced by :func:`computeElementMapping` and
    :func:`computeRelationMapping`) and searches for the least expensive
    complete edit path that transforms ``instructor_graph`` into
    ``student_graph``.

    Parameters
    ----------
    instructor_graph : Graph
        Valid attributed undirected multigraph representing the instructor
        model.  Must satisfy :func:`isValidGraph`.
    student_graph : Graph
        Valid attributed undirected multigraph representing the student model.
        Must satisfy :func:`isValidGraph`.
    element_mapping : Mapping
        Mapping object whose ``element_cost_matrix`` contains the intra-level
        tree distances ``δ(m, m')`` for every vertex pair.  Must satisfy
        :func:`isValidMapping`.
    relation_mapping : Mapping
        Mapping object whose ``relation_cost_matrix`` contains the intra-level
        tree distances ``δ(R_mn, R_m'n')`` for every edge pair.  Must satisfy
        :func:`isValidMapping`.

    Returns
    -------
    Mapping
        A new ``Mapping`` instance populated with:

        * ``vertex_mappings`` – list of :class:`VertexMappingEntry`
          describing every substituted vertex pair and its raw cost.
        * ``edge_mappings`` – list of :class:`EdgeMappingEntry` describing
          every substituted edge pair and its raw cost.
        * ``unmapped_instructor_vertices`` / ``unmapped_student_vertices``
          – vertex ids that are deleted or inserted (cost = 1 each).
        * ``unmapped_instructor_edges`` / ``unmapped_student_edges`` –
          edge ids that are deleted or inserted (cost = 1 each).
        * ``total_raw_cost`` – sum of all raw costs in the optimal edit path.

        The returned mapping is guaranteed to satisfy :func:`isValidMapping`
        and to account for **every** vertex and edge of both input graphs
        (completeness).

    Algorithm & Theory (deterministic)
    ----------------------------------
    The implementation **must** use the Hungarian algorithm (e.g.
    ``scipy.optimize.linear_sum_assignment`` or any exact bipartite-matching
    algorithm that yields the same globally optimal cost) on ε-padded cost
    matrices.

    **Edit path**
        A complete edit path ``λ(G₁, G₂)`` is a sequence of elementary
        operations that transforms all vertices and edges of the source graph
        ``G₁`` into the target graph ``G₂``.  The elementary set comprises
        vertex/edge *substitution*, *deletion* ``(· → ε)``, and *insertion*
        ``(ε → ·)``.

    **Vertex assignment (Hungarian algorithm)**
        Build a square cost matrix ``C`` of size ``N × N`` where
        ``N = max(|V₁|, |V₂|)``:

        * For ``i < |V₁|`` and ``j < |V₂|``:
          ``C[i,j] = element_cost_matrix[(u_i, u'_j)]`` (substitution cost).
        * For ``i < |V₁|`` and ``j ≥ |V₂|``: ``C[i,j] = 1.0`` (deletion cost).
        * For ``i ≥ |V₁|`` and ``j < |V₂|``: ``C[i,j] = 1.0`` (insertion cost).
        * For ``i ≥ |V₁|`` and ``j ≥ |V₂|``: ``C[i,j] = 0.0`` (dummy → dummy).

        The Hungarian algorithm returns a minimum-cost perfect matching.
        Entries where ``i < |V₁|`` and ``j < |V₂|`` are **vertex substitutions**;
        entries where ``i < |V₁|`` and ``j ≥ |V₂|`` are **deletions**;
        entries where ``i ≥ |V₁|`` and ``j < |V₂|`` are **insertions**.

    **Edge assignment (same algorithm)**
        Repeat the same procedure on ``relation_cost_matrix`` with
        ``N = max(|E₁|, |E₂|)`` and dummy cost ``1.0``.  The result yields
        edge substitutions, deletions, and insertions.

    **Why the Hungarian algorithm?**
        Because vertex and edge assignments are independent bipartite
        matching problems once the intra-level cost matrices are known,
        the Hungarian algorithm finds the *globally* optimal assignment in
        polynomial time.  This guarantees deterministic, reproducible output
        across implementations.  Beam-search or A* heuristics that prune the
        search space are **not allowed** because they can yield suboptimal
        and therefore non-deterministic results.

    **Cost properties**
        All substitution costs lie in ``[0, 1]`` (intra-level distances are
        normalised), whereas insertion and deletion incur unit cost (1).
        Consequently the maximum possible raw cost is bounded by

        .. math::
            c_{max} = \max(|V_1|, |V_2|) + |E_1| + |E_2|

        which is later used by :func:`scaleEditCosts` to scale the distance
        to the unit interval ``[0, 1]``.

    Preconditions (requires)
    ------------------------
    * ``isValidGraph(instructor_graph)``
    * ``isValidGraph(student_graph)``
    * ``isValidMapping(element_mapping)`` (cost matrix must be present)
    * ``isValidMapping(relation_mapping)`` (cost matrix must be present)

    Postconditions (ensures)
    --------------------------
    * ``isValidMapping(result)`` – structural and bijection constraints hold.
    * Completeness for instructor vertices:
      ``|vertex_mappings| + |unmapped_instructor_vertices| == |V_instructor|``
    * Completeness for student vertices:
      ``|vertex_mappings| + |unmapped_student_vertices| == |V_student|``
    * Completeness for instructor edges:
      ``|edge_mappings| + |unmapped_instructor_edges| == |E_instructor|``
    * Completeness for student edges:
      ``|edge_mappings| + |unmapped_student_edges| == |E_student|``

    These together guarantee that the returned mapping forms a **bijective
    optimal mapping** that covers every vertex and edge of both graphs.
    """
    ...
