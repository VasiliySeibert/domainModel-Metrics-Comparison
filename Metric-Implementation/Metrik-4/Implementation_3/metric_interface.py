from typing import Protocol, TypedDict, runtime_checkable


class MetricResult(TypedDict):
    """
    Standardized metric output structure.

    All metrics must return scores for three element types to enable
    direct comparison with human evaluation F1 scores.

    Attributes:
        class_score: Similarity score for class detection (0.0 to 1.0).
            Corresponds to human evaluation "Class" category.
        attribute_score: Similarity score for attribute detection (0.0 to 1.0).
            Corresponds to human evaluation "Attribute" category.
        association_score: Similarity score for relationship detection (0.0 to 1.0).
            Corresponds to human evaluation "Association" category.
    """
    class_score: float
    attribute_score: float
    association_score: float


@runtime_checkable
class MetricProtocol(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def compute(
        self,
        reference_plantuml: str,
        generated_plantuml: str,
    ) -> MetricResult: ...


def validate_metric(metric: object) -> bool:
    return isinstance(metric, MetricProtocol)


def validate_metric_result(result: dict) -> bool:
    """
    Validate that a result dictionary has the required MetricResult structure.

    Args:
        result: Dictionary to validate

    Returns:
        True if result has valid structure and values, False otherwise
    """
    required_keys = {"class_score", "attribute_score", "association_score"}

    if not isinstance(result, dict):
        return False

    if not required_keys.issubset(result.keys()):
        return False

    for key in required_keys:
        value = result[key]
        if not isinstance(value, (int, float)):
            return False
        if not 0.0 <= value <= 1.0:
            return False

    return True