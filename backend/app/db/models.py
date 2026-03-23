"""
SQLAlchemy models for database tables
"""

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey, Double, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Model(Base):
    """Model table - stores uploaded model metadata"""
    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False, default='processing')
    entities_count = Column(Integer, default=0)
    cache_key = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    statistics = relationship("ModelStatistics", back_populates="model", uselist=False, cascade="all, delete-orphan")
    assembly_tree = relationship("AssemblyTree", back_populates="model", uselist=False, cascade="all, delete-orphan")
    dependency_graph = relationship("DependencyGraph", back_populates="model", uselist=False, cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="model", cascade="all, delete-orphan")


class ModelStatistics(Base):
    """Model statistics table"""
    __tablename__ = "model_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_solids = Column(Integer, default=0)
    total_faces = Column(Integer, default=0)
    total_edges = Column(Integer, default=0)
    total_vertices = Column(Integer, default=0)
    total_surfaces = Column(Integer, default=0)
    min_x = Column(Double)
    min_y = Column(Double)
    min_z = Column(Double)
    max_x = Column(Double)
    max_y = Column(Double)
    max_z = Column(Double)
    dimensions_x = Column(Double)
    dimensions_y = Column(Double)
    dimensions_z = Column(Double)
    total_volume = Column(Double)
    total_surface_area = Column(Double)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    model = relationship("Model", back_populates="statistics")


class AssemblyTree(Base):
    """Assembly tree structure table"""
    __tablename__ = "assembly_trees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, unique=True)
    root_node = Column(JSONB, nullable=False)
    total_nodes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    model = relationship("Model", back_populates="assembly_tree")


class DependencyGraph(Base):
    """Dependency graph table"""
    __tablename__ = "dependency_graphs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    model = relationship("Model", back_populates="dependency_graph")
    nodes = relationship("GraphNode", back_populates="graph", cascade="all, delete-orphan", lazy="selectin")
    edges = relationship("GraphEdge", back_populates="graph_rel", cascade="all, delete-orphan", lazy="selectin")


class GraphNode(Base):
    """Graph nodes table"""
    __tablename__ = "graph_nodes"

    id = Column(String(50), primary_key=True)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("dependency_graphs.id", ondelete="CASCADE"), primary_key=True)
    label = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    properties = Column(JSONB)
    references = Column("references", ARRAY(String), default=[])
    referenced_by = Column(ARRAY(String), default=[])

    # Relationship
    graph = relationship("DependencyGraph", back_populates="nodes")


class GraphEdge(Base):
    """Graph edges table"""
    __tablename__ = "graph_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    graph_id = Column(UUID(as_uuid=True), ForeignKey("dependency_graphs.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(50), nullable=False)
    target = Column(String(50), nullable=False)
    rel_type = Column("relationship", String(100), nullable=False)  # Python attr: rel_type, DB column: relationship
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    graph_rel = relationship("DependencyGraph", back_populates="edges", foreign_keys=[graph_id], lazy="selectin")


class Entity(Base):
    """STEP entities table"""
    __tablename__ = "entities"

    id = Column(String(50), primary_key=True)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), primary_key=True)
    entity_type = Column(String(100), nullable=False)
    attributes = Column(JSONB)
    references = Column("references", ARRAY(String), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    model = relationship("Model", back_populates="entities")


class ModelMesh(Base):
    """Model mesh table - stores triangulated mesh data for 3D visualization"""
    __tablename__ = "model_meshes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    face_id = Column(String(100), nullable=False)
    surface_type = Column(String(100), nullable=False)
    solid_index = Column(Integer)
    shell_index = Column(Integer)
    face_index = Column(Integer)
    vertices = Column(JSONB, nullable=False)  # Array of vertex coordinates
    normals = Column(JSONB)  # Array of normal vectors
    indices = Column(JSONB)  # Triangle indices
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    model = relationship("Model", back_populates="meshes")


# Add meshes relationship to Model class
Model.meshes = relationship("ModelMesh", back_populates="model", cascade="all, delete-orphan")
            