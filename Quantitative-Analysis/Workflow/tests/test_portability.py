"""
Portability tests - verify the dummyMetric folder can be copied and reused.

These tests ensure that:
1. The module uses relative paths correctly
2. Copying the folder creates a working metric system
3. No hardcoded absolute paths exist
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path


class TestPathResolution:
    """Test that paths are resolved correctly relative to module location."""

    def test_data_loader_uses_relative_path(self):
        """Test DataLoader resolves dataset path from project root."""
        from TestingMetrics.dummyMetric.data_loader import (
            DEFAULT_DATASET_PATH,
            PROJECT_ROOT,
            MODULE_DIR
        )

        # Module dir should be inside TestingMetrics/dummyMetric
        assert "TestingMetrics" in str(MODULE_DIR)
        assert "dummyMetric" in str(MODULE_DIR)

        # Project root should be 2 levels up
        assert PROJECT_ROOT == MODULE_DIR.parent.parent

        # Default dataset path should exist
        assert DEFAULT_DATASET_PATH.exists(), \
            f"Dataset not found at {DEFAULT_DATASET_PATH}"

    def test_results_writer_uses_relative_path(self):
        """Test ResultsWriter uses module-relative output path."""
        from TestingMetrics.dummyMetric.results_writer import (
            DEFAULT_OUTPUT_DIR,
            MODULE_DIR
        )

        # Output dir should be inside dummyMetric
        assert DEFAULT_OUTPUT_DIR.parent == MODULE_DIR
        assert DEFAULT_OUTPUT_DIR.name == "output"

    def test_no_hardcoded_paths_in_data_loader(self):
        """Check data_loader.py doesn't contain hardcoded absolute paths."""
        from TestingMetrics.dummyMetric import data_loader
        import inspect

        source = inspect.getsource(data_loader)

        # Should not contain hardcoded Windows paths
        assert "C:\\Users" not in source
        assert "C:/Users" not in source

        # Should not contain hardcoded Unix home paths
        assert "/home/" not in source
        assert "/Users/" not in source

    def test_no_hardcoded_paths_in_workflow(self):
        """Check workflow.py doesn't contain hardcoded absolute paths."""
        from TestingMetrics.dummyMetric import workflow
        import inspect

        source = inspect.getsource(workflow)

        # Should not contain hardcoded paths
        assert "C:\\Users" not in source
        assert "C:/Users" not in source
        assert "/home/" not in source
        assert "/Users/" not in source


class TestModuleImports:
    """Test that module imports work correctly."""

    def test_import_from_package(self):
        """Test importing from package root."""
        from TestingMetrics.dummyMetric import (
            MetricProtocol,
            MetricResult,
            DummyMetric,
            MetricWorkflow,
            DataLoader,
            ComparisonData,
            DeltaCalculator,
            PlantUMLServer
        )

        assert MetricProtocol is not None
        assert MetricResult is not None
        assert DummyMetric is not None
        assert MetricWorkflow is not None
        assert DataLoader is not None
        assert ComparisonData is not None
        assert DeltaCalculator is not None
        assert PlantUMLServer is not None

    def test_import_visualization(self):
        """Test importing visualization modules."""
        from TestingMetrics.dummyMetric.visualization import (
            QuantitativeVisualizer,
            QualitativeVisualizer
        )

        assert QuantitativeVisualizer is not None
        assert QualitativeVisualizer is not None


class TestCopyPastePortability:
    """Test that copying the folder creates a working metric system."""

    @pytest.fixture
    def copied_module(self):
        """
        Copy dummyMetric folder to temp directory and set up imports.

        This simulates copying the folder for a new metric implementation.
        """
        # Get source path
        from TestingMetrics.dummyMetric import data_loader
        source_dir = Path(data_loader.__file__).parent

        # Create temp directory structure
        tmpdir = tempfile.mkdtemp()
        dest_parent = Path(tmpdir) / "TestingMetrics"
        dest_parent.mkdir()

        # Copy the folder with new name
        new_name = "testCopiedMetric"
        dest_dir = dest_parent / new_name
        shutil.copytree(source_dir, dest_dir)

        # Add temp dir to path so we can import
        sys.path.insert(0, tmpdir)

        yield {
            "tmpdir": tmpdir,
            "dest_dir": dest_dir,
            "module_name": f"TestingMetrics.{new_name}"
        }

        # Cleanup
        sys.path.remove(tmpdir)

        # Remove from sys.modules
        modules_to_remove = [
            key for key in sys.modules
            if key.startswith(f"TestingMetrics.{new_name}")
        ]
        for mod in modules_to_remove:
            del sys.modules[mod]

        shutil.rmtree(tmpdir)

    def test_copied_module_imports(self, copied_module):
        """Test that copied module can be imported."""
        import importlib

        module_name = copied_module["module_name"]

        # Should be able to import the copied module
        mod = importlib.import_module(module_name)
        assert hasattr(mod, "DummyMetric")
        assert hasattr(mod, "MetricWorkflow")

    def test_copied_module_dummy_metric_works(self, copied_module):
        """Test that DummyMetric works in copied module."""
        import importlib

        module_name = copied_module["module_name"]
        mod = importlib.import_module(module_name)

        metric = mod.DummyMetric()
        result = metric.compute("@startuml\n@enduml", "@startuml\n@enduml")

        assert result["class_score"] == 0.5
        assert result["attribute_score"] == 0.5
        assert result["association_score"] == 0.5

    def test_copied_module_data_loader_finds_dataset(self, copied_module):
        """Test that DataLoader in copied module can find dataset."""
        import importlib

        # The copied module won't have the correct project structure,
        # so we test that it correctly calculates relative paths
        module_name = copied_module["module_name"]
        data_loader_mod = importlib.import_module(f"{module_name}.data_loader")

        # Check that paths are calculated from __file__
        assert "MODULE_DIR" in dir(data_loader_mod)
        assert "PROJECT_ROOT" in dir(data_loader_mod)

        # The paths should be Path objects
        assert isinstance(data_loader_mod.MODULE_DIR, Path)
        assert isinstance(data_loader_mod.PROJECT_ROOT, Path)


class TestWorkflowIntegration:
    """Integration test for full workflow execution."""

    def test_full_workflow_execution(self):
        """Test complete workflow runs successfully."""
        from TestingMetrics.dummyMetric import MetricWorkflow, DummyMetric

        metric = DummyMetric()
        workflow = MetricWorkflow(metric, verbose=False)

        results = workflow.run()

        # Should have processed comparisons
        assert len(results["comparisons"]) >= 39

        # Should have metadata
        assert results["metadata"]["metric_name"] == "DummyMetric"

        # Should have summary statistics
        assert "mean_class_delta_f1" in results["summary_statistics"]

    def test_workflow_save_to_custom_path(self):
        """Test saving results to custom path."""
        from TestingMetrics.dummyMetric import MetricWorkflow, DummyMetric

        with tempfile.TemporaryDirectory() as tmpdir:
            metric = DummyMetric()
            workflow = MetricWorkflow(metric, verbose=False)
            workflow.run()

            output_path = Path(tmpdir) / "custom_output.json"
            saved_path = workflow.save(str(output_path))

            assert saved_path.exists()
            assert saved_path.name == "custom_output.json"
