"""
Tests for DummyMetric implementation.
"""

import pytest
from TestingMetrics.dummyMetric.dummy_metric import DummyMetric


class TestDummyMetric:
    """Test DummyMetric returns expected fixed values."""

    def test_default_values(self):
        """Test default values are 0.5."""
        metric = DummyMetric()
        result = metric.compute("anything", "anything")

        assert result["class_score"] == 0.5
        assert result["attribute_score"] == 0.5
        assert result["association_score"] == 0.5

    def test_custom_values(self):
        """Test custom initialization values."""
        metric = DummyMetric(
            class_score=0.8,
            attribute_score=0.6,
            association_score=0.4
        )
        result = metric.compute("anything", "anything")

        assert result["class_score"] == 0.8
        assert result["attribute_score"] == 0.6
        assert result["association_score"] == 0.4

    def test_ignores_input(self):
        """Test that input PlantUML is ignored (dummy behavior)."""
        metric = DummyMetric()
        result1 = metric.compute(
            "@startuml\nA -- B\n@enduml",
            "@startuml\nC -- D\n@enduml"
        )
        result2 = metric.compute(
            "@startuml\nX -- Y\n@enduml",
            "@startuml\nX -- Y\n@enduml"
        )

        assert result1 == result2

    def test_name_property(self):
        """Test name property."""
        metric = DummyMetric()
        assert metric.name == "DummyMetric"

    def test_version_property(self):
        """Test version property."""
        metric = DummyMetric()
        assert metric.version == "1.0.0"

    def test_repr(self):
        """Test string representation."""
        metric = DummyMetric(class_score=0.7, attribute_score=0.6, association_score=0.5)
        repr_str = repr(metric)

        assert "DummyMetric" in repr_str
        assert "0.7" in repr_str
        assert "0.6" in repr_str
        assert "0.5" in repr_str

    def test_invalid_score_type(self):
        """Test that non-numeric scores raise TypeError."""
        with pytest.raises(TypeError):
            DummyMetric(class_score="invalid")

    def test_invalid_score_range_high(self):
        """Test that scores > 1.0 raise ValueError."""
        with pytest.raises(ValueError):
            DummyMetric(class_score=1.5)

    def test_invalid_score_range_low(self):
        """Test that scores < 0.0 raise ValueError."""
        with pytest.raises(ValueError):
            DummyMetric(attribute_score=-0.5)

    def test_boundary_values(self):
        """Test boundary values (0.0 and 1.0) are accepted."""
        metric_zero = DummyMetric(
            class_score=0.0,
            attribute_score=0.0,
            association_score=0.0
        )
        result_zero = metric_zero.compute("a", "b")
        assert result_zero["class_score"] == 0.0

        metric_one = DummyMetric(
            class_score=1.0,
            attribute_score=1.0,
            association_score=1.0
        )
        result_one = metric_one.compute("a", "b")
        assert result_one["class_score"] == 1.0

    def test_integer_scores_converted_to_float(self):
        """Test that integer scores are converted to float."""
        metric = DummyMetric(class_score=1, attribute_score=0, association_score=1)
        result = metric.compute("a", "b")

        assert isinstance(result["class_score"], float)
        assert result["class_score"] == 1.0
