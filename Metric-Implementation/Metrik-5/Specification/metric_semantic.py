"""
Semantic Similarity Pipeline

Implements the semantic component of the S-1 similarity metric
(see Metric-Implementation/Metrik-5/Implementation_3/s1.md).

Exported functions:
    classSem  – combines propSim and relSim using rho_sem = 0.3.
    propSim   – class-level property similarity via cSim and greedy optimal sum.
    relSim    – relationship-level similarity with dynamic weighting.
"""

import icontract

from metric_models import Diagram, SemanticScores
from ..Testset.metric_invariants import isValidDiagram, isValidSimilarity
from metric_primitives import greedyOptimalSum


# ----------------------------------------------------------------------
# Top-level semantic similarity
# ----------------------------------------------------------------------
@icontract.require(lambda d1: isValidDiagram(d1))
@icontract.require(lambda d2: isValidDiagram(d2))
@icontract.ensure(
    lambda result: (
        isValidSimilarity(result.semantic)
        and isValidSimilarity(result.propSim)
        and isValidSimilarity(result.relSim)
    )
)
def classSem(d1: Diagram, d2: Diagram) -> SemanticScores:
    """
    Compute the combined semantic similarity between two Diagrams.

    This function implements the top-level semantic formula that balances
    class-level *property* similarity (names and attributes) against
    *relationship* similarity (associations, dependencies, generalisations).

    Formula (Eq. 1)
    ----------------
        sem = (1 - rho_sem) * propSim(d1, d2) + rho_sem * relSim(d1, d2)

    where
        rho_sem = 0.3                               (semantic weight)
        propSim = class property similarity           (Eq. 2)
        relSim  = relationship similarity             (Eq. 9)

    Algorithm
    ---------
    1. Compute ``propSim(d1, d2)``.
    2. Compute ``relSim(d1, d2)``.
    3. Return ``SemanticScores(semantic=0.7*propSim + 0.3*relSim,
                               propSim=propSim,
                               relSim=relSim)``.

    Args
    ----
    d1 : Diagram
        First diagram (e.g. reference / instructor model).
    d2 : Diagram
        Second diagram (e.g. student model).

    Returns
    -------
    SemanticScores
        A frozen dataclass containing ``semantic``, ``propSim``, and
        ``relSim``.  The invariant ``semantic == 0.7*propSim + 0.3*relSim``
        holds up to float tolerance ``1e-6``.

    Requires
    --------
    * ``isValidDiagram(d1)``
    * ``isValidDiagram(d2)``

    Ensures
    -------
    * ``isValidSimilarity(result.semantic)``
    * ``isValidSimilarity(result.propSim)``
    * ``isValidSimilarity(result.relSim)``

    Notes
    -----
    * The paper originally defines class-level similarity as

          cSim = w_cn * cnSim + w_a * aSim + w_op * opSim,

      with ``(w_cn, w_a, w_op) = (0.4, 0.3, 0.3)``.  Because the PlantUML
      parser does not expose operations, the operation term ``opSim`` is
      omitted and the remaining weights are re-normalised so that they sum
      to 1.0:

          cSim = (0.4 / 0.7) * cnSim + (0.3 / 0.7) * aSim
               = 0.571 * cnSim + 0.429 * aSim.

      Here ``cnSim = CosineSim(c1.name, c2.name)`` and ``aSim`` is the
      attribute-set similarity defined in Eq. 3--5 (see ``propSim``).
    * Both sub-pipelines rely on ``CosineSim``, an NLP primitive that
      performs camelCase-aware tokenisation, Penn-Treebank POS tagging,
      stopword removal, lemmatisation, Wu--Palmer semantic filtering
      (threshold ``tau = 0.85``), and cosine similarity over weighted
      WordNet vectors.
    * ``clampToUnit`` is applied to the final result to guarantee the
      ``[0.0, 1.0]`` invariant.

    See Also
    --------
    propSim, relSim, CosineSim, clampToUnit, SemanticScores
    """
    ...


