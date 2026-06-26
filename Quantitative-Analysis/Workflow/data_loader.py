"""
Data Loader Module

This module provides functionality to load and iterate through the dataset
of PlantUML model comparisons. It handles the combined-data.json file and
provides convenient access to individual comparisons.

Path Resolution:
    The dataset path is resolved relative to the project root, making this
    module portable when the dummyMetric folder is copied for new metrics.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, List, Dict, Any


# Resolve project root from module location
# Structure: TestingMetrics/dummyMetric/data_loader.py -> ../../ = project root
MODULE_DIR = Path(__file__).parent
PROJECT_ROOT = MODULE_DIR.parent.parent
DEFAULT_DATASET_PATH = PROJECT_ROOT / "Dataset" / "combined-data.json"


@dataclass
class ComparisonData:
    """
    Container for a single comparison's data.

    This dataclass holds all information needed to evaluate a metric
    on one comparison (model + setting combination).

    Attributes:
        comparison_id: Unique identifier in format "{model_key}_{setting}"
        model_key: Short model name (e.g., "LabTracker")
        model_full_name: Full descriptive name (e.g., "Lab Requisition Management System")
        setting: LLM prompting strategy (e.g., "0shot", "1shot_BTMS")
        reference_plantuml: Ground truth PlantUML string
        generated_plantuml: LLM-generated PlantUML string
        human_metrics: Human evaluation metrics dictionary with structure:
            {
                "Class": {"precision": float, "recall": float, "f1": float},
                "Attribute": {"precision": float, "recall": float, "f1": float},
                "Association": {"precision": float, "recall": float, "f1": float}
            }
    """
    comparison_id: str
    model_key: str
    model_full_name: str
    setting: str
    reference_plantuml: str
    generated_plantuml: str
    human_metrics: Dict[str, Dict[str, float]]


class DataLoader:
    """
    Load and iterate through the dataset of PlantUML model comparisons.

    This class provides convenient access to the combined-data.json file,
    allowing iteration through all comparisons and retrieval of specific
    comparisons by ID.

    Example:
        loader = DataLoader()
        loader.load()

        # Iterate through all valid comparisons
        for comparison in loader.iter_comparisons():
            print(f"Processing {comparison.comparison_id}")

        # Get specific comparison
        comp = loader.get_comparison("LabTracker_0shot")
        if comp:
            print(comp.reference_plantuml)

    Attributes:
        dataset_path: Path to the combined-data.json file
        models: List of model keys after loading
        settings: List of setting keys after loading
    """

    def __init__(self, dataset_path: Optional[str] = None):
        """
        Initialize the data loader.

        Args:
            dataset_path: Path to combined-data.json. If None, uses default
                         path relative to project root (Dataset/combined-data.json)
        """
        if dataset_path is None:
            self.dataset_path = DEFAULT_DATASET_PATH
        else:
            self.dataset_path = Path(dataset_path)

        self._data: Optional[Dict[str, Any]] = None
        self._warnings: List[str] = []

    def load(self) -> Dict[str, Any]:
        """
        Load dataset from JSON file.

        Returns:
            Complete dataset dictionary

        Raises:
            FileNotFoundError: If dataset file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
        """
        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self.dataset_path}. "
                f"Expected location: {DEFAULT_DATASET_PATH}"
            )

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        # Extract warnings from metadata
        metadata = self._data.get("metadata", {})
        self._warnings = metadata.get("validation_warnings", [])

        return self._data

    def validate(self) -> List[str]:
        """
        Validate dataset structure and return list of warnings.

        Returns:
            List of validation warning messages

        Raises:
            RuntimeError: If load() hasn't been called yet
        """
        if self._data is None:
            raise RuntimeError("Must call load() before validate()")

        warnings = list(self._warnings)  # Copy existing warnings

        # Check required top-level keys
        if "models" not in self._data:
            warnings.append("Missing 'models' key in dataset")

        if "metadata" not in self._data:
            warnings.append("Missing 'metadata' key in dataset")

        # Validate each model
        for model_key, model_data in self._data.get("models", {}).items():
            if "reference_plantuml" not in model_data:
                warnings.append(f"{model_key}: Missing reference_plantuml")
            if "generated_plantuml" not in model_data:
                warnings.append(f"{model_key}: Missing generated_plantuml")
            if "metrics" not in model_data:
                warnings.append(f"{model_key}: Missing metrics")

        return warnings

    def iter_comparisons(self) -> Iterator[ComparisonData]:
        """
        Yield ComparisonData for each valid model/setting combination.

        Skips comparisons where data is missing (e.g., SHAS_0shot).
        Invalid comparisons are logged but not yielded.

        Yields:
            ComparisonData objects for each valid comparison

        Raises:
            RuntimeError: If load() hasn't been called yet
        """
        if self._data is None:
            raise RuntimeError("Must call load() before iter_comparisons()")

        models = self._data.get("models", {})
        metadata = self._data.get("metadata", {})
        settings = metadata.get("settings_included", [
            "0shot", "1shot_BTMS", "1shot_H2S", "2shots", "CoT"
        ])

        for model_key, model_data in models.items():
            for setting in settings:
                comparison_id = f"{model_key}_{setting}"

                # Get generated PlantUML for this setting
                generated = model_data.get("generated_plantuml", {}).get(setting)
                if generated is None:
                    # Skip missing data (e.g., SHAS_0shot)
                    continue

                # Get human metrics for this setting
                metrics = model_data.get("metrics", {}).get(setting)
                if metrics is None:
                    continue

                yield ComparisonData(
                    comparison_id=comparison_id,
                    model_key=model_key,
                    model_full_name=model_data.get("full_name", model_key),
                    setting=setting,
                    reference_plantuml=model_data.get("reference_plantuml", ""),
                    generated_plantuml=generated,
                    human_metrics=metrics
                )

    def get_comparison(self, comparison_id: str) -> Optional[ComparisonData]:
        """
        Get a specific comparison by ID.

        Args:
            comparison_id: Comparison ID in format "{model_key}_{setting}"

        Returns:
            ComparisonData if found, None if not found or invalid

        Raises:
            RuntimeError: If load() hasn't been called yet
            ValueError: If comparison_id format is invalid
        """
        if self._data is None:
            raise RuntimeError("Must call load() before get_comparison()")

        # Parse comparison ID
        parts = comparison_id.rsplit("_", 1)
        if len(parts) != 2:
            # Try to find by splitting at known settings
            for setting in ["0shot", "1shot_BTMS", "1shot_H2S", "2shots", "CoT"]:
                if comparison_id.endswith(f"_{setting}"):
                    model_key = comparison_id[:-len(setting)-1]
                    parts = [model_key, setting]
                    break
            else:
                raise ValueError(
                    f"Invalid comparison_id format: {comparison_id}. "
                    "Expected format: {{model_key}}_{{setting}}"
                )

        model_key, setting = parts

        models = self._data.get("models", {})
        if model_key not in models:
            return None

        model_data = models[model_key]
        generated = model_data.get("generated_plantuml", {}).get(setting)
        metrics = model_data.get("metrics", {}).get(setting)

        if generated is None or metrics is None:
            return None

        return ComparisonData(
            comparison_id=comparison_id,
            model_key=model_key,
            model_full_name=model_data.get("full_name", model_key),
            setting=setting,
            reference_plantuml=model_data.get("reference_plantuml", ""),
            generated_plantuml=generated,
            human_metrics=metrics
        )

    def list_comparison_ids(self) -> List[str]:
        """
        List all valid comparison IDs.

        Returns:
            List of comparison IDs for all valid comparisons

        Raises:
            RuntimeError: If load() hasn't been called yet
        """
        return [comp.comparison_id for comp in self.iter_comparisons()]

    @property
    def models(self) -> List[str]:
        """
        List of model keys.

        Returns:
            List of model key strings

        Raises:
            RuntimeError: If load() hasn't been called yet
        """
        if self._data is None:
            raise RuntimeError("Must call load() before accessing models")
        return list(self._data.get("models", {}).keys())

    @property
    def settings(self) -> List[str]:
        """
        List of setting keys.

        Returns:
            List of setting key strings

        Raises:
            RuntimeError: If load() hasn't been called yet
        """
        if self._data is None:
            raise RuntimeError("Must call load() before accessing settings")
        return self._data.get("metadata", {}).get(
            "settings_included",
            ["0shot", "1shot_BTMS", "1shot_H2S", "2shots", "CoT"]
        )

    @property
    def total_comparisons(self) -> int:
        """
        Total number of valid comparisons.

        Returns:
            Count of valid comparisons

        Raises:
            RuntimeError: If load() hasn't been called yet
        """
        return len(self.list_comparison_ids())

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Dataset metadata.

        Returns:
            Metadata dictionary

        Raises:
            RuntimeError: If load() hasn't been called yet
        """
        if self._data is None:
            raise RuntimeError("Must call load() before accessing metadata")
        return self._data.get("metadata", {})
