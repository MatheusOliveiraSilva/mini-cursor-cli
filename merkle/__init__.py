"""
Merkle Tree implementation for code chunk indexing.

This module provides a manual implementation of Merkle Trees using SHA-256 hashing
for tracking changes in code chunks and enabling incremental reindexing.
"""

from .node import MerkleNode
from .tree import MerkleTree
from .exceptions import MerkleTreeError, InvalidHashError

__all__ = ["MerkleNode", "MerkleTree", "MerkleTreeError", "InvalidHashError"]
