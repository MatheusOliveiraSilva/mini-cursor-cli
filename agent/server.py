"""FastAPI server for mini-cursor-cli agent.

Handles project registration, Merkle tree synchronization, and provides
endpoints for the CLI client to communicate with.
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn

from merkle.tree import MerkleTree
from merkle.exceptions import MerkleTreeError


# Pydantic models for API requests/responses
class ProjectRegisterRequest(BaseModel):
    project_path: str
    project_name: Optional[str] = None


class ProjectRegisterResponse(BaseModel):
    project_id: str
    message: str
    registered_at: str


class SyncRequest(BaseModel):
    project_id: str
    client_tree: Dict[str, Any]


class SyncResponse(BaseModel):
    project_id: str
    server_has_project: bool
    trees_match: bool
    changed_files: List[str]
    sync_completed_at: str


class HealthResponse(BaseModel):
    status: str
    message: str
    projects_count: int
    uptime: str


# Global server state (in-memory storage)
class ServerState:
    def __init__(self):
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.startup_time = datetime.now()
    
    def register_project(self, project_path: str, project_name: Optional[str] = None) -> str:
        """Register a new project or update existing one."""
        abs_path = os.path.abspath(project_path)
        project_id = abs_path  # Use absolute path as unique ID
        
        if not os.path.exists(abs_path):
            raise ValueError(f"Project path does not exist: {abs_path}")
        
        # Build Merkle tree for the project
        try:
            tree = MerkleTree(abs_path)
            tree_dict = tree.to_dict()
        except Exception as e:
            raise ValueError(f"Failed to build Merkle tree: {str(e)}")
        
        # Store project data
        self.projects[project_id] = {
            "project_path": abs_path,
            "project_name": project_name or Path(abs_path).name,
            "tree": tree_dict,
            "registered_at": datetime.now(),
            "last_sync": datetime.now()
        }
        
        return project_id
    
    def sync_project(self, project_id: str, client_tree_dict: Dict[str, Any]) -> SyncResponse:
        """Synchronize client tree with server tree."""
        if project_id not in self.projects:
            # Project not registered - register it first
            try:
                # Try to rebuild from the path in client tree
                client_path = client_tree_dict.get("root_path")
                if not client_path:
                    raise ValueError("No root_path in client tree")
                
                registered_id = self.register_project(client_path)
                if registered_id != project_id:
                    raise ValueError("Project ID mismatch after registration")
                
            except Exception:
                return SyncResponse(
                    project_id=project_id,
                    server_has_project=False,
                    trees_match=False,
                    changed_files=[],
                    sync_completed_at=datetime.now().isoformat()
                )
        
        # Compare trees
        try:
            # Reconstruct trees from dictionaries
            server_tree = MerkleTree.from_dict(self.projects[project_id]["tree"])
            client_tree = MerkleTree.from_dict(client_tree_dict)
            
            # Find differences
            changed_files = server_tree.find_differences(client_tree)
            trees_match = len(changed_files) == 0
            
            # Update server tree with client tree if different
            if not trees_match:
                self.projects[project_id]["tree"] = client_tree_dict
                self.projects[project_id]["last_sync"] = datetime.now()
            
            return SyncResponse(
                project_id=project_id,
                server_has_project=True,
                trees_match=trees_match,
                changed_files=changed_files,
                sync_completed_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Tree synchronization failed: {str(e)}"
            )
    
    def get_health_info(self) -> HealthResponse:
        """Get server health information."""
        uptime = datetime.now() - self.startup_time
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        
        return HealthResponse(
            status="healthy",
            message="Mini Cursor CLI server is running",
            projects_count=len(self.projects),
            uptime=uptime_str
        )


# Initialize server state
server_state = ServerState()

# FastAPI app
app = FastAPI(
    title="Mini Cursor CLI Server",
    description="FastAPI server for mini-cursor-cli agent communication",
    version="0.1.0"
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return server_state.get_health_info()


@app.post("/register", response_model=ProjectRegisterResponse)
async def register_project(request: ProjectRegisterRequest):
    """Register a new project with the server."""
    try:
        project_id = server_state.register_project(
            request.project_path, 
            request.project_name
        )
        
        return ProjectRegisterResponse(
            project_id=project_id,
            message=f"Project registered successfully: {Path(request.project_path).name}",
            registered_at=datetime.now().isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register project: {str(e)}"
        )


@app.post("/sync", response_model=SyncResponse)
async def sync_project(request: SyncRequest):
    """Synchronize client Merkle tree with server."""
    try:
        result = server_state.sync_project(request.project_id, request.client_tree)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync operation failed: {str(e)}"
        )


@app.get("/projects")
async def list_projects():
    """List all registered projects."""
    projects_info = []
    for project_id, data in server_state.projects.items():
        projects_info.append({
            "project_id": project_id,
            "project_name": data["project_name"],
            "project_path": data["project_path"],
            "registered_at": data["registered_at"].isoformat(),
            "last_sync": data["last_sync"].isoformat(),
            "file_count": len(MerkleTree.from_dict(data["tree"]))
        })
    
    return {
        "projects_count": len(projects_info),
        "projects": projects_info
    }


def start_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """Start the FastAPI server."""
    uvicorn.run(
        "agent.server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info"
    )


if __name__ == "__main__":
    # For development - run with: python -m agent.server
    start_server(debug=True) 