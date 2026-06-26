"""
Workflow Orchestrator Module

This module provides the main workflow orchestrator that coordinates
data loading, metric computation, delta calculation, and result saving.

Example usage:
    from TestingMetrics.dummyMetric import MetricWorkflow, DummyMetric

    metric = DummyMetric()
    workflow = MetricWorkflow(metric)
    results = workflow.run()
    workflow.save()  # Saves to output/results.json
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .metric_interface import MetricProtocol, validate_metric
from .data_loader import DataLoader, ComparisonData
from .delta_calculator import DeltaCalculator
from .results_writer import ResultsWriter


# Default output directory relative to module
MODULE_DIR = Path(__file__).parent
DEFAULT_OUTPUT_DIR = MODULE_DIR / "output"


class MetricWorkflow:
    """
    Orchestrates the complete metric evaluation workflow.

    This class coordinates:
    1. Loading dataset from combined-data.json
    2. Iterating through all model/setting comparisons
    3. Computing metric scores for each comparison
    4. Calculating deltas against human evaluation
    5. Computing summary statistics
    6. Saving results to JSON

    Attributes:
        metric: The metric implementation to evaluate
        data_loader: DataLoader instance for accessing dataset
        delta_calculator: DeltaCalculator for computing deltas
        verbose: Whether to print progress information
        results: Computed results (available after run())

    Example:
        # Basic usage
        from TestingMetrics.dummyMetric import MetricWorkflow, DummyMetric

        metric = DummyMetric()
        workflow = MetricWorkflow(metric)
        results = workflow.run()
        workflow.save()

        # With custom options
        workflow = MetricWorkflow(
            metric=DummyMetric(),
            dataset_path="custom/path/data.json",
            verbose=True
        )
        workflow.run()
        workflow.save("custom_output.json")
    """

    def __init__(
        self,
        metric: MetricProtocol,
        dataset_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        verbose: bool = True
    ):
        """
        Initialize the workflow.

        Args:
            metric: Metric implementation that follows MetricProtocol
            dataset_path: Path to combined-data.json (None uses default)
            output_dir: Directory for output files (None uses default)
            verbose: Whether to print progress information

        Raises:
            TypeError: If metric doesn't implement MetricProtocol
        """
        if not validate_metric(metric):
            raise TypeError(
                f"metric must implement MetricProtocol. "
                f"Got {type(metric).__name__} which is missing required methods."
            )

        self.metric = metric
        self.data_loader = DataLoader(dataset_path)
        self.delta_calculator = DeltaCalculator()
        self.results_writer = ResultsWriter(output_dir)
        self.verbose = verbose

        self._results: Optional[Dict[str, Any]] = None
        self._errors: List[Dict[str, Any]] = []

    def run(self) -> Dict[str, Any]:
        """
        Execute the full workflow.

        Steps:
        1. Load dataset
        2. Iterate through all comparisons
        3. Compute metrics for each comparison
        4. Calculate deltas
        5. Generate summary statistics

        Returns:
            Complete results dictionary containing:
                - metadata: Workflow execution metadata
                - comparisons: All comparison results
                - summary_statistics: Aggregated statistics
                - errors: Any errors encountered

        Raises:
            FileNotFoundError: If dataset file doesn't exist
            RuntimeError: If workflow has already been run
        """
        if self._results is not None:
            raise RuntimeError(
                "Workflow has already been run. Create a new instance to run again."
            )

        self._log(f"Starting workflow with metric: {self.metric.name} v{self.metric.version}")

        # Load dataset
        self._log("Loading dataset...")
        self.data_loader.load()
        self._log(f"Found {self.data_loader.total_comparisons} valid comparisons")

        # Process comparisons
        comparisons: Dict[str, Dict[str, Any]] = {}
        successful = 0
        failed = 0

        for comparison in self.data_loader.iter_comparisons():
            try:
                result = self._process_comparison(comparison)
                comparisons[comparison.comparison_id] = result
                successful += 1
                self._log(f"  Processed: {comparison.comparison_id}")
            except Exception as e:
                self._errors.append({
                    "comparison_id": comparison.comparison_id,
                    "error_type": type(e).__name__,
                    "message": str(e)
                })
                failed += 1
                self._log(f"  FAILED: {comparison.comparison_id} - {e}")

        self._log(f"Processed {successful} comparisons, {failed} failed")

        # Compute summary statistics
        self._log("Computing summary statistics...")
        summary = self.delta_calculator.compute_summary_statistics(comparisons)

        # Build results
        self._results = {
            "metadata": self._build_metadata(successful, failed),
            "comparisons": comparisons,
            "summary_statistics": summary,
            "errors": self._errors
        }

        self._log("Workflow complete!")
        return self._results

    def _process_comparison(self, comparison: ComparisonData) -> Dict[str, Any]:
        """
        Process a single comparison.

        Args:
            comparison: ComparisonData object

        Returns:
            Dictionary with comparison results
        """
        # Compute metric
        metric_results = self.metric.compute(
            comparison.reference_plantuml,
            comparison.generated_plantuml
        )

        # Convert to dict if needed
        metric_dict = dict(metric_results)

        # Compute delta
        delta = self.delta_calculator.compute_comparison_delta(
            metric_dict,
            comparison.human_metrics
        )

        # Compute aggregated scores
        aggregated = self.delta_calculator.compute_aggregated(
            metric_dict,
            comparison.human_metrics
        )

        return {
            "comparison_id": comparison.comparison_id,
            "model_key": comparison.model_key,
            "model_full_name": comparison.model_full_name,
            "setting": comparison.setting,
            "reference_plantuml": comparison.reference_plantuml,
            "generated_plantuml": comparison.generated_plantuml,
            "metric_results": metric_dict,
            "human_metrics": comparison.human_metrics,
            "delta": delta.to_dict(),
            "aggregated": aggregated.to_dict()
        }

    def _build_metadata(self, successful: int, failed: int) -> Dict[str, Any]:
        """
        Build metadata section.

        Args:
            successful: Number of successfully processed comparisons
            failed: Number of failed comparisons

        Returns:
            Metadata dictionary
        """
        return {
            "generated_timestamp": datetime.now().isoformat(),
            "metric_name": self.metric.name,
            "metric_version": self.metric.version,
            "dataset_source": str(self.data_loader.dataset_path),
            "total_comparisons": successful + failed,
            "successful_comparisons": successful,
            "failed_comparisons": failed
        }

    def save(self, filename: str = "results.json") -> Path:
        """
        Save results to JSON file.

        Args:
            filename: Output filename (relative to output_dir or absolute)

        Returns:
            Path to saved file

        Raises:
            RuntimeError: If run() hasn't been called yet
        """
        if self._results is None:
            raise RuntimeError("Must call run() before save()")

        output_path = self.results_writer.write(self._results, filename)
        self._log(f"Results saved to: {output_path}")
        return output_path

    @property
    def results(self) -> Optional[Dict[str, Any]]:
        """
        Access computed results.

        Returns:
            Results dictionary if run() has been called, None otherwise
        """
        return self._results

    @property
    def errors(self) -> List[Dict[str, Any]]:
        """
        Access any errors encountered during processing.

        Returns:
            List of error dictionaries
        """
        return self._errors

    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)


def run_workflow(
    metric: MetricProtocol,
    output_filename: str = "results.json",
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to run the complete workflow.

    This function creates a MetricWorkflow instance, runs it, saves the
    results, and returns them.

    Args:
        metric: Metric implementation to evaluate
        output_filename: Output filename for results
        verbose: Whether to print progress

    Returns:
        Complete results dictionary

    Example:
        from TestingMetrics.dummyMetric import DummyMetric, run_workflow

        results = run_workflow(DummyMetric())
    """
    workflow = MetricWorkflow(metric, verbose=verbose)
    results = workflow.run()
    workflow.save(output_filename)
    return results
