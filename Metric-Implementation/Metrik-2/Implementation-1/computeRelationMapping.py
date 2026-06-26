import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidGraph import isValidGraph
from Testset.isValidMapping import isValidMapping
from Testset.s1_types import Graph, Mapping


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
    from scipy.optimize import linear_sum_assignment
    import numpy as np
    import Levenshtein
    from Parser.models import RelationshipType

    inst_edges = {e.edge_id: e for e in instructor_graph.edges}
    stud_edges = {e.edge_id: e for e in student_graph.edges}

    def parse_multiplicity(s):
        if s is None:
            return None
        parts = s.split(",")
        result = set()
        for part in parts:
            part = part.strip()
            if ".." in part:
                low, high = part.split("..", 1)
                low = int(low.strip())
                high = high.strip()
                if high == "*":
                    high = 100
                else:
                    high = int(high)
                result.update(range(low, high + 1))
            else:
                if part == "*":
                    result.update(range(1, 101))
                else:
                    result.add(int(part))
        return result

    def cardinality_distance(a, b):
        if a is None and b is None:
            return 0.0
        if a is None or b is None:
            return 1.0
        if not a and not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return 1.0 - (inter / union) if union else 0.0

    def relation_end_distance(a_card, a_label, b_card, b_label):
        d_role = Levenshtein.distance(a_label or "", b_label or "") / max(
            len(a_label or ""), len(b_label or ""), 1
        )
        d_card = cardinality_distance(parse_multiplicity(a_card), parse_multiplicity(b_card))
        d_nav = 0.0 if (a_card is None) == (b_card is None) else 1.0
        return 0.4 * d_role + 0.4 * d_card + 0.2 * d_nav

    KIND_DIST = {
        frozenset({RelationshipType.ASSOCIATION, RelationshipType.DIRECTED_ASSOCIATION}): 0.25,
        frozenset({RelationshipType.COMPOSITION, RelationshipType.AGGREGATION}): 0.25,
        frozenset({RelationshipType.INHERITANCE, RelationshipType.COMPOSITION}): 0.50,
        frozenset({RelationshipType.INHERITANCE, RelationshipType.AGGREGATION}): 0.50,
        frozenset({RelationshipType.ASSOCIATION, RelationshipType.COMPOSITION}): 0.50,
        frozenset({RelationshipType.ASSOCIATION, RelationshipType.AGGREGATION}): 0.50,
        frozenset({RelationshipType.DIRECTED_ASSOCIATION, RelationshipType.COMPOSITION}): 0.50,
        frozenset({RelationshipType.DIRECTED_ASSOCIATION, RelationshipType.AGGREGATION}): 0.50,
        frozenset({RelationshipType.INHERITANCE, RelationshipType.ASSOCIATION}): 0.50,
        frozenset({RelationshipType.INHERITANCE, RelationshipType.DIRECTED_ASSOCIATION}): 0.50,
    }

    def relation_kind_distance(ka, kb):
        if ka == kb:
            return 0.0
        pair = frozenset({ka, kb})
        if RelationshipType.DEPENDENCY in pair and len(pair) == 2:
            return 0.75
        return KIND_DIST.get(pair, 1.0)

    def single_relation_distance(r1, r2):
        d_kind = relation_kind_distance(r1.relationship_type, r2.relationship_type)
        d_source = relation_end_distance(
            r1.source_cardinality, r1.label, r2.source_cardinality, r2.label
        )
        d_target = relation_end_distance(
            r1.target_cardinality, r1.label, r2.target_cardinality, r2.label
        )
        return 0.4 * d_kind + 0.3 * d_source + 0.3 * d_target

    def relation_set_distance(rels1, rels2):
        n = max(len(rels1), len(rels2))
        if n == 0:
            return 0.0
        cost = np.zeros((n, n), dtype=float)
        for i in range(n):
            for j in range(n):
                if i < len(rels1) and j < len(rels2):
                    cost[i, j] = single_relation_distance(rels1[i], rels2[j])
                else:
                    cost[i, j] = 1.0
        row_ind, col_ind = linear_sum_assignment(cost)
        total = cost[row_ind, col_ind].sum()
        return float(total) / n

    relation_cost_matrix = {}
    for ie in instructor_graph.edges:
        for se in student_graph.edges:
            if ie.edge_id == se.edge_id:
                d = 0.0
            else:
                d = relation_set_distance(ie.relations, se.relations)
            relation_cost_matrix[(ie.edge_id, se.edge_id)] = d

    return Mapping(relation_cost_matrix=relation_cost_matrix)
