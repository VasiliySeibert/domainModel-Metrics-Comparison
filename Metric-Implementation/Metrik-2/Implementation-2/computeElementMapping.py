import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidGraph import isValidGraph
from Testset.isValidMapping import isValidMapping
from Testset.s1_types import Graph, Mapping

import numpy as np
from scipy.optimize import linear_sum_assignment


def _normalised_levenshtein(s1: str, s2: str) -> float:
    """Compute normalised Levenshtein distance between two strings."""
    if len(s1) == 0 and len(s2) == 0:
        return 0.0
    m, n = len(s1), len(s2)
    # Standard Levenshtein DP
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    max_len = max(m, n)
    if max_len == 0:
        return 0.0
    return dp[m][n] / max_len


def _attribute_distance(a1, a2) -> float:
    """Distance between two ParsedAttribute instances."""
    # 0.5 * name_levenshtein + 0.3 * type_distance + 0.1 * const_distance + 0.1 * default_distance
    name_dist = _normalised_levenshtein(a1.name, a2.name)
    type_dist = 0.0 if (a1.type == a2.type) else 1.0
    const_dist = 0.0 if (a1.is_constant == a2.is_constant) else 1.0
    default1 = a1.default_value if a1.default_value is not None else ""
    default2 = a2.default_value if a2.default_value is not None else ""
    default_dist = _normalised_levenshtein(default1, default2)
    return 0.5 * name_dist + 0.3 * type_dist + 0.1 * const_dist + 0.1 * default_dist


def _attribute_set_distance(attrs1, attrs2) -> float:
    """Hungarian matching on two attribute sets with epsilon padding."""
    n1, n2 = len(attrs1), len(attrs2)
    if n1 == 0 and n2 == 0:
        return 0.0
    max_size = max(n1, n2)
    if max_size == 0:
        return 0.0
    # Build padded cost matrix
    N = max(n1, n2)
    cost_matrix = np.ones((N, N))
    # Fill actual pairwise distances
    for i in range(n1):
        for j in range(n2):
            cost_matrix[i][j] = _attribute_distance(attrs1[i], attrs2[j])
    # Rows beyond n1: insertion (cost 1.0 already set)
    # Cols beyond n2: deletion (cost 1.0 already set)

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    total = sum(cost_matrix[row_ind[k], col_ind[k]] for k in range(N))
    return total / max_size


def _element_distance(e1, e2) -> float:
    """Distance between two ParsedClass instances."""
    # Weights: name=0.4, is_abstract (kind proxy)=0.1, attributes=0.5
    # Note: ParsedClass has no operations or scope fields, so we omit them.
    name_dist = _normalised_levenshtein(e1.name, e2.name)
    kind_dist = 0.0 if (e1.is_abstract == e2.is_abstract) else 1.0
    attrs_dist = _attribute_set_distance(e1.attributes, e2.attributes)
    # Normalize weights to sum to 1: 0.4 + 0.1 + 0.5 = 1.0 already
    return 0.4 * name_dist + 0.1 * kind_dist + 0.5 * attrs_dist


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
    """
    inst_vertices = instructor_graph.vertices
    stud_vertices = student_graph.vertices

    element_cost_matrix = {}

    for iv in inst_vertices:
        for sv in stud_vertices:
            if iv.vertex_id == sv.vertex_id:
                dist = 0.0
            else:
                dist = _element_distance(iv.element, sv.element)
            element_cost_matrix[(iv.vertex_id, sv.vertex_id)] = dist

    # Build full square padded cost matrix for Hungarian
    n1 = len(inst_vertices)
    n2 = len(stud_vertices)
    N = max(n1, n2)

    # Use Hungarian on the padded matrix to get optimal element mapping cost
    # (We need this for computeOptimalMapping to work correctly)
    cost_matrix = np.ones((N, N))
    for i in range(n1):
        for j in range(n2):
            iv = inst_vertices[i]
            sv = stud_vertices[j]
            cost_matrix[i][j] = element_cost_matrix[(iv.vertex_id, sv.vertex_id)]

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    total_raw = sum(cost_matrix[row_ind[k], col_ind[k]] for k in range(N))

    return Mapping(
        element_cost_matrix=element_cost_matrix,
        total_raw_cost=total_raw,
    )