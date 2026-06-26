"""
Tests for metric interface protocol compliance.
"""

import pytest
from TestingMetrics.dummyMetric.metric_interface import (
    MetricProtocol,
    MetricResult,
    validate_metric,
    validate_metric_result
)
from TestingMetrics.dummyMetric.dummy_metric import DummyMetric


class TestMetricProtocol:
    """Test that DummyMetric implements MetricProtocol correctly."""

    def test_dummy_metric_is_protocol_compliant(self):
        """Verify DummyMetric satisfies MetricProtocol."""
        metric = DummyMetric()

        # Check required properties exist
        assert hasattr(metric, "name")
        assert hasattr(metric, "version")
        assert hasattr(metric, "compute")

        # Check types
        assert isinstance(metric.name, str)
        assert isinstance(metric.version, str)

    def test_compute_returns_metric_result(self):
        """Verify compute returns properly structured MetricResult."""
        metric = DummyMetric()
        result = metric.compute(
            "@startuml\nA -- B\n@enduml",
            "@startuml\nA -- C\n@enduml"
        )

        assert "class_score" in result
        assert "attribute_score" in result
        assert "association_score" in result

        # Values in valid range
        assert 0.0 <= result["class_score"] <= 1.0
        assert 0.0 <= result["attribute_score"] <= 1.0
        assert 0.0 <= result["association_score"] <= 1.0

    def test_validate_metric_with_valid_metric(self):
        """Test validate_metric returns True for valid metric."""
        metric = DummyMetric()
        assert validate_metric(metric) is True

    def test_validate_metric_with_invalid_object(self):
        """Test validate_metric returns False for invalid object."""
        assert validate_metric("not a metric") is False
        assert validate_metric(123) is False
        assert validate_metric(None) is False

    def test_validate_metric_with_partial_implementation(self):
        """Test validate_metric with object missing required methods."""
        class PartialMetric:
            @property
            def name(self):
                return "Partial"
            # Missing version and compute

        partial = PartialMetric()
        assert validate_metric(partial) is False


class TestMetricResult:
    """Test MetricResult structure."""

    def test_create_metric_result(self):
        """Test creating MetricResult TypedDict."""
        result = MetricResult(
            class_score=0.8,
            attribute_score=0.7,
            association_score=0.6
        )

        assert result["class_score"] == 0.8
        assert result["attribute_score"] == 0.7
        assert result["association_score"] == 0.6


class TestValidateMetricResult:
    """Test validate_metric_result function."""

    def test_valid_result(self):
        """Test with valid result structure."""
        result = {
            "class_score": 0.5,
            "attribute_score": 0.5,
            "association_score": 0.5
        }
        assert validate_metric_result(result) is True

    def test_invalid_missing_key(self):
        """Test with missing required key."""
        result = {
            "class_score": 0.5,
            "attribute_score": 0.5
            # Missing association_score
        }
        assert validate_metric_result(result) is False

    def test_invalid_value_type(self):
        """Test with non-numeric value."""
        result = {
            "class_score": "not a number",
            "attribute_score": 0.5,
            "association_score": 0.5
        }
        assert validate_metric_result(result) is False

    def test_invalid_value_range(self):
        """Test with value outside valid range."""
        result = {
            "class_score": 1.5,  # Greater than 1
            "attribute_score": 0.5,
            "association_score": 0.5
        }
        assert validate_metric_result(result) is False

        result2 = {
            "class_score": -0.5,  # Less than 0
            "attribute_score": 0.5,
            "association_score": 0.5
        }
        assert validate_metric_result(result2) is False

    def test_invalid_not_dict(self):
        """Test with non-dictionary input."""
        assert validate_metric_result("not a dict") is False
        assert validate_metric_result([0.5, 0.5, 0.5]) is False
