import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidGraph import isValidGraph
from Testset.isValidMapping import isValidMapping
from Testset.s1_types import Graph, Mapping, VertexMappingEntry, EdgeMappingEntry

import numpy as np
from scipy.optimize import linear_sum_assignment


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
    """
    inst_vertices = instructor_graph.vertices
    stud_vertices = student_graph.vertices
    inst_edges = instructor_graph.edges
    stud_edges = student_graph.edges
    
    # --- Vertex assignment ---
    n1v = len(inst_vertices)
    n2v = len(stud_vertices)
    Nv = max(n1v, n2v)
    
    vertex_mappings = []
    unmapped_instructor_vertices = []
    unmapped_student_vertices = []
    
    if Nv > 0:
        # Build padded cost matrix for vertices
        cost_matrix_v = np.ones((Nv, Nv))
        for i in range(n1v):
            for j in range(n2v):
                iv = inst_vertices[i]
                sv = stud_vertices[j]
                cost_matrix_v[i][j] = element_mapping.element_cost_matrix[(iv.vertex_id, sv.vertex_id)]
        # Rows i >= n1v: dummy -> insertion cost 1.0 (already set)
        # Cols j >= n2v: dummy -> deletion cost 1.0 (already set)
        # Cell (i>=n1v, j>=n2v): dummy->dummy cost 0.0
        for i in range(n1v, Nv):
            for j in range(n2v, Nv):
                cost_matrix_v[i][j] = 0.0
        
        row_ind, col_ind = linear_sum_assignment(cost_matrix_v)
        
        for k in range(Nv):
            i = row_ind[k]
            j = col_ind[k]
            cost = cost_matrix_v[i][j]
            
            if i < n1v and j < n2v:
                # Substitution
                vertex_mappings.append(VertexMappingEntry(
                    instructor_vertex_id=inst_vertices[i].vertex_id,
                    student_vertex_id=stud_vertices[j].vertex_id,
                    raw_cost=float(cost),
                ))
            elif i < n1v and j >= n2v:
                # Deletion (instructor vertex unmapped)
                unmapped_instructor_vertices.append(inst_vertices[i].vertex_id)
            elif i >= n1v and j < n2v:
                # Insertion (student vertex unmapped)
                unmapped_student_vertices.append(stud_vertices[j].vertex_id)
            # else: dummy -> dummy, skip
    
    # --- Edge assignment ---
    n1e = len(inst_edges)
    n2e = len(stud_edges)
    Ne = max(n1e, n2e)
    
    edge_mappings = []
    unmapped_instructor_edges = []
    unmapped_student_edges = []
    
    if Ne > 0:
        # Build padded cost matrix for edges
        cost_matrix_e = np.ones((Ne, Ne))
        for i in range(n1e):
            for j in range(n2e):
                ie = inst_edges[i]
                se = stud_edges[j]
                cost_matrix_e[i][j] = relation_mapping.relation_cost_matrix[(ie.edge_id, se.edge_id)]
        # Rows i >= n1e: dummy -> insertion cost 1.0 (already set)
        # Cols j >= n2e: dummy -> deletion cost 1.0 (already set)
        for i in range(n1e, Ne):
            for j in range(n2e, Ne):
                cost_matrix_e[i][j] = 0.0
        
        row_ind, col_ind = linear_sum_assignment(cost_matrix_e)
        
        for k in range(Ne):
            i = row_ind[k]
            j = col_ind[k]
            cost = cost_matrix_e[i][j]
            
            if i < n1e and j < n2e:
                # Substitution
                edge_mappings.append(EdgeMappingEntry(
                    instructor_edge_id=inst_edges[i].edge_id,
                    student_edge_id=stud_edges[j].edge_id,
                    raw_cost=float(cost),
                ))
            elif i < n1e and j >= n2e:
                # Deletion (instructor edge unmapped)
                unmapped_instructor_edges.append(inst_edges[i].edge_id)
            elif i >= n1e and j < n2e:
                # Insertion (student edge unmapped)
                unmapped_student_edges.append(stud_edges[j].edge_id)
            # else: dummy -> dummy, skip
    
    # Compute total raw cost
    total_raw_cost = (
        sum(vm.raw_cost for vm in vertex_mappings)
        + sum(em.raw_cost for em in edge_mappings)
        + len(unmapped_instructor_vertices) * 1.0  # deletion cost
        + len(unmapped_student_vertices) * 1.0  # insertion cost
        + len(unmapped_instructor_edges) * 1.0  # deletion cost
        + len(unmapped_student_edges) * 1.0  # insertion cost
    )
    
    return Mapping(
        element_cost_matrix=element_mapping.element_cost_matrix,
        relation_cost_matrix=relation_mapping.relation_cost_matrix,
        vertex_mappings=vertex_mappings,
        edge_mappings=edge_mappings,
        unmapped_instructor_vertices=unmapped_instructor_vertices,
        unmapped_student_vertices=unmapped_student_vertices,
        unmapped_instructor_edges=unmapped_instructor_edges,
        unmapped_student_edges=unmapped_student_edges,
        total_raw_cost=total_raw_cost,
    )