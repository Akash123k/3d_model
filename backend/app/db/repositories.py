"""
Repository classes for database operations
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import (
    Model,
    ModelStatistics,
    AssemblyTree,
    DependencyGraph,
    GraphNode,
    GraphEdge,
    Entity,
    ModelMesh
)


class ModelRepository:
    """Repository for model operations"""
    
    @staticmethod
    def create(db: Session, model_data: Dict[str, Any]) -> Model:
        """Create a new model record"""
        model = Model(
            id=model_data.get("id"),
            filename=model_data["filename"],
            original_filename=model_data.get("original_filename", model_data["filename"]),
            file_path=model_data["file_path"],
            file_size=model_data["file_size"],
            status=model_data.get("status", "processing"),
            entities_count=model_data.get("entities_count", 0),
            cache_key=model_data.get("cache_key")
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model
    
    @staticmethod
    def get_by_id(db: Session, model_id: str) -> Optional[Model]:
        """Get model by ID"""
        from uuid import UUID
        try:
            uuid_model_id = UUID(model_id)
            return db.query(Model).filter(Model.id == uuid_model_id).first()
        except ValueError:
            return None
    
    @staticmethod
    def update_status(db: Session, model_id: str, status: str) -> Optional[Model]:
        """Update model status"""
        model = ModelRepository.get_by_id(db, model_id)
        if model:
            model.status = status
            db.commit()
            db.refresh(model)
        return model
    
    @staticmethod
    def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[Model]:
        """Get all models with pagination"""
        return db.query(Model).order_by(Model.created_at.desc()).limit(limit).offset(offset).all()


class StatisticsRepository:
    """Repository for model statistics operations"""
    
    @staticmethod
    def create(db: Session, model_id: str, stats_data: Dict[str, Any]) -> ModelStatistics:
        """Create statistics record"""
        stats = ModelStatistics(
            model_id=model_id,
            total_solids=stats_data.get("total_solids", 0),
            total_faces=stats_data.get("total_faces", 0),
            total_edges=stats_data.get("total_edges", 0),
            total_vertices=stats_data.get("total_vertices", 0),
            total_surfaces=stats_data.get("total_surfaces", 0),
            min_x=stats_data.get("min_x"),
            min_y=stats_data.get("min_y"),
            min_z=stats_data.get("min_z"),
            max_x=stats_data.get("max_x"),
            max_y=stats_data.get("max_y"),
            max_z=stats_data.get("max_z"),
            dimensions_x=stats_data.get("dimensions_x"),
            dimensions_y=stats_data.get("dimensions_y"),
            dimensions_z=stats_data.get("dimensions_z"),
            total_volume=stats_data.get("total_volume"),
            total_surface_area=stats_data.get("total_surface_area")
        )
        db.add(stats)
        return stats
    
    @staticmethod
    def get_by_model_id(db: Session, model_id: str) -> Optional[ModelStatistics]:
        """Get statistics by model ID"""
        return db.query(ModelStatistics).filter(
            ModelStatistics.model_id == model_id
        ).first()
    
    @staticmethod
    def to_dict(stats: ModelStatistics) -> Dict[str, Any]:
        """Convert statistics to dictionary"""
        return {
            "total_solids": stats.total_solids,
            "total_faces": stats.total_faces,
            "total_edges": stats.total_edges,
            "total_vertices": stats.total_vertices,
            "total_surfaces": stats.total_surfaces,
            "bounding_box": {
                "min_point": {
                    "x": stats.min_x or 0,
                    "y": stats.min_y or 0,
                    "z": stats.min_z or 0
                },
                "max_point": {
                    "x": stats.max_x or 0,
                    "y": stats.max_y or 0,
                    "z": stats.max_z or 0
                },
                "dimensions": {
                    "x": stats.dimensions_x or 0,
                    "y": stats.dimensions_y or 0,
                    "z": stats.dimensions_z or 0
                },
                "center": {
                    "x": ((stats.min_x or 0) + (stats.max_x or 0)) / 2,
                    "y": ((stats.min_y or 0) + (stats.max_y or 0)) / 2,
                    "z": ((stats.min_z or 0) + (stats.max_z or 0)) / 2
                }
            },
            "total_volume": stats.total_volume,
            "total_surface_area": stats.total_surface_area
        }


class AssemblyTreeRepository:
    """Repository for assembly tree operations"""
    
    @staticmethod
    def create(db: Session, model_id: str, root_node: Dict[str, Any], total_nodes: int) -> AssemblyTree:
        """Create assembly tree record"""
        tree = AssemblyTree(
            model_id=model_id,
            root_node=root_node,
            total_nodes=total_nodes
        )
        db.add(tree)
        return tree
    
    @staticmethod
    def get_by_model_id(db: Session, model_id: str) -> Optional[AssemblyTree]:
        """Get assembly tree by model ID"""
        return db.query(AssemblyTree).filter(
            AssemblyTree.model_id == model_id
        ).first()


class DependencyGraphRepository:
    """Repository for dependency graph operations"""
    
    @staticmethod
    def create(db: Session, model_id: str) -> DependencyGraph:
        """Create dependency graph record"""
        graph = DependencyGraph(model_id=model_id)
        db.add(graph)
        db.commit()
        db.refresh(graph)
        return graph
    
    @staticmethod
    def get_by_model_id(db: Session, model_id: str) -> Optional[DependencyGraph]:
        """Get dependency graph by model ID"""
        from sqlalchemy.orm import selectinload
        return db.query(DependencyGraph).options(
            selectinload(DependencyGraph.nodes),
            selectinload(DependencyGraph.edges)
        ).filter(
            DependencyGraph.model_id == model_id
        ).first()
    
    @staticmethod
    def add_nodes(db: Session, graph_id: str, nodes: List[Dict[str, Any]]) -> List[GraphNode]:
        """Add nodes to graph"""
        created_nodes = []
        import uuid
        uuid_graph_id = uuid.UUID(graph_id) if isinstance(graph_id, str) else graph_id
        for node_data in nodes:
            node = GraphNode(
                id=str(node_data["id"]),
                graph_id=uuid_graph_id,
                label=str(node_data["label"]),
                type=str(node_data["type"]),
                properties=node_data.get("properties"),
                references=[str(r) for r in node_data.get("references", [])],
                referenced_by=[str(r) for r in node_data.get("referenced_by", [])]
            )
            db.add(node)
            created_nodes.append(node)
        return created_nodes
    
    @staticmethod
    def add_edges(db: Session, graph_id: str, edges: List[Dict[str, Any]]) -> List[GraphEdge]:
        """Add edges to graph"""
        created_edges = []
        import uuid
        uuid_graph_id = uuid.UUID(graph_id) if isinstance(graph_id, str) else graph_id
        for edge_data in edges:
            edge = GraphEdge(
                graph_id=uuid_graph_id,
                source=str(edge_data["source"]),
                target=str(edge_data["target"]),
                rel_type=str(edge_data["relationship"])
            )
            db.add(edge)
            created_edges.append(edge)
        return created_edges
    
    @staticmethod
    def to_dict(graph: DependencyGraph) -> Dict[str, Any]:
        """Convert graph to dictionary"""
        return {
            "model_id": str(graph.model_id),
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "type": node.type,
                    "properties": node.properties,
                    "references": node.references,
                    "referenced_by": node.referenced_by
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "relationship": edge.rel_type
                }
                for edge in graph.edges
            ],
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges)
        }


class EntityRepository:
    """Repository for entity operations"""
    
    @staticmethod
    def bulk_create(db: Session, model_id: str, entities: Dict[str, Dict[str, Any]]) -> List[Entity]:
        """Bulk create entities from dictionary"""
        created_entities = []
        import uuid
        uuid_model_id = uuid.UUID(model_id) if isinstance(model_id, str) else model_id
        for entity_id, entity_data in entities.items():
            entity = Entity(
                id=str(entity_id),
                model_id=uuid_model_id,
                entity_type=str(entity_data.get("type", "UNKNOWN")),
                attributes=entity_data.get("attributes", {}),
                references=[str(r) for r in entity_data.get("references", [])]
            )
            db.add(entity)
            created_entities.append(entity)
        return created_entities
    
    @staticmethod
    def get_by_model_id(db: Session, model_id: str, limit: int = 1000) -> List[Entity]:
        """Get entities by model ID with limit"""
        return db.query(Entity).filter(
            Entity.model_id == model_id
        ).limit(limit).all()


class MeshRepository:
    """Repository for model mesh operations"""
    
    @staticmethod
    def create(db: Session, model_id: str, mesh_data: Dict[str, Any]) -> ModelMesh:
        """Create a new mesh record"""
        mesh = ModelMesh(
            model_id=model_id,
            face_id=mesh_data.get("face_id", "unknown"),
            surface_type=mesh_data.get("surface_type", "UNKNOWN"),
            solid_index=mesh_data.get("solid_index"),
            shell_index=mesh_data.get("shell_index"),
            face_index=mesh_data.get("face_index"),
            vertices=mesh_data.get("vertices", []),
            normals=mesh_data.get("normals"),
            indices=mesh_data.get("indices")
        )
        
        db.add(mesh)
        return mesh
    
    @staticmethod
    def bulk_create(db: Session, model_id: str, meshes: List[Dict[str, Any]]) -> List[ModelMesh]:
        """Bulk create multiple mesh records using batch insert with single commit"""
        if not meshes:
            return []
        
        created_meshes = []
        batch_size = 100  # Process in batches of 100 for better performance
        
        for i in range(0, len(meshes), batch_size):
            batch = meshes[i:i + batch_size]
            
            for mesh_data in batch:
                mesh = ModelMesh(
                    model_id=model_id,
                    face_id=mesh_data.get("face_id", "unknown"),
                    surface_type=mesh_data.get("surface_type", "UNKNOWN"),
                    solid_index=mesh_data.get("solid_index"),
                    shell_index=mesh_data.get("shell_index"),
                    face_index=mesh_data.get("face_index"),
                    vertices=mesh_data.get("vertices", []),
                    normals=mesh_data.get("normals"),
                    indices=mesh_data.get("indices")
                )
                db.add(mesh)
                created_meshes.append(mesh)
            
            # Flush batch to database (don't commit yet)
            db.flush()
        
        # Single commit happens in _save_to_database method
        return created_meshes
    
    @staticmethod
    def get_by_model_id(db: Session, model_id: str) -> List[ModelMesh]:
        """Get all meshes for a model"""
        return db.query(ModelMesh).filter(
            ModelMesh.model_id == model_id
        ).all()
    
    @staticmethod
    def delete_by_model_id(db: Session, model_id: str) -> None:
        """Delete all meshes for a model"""
        db.query(ModelMesh).filter(
            ModelMesh.model_id == model_id
        ).delete()
        db.commit()
    
    @staticmethod
    def to_dict(mesh: ModelMesh) -> Dict[str, Any]:
        """Convert mesh object to dictionary"""
        return {
            "face_id": mesh.face_id,
            "surface_type": mesh.surface_type,
            "solid_index": mesh.solid_index,
            "shell_index": mesh.shell_index,
            "face_index": mesh.face_index,
            "vertices": mesh.vertices,
            "normals": mesh.normals,
            "indices": mesh.indices
        }
