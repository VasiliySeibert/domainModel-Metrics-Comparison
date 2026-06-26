"""
metric — Orchestrates the Metrik-2 pipeline (S2 normalised version).

Pipeline
--------
1. mapping = mapClasses/Relations
2. mistakes  = checkClasses/Relations/Missing
3. result = normalize(mistakes)
4. return result
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidModel import isValidModel
from Testset.isValidEditInformations import isValidEditInformations
from Testset.s1_types import EditInformations
from metric_interface import validate_metric_result

from createGraph import createGraph
from computeElementMapping import computeElementMapping
from computeRelationMapping import computeRelationMapping
from computeOptimalMapping import computeOptimalMapping
from extractVertexEditInformations import extractVertexEditInformations
from extractEdgeEditInformations import extractEdgeEditInformations
from aggregateEditInformations import aggregateEditInformations
from scaleEditCosts import scaleEditCosts
from normalization import normalization


@icontract.require(lambda instructor_model, student_model: (
    isValidModel(instructor_model) and isValidModel(student_model)
))
@icontract.ensure(lambda result: validate_metric_result(result))
def metric(instructor_model, student_model) -> dict:
    """
    Compare an instructor domain model against a student domain model and
    return a normalised MetricResult with three scores in [0.0, 1.0].

    Pipeline
    --------
    1. instructor_graph = createGraph(instructor_model)
       student_graph    = createGraph(student_model)
    2. element_mapping  = computeElementMapping(instructor_graph, student_graph)
    3. relation_mapping = computeRelationMapping(instructor_graph, student_graph)
    4. optimal_mapping  = computeOptimalMapping(
           instructor_graph, student_graph, element_mapping, relation_mapping
       )
    5. vertex_edit_informations = extractVertexEditInformations(optimal_mapping)
    6. edge_edit_informations   = extractEdgeEditInformations(optimal_mapping)
    7. edit_informations = aggregateEditInformations(
           vertex_edit_informations, edge_edit_informations
       )
    8. edit_informations = scaleEditCosts(
           edit_informations, instructor_graph, student_graph
       )
    9. result = normalization(
           edit_informations,
           optimal_mapping,
           element_mapping,
           instructor_graph,
           student_graph,
       )
    10. return result

    requires:
        isValidModel(instructor_model)
        isValidModel(student_model)
    ensures:
        validate_metric_result(result)
    """
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
    result = normalization(
        edit_informations,
        optimal_mapping,
        element_mapping,
        instructor_graph,
        student_graph,
    )
    return result
