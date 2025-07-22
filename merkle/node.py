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

    __slots__ = ["name", "path", "hash", "children"]

    def __init__(
        self, 
        name: str, 
        path: str,
        hash: str,
        children: Optional[Dict[str, "MerkleNode"]]
    ) -> None:
        
        self.name = name
        self.path = path
        self.hash = hash
        self.children = children

    def _validate_hash(self, hash: str) -> None:
        if not re.match(r"^[0-9a-fA-F]{64}$", hash):
            raise InvalidHashError(f"Invalid hash: {hash}")

    @classmethod
    def create_file_node(cls, name: str, path: str, hash: str) -> "MerkleNode":
        cls._validate_hash(hash)
        return cls(name, path, hash, hash)
    
    @classmethod
    def create_directory_node(cls, name: str, path: str, combined_hash: str, children: Dict[str, "MerkleNode"]) -> "MerkleNode":
        cls._validate_hash(combined_hash)
        return cls(name, path, combined_hash, children)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MerkleNode):
            return False
        return self.hash == other.hash