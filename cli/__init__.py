"""
CLI package for mini-cursor-cli.

Contains the command-line interface, HTTP client, and chat session
functionality for interacting with the server.
"""

from .client import MiniCursorClient, detect_project_root
from .main import main
from .chat import ChatSession

__all__ = ["MiniCursorClient", "detect_project_root", "main", "ChatSession"] 