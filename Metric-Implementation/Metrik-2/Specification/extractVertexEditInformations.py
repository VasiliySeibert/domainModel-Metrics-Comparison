import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidMapping import isValidMapping
from Testset.isValidEditInformations import isValidEditInformations
from Testset.s1_types import Mapping, EditInformations, EditInformation, OperationType


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.ensure(lambda result: isValidEditInformations(result))
def extractVertexEditInformations(mapping: Mapping) -> EditInformations:
    """
    Convert the optimal vertex mapping produced by ``computeOptimalMapping``
    into a list of vertex-level ``EditInformation`` records.

    This is the first step in decomposing the optimal GED mapping into an
    explicit edit path.  For every mapped vertex pair the function emits a
    *vertex substitution*; for every instructor vertex that was left
    unmapped it emits a *vertex deletion*; and for every student vertex
    that was left unmapped it emits a *vertex insertion*.

    Parameters
    ----------
    mapping : Mapping
        A valid ``Mapping`` instance produced by ``computeOptimalMapping``.
        It contains:

        * ``vertex_mappings`` – bijective pairs of instructor/student vertices
          together with their raw intra-element distance ``raw_cost``.
        * ``unmapped_instructor_vertices`` – instructor vertices assigned to
          the empty vertex ε (implying deletion).
        * ``unmapped_student_vertices`` – student vertices assigned from
          the empty vertex ε (implying insertion).

    Returns
    -------
    EditInformations
        A container whose ``operations`` list holds exactly one
        ``EditInformation`` per vertex-related edit operation.

    Algorithm / Theory
    ------------------
    The function follows the Graph Edit Distance (GED) decomposition defined
    in the S1 specification (s1.md, § ``extractVertexEditInformations``).

    For each ``VertexMappingEntry`` in ``mapping.vertex_mappings``:

        operation_type = OperationType.VERTEX_SUBSTITUTION
        source_ref     = instructor_vertex_id
        target_ref     = student_vertex_id
        raw_cost       = entry.raw_cost          # δ(m, m') ∈ [0, 1]

    For each ``unmapped_instructor_vertex``:

        operation_type = OperationType.VERTEX_DELETION
        source_ref     = instructor_vertex_id
        target_ref     = None   (ε)
        raw_cost       = 1.0

    For each ``unmapped_student_vertex``:

        operation_type = OperationType.VERTEX_INSERTION
        source_ref     = None   (ε)
        target_ref     = student_vertex_id
        raw_cost       = 1.0

    The constant cost ``1.0`` for insertions and deletions is dictated by the
    GED cost model (see metric-information.txt, Eq. 18) which requires

        c(u → ε) = c(ε → u′) = 1

    This guarantees that substitution is never more expensive than a paired
    deletion and insertion, thereby satisfying the triangle-inequality
    condition of a valid edit distance (Riesen, 2015).

    The returned ``EditInformations`` instance is later merged with the
    edge-level edit informations (``extractEdgeEditInformations``) by
    ``aggregateEditInformations`` and subsequently scaled by
    ``scaleEditCosts`` using :math:`c_{max}` (Eq. 19) to obtain a normalised
    distance in ``[0, 1]``.

    Preconditions
    -----------
    * ``isValidMapping(mapping)`` must hold.

    Postconditions
    --------------
    * ``isValidEditInformations(result)`` holds.
    * Every operation type is one of ``VERTEX_SUBSTITUTION``,
      ``VERTEX_DELETION``, or ``VERTEX_INSERTION``.
    * Insertion and deletion operations carry ``raw_cost == 1.0``.
    * Substitution operations carry ``raw_cost`` copied from the mapping
      entry, which lies in ``[0, 1]`` because of ``isValidMapping``.
    """
    pass
