"""
Structural Similarity Pipeline

Implements the structural component of the S-1 similarity metric using
UML Common Graphs (UCG) and Graph Edit Distance
(see Metric-Implementation/Metrik-5/Implementation_3/s1.md).

Exported functions:
    classStruc  – combines intraSim and interSim using rho_struc = 0.1.
    buildUCG    – constructs a UCG (networkx.MultiDiGraph) from a Diagram.
    intraSim    – GED similarity over per-class intra-subgraphs.
    interSim    – GED similarity over inter-class relationship subgraphs.
"""

import icontract
import networkx as nx

from metric_models import Diagram, StructuralScores
from ..Testset.metric_invariants import isValidDiagram, isValidUCG, isValidSimilarity
from metric_primitives import gedNormalized, greedyOptimalSum


# ----------------------------------------------------------------------
# Top-level structural similarity
# ----------------------------------------------------------------------
@icontract.require(lambda d1: isValidDiagram(d1))
@icontract.require(lambda d2: isValidDiagram(d2))
@icontract.ensure(
    lambda result: (
        isValidSimilarity(result.structural)
        and isValidSimilarity(result.intraSim)
        and isValidSimilarity(result.interSim)
    )
)
def classStruc(d1: Diagram, d2: Diagram) -> StructuralScores:
    """
    Computes the combined structural similarity between two Diagrams.

    Formula (s1.md Eq. adapted with rho_struc = 0.1):
        structural = (1 - 0.1) * intraSim(g1, g2) + 0.1 * interSim(g1, g2)
                 = 0.9 * intra + 0.1 * inter

    where g1 = buildUCG(d1), g2 = buildUCG(d2).

    Returns
    -------
    StructuralScores
        A frozen dataclass containing ``structural``, ``intraSim``, and
        ``interSim``.  The invariant
        ``structural == 0.9*intraSim + 0.1*interSim`` holds up to float
        tolerance ``1e-6``.
    """
    ...


# ----------------------------------------------------------------------
# UCG construction
# ----------------------------------------------------------------------
@icontract.require(lambda diagram: isValidDiagram(diagram))
@icontract.ensure(lambda result: isValidUCG(result))
def buildUCG(diagram: Diagram) -> nx.MultiDiGraph:
    """
    Builds a UML Common Graph (UCG) from a normalised Diagram.

    Algorithm
    ---------
    1. Create empty nx.MultiDiGraph G.
    2. For each class vertex:
           Add node ("vc", c.name) with tag="vc".
           For each attribute:
               Add node ("va", c.name, a.name) with tag="va".
               Add edge from vc node to va node with tag="e_a".
    3. For each association edge:
           Determine tag based on ownership:
               "none"        -> "e_1" (plain association)
               "aggregation" -> "e_3"
               "composition" -> "e_4"
           Add edge between ("vc", source) and ("vc", target) with that tag.
    4. For each dependency edge:   tag="e_5".
    5. For each generalization edge: tag="e_2".
    6. Return G.

    UCG taxonomy (s1.md §5.1):
        vc  – class vertex
        va  – attribute vertex
        e_a – attribute edge
        e_1 – association (ownership == "none")
        e_2 – generalization
        e_3 – aggregation
        e_4 – composition
        e_5 – dependency
    """
    ...


# ----------------------------------------------------------------------
# Intra-structure similarity
# ----------------------------------------------------------------------
@icontract.require(lambda g1: isValidUCG(g1))
@icontract.require(lambda g2: isValidUCG(g2))
@icontract.ensure(lambda result: isValidSimilarity(result))
def intraSim(g1: nx.MultiDiGraph, g2: nx.MultiDiGraph) -> float:
    """
    Computes GED-based similarity over per-class intra-subgraphs.

    Algorithm
    ---------
    1. sg1 = intraSubgraphs(g1) — list of subgraphs, one per class vertex.
    2. sg2 = intraSubgraphs(g2).
    3. If both empty -> return 1.0; if exactly one empty -> return 0.0.
    4. Build matrix M where M[i][j] = gedNormalized(sg1[i], sg2[j]).
    5. bestSum = greedyOptimalSum(M).
    6. Return (2 * bestSum) / (len(sg1) + len(sg2)).

    Note: intraSubgraphs is an implicit helper (not decomposed in s1.md)
          that extracts, for each "vc" node, the vc node plus all incident
          "va" nodes and "e_a" edges.
    """
    ...


# ----------------------------------------------------------------------
# Inter-structure similarity
# ----------------------------------------------------------------------
@icontract.require(lambda g1: isValidUCG(g1))
@icontract.require(lambda g2: isValidUCG(g2))
@icontract.ensure(lambda result: isValidSimilarity(result))
def interSim(g1: nx.MultiDiGraph, g2: nx.MultiDiGraph) -> float:
    """
    Computes GED-based similarity over inter-class relationship subgraphs.

    Algorithm
    ---------
    1. ig1 = interGraph(g1) — subgraph containing only "vc" vertices and
       relationship edges (e_1 .. e_5).
    2. ig2 = interGraph(g2).
    3. Return gedNormalized(ig1, ig2).

    Note: interGraph is an implicit helper (not decomposed in s1.md)
          that filters the UCG down to vc nodes and non-attribute edges.
    """
    ...