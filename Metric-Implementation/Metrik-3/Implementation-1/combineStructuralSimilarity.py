import icontract
from Testset.isValidSimilarity import isValidSimilarity

# Weighting factor for combining inter- and intra-structure similarity.
# Inter-structure (relationship topology) is weighted more heavily because
# it is the dominant driver of perceived structural similarity.
THETA: float = 0.9


@icontract.require(
    lambda sim_inter: isValidSimilarity(sim_inter)
)
@icontract.require(
    lambda sim_intra: isValidSimilarity(sim_intra)
)
@icontract.ensure(lambda result: isValidSimilarity(result))
def combineStructuralSimilarity(sim_inter: float, sim_intra: float) -> float:
    r"""
    Combine inter-structure and intra-structure similarity into a single
    structural similarity value.

    --------------------------------------------------------------------------
    Formula
    --------------------------------------------------------------------------
    .. math::
        Sim(g_1, g_2) = \theta \cdot sim_{inter} + (1 - \theta) \cdot sim_{intra}

    where ``\theta`` is the module-level constant ``THETA`` (set to ``0.9``).

    The weighting factor ``THETA`` is fixed at ``0.9`` because the
    inter-structure (relationship topology) is experimentally found to be the
    dominant driver of perceived structural similarity, while the
    intra-structure (attribute composition inside classes) provides a secondary
    refinement.

    --------------------------------------------------------------------------
    Input
    --------------------------------------------------------------------------
    sim_inter : float
        Inter-structure similarity, already validated by ``isValidSimilarity``.
    sim_intra : float
        Intra-structure similarity, already validated by ``isValidSimilarity``.

    Output
    --------------------------------------------------------------------------
    float
        Combined structural similarity in ``[0, 1]``.

    Preconditions (requires)
    --------------------------------------------------------------------------
    * ``isValidSimilarity(sim_inter)`` holds.
    * ``isValidSimilarity(sim_intra)`` holds.

    Postconditions (ensures)
    --------------------------------------------------------------------------
    * ``isValidSimilarity(result)`` holds.
    * ``result == THETA * sim_inter + (1 - THETA) * sim_intra``.
    """
    return THETA * sim_inter + (1 - THETA) * sim_intra
