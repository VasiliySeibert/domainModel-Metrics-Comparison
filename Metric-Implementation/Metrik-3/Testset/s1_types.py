from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple, Dict
from enum import Enum


class OperationType(Enum):
    """Types of edit operations in the GED framework."""
    VERTEX_SUBSTITUTION = "vertex_substitution"
    VERTEX_DELETION = "vertex_deletion"
    VERTEX_INSERTION = "vertex_insertion"
    EDGE_SUBSTITUTION = "edge_substitution"
    EDGE_DELETION = "edge_deletion"
    EDGE_INSERTION = "edge_insertion"


@dataclass
class EditInformation:
    """A single edit operation in the edit path."""
    operation_type: OperationType
    source_ref: Optional[str]
    target_ref: Optional[str]
    raw_cost: float
    scaled_cost: float


@dataclass
class EditInformations:
    """Complete edit path with total scaled distance."""
    operations: List[EditInformation]
    total_scaled_distance: float


@dataclass
class UCGVertex:
    """A vertex in the UML Class Graph (UCG)."""
    vertex_id: str
    vertex_type: str          # one of {"class", "attribute", "operation", "parameter"}
    label: str                # name of the class/attribute/operation/parameter
    element: Optional[object] = None   # reference to the original parsed element


@dataclass
class UCGEdge:
    """An edge in the UML Class Graph (UCG)."""
    edge_id: str
    source_vertex_id: str
    target_vertex_id: str
    edge_type: str            # one of {"attribute", "operation", "parameter", "relationship"}
    tag: str                  # e.g. "ea", "eo", "ep", "e1".."e6"


@dataclass
class UCG:
    """
    UML Class Graph (UCG).
    G = (V, E, L) where L is encoded implicitly via vertex labels.
    """
    vertices: List[UCGVertex] = field(default_factory=list)
    edges: List[UCGEdge] = field(default_factory=list)

    # Convenience getters
    def class_vertices(self) -> List[UCGVertex]:
        return [v for v in self.vertices if v.vertex_type == "class"]

    def attribute_vertices(self) -> List[UCGVertex]:
        return [v for v in self.vertices if v.vertex_type == "attribute"]

    def operation_vertices(self) -> List[UCGVertex]:
        return [v for v in self.vertices if v.vertex_type == "operation"]

    def parameter_vertices(self) -> List[UCGVertex]:
        return [v for v in self.vertices if v.vertex_type == "parameter"]

    def relationship_edges(self) -> List[UCGEdge]:
        return [e for e in self.edges if e.edge_type == "relationship"]

    def attribute_edges(self) -> List[UCGEdge]:
        return [e for e in self.edges if e.edge_type == "attribute"]

    def operation_edges(self) -> List[UCGEdge]:
        return [e for e in self.edges if e.edge_type == "operation"]

    def parameter_edges(self) -> List[UCGEdge]:
        return [e for e in self.edges if e.edge_type == "parameter"]


@dataclass
class UMCS:
    """
    A UCG Maximum Common Subgraph (UMCS).
    Represents a set of matched relationship edges from g1 together with the
    vertex mapping that establishes the match against g2.
    """
    edge_ids: frozenset           # relationship edge IDs from g1
    vertex_map: Dict[str, str]    # g1 class vertex ID -> g2 class vertex ID


@dataclass
class UMCSNode:
    """
    A node in the UMCS Tree.
    Each node stores the MCSL (list of UMCS) found at a particular level.
    """
    mcsl: List[UMCS] = field(default_factory=list)
    children: List["UMCSNode"] = field(default_factory=list)
