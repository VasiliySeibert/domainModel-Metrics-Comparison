"""
Delta Calculator Module

This module provides comprehensive calculation logic for computing deltas
(differences) between automated metric scores and human evaluation scores.

=============================================================================
CALCULATION METHODOLOGY
=============================================================================

1. DELTA CALCULATION
   -----------------
   Delta represents the difference between the automated metric score and
   the human evaluation score.

   Formula: delta = metric_score - human_score

   Interpretation:
   - Positive delta (+): Metric OVERESTIMATES quality compared to humans
   - Negative delta (-): Metric UNDERESTIMATES quality compared to humans
   - Zero delta (0): Perfect alignment with human evaluation

   Example:
   If metric_class_score = 0.7 and human_Class_f1 = 0.5
   Then delta_class_vs_f1 = 0.7 - 0.5 = +0.2 (metric overestimates by 0.2)

2. COMPARISON TYPES
   ----------------
   For each element type (Class, Attribute, Association), we compute deltas
   against three human metrics:

   a) vs F1 Score (Primary comparison)
      - F1 is the harmonic mean of precision and recall
      - Best single measure of overall accuracy
      - Formula: F1 = 2 * (precision * recall) / (precision + recall)

   b) vs Precision
      - Precision measures "of the elements the model found, how many were correct"
      - High precision = few false positives

   c) vs Recall
      - Recall measures "of all correct elements, how many did the model find"
      - High recall = few false negatives

3. AGGREGATED SCORES
   -----------------
   Overall metric average: (class_score + attribute_score + association_score) / 3
   Overall human F1 average: (Class_f1 + Attribute_f1 + Association_f1) / 3
   Overall delta: metric_average - human_f1_average

4. SUMMARY STATISTICS
   ------------------
   Across all comparisons, we compute:

   a) Mean Delta: Average delta across all comparisons
      - Shows systematic bias (over/underestimation tendency)

   b) Standard Deviation: Spread of deltas
      - Shows consistency of the metric

   c) Pearson Correlation: Linear relationship between metric and human scores
      - Range: -1 to +1
      - +1: Perfect positive correlation (when human score increases, metric increases)
      - 0: No correlation
      - -1: Perfect negative correlation (inverse relationship)

   d) Correlation significance (p-value):
      - p < 0.05: Statistically significant correlation
      - p >= 0.05: Correlation may be due to chance

=============================================================================
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class DeltaResult:
    """
    Container for delta calculation results.

    Attributes:
        class_vs_f1: Delta between metric class score and human Class F1
        attribute_vs_f1: Delta between metric attribute score and human Attribute F1
        association_vs_f1: Delta between metric association score and human Association F1
        class_vs_precision: Delta vs human Class precision
        class_vs_recall: Delta vs human Class recall
        attribute_vs_precision: Delta vs human Attribute precision
        attribute_vs_recall: Delta vs human Attribute recall
        association_vs_precision: Delta vs human Association precision
        association_vs_recall: Delta vs human Association recall
    """
    class_vs_f1: float
    attribute_vs_f1: float
    association_vs_f1: float
    class_vs_precision: float
    class_vs_recall: float
    attribute_vs_precision: float
    attribute_vs_recall: float
    association_vs_precision: float
    association_vs_recall: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return {
            "class_vs_f1": self.class_vs_f1,
            "attribute_vs_f1": self.attribute_vs_f1,
            "association_vs_f1": self.association_vs_f1,
            "class_vs_precision": self.class_vs_precision,
            "class_vs_recall": self.class_vs_recall,
            "attribute_vs_precision": self.attribute_vs_precision,
            "attribute_vs_recall": self.attribute_vs_recall,
            "association_vs_precision": self.association_vs_precision,
            "association_vs_recall": self.association_vs_recall,
        }


@dataclass
class AggregatedResult:
    """
    Container for aggregated score results.

    Attributes:
        metric_average: Average of all three metric scores
        human_f1_average: Average of all three human F1 scores
        overall_delta: Difference between metric and human averages
    """
    metric_average: float
    human_f1_average: float
    overall_delta: float

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric_average": self.metric_average,
            "human_f1_average": self.human_f1_average,
            "overall_delta": self.overall_delta,
        }


class DeltaCalculator:
    """
    Calculate deltas and statistics between metric and human scores.

    This class provides methods for:
    1. Computing detailed deltas for single comparisons
    2. Computing aggregated scores
    3. Computing summary statistics across all comparisons

    All calculations are documented in the module docstring above.

    Example:
        calculator = DeltaCalculator()

        # Single comparison
        metric_results = {"class_score": 0.7, "attribute_score": 0.6, "association_score": 0.5}
        human_metrics = {
            "Class": {"precision": 0.9, "recall": 0.5, "f1": 0.64},
            "Attribute": {"precision": 0.8, "recall": 0.6, "f1": 0.69},
            "Association": {"precision": 0.4, "recall": 0.3, "f1": 0.34}
        }

        delta = calculator.compute_comparison_delta(metric_results, human_metrics)
        print(f"Class delta vs F1: {delta.class_vs_f1}")

        aggregated = calculator.compute_aggregated(metric_results, human_metrics)
        print(f"Overall delta: {aggregated.overall_delta}")
    """

    @staticmethod
    def compute_comparison_delta(
        metric_results: Dict[str, float],
        human_metrics: Dict[str, Dict[str, float]]
    ) -> DeltaResult:
        """
        Compute detailed delta for a single comparison.

        This method calculates the difference between the automated metric
        scores and human evaluation scores for all element types and
        human metric types (precision, recall, F1).

        Formula: delta = metric_score - human_score

        Args:
            metric_results: Dictionary with keys:
                - class_score (float): Metric's class similarity score
                - attribute_score (float): Metric's attribute similarity score
                - association_score (float): Metric's association similarity score

            human_metrics: Dictionary with structure:
                {
                    "Class": {"precision": float, "recall": float, "f1": float},
                    "Attribute": {"precision": float, "recall": float, "f1": float},
                    "Association": {"precision": float, "recall": float, "f1": float}
                }

        Returns:
            DeltaResult containing all computed deltas

        Raises:
            KeyError: If required keys are missing from input dictionaries
        """
        # Extract metric scores
        class_score = metric_results["class_score"]
        attribute_score = metric_results["attribute_score"]
        association_score = metric_results["association_score"]

        # Extract human scores
        human_class = human_metrics["Class"]
        human_attr = human_metrics["Attribute"]
        human_assoc = human_metrics["Association"]

        return DeltaResult(
            # F1 deltas (primary comparison)
            class_vs_f1=class_score - human_class["f1"],
            attribute_vs_f1=attribute_score - human_attr["f1"],
            association_vs_f1=association_score - human_assoc["f1"],

            # Precision deltas
            class_vs_precision=class_score - human_class["precision"],
            attribute_vs_precision=attribute_score - human_attr["precision"],
            association_vs_precision=association_score - human_assoc["precision"],

            # Recall deltas
            class_vs_recall=class_score - human_class["recall"],
            attribute_vs_recall=attribute_score - human_attr["recall"],
            association_vs_recall=association_score - human_assoc["recall"],
        )

    @staticmethod
    def compute_aggregated(
        metric_results: Dict[str, float],
        human_metrics: Dict[str, Dict[str, float]]
    ) -> AggregatedResult:
        """
        Compute aggregated scores for a comparison.

        This method calculates overall averages and the aggregate delta
        between the metric and human evaluation.

        Formulas:
            metric_average = (class_score + attribute_score + association_score) / 3
            human_f1_average = (Class_f1 + Attribute_f1 + Association_f1) / 3
            overall_delta = metric_average - human_f1_average

        Args:
            metric_results: Dictionary with metric scores (class_score,
                           attribute_score, association_score)
            human_metrics: Dictionary with human evaluation scores

        Returns:
            AggregatedResult with averages and overall delta
        """
        # Compute metric average
        metric_average = (
            metric_results["class_score"] +
            metric_results["attribute_score"] +
            metric_results["association_score"]
        ) / 3

        # Compute human F1 average
        human_f1_average = (
            human_metrics["Class"]["f1"] +
            human_metrics["Attribute"]["f1"] +
            human_metrics["Association"]["f1"]
        ) / 3

        # Compute overall delta
        overall_delta = metric_average - human_f1_average

        return AggregatedResult(
            metric_average=metric_average,
            human_f1_average=human_f1_average,
            overall_delta=overall_delta
        )

    @staticmethod
    def compute_summary_statistics(comparisons: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute summary statistics across all comparisons.

        This method calculates statistical measures that describe how well
        the metric aligns with human evaluation across the entire dataset.

        Statistics computed:
        1. Mean delta: Average difference (shows bias)
        2. Standard deviation: Spread of deltas (shows consistency)
        3. Pearson correlation: Linear relationship strength
        4. Min/max delta: Range of differences

        Args:
            comparisons: Dictionary of comparison results where each value
                        contains "metric_results", "human_metrics", and "delta"

        Returns:
            Dictionary containing:
                - mean_class_delta_f1, mean_attribute_delta_f1, mean_association_delta_f1
                - std_class_delta_f1, std_attribute_delta_f1, std_association_delta_f1
                - min_class_delta_f1, max_class_delta_f1 (and for other types)
                - correlation_class, correlation_attribute, correlation_association
                - correlation_class_pvalue, etc. (p-values)
                - overall_mean_delta
                - overall_correlation
        """
        # Import here to avoid dependency issues if scipy not available
        try:
            from scipy import stats as scipy_stats
            HAS_SCIPY = True
        except ImportError:
            HAS_SCIPY = False

        # Collect arrays for analysis
        class_deltas: List[float] = []
        attribute_deltas: List[float] = []
        association_deltas: List[float] = []

        metric_class_scores: List[float] = []
        metric_attribute_scores: List[float] = []
        metric_association_scores: List[float] = []

        human_class_f1s: List[float] = []
        human_attribute_f1s: List[float] = []
        human_association_f1s: List[float] = []

        # Extract data from comparisons
        for comp_data in comparisons.values():
            delta = comp_data.get("delta", {})
            metric = comp_data.get("metric_results", {})
            human = comp_data.get("human_metrics", {})

            # Deltas
            if "class_vs_f1" in delta:
                class_deltas.append(delta["class_vs_f1"])
            if "attribute_vs_f1" in delta:
                attribute_deltas.append(delta["attribute_vs_f1"])
            if "association_vs_f1" in delta:
                association_deltas.append(delta["association_vs_f1"])

            # Metric scores
            if "class_score" in metric:
                metric_class_scores.append(metric["class_score"])
            if "attribute_score" in metric:
                metric_attribute_scores.append(metric["attribute_score"])
            if "association_score" in metric:
                metric_association_scores.append(metric["association_score"])

            # Human F1 scores
            if "Class" in human and "f1" in human["Class"]:
                human_class_f1s.append(human["Class"]["f1"])
            if "Attribute" in human and "f1" in human["Attribute"]:
                human_attribute_f1s.append(human["Attribute"]["f1"])
            if "Association" in human and "f1" in human["Association"]:
                human_association_f1s.append(human["Association"]["f1"])

        # Helper functions for statistics
        def safe_mean(arr: List[float]) -> Optional[float]:
            return sum(arr) / len(arr) if arr else None

        def safe_std(arr: List[float]) -> Optional[float]:
            if len(arr) < 2:
                return None
            mean = sum(arr) / len(arr)
            variance = sum((x - mean) ** 2 for x in arr) / (len(arr) - 1)
            return variance ** 0.5

        def safe_correlation(x: List[float], y: List[float]) -> Dict[str, Optional[float]]:
            """Compute Pearson correlation with p-value."""
            if len(x) != len(y) or len(x) < 3:
                return {"correlation": None, "pvalue": None}

            if HAS_SCIPY:
                try:
                    corr, pvalue = scipy_stats.pearsonr(x, y)
                    return {"correlation": corr, "pvalue": pvalue}
                except Exception:
                    pass

            # Fallback: manual Pearson correlation (no p-value)
            n = len(x)
            mean_x = sum(x) / n
            mean_y = sum(y) / n

            numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
            denom_x = sum((xi - mean_x) ** 2 for xi in x) ** 0.5
            denom_y = sum((yi - mean_y) ** 2 for yi in y) ** 0.5

            if denom_x == 0 or denom_y == 0:
                return {"correlation": None, "pvalue": None}

            return {"correlation": numerator / (denom_x * denom_y), "pvalue": None}

        # Compute statistics
        result: Dict[str, Any] = {}

        # Delta means
        result["mean_class_delta_f1"] = safe_mean(class_deltas)
        result["mean_attribute_delta_f1"] = safe_mean(attribute_deltas)
        result["mean_association_delta_f1"] = safe_mean(association_deltas)

        # Delta standard deviations
        result["std_class_delta_f1"] = safe_std(class_deltas)
        result["std_attribute_delta_f1"] = safe_std(attribute_deltas)
        result["std_association_delta_f1"] = safe_std(association_deltas)

        # Delta min/max
        result["min_class_delta_f1"] = min(class_deltas) if class_deltas else None
        result["max_class_delta_f1"] = max(class_deltas) if class_deltas else None
        result["min_attribute_delta_f1"] = min(attribute_deltas) if attribute_deltas else None
        result["max_attribute_delta_f1"] = max(attribute_deltas) if attribute_deltas else None
        result["min_association_delta_f1"] = min(association_deltas) if association_deltas else None
        result["max_association_delta_f1"] = max(association_deltas) if association_deltas else None

        # Correlations (metric vs human)
        class_corr = safe_correlation(metric_class_scores, human_class_f1s)
        attr_corr = safe_correlation(metric_attribute_scores, human_attribute_f1s)
        assoc_corr = safe_correlation(metric_association_scores, human_association_f1s)

        result["correlation_class"] = class_corr["correlation"]
        result["correlation_class_pvalue"] = class_corr["pvalue"]
        result["correlation_attribute"] = attr_corr["correlation"]
        result["correlation_attribute_pvalue"] = attr_corr["pvalue"]
        result["correlation_association"] = assoc_corr["correlation"]
        result["correlation_association_pvalue"] = assoc_corr["pvalue"]

        # Overall statistics
        all_deltas = class_deltas + attribute_deltas + association_deltas
        result["overall_mean_delta"] = safe_mean(all_deltas)
        result["overall_std_delta"] = safe_std(all_deltas)

        # Overall correlation (all scores combined)
        all_metric = metric_class_scores + metric_attribute_scores + metric_association_scores
        all_human = human_class_f1s + human_attribute_f1s + human_association_f1s
        overall_corr = safe_correlation(all_metric, all_human)
        result["overall_correlation"] = overall_corr["correlation"]
        result["overall_correlation_pvalue"] = overall_corr["pvalue"]

        # Count of comparisons
        result["n_comparisons"] = len(comparisons)

        return result


def compute_single_delta(
    metric_score: float,
    human_score: float
) -> float:
    """
    Compute delta between a single metric score and human score.

    This is a convenience function for simple delta calculations.

    Formula: delta = metric_score - human_score

    Args:
        metric_score: Automated metric score (0.0 to 1.0)
        human_score: Human evaluation score (0.0 to 1.0)

    Returns:
        Delta value (positive = overestimate, negative = underestimate)

    Example:
        >>> compute_single_delta(0.7, 0.5)
        0.2  # Metric overestimates by 0.2
        >>> compute_single_delta(0.3, 0.5)
        -0.2  # Metric underestimates by 0.2
    """
    return metric_score - human_score
