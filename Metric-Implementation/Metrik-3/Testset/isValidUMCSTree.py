import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Testset.s1_types import UMCSNode, UMCS


def isValidUMCSTree(root: UMCSNode) -> bool:
    """
    Validate that a UMCS Tree adheres to structural constraints.

    Constraints:
      1. Root node exists and is a UMCSNode instance.
      2. At each node, every UMCS in mcsl is a UMCS instance.
      3. At each node, every UMCS in mcsl has the same size (number of edge IDs).
      4. All UMCS in a node's mcsl are pairwise distinct.
      5. Along any root-to-leaf path, sizes are non-increasing.
    """
    if not isinstance(root, UMCSNode):
        return False

    def _check_node(node: UMCSNode, parent_size: int) -> bool:
        # Check that every entry in mcsl is a UMCS instance
        for umcs in node.mcsl:
            if not isinstance(umcs, UMCS):
                return False

        # Get sizes of all UMCS in this node
        sizes = [len(umcs.edge_ids) for umcs in node.mcsl]

        # If there are UMCS entries, they must all have the same size
        if sizes:
            first_size = sizes[0]
            if any(s != first_size for s in sizes):
                return False

            # Check non-increasing along path
            if first_size > parent_size:
                return False

            # Check distinctness — UMCS is not frozen, so we compare explicitly
            seen = set()
            for entry in node.mcsl:
                sig = (entry.edge_ids, tuple(sorted(entry.vertex_map.items())))
                if sig in seen:
                    return False
                seen.add(sig)

            current_size = first_size
        else:
            current_size = parent_size  # no UMCS at this level, keep parent size

        # Recurse into children
        for child in node.children:
            if not _check_node(child, current_size):
                return False

        return True

    return _check_node(root, float("inf"))


if __name__ == "__main__":
    # Minimal smoke test
    root = UMCSNode(
        mcsl=[
            UMCS(edge_ids=frozenset({"e1", "e2"}), vertex_map={"cv1": "cvA"}),
            UMCS(edge_ids=frozenset({"e3", "e4"}), vertex_map={"cv2": "cvB"}),
        ]
    )
    child = UMCSNode(
        mcsl=[UMCS(edge_ids=frozenset({"e5"}), vertex_map={"cv3": "cvC"})]
    )
    root.children.append(child)
    print(isValidUMCSTree(root))  # Expected: True
