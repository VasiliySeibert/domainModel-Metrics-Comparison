"""
Metric Internal Data Models

Dataclasses for the intermediate Diagram representation used by the S-1
similarity metric (see Metric-Implementation/Metrik-4/Implementation_3/s1.md).

Exported types:
    AttributeInfo  – normalised attribute with type and modifier.
    ClassInfo      – normalised class (or enum-as-class) with attributes.
    Edge           – normalised relationship edge with ownership tag.
    Diagram        – complete normalised class-diagram container.
"""

from dataclasses import dataclass, field
from typing import List


# ----------------------------------------------------------------------
# Score containers (decomposed metric output)
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class SemanticScores:
    """Decomposed semantic similarity scores.

    Fields
    ------
    semantic : float
        Top-level semantic score (Eq. 1).
    propSim : float
        Property (class + attribute) similarity (Eq. 2).
    relSim : float
        Relationship similarity (Eq. 9).

    Invariant
    ---------
    ``semantic == (1 - 0.3) * propSim + 0.3 * relSim``
    up to floating-point tolerance ``1e-6``.
    """
    semantic: float
    propSim: float
    relSim: float


@dataclass(frozen=True)
class StructuralScores:
    """Decomposed structural similarity scores.

    Fields
    ------
    structural : float
        Top-level structural score (Eq. 16).
    intraSim : float
        Intra-class subgraph GED similarity (Eq. 17).
    interSim : float
        Inter-class relationship subgraph GED similarity (Eq. 19).

    Invariant
    ---------
    ``structural == (1 - 0.1) * intraSim + 0.1 * interSim``
    up to floating-point tolerance ``1e-6``.
    """
    structural: float
    intraSim: float
    interSim: float


@dataclass(frozen=True)
class SimilarityResult:
    """Complete combined similarity result.

    Fields
    ------
    similarity : float
        Final combined score (Eq. 20).
    semantic : float
        Semantic component (Eq. 1).
    structural : float
        Structural component (Eq. 16).
    propSim : float
        Property similarity (Eq. 2).
    relSim : float
        Relationship similarity (Eq. 9).
    intraSim : float
        Intra-structure similarity (Eq. 17).
    interSim : float
        Inter-structure similarity (Eq. 19).

    Invariants
    ----------
    - ``similarity == 0.5 * semantic + 0.5 * structural``
    - ``semantic   == 0.7 * propSim   + 0.3 * relSim``
    - ``structural == 0.9 * intraSim  + 0.1 * interSim``

    All identities hold up to floating-point tolerance ``1e-6``.
    """
    similarity: float
    semantic: float
    structural: float
    propSim: float
    relSim: float
    intraSim: float
    interSim: float


# ----------------------------------------------------------------------
# Diagram model
# ----------------------------------------------------------------------

@dataclass
class AttributeInfo:
    """
    Normalised attribute used within the similarity pipeline.

    Fields:
        name      – attribute identifier (non-empty string).
        type      – normalised type string (empty if originally untyped).
        modifier  – "const" if the original attribute was constant, otherwise "".
    """
    name: str
    type: str = ""
    modifier: str = ""


@dataclass
class ClassInfo:
    """
    Normalised class (or enum-as-class) used within the similarity pipeline.

    Fields:
        name        – class identifier (non-empty string).
        is_abstract – carried over from ParsedClass.is_abstract.
        attributes  – normalised attributes belonging to this class.
    """
    name: str
    is_abstract: bool = False
    attributes: List[AttributeInfo] = field(default_factory=list)


@dataclass
class Edge:
    """
    Normalised relationship edge.

    Fields:
        source    – name of the source class (non-empty string).
        target    – name of the target class (non-empty string).
        name      – relationship label (may be empty).
        ownership – "composition" | "aggregation" | "none".
    """
    source: str
    target: str
    name: str = ""
    ownership: str = "none"


@dataclass
class Diagram:
    """
    Complete normalised class-diagram container.

    Fields:
        classes         – all ClassInfo instances (classes + enums-as-classes + implicit classes).
        associations    – normalised association-type edges.
        dependencies    – normalised dependency-type edges.
        generalizations – normalised generalisation-type (inheritance) edges.
    """
    classes: List[ClassInfo] = field(default_factory=list)
    associations: List[Edge] = field(default_factory=list)
    dependencies: List[Edge] = field(default_factory=list)
    generalizations: List[Edge] = field(default_factory=list)