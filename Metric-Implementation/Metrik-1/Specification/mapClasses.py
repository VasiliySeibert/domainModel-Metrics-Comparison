import icontract

from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    ClassMapping,
    MappedClass,
    MappingType,
    MappedAttributes,
)


@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMapping(result))
def mapClasses(instructor_model: ParsedModel, student_model: ParsedModel) -> ParsedMapping:
    """
    Maps instructor classes to student classes using a two-stage greedy
    algorithm.  Matching proceeds in strict order of evidence strength so
    that a high-confidence name match cannot be blocked by a weaker one.

    Algorithm
    -----------
    1. Initialise every class in both models as *unmatched*.

    2. Stage 1 – Name-driven matching.
       For every unmatched (ic, sc) pair compute a lexical tier:
       • HIGH   – exact string match (treated as Levenshtein distance 0)
       • MEDIUM – Levenshtein distance d where 1 ≤ d ≤ 2
       • LOW    – the instructor class name is a strict substring of the
                   student class name (e.g. "Case" inside "Cases")
                   OR vice-versa.
       • NONE   – everything else

       Build the candidate list containing all HIGH and MEDIUM pairs.
       Sort it by distance ascending; ties are broken by descending
       attribute-overlap percentage, then by alphabetical student-class name,
       then by alphabetical instructor-class name.  The sort must use only
       these scalar keys (never compare ParsedClass objects directly).
       Greedily walk the sorted list:
           if both classes are still unmatched:
               map ic ↔ sc, mark both as matched.

       Repeat the same greedy step for LOW pairs sorted by the same
       scalar-key order (distance, overlap, student name, instructor name)
       so ties have a fully deterministic order.

    3. Stage 2 – Attribute-driven matching.
       Consider only the *remaining* unmatched classes.
       For every (ic, sc) pair:
           overlap = percentage of ic's attributes whose name occurs in
           sc's attribute list.
       If ic has no attributes or overlap < 50 % the pair is discarded.
       Otherwise add it to the candidate list.
       Sort candidates by overlap descending; ties are broken by distance
       of the class names ascending, then by alphabetical student-class
       name, then by alphabetical instructor-class name.  The sort must use
       only these scalar keys (never compare ParsedClass objects directly).
       Greedily walk the list:
           if both classes are still unmatched:
               map ic ↔ sc, mark both as matched.

    4. Remainders
       Every still-unmatched instructor class → unmapped_instructor_classes.
       Every still-unmatched student class    → unmapped_student_classes.

    5. Return the mapping wrapped in a ParsedMapping.

    Note on ordering
    ----------------
    Stage 1 is ordered by Levenshtein distance, so an instructor class that
    has both a distance-0 and a distance-2 partner is guaranteed to be mapped
    to the distance-0 partner first.  Once a class is matched it is removed
    from the pool, so weaker candidates cannot "steal" a class that already
    has a better match.

    Tie breaking within the same tier uses attribute overlap as a secondary
    signal, then the alphabetical student-class name, then the alphabetical
    instructor-class name.  All tie-breakers are scalar values; comparing
    ParsedClass objects directly must never be relied on.
    """
    ...


def levenshtein_distance(a: str, b: str) -> int:
    """Classic DP implementation."""
    ...
