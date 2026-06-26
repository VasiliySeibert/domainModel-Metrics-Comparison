"""
Metric Interface Definition

This module defines the standard interface (protocol) that all metrics must implement
to be compatible with the workflow system. Using Python's Protocol enables structural
subtyping (duck typing) - any class with matching methods will work.

The interface requires metrics to return three separate scores aligned with
human evaluation categories: Class, Attribute, and Association.
"""

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
    """
    Protocol that all metrics must implement for compatibility with the workflow.

    This protocol defines the required interface for metric implementations.
    Any class that provides these methods and properties will be accepted
    by the workflow system, enabling easy metric swapping.

    Example implementation:
        class MyMetric:
            @property
            def name(self) -> str:
                return "MyMetric"

            @property
            def version(self) -> str:
                return "1.0.0"

            def compute(
                self,
                reference_plantuml: str,
                generated_plantuml: str
            ) -> MetricResult:
                # Custom metric logic here
                return MetricResult(
                    class_score=0.8,
                    attribute_score=0.7,
                    association_score=0.6
                )
    """

    @property
    def name(self) -> str:
        """
        Return the metric name for identification.

        This name appears in output files and logs for tracking
        which metric was used to generate results.

        Returns:
            Human-readable metric name (e.g., "DummyMetric", "GraphSimilarity")
        """
        ...

    @property
    def version(self) -> str:
        """
        Return the metric version for reproducibility.

        Version tracking ensures results can be reproduced and
        compared across different metric versions.

        Returns:
            Semantic version string (e.g., "1.0.0", "2.1.3")
        """
        ...

    def compute(
        self,
        reference_plantuml: str,
        generated_plantuml: str
    ) -> MetricResult:
        """
        Compute similarity scores between reference and generated PlantUML models.

        This is the core method that implements the metric's comparison logic.
        It receives two PlantUML strings and must return scores for all three
        element types (class, attribute, association).

        Args:
            reference_plantuml: Ground truth PlantUML string.
                Format: "@startuml\\n...\\n@enduml"
            generated_plantuml: LLM-generated PlantUML string.
                Format: "@startuml\\n...\\n@enduml"

        Returns:
            MetricResult containing:
                - class_score (float): 0.0 to 1.0
                - attribute_score (float): 0.0 to 1.0
                - association_score (float): 0.0 to 1.0

        Raises:
            ValueError: If input PlantUML is invalid or cannot be parsed.
        """
        ...


def validate_metric(metric: object) -> bool:
    """
    Validate that an object implements the MetricProtocol.

    Args:
        metric: Object to validate

    Returns:
        True if metric implements the protocol, False otherwise
    """
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
