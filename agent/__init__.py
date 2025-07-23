"""
Agent package for mini-cursor-cli.

Contains the FastAPI server and related functionality for handling
client-server communication and Merkle tree synchronization.
"""

from .server import app, start_server

__all__ = ["app", "start_server"] 