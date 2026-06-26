import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidModel import isValidModel
from Testset.isValidEditInformations import isValidEditInformations
from Testset.s1_types import EditInformations

from createGraph import createGraph
from computeElementMapping import computeElementMapping
from computeRelationMapping import computeRelationMapping
from computeOptimalMapping import computeOptimalMapping
from extractVertexEditInformations import extractVertexEditInformations
from extractEdgeEditInformations import extractEdgeEditInformations
from aggregateEditInformations import aggregateEditInformations
from scaleEditCosts import scaleEditCosts


@icontract.require(lambda instructor_model, student_model: (
    isValidModel(instructor_model) and isValidModel(student_model)
))
@icontract.ensure(lambda result: isValidEditInformations(result))
def metric(instructor_model, student_model) -> EditInformations:
    instructor_graph = createGraph(instructor_model)
    student_graph = createGraph(student_model)

    element_mapping = computeElementMapping(instructor_graph, student_graph)
    relation_mapping = computeRelationMapping(instructor_graph, student_graph)
    optimal_mapping = computeOptimalMapping(
        instructor_graph, student_graph, element_mapping, relation_mapping
    )
    vertex_edit_informations = extractVertexEditInformations(optimal_mapping)
    edge_edit_informations = extractEdgeEditInformations(optimal_mapping)
    edit_informations = aggregateEditInformations(
        vertex_edit_informations, edge_edit_informations
    )
    edit_informations = scaleEditCosts(
        edit_informations, instructor_graph, student_graph
    )

    return edit_informations