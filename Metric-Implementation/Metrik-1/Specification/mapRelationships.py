import icontract
from typing import List, Dict, Optional, Tuple

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Parser.models import ParsedRelationship, RelationshipType

from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    MappedRelationship,
    RelationshipMapping,
    MappingType,
)


@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.ensure(lambda result: isValidMapping(result))
def mapRelationships(
    instructor_model: ParsedModel,
    student_model: ParsedModel,
    mapping: ParsedMapping,
) -> ParsedMapping:
    """
    Maps instructor relationships to student relationships by reusing the
    existing class mapping.  Association-class relationships are ignored.

    Algorithm
    ---------
    1. Build a dictionary instructor_class_name → student_class_name from
       the existing class mapping.

    2. Initialise every relationship in both models as *unmatched*,
       discarding association-class relationships.

    3. Stage 1 – Strong matching.
       For each unmatched (ir, sr) pair translate ir's endpoints.
       A candidate is created when both endpoints of ir are mapped and
       the translated names coincide with sr's endpoints (exact direction
       or reversed).

       Determine whether the match is inverted:
           • exact direction  – translated_src == sr.source AND
                                translated_tgt == sr.target
           • reversed         – translated_src == sr.target AND
                                translated_tgt == sr.source
       A candidate has is_inverted = True when reversed, else False.

       Score:
           +100  ir.relationship_type == sr.relationship_type
           +10   ir.label == sr.label
            +5   cardinalities match in corresponding positions:
                 – if exact direction:
                     ir.source_cardinality == sr.source_cardinality
                     AND ir.target_cardinality == sr.target_cardinality
                 – if reversed:
                     ir.source_cardinality == sr.target_cardinality
                     AND ir.target_cardinality == sr.source_cardinality
            +1   exact direction (not reversed)

       Sort by score descending, break ties by endpoint names (student
       source then target), then by relationship index pairs.  All sort
       keys must be scalar values; do not compare ParsedRelationship or
       ParsedClass objects directly.

       Greedily walk the list: if both relationships are still
       unmatched, map them with mapping_type = EXACT when the
       relationship_type values match, otherwise TYPE_CHANGE.
       is_inverted is set as determined above.

    4. Stage 2 – Weak endpoint-only matching.
       Any remaining pair whose translated endpoints match in either
       direction (exact or reversed) becomes a candidate.
       Set is_inverted = True for reversed matches, else False.
       Sort deterministically by endpoint names (student source then
       target), then by relationship index pairs, using only scalar keys.
       Greedily map with mapping_type CUSTOM.

    5. Remainders → unmapped_instructor_relationships /
       unmapped_student_relationships.

    6. Return the updated mapping.
    """
    
