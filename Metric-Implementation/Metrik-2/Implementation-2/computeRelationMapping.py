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

from Parser.models import RelationshipType


def _normalised_levenshtein(s1: str, s2: str) -> float:
    """Compute normalised Levenshtein distance between two strings."""
    if len(s1) == 0 and len(s2) == 0:
        return 0.0
    m, n = len(s1), len(s2)
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


def _parse_cardinality(card_str):
    """Parse a multiplicity string like '1..*' or '0..1' into a set of integers.
    
    '*' is treated as 1..100 (capped at 100).
    Comma-separated parts are unioned.
    None returns None.
    """
    if card_str is None:
        return None
    
    result = set()
    parts = [p.strip() for p in card_str.split(',')]
    for part in parts:
        # Handle ranges like "1..*", "0..1", "1..2"
        if '..' in part:
            range_parts = part.split('..')
            start_str = range_parts[0].strip()
            end_str = range_parts[1].strip()
            
            start = int(start_str) if start_str != '*' else 1
            end_val = int(end_str) if end_str != '*' else 100
            result.update(range(start, end_val + 1))
        else:
            # Single value like "1" or "*"
            if part == '*':
                result.update(range(1, 101))
            else:
                result.add(int(part))
    
    return result


def _jaccard_cardinality_distance(card1, card2):
    """Jaccard distance between two parsed cardinality sets.
    
    If either is None and the other is not, distance is 1.0.
    If both are None, distance is 0.0.
    """
    set1 = _parse_cardinality(card1)
    set2 = _parse_cardinality(card2)
    
    if set1 is None and set2 is None:
        return 0.0
    if set1 is None or set2 is None:
        return 1.0
    
    if not set1 and not set2:
        return 0.0
    if not set1 or not set2:
        return 1.0
    
    intersection = set1 & set2
    union = set1 | set2
    return 1.0 - len(intersection) / len(union)


def _navigability_proxy(rel1, rel2, which_end):
    """Navigability proxy distance for a given end.
    
    For 'source': 0.0 if both source_cardinality are None or both are not None; 1.0 otherwise.
    For 'target': 0.0 if both target_cardinality are None or both are not None; 1.0 otherwise.
    Actually, the spec says navigability proxy based on whether the corresponding cardinality is None or not.
    Since the docstring says `δ_nav – navigability proxy: 0.0 if both source_cardinality are None or both are not None; 1.0 otherwise`
    we'll check source for source end and target for target end.
    """
    if which_end == 'source':
        c1 = rel1.source_cardinality
        c2 = rel2.source_cardinality
    else:
        c1 = rel1.target_cardinality
        c2 = rel2.target_cardinality
    
    # Both None or both not None -> 0.0; otherwise 1.0
    if (c1 is None) == (c2 is None):
        return 0.0
    return 1.0


# Relation-kind distance table
_KIND_DISTANCE = {
    # Identical
}

def _kind_distance(type1, type2):
    """Distance between two RelationshipType values according to the semantic distance table."""
    if type1 == type2:
        return 0.0
    
    t1 = type1.value if isinstance(type1, RelationshipType) else type1
    t2 = type2.value if isinstance(type2, RelationshipType) else type2
    
    # Normalize: sort pair so we can look it up
    pair = frozenset([t1, t2])
    
    distances = {
        frozenset(["association", "directed"]): 0.25,
        frozenset(["composition", "aggregation"]): 0.25,
        frozenset(["inheritance", "composition"]): 0.50,
        frozenset(["inheritance", "aggregation"]): 0.50,
        frozenset(["association", "composition"]): 0.50,
        frozenset(["association", "aggregation"]): 0.50,
        frozenset(["directed", "composition"]): 0.50,
        frozenset(["directed", "aggregation"]): 0.50,
        frozenset(["inheritance", "association"]): 0.50,
        frozenset(["inheritance", "directed"]): 0.50,
    }
    
    if pair in distances:
        return distances[pair]
    
    # Any pair involving dependency (not identical) -> 0.75
    if "dependency" in pair:
        return 0.75
    
    # All other distinct pairs -> 1.00
    return 1.0


