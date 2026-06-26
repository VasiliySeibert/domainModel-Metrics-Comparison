"""
Dataset integration tests for PlantUML parser.

These tests run the parser against the actual dataset to ensure
all PlantUML strings can be parsed successfully.
"""

import pytest
from pathlib import Path
from TestingMetrics.dummyMetric.Parser.parser import PlantUMLParser
from TestingMetrics.dummyMetric.Parser.test_runner import ParserTestRunner


class TestDatasetParsing:
    """Integration tests against the actual dataset."""

    @pytest.fixture
    def parser(self):
        """Create a strict parser instance."""
        return PlantUMLParser(strict=True)

    @pytest.fixture
    def runner(self, parser):
        """Create a test runner instance."""
        return ParserTestRunner(parser)

    def test_dataset_exists(self, runner):
        """Verify the dataset file exists."""
        assert runner.dataset_path.exists(), f"Dataset not found at {runner.dataset_path}"

    def test_can_load_dataset(self, runner):
        """Verify the dataset can be loaded."""
        models = runner.get_model_keys()
        assert len(models) > 0, "Dataset appears to be empty"
        # We expect 8 models
        assert len(models) == 8, f"Expected 8 models, got {len(models)}"

    def test_all_reference_models(self, runner):
        """
        Test that all reference models can be parsed.

        Reference models are typically cleaner and more consistent,
        so they should parse first.
        """
        report = runner.run_references_only(stop_on_failure=False)

        # Print failures for debugging
        for failure in report.all_failures:
            print(f"\nFailed: {failure.comparison_id}")
            print(f"Error: {failure.error_message}")
            if failure.failed_line:
                print(f"Line: {failure.failed_line}")

        assert report.failed == 0, (
            f"{report.failed}/{report.total} reference models failed to parse"
        )

    def test_all_generated_models(self, runner):
        """
        Test that all generated models can be parsed.

        Generated models may have more varied syntax patterns.
        """
        report = runner.run_all(stop_on_failure=False)

        # Filter to only generated (non-reference) failures
        generated_failures = [
            r for r in report.all_failures if not r.is_reference
        ]

        for failure in generated_failures:
            print(f"\nFailed: {failure.comparison_id}")
            print(f"Error: {failure.error_message}")

        assert len(generated_failures) == 0, (
            f"{len(generated_failures)} generated models failed to parse"
        )

    @pytest.mark.parametrize("model_key", [
        "LabTracker",
        "CelO",
        "TSS",
        "SHAS",
        "OTS",
        "Block",
        "TileO",
        "HBMS",
    ])
    def test_reference_model(self, runner, model_key):
        """Test each reference model individually."""
        try:
            result = runner.run_specific(model_key, 'reference')
            assert result.success, (
                f"Failed to parse {model_key} reference model: {result.error_message}"
            )
        except ValueError as e:
            # Model might not have reference PlantUML
            pytest.skip(f"No reference model for {model_key}: {e}")

    @pytest.mark.parametrize("model_key,setting", [
        ("LabTracker", "0shot"),
        ("LabTracker", "1shot_BTMS"),
        ("LabTracker", "CoT"),
        ("SHAS", "1shot_BTMS"),  # SHAS_0shot is known to be missing
        ("HBMS", "2shots"),
    ])
    def test_specific_generated_model(self, runner, model_key, setting):
        """Test specific generated models."""
        try:
            result = runner.run_specific(model_key, setting)
            assert result.success, (
                f"Failed to parse {model_key}_{setting}: {result.error_message}"
            )
        except ValueError as e:
            pytest.skip(f"No generated model for {model_key}/{setting}: {e}")


class TestParserCoverage:
    """Tests to verify parser handles all syntax patterns in the dataset."""

    @pytest.fixture
    def runner(self):
        return ParserTestRunner(PlantUMLParser(strict=True))

    def test_counts_are_reasonable(self, runner):
        """
        Verify that parsed element counts are reasonable.

        This is a sanity check that the parser is actually extracting content.
        """
        report = runner.run_all(stop_on_failure=False)

        total_classes = sum(r.num_classes for r in report.results if r.success)
        total_enums = sum(r.num_enums for r in report.results if r.success)
        total_relationships = sum(r.num_relationships for r in report.results if r.success)

        # We should have extracted a reasonable number of elements
        assert total_classes > 0 or total_relationships > 0, (
            "Parser didn't extract any classes or relationships"
        )

        print(f"\nParsed totals across all successful models:")
        print(f"  Classes: {total_classes}")
        print(f"  Enums: {total_enums}")
        print(f"  Relationships: {total_relationships}")