# ----------------------------------------------------------------------
# Property similarity
# ----------------------------------------------------------------------
@icontract.require(lambda d1: isValidDiagram(d1))
@icontract.require(lambda d2: isValidDiagram(d2))
@icontract.ensure(lambda result: isValidSimilarity(result))
def propSim(d1: Diagram, d2: Diagram) -> float:
    """
    Compute class property similarity using optimal bipartite matching.

    The function compares the *lexical content* (class names and their
    attributes) of two diagrams.  It builds a complete bipartite graph between
    the class sets of ``d1`` and ``d2``, then selects the best one-to-one
    matching via the greedy optimal-sum algorithm (``greedyOptimalSum``).
    The result is normalised so that a complete correspondence yields ``1.0``.

    Formula (Eq. 2)
    ---------------
                      2 * greedyOptimalSum( cSim_matrix )
        propSim = ------------------------------------------
                        |C1| + |C2|

    where
        C1     = d1.classes   (including enums-as-classes)
        C2     = d2.classes   (including enums-as-classes)
        M[i][j] = cSim( C1[i], C2[j] )

    Algorithm
    ---------
    1. Let ``C1 = d1.classes`` and ``C2 = d2.classes``.
    2. If both are empty → return ``1.0`` (trivially identical).
       If exactly one is empty → return ``0.0`` (trivially disjoint).
    3. Build the similarity matrix ``M`` where ``M[i][j] = cSim(C1[i], C2[j])``.
    4. ``bestSum = greedyOptimalSum(M)``.
    5. Return ``(2 * bestSum) / (|C1| + |C2|)``.

    Args
    ----
    d1 : Diagram
        First diagram (reference / instructor).
    d2 : Diagram
        Second diagram (student).

    Returns
    -------
    float
        Similarity in ``[0.0, 1.0]``.

    Requires
    --------
    * ``isValidDiagram(d1)``
    * ``isValidDiagram(d2)``

    Ensures
    -------
    * ``isValidSimilarity(result)``

    Sub-component: cSim (Eq. 3)
    ---------------------------
    Single-class similarity of two classes ``c1`` and ``c2``:

        cSim = 0.571 * cnSim + 0.429 * aSim

    where
        cnSim = CosineSim( c1.name, c2.name )
        aSim  = attribute-set similarity of c1 and c2    (Eq. 4)

    Sub-component: aSim (Eq. 4)
    ---------------------------
    Aggregate attribute similarity of two attribute sets ``A1`` and ``A2``:

                      2 * greedyOptimalSum( daSim_matrix )
        aSim = ------------------------------------------
                        |A1| + |A2|

    where
        M'[i][j] = daSim( A1[i], A2[j] )

    Edge cases:
    * both attribute lists empty → ``1.0``
    * exactly one attribute list empty → ``0.0``

    Sub-component: daSim (Eq. 5)
    ----------------------------
    Detailed attribute similarity of two single attributes ``a1``, ``a2``:

        daSim = 0.1 * sim(a1.modifier, a2.modifier)
              + 0.7 * CosineSim(a1.name, a2.name)
              + 0.2 * sim(a1.type, a2.type)

    where
        sim(x, y) = 1.0  if x == y
                    0.0  otherwise

    (string comparison is case-insensitive: both strings are lower-cased
    before equality test.)

    Notes
    -----
    * **Operations omitted** — The paper originally includes an operation
      component with ``w_op = 0.3``.  Because the parser does not expose
      operations, weights were re-normalised so that name and attribute
      contributions sum to ``1.0`` (``0.571`` vs. ``0.429``).
    * **Enums treated as classes** — ``ParsedEnum`` objects (standalone or
      nested) are converted to ``ClassInfo`` instances with ``name = enum
      name`` and ``attributes = [AttributeInfo(v, "enum_value", "const")
      for v in enum.values]``.  They compete naturally in the same bipartite
      matching pool as regular classes.
    * **Edge cases** — Two empty class sets → ``1.0``; one empty and one
      non-empty → ``0.0``.
    * **Complexity** — Building the matrix costs ``O(|C1| * |C2|)`` calls to
      ``cSim``; ``greedyOptimalSum`` is ``O(min(|C1|, |C2|)^2)``.

    See Also
    --------
    classSem, relSim, greedyOptimalSum, CosineSim, sim
    """
    ...