def _relation_end_distance(rel1, rel2, which_end):
    """Distance between two relation ends (source or target).
    
    δ_end(b, b') = 0.4 * δ_role + 0.4 * δ_card + 0.2 * δ_nav
    """
    if which_end == 'source':
        label1 = rel1.label if rel1.label is not None else ""
        label2 = rel2.label if rel2.label is not None else ""
        # Wait, the label is on the relationship itself, not per end.
        # The spec says: δ_role – normalised Levenshtein distance on label (empty string if None)
        # But the label belongs to the relationship, not the end.
        # The source end's "label" in the sense of the role name.
        # ParsedRelationship has: source, target, source_cardinality, target_cardinality, label
        # The label is a single label for the whole relationship.
        # For source end distance, we'll use the relationship label.
        # For target end distance, we'll also use the relationship label.
        # Actually the spec says "role name" which is usually the label.
        # Let's use the label for both ends since ParsedRelationship only has one label.
        role_dist = _normalised_levenshtein(
            rel1.label if rel1.label is not None else "",
            rel2.label if rel2.label is not None else ""
        )
        card_dist = _jaccard_cardinality_distance(rel1.source_cardinality, rel2.source_cardinality)
        nav_dist = _navigability_proxy(rel1, rel2, 'source')
    else:
        role_dist = _normalised_levenshtein(
            rel1.label if rel1.label is not None else "",
            rel2.label if rel2.label is not None else ""
        )
        card_dist = _jaccard_cardinality_distance(rel1.target_cardinality, rel2.target_cardinality)
        nav_dist = _navigability_proxy(rel1, rel2, 'target')
    
    return 0.4 * role_dist + 0.4 * card_dist + 0.2 * nav_dist


def _single_relation_distance(r1, r2):
    """Distance between two ParsedRelationship instances.
    
    δ_rel(r, r') = 0.4 * δ_kind + 0.3 * δ_source + 0.3 * δ_target
    """
    kind_dist = _kind_distance(r1.relationship_type, r2.relationship_type)
    source_dist = _relation_end_distance(r1, r2, 'source')
    target_dist = _relation_end_distance(r1, r2, 'target')
    return 0.4 * kind_dist + 0.3 * source_dist + 0.3 * target_dist


def _relation_set_distance(rels1, rels2):
    """Hungarian matching on two relation sets with epsilon padding.
    
    Normalised by max(|R|, |R'|).
    """
    n1, n2 = len(rels1), len(rels2)
    if n1 == 0 and n2 == 0:
        return 0.0
    
    max_size = max(n1, n2)
    if max_size == 0:
        return 0.0
    
    N = max_size
    cost_matrix = np.ones((N, N))
    for i in range(n1):
        for j in range(n2):
            cost_matrix[i][j] = _single_relation_distance(rels1[i], rels2[j])
    
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    total = sum(cost_matrix[row_ind[k], col_ind[k]] for k in range(N))
    return total / max_size


@icontract.require(lambda instructor_graph: isValidGraph(instructor_graph))
@icontract.require(lambda student_graph: isValidGraph(student_graph))
@icontract.ensure(lambda result: isValidMapping(result))
@icontract.ensure(
    lambda result: all(0.0 <= v <= 1.0 for v in result.relation_cost_matrix.values())
)
@icontract.ensure(
    lambda result: all(
        v == 0.0
        for (i, j), v in result.relation_cost_matrix.items()
        if i == j
    )
)
def computeRelationMapping(instructor_graph: Graph, student_graph: Graph) -> Mapping:
    r"""
    Compute the intra-level relation cost matrix for the Graph Edit Distance
    (GED) pipeline.
    """
    inst_edges = instructor_graph.edges
    stud_edges = student_graph.edges
    
    relation_cost_matrix = {}
    
    for ie in inst_edges:
        for se in stud_edges:
            if ie.edge_id == se.edge_id:
                dist = 0.0
            else:
                dist = _relation_set_distance(ie.relations, se.relations)
            relation_cost_matrix[(ie.edge_id, se.edge_id)] = dist
    
    # Build padded cost matrix for Hungarian to compute total_raw_cost
    n1 = len(inst_edges)
    n2 = len(stud_edges)
    N = max(n1, n2) if max(n1, n2) > 0 else 0
    
    total_raw = 0.0
    if N > 0:
        cost_matrix = np.ones((N, N))
        for i in range(n1):
            for j in range(n2):
                ie = inst_edges[i]
                se = stud_edges[j]
                cost_matrix[i][j] = relation_cost_matrix[(ie.edge_id, se.edge_id)]
        
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        total_raw = sum(cost_matrix[row_ind[k], col_ind[k]] for k in range(N))
    
    return Mapping(
        relation_cost_matrix=relation_cost_matrix,
        total_raw_cost=total_raw,
    )