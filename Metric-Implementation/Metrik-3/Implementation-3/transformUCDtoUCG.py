import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidModel import isValidModel
from Testset.isValidUCG import isValidUCG
from Testset.s1_types import UCG, UCGVertex, UCGEdge


# Mapping from ParsedRelationship.relationship_type to UCG relationship edge tag.
# Direction convention (source -> target) is defined in the transformation spec.
_REL_TYPE_TO_TAG = {
    "association":           "e1",
    "directed":              "e1",   # directed association -> same tag as plain association
    "inheritance":           "e2",
    "aggregation":           "e3",
    "composition":           "e4",
    "dependency":            "e5",
    # "association_class" is not covered by the paper's UCG definition and is ignored.
}


@icontract.require(lambda model: isValidModel(model))
@icontract.ensure(lambda result: isValidUCG(result))
def transformUCDtoUCG(model) -> UCG:
    r"""
    Transform a parsed PlantUML model into a UML Class Graph (UCG).
    """
    vertices = []
    edges = []

    # Phase 1 — Classes and enumerations → class vertices
    all_names = sorted(set(model.all_class_names + model.all_enum_names))
    for name in all_names:
        vertices.append(UCGVertex(
            vertex_id=f"cv:{name}",
            vertex_type="class",
            label=name,
        ))

    # Phase 2 — Attributes → attribute vertices
    # Phase 3 — Attribute edges
    for cls in model.classes:
        for attr in cls.attributes:
            attr_vid = f"av:{cls.name}:{attr.name}"
            vertices.append(UCGVertex(
                vertex_id=attr_vid,
                vertex_type="attribute",
                label=attr.name,
            ))
            edges.append(UCGEdge(
                edge_id=f"ae:{cls.name}:{attr.name}",
                source_vertex_id=f"cv:{cls.name}",
                target_vertex_id=attr_vid,
                edge_type="attribute",
                tag="ea",
            ))

    # Phase 4 — Relationships → relationship edges
    seen_rels = set()
    for rel in model.relationships:
        if rel.relationship_type.value == "association_class":
            continue
        tag = _REL_TYPE_TO_TAG.get(rel.relationship_type.value)
        if tag is None:
            continue
        sig = (f"cv:{rel.source}", f"cv:{rel.target}", "relationship", tag)
        if sig in seen_rels:
            continue
        seen_rels.add(sig)
        edges.append(UCGEdge(
            edge_id=f"re:{rel.source}:{rel.target}:{tag}",
            source_vertex_id=f"cv:{rel.source}",
            target_vertex_id=f"cv:{rel.target}",
            edge_type="relationship",
            tag=tag,
        ))

    return UCG(vertices=vertices, edges=edges)
