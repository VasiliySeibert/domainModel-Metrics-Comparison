from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum

# Re-use existing parser models for element references
from Parser.models import ParsedClass, ParsedRelationship


class OperationType(Enum):
    """Types of edit operations in the GED framework."""
    VERTEX_SUBSTITUTION = "vertex_substitution"
    VERTEX_DELETION     = "vertex_deletion"
    VERTEX_INSERTION    = "vertex_insertion"
    EDGE_SUBSTITUTION   = "edge_substitution"
    EDGE_DELETION       = "edge_deletion"
    EDGE_INSERTION      = "edge_insertion"


@dataclass
class GraphVertex:
    """A vertex in the attributed undirected multigraph."""
    vertex_id: str
    element: ParsedClass          # the model element assigned by μ


@dataclass
class GraphEdge:
    """An edge in the attributed undirected multigraph."""
    edge_id: str
    source_vertex_id: str
    target_vertex_id: str
    relations: List[ParsedRelationship]   # the subset of relations assigned by ρ


@dataclass
class Graph:
    """Attributed undirected multigraph G = (V, E, μ, ρ)."""
    vertices: List[GraphVertex] = field(default_factory=list)
    edges: List[GraphEdge]     = field(default_factory=list)

    # μ and ρ are encoded implicitly:
    #   μ(v)  == v.element
    #   ρ(e)  == e.relations


@dataclass
class VertexMappingEntry:
    """One substituted vertex pair with its raw intra-element distance."""
    instructor_vertex_id: str
    student_vertex_id: str
    raw_cost: float                     # δ(m, m') ∈ [0, 1]


@dataclass
class EdgeMappingEntry:
    """One substituted edge pair with its raw intra-relation distance."""
    instructor_edge_id: str
    student_edge_id: str
    raw_cost: float                     # δ(R, R') ∈ [0, 1]


@dataclass
class Mapping:
    """
    Static mapping structure that carries the full GED pipeline state.
    Used for:
      - pairwise element/relation cost tables (intra-level)
      - optimal vertex/edge bijection   (inter-level)
      - unmapped items (implied deletions / insertions)
      - accumulated raw cost
    """
    # --- intra-level cost tables (populated by computeElementMapping / computeRelationMapping) ---
    element_cost_matrix: Dict[Tuple[str, str], float] = field(default_factory=dict)
    relation_cost_matrix: Dict[Tuple[str, str], float] = field(default_factory=dict)

    # --- inter-level optimal mapping (populated by computeOptimalMapping) ---
    vertex_mappings: List[VertexMappingEntry]           = field(default_factory=list)
    edge_mappings:   List[EdgeMappingEntry]             = field(default_factory=list)

    unmapped_instructor_vertices: List[str] = field(default_factory=list)
    unmapped_student_vertices:    List[str] = field(default_factory=list)
    unmapped_instructor_edges:    List[str] = field(default_factory=list)
    unmapped_student_edges:     List[str] = field(default_factory=list)

    total_raw_cost: float = 0.0


@dataclass
class EditInformation:
    """A single edit operation with its costs."""
    operation_type: OperationType
    source_ref: Optional[str]       # vertex_id / edge_id or None for ε
    target_ref: Optional[str]       # vertex_id / edge_id or None for ε
    raw_cost: float                 # ≥ 0; 1 for insertion/deletion, [0,1] for substitution
    scaled_cost: float = 0.0        # raw_cost / c_max  ∈ [0, 1]


@dataclass
class EditInformations:
    """Complete ordered list of edit operations + scaled total distance."""
    operations: List[EditInformation] = field(default_factory=list)
    total_scaled_distance: float = 0.0   # sum(raw_cost) / c_max  ∈ [0, 1]
