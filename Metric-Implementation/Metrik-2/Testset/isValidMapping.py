import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Testset.s1_types import Mapping, VertexMappingEntry, EdgeMappingEntry


def isValidMapping(mapping: Mapping) -> bool:
    """
    Validate that a Mapping instance is structurally consistent
    and adheres to the GED bijection constraints.
    """
    # 1. Must be a Mapping instance
    if not isinstance(mapping, Mapping):
        return False

    # 2. All vertex mapping entries must be VertexMappingEntry instances
    if not all(isinstance(vm, VertexMappingEntry) for vm in mapping.vertex_mappings):
        return False

    # 3. All edge mapping entries must be EdgeMappingEntry instances
    if not all(isinstance(em, EdgeMappingEntry) for em in mapping.edge_mappings):
        return False

    # 4. No instructor vertex mapped twice
    inst_vertex_ids = [vm.instructor_vertex_id for vm in mapping.vertex_mappings]
    if len(inst_vertex_ids) != len(set(inst_vertex_ids)):
        return False

    # 5. No student vertex mapped twice
    stu_vertex_ids = [vm.student_vertex_id for vm in mapping.vertex_mappings]
    if len(stu_vertex_ids) != len(set(stu_vertex_ids)):
        return False

    # 6. No instructor edge mapped twice
    inst_edge_ids = [em.instructor_edge_id for em in mapping.edge_mappings]
    if len(inst_edge_ids) != len(set(inst_edge_ids)):
        return False

    # 7. No student edge mapped twice
    stu_edge_ids = [em.student_edge_id for em in mapping.edge_mappings]
    if len(stu_edge_ids) != len(set(stu_edge_ids)):
        return False

    # 8. No overlap between mapped and unmapped instructor vertices
    mapped_inst_vertices = set(inst_vertex_ids)
    if mapped_inst_vertices.intersection(set(mapping.unmapped_instructor_vertices)):
        return False

    # 9. No overlap between mapped and unmapped student vertices
    mapped_stu_vertices = set(stu_vertex_ids)
    if mapped_stu_vertices.intersection(set(mapping.unmapped_student_vertices)):
        return False

    # 10. No overlap between mapped and unmapped instructor edges
    mapped_inst_edges = set(inst_edge_ids)
    if mapped_inst_edges.intersection(set(mapping.unmapped_instructor_edges)):
        return False

    # 11. No overlap between mapped and unmapped student edges
    mapped_stu_edges = set(stu_edge_ids)
    if mapped_stu_edges.intersection(set(mapping.unmapped_student_edges)):
        return False

    # 12. All raw costs in vertex mappings must be in [0, 1]
    for vm in mapping.vertex_mappings:
        if not (0.0 <= vm.raw_cost <= 1.0):
            return False

    # 13. All raw costs in edge mappings must be in [0, 1]
    for em in mapping.edge_mappings:
        if not (0.0 <= em.raw_cost <= 1.0):
            return False

    # 14. No negative costs in cost matrices
    for cost in mapping.element_cost_matrix.values():
        if cost < 0:
            return False
    for cost in mapping.relation_cost_matrix.values():
        if cost < 0:
            return False

    # 15. total_raw_cost must be non-negative
    if mapping.total_raw_cost < 0:
        return False

    return True


if __name__ == "__main__":
    # Minimal smoke test
    m = Mapping(
        vertex_mappings=[
            VertexMappingEntry(instructor_vertex_id="vA", student_vertex_id="vA1", raw_cost=0.0)
        ],
        unmapped_instructor_vertices=[],
        unmapped_student_vertices=["vB1"],
        edge_mappings=[],
        unmapped_instructor_edges=[],
        unmapped_student_edges=[],
        total_raw_cost=0.0
    )
    print(isValidMapping(m))  # Expected: True
