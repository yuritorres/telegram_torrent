"""
Advanced Docker API Routes
Comprehensive Docker management endpoints inspired by Pulse
All routes are protected with authentication
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Optional, List
from datetime import datetime
import logging
from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/docker-advanced", tags=["docker-advanced"])

# This will be set by main.py
_app_state = None

def set_app_state(app_state):
    """Set the app_state reference"""
    global _app_state
    _app_state = app_state


def get_docker_manager():
    """Dependency to get Docker manager"""
    if _app_state is None:
        raise HTTPException(status_code=500, detail="Application not initialized")
    if not _app_state.docker or not _app_state.docker.is_available():
        raise HTTPException(status_code=503, detail="Docker not available")
    return _app_state.docker


# Container Management Endpoints

@router.get("/system/info")
async def get_docker_system_info(
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Get Docker system information (requires authentication)"""
    info = docker_manager.get_system_info()
    if not info:
        raise HTTPException(status_code=500, detail="Failed to get system info")
    return info


@router.get("/containers")
async def list_containers(
    all: bool = Query(True, description="Include stopped containers"),
    status: Optional[str] = Query(None, description="Filter by status (running, exited, etc)"),
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """List all Docker containers with enhanced metadata (requires authentication)"""
    filters = {}
    if status:
        filters['status'] = status
    
    containers = docker_manager.list_containers(all=all, filters=filters if filters else None)
    return {
        "containers": containers,
        "total": len(containers),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/containers/{container_id}/inspect")
async def inspect_container(
    container_id: str,
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Get detailed container inspection data (requires authentication)"""
    inspection = docker_manager.inspect_container(container_id)
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    return inspection


@router.get("/containers/{container_id}/stats")
async def get_container_stats(
    container_id: str,
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Get container resource usage statistics (requires authentication)"""
    stats = docker_manager.get_container_stats(container_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found or stats unavailable")
    return stats


@router.get("/containers/{container_id}/logs")
async def get_container_logs(
    container_id: str,
    tail: int = Query(100, description="Number of lines to return"),
    since: Optional[str] = Query(None, description="Show logs since timestamp or relative time"),
    timestamps: bool = Query(True, description="Include timestamps"),
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Get container logs (requires authentication)"""
    logs = docker_manager.get_container_logs(
        container_id,
        tail=tail,
        since=since,
        timestamps=timestamps
    )
    if logs is None:
        raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
    
    return {
        "container_id": container_id,
        "logs": logs,
        "tail": tail,
        "timestamp": datetime.now().isoformat()
    }


# Container Actions

@router.post("/containers/{container_id}/start")
async def start_container(
    container_id: str,
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Start a container (requires authentication)"""
    success, message = docker_manager.start_container(container_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.post("/containers/{container_id}/stop")
async def stop_container(
    container_id: str,
    timeout: int = Query(10, description="Timeout in seconds"),
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Stop a container (requires authentication)"""
    success, message = docker_manager.stop_container(container_id, timeout=timeout)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.post("/containers/{container_id}/restart")
async def restart_container(
    container_id: str,
    timeout: int = Query(10, description="Timeout in seconds"),
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Restart a container (requires authentication)"""
    success, message = docker_manager.restart_container(container_id, timeout=timeout)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.post("/containers/{container_id}/pause")
async def pause_container(
    container_id: str,
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Pause a container (requires authentication)"""
    success, message = docker_manager.pause_container(container_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.post("/containers/{container_id}/unpause")
async def unpause_container(
    container_id: str,
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Unpause a container (requires authentication)"""
    success, message = docker_manager.unpause_container(container_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.delete("/containers/{container_id}")
async def remove_container(
    container_id: str,
    force: bool = Query(False, description="Force removal of running container"),
    volumes: bool = Query(False, description="Remove associated volumes"),
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Remove a container (requires authentication)"""
    success, message = docker_manager.remove_container(container_id, force=force, volumes=volumes)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


# Docker Compose Stack Management

@router.get("/stacks")
async def list_compose_stacks(
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """List all Docker Compose stacks (projects) (requires authentication)"""
    stacks = docker_manager.get_compose_stacks()
    return {
        "stacks": stacks,
        "total": len(stacks),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/stacks/{stack_name}/start")
async def start_stack(
    stack_name: str,
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Start all containers in a Docker Compose stack (requires authentication)"""
    stacks = docker_manager.get_compose_stacks()
    stack = next((s for s in stacks if s['name'] == stack_name), None)
    
    if not stack:
        raise HTTPException(status_code=404, detail=f"Stack {stack_name} not found")
    
    results = []
    for container in stack['containers']:
        if container['state'] != 'running':
            success, message = docker_manager.start_container(container['id'])
            results.append({
                "container": container['name'],
                "success": success,
                "message": message
            })
    
    return {
        "stack": stack_name,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/stacks/{stack_name}/stop")
async def stop_stack(
    stack_name: str,
    timeout: int = Query(10, description="Timeout in seconds"),
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Stop all containers in a Docker Compose stack (requires authentication)"""
    stacks = docker_manager.get_compose_stacks()
    stack = next((s for s in stacks if s['name'] == stack_name), None)
    
    if not stack:
        raise HTTPException(status_code=404, detail=f"Stack {stack_name} not found")
    
    results = []
    for container in stack['containers']:
        if container['state'] == 'running':
            success, message = docker_manager.stop_container(container['id'], timeout=timeout)
            results.append({
                "container": container['name'],
                "success": success,
                "message": message
            })
    
    return {
        "stack": stack_name,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/stacks/{stack_name}/restart")
async def restart_stack(
    stack_name: str,
    timeout: int = Query(10, description="Timeout in seconds"),
    current_user: Dict = Depends(get_current_user),
    docker_manager=Depends(get_docker_manager)
):
    """Restart all containers in a Docker Compose stack (requires authentication)"""
    stacks = docker_manager.get_compose_stacks()
    stack = next((s for s in stacks if s['name'] == stack_name), None)
    
    if not stack:
        raise HTTPException(status_code=404, detail=f"Stack {stack_name} not found")
    
    results = []
    for container in stack['containers']:
        success, message = docker_manager.restart_container(container['id'], timeout=timeout)
        results.append({
            "container": container['name'],
            "success": success,
            "message": message
        })
    
    return {
        "stack": stack_name,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }
