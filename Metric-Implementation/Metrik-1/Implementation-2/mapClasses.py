import icontract
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4 / "Parser"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    MappedClass,
    MappedAttributes,
    MappedAttribute,
    ClassMapping,
    RelationshipMapping,
    MappingType,
)
from isValidMistakes import isValidMistakes, ParsedMistake, KNOWN_MISTAKE_IDS
from models import ParsedClass, ParsedAttribute, ParsedRelationship, RelationshipType


@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMapping(result))
def mapClasses(instructor_model: ParsedModel, student_model: ParsedModel) -> ParsedMapping:
    """
    mapping = mapClasses(instructor_model, student_model):
       unmatched_ic, unmatched_sc = instructor_model.classes, student_model.classes
       mapping  = greedyNameMatch(unmatched_ic, unmatched_sc)
       mapping += greedyAttributeMatch(unmatched_ic, unmatched_sc)
       return mapping

       requires: isValidModel
       ensures: isValidMapping
    """
    unmatched_ic = list(instructor_model.classes)
    unmatched_sc = list(student_model.classes)

    # --- Greedy name match ---
    ic_by_name: Dict[str, ParsedClass] = {c.name: c for c in unmatched_ic}
    sc_by_name: Dict[str, ParsedClass] = {c.name: c for c in unmatched_sc}

    mapped_classes: List[MappedClass] = []
    matched_ic_names: Set[str] = set()
    matched_sc_names: Set[str] = set()

    for sc_name in sorted(sc_by_name.keys()):
        if sc_name in ic_by_name:
            ic = ic_by_name[sc_name]
            sc = sc_by_name[sc_name]
            mapped_classes.append(
                MappedClass(
                    student_class=sc_name,
                    instructor_classes=[sc_name],
                    mapping_type=MappingType.EXACT,
                    mapped_attributes=_map_attributes(sc, ic),
                )
            )
            matched_ic_names.add(sc_name)
            matched_sc_names.add(sc_name)

    remaining_ic = [c for c in unmatched_ic if c.name not in matched_ic_names]
    remaining_sc = [c for c in unmatched_sc if c.name not in matched_sc_names]

    # --- Greedy attribute match ---
    while True:
        best_pair: Tuple[ParsedClass, ParsedClass] | None = None
        best_overlap = -1
        for ic in remaining_ic:
            ic_attr_names = {a.name for a in ic.attributes}
            for sc in remaining_sc:
                sc_attr_names = {a.name for a in sc.attributes}
                overlap = len(ic_attr_names & sc_attr_names)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_pair = (ic, sc)
                elif overlap == best_overlap and overlap >= 0 and best_pair is not None:
                    if (ic.name, sc.name) < (best_pair[0].name, best_pair[1].name):
                        best_pair = (ic, sc)

        if best_pair is None or best_overlap <= 0:
            break

        ic, sc = best_pair
        mapped_classes.append(
            MappedClass(
                student_class=sc.name,
                instructor_classes=[ic.name],
                mapping_type=MappingType.RENAME,
                mapped_attributes=_map_attributes(sc, ic),
            )
        )
        remaining_ic = [c for c in remaining_ic if c.name != ic.name]
        remaining_sc = [c for c in remaining_sc if c.name != sc.name]

    class_mapping = ClassMapping(
        mapped_classes=mapped_classes,
        unmapped_instructor_classes=sorted([c.name for c in remaining_ic]),
        unmapped_student_classes=sorted([c.name for c in remaining_sc]),
    )

    return ParsedMapping(
        class_mapping=class_mapping,
        relationship_mapping=RelationshipMapping(),
        raw_source="",
    )


def _map_attributes(sc: ParsedClass, ic: ParsedClass) -> MappedAttributes:
    """Map attributes between a matched student and instructor class."""
    s_attrs = list(sc.attributes)
    i_attrs = list(ic.attributes)

    s_by_name = {a.name: a for a in s_attrs}
    i_by_name = {a.name: a for a in i_attrs}

    mappings: List[MappedAttribute] = []
    matched_s_names: Set[str] = set()
    matched_i_names: Set[str] = set()

    # Exact name matches
    common_names = sorted(set(s_by_name.keys()) & set(i_by_name.keys()))
    for name in common_names:
        s_attr = s_by_name[name]
        i_attr = i_by_name[name]
        if s_attr.type == i_attr.type:
            mappings.append(MappedAttribute(name, name, MappingType.EXACT))
        else:
            mappings.append(MappedAttribute(name, name, MappingType.TYPE_CHANGE))
        matched_s_names.add(name)
        matched_i_names.add(name)

    # Remaining: match by type (treated as renamed)
    remaining_s = sorted([a for a in s_attrs if a.name not in matched_s_names], key=lambda a: a.name)
    remaining_i = sorted([a for a in i_attrs if a.name not in matched_i_names], key=lambda a: a.name)

    used_i_names: Set[str] = set()
    for s_attr in remaining_s:
        found = None
        for i_attr in remaining_i:
            if i_attr.name in used_i_names:
                continue
            if s_attr.type == i_attr.type:
                found = i_attr
                break
        if found:
            mappings.append(MappedAttribute(s_attr.name, found.name, MappingType.RENAME))
            used_i_names.add(found.name)
        else:
            mappings.append(MappedAttribute(s_attr.name, None, MappingType.EXTRA))

    return MappedAttributes(mappings=mappings)
