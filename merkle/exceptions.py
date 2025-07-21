"""Custom exceptions for Merkle Tree operations."""

class MerkleTreeError(Exception):
    """Base exception for all Merkle Tree related errors."""
    pass


class InvalidHashError(MerkleTreeError):
    """Raised when an invalid hash is provided to the tree."""
    pass


class EmptyTreeError(MerkleTreeError):
    """Raised when trying to get root from an empty tree."""
    pass


class InvalidIndexError(MerkleTreeError):
    """Raised when trying to access a leaf with invalid index."""
    pass 