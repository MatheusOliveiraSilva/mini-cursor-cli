"""Merkle Tree implementation for file system indexing."""

import hashlib
import os
from typing import List, Optional, Dict, Set
from .node import MerkleNode
from .exceptions import EmptyTreeError, InvalidIndexError, InvalidHashError

class MerkleTree:
    """
    A Merkle Tree implementation for tracking file changes.
    Follows Cursor's architecture: files as leaves, directories as internal nodes.
    """
    
    def __init__(self, root_path: str = None) -> None:
        """Initialize a Merkle Tree."""
        self.root: Optional[MerkleNode] = None
        self.root_path = root_path
        self.ignored_patterns = {
            ".env", ".gitignore", ".git", ".DS_Store",
             "__pycache__", ".venv", "venv"
        }
        
        if root_path:
            self.build_from_directory(root_path)

    def build_from_directory(self, root_path: str) -> None:
        """Build the Merkle Tree from a directory."""
        if not os.path.exists(root_path):
            raise FileNotFoundError(f"Path {root_path} does not exist")
        
        self.root_path = os.path.abspath(root_path)
        self.root = self._build_recursive(self.root_path)

    def _build_recursive(self, path: str) -> MerkleNode:
        """Build the Merkle Tree recursively."""
        name = os.path.basename(path)
        
        if os.path.isfile(path):
            # File node (leaf) - hash content
            with open(path, "rb") as f:
                content = f.read()
            file_hash = hashlib.sha256(content).hexdigest()
            return MerkleNode.create_file(name, path, file_hash)
        
        # Directory node - hash children
        children = {}
        for item in sorted(os.listdir(path)):  # Sort for deterministic hash
            if item in self.ignored_patterns:
                continue
            
            child_path = os.path.join(path, item)
            try:
                children[item] = self._build_recursive(child_path)
            except (OSError, PermissionError):
                # Skip files we can't read
                continue
        
        # Calculate directory hash from children
        child_hashes = [child.hash for child in children.values()]
        child_hashes.sort()  # Ensure deterministic hash
        combined = "|".join(child_hashes)
        dir_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return MerkleNode.create_directory(name, path, dir_hash, children)

    def get_root_hash(self) -> str:
        """Get the root hash of the tree."""
        if not self.root:
            raise EmptyTreeError("Tree is empty")
        return self.root.hash

    def find_differences(self, other_tree: "MerkleTree") -> List[str]:
        """
        Compare with another tree and return list of changed file paths.
        This is the core algorithm for incremental sync.
        """
        if not self.root or not other_tree.root:
            return []
        
        changed_files = []
        self._compare_nodes(self.root, other_tree.root, changed_files)
        return changed_files

    def _compare_nodes(self, node1: MerkleNode, node2: MerkleNode, changed_files: List[str]) -> None:
        """
        Recursive tree traversal to find differences.
        Optimization: stops descending when hashes match (entire subtree is identical).
        """
        if node1.hash == node2.hash:
            # Hashes match - entire subtree is identical, stop here
            return
        
        if node1.is_file:
            # File changed
            changed_files.append(node1.path)
            return
        
        # Directory changed - compare children
        node1_children = set(node1.children.keys()) if node1.children else set()
        node2_children = set(node2.children.keys()) if node2.children else set()
        
        # Files added or removed
        for child_name in node1_children - node2_children:
            self._add_all_files(node1.children[child_name], changed_files)
        
        for child_name in node2_children - node1_children:
            self._add_all_files(node2.children[child_name], changed_files)
        
        # Files that exist in both - recurse
        for child_name in node1_children & node2_children:
            self._compare_nodes(
                node1.children[child_name], 
                node2.children[child_name], 
                changed_files
            )

    def _add_all_files(self, node: MerkleNode, changed_files: List[str]) -> None:
        """Add all files in a subtree to the changed list."""
        if node.is_file:
            changed_files.append(node.path)
        else:
            for child in node.children.values():
                self._add_all_files(child, changed_files)

    def to_dict(self) -> Dict:
        """Serialize tree to dictionary for client-server communication."""
        if not self.root:
            return {"root": None, "root_path": self.root_path}
        
        return {
            "root": self._node_to_dict(self.root),
            "root_path": self.root_path
        }

    def _node_to_dict(self, node: MerkleNode) -> Dict:
        """Convert node to dictionary recursively."""
        result = {
            "name": node.name,
            "path": node.path,
            "hash": node.hash,
            "is_file": node.is_file
        }
        
        if not node.is_file and node.children:
            result["children"] = {
                name: self._node_to_dict(child) 
                for name, child in node.children.items()
            }
        
        return result

    @classmethod
    def from_dict(cls, data: Dict) -> "MerkleTree":
        """Reconstruct tree from dictionary."""
        tree = cls()
        tree.root_path = data.get("root_path")
        
        if data["root"]:
            tree.root = cls._node_from_dict(data["root"])
        
        return tree

    @classmethod
    def _node_from_dict(cls, data: Dict) -> MerkleNode:
        """Reconstruct node from dictionary recursively."""
        if data["is_file"]:
            return MerkleNode.create_file(
                data["name"], 
                data["path"], 
                data["hash"]
            )
        else:
            children = {}
            if "children" in data:
                children = {
                    name: cls._node_from_dict(child_data)
                    for name, child_data in data["children"].items()
                }
            
            return MerkleNode.create_directory(
                data["name"],
                data["path"], 
                data["hash"],
                children
            )

    def get_file_count(self) -> int:
        """Count total files in the tree."""
        if not self.root:
            return 0
        return self._count_files(self.root)

    def _count_files(self, node: MerkleNode) -> int:
        """Count files recursively."""
        if node.is_file:
            return 1
        
        count = 0
        if node.children:
            for child in node.children.values():
                count += self._count_files(child)
        return count

    def __str__(self) -> str:
        """String representation of the tree."""
        if not self.root:
            return "MerkleTree(empty)"
        
        file_count = self.get_file_count()
        root_hash = self.root.hash[:8] + "..."
        return f"MerkleTree(files={file_count}, root={root_hash})"
    
    def __len__(self) -> int:
        """Return number of files in the tree."""
        return self.get_file_count() 