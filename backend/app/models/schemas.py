"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class GeometryType(str, Enum):
    """Types of geometry entities in STEP files"""
    CARTESIAN_POINT = "CARTESIAN_POINT"
    EDGE_CURVE = "EDGE_CURVE"
    ADVANCED_FACE = "ADVANCED_FACE"
    MANIFOLD_SOLID_BREP = "MANIFOLD_SOLID_BREP"
    LINE = "LINE"
    CIRCLE = "CIRCLE"
    PLANE = "PLANE"
    CYLINDRICAL_SURFACE = "CYLINDRICAL_SURFACE"
    VERTEX_POINT = "VERTEX_POINT"
    FACE_BOUND = "FACE_BOUND"
    EDGE_LOOP = "EDGE_LOOP"
    SHELL = "SHELL"


# Upload schemas
class FileUploadResponse(BaseModel):
    """Response after file upload"""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str
    filename: str
    file_size: int
    upload_time: datetime
    status: str = "processing"


class ModelSummary(BaseModel):
    """Summary of a model for listing"""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str
    filename: str
    original_filename: str
    file_size: int
    upload_time: datetime
    status: str
    entities_count: int
    has_statistics: bool = False
    has_assembly_tree: bool = False
    has_dependency_graph: bool = False


class ModelsListResponse(BaseModel):
    """Response for listing all models"""
    models: List[ModelSummary]
    total: int


# Assembly tree schemas
class AssemblyNode(BaseModel):
    """Node in the assembly tree"""
    id: str
    name: str
    type: str
    children: List["AssemblyNode"] = []
    parent_id: Optional[str] = None
    properties: Dict[str, Any] = {}
    
    class Config:
        recursive = True


class AssemblyTreeResponse(BaseModel):
    """Complete assembly tree response"""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str
    root_node: AssemblyNode
    total_nodes: int


# Geometry schemas
class Vertex(BaseModel):
    """3D vertex coordinates"""
    x: float
    y: float
    z: float


class Edge(BaseModel):
    """Edge with vertices"""
    id: str
    type: str
    vertices: List[Vertex] = []
    curve_type: Optional[str] = None


class Face(BaseModel):
    """Face with edges"""
    id: str
    type: str
    edges: List[Edge] = []
    surface_type: Optional[str] = None
    area: Optional[float] = None


class Shell(BaseModel):
    """Shell with faces"""
    id: str
    faces: List[Face] = []


class Solid(BaseModel):
    """Solid with shells"""
    id: str
    type: str
    shells: List[Shell] = []
    volume: Optional[float] = None


class BRepHierarchy(BaseModel):
    """B-Rep topology hierarchy"""
    solids: List[Solid] = []
    total_solids: int
    total_faces: int
    total_edges: int
    total_vertices: int


# Statistics schemas
class BoundingBox(BaseModel):
    """3D bounding box"""
    min_point: Vertex
    max_point: Vertex
    dimensions: Vertex  # Size in each dimension


class ModelStatistics(BaseModel):
    """Model statistics"""
    model_config = ConfigDict(protected_namespaces=())
    
    total_solids: int
    total_faces: int
    total_edges: int
    total_vertices: int
    total_surfaces: int
    bounding_box: Optional[BoundingBox] = None
    total_volume: Optional[float] = None
    total_surface_area: Optional[float] = None


# Dependency graph schemas
class GraphNode(BaseModel):
    """Node in dependency graph"""
    id: str
    label: str
    type: str
    references: List[str] = []
    referenced_by: List[str] = []
    properties: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    """Edge in dependency graph"""
    source: str
    target: str
    relationship: str


class DependencyGraphResponse(BaseModel):
    """Dependency graph response"""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int


# Entity detail schema
class EntityDetail(BaseModel):
    """Detailed information about a STEP entity"""
    entity_id: str
    entity_type: str
    step_line: Optional[str] = None
    attributes: Dict[str, Any] = {}
    references: List[str] = []
    referenced_by: List[str] = []


# Mesh export schema
class MeshData(BaseModel):
    """Mesh data for Three.js"""
    vertices: List[float]
    normals: List[float]
    indices: List[int]
    material_id: Optional[str] = None


class MeshExportResponse(BaseModel):
    """Response with mesh data"""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str
    meshes: List[MeshData]
    format: str = "json"


# Error response schema
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
