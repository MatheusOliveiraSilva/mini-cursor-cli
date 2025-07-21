"""Merkle Tree Node implementation."""

import hashlib
import re
from typing import Optional
from .exceptions import InvalidHashError


class MerkleNode:
    """
    Represents a node in a Merkle Tree.
    
    Can be either a leaf node (containing data hash) or internal node
    (containing hash of concatenated children hashes).
    """
    
    def __init__(
        self, 
        hash_value: str,
        left: Optional["MerkleNode"] = None,
        right: Optional["MerkleNode"] = None,
        is_leaf: bool = False
    ):
        """
        Initialize a Merkle Tree node.
        
        Args:
            hash_value: SHA-256 hash as hex string
            left: Left child node (for internal nodes)
            right: Right child node (for internal nodes)  
            is_leaf: Whether this is a leaf node
            
        Raises:
            InvalidHashError: If hash_value is not valid SHA-256 hex
        """
        self.hash = self._validate_hash(hash_value)
        self.left = left
        self.right = right
        self.is_leaf = is_leaf
    
    @staticmethod
    def _validate_hash(hash_value: str) -> str:
        """
        Validate that the provided hash is a valid SHA-256 hex string.
        
        Args:
            hash_value: Hash string to validate
            
        Returns:
            The validated hash string
            
        Raises:
            InvalidHashError: If hash is not valid SHA-256 hex
        """
        if not isinstance(hash_value, str):
            raise InvalidHashError(f"Hash must be string, got {type(hash_value)}")
            
        # SHA-256 produces 64 character hex string
        if len(hash_value) != 64:
            raise InvalidHashError(f"SHA-256 hash must be 64 characters, got {len(hash_value)}")
            
        # Check if it's valid hexadecimal
        if not re.match(r'^[a-fA-F0-9]{64}$', hash_value):
            raise InvalidHashError(f"Hash must be valid hexadecimal: {hash_value}")
            
        return hash_value.lower()
    
    @staticmethod
    def create_leaf(data_hash: str) -> "MerkleNode":
        """
        Create a leaf node from a data hash.
        
        Args:
            data_hash: SHA-256 hash of the data chunk
            
        Returns:
            New leaf node
        """
        return MerkleNode(data_hash, is_leaf=True)
    
    @staticmethod
    def create_internal(left: "MerkleNode", right: "MerkleNode") -> "MerkleNode":
        """
        Create an internal node from two child nodes.
        
        Args:
            left: Left child node
            right: Right child node
            
        Returns:
            New internal node with hash of concatenated child hashes
        """
        # Concatenate child hashes and compute SHA-256
        combined_hash = left.hash + right.hash
        parent_hash = hashlib.sha256(combined_hash.encode('utf-8')).hexdigest()
        
        return MerkleNode(parent_hash, left=left, right=right, is_leaf=False)
    
    def __str__(self) -> str:
        """String representation of the node."""
        node_type = "Leaf" if self.is_leaf else "Internal"
        return f"{node_type}Node(hash={self.hash[:8]}...)"
    
    def __repr__(self) -> str:
        """Developer representation of the node."""
        return (f"MerkleNode(hash='{self.hash}', "
                f"is_leaf={self.is_leaf}, "
                f"has_children={self.left is not None})")
    
    def __eq__(self, other) -> bool:
        """Check equality based on hash value."""
        if not isinstance(other, MerkleNode):
            return False
        return self.hash == other.hash 