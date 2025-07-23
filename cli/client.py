"""HTTP client for communicating with mini-cursor-cli server.

Handles all server communication including health checks, project registration,
and Merkle tree synchronization.
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path

import httpx
from rich.console import Console

from merkle.tree import MerkleTree
from merkle.exceptions import MerkleTreeError


class ServerConnectionError(Exception):
    """Raised when unable to connect to server."""
    pass


class ClientError(Exception):
    """Raised when client operation fails."""
    pass


class MiniCursorClient:
    """HTTP client for mini-cursor-cli server communication."""
    
    def __init__(self, server_url: str = "http://localhost:8000", timeout: float = 10.0):
        """
        Initialize the client.
        
        Args:
            server_url: Base URL of the server
            timeout: HTTP request timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.console = Console()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    async def check_server_health(self) -> Dict[str, Any]:
        """
        Check if server is healthy and reachable.
        
        Returns:
            Server health information
            
        Raises:
            ServerConnectionError: If server is unreachable
        """
        try:
            if not self._client:
                raise ClientError("Client not initialized - use async context manager")
            
            response = await self._client.get(f"{self.server_url}/health")
            response.raise_for_status()
            
            health_data = response.json()
            return health_data
            
        except httpx.ConnectError:
            raise ServerConnectionError(
                f"Cannot connect to server at {self.server_url}. "
                "Make sure the server is running.\n"
                "📖 Check README.md for setup instructions."
            )
        except httpx.TimeoutException:
            raise ServerConnectionError(
                f"Server at {self.server_url} is not responding (timeout: {self.timeout}s)"
            )
        except httpx.HTTPStatusError as e:
            raise ServerConnectionError(
                f"Server returned error {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            raise ServerConnectionError(f"Unexpected error connecting to server: {str(e)}")
    
    async def register_project(self, project_path: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Register a project with the server.
        
        Args:
            project_path: Absolute path to the project
            project_name: Optional project name (defaults to directory name)
            
        Returns:
            Registration response data
            
        Raises:
            ClientError: If registration fails
            ServerConnectionError: If server communication fails
        """
        try:
            if not self._client:
                raise ClientError("Client not initialized - use async context manager")
            
            abs_path = os.path.abspath(project_path)
            if not os.path.exists(abs_path):
                raise ClientError(f"Project path does not exist: {abs_path}")
            
            request_data = {
                "project_path": abs_path,
                "project_name": project_name
            }
            
            response = await self._client.post(
                f"{self.server_url}/register",
                json=request_data
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", "Unknown error")
            raise ClientError(f"Failed to register project: {error_detail}")
        except httpx.RequestError as e:
            raise ServerConnectionError(f"Request failed: {str(e)}")
        except Exception as e:
            raise ClientError(f"Unexpected error during registration: {str(e)}")
    
    async def sync_project(self, project_path: str) -> Dict[str, Any]:
        """
        Synchronize project Merkle tree with server.
        
        Args:
            project_path: Absolute path to the project
            
        Returns:
            Sync response data
            
        Raises:
            ClientError: If sync fails
            ServerConnectionError: If server communication fails
        """
        try:
            if not self._client:
                raise ClientError("Client not initialized - use async context manager")
            
            abs_path = os.path.abspath(project_path)
            if not os.path.exists(abs_path):
                raise ClientError(f"Project path does not exist: {abs_path}")
            
            # Build local Merkle tree
            try:
                tree = MerkleTree(abs_path)
                tree_dict = tree.to_dict()
            except MerkleTreeError as e:
                raise ClientError(f"Failed to build Merkle tree: {str(e)}")
            
            request_data = {
                "project_id": abs_path,  # Using absolute path as project ID
                "client_tree": tree_dict
            }
            
            response = await self._client.post(
                f"{self.server_url}/sync",
                json=request_data
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", "Unknown error")
            raise ClientError(f"Failed to sync project: {error_detail}")
        except httpx.RequestError as e:
            raise ServerConnectionError(f"Request failed: {str(e)}")
        except Exception as e:
            raise ClientError(f"Unexpected error during sync: {str(e)}")
    
    async def list_projects(self) -> Dict[str, Any]:
        """
        List all projects registered on the server.
        
        Returns:
            Projects list data
            
        Raises:
            ServerConnectionError: If server communication fails
        """
        try:
            if not self._client:
                raise ClientError("Client not initialized - use async context manager")
            
            response = await self._client.get(f"{self.server_url}/projects")
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", "Unknown error")
            raise ClientError(f"Failed to list projects: {error_detail}")
        except httpx.RequestError as e:
            raise ServerConnectionError(f"Request failed: {str(e)}")
        except Exception as e:
            raise ClientError(f"Unexpected error listing projects: {str(e)}")
    
    def format_server_error(self, error: Exception) -> str:
        """
        Format server connection errors for user display.
        
        Args:
            error: The exception to format
            
        Returns:
            Formatted error message
        """
        if isinstance(error, ServerConnectionError):
            return f"🔴 [bold red]Server Connection Error[/bold red]\n{str(error)}"
        elif isinstance(error, ClientError):
            return f"🔴 [bold red]Client Error[/bold red]\n{str(error)}"
        else:
            return f"🔴 [bold red]Unexpected Error[/bold red]\n{str(error)}"


def detect_project_root(start_path: str = ".") -> Optional[str]:
    """
    Detect the project root directory by looking for common markers.
    
    Args:
        start_path: Path to start searching from
        
    Returns:
        Absolute path to project root, or None if not found
    """
    current = Path(start_path).resolve()
    
    # Common project markers
    markers = {
        ".git",
        "pyproject.toml", 
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "requirements.txt",
        "setup.py"
    }
    
    # Search upward from current directory
    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            return str(parent)
    
    # If no markers found, use the starting directory
    return str(current) 