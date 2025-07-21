"""Merkle Tree Node implementation."""

from asyncio import streams
import hashlib
import re
from typing import Optional, Dict
from .exceptions import InvalidHashError


class MerkleNode:
    """
    Represents a node in a Merkle Tree, a node can be a file (leaf) or a directory (internal).
    
    Can be either a leaf node (containing data hash) or internal node
    (containing hash of concatenated children hashes).
    """

    __slots__ = ["name", "path", "hash", "is_file", "children"]

    def __init__(
        self, 
        name: str, 
        path: str, 
        is_file: bool, 
        children: Optional[Dict[str, "MerkleNode"]]
    ) -> None:
        
        self.name = name
        self.path = path
        self.is_file = is_file
        self.children = children

        self._hash_calculated = False
        self._hash = None

    @classmethod
    def create_file_node(cls, name: str, path: str, hash: str) -> "MerkleNode":
        return cls(name, path, hash, True, None)
    
    @classmethod
    def create_directory_node(cls, name: str, path: str, children: Dict[str, "MerkleNode"]) -> "MerkleNode":
        return cls(name, path, False, children)

    @property
    def hash(self) -> str:
        pass
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MerkleNode):
            return False
        return self.name == other.name and self.path == other.path and self.is_file == other.is_file and self.children == other.children