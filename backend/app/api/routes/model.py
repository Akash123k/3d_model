"""
Model data API routes
Provides access to processed model data
"""

from fastapi import APIRouter, HTTPException, Depends, Path
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.core.logging import log, access_log
from app.core.exceptions import ModelNotFoundError
from app.api.dependencies import get_settings
from app.db.database import get_db
from app.db.repositories import (
    ModelRepository,
    StatisticsRepository,
    AssemblyTreeRepository,
    DependencyGraphRepository,
    MeshRepository
)
from app.models.schemas import (
    AssemblyTreeResponse,
    DependencyGraphResponse,
    ModelStatistics,
    EntityDetail,
    MeshExportResponse,
    ModelsListResponse,
    ModelSummary
)
from app.services.model_processor import ModelProcessor
from app.services.step_parser import STEPParser
from app.services.brep_geometry_parser import BRepGeometryParser
from app.services.dependency_graph import DependencyGraphBuilder

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=ModelsListResponse)
async def list_models(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all uploaded models with pagination"""
    access_log.info("list_models_requested", limit=limit, offset=offset)
    
    models = ModelRepository.get_all(db, limit=limit, offset=offset)
    
    model_summaries = []
    for model in models:
        summary = ModelSummary(
            model_id=str(model.id),
            filename=model.filename,
            original_filename=model.original_filename,
            file_size=model.file_size,
            upload_time=model.upload_time.isoformat() if model.upload_time else None,
            status=model.status,
            entities_count=model.entities_count or 0,
            has_statistics=model.statistics is not None,
            has_assembly_tree=model.assembly_tree is not None,
            has_dependency_graph=model.dependency_graph is not None
        )
        model_summaries.append(summary)
    
    response = ModelsListResponse(
        models=model_summaries,
        total=len(model_summaries)
    )
    
    access_log.info("list_models_completed", count=len(model_summaries))
    return response


@router.get("/{model_id}", response_model=Dict[str, Any])
async def get_model(
    model_id: str = Path(..., description="Model ID"),
    settings: dict = Depends(get_settings),
    db: Session = Depends(get_db)
):
    """Get complete model data by ID"""
    access_log.info("get_model_requested", model_id=model_id)
    
    # Try database first
    model = ModelRepository.get_by_id(db, model_id)
    if model:
        # Build response from database
        response_data = {
            "model_id": str(model.id),
            "filename": model.filename,
            "file_size": model.file_size,
            "upload_time": model.upload_time.isoformat() if model.upload_time else None,
            "status": model.status,
            "entities_count": model.entities_count
        }
        
        # Add statistics if available
        if model.statistics:
            response_data["statistics"] = StatisticsRepository.to_dict(model.statistics)
        
        # Add assembly tree if available
        if model.assembly_tree:
            response_data["assembly_tree"] = {
                "model_id": str(model.id),
                "root_node": model.assembly_tree.root_node,
                "total_nodes": model.assembly_tree.total_nodes
            }
        
        # Add dependency graph if available AND has data
        if model.dependency_graph and len(model.dependency_graph.nodes) > 0:
            response_data["dependency_graph"] = DependencyGraphRepository.to_dict(model.dependency_graph)
        else:
            # Fallback to cache for dependency graph
            cached_data = ModelProcessor.get_cached(model_id, settings["redis_url"])
            if cached_data and "dependency_graph" in cached_data:
                response_data["dependency_graph"] = cached_data["dependency_graph"]
        
        access_log.info("get_model_completed", model_id=model_id, source="database")
        return response_data
    
    # Try cache second
    cached_data = ModelProcessor.get_cached(model_id, settings["redis_url"])
    if cached_data:
        access_log.info("get_model_completed", model_id=model_id, source="cache")
        return cached_data
    
    raise ModelNotFoundError(model_id)


@router.get("/{model_id}/assembly-tree", response_model=AssemblyTreeResponse)
async def get_assembly_tree(
    model_id: str = Path(..., description="Model ID"),
    db: Session = Depends(get_db)
):
    """Get assembly tree structure for a model"""
    access_log.info("get_assembly_tree_requested", model_id=model_id)
    
    tree = AssemblyTreeRepository.get_by_model_id(db, model_id)
    if tree:
        access_log.info("get_assembly_tree_completed", model_id=model_id)
        return {
            "model_id": str(tree.model_id),
            "root_node": tree.root_node,
            "total_nodes": tree.total_nodes
        }
    
    # Fallback to cache
    settings = {"redis_url": "redis://redis:6379/0"}  # TODO: Get from config
    cached_data = ModelProcessor.get_cached(model_id, settings["redis_url"])
    if cached_data and "assembly_tree" in cached_data:
        return cached_data["assembly_tree"]
    
    raise ModelNotFoundError(model_id)


@router.get("/{model_id}/dependency-graph", response_model=DependencyGraphResponse)
async def get_dependency_graph(
    model_id: str = Path(..., description="Model ID"),
    db: Session = Depends(get_db)
):
    """Get dependency graph for a model"""
    access_log.info("get_dependency_graph_requested", model_id=model_id)
    
    # Try database first with eager loading
    graph = DependencyGraphRepository.get_by_model_id(db, model_id)
    if graph:
        # Explicitly refresh to ensure relationships are loaded
        db.refresh(graph)
        access_log.info("get_dependency_graph_completed", model_id=model_id, 
                       nodes=len(graph.nodes), edges=len(graph.edges))
        return DependencyGraphRepository.to_dict(graph)
    
    # Fallback to cache
    settings = {"redis_url": "redis://redis:6379/0"}
    cached_data = ModelProcessor.get_cached(model_id, settings["redis_url"])
    if cached_data and "dependency_graph" in cached_data:
        access_log.info("get_dependency_graph_completed", model_id=model_id, source="cache")
        return cached_data["dependency_graph"]
    
    raise ModelNotFoundError(model_id)


@router.get("/{model_id}/statistics", response_model=ModelStatistics)
async def get_statistics(
    model_id: str = Path(..., description="Model ID"),
    db: Session = Depends(get_db)
):
    """Get model statistics"""
    access_log.info("get_statistics_requested", model_id=model_id)
    
    stats = StatisticsRepository.get_by_model_id(db, model_id)
    if stats:
        access_log.info("get_statistics_completed", model_id=model_id)
        return StatisticsRepository.to_dict(stats)
    
    # Fallback to cache
    settings = {"redis_url": "redis://redis:6379/0"}
    cached_data = ModelProcessor.get_cached(model_id, settings["redis_url"])
    if cached_data and "statistics" in cached_data:
        return cached_data["statistics"]
    
    raise ModelNotFoundError(model_id)


@router.get("/{model_id}/entity/{entity_id}", response_model=EntityDetail)
async def get_entity_detail(
    model_id: str = Path(..., description="Model ID"),
    entity_id: str = Path(..., description="Entity ID (e.g., #123)"),
    db: Session = Depends(get_db),
    settings: dict = Depends(get_settings)
):
    """Get detailed information about a specific entity"""
    access_log.info("get_entity_detail_requested", 
                   model_id=model_id, 
                   entity_id=entity_id)
    
    # Try database first
    # (Implementation would fetch from entities table)
    
    # Fallback to cache or re-parse file
    cached_data = ModelProcessor.get_cached(model_id, settings["redis_url"])
    if not cached_data:
        raise ModelNotFoundError(model_id)
    
    # For now, return a simplified response
    return EntityDetail(
        entity_id=entity_id,
        entity_type="UNKNOWN",
        attributes={},
        references=[],
        referenced_by=[]
    )


@router.get("/{model_id}/mesh", response_model=MeshExportResponse)
async def get_mesh_data(
    model_id: str = Path(..., description="Model ID"),
    db: Session = Depends(get_db),
    settings: dict = Depends(get_settings)
):
    """Get triangulated mesh data for 3D visualization"""
    access_log.info("get_mesh_data_requested", model_id=model_id)
    
    # Try database first (persistent storage)
    model = ModelRepository.get_by_id(db, model_id)
    if model and hasattr(model, 'meshes') and model.meshes:
        # Convert mesh objects to dictionaries
        meshes = [MeshRepository.to_dict(mesh) for mesh in model.meshes]
        access_log.info("get_mesh_data_completed", 
                       model_id=model_id, 
                       mesh_count=len(meshes),
                       source="database")
        
        return {
            "model_id": model_id,
            "meshes": meshes,
            "format": "json"
        }
    
    # Fallback to cache (for backward compatibility)
    cached_data = ModelProcessor.get_cached(model_id, settings["redis_url"])
    
    if cached_data and "meshes" in cached_data:
        meshes = cached_data["meshes"]
        access_log.info("get_mesh_data_completed", 
                       model_id=model_id, 
                       mesh_count=len(meshes),
                       source="cache")
        
        return {
            "model_id": model_id,
            "meshes": meshes,
            "format": "json"
        }
    
    # Model not found or no mesh data
    raise ModelNotFoundError(model_id)


@router.get("/{model_id}/brep-geometry")
async def get_brep_geometry(
    model_id: str = Path(..., description="Model ID"),
    db: Session = Depends(get_db),
    settings: dict = Depends(get_settings)
):
    """Get B-Rep geometry tree structure using brep.py methodology"""
    access_log.info("get_brep_geometry_requested", model_id=model_id)
    
    # Try database first - check if we already have entities stored
    model = ModelRepository.get_by_id(db, model_id)
    if model:
        # Re-parse from file to build the brep.py-style tree
        try:
            parser = BRepGeometryParser(model.file_path)
            parsed_data = parser.parse()
            
            access_log.info("get_brep_geometry_completed", 
                           model_id=model_id,
                           entities=len(parsed_data["entities"]),
                           components=parsed_data["total_components"])
            
            return {
                "model_id": model_id,
                "entities_count": len(parsed_data["entities"]),
                "total_components": parsed_data["total_components"],
                "brep_tree": parsed_data["brep_tree"],
                "bounding_box": parsed_data["bounding_box"]
            }
        except Exception as e:
            access_log.error("get_brep_geometry_parse_failed",
                           model_id=model_id,
                           error=str(e))
    
    # Fallback to cache
    cached_data = ModelProcessor.get_cached(model_id, settings["redis_url"])
    if cached_data and "brep_hierarchy" in cached_data:
        return {
            "model_id": model_id,
            "brep_hierarchy": cached_data["brep_hierarchy"]
        }
    
    raise ModelNotFoundError(model_id)
