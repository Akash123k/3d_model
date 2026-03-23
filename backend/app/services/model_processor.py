"""
Model processor service
Orchestrates STEP file processing pipeline
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import redis

from app.core.logging import processing_log, log
from app.services.step_parser_optimized import OptimizedSTEPParser as STEPParser
from app.services.dependency_graph import DependencyGraphBuilder
from app.services.mesh_generator import MeshGenerator
from app.models.schemas import ModelStatistics, BoundingBox, Vertex
from app.db.models import Model
from app.db.repositories import (
    ModelRepository,
    StatisticsRepository,
    AssemblyTreeRepository,
    DependencyGraphRepository,
    EntityRepository
)
from sqlalchemy.orm import Session


class ModelProcessor:
    """Orchestrates model processing pipeline"""
    
    def __init__(self, model_id: str, file_path: str, redis_url: str = None, db: Session = None, max_workers: int = 16):
        self.model_id = model_id
        self.file_path = Path(file_path)
        self.db = db
        self.redis_client = None
        self.max_workers = max_workers  # Default 16 for high-performance parallel processing
        
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                processing_log.info("redis_connection_established")
            except Exception as e:
                processing_log.warning("redis_connection_failed", error=str(e))
        
        self.processed_data: Optional[Dict[str, Any]] = None
        
        processing_log.info("model_processor_initialized",
                          model_id=model_id,
                          max_workers=max_workers,
                          parallel_optimization="enabled")
        
    def process(self) -> Dict[str, Any]:
        """
        Process STEP file through complete pipeline
        Returns processed model data
        """
        processing_log.info("model_processing_started",
                          model_id=self.model_id,
                          file_path=str(self.file_path))
        
        try:
            # Step 1: Parse STEP file with multi-threading
            parser = STEPParser(str(self.file_path), max_workers=self.max_workers)
            parsed_data = parser.parse()
            
            # Step 2: Build dependency graph (with multithreading)
            graph_builder = DependencyGraphBuilder(parsed_data["entities"], max_workers=self.max_workers)
            graph_data = graph_builder.build()
            
            processing_log.info("dependency_graph_built",
                              model_id=self.model_id,
                              total_nodes=graph_data["total_nodes"],
                              total_edges=graph_data["total_edges"],
                              parallel_processing=True)
            
            # Step 3: Generate meshes for 3D visualization (with multithreading)
            mesh_generator = MeshGenerator(max_workers=self.max_workers)
            mesh_data = mesh_generator.generate_meshes(parsed_data.get("brep_hierarchy", {}))
            
            # Step 4: Calculate statistics
            statistics = self._calculate_statistics(parsed_data)
            
            # Step 4: Save to database
            if self.db:
                self._save_to_database(parsed_data, graph_data, statistics, mesh_data)
            
            # Step 5: Cache in Redis (for fast access)
            self._assemble_processed_data(parsed_data, graph_data, statistics, mesh_data)
            self._cache_model_data()
            
            processing_log.info("model_processing_completed",
                              model_id=self.model_id,
                              entities_count=len(parsed_data["entities"]),
                              graph_nodes=graph_data["total_nodes"])
            
            return self.processed_data
            
        except Exception as e:
            processing_log.error("model_processing_failed",
                               model_id=self.model_id,
                               error=str(e))
            raise
    
    def _assemble_processed_data(self, parsed_data: Dict[str, Any], 
                                 graph_data: Dict[str, Any],
                                 statistics: ModelStatistics,
                                 mesh_data: List[Dict[str, Any]]):
        """Assemble processed data for caching with B-Rep hierarchy and meshes"""
        # Use B-Rep hierarchy as root node if available
        root_node = None
        total_nodes = 0
        
        if parsed_data.get("brep_hierarchy") and parsed_data["brep_hierarchy"].get("solids"):
            # Convert B-Rep hierarchy to tree structure
            root_node = {
                "id": f"brep_root_{self.model_id}",
                "name": parsed_data["filename"],
                "type": "BREP_MODEL",
                "children": [],
                "properties": {
                    "total_solids": parsed_data["brep_hierarchy"].get("total_solids", 0),
                    "total_faces": parsed_data["brep_hierarchy"].get("total_faces", 0)
                }
            }
            
            # Add solids
            for solid in parsed_data["brep_hierarchy"]["solids"]:
                solid_node = {
                    "id": solid["id"],
                    "name": f"Solid {solid['id']}",
                    "type": "SOLID",
                    "children": []
                }
                
                # Add shells
                for shell in solid.get("shells", []):
                    shell_node = {
                        "id": shell["id"],
                        "name": f"Shell {shell['id']}",
                        "type": "SHELL",
                        "children": []
                    }
                    
                    # Add faces (NO LIMIT for complete data)
                    for face in shell.get("faces", []):
                        face_node = {
                            "id": face["id"],
                            "name": f"{face.get('surface_type', 'Face')} {face['id']}",
                            "type": "FACE",
                            "children": [],
                            "properties": {
                                "surface_type": face.get("surface_type"),
                                "surface_description": face.get("surface_description")
                            }
                        }
                        
                        # Add edges grouped by type (NO LIMIT)
                        edge_types = {}
                        for edge in face.get("edges", []):
                            edge_type = edge.get("curve_type", "EDGE")
                            if edge_type not in edge_types:
                                edge_types[edge_type] = []
                            edge_types[edge_type].append(edge)
                        
                        for etype, edges in edge_types.items():
                            edge_group = {
                                "id": f"{face['id']}_{etype}",
                                "name": f"{etype.replace('_', ' ').title()} ({len(edges)})",
                                "type": "EDGE_GROUP",
                                "children": []
                            }
                            
                            # Add all edges (NO LIMIT)
                            for edge in edges:
                                edge_node = {
                                    "id": edge["id"],
                                    "name": f"Edge {edge['id']}",
                                    "type": "EDGE",
                                    "children": [],
                                    "properties": {
                                        "curve_type": edge.get("curve_type"),
                                        "geometry": edge.get("geometry")
                                    }
                                }
                                
                                # Add all vertices (NO LIMIT)
                                for vertex in edge.get("vertices", []):
                                    vertex_node = {
                                        "id": f"{edge['id']}_v",
                                        "name": "Vertex",
                                        "type": "VERTEX",
                                        "properties": {
                                            "coordinates": vertex.get("coordinates")
                                        }
                                    }
                                    edge_node["children"].append(vertex_node)
                                
                                edge_group["children"].append(edge_node)
                            
                            face_node["children"].append(edge_group)
                        
                        shell_node["children"].append(face_node)
                    
                    solid_node["children"].append(shell_node)
                
                root_node["children"].append(solid_node)
                total_nodes += 1
        
        # Fallback to old structure if no B-Rep hierarchy
        if not root_node and parsed_data.get("structure"):
            root_node = parsed_data["structure"][0]
            total_nodes = len(parsed_data["structure"])
        
        self.processed_data = {
            "model_id": self.model_id,
            "filename": parsed_data["filename"],
            "file_size": parsed_data["file_size"],
            "upload_time": datetime.now().isoformat(),
            "status": "completed",
            "assembly_tree": {
                "model_id": self.model_id,
                "root_node": root_node,
                "total_nodes": total_nodes if total_nodes > 0 else len(parsed_data.get("structure", [1]))
            },
            "dependency_graph": {
                "model_id": self.model_id,
                "nodes": graph_data["nodes"],
                "edges": graph_data["edges"],
                "total_nodes": graph_data["total_nodes"],
                "total_edges": graph_data["total_edges"]
            },
            "brep_hierarchy": parsed_data.get("brep_hierarchy"),
            "meshes": mesh_data,
            "statistics": statistics.dict(),
            "entities_count": len(parsed_data["entities"]),
            "cache_key": f"model:{self.model_id}"
        }
    
    def _save_to_database(self, parsed_data: Dict[str, Any], 
                         graph_data: Dict[str, Any],
                         statistics: ModelStatistics,
                         mesh_data: List[Dict[str, Any]]):
        """Save all processed data to database including meshes"""
        try:
            processing_log.info("saving_to_database", model_id=self.model_id)
            
            # 1. Update or create model record FIRST
            model_data = {
                "filename": parsed_data["filename"],
                "file_path": str(self.file_path),
                "file_size": parsed_data["file_size"],
                "status": "completed",
                "entities_count": len(parsed_data["entities"]),
                "cache_key": f"model:{self.model_id}"
            }
            
            # Check if model exists
            existing_model = ModelRepository.get_by_id(self.db, self.model_id)
            if not existing_model:
                # Create new model record with the SAME model_id
                model_data["cache_key"] = f"model:{self.model_id}"
                model = Model(
                    id=self.model_id,  # Use the same ID from upload
                    filename=model_data["filename"],
                    original_filename=model_data.get("original_filename", model_data["filename"]),
                    file_path=model_data["file_path"],
                    file_size=model_data["file_size"],
                    status=model_data.get("status", "processing"),
                    entities_count=model_data.get("entities_count", 0),
                    cache_key=model_data.get("cache_key")
                )
                self.db.add(model)
                self.db.commit()
                self.db.refresh(model)
                processing_log.info("model_record_created_with_same_id", 
                                  model_id=str(model.id))
            else:
                model = ModelRepository.update_status(self.db, self.model_id, "completed")
                self.db.commit()
                self.db.refresh(model)
            
            # 2. Save statistics (after model is committed)
            # Flatten bounding box for database storage
            stats_dict = {
                "total_solids": statistics.total_solids,
                "total_faces": statistics.total_faces,
                "total_edges": statistics.total_edges,
                "total_vertices": statistics.total_vertices,
                "total_surfaces": statistics.total_surfaces,
                "total_volume": statistics.total_volume,
                "total_surface_area": statistics.total_surface_area,
            }
            
            # Add bounding box fields if available
            if statistics.bounding_box:
                stats_dict["min_x"] = statistics.bounding_box.min_point.x
                stats_dict["min_y"] = statistics.bounding_box.min_point.y
                stats_dict["min_z"] = statistics.bounding_box.min_point.z
                stats_dict["max_x"] = statistics.bounding_box.max_point.x
                stats_dict["max_y"] = statistics.bounding_box.max_point.y
                stats_dict["max_z"] = statistics.bounding_box.max_point.z
                stats_dict["dimensions_x"] = statistics.bounding_box.dimensions.x
                stats_dict["dimensions_y"] = statistics.bounding_box.dimensions.y
                stats_dict["dimensions_z"] = statistics.bounding_box.dimensions.z
            
            StatisticsRepository.create(self.db, self.model_id, stats_dict)
            processing_log.info("statistics_saved", model_id=self.model_id)
            
            # 3. Save assembly tree
            if parsed_data["structure"]:
                root_node = parsed_data["structure"][0]
                AssemblyTreeRepository.create(
                    self.db, 
                    self.model_id,
                    root_node,
                    len(parsed_data["structure"])
                )
                processing_log.info("assembly_tree_saved", model_id=self.model_id)
            
            # 4. Save dependency graph
            graph = DependencyGraphRepository.create(self.db, self.model_id)
            DependencyGraphRepository.add_nodes(self.db, str(graph.id), graph_data["nodes"])
            DependencyGraphRepository.add_edges(self.db, str(graph.id), graph_data["edges"])
            processing_log.info("dependency_graph_saved", model_id=self.model_id)
            
            # 5. Save entities with batch processing (NO ARTIFICIAL LIMIT)
            # Process all entities in batches of 10,000 for memory efficiency
            from app.db.repositories import EntityRepository
            all_entities = parsed_data["entities"]
            batch_size = 10000
            
            entity_items = list(all_entities.items())
            total_entities = len(entity_items)
            
            for i in range(0, total_entities, batch_size):
                batch = dict(entity_items[i:i + batch_size])
                EntityRepository.bulk_create(self.db, self.model_id, batch)
                processing_log.info("entities_batch_saved", 
                                  model_id=self.model_id, 
                                  batch_start=i,
                                  batch_end=min(i + batch_size, total_entities),
                                  total=total_entities)
            
            processing_log.info("all_entities_saved", 
                              model_id=self.model_id, 
                              count=total_entities)
            
            # 6. Save mesh data (NEW - Critical for 3D visualization)
            # Optimized with batch inserts (50 meshes per batch)
            if mesh_data and len(mesh_data) > 0:
                from app.db.repositories import MeshRepository
                MeshRepository.bulk_create(self.db, self.model_id, mesh_data)
                processing_log.info("meshes_saved", 
                                  model_id=self.model_id, 
                                  mesh_count=len(mesh_data),
                                  batch_processing=True)
            
            # Final commit for all related data (single commit at end)
            self.db.commit()
            
            processing_log.info("database_save_completed", model_id=self.model_id)
            
        except Exception as e:
            processing_log.error("database_save_failed",
                               model_id=self.model_id,
                               error=str(e))
            # Don't raise - allow processing to continue even if DB save fails
    
    def _extract_coordinates_from_attributes(self, attrs: Dict[str, Any]) -> List[float]:
        """Extract XYZ coordinates from entity attributes"""
        import re
        coords = []
        
        # Try to extract coordinates from attributes
        for key, value in sorted(attrs.items()):
            if isinstance(value, dict):
                value_type = value.get("type")
                
                # Handle nested structure (most common for CARTESIAN_POINT)
                # e.g., CARTESIAN_POINT('',(0.,0.,0.)) becomes nested type with values array
                if value_type == "nested" and "values" in value:
                    nested_values = value["values"]
                    if isinstance(nested_values, list):
                        for nv in nested_values:
                            if isinstance(nv, dict):
                                if nv.get("type") == "float":
                                    coord = nv.get("value")
                                    if coord is not None and -1e6 < coord < 1e6:
                                        coords.append(coord)
                                elif nv.get("type") == "integer":
                                    coord = float(nv.get("value"))
                                    if -1e6 < coord < 1e6:
                                        coords.append(coord)
                
                # Handle direct float values
                elif value_type == "float":
                    coord = value.get("value")
                    if coord is not None and -1e6 < coord < 1e6:
                        coords.append(coord)
                
                # Handle integer values
                elif value_type == "integer":
                    coord = float(value.get("value"))
                    if -1e6 < coord < 1e6:
                        coords.append(coord)
                        
            elif isinstance(value, str) and ('(' in value or ')' in value):
                # Handle raw coordinate string: '( 15.44, 15.67, 2.80'
                # Extract numbers from string like '( 15.44142079503200193, 15.67043470458795085, 2.799999999999999822'
                numbers = re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', value)
                for num_str in numbers:
                    try:
                        num = float(num_str)
                        if -1e6 < num < 1e6:
                            coords.append(num)
                    except ValueError:
                        pass
            elif isinstance(value, (int, float)):
                if -1e6 < value < 1e6:
                    coords.append(float(value))
        
        return coords
    
    def _calculate_statistics(self, parsed_data: Dict[str, Any]) -> ModelStatistics:
        """Calculate model statistics from parsed data"""
        entities = parsed_data["entities"]
        
        processing_log.info("statistics_calculation_started",
                          total_entities=len(entities))
        
        # Count entity types directly from entities
        type_counts: Dict[str, int] = {}
        for entity in entities.values():
            entity_type = entity["type"]
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        # Log top entity types
        top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        processing_log.info("top_entity_types", types=top_types)
        
        # Count actual B-Rep entities
        total_solids = sum(1 for e in entities.values() 
                          if e["type"] == "MANIFOLD_SOLID_BREP")
        total_faces = sum(1 for e in entities.values() 
                         if e["type"] == "ADVANCED_FACE")
        total_edges = sum(1 for e in entities.values() 
                         if e["type"] in ["EDGE_CURVE", "EDGE"])
        total_vertices = sum(1 for e in entities.values() 
                            if e["type"] == "VERTEX_POINT")
        total_surfaces = sum(
            count for etype, count in type_counts.items() 
            if "SURFACE" in etype or "PLANE" in etype or "CYLINDER" in etype
        )
        
        # Use B-Rep hierarchy counts if available (more accurate)
        if parsed_data.get("brep_hierarchy"):
            brep = parsed_data["brep_hierarchy"]
            total_solids = brep.get("total_solids", total_solids)
            total_faces = brep.get("total_faces", total_faces)
            
            processing_log.info("using_brep_counts",
                              solids=total_solids,
                              faces=total_faces)
        
        # Calculate bounding box from Cartesian points with improved extraction
        min_coords = [float('inf'), float('inf'), float('inf')]
        max_coords = [float('-inf'), float('-inf'), float('-inf')]
        
        for entity_id, entity in entities.items():
            if entity["type"] == "CARTESIAN_POINT":
                attrs = entity.get("attributes", {})
                coords = self._extract_coordinates_from_attributes(attrs)
                
                # If we have 3 coordinates, use them as a point
                if len(coords) >= 3:
                    for i in range(3):
                        if coords[i] < min_coords[i]:
                            min_coords[i] = coords[i]
                        if coords[i] > max_coords[i]:
                            max_coords[i] = coords[i]
            
            # Also check VERTEX_POINT entities
            elif entity["type"] == "VERTEX_POINT":
                attrs = entity.get("attributes", {})
                coords = self._extract_coordinates_from_attributes(attrs)
                
                if len(coords) >= 3:
                    for i in range(3):
                        if coords[i] < min_coords[i]:
                            min_coords[i] = coords[i]
                        if coords[i] > max_coords[i]:
                            max_coords[i] = coords[i]
        
        # Check if we found valid coordinates
        has_valid_bbox = all(c != float('inf') and c != float('-inf') for c in min_coords + max_coords)
        
        if has_valid_bbox:
            dimensions = [max_coords[i] - min_coords[i] for i in range(3)]
            
            # Ensure minimum dimensions
            for i in range(3):
                if dimensions[i] < 1.0:
                    dimensions[i] = 1.0
            
            bounding_box = BoundingBox(
                min_point=Vertex(x=min_coords[0], y=min_coords[1], z=min_coords[2]),
                max_point=Vertex(x=max_coords[0], y=max_coords[1], z=max_coords[2]),
                dimensions=Vertex(x=dimensions[0], y=dimensions[1], z=dimensions[2])
            )
            
            processing_log.info("bounding_box_calculated",
                              dimensions=dimensions,
                              min=min_coords,
                              max=max_coords)
        else:
            # Fallback to default bounding box
            processing_log.warning("bounding_box_fallback_used",
                                 reason="no_valid_coordinates_found")
            
            bounding_box = BoundingBox(
                min_point=Vertex(x=0.0, y=0.0, z=0.0),
                max_point=Vertex(x=100.0, y=100.0, z=100.0),
                dimensions=Vertex(x=100.0, y=100.0, z=100.0)
            )
        
        return ModelStatistics(
            total_solids=total_solids,
            total_faces=total_faces,
            total_edges=total_edges,
            total_vertices=total_vertices,
            total_surfaces=total_surfaces,
            bounding_box=bounding_box,
            total_volume=None,  # Would require pythonOCC
            total_surface_area=None  # Would require pythonOCC
        )
    
    def _cache_model_data(self):
        """Cache processed model data in Redis"""
        if not self.redis_client:
            return
        
        try:
            cache_key = f"model:{self.model_id}"
            self.redis_client.setex(
                cache_key,
                3600 * 24,  # 24 hours TTL
                json.dumps(self.processed_data, default=str)
            )
            processing_log.info("model_data_cached",
                              model_id=self.model_id,
                              cache_key=cache_key)
        except Exception as e:
            processing_log.warning("redis_cache_write_failed",
                                 model_id=self.model_id,
                                 error=str(e))
    
    @classmethod
    def get_cached(cls, model_id: str, redis_url: str) -> Optional[Dict[str, Any]]:
        """Get processed model data from cache"""
        try:
            redis_client = redis.from_url(redis_url)
            cache_key = f"model:{model_id}"
            cached_data = redis_client.get(cache_key)
            
            if cached_data:
                processing_log.info("model_data_cache_hit",
                                  model_id=model_id)
                return json.loads(cached_data)
            else:
                processing_log.info("model_data_cache_miss",
                                  model_id=model_id)
                return None
                
        except Exception as e:
            processing_log.warning("redis_cache_read_failed",
                                 model_id=model_id,
                                 error=str(e))
            return None
