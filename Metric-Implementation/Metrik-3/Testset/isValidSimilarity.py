import math


def isValidSimilarity(s) -> bool:
    """
    Validate that a similarity value is a finite numeric value in [0, 1].

    A valid similarity value satisfies all of the following:
      1. It is an instance of ``int`` or ``float``.
      2. It is finite: ``not math.isnan(s)`` and ``not math.isinf(s)``.
      3. It lies within the closed interval ``[0.0, 1.0]``.

    The range semantics are:
      * ``0.0`` — the two compared objects are completely different.
      * ``1.0`` — the two compared objects are structurally identical.
      * Values strictly between ``0.0`` and ``1.0`` denote degrees of partial
        structural overlap.
    """
    if not isinstance(s, (int, float)):
        return False
    if not math.isfinite(s):
        return False
    if s < 0.0 or s > 1.0:
        return False
    return True


if __name__ == "__main__":
    # Minimal smoke test
    print(isValidSimilarity(0.5))   # Expected: True
    print(isValidSimilarity(-0.1))  # Expected: False
    print(isValidSimilarity(1.2))   # Expected: False
