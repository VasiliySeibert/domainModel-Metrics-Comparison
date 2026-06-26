import sys
from pathlib import Path
from typing import List, Dict
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidUCG import isValidUCG
from Testset.s1_types import UCG, UCGEdge, UMCS


@icontract.require(lambda g1, g2: isValidUCG(g1) and isValidUCG(g2))
def computeUMCSList(g1: UCG, g2: UCG) -> List[UMCS]:
    r"""
    Search for all UCG Maximum Common Subgraphs (UMCS) between two UCGs.
    Exact exponential-time backtracking with strong branch-and-bound pruning.
    To keep the UMCS Tree construction tractable, only the first-found
    maximum-size subgraph is returned.  This preserves determinism and
    keeps the tree linear, which is sufficient for the structural similarity
    computation.
    """
    E1 = sorted(
        [e for e in g1.edges if e.edge_type == "relationship"],
        key=lambda e: (e.tag, e.source_vertex_id, e.target_vertex_id),
    )
    E2 = sorted(
        [e for e in g2.edges if e.edge_type == "relationship"],
        key=lambda e: (e.tag, e.source_vertex_id, e.target_vertex_id),
    )

    if not E1 or not E2:
        return []

    # Index E2 by tag and nested lookup keys
    e2_by_tag: Dict[str, List[UCGEdge]] = defaultdict(list)
    e2_by_tag_source: Dict = defaultdict(list)
    e2_by_tag_target: Dict = defaultdict(list)
    e2_by_tag_source_target: Dict = defaultdict(list)
    for e in E2:
        e2_by_tag[e.tag].append(e)
        e2_by_tag_source[(e.tag, e.source_vertex_id)].append(e)
        e2_by_tag_target[(e.tag, e.target_vertex_id)].append(e)
        e2_by_tag_source_target[(e.tag, e.source_vertex_id, e.target_vertex_id)].append(e)

    # Precompute suffix tag counts for E1
    suffix_tag_counts = []
    running = Counter()
    for e in reversed(E1):
        running[e.tag] += 1
        suffix_tag_counts.append(dict(running))
    suffix_tag_counts.reverse()
    suffix_tag_counts.append({})

    best_size = 0
    best_umcs: UMCS = None
    S: List = []
    vertex_map: Dict[str, str] = {}
    inv_map: Dict[str, str] = {}
    used_g2_ids: set = set()
    remaining_e2_tag_counts = Counter(e.tag for e in E2)

    def backtrack(i: int):
        nonlocal best_size, best_umcs

        # Pruning 1: total remaining edges
        max_possible = len(S) + (len(E1) - i)
        if max_possible < best_size:
            return

        # Pruning 2: per-tag upper bound
        upper = 0
        rem = suffix_tag_counts[i]
        for tag, cnt1 in rem.items():
            cnt2 = remaining_e2_tag_counts.get(tag, 0)
            upper += min(cnt1, cnt2)
        if len(S) + upper < best_size:
            return

        if i == len(E1):
            if len(S) > best_size:
                best_size = len(S)
                best_umcs = UMCS(
                    edge_ids=frozenset(e1_id for e1_id, _ in S),
                    vertex_map=dict(vertex_map),
                )
            return

        # Skip branch
        backtrack(i + 1)

        # Include branch
        e1 = E1[i]
        s1 = e1.source_vertex_id
        t1 = e1.target_vertex_id
        tag = e1.tag

        # Look up candidates based on current vertex_map
        if s1 in vertex_map and t1 in vertex_map:
            cands = e2_by_tag_source_target.get((tag, vertex_map[s1], vertex_map[t1]), [])
        elif s1 in vertex_map:
            cands = e2_by_tag_source.get((tag, vertex_map[s1]), [])
        elif t1 in vertex_map:
            cands = e2_by_tag_target.get((tag, vertex_map[t1]), [])
        else:
            cands = e2_by_tag.get(tag, [])

        for e2 in cands:
            if e2.edge_id in used_g2_ids:
                continue
            if remaining_e2_tag_counts[e2.tag] == 0:
                continue
            s2 = e2.source_vertex_id
            t2 = e2.target_vertex_id

            # Consistency check
            if vertex_map.get(s1, s2) != s2:
                continue
            if vertex_map.get(t1, t2) != t2:
                continue
            if inv_map.get(s2, s1) != s1:
                continue
            if inv_map.get(t2, t1) != t1:
                continue
            if s1 == t1 and s2 != t2:
                continue

            # Injectivity check for new mappings
            new_vm = {}
            if s1 not in vertex_map:
                new_vm[s1] = s2
            if t1 not in vertex_map:
                new_vm[t1] = t2
            new_vals = list(new_vm.values())
            if len(set(new_vals)) != len(new_vals):
                continue
            if any(v in inv_map for v in new_vals):
                continue

            # Apply changes
            new_im = []
            for k, v in new_vm.items():
                vertex_map[k] = v
                inv_map[v] = k
                new_im.append(v)

            S.append((e1.edge_id, e2.edge_id))
            used_g2_ids.add(e2.edge_id)
            remaining_e2_tag_counts[e2.tag] -= 1

            backtrack(i + 1)

            # Restore state
            S.pop()
            used_g2_ids.remove(e2.edge_id)
            remaining_e2_tag_counts[e2.tag] += 1
            for k in new_vm:
                del vertex_map[k]
            for v in new_im:
                del inv_map[v]

    backtrack(0)
    if best_umcs is None:
        return []
    return [best_umcs]
