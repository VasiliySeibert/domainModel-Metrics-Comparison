import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidEditInformations import isValidEditInformations
from Testset.isValidMapping import isValidMapping
from Testset.isValidGraph import isValidGraph
from Testset.s1_types import EditInformations, Graph, Mapping, OperationType
from metric_interface import validate_metric_result


@icontract.require(
    lambda edit_informations, optimal_mapping, element_mapping,
    instructor_graph, student_graph: (
        isValidEditInformations(edit_informations)
        and isValidMapping(optimal_mapping)
        and isValidMapping(element_mapping)
        and isValidGraph(instructor_graph)
        and isValidGraph(student_graph)
    )
)
@icontract.ensure(
    lambda result: validate_metric_result(result),
    "Returned dict satisfies validate_metric_result",
)
def normalization(
    edit_informations: EditInformations,
    optimal_mapping: Mapping,
    element_mapping: Mapping,
    instructor_graph: Graph,
    student_graph: Graph,
) -> dict:
    r"""
    Decompose the aggregate edit distance into three normalized scores.

    Parameters
    ----------
    edit_informations : EditInformations
        The complete edit path returned by ``scaleEditCosts``.
    optimal_mapping : Mapping
        The optimal bijection returned by ``computeOptimalMapping``.
    element_mapping : Mapping
        Contains ``element_cost_matrix`` with intra-level distances δ(m, m').
    instructor_graph : Graph
        The instructor graph G₁ = (V₁, E₁, μ, ρ).
    student_graph : Graph
        The student graph G₂ = (V₂, E₂, μ, ρ).

    Returns
    -------
    dict
        {
            "class_score":       float,  # [0, 1]
            "attribute_score":   float,  # [0, 1]
            "association_score": float,  # [0, 1]
        }

    Algorithm
    ---------
    **class_score**
        Sum raw costs of all vertex operations (substitution, deletion,
        insertion).  Maximum possible cost is ``max(|V₁|, |V₂|)``.

        class_score = 1.0 - (vertex_raw_costs / max(|V₁|, |V₂|))

    **association_score**
        Sum raw costs of all edge operations.  Maximum possible cost is
        ``|E₁| + |E₂|``.

        association_score = 1.0 - (edge_raw_costs / (|E₁| + |E₂|))

    **attribute_score**
        For every mapped vertex pair (m, m') in ``optimal_mapping``,
        recompute the attribute-only distance δ_attrs(m, m') using the
        Hungarian attribute-matching logic from ``computeElementMapping``
        with name/type/const/default weights.  Unmapped vertices count as
        unit cost 1.0.

        attribute_penalty = sum(δ_attrs) + n_unmapped
        max_attr_cost = max(|V₁|, |V₂|)
        attribute_score = 1.0 - (attribute_penalty / max_attr_cost)

    All scores are clamped to [0, 1].
    """
    import numpy as np
    from scipy.optimize import linear_sum_assignment

    def lev(a: str, b: str) -> float:
        import Levenshtein
        if a == b:
            return 0.0
        max_len = max(len(a), len(b))
        if max_len == 0:
            return 0.0
        return Levenshtein.distance(a, b) / max_len

    def attr_distance(a, b):
        d_name = lev(a.name, b.name)
        d_type = 0.0 if a.type == b.type else 1.0
        d_const = 0.0 if a.is_constant == b.is_constant else 1.0
        d_default = lev(a.default_value or "", b.default_value or "")
        return 0.5 * d_name + 0.3 * d_type + 0.1 * d_const + 0.1 * d_default

    def attr_set_distance(attrs_a, attrs_b):
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

    # 1. class_score
    vertex_raw_costs = sum(
        op.raw_cost
        for op in edit_informations.operations
        if op.operation_type.name.startswith("VERTEX")
    )
    v_inst = len(instructor_graph.vertices)
    v_stud = len(student_graph.vertices)
    max_v = max(v_inst, v_stud)
    class_score = 1.0 - (vertex_raw_costs / max_v) if max_v > 0 else 1.0

    # 2. association_score — tight bound is max(|E₁|, |E₂|) because Hungarian
    # pads the cost matrix to that square size.
    edge_raw_costs = sum(
        op.raw_cost
        for op in edit_informations.operations
        if op.operation_type.name.startswith("EDGE")
    )
    e_inst = len(instructor_graph.edges)
    e_stud = len(student_graph.edges)
    max_e = max(e_inst, e_stud)
    association_score = 1.0 - (edge_raw_costs / max_e) if max_e > 0 else 1.0

    # 3. attribute_score
    # Build lookup from vertex_id to element
    inst_elem = {v.vertex_id: v.element for v in instructor_graph.vertices}
    stud_elem = {v.vertex_id: v.element for v in student_graph.vertices}

    def attr_count_for(vid, is_inst=True):
        elem = inst_elem[vid] if is_inst else stud_elem[vid]
        return len(elem.attributes)

    attr_penalty = 0.0
    max_attr_penalty = 0.0
    for entry in optimal_mapping.vertex_mappings:
        m = inst_elem[entry.instructor_vertex_id]
        mp = stud_elem[entry.student_vertex_id]
        d = attr_set_distance(m.attributes, mp.attributes)
        attr_penalty += d
        max_attr_penalty += max(len(m.attributes), len(mp.attributes))

    for vid in optimal_mapping.unmapped_instructor_vertices:
        n = attr_count_for(vid, is_inst=True)
        attr_penalty += n   # all attributes deleted
        max_attr_penalty += n

    for vid in optimal_mapping.unmapped_student_vertices:
        n = attr_count_for(vid, is_inst=False)
        attr_penalty += n   # all attributes inserted
        max_attr_penalty += n

    attribute_score = 1.0 - (attr_penalty / max_attr_penalty) if max_attr_penalty > 0 else 1.0

    def clamp(x):
        return max(0.0, min(1.0, float(x)))

    result = {
        "class_score": clamp(class_score),
        "attribute_score": clamp(attribute_score),
        "association_score": clamp(association_score),
    }
    return result
