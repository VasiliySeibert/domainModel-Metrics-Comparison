import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidEditInformations import isValidEditInformations
from Testset.isValidGraph import isValidGraph
from Testset.s1_types import EditInformations, Graph


@icontract.require(
    lambda edit_informations, instructor_graph, student_graph: isValidEditInformations(
        edit_informations
    )
)
@icontract.require(
    lambda edit_informations, instructor_graph, student_graph: isValidGraph(
        instructor_graph
    )
)
@icontract.require(
    lambda edit_informations, instructor_graph, student_graph: isValidGraph(
        student_graph
    )
)
@icontract.ensure(
    lambda result, edit_informations, instructor_graph, student_graph: isValidEditInformations(
        result
    )
)
@icontract.ensure(
    lambda result, edit_informations, instructor_graph, student_graph: 0.0
    <= result.total_scaled_distance
    <= 1.0
)
def scaleEditCosts(
    edit_informations: EditInformations,
    instructor_graph: Graph,
    student_graph: Graph,
) -> EditInformations:
    """
    ```
    edit_informations = scaleEditCosts(edit_informations, instructor_graph, student_graph):
        c_max = max(|V_instructor|, |V_student|) + |E_instructor| + |E_student|
        for each op in edit_informations.operations:
            op.scaled_cost = op.raw_cost / c_max
        total_raw = sum(op.raw_cost for op in edit_informations.operations)
        edit_informations.total_scaled_distance = total_raw / c_max
        return edit_informations

        requires:
            isValidEditInformations(edit_informations),
            isValidGraph(instructor_graph),
            isValidGraph(student_graph)
        ensures:
            isValidEditInformations(edit_informations),
            edit_informations.total_scaled_distance ∈ [0, 1]

    Input:  A valid edit_informations instance and the two original graphs.
    Output: The same edit_informations instance with scaled_cost fields populated
            and total_scaled_distance computed.
    ```

    Theory & Algorithm
    ------------------
    The raw graph-edit distance computed by the preceding GED pipeline stages
    depends on the absolute sizes of the compared class models.  To obtain a
    size-independent dissimilarity measure in the unit interval [0, 1], each
    raw cost is divided by the theoretical maximum cost ``c_max``
    (Cech, 2019, Eq. 19):

        c_max(G_inst, G_stud) = max(|V_inst|, |V_stud|) + |E_inst| + |E_stud|

    where
        |V| – number of vertices (model elements: classes / interfaces)
        |E| – number of edges (subsets of relations between element pairs)

    This bound reflects the most expensive complete edit path: every vertex of
    the larger graph can be substituted (cost ≤ 1) and every edge of both graphs
    can be deleted or inserted (cost 1 per edge).  Consequently the sum of all
    raw costs never exceeds ``c_max``.

    Scaling is performed in two steps:

        1. Per-operation scaling:
           for each ``op`` in ``edit_informations.operations``:
               op.scaled_cost = op.raw_cost / c_max

        2. Overall distance scaling:
           total_raw = Σ op.raw_cost
           edit_informations.total_scaled_distance = total_raw / c_max

    The scaled overall distance corresponds to the normalised graph edit
    distance :math:`\\bar{\\delta}(G, G')` (Cech, 2019, Eq. 20).  Because all
    raw costs are non-negative and ``c_max > 0`` for any non-empty graph
    pair, every ``scaled_cost`` and ``total_scaled_distance`` is guaranteed to
    lie in the closed interval [0, 1].

    The function mutates the supplied ``EditInformations`` instance in-place
    and returns the same object.

    Invariants enforced by the contract
    -----------------------------------
    Pre-conditions (requires):
        • ``edit_informations`` satisfies ``isValidEditInformations`` – the edit
          path is complete, ``raw_cost`` values are bounded, and every
          ``scaled_cost`` is initialised inside [0, 1].
        • ``instructor_graph`` satisfies ``isValidGraph`` – a well-formed
          attributed undirected multigraph representing the reference model.
        • ``student_graph`` satisfies ``isValidGraph`` – a well-formed
          attributed undirected multigraph representing the learner model.

    Post-conditions (ensures):
        • The returned ``EditInformations`` still satisfies
          ``isValidEditInformations``; in particular every operation's
          ``scaled_cost`` remains in [0, 1] and ``total_raw`` is non-negative.
        • ``edit_informations.total_scaled_distance`` is in the closed
          interval [0, 1].
    """
    c_max = max(len(instructor_graph.vertices), len(student_graph.vertices)) + len(
        instructor_graph.edges
    ) + len(student_graph.edges)
    if c_max == 0:
        c_max = 1  # avoid division by zero
    for op in edit_informations.operations:
        op.scaled_cost = op.raw_cost / c_max
    total_raw = sum(op.raw_cost for op in edit_informations.operations)
    edit_informations.total_scaled_distance = total_raw / c_max
    return edit_informations
