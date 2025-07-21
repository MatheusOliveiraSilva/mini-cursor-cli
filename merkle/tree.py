"""Merkle Tree implementation for code chunk indexing."""

import hashlib
from typing import List, Optional
from .node import MerkleNode
from .exceptions import EmptyTreeError, InvalidIndexError

class MerkleTree:
    """
    A Merkle Tree implementation for tracking code chunk changes.
    
    Provides efficient change detection and incremental updates for code indexing.
    Handles edge cases like odd number of leaves and empty trees.
    """
    
    def __init__(self):
        """Initialize an empty Merkle Tree."""
        self._leaves: List[MerkleNode] = []
        self._root: Optional[MerkleNode] = None
        self._dirty = False  # Track if tree needs rebuilding
    
    def add_leaf(self, data_hash: str) -> None:
        """
        Add a new leaf node to the tree.
        
        Args:
            data_hash: SHA-256 hash of the data chunk as hex string
            
        Note:
            Tree is marked as dirty and will be rebuilt on next get_root() call.
        """
        leaf_node = MerkleNode.create_leaf(data_hash)
        self._leaves.append(leaf_node)
        self._dirty = True
    
    def get_root(self) -> str:
        """
        Get the root hash of the tree.
        
        Returns:
            SHA-256 hash of the root node as hex string
            
        Raises:
            EmptyTreeError: If tree has no leaves
        """
        if not self._leaves:
            raise EmptyTreeError("Cannot get root of empty tree")
        
        if self._dirty or self._root is None:
            self._rebuild_tree()
            
        return self._root.hash
    
    def get_leaf_count(self) -> int:
        """Get the number of leaf nodes in the tree."""
        return len(self._leaves)
    
    def get_leaf_hashes(self) -> List[str]:
        """Get all leaf hashes in order."""
        return [leaf.hash for leaf in self._leaves]
    
    def _rebuild_tree(self) -> None:
        """
        Rebuild the entire tree structure from current leaves.
        
        Handles edge cases:
        - Single leaf: root = leaf
        - Odd leaves: duplicate last leaf to make even pairs
        - Even leaves: build binary tree normally
        """
        if not self._leaves:
            self._root = None
            return
            
        if len(self._leaves) == 1:
            # Single leaf case: root is the leaf itself
            self._root = self._leaves[0]
            self._dirty = False
            return
        
        # Build tree level by level, bottom-up
        current_level = self._leaves.copy()
        while len(current_level) > 1:
            next_level = []
            
            # Process pairs of nodes
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                
                if i + 1 < len(current_level):
                    # We have a pair
                    right = current_level[i + 1]
                else:
                    # Odd number: duplicate the last node
                    right = current_level[i]
                
                # Create parent node
                parent = MerkleNode.create_internal(left, right)
                next_level.append(parent)
            
            current_level = next_level
        
        # The last remaining node is the root
        self._root = current_level[0]
        self._dirty = False
    
    def get_proof(self, leaf_index: int) -> List[str]:
        """
        Generate a Merkle proof for a specific leaf.
        
        Args:
            leaf_index: Index of the leaf to prove (0-based)
            
        Returns:
            List of hashes needed to verify the leaf exists
            
        Raises:
            InvalidIndexError: If leaf_index is out of range
            EmptyTreeError: If tree is empty
        """
        if not self._leaves:
            raise EmptyTreeError("Cannot generate proof for empty tree")
            
        if leaf_index < 0 or leaf_index >= len(self._leaves):
            raise InvalidIndexError(f"Leaf index {leaf_index} out of range [0, {len(self._leaves)})")
        
        if self._dirty or self._root is None:
            self._rebuild_tree()
            
        # For single leaf, proof is empty (leaf is root)
        if len(self._leaves) == 1:
            return []
        
        proof = []
        current_level = self._leaves.copy()
        current_index = leaf_index
        
        while len(current_level) > 1:
            next_level = []
            next_index = current_index // 2
            
            # Find sibling at current level
            if current_index % 2 == 0:
                # Left child - sibling is right
                sibling_index = current_index + 1
                if sibling_index < len(current_level):
                    proof.append(current_level[sibling_index].hash)
                else:
                    # Odd case: sibling is self (duplicate)
                    proof.append(current_level[current_index].hash)
            else:
                # Right child - sibling is left
                sibling_index = current_index - 1
                proof.append(current_level[sibling_index].hash)
            
            # Build next level
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else current_level[i]
                parent = MerkleNode.create_internal(left, right)
                next_level.append(parent)
            
            current_level = next_level
            current_index = next_index
        
        return proof
    
    @staticmethod
    def verify_proof(leaf_hash: str, proof: List[str], root_hash: str, leaf_index: int) -> bool:
        """
        Verify a Merkle proof.
        
        Args:
            leaf_hash: Hash of the leaf being verified
            proof: List of sibling hashes from get_proof()
            root_hash: Expected root hash
            leaf_index: Index of the leaf in the original tree
            
        Returns:
            True if proof is valid, False otherwise
        """
        if not proof:  # Single leaf case
            return leaf_hash == root_hash
            
        current_hash = leaf_hash
        current_index = leaf_index
        
        for sibling_hash in proof:
            if current_index % 2 == 0:
                # Current is left child
                combined = current_hash + sibling_hash
            else:
                # Current is right child  
                combined = sibling_hash + current_hash
                
            current_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
            current_index //= 2
        
        return current_hash == root_hash
    
    def __str__(self) -> str:
        """String representation of the tree."""
        leaf_count = len(self._leaves)
        root_hash = "None" if not self._leaves else (self.get_root()[:8] + "...")
        return f"MerkleTree(leaves={leaf_count}, root={root_hash})"
    
    def __len__(self) -> int:
        """Return number of leaves in the tree."""
        return len(self._leaves) 