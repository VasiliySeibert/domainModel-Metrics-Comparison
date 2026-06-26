"""
Tests for delta calculation functions.
"""

import pytest
from TestingMetrics.dummyMetric.delta_calculator import (
    DeltaCalculator,
    DeltaResult,
    AggregatedResult,
    compute_single_delta
)


class TestDeltaCalculator:
    """Test delta calculation logic."""

    def test_compute_comparison_delta(self):
        """Test single comparison delta calculation."""
        metric_results = {
            "class_score": 0.7,
            "attribute_score": 0.6,
            "association_score": 0.5
        }
        human_metrics = {
            "Class": {"precision": 0.9, "recall": 0.5, "f1": 0.65},
            "Attribute": {"precision": 0.8, "recall": 0.6, "f1": 0.69},
            "Association": {"precision": 0.4, "recall": 0.3, "f1": 0.34}
        }

        delta = DeltaCalculator.compute_comparison_delta(metric_results, human_metrics)

        # Check F1 deltas
        assert delta.class_vs_f1 == pytest.approx(0.05, abs=0.001)
        assert delta.attribute_vs_f1 == pytest.approx(-0.09, abs=0.001)
        assert delta.association_vs_f1 == pytest.approx(0.16, abs=0.001)

        # Check precision deltas
        assert delta.class_vs_precision == pytest.approx(-0.2, abs=0.001)
        assert delta.attribute_vs_precision == pytest.approx(-0.2, abs=0.001)
        assert delta.association_vs_precision == pytest.approx(0.1, abs=0.001)

        # Check recall deltas
        assert delta.class_vs_recall == pytest.approx(0.2, abs=0.001)
        assert delta.attribute_vs_recall == pytest.approx(0.0, abs=0.001)
        assert delta.association_vs_recall == pytest.approx(0.2, abs=0.001)

    def test_compute_comparison_delta_to_dict(self):
        """Test DeltaResult.to_dict() method."""
        metric_results = {
            "class_score": 0.5,
            "attribute_score": 0.5,
            "association_score": 0.5
        }
        human_metrics = {
            "Class": {"precision": 0.5, "recall": 0.5, "f1": 0.5},
            "Attribute": {"precision": 0.5, "recall": 0.5, "f1": 0.5},
            "Association": {"precision": 0.5, "recall": 0.5, "f1": 0.5}
        }

        delta = DeltaCalculator.compute_comparison_delta(metric_results, human_metrics)
        delta_dict = delta.to_dict()

        assert isinstance(delta_dict, dict)
        assert "class_vs_f1" in delta_dict
        assert "attribute_vs_f1" in delta_dict
        assert "association_vs_f1" in delta_dict
        assert all(v == pytest.approx(0.0) for v in delta_dict.values())

    def test_compute_aggregated(self):
        """Test aggregated score calculation."""
        metric_results = {
            "class_score": 0.6,
            "attribute_score": 0.6,
            "association_score": 0.6
        }
        human_metrics = {
            "Class": {"precision": 0.9, "recall": 0.4, "f1": 0.5},
            "Attribute": {"precision": 0.8, "recall": 0.5, "f1": 0.5},
            "Association": {"precision": 0.5, "recall": 0.5, "f1": 0.5}
        }

        aggregated = DeltaCalculator.compute_aggregated(metric_results, human_metrics)

        assert aggregated.metric_average == pytest.approx(0.6, abs=0.001)
        assert aggregated.human_f1_average == pytest.approx(0.5, abs=0.001)
        assert aggregated.overall_delta == pytest.approx(0.1, abs=0.001)

    def test_compute_aggregated_to_dict(self):
        """Test AggregatedResult.to_dict() method."""
        metric_results = {
            "class_score": 0.5,
            "attribute_score": 0.5,
            "association_score": 0.5
        }
        human_metrics = {
            "Class": {"f1": 0.5},
            "Attribute": {"f1": 0.5},
            "Association": {"f1": 0.5}
        }

        aggregated = DeltaCalculator.compute_aggregated(metric_results, human_metrics)
        agg_dict = aggregated.to_dict()

        assert isinstance(agg_dict, dict)
        assert "metric_average" in agg_dict
        assert "human_f1_average" in agg_dict
        assert "overall_delta" in agg_dict

    def test_compute_summary_statistics(self):
        """Test summary statistics computation."""
        comparisons = {
            "comp1": {
                "metric_results": {
                    "class_score": 0.6,
                    "attribute_score": 0.6,
                    "association_score": 0.6
                },
                "human_metrics": {
                    "Class": {"f1": 0.5},
                    "Attribute": {"f1": 0.5},
                    "Association": {"f1": 0.5}
                },
                "delta": {
                    "class_vs_f1": 0.1,
                    "attribute_vs_f1": 0.1,
                    "association_vs_f1": 0.1
                }
            },
            "comp2": {
                "metric_results": {
                    "class_score": 0.4,
                    "attribute_score": 0.4,
                    "association_score": 0.4
                },
                "human_metrics": {
                    "Class": {"f1": 0.5},
                    "Attribute": {"f1": 0.5},
                    "Association": {"f1": 0.5}
                },
                "delta": {
                    "class_vs_f1": -0.1,
                    "attribute_vs_f1": -0.1,
                    "association_vs_f1": -0.1
                }
            }
        }

        summary = DeltaCalculator.compute_summary_statistics(comparisons)

        assert summary["n_comparisons"] == 2
        assert summary["mean_class_delta_f1"] == pytest.approx(0.0, abs=0.001)
        assert summary["mean_attribute_delta_f1"] == pytest.approx(0.0, abs=0.001)
        assert summary["mean_association_delta_f1"] == pytest.approx(0.0, abs=0.001)

    def test_compute_summary_statistics_empty(self):
        """Test summary statistics with empty input."""
        summary = DeltaCalculator.compute_summary_statistics({})

        assert summary["n_comparisons"] == 0
        assert summary["mean_class_delta_f1"] is None


class TestComputeSingleDelta:
    """Test compute_single_delta helper function."""

    def test_positive_delta(self):
        """Test positive delta (overestimate)."""
        delta = compute_single_delta(0.7, 0.5)
        assert delta == pytest.approx(0.2)

    def test_negative_delta(self):
        """Test negative delta (underestimate)."""
        delta = compute_single_delta(0.3, 0.5)
        assert delta == pytest.approx(-0.2)

    def test_zero_delta(self):
        """Test zero delta (perfect match)."""
        delta = compute_single_delta(0.5, 0.5)
        assert delta == pytest.approx(0.0)


class TestDeltaResult:
    """Test DeltaResult dataclass."""

    def test_create_delta_result(self):
        """Test creating DeltaResult."""
        delta = DeltaResult(
            class_vs_f1=0.1,
            attribute_vs_f1=0.2,
            association_vs_f1=0.3,
            class_vs_precision=-0.1,
            class_vs_recall=0.1,
            attribute_vs_precision=-0.2,
            attribute_vs_recall=0.2,
            association_vs_precision=-0.3,
            association_vs_recall=0.3
        )

        assert delta.class_vs_f1 == 0.1
        assert delta.attribute_vs_f1 == 0.2
        assert delta.association_vs_f1 == 0.3


class TestAggregatedResult:
    """Test AggregatedResult dataclass."""

    def test_create_aggregated_result(self):
        """Test creating AggregatedResult."""
        agg = AggregatedResult(
            metric_average=0.6,
            human_f1_average=0.5,
            overall_delta=0.1
        )

        assert agg.metric_average == 0.6
        assert agg.human_f1_average == 0.5
        assert agg.overall_delta == 0.1