# ----------------------------------------------------------------------
# Relationship similarity
# ----------------------------------------------------------------------
@icontract.require(lambda d1: isValidDiagram(d1))
@icontract.require(lambda d2: isValidDiagram(d2))
@icontract.ensure(lambda result: isValidSimilarity(result))
def relSim(d1: Diagram, d2: Diagram) -> float:
    """
    Compute relationship similarity with dynamic weights per edge type.

    The function compares the *relationship topology* (associations,
    dependencies, generalisations) between two diagrams.  It weights each
    sub-component proportionally to the total number of edges of that type
    across both diagrams, giving more influence to the categories that are
    actually present.

    Formula (Eq. 9)
    ---------------
        relSim = w_ra * raSim(RA1, RA2)
               + w_rd * rdSim(RD1, RD2)
               + w_rg * rgSim(RG1, RG2)

    where
        RA  = association    edges (ASSOCIATION, DIRECTED_ASSOCIATION,
                                    COMPOSITION, AGGREGATION)
        RD  = dependency     edges
        RG  = generalisation edges (INHERITANCE)

    Dynamic weights (Eq. 9 continued)
    ---------------------------------
        N    = |RA1| + |RD1| + |RG1| + |RA2| + |RD2| + |RG2|

        w_ra = (|RA1| + |RA2|) / N
        w_rd = (|RD1| + |RD2|) / N
        w_rg = (|RG1| + |RG2|) / N

    Edge cases:
    * ``N == 0`` and both diagrams truly empty → ``1.0``
    * ``N == 0`` but one diagram has relationships → ``0.0``

    Algorithm
    ---------
    1. Unpack edge lists: ``RA, RD, RG`` for both diagrams.
    2. Compute ``N`` (total relationship edges in either diagram).
    3. Handle the ``N == 0`` edge cases above.
    4. Compute ``w_ra, w_rd, w_rg`` as defined above.
    5. Return ``w_ra * raSim(RA1, RA2) + w_rd * rdSim(RD1, RD2)
              + w_rg * rgSim(RG1, RG2)``.

    Args
    ----
    d1 : Diagram
        First diagram (reference / instructor).
    d2 : Diagram
        Second diagram (student).

    Returns
    -------
    float
        Relationship similarity in ``[0.0, 1.0]``.

    Requires
    --------
    * ``isValidDiagram(d1)``
    * ``isValidDiagram(d2)``

    Ensures
    -------
    * ``isValidSimilarity(result)``

    Sub-component: raSim (Eq. 10--11)
    ---------------------------------
    Association-set similarity of ``RA1`` and ``RA2``:

                        2 * greedyOptimalSum( draSim_matrix )
        raSim = ----------------------------------------
                        |RA1| + |RA2|

    where
        M_ra[i][j] = draSim( RA1[i], RA2[j] )

    and the per-pair association similarity is

        draSim = 0.3 * CosineSim( ra1.source, ra2.source )
               + 0.2 * CosineSim( ra1.name,  ra2.name  )
               + 0.2 * sim(       ra1.ownership, ra2.ownership )
               + 0.3 * CosineSim( ra1.target, ra2.target )

    where
        sim(x, y) = 1.0  if x == y
                    0.0  otherwise

    ``ownership`` is one of ``{"none", "aggregation", "composition"}``.
    If both relationship names are empty/None, the name term evaluates to
    ``0`` because an empty-string cosine returns ``0``.

    Edge cases:
    * both ``RA`` empty → ``1.0``
    * exactly one ``RA`` empty → ``0.0``

    Sub-component: rdSim (Eq. 12--13)
    ----------------------------------
    Dependency-set similarity of ``RD1`` and ``RD2``:

                        2 * greedyOptimalSum( drdSim_matrix )
        rdSim = ----------------------------------------
                        |RD1| + |RD2|

    where
        M_rd[i][j] = drdSim( RD1[i], RD2[j] )

    and the per-pair dependency similarity is

        drdSim = ( CosineSim( rd1.source, rd2.source )
                 + CosineSim( rd1.target, rd2.target ) ) / 2

    Edge cases:
    * both ``RD`` empty → ``1.0``
    * exactly one ``RD`` empty → ``0.0``

    Sub-component: rgSim (Eq. 14--15)
    ----------------------------------
    Generalisation-set similarity of ``RG1`` and ``RG2``:

                        2 * greedyOptimalSum( drgSim_matrix )
        rgSim = ----------------------------------------
                        |RG1| + |RG2|

    where
        M_rg[i][j] = drgSim( RG1[i], RG2[j] )

    and the per-pair generalisation similarity is

        drgSim = ( CosineSim( rg1.source, rg2.source )
                 + CosineSim( rg1.target, rg2.target ) ) / 2

    Edge cases:
    * both ``RG`` empty → ``1.0``
    * exactly one ``RG`` empty → ``0.0``

    Notes
    -----
    * **Dynamic weighting rationale** — A diagram that contains only
      associations and no dependencies should not be penalised by a fixed
      zero weight on the dependency component.  Normalising by the total
      edge count makes the metric sensitive to the *actual* content of
      the diagrams rather than their adherence to a fixed schema.
    * **Association-class expansion** — ``ASSOCIATION_CLASS`` relationships
      are decomposed into two plain associations before they reach this
      pipeline, so they naturally participate in ``RA``.
    * **Empty edge sets** — If ``RA1`` and ``RA2`` are both empty then
      ``w_ra * raSim(...)`` yields ``0.0`` and the remaining non-empty
      components carry the full weight.
    * **Complexity** — Matrix construction is ``O(k1 * k2)`` per type
      (``k`` = edge count of that type); ``greedyOptimalSum`` adds
      ``O(min(k1, k2)^2)`` for each non-empty type.

    See Also
    --------
    classSem, propSim, greedyOptimalSum, raSim, rdSim, rgSim, CosineSim
    """
    ...
