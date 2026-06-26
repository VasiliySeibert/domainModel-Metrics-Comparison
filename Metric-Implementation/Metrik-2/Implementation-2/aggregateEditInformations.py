import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidEditInformations import isValidEditInformations
from Testset.s1_types import EditInformations


@icontract.require(lambda vertex_edit_informations, edge_edit_informations: (
    isValidEditInformations(vertex_edit_informations)
))
@icontract.require(lambda vertex_edit_informations, edge_edit_informations: (
    isValidEditInformations(edge_edit_informations)
))
@icontract.ensure(lambda result: isValidEditInformations(result))
def aggregateEditInformations(
    vertex_edit_informations: EditInformations,
    edge_edit_informations: EditInformations,
) -> EditInformations:
    """
    Aggregate vertex-level and edge-level edit operations into a single edit path.
    """
    combined_operations = (
        vertex_edit_informations.operations + edge_edit_informations.operations
    )
    
    return EditInformations(
        operations=combined_operations,
        total_scaled_distance=0.0,
    )