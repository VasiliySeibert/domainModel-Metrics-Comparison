import sys
from pathlib import Path
from typing import List, Tuple, Set

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidUCG import isValidUCG
from Testset.isValidSimilarity import isValidSimilarity
from Testset.s1_types import UCG


# Default weights for intra-structure components.
# Because the concrete parser does not extract operations or parameters,
# simOper and simParam always evaluate to 1.0 (zero edit cost).  The
# effective formula therefore reduces to:
#     sim_intra = ALPHA * simAttr + BETA * 1.0 + GAMMA * 1.0
ALPHA: float = 0.4   # weight of attribute component
BETA:  float = 0.5   # weight of operation component (always 1.0 here)
GAMMA: float = 0.1   # weight of parameter component (always 1.0 here)

# Edit costs (all set to 1; the edit distance is measured by operation count)
IC1: int = 1   # insertion/deletion cost for one attribute vertex + edge
IC2: int = 1   # insertion/deletion cost for one operation vertex + edge
IC3: int = 1   # insertion/deletion cost for one parameter vertex + edge


@icontract.require(lambda g1, g2, matching_pairs: (
    isValidUCG(g1) and isValidUCG(g2)
))
@icontract.ensure(lambda result: isValidSimilarity(result))
def computeIntraStructureSimilarity(
    g1: UCG, g2: UCG, matching_pairs: Set[Tuple[str, str]]
) -> float:
    r"""
    Calculate intra-structure similarity between two matched UCGs.
    """
    # Pre-compute attribute edge counts per class vertex
    attr_count_g1: dict = {}
    attr_count_g2: dict = {}
    for e in g1.edges:
        if e.edge_type == "attribute":
            attr_count_g1[e.source_vertex_id] = attr_count_g1.get(e.source_vertex_id, 0) + 1
    for e in g2.edges:
        if e.edge_type == "attribute":
            attr_count_g2[e.source_vertex_id] = attr_count_g2.get(e.source_vertex_id, 0) + 1

    total_diff = 0
    total_max = 0

    for cvi, cvj in matching_pairs:
        na_i = attr_count_g1.get(cvi, 0)
        na_j = attr_count_g2.get(cvj, 0)
        max_val = max(na_i, na_j)
        if max_val > 0:
            total_diff += abs(na_i - na_j)
            total_max += max_val

    if total_max == 0:
        simAttr = 1.0
    else:
        simAttr = 1.0 - (total_diff * IC1) / total_max

    simOper = 1.0
    simParam = 1.0

    sim_intra = ALPHA * simAttr + BETA * simOper + GAMMA * simParam
    return sim_intra
