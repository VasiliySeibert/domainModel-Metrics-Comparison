import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidEditInformations import isValidEditInformations
from Testset.isValidMapping import isValidMapping
from Testset.isValidGraph import isValidGraph
from Testset.s1_types import EditInformations, Graph, Mapping
from Specification.metric_interface import validate_metric_result


@icontract.require(
    lambda edit_informations, optimal_mapping, element_mapping,
    instructor_graph, student_graph: (
        isValidEditInformations(edit_informations)
        and isValidMapping(optimal_mapping)
        and isValidMapping(element_mapping)
        and isValidGraph(instructor_graph)
        and isValidGraph(student_graph)
    )
)
@icontract.ensure(
    lambda result: validate_metric_result(result),
    "Returned dict satisfies validate_metric_result",
)
def normalization(
    edit_informations: EditInformations,
    optimal_mapping: Mapping,
    element_mapping: Mapping,
    instructor_graph: Graph,
    student_graph: Graph,
) -> dict:
    r"""
    Decompose the aggregate edit distance into three normalized scores.

    Parameters
    ----------
    edit_informations : EditInformations
        The complete edit path returned by ``scaleEditCosts``.
    optimal_mapping : Mapping
        The optimal bijection returned by ``computeOptimalMapping``.
    element_mapping : Mapping
        Contains ``element_cost_matrix`` with intra-level distances δ(m, m').
    instructor_graph : Graph
        The instructor graph G₁ = (V₁, E₁, μ, ρ).
    student_graph : Graph
        The student graph G₂ = (V₂, E₂, μ, ρ).

    Returns
    -------
    dict
        {
            "class_score":       float,  # [0, 1]
            "attribute_score":   float,  # [0, 1]
            "association_score": float,  # [0, 1]
        }

    Algorithm
    ---------
    **class_score**
        Sum raw costs of all vertex operations (substitution, deletion,
        insertion).  Maximum possible cost is ``max(|V₁|, |V₂|)``.

        class_score = 1.0 - (vertex_raw_costs / max(|V₁|, |V₂|))

    **association_score**
        Sum raw costs of all edge operations.  Maximum possible cost is
        ``|E₁| + |E₂|``.

        association_score = 1.0 - (edge_raw_costs / (|E₁| + |E₂|))

    **attribute_score**
        For every mapped vertex pair (m, m') in ``optimal_mapping``,
        recompute the attribute-only distance δ_attrs(m, m') using the
        Hungarian attribute-matching logic from ``computeElementMapping``
        with name/type/const/default weights.  Unmapped vertices count as
        unit cost 1.0.

        attribute_penalty = sum(δ_attrs) + n_unmapped
        max_attr_cost = max(|V₁|, |V₂|)
        attribute_score = 1.0 - (attribute_penalty / max_attr_cost)

    All scores are clamped to [0, 1].
    """
    # TODO: implementation here ...
    return {
        "class_score": 0.0,
        "attribute_score": 0.0,
        "association_score": 0.0,
    }
