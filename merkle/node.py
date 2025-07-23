"""Merkle Tree Node implementation."""

import hashlib
import re
from typing import Optional, Dict
from .exceptions import InvalidHashError


class MerkleNode:
    """
    Represents a node in a Merkle Tree.
    
    Can be either a file node (leaf) or directory node (internal).
    Follows Cursor's architecture: files as leaves, directories as internal nodes.
    """

    __slots__ = ["name", "path", "hash", "is_file", "children"]

    def __init__(
        self, 
        name: str, 
        path: str,
        hash: str,
        is_file: bool,
        children: Optional[Dict[str, "MerkleNode"]] = None
    ) -> None:
        """
        Initialize a Merkle Tree node.
        
        Args:
            name: File or directory name
            path: Full path to file or directory
            hash: SHA-256 hash of content (file) or children (directory)
            is_file: True if file, False if directory
            children: Dictionary of child nodes (None for files)
        """
        self.name = name
        self.path = path
        self.hash = self._validate_hash(hash)
        self.is_file = is_file
        self.children = children if not is_file else None

    @staticmethod
    def _validate_hash(hash_value: str) -> str:
        """
        Validate that the provided hash is a valid SHA-256 hex string.
        
        Args:
            hash_value: Hash string to validate
            
        Returns:
            The validated hash string (lowercase)
            
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

    @classmethod
    def create_file_node(cls, name: str, path: str, content_hash: str) -> "MerkleNode":
        """
        Create a file node (leaf) with content hash.
        
        Args:
            name: File name
            path: Full file path
            content_hash: SHA-256 hash of file content
            
        Returns:
            New file node
        """
        return cls(name=name, path=path, hash=content_hash, is_file=True)
    
    @classmethod
    def create_directory_node(
        cls, 
        name: str, 
        path: str, 
        combined_hash: str, 
        children: Dict[str, "MerkleNode"]
    ) -> "MerkleNode":
        """
        Create a directory node (internal) with children.
        
        Args:
            name: Directory name
            path: Full directory path
            combined_hash: SHA-256 hash of children hashes
            children: Dictionary of child nodes
            
        Returns:
            New directory node
        """
        return cls(
            name=name, 
            path=path, 
            hash=combined_hash, 
            is_file=False, 
            children=children
        )
    
    def add_child(self, child: "MerkleNode") -> None:
        """
        Add a child node to this directory node.
        
        Args:
            child: Child node to add
            
        Raises:
            ValueError: If this is a file node
        """
        if self.is_file:
            raise ValueError("Cannot add child to file node")
        
        if self.children is None:
            self.children = {}
        
        self.children[child.name] = child
    
    def get_child(self, name: str) -> Optional["MerkleNode"]:
        """
        Get a child node by name.
        
        Args:
            name: Child name to lookup
            
        Returns:
            Child node or None if not found
        """
        if self.is_file or not self.children:
            return None
        
        return self.children.get(name)
    
    def __str__(self) -> str:
        """String representation of the node."""
        node_type = "File" if self.is_file else "Directory"
        return f"{node_type}({self.name}, hash={self.hash[:8]}...)"
    
    def __repr__(self) -> str:
        """Developer representation of the node."""
        return (f"MerkleNode(name='{self.name}', path='{self.path}', "
                f"hash='{self.hash}', is_file={self.is_file})")
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on hash value."""
        if not isinstance(other, MerkleNode):
            return False
        return self.hash == other.hash