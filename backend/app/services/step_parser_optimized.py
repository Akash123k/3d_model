"""
Optimized STEP parser with multi-threading support
Significantly faster parsing for large files
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app.core.logging import processing_log, log
from app.models.schemas import AssemblyNode


class OptimizedSTEPParser:
    """High-performance STEP parser with parallel processing"""
    
    def __init__(self, file_path: str, max_workers: int = 4):
        self.file_path = Path(file_path)
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.structure: List[Dict[str, Any]] = []
        self.raw_lines: List[str] = []
        self.brep_hierarchy: Dict[str, Any] = {}
        self.max_workers = max_workers
        self.lock = threading.Lock()
        
    def parse(self) -> Dict[str, Any]:
        """
        Parse the STEP file using multi-threading for better performance
        Returns parsed data structure
        """
        processing_log.info("optimized_step_parse_started", 
                        file_path=str(self.file_path),
                        max_workers=self.max_workers,
                        timestamp=datetime.now().isoformat())
        
        try:
            # Read file content
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.raw_lines = content.split('\n')
            
            # OPTIMIZATION 1: Parallel entity parsing
            processing_log.info("parallel_entity_parsing_started")
            self._parse_entities_parallel(content)
            processing_log.info("parallel_entity_parsing_completed",
                              total_entities=len(self.entities))
            
            # OPTIMIZATION 2: Fast B-Rep hierarchy building
            processing_log.info("brep_hierarchy_building_started")
            self._build_brep_hierarchy_optimized()
            
            # Log B-Rep statistics
            if self.brep_hierarchy:
                processing_log.info("brep_hierarchy_summary",
                                  solids=self.brep_hierarchy.get("total_solids", 0),
                                  faces=self.brep_hierarchy.get("total_faces", 0),
                                  edges=self.brep_hierarchy.get("total_edges", 0),
                                  vertices=self.brep_hierarchy.get("total_vertices", 0))
            
            # Extract assembly structure
            self._extract_assembly_structure()
            
            # Final summary logging
            total_refs = sum(len(e.get("references", [])) for e in self.entities.values())
            processing_log.info("optimized_step_parse_completed",
                            total_entities=len(self.entities),
                            total_references=total_refs,
                            avg_refs_per_entity=round(total_refs / max(len(self.entities), 1), 2),
                            structure_nodes=len(self.structure),
                            brep_solids=len(self.brep_hierarchy.get('solids', [])))
            
            return {
                "entities": self.entities,
                "structure": self.structure,
                "brep_hierarchy": self.brep_hierarchy,
                "file_size": self.file_path.stat().st_size,
                "filename": self.file_path.name
            }
            
        except Exception as e:
            processing_log.error("optimized_step_parse_failed",
                            error=str(e),
                            file_path=str(self.file_path))
            raise
    
    def _parse_entities_parallel(self, content: str):
        """Parse STEP entities in parallel using thread pool"""
        # Pattern to match STEP entities
        content_clean = re.sub(r'[\r\n]+', ' ', content)
        content_clean = re.sub(r'\s+', ' ', content_clean)
        
        entity_pattern = re.compile(r'#(\d+)\s*=\s*([A-Z_0-9]+)\s*\((.*?)\)\s*;')
        
        # Find all matches first
        all_matches = list(entity_pattern.finditer(content_clean))
        processing_log.info("total_entity_matches_found", count=len(all_matches))
        
        # Split matches into chunks for parallel processing
        chunk_size = max(len(all_matches) // (self.max_workers * 2), 100)
        chunks = [all_matches[i:i + chunk_size] for i in range(0, len(all_matches), chunk_size)]
        
        processing_log.info("processing_chunks_created", 
                          chunks=len(chunks), 
                          chunk_size=chunk_size)
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._process_entity_chunk, chunk) for chunk in chunks]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    with self.lock:
                        self.entities.update(result)
                    completed += 1
                    if completed % 5 == 0:
                        processing_log.info("entity_parsing_progress",
                                          completed=completed,
                                          total=len(futures),
                                          percentage=round((completed / len(futures)) * 100, 2))
                except Exception as e:
                    processing_log.error("entity_chunk_processing_failed", error=str(e))
        
        processing_log.info("parallel_entity_parsing_completed",
                          total_parsed=len(self.entities))
    
    def _process_entity_chunk(self, matches: List) -> Dict[str, Dict[str, Any]]:
        """Process a chunk of entity matches"""
        chunk_entities = {}
        
        for match in matches:
            entity_id = f"#{match.group(1)}"
            entity_type = match.group(2)
            attributes_str = match.group(3)
            
            # Parse attributes with improved nested structure handling
            attributes = self._parse_advanced_attributes(attributes_str)
            
            # Extract ALL references including nested and raw strings
            references = self._extract_all_references(attributes)
            
            chunk_entities[entity_id] = {
                "id": entity_id,
                "type": entity_type,
                "attributes": attributes,
                "references": references,
                "raw_data": attributes_str.strip()
            }
        
        return chunk_entities
    
    def _parse_advanced_attributes(self, attributes_str: str) -> Dict[str, Any]:
        """Parse attributes with support for nested structures and enums"""
        attributes = {}
        
        # Handle empty attributes
        if not attributes_str or attributes_str.strip() == '.':
            return attributes
        
        # Split by comma but respect parentheses and quotes
        parts = self._smart_split(attributes_str)
        
        # Parse each part
        for idx, part in enumerate(parts):
            part = part.strip()
            if not part or part == '*':
                continue
            
            # Try to parse value
            value = self._parse_single_value(part)
            if value is not None:
                attributes[f"attr_{idx}"] = value
        
        return attributes
    
    def _smart_split(self, s: str) -> List[str]:
        """Split string by commas respecting parentheses and quotes"""
        result = []
        current = ""
        paren_depth = 0
        in_quotes = False
        
        for char in s:
            if char == "'" and (not current or current[-1] != '\\'):
                in_quotes = not in_quotes
                current += char
            elif char == '(' and not in_quotes:
                paren_depth += 1
                current += char
            elif char == ')' and not in_quotes:
                paren_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0 and not in_quotes:
                result.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            result.append(current.strip())
        
        return result
    
    def _parse_single_value(self, value_str: str) -> Any:
        """Parse a single attribute value with proper type handling"""
        value_str = value_str.strip()
        
        # Handle empty
        if not value_str or value_str == '*' or value_str == '.':
            return None
        
        # Handle quoted string
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]
        
        # Handle enum (.VALUE.)
        if value_str.startswith(".") and value_str.endswith("."):
            return {"type": "enum", "value": value_str[1:-1]}
        
        # Handle number
        try:
            if '.' in value_str or 'E' in value_str or 'e' in value_str:
                return {"type": "float", "value": float(value_str)}
            else:
                return {"type": "integer", "value": int(value_str)}
        except ValueError:
            pass
        
        # Handle reference
        if value_str.startswith('#'):
            return {"type": "reference", "id": value_str}
        
        # Handle boolean
        if value_str.upper() == '.T.':
            return True
        if value_str.upper() == '.F.':
            return False
        
        # Handle nested structure (parentheses) - CRITICAL FOR B-REP
        if value_str.startswith("(") and value_str.endswith(")"):
            inner = value_str[1:-1]
            # Recursively parse nested content using smart_split
            nested_parts = self._smart_split(inner)
            nested_values = [self._parse_single_value(p) for p in nested_parts if p]
            return {"type": "nested", "values": nested_values}
        
        # Return as string if nothing else matches
        return value_str
    
    def _extract_all_references(self, attributes: Dict[str, Any]) -> List[str]:
        """Extract all entity references from attributes recursively"""
        references = []
        
        def extract_recursive(obj):
            if isinstance(obj, dict):
                # Handle direct reference
                if obj.get("type") == "reference" and obj.get("id"):
                    references.append(obj["id"])
                # Handle nested structures (CRITICAL for B-REP)
                elif obj.get("type") == "nested" and obj.get("values"):
                    for nested_val in obj["values"]:
                        extract_recursive(nested_val)
                # Recurse through all other dict values
                else:
                    for value in obj.values():
                        extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
            # Handle raw strings with references (e.g., "(#20,#25,#30)")
            elif isinstance(obj, str) and '#' in obj:
                import re
                matches = re.findall(r'#(\d+)', obj)
                for match in matches:
                    references.append(f"#{match}")
        
        extract_recursive(attributes)
        return references
    
    def _build_brep_hierarchy_optimized(self):
        """Optimized B-Rep hierarchy building with early termination"""
        solids = []
        total_faces = 0
        total_edges = 0
        total_vertices = 0
        
        # Find all MANIFOLD_SOLID_BREP and other solid entities
        solid_entities = {
            eid: ent for eid, ent in self.entities.items()
            if any(t in ent["type"] for t in ["MANIFOLD_SOLID_BREP", "BREP_WITH_VOIDS", "FACETED_BREP", "SHELL_BASED_SURFACE_MODEL", "CLOSED_SHELL", "OPEN_SHELL"])
        }
        
        processing_log.info("solid_entities_found", count=len(solid_entities))
        
        # Process each solid
        for solid_id, solid_entity in solid_entities.items():
            try:
                solid_data = self._extract_solid_data_optimized(solid_id, solid_entity)
                if solid_data:
                    solids.append(solid_data)
                    total_faces += solid_data.get("total_faces", 0)
                    total_edges += solid_data.get("total_edges", 0)
                    total_vertices += solid_data.get("total_vertices", 0)
            except Exception as e:
                processing_log.warning("solid_extraction_failed",
                                     solid_id=solid_id,
                                     error=str(e))
        
        self.brep_hierarchy = {
            "solids": solids,
            "total_solids": len(solids),
            "total_faces": total_faces,
            "total_edges": total_edges,
            "total_vertices": total_vertices
        }
        
        processing_log.info("brep_hierarchy_built",
                          solids=len(solids),
                          faces=total_faces,
                          edges=total_edges,
                          vertices=total_vertices)
    
    def _extract_solid_data_optimized(self, solid_id: str, solid_entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimized solid data extraction with caching"""
        shells = []
        
        # Get shell references
        attrs = solid_entity.get("attributes", {})
        shell_refs = []
        
        if "SHELL" in solid_entity.get("type", ""):
            # The entity itself is a shell (no wrapper solid)
            shell_refs.append(solid_id)
        else:
            for key, value in attrs.items():
                if isinstance(value, dict) and value.get("type") == "reference":
                    ref_id = value.get("id")
                    if ref_id and ref_id in self.entities:
                        ref_entity = self.entities[ref_id]
                        if "SHELL" in ref_entity["type"]:
                            shell_refs.append(ref_id)
                elif isinstance(value, str):
                    import re
                    matches = re.findall(r'#(\d+)', value)
                    for match_id in matches:
                        full_id = f"#{match_id}"
                        if full_id in self.entities:
                            ref_entity = self.entities[full_id]
                            if "SHELL" in ref_entity["type"]:
                                shell_refs.append(full_id)
        
        # Process shells (NO LIMIT for complete data)
        for shell_id in shell_refs:
            try:
                shell_data = self._extract_shell_data_fast(shell_id)
                if shell_data:
                    shells.append(shell_data)
            except Exception as e:
                processing_log.warning("shell_extraction_failed",
                                     shell_id=shell_id,
                                     error=str(e))
        
        return {
            "id": solid_id,
            "shells": shells,
            "total_shells": len(shells),
            "total_faces": sum(s.get("total_faces", 0) for s in shells),
            "total_edges": sum(s.get("total_edges", 0) for s in shells),
            "total_vertices": sum(s.get("total_vertices", 0) for s in shells)
        }
    
    def _extract_shell_data_fast(self, shell_id: str) -> Optional[Dict[str, Any]]:
        """Fast shell data extraction"""
        faces = []
        
        shell_entity = self.entities.get(shell_id)
        if not shell_entity:
            return None
        
        # Get face references
        attrs = shell_entity.get("attributes", {})
        face_refs = []
        
        # Method 1: Look for direct structured references
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "reference":
                ref_id = value.get("id")
                if ref_id and ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    if "FACE" in ref_entity["type"]:
                        face_refs.append(ref_id)
        
        # Method 2: Parse nested structures (CRITICAL FOR B-REP!)
        # e.g., attr_1: {'type': 'nested', 'values': [{'type': 'reference', 'id': '#15715'}, ...]}
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "nested" and value.get("values"):
                processing_log.info(f"found_nested_structure_in_shell_{shell_id}", 
                                  key=key, 
                                  nested_count=len(value["values"]))
                for nested_val in value["values"]:
                    if isinstance(nested_val, dict) and nested_val.get("type") == "reference":
                        ref_id = nested_val.get("id")
                        if ref_id and ref_id in self.entities:
                            ref_entity = self.entities[ref_id]
                            if "FACE" in ref_entity["type"]:
                                face_refs.append(ref_id)
                                processing_log.debug("found_face_from_nested", face_id=ref_id)
        
        # Method 3: Parse raw string references from attr_1 (e.g., '(#17,#37,#83...')
        # This handles cases where faces are stored as raw strings
        if not face_refs and "attr_1" in attrs:
            attr_value = attrs["attr_1"]
            if isinstance(attr_value, str):
                # Extract all #ID patterns
                import re
                matches = re.findall(r'#(\d+)', attr_value)
                for match_id in matches:
                    full_id = f"#{match_id}"
                    if full_id in self.entities:
                        ref_entity = self.entities[full_id]
                        if "FACE" in ref_entity["type"]:
                            face_refs.append(full_id)
                            processing_log.debug("found_face_from_raw_string", face_id=full_id)
        
        processing_log.info("shell_face_references_found",
                          shell_id=shell_id,
                          face_count=len(face_refs))
        
        # Process faces (NO LIMIT for complete data)
        for face_id in face_refs:
            try:
                face_data = self._extract_face_data_simple(face_id)
                if face_data:
                    faces.append(face_data)
            except Exception as e:
                processing_log.warning("face_extraction_failed",
                                     face_id=face_id,
                                     error=str(e))
        
        return {
            "id": shell_id,
            "faces": faces,
            "total_faces": len(faces),
            "total_edges": sum(f.get("total_edges", 0) for f in faces),
            "total_vertices": sum(f.get("total_vertices", 0) for f in faces)
        }
    
    def _extract_face_data_simple(self, face_id: str) -> Optional[Dict[str, Any]]:
        """Simple face data extraction with complete B-Rep chain traversal"""
        face_entity = self.entities.get(face_id)
        if not face_entity:
            return None
        
        surface_type = "UNKNOWN"
        edges = []
        
        # Determine surface type from attributes or bound reference
        attrs = face_entity.get("attributes", {})
        
        # Method 1: Look for enum in attributes
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "enum":
                surface_type = value.get("value", "UNKNOWN")
                break
        
        # Method 2: Check surface reference for type (e.g., PLANE, CYLINDRICAL_SURFACE)
        # The surface is usually in attr_2 for ADVANCED_FACE
        if surface_type == "UNKNOWN" and "attr_2" in attrs:
            surf_ref = attrs["attr_2"]
            if isinstance(surf_ref, dict) and surf_ref.get("type") == "reference":
                surf_id = surf_ref.get("id")
                if surf_id and surf_id in self.entities:
                    surf_entity = self.entities[surf_id]
                    # Extract surface type from entity type name
                    full_type = surf_entity.get("type", "")
                    if "PLANE" in full_type:
                        surface_type = "PLANE"
                    elif "CYLINDRICAL" in full_type:
                        surface_type = "CYLINDRICAL_SURFACE"
                    elif "CONICAL" in full_type:
                        surface_type = "CONICAL_SURFACE"
                    elif "SPHERICAL" in full_type:
                        surface_type = "SPHERICAL_SURFACE"
                    elif "TOROIDAL" in full_type:
                        surface_type = "TOROIDAL_SURFACE"
                    elif "B_SPLINE" in full_type:
                        surface_type = "B_SPLINE_SURFACE_WITH_KNOTS"
        
        # CRITICAL: Get edge references through FACE_BOUND → EDGE_LOOP → ORIENTED_EDGE chain
        edge_refs = self._extract_edges_from_face_complete(face_entity)
        
        processing_log.info("face_edge_references_found",
                          face_id=face_id,
                          edge_count=len(edge_refs),
                          surface_type=surface_type)
        
        # Process edges (NO LIMIT for complete data)
        for edge_id in edge_refs:
            edge_data = self._extract_edge_data_basic(edge_id)
            if edge_data:
                edges.append(edge_data)
        
        return {
            "id": face_id,
            "surface_type": surface_type,
            "edges": edges,
            "total_edges": len(edges),
            "total_vertices": len(edges) * 2  # Approximate
        }
    
    def _extract_edges_from_face_complete(self, face_entity: Dict[str, Any]) -> List[str]:
        """
        Complete edge extraction following full B-Rep chain:
        ADVANCED_FACE → FACE_BOUND → EDGE_LOOP → ORIENTED_EDGE → EDGE_CURVE
        """
        edge_refs = []
        attrs = face_entity.get("attributes", {})
        
        # Step 1: Look for FACE_BOUND references in face attributes
        face_bound_refs = []
        for key, value in attrs.items():
            if isinstance(value, dict):
                if value.get("type") == "reference":
                    ref_id = value.get("id")
                    if ref_id and ref_id in self.entities:
                        ref_entity = self.entities[ref_id]
                        if "FACE_BOUND" in ref_entity.get("type", ""):
                            face_bound_refs.append(ref_id)
                elif value.get("type") == "nested":
                    # Extract FACE_BOUND from nested structure
                    for nested_val in value.get("values", []):
                        if isinstance(nested_val, dict) and nested_val.get("type") == "reference":
                            ref_id = nested_val.get("id")
                            if ref_id and ref_id in self.entities:
                                ref_entity = self.entities[ref_id]
                                if "FACE_BOUND" in ref_entity.get("type", ""):
                                    face_bound_refs.append(ref_id)
        
        # Step 2: For each FACE_BOUND, get EDGE_LOOP
        for face_bound_id in face_bound_refs:
            face_bound_entity = self.entities.get(face_bound_id)
            if not face_bound_entity:
                continue
            
            bound_attrs = face_bound_entity.get("attributes", {})
            # EDGE_LOOP is typically in attr_1 of FACE_BOUND
            if "attr_1" in bound_attrs:
                loop_ref = bound_attrs["attr_1"]
                if isinstance(loop_ref, dict) and loop_ref.get("type") == "reference":
                    loop_id = loop_ref.get("id")
                    if loop_id and loop_id in self.entities:
                        loop_entity = self.entities[loop_id]
                        if "EDGE_LOOP" in loop_entity.get("type", ""):
                            # Step 3: Extract edges from EDGE_LOOP
                            edge_refs.extend(self._extract_edges_from_loop_complete(loop_entity))
        
        # Fallback: If no FACE_BOUND found, try direct attribute references
        if not edge_refs:
            for key, value in attrs.items():
                if isinstance(value, dict) and value.get("type") == "reference":
                    ref_id = value.get("id")
                    if ref_id and ref_id in self.entities:
                        ref_entity = self.entities[ref_id]
                        if "EDGE" in ref_entity.get("type", ""):
                            edge_refs.append(ref_id)
        
        return edge_refs
    
    def _extract_edges_from_loop_complete(self, loop_entity: Dict[str, Any]) -> List[str]:
        """
        Extract edges from EDGE_LOOP entity
        EDGE_LOOP contains list of ORIENTED_EDGE entities
        """
        edge_refs = []
        attrs = loop_entity.get("attributes", {})
        
        # Edges are typically stored in attr_1 as nested structure or raw string
        for key, value in attrs.items():
            if isinstance(value, dict):
                if value.get("type") == "reference":
                    # Direct reference to ORIENTED_EDGE
                    ref_id = value.get("id")
                    if ref_id and ref_id in self.entities:
                        ref_entity = self.entities[ref_id]
                        if "ORIENTED_EDGE" in ref_entity.get("type", "") or \
                           "EDGE_CURVE" in ref_entity.get("type", ""):
                            edge_refs.append(ref_id)
                elif value.get("type") == "nested":
                    # Multiple edges in nested structure
                    for nested_val in value.get("values", []):
                        if isinstance(nested_val, dict) and nested_val.get("type") == "reference":
                            ref_id = nested_val.get("id")
                            if ref_id and ref_id in self.entities:
                                ref_entity = self.entities[ref_id]
                                if "ORIENTED_EDGE" in ref_entity.get("type", "") or \
                                   "EDGE_CURVE" in ref_entity.get("type", ""):
                                    edge_refs.append(ref_id)
            # Handle raw string format: "(#20,#25,#30,#35)"
            elif isinstance(value, str) and '#' in value:
                import re
                matches = re.findall(r'#(\d+)', value)
                for match_id in matches:
                    full_id = f"#{match_id}"
                    if full_id in self.entities:
                        entity = self.entities[full_id]
                        if "ORIENTED_EDGE" in entity.get("type", "") or \
                           "EDGE_CURVE" in entity.get("type", ""):
                            edge_refs.append(full_id)
        
        return edge_refs
    
    def _extract_edge_data_basic(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """Basic edge data extraction with proper vertex extraction"""
        edge_entity = self.entities.get(edge_id)
        if not edge_entity:
            processing_log.warning("edge_entity_not_found", edge_id=edge_id, total_entities=len(self.entities))
            return None
        
        curve_type = "UNKNOWN"
        vertices = []
        
        # Handle ORIENTED_EDGE wrapper - it references the actual EDGE_CURVE
        entity_type = edge_entity.get("type", "")
        if "ORIENTED_EDGE" in entity_type:
            # ORIENTED_EDGE('',*,*,#21,.F.) - the actual edge is in attr_3
            attrs = edge_entity.get("attributes", {})
            if "attr_3" in attrs:
                edge_ref = attrs["attr_3"]
                if isinstance(edge_ref, dict) and edge_ref.get("type") == "reference":
                    actual_edge_id = edge_ref.get("id")
                    if not actual_edge_id.startswith('#'):
                        actual_edge_id = f"#{actual_edge_id}"
                    processing_log.info("orientated_edge_followed", oriented_edge=edge_id, actual_edge=actual_edge_id)
                    # Recursively get the actual edge data
                    return self._extract_edge_data_basic(actual_edge_id)
        
        # Now process the actual EDGE_CURVE
        attrs = edge_entity.get("attributes", {})
        
        # Determine curve type from enum or type name
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "enum":
                curve_type = value.get("value", "UNKNOWN")
                break
        
        # CRITICAL: Extract vertices from edge attributes
        # EDGE_CURVE('',#22,#24,#26,.T.) where #22 and #24 are VERTEX_POINT
        processing_log.info(f"extracting_vertices_for_edge_{edge_id}", 
                           has_attr1='attr_1' in attrs,
                           has_attr2='attr_2' in attrs,
                           total_entities_available=len(self.entities),
                           entity_type=edge_entity.get("type"))
        
        # Try both start and end vertices (attr_1 and attr_2)
        for attr_key in ['attr_1', 'attr_2']:
            if attr_key in attrs:
                attr_value = attrs[attr_key]
                processing_log.info(f"edge_{edge_id}_{attr_key}_analysis", 
                                   value_type=type(attr_value).__name__,
                                   value=str(attr_value)[:100],
                                   is_dict=isinstance(attr_value, dict),
                                   ref_type=attr_value.get("type") if isinstance(attr_value, dict) else None,
                                   ref_id=attr_value.get("id") if isinstance(attr_value, dict) else None)
                
                # Method 1: Direct reference to VERTEX_POINT
                if isinstance(attr_value, dict) and attr_value.get("type") == "reference":
                    vertex_id = attr_value.get("id")
                    processing_log.info(f"edge_{edge_id}_vertex_reference_found", vertex_id=vertex_id)
                    
                    if vertex_id:
                        # Try both with and without # prefix
                        if not vertex_id.startswith('#'):
                            vertex_id = f"#{vertex_id}"
                        
                        if vertex_id in self.entities:
                            vertex_entity = self.entities[vertex_id]
                            processing_log.info(f"vertex_entity_found", 
                                               entity_id=vertex_id,
                                               entity_type=vertex_entity.get("type"),
                                               has_attrs='attributes' in vertex_entity)
                            
                            # Check if it's a VERTEX_POINT
                            if "VERTEX" in vertex_entity.get("type", ""):
                                # Get coordinates from vertex
                                vertex_attrs = vertex_entity.get("attributes", {})
                                if "attr_1" in vertex_attrs:
                                    coord_ref = vertex_attrs["attr_1"]
                                    processing_log.info(f"vertex_coord_reference", 
                                                       coord_ref_type=type(coord_ref).__name__,
                                                       coord_ref=str(coord_ref)[:50])
                                    
                                    # Follow reference to CARTESIAN_POINT
                                    if isinstance(coord_ref, dict) and coord_ref.get("type") == "reference":
                                        point_id = coord_ref.get("id")
                                        processing_log.info(f"cartesian_point_reference_found", point_id=point_id)
                                        
                                        if point_id:
                                            # Try both with and without # prefix
                                            if not point_id.startswith('#'):
                                                point_id = f"#{point_id}"
                                            
                                            if point_id in self.entities:
                                                point_entity = self.entities[point_id]
                                                processing_log.info(f"cartesian_point_entity_found", 
                                                                   entity_id=point_id,
                                                                   entity_type=point_entity.get("type"))
                                                
                                                if "CARTESIAN_POINT" in point_entity.get("type", ""):
                                                    # Extract coordinates from CartesianPoint
                                                    coords = self._extract_coordinates_from_cartesian_point(point_entity)
                                                    if coords and len(coords) >= 3:
                                                        vertices.append({
                                                            "coordinates": coords,
                                                            "id": point_id
                                                        })
                                                        processing_log.info(f"vertex_extraction_success", 
                                                                           edge_id=edge_id,
                                                                           coords=coords)
                                                    else:
                                                        processing_log.warning("coordinate_extraction_failed_from_cartesian", 
                                                                             edge_id=edge_id,
                                                                             point_id=point_id,
                                                                             coords=coords)
                                                else:
                                                    processing_log.warning("entity_not_cartesian_point", 
                                                                         entity_id=point_id,
                                                                         entity_type=point_entity.get("type"))
                                            else:
                                                processing_log.warning("cartesian_point_id_not_in_entities", 
                                                                     point_id=point_id)
                                        else:
                                            processing_log.warning("cartesian_point_ref_has_no_id", 
                                                                 coord_ref=coord_ref)
                                    else:
                                        processing_log.warning("vertex_coord_not_reference", 
                                                             attr_key=attr_key,
                                                             coord_ref_type=type(coord_ref).__name__)
                                else:
                                    processing_log.warning("vertex_missing_attr1", vertex_id=vertex_id)
                        else:
                            processing_log.warning("vertex_id_not_in_entities", 
                                                 vertex_id=vertex_id,
                                                 total_entities=len(self.entities))
                    else:
                        processing_log.warning("vertex_ref_has_no_id", attr_key=attr_key)
                
                # Method 2: Raw string with references (e.g., attr_1: '#22')
                elif isinstance(attr_value, str):
                    import re
                    matches = re.findall(r'#(\d+)', attr_value)
                    processing_log.info(f"found_raw_vertex_references", matches=matches)
                    for match_id in matches:
                        vertex_id = f"#{match_id}"
                        if vertex_id in self.entities:
                            vertex_entity = self.entities[vertex_id]
                            if "VERTEX" in vertex_entity.get("type", ""):
                                # Same extraction as above
                                vertex_attrs = vertex_entity.get("attributes", {})
                                if "attr_1" in vertex_attrs:
                                    coord_ref = vertex_attrs["attr_1"]
                                    if isinstance(coord_ref, dict) and coord_ref.get("type") == "reference":
                                        point_id = coord_ref.get("id")
                                        if not point_id.startswith('#'):
                                            point_id = f"#{point_id}"
                                        if point_id in self.entities:
                                            point_entity = self.entities[point_id]
                                            if "CARTESIAN_POINT" in point_entity.get("type", ""):
                                                coords = self._extract_coordinates_from_cartesian_point(point_entity)
                                                if coords and len(coords) >= 3:
                                                    vertices.append({
                                                        "coordinates": coords,
                                                        "id": point_id
                                                    })
        
        processing_log.info("edge_vertices_extracted_summary",
                           edge_id=edge_id,
                           vertex_count=len(vertices),
                           success=len(vertices) > 0)
        
        return {
            "id": edge_id,
            "curve_type": curve_type,
            "vertices": vertices
        }
    
    def _extract_coordinates_from_cartesian_point(self, point_entity: Dict[str, Any]) -> Optional[List[float]]:
        """
        Extract XYZ coordinates from CARTESIAN_POINT entity
        Handles format: CARTESIAN_POINT('',(x,y,z))
        """
        coords = []
        attrs = point_entity.get("attributes", {})
        
        # Look for coordinate values in attributes
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
                                    coords.append(nv.get("value"))
                                elif nv.get("type") == "integer":
                                    coords.append(float(nv.get("value")))
                
                # Handle direct float values
                elif value_type == "float":
                    coords.append(value.get("value"))
                
                # Handle integer values
                elif value_type == "integer":
                    coords.append(float(value.get("value")))
            
            # Handle raw coordinate string: '( 15.44, 15.67, 2.80'
            elif isinstance(value, str) and ('(' in value or ')' in value):
                import re
                numbers = re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', value)
                for num_str in numbers:
                    try:
                        num = float(num_str)
                        if -1e6 < num < 1e6:
                            coords.append(num)
                    except ValueError:
                        pass
        
        return coords if len(coords) >= 3 else None
    
    def _extract_assembly_structure(self):
        """Extract assembly structure from entities"""
        # Simplified assembly extraction
        product_defs = [
            (eid, ent) for eid, ent in self.entities.items()
            if "PRODUCT" in ent["type"] or "ASSEMBLY" in ent["type"]
        ]
        
        for entity_id, entity in product_defs[:100]:  # Limit to 100
            self.structure.append({
                "id": entity_id,
                "name": entity.get("attributes", {}).get("attr_1", entity_id),
                "type": entity["type"],
                "children": []
            })
