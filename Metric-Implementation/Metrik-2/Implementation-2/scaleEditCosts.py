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
    Scale edit costs by c_max to obtain a normalised distance in [0, 1].
    
    c_max = max(|V_instructor|, |V_student|) + |E_instructor| + |E_student|
    """
    c_max = max(len(instructor_graph.vertices), len(student_graph.vertices)) + len(instructor_graph.edges) + len(student_graph.edges)
    
    if c_max == 0:
        # Edge case: both graphs empty
        edit_informations.total_scaled_distance = 0.0
        for op in edit_informations.operations:
            op.scaled_cost = 0.0
        return edit_informations
    
    for op in edit_informations.operations:
        op.scaled_cost = op.raw_cost / c_max
    
    total_raw = sum(op.raw_cost for op in edit_informations.operations)
    edit_informations.total_scaled_distance = total_raw / c_max
    
    return edit_informations