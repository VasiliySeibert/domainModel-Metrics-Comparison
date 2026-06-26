"""
Integration tests for MetricWorkflow.
"""

import json
import pytest
from pathlib import Path
import tempfile
import shutil

from TestingMetrics.dummyMetric.workflow import MetricWorkflow, run_workflow
from TestingMetrics.dummyMetric.dummy_metric import DummyMetric


class TestWorkflow:
    """Integration tests for the complete workflow."""

    @pytest.fixture
    def workflow(self):
        """Create workflow with dummy metric."""
        metric = DummyMetric()
        return MetricWorkflow(metric, verbose=False)

    def test_run_produces_results(self, workflow):
        """Test that run() produces valid results structure."""
        results = workflow.run()

        assert "metadata" in results
        assert "comparisons" in results
        assert "summary_statistics" in results
        assert "errors" in results

    def test_metadata_structure(self, workflow):
        """Test metadata is correctly populated."""
        results = workflow.run()
        metadata = results["metadata"]

        assert metadata["metric_name"] == "DummyMetric"
        assert metadata["metric_version"] == "1.0.0"
        assert "generated_timestamp" in metadata
        assert metadata["total_comparisons"] >= 39  # At least 39 valid
        assert metadata["successful_comparisons"] >= 39

    def test_comparison_structure(self, workflow):
        """Test individual comparison structure."""
        results = workflow.run()

        # Check at least one comparison exists
        assert len(results["comparisons"]) > 0

        # Check structure of first comparison
        comp_id = list(results["comparisons"].keys())[0]
        comp = results["comparisons"][comp_id]

        assert "comparison_id" in comp
        assert "model_key" in comp
        assert "model_full_name" in comp
        assert "setting" in comp
        assert "reference_plantuml" in comp
        assert "generated_plantuml" in comp
        assert "metric_results" in comp
        assert "human_metrics" in comp
        assert "delta" in comp
        assert "aggregated" in comp

    def test_metric_results_structure(self, workflow):
        """Test metric results have correct structure."""
        results = workflow.run()

        comp_id = list(results["comparisons"].keys())[0]
        metric_results = results["comparisons"][comp_id]["metric_results"]

        assert "class_score" in metric_results
        assert "attribute_score" in metric_results
        assert "association_score" in metric_results

        # All should be 0.5 for DummyMetric
        assert metric_results["class_score"] == 0.5
        assert metric_results["attribute_score"] == 0.5
        assert metric_results["association_score"] == 0.5

    def test_delta_calculation(self, workflow):
        """Test delta values are correctly calculated."""
        results = workflow.run()

        for comp in results["comparisons"].values():
            # Verify delta formula: metric - human
            expected_class_delta = (
                comp["metric_results"]["class_score"] -
                comp["human_metrics"]["Class"]["f1"]
            )
            assert abs(comp["delta"]["class_vs_f1"] - expected_class_delta) < 0.0001

    def test_summary_statistics(self, workflow):
        """Test summary statistics are computed."""
        results = workflow.run()
        summary = results["summary_statistics"]

        assert "mean_class_delta_f1" in summary
        assert "mean_attribute_delta_f1" in summary
        assert "mean_association_delta_f1" in summary
        assert "n_comparisons" in summary
        assert summary["n_comparisons"] >= 39

    def test_save_creates_file(self, workflow):
        """Test that save creates a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow.run()
            output_path = workflow.save(f"{tmpdir}/test_results.json")

            assert output_path.exists()
            assert output_path.suffix == ".json"

            # Verify it's valid JSON
            with open(output_path) as f:
                data = json.load(f)
            assert "metadata" in data
            assert "comparisons" in data

    def test_save_without_run_raises_error(self, workflow):
        """Test that save() without run() raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Must call run"):
            workflow.save("output.json")

    def test_run_twice_raises_error(self, workflow):
        """Test that running workflow twice raises RuntimeError."""
        workflow.run()
        with pytest.raises(RuntimeError, match="already been run"):
            workflow.run()

    def test_results_property(self, workflow):
        """Test results property."""
        assert workflow.results is None
        workflow.run()
        assert workflow.results is not None
        assert "comparisons" in workflow.results

    def test_errors_property(self, workflow):
        """Test errors property."""
        assert workflow.errors == []
        workflow.run()
        # May or may not have errors depending on dataset
        assert isinstance(workflow.errors, list)


class TestRunWorkflowFunction:
    """Test run_workflow convenience function."""

    def test_run_workflow(self):
        """Test run_workflow function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metric = DummyMetric()
            results = run_workflow(
                metric,
                output_filename=f"{tmpdir}/results.json",
                verbose=False
            )

            assert "metadata" in results
            assert "comparisons" in results
            assert Path(f"{tmpdir}/results.json").exists()


class TestWorkflowWithCustomMetric:
    """Test workflow with custom metric implementations."""

    def test_invalid_metric_raises_error(self):
        """Test that invalid metric raises TypeError."""
        with pytest.raises(TypeError, match="MetricProtocol"):
            MetricWorkflow("not a metric")

    def test_custom_metric_values(self):
        """Test workflow with custom metric values."""
        metric = DummyMetric(
            class_score=0.9,
            attribute_score=0.8,
            association_score=0.7
        )
        workflow = MetricWorkflow(metric, verbose=False)
        results = workflow.run()

        comp_id = list(results["comparisons"].keys())[0]
        metric_results = results["comparisons"][comp_id]["metric_results"]

        assert metric_results["class_score"] == 0.9
        assert metric_results["attribute_score"] == 0.8
        assert metric_results["association_score"] == 0.7


class TestComparisonIds:
    """Test comparison ID format and content."""

    def test_comparison_id_format(self):
        """Test that comparison IDs have expected format."""
        workflow = MetricWorkflow(DummyMetric(), verbose=False)
        results = workflow.run()

        for comp_id in results["comparisons"].keys():
            # Should be in format model_setting
            parts = comp_id.rsplit("_", 1)
            assert len(parts) >= 1

    def test_expected_comparison_count(self):
        """Test that we get expected number of comparisons."""
        workflow = MetricWorkflow(DummyMetric(), verbose=False)
        results = workflow.run()

        # 8 models * 5 settings = 40, minus SHAS_0shot = 39
        assert len(results["comparisons"]) >= 39
        assert len(results["comparisons"]) <= 40
