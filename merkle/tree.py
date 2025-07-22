"""Merkle Tree implementation for code chunk indexing."""

from dataclasses import dataclass
import hashlib
import os
from typing import List, Optional, Dict
from .node import MerkleNode
from .exceptions import EmptyTreeError, InvalidIndexError, InvalidHashError

class MerkleTree:
    """
    A Merkle Tree implementation for tracking file changes.
    """
    
    ignored_patterns = [
        ".env", ".gitignore", ".git", ".DS_Store"
    ]

    def __init__(self) -> None:
        """Initialize a Merkle Tree."""
        self._root: Optional[MerkleNode] = None

    def _build_tree(self, root_path: str) -> None:
        """Build the Merkle Tree."""
        self._root = self._build_tree_recursive(root_path)

    def _build_tree_recursive(self, path: str) -> MerkleNode:
        """Build the Merkle Tree recursively."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} does not exist")
        
        if os.path.isfile(path):
            file_hash = hashlib.sha256(open(path, "rb").read()).hexdigest()
            return MerkleNode.create_file_node(file, path, file_hash)

        childrens: Dict[str, MerkleNode] = {}
        childrens_hash: List[str] = []
        for file in os.listdir(path):
            if file in self.ignored_patterns:
                continue
            child_path = os.path.join(path, file)
            childrens[file] = self._build_tree_recursive(child_path)
            childrens_hash.append(childrens[file].hash)

        childrens_hash.sort()
        childrens_hash = "".join(childrens_hash)
        combined_hash = hashlib.sha256(childrens_hash.encode()).hexdigest()
        return MerkleNode.create_directory_node(file, path, combined_hash, childrens)
    
    def __str__(self) -> str:
        """String representation of the tree."""
        leaf_count = len(self._leaves)
        root_hash = "None" if not self._leaves else (self.get_root()[:8] + "...")
        return f"MerkleTree(leaves={leaf_count}, root={root_hash})"
    
    def __len__(self) -> int:
        """Return number of leaves in the tree."""
        return len(self._leaves) 