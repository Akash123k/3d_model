"""
STEP file parser service
Parses STEP files and extracts structure and geometry with detailed B-Rep hierarchy
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
import json

from app.core.logging import processing_log, log
from app.models.schemas import AssemblyNode


class STEPParser:
    """Advanced parser for STEP (.step, .stp) files with B-Rep hierarchy extraction"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.structure: List[Dict[str, Any]] = []
        self.raw_lines: List[str] = []
        self.brep_hierarchy: Dict[str, Any] = {}
        
    def parse(self) -> Dict[str, Any]:
        """
        Parse the STEP file and extract structure with B-Rep hierarchy
        Returns parsed data structure
        """
        processing_log.info("step_file_parse_started", 
                        file_path=str(self.file_path),
                        timestamp=datetime.now().isoformat())
        
        try:
            # Read file content
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            self.raw_lines = content.split('\n')
            
            # Parse entities with detailed attributes
            self._parse_entities_detailed(content)
            
            # Build B-Rep hierarchy
            self._build_brep_hierarchy()
            
            # Extract assembly structure
            self._extract_assembly_structure()
            
            processing_log.info("step_file_parse_completed",
                            total_entities=len(self.entities),
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
            processing_log.error("step_file_parse_failed",
                            error=str(e),
                            file_path=str(self.file_path))
            raise
    
    def _parse_entities_detailed(self, content: str):
        """Parse STEP entities with complete attribute extraction"""
        # Pattern to match STEP entities like: #123 = ENTITY_NAME (...);
        # Handle Windows line endings and normalize whitespace
        content_clean = re.sub(r'[\r\n]+', ' ', content)  # Replace line breaks with spaces
        content_clean = re.sub(r'\s+', ' ', content_clean)  # Normalize remaining whitespace
        
        # Updated pattern to handle spaces before semicolon and match closing paren
        entity_pattern = re.compile(r'#(\d+)\s*=\s*([A-Z_]+)\s*\(([^)]*)\)')
        
        for match in entity_pattern.finditer(content_clean):
            entity_id = f"#{match.group(1)}"
            entity_type = match.group(2)
            attributes_str = match.group(3)
            
            # Parse attributes with proper handling of nested structures
            attributes = self._parse_advanced_attributes(attributes_str)
            
            self.entities[entity_id] = {
                "id": entity_id,
                "type": entity_type,
                "attributes": attributes,
                "references": self._extract_all_references(attributes),
                "raw_data": attributes_str.strip()
            }
    
    def _parse_advanced_attributes(self, attributes_str: str) -> Dict[str, Any]:
        """Parse attributes with support for nested structures and enums"""
        attributes = {}
        
        # Handle empty attributes
        if not attributes_str.strip():
            return attributes
        
        # Split by comma but respect parentheses and quotes
        parts = self._smart_split(attributes_str)
        
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
                
            key = f"attr_{i}"
            parsed_value = self._parse_attribute_value(part)
            
            if parsed_value is not None:
                attributes[key] = parsed_value
        
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
    
    def _parse_attribute_value(self, value: str) -> Any:
        """Parse individual attribute value"""
        value = value.strip()
        
        if not value:
            return None
        
        # String literal
        if value.startswith("'") and value.endswith("'"):
            return {"value": value.strip("'"), "type": "string"}
        
        # Entity reference
        if value.startswith("#"):
            return {"ref": value, "type": "reference"}
        
        # Boolean
        if value == ".T.":
            return {"value": True, "type": "boolean"}
        if value == ".F.":
            return {"value": False, "type": "boolean"}
        
        # Enum (e.g., .CARTESIAN_POINT.)
        if value.startswith(".") and value.endswith("."):
            return {"value": value.strip("."), "type": "enum"}
        
        # Integer
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return {"value": int(value), "type": "integer"}
        
        # Float
        try:
            float_val = float(value)
            return {"value": float_val, "type": "float"}
        except ValueError:
            pass
        
        # Nested structure (parentheses)
        if value.startswith("(") and value.endswith(")"):
            inner = value[1:-1]
            nested_parts = self._smart_split(inner)
            nested_values = [self._parse_attribute_value(p) for p in nested_parts if p]
            return {"values": nested_values, "type": "nested"}
        
        # Default: treat as string
        return {"value": value, "type": "unknown"}
    
    def _extract_all_references(self, attributes: Dict[str, Any]) -> List[str]:
        """Extract all entity references from attributes recursively"""
        refs = []
        
        def extract_recursive(obj: Any):
            if isinstance(obj, dict):
                if obj.get("type") == "reference" and obj.get("ref"):
                    refs.append(obj["ref"])
                else:
                    for value in obj.values():
                        extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(attributes)
        return refs
    
    def _build_brep_hierarchy(self):
        """Build detailed B-Rep hierarchy from STEP entities"""
        processing_log.info("brep_hierarchy_building_started")
        
        # First, try to find MANIFOLD_SOLID_BREP entities (primary structure)
        solids = []
        for entity_id, entity in self.entities.items():
            if entity["type"] == "MANIFOLD_SOLID_BREP":
                solid = self._build_solid_from_brep(entity)
                if solid:
                    solids.append(solid)
        
        # If no MANIFOLD_SOLID_BREP found, fall back to shells
        if not solids:
            processing_log.info("no_manifold_solids_found_trying_shells")
            for entity_id, entity in self.entities.items():
                if 'SHELL' in entity["type"] or entity["type"] in ['CLOSED_SHELL', 'OPEN_SHELL']:
                    solid = self._build_solid_from_shell(entity)
                    if solid:
                        solids.append(solid)
        
        # Build hierarchy for each solid
        solid_count = 0
        for solid in solids:
            self.brep_hierarchy.setdefault('solids', []).append(solid)
            solid_count += 1
        
        # Count totals accurately
        self.brep_hierarchy['total_solids'] = solid_count
        
        # Count faces by actually traversing the hierarchy
        total_faces = 0
        for solid in self.brep_hierarchy.get('solids', []):
            for shell in solid.get('shells', []):
                total_faces += len(shell.get('faces', []))
        
        self.brep_hierarchy['total_faces'] = total_faces
        
        processing_log.info("brep_hierarchy_built",
                        solids=solid_count,
                        faces=total_faces)
    
    def _build_solid_from_shell(self, shell_entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build a solid from a shell entity with meaningful data"""
        solid = {
            "id": shell_entity["id"],
            "type": "MANIFOLD_SOLID_BREP",
            "name": f"Solid Component {shell_entity['id']}",
            "description": "A manifold solid boundary representation",
            "shells": [],
            "properties": {
                "entity_id": shell_entity["id"],
                "is_closed": "CLOSED" in shell_entity.get("type", ""),
                "solid_type": "B-Rep"
            }
        }
        
        shell_data = {
            "id": shell_entity["id"],
            "name": f"Shell {shell_entity['id']}",
            "description": "Collection of connected faces",
            "faces": [],
            "properties": {
                "shell_type": "CLOSED_SHELL" if "CLOSED" in shell_entity.get("type", "") else "OPEN_SHELL"
            }
        }
        
        # Get faces from shell
        face_refs = self._get_face_references(shell_entity)
        for face_ref in face_refs[:50]:  # Limit for performance
            face_data = self._build_face_hierarchy(face_ref)
            if face_data:
                shell_data["faces"].append(face_data)
        
        # Calculate shell statistics
        shell_data["statistics"] = {
            "total_faces": len(shell_data["faces"]),
            "surface_types": list(set(
                [f.get("surface_type", "UNKNOWN") for f in shell_data["faces"]]
            ))
        }
        
        solid["shells"].append(shell_data)
        
        # Add solid-level statistics
        solid["statistics"] = {
            "total_shells": len(solid["shells"]),
            "total_faces": sum([len(s.get("faces", [])) for s in solid["shells"]]),
            "volume_approximate": self._calculate_approximate_volume(shell_data)
        }
        
        return solid
    
    def _build_solid_from_brep(self, brep_entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build a solid directly from MANIFOLD_SOLID_BREP entity"""
        solid = {
            "id": brep_entity["id"],
            "type": "MANIFOLD_SOLID_BREP",
            "name": f"Solid Component {brep_entity['id']}",
            "description": "A manifold solid boundary representation",
            "shells": [],
            "properties": {
                "entity_id": brep_entity["id"],
                "solid_type": "B-Rep"
            }
        }
        
        # Find shell references in B-Rep attributes
        shell_refs = self._get_shell_references(brep_entity)
        
        for shell_ref in shell_refs:
            shell_data = self._build_shell_from_reference(shell_ref)
            if shell_data:
                solid["shells"].append(shell_data)
        
        # If no shells found directly, search all entities
        if not solid["shells"]:
            processing_log.info("no_direct_shells_found_searching_all",
                              solid_id=brep_entity["id"])
            
            # Look for SHELL entities that might belong to this solid
            for entity_id, entity in self.entities.items():
                if 'SHELL' in entity["type"]:
                    # Check if this shell references the solid or is referenced by it
                    if self._shell_belongs_to_solid(entity, brep_entity):
                        shell_data = self._build_shell_from_reference(entity_id)
                        if shell_data:
                            solid["shells"].append(shell_data)
        
        # Add solid-level statistics
        solid["statistics"] = {
            "total_shells": len(solid["shells"]),
            "total_faces": sum([len(s.get("faces", [])) for s in solid["shells"]])
        }
        
        return solid
    
    def _get_shell_references(self, brep_entity: Dict[str, Any]) -> List[str]:
        """Get shell references from B-Rep entity"""
        shell_refs = []
        attrs = brep_entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict):
                if value.get("type") == "reference":
                    ref_id = value.get("ref")
                    if ref_id and ref_id in self.entities:
                        ref_entity = self.entities[ref_id]
                        if 'SHELL' in ref_entity["type"]:
                            shell_refs.append(ref_id)
                elif value.get("type") == "nested":
                    shell_refs.extend(self._extract_refs_from_nested_by_type(value, 'SHELL'))
        
        return shell_refs
    
    def _extract_refs_from_nested_by_type(self, nested: Dict[str, Any], 
                                         target_type: str) -> List[str]:
        """Extract references of specific type from nested structure"""
        refs = []
        values = nested.get("values", [])
        
        for val in values:
            if isinstance(val, dict):
                if val.get("type") == "reference":
                    ref_id = val.get("ref")
                    if ref_id and ref_id in self.entities:
                        if target_type in self.entities[ref_id]["type"]:
                            refs.append(ref_id)
                elif val.get("type") == "nested":
                    refs.extend(self._extract_refs_from_nested_by_type(val, target_type))
        
        return refs
    
    def _shell_belongs_to_solid(self, shell_entity: Dict[str, Any], 
                               solid_entity: Dict[str, Any]) -> bool:
        """Check if a shell belongs to a solid by analyzing relationships"""
        # Simple heuristic: check if shell is referenced in solid's attributes
        solid_attrs_str = str(solid_entity.get("attributes", {}))
        return shell_entity["id"] in solid_attrs_str
    
    def _build_shell_from_reference(self, shell_ref: str) -> Optional[Dict[str, Any]]:
        """Build shell data from a shell reference"""
        if shell_ref not in self.entities:
            return None
        
        shell_entity = self.entities[shell_ref]
        
        shell_data = {
            "id": shell_entity["id"],
            "name": f"Shell {shell_entity['id']}",
            "description": "Collection of connected faces",
            "faces": [],
            "properties": {
                "shell_type": "CLOSED_SHELL" if "CLOSED" in shell_entity.get("type", "") else "OPEN_SHELL"
            }
        }
        
        # Get faces using improved traversal
        face_refs = self._get_face_references_improved(shell_entity)
        
        for face_ref in face_refs[:50]:  # Limit for performance
            face_data = self._build_face_hierarchy(face_ref)
            if face_data:
                shell_data["faces"].append(face_data)
        
        # Calculate shell statistics
        shell_data["statistics"] = {
            "total_faces": len(shell_data["faces"]),
            "surface_types": list(set(
                [f.get("surface_type", "UNKNOWN") for f in shell_data["faces"]]
            ))
        }
        
        return shell_data
    
    def _get_face_references_improved(self, shell_entity: Dict[str, Any]) -> List[str]:
        """Improved method to get face references through proper STEP structure traversal"""
        face_refs = []
        
        # Method 1: Direct attribute references (including through FACE_BOUND)
        attrs = shell_entity.get("attributes", {})
        for key, value in attrs.items():
            refs = self._extract_face_refs_recursive(value)
            face_refs.extend(refs)
        
        # Method 2: Search all FACE_BOUND entities that reference this shell
        if not face_refs:
            processing_log.info("direct_face_refs_not_found_searching_all",
                              shell_id=shell_entity["id"])
            
            # Look for FACE_BOUND entities that might connect shell to faces
            for entity_id, entity in self.entities.items():
                if entity["type"] == "FACE_BOUND":
                    # Check if this FACE_BOUND is referenced by or references the shell
                    if self._face_bound_connected_to_shell(entity, shell_entity):
                        # Extract the face from FACE_BOUND
                        face_refs.extend(self._extract_face_from_face_bound(entity))
        
        # Method 3: Last resort - search for ADVANCED_FACE entities and check relationships
        if not face_refs:
            processing_log.info("face_bound_search_failed_trying_direct_faces",
                              shell_id=shell_entity["id"])
            
            # Try to find faces by looking at what the shell directly references
            shell_refs = self._get_all_direct_references(shell_entity)
            for ref_id in shell_refs:
                if ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    if ref_entity["type"] == "ADVANCED_FACE":
                        face_refs.append(ref_id)
        
        # Remove duplicates
        face_refs = list(set(face_refs))
        
        processing_log.info("face_references_extracted",
                          shell_id=shell_entity["id"],
                          face_count=len(face_refs))
        
        return face_refs
    
    def _face_bound_connected_to_shell(self, face_bound_entity: Dict[str, Any], 
                                       shell_entity: Dict[str, Any]) -> bool:
        """Check if a FACE_BOUND entity is connected to a shell"""
        # Get all entities that reference this FACE_BOUND
        referencing_entities = self._get_entities_referencing(face_bound_entity["id"])
        
        # Check if any of them is the shell or related to the shell
        for ref_entity_id in referencing_entities:
            if ref_entity_id == shell_entity["id"]:
                return True
            
            # Check if it's an EDGE_LOOP that might be part of the shell's structure
            if ref_entity_id in self.entities:
                ref_entity = self.entities[ref_entity_id]
                if 'LOOP' in ref_entity["type"]:
                    # Check if this loop is referenced by the shell
                    if self._entity_references(shell_entity, ref_entity_id):
                        return True
        
        return False
    
    def _extract_face_from_face_bound(self, face_bound_entity: Dict[str, Any]) -> List[str]:
        """Extract face reference from FACE_BOUND entity"""
        attrs = face_bound_entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "reference":
                ref_id = value.get("ref")
                if ref_id and ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    if 'FACE' in ref_entity["type"]:
                        return [ref_id]
        
        return []
    
    def _get_all_direct_references(self, entity: Dict[str, Any]) -> List[str]:
        """Get all direct entity references from an entity's attributes"""
        refs = []
        attrs = entity.get("attributes", {})
        
        for key, value in attrs.items():
            extracted = self._extract_refs_recursive_simple(value)
            refs.extend(extracted)
        
        return refs
    
    def _extract_refs_recursive_simple(self, value: Any) -> List[str]:
        """Simple recursive reference extraction"""
        refs = []
        
        if isinstance(value, dict):
            if value.get("type") == "reference" and value.get("ref"):
                refs.append(value["ref"])
            elif value.get("type") == "nested":
                for nested_val in value.get("values", []):
                    refs.extend(self._extract_refs_recursive_simple(nested_val))
        
        return refs
    
    def _get_entities_referencing(self, target_id: str) -> List[str]:
        """Get all entities that reference the target entity"""
        referencing = []
        
        for entity_id, entity in self.entities.items():
            if self._entity_references(entity, target_id):
                referencing.append(entity_id)
        
        return referencing
    
    def _entity_references(self, entity: Dict[str, Any], target_id: str) -> bool:
        """Check if an entity references a target entity ID"""
        attrs = entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict):
                if value.get("type") == "reference" and value.get("ref") == target_id:
                    return True
                elif value.get("type") == "nested":
                    if self._nested_contains_reference(value, target_id):
                        return True
        
        return False
    
    def _nested_contains_reference(self, nested: Dict[str, Any], target_id: str) -> bool:
        """Check if nested structure contains reference to target"""
        for val in nested.get("values", []):
            if isinstance(val, dict):
                if val.get("type") == "reference" and val.get("ref") == target_id:
                    return True
                elif val.get("type") == "nested":
                    if self._nested_contains_reference(val, target_id):
                        return True
        
        return False
    
    def _extract_face_refs_recursive(self, value: Any) -> List[str]:
        """Recursively extract face references through nested structures including FACE_BOUND and EDGE_LOOP"""
        refs = []
        
        if isinstance(value, dict):
            if value.get("type") == "reference":
                ref_id = value.get("ref")
                if ref_id and ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    
                    # Direct face reference
                    if 'FACE' in ref_entity["type"]:
                        refs.append(ref_id)
                    
                    # Traverse through intermediate entities (FACE_BOUND, EDGE_LOOP)
                    elif ref_entity["type"] == "FACE_BOUND":
                        nested_refs = self._extract_face_refs_from_face_bound(ref_entity)
                        refs.extend(nested_refs)
                    elif ref_entity["type"] == "EDGE_LOOP":
                        # EDGE_LOOP doesn't directly reference faces, skip
                        pass
                        
            elif value.get("type") == "nested":
                for nested_val in value.get("values", []):
                    refs.extend(self._extract_face_refs_recursive(nested_val))
        
        return refs
    
    def _extract_face_refs_from_face_bound(self, face_bound_entity: Dict[str, Any]) -> List[str]:
        """Extract face reference from FACE_BOUND entity"""
        # FACE_BOUND has an attribute pointing to the actual face
        attrs = face_bound_entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "reference":
                ref_id = value.get("ref")
                if ref_id and ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    if 'FACE' in ref_entity["type"]:
                        return [ref_id]
        
        return []
    
    def _face_belongs_to_shell(self, face_entity: Dict[str, Any], 
                              shell_entity: Dict[str, Any]) -> bool:
        """Check if a face belongs to a shell by analyzing relationships"""
        # Simple heuristic: check if shell ID appears in face's context
        # More sophisticated: trace through FACE_BOUND entities
        
        # For now, use string matching as fallback
        face_attrs_str = str(face_entity.get("attributes", {}))
        return shell_entity["id"] in face_attrs_str
    
    def _get_face_references(self, shell_entity: Dict[str, Any]) -> List[str]:
        """Get face references from shell entity"""
        face_refs = []
        
        # Check attributes for face references
        attrs = shell_entity.get("attributes", {})
        for key, value in attrs.items():
            if isinstance(value, dict):
                if value.get("type") == "reference":
                    ref_id = value.get("ref")
                    if ref_id and ref_id in self.entities:
                        ref_entity = self.entities[ref_id]
                        if 'FACE' in ref_entity["type"]:
                            face_refs.append(ref_id)
                elif value.get("type") == "nested":
                    # Look for references in nested structures
                    face_refs.extend(self._extract_refs_from_nested(value))
        
        return face_refs
    
    def _extract_refs_from_nested(self, nested: Dict[str, Any]) -> List[str]:
        """Extract face references from nested structure"""
        refs = []
        values = nested.get("values", [])
        
        for val in values:
            if isinstance(val, dict):
                if val.get("type") == "reference":
                    ref_id = val.get("ref")
                    if ref_id and ref_id in self.entities:
                        if 'FACE' in self.entities[ref_id]["type"]:
                            refs.append(ref_id)
                elif val.get("type") == "nested":
                    refs.extend(self._extract_refs_from_nested(val))
        
        return refs
    
    def _build_face_hierarchy(self, face_ref: str) -> Optional[Dict[str, Any]]:
        """Build complete face hierarchy with meaningful edges and vertices"""
        if face_ref not in self.entities:
            return None
        
        face_entity = self.entities[face_ref]
        
        # Extract surface description first
        surface_desc = self._extract_surface_description(face_entity)
        surface_type = surface_desc["type"] if surface_desc else "UNKNOWN_SURFACE"
        
        face_data = {
            "id": face_entity["id"],
            "name": f"{surface_type.replace('_', ' ').title()} {face_entity['id']}",
            "type": face_entity["type"],
            "surface_type": surface_type,
            "description": self._get_face_description(surface_type),
            "edges": [],
            "vertices": [],
            "surface_description": surface_desc,
            "properties": {
                "is_planar": surface_type == "PLANE",
                "is_curved": surface_type in ["CYLINDRICAL_SURFACE", "SPHERICAL_SURFACE", 
                                            "CONICAL_SURFACE", "TOROIDAL_SURFACE"],
                "surface_class": self._get_surface_class(surface_type)
            }
        }
        
        # Extract edge loops and boundaries
        edge_loops = self._extract_edge_loops(face_entity)
        for loop in edge_loops:
            loop_edges = self._extract_edges_from_loop(loop)
            face_data["edges"].extend(loop_edges)
        
        # Extract vertices from edges
        for edge in face_data["edges"]:
            if "vertices" in edge:
                face_data["vertices"].extend(edge["vertices"])
        
        # Remove duplicate vertices
        unique_vertices = []
        seen_ids = set()
        for vertex in face_data["vertices"]:
            vid = json.dumps(vertex, sort_keys=True)
            if vid not in seen_ids:
                unique_vertices.append(vertex)
                seen_ids.add(vid)
        face_data["vertices"] = unique_vertices
        
        # Calculate face statistics
        face_data["statistics"] = {
            "total_edges": len(face_data["edges"]),
            "total_vertices": len(face_data["vertices"]),
            "edge_types": list(set(
                [e.get("curve_type", "UNKNOWN") for e in face_data["edges"]]
            )),
            "perimeter_approximate": self._calculate_perimeter(face_data["edges"])
        }
        
        return face_data
    
    def _get_face_description(self, surface_type: str) -> str:
        """Get human-readable description of face type"""
        descriptions = {
            "PLANE": "A flat rectangular or polygonal surface",
            "CYLINDRICAL_SURFACE": "A curved surface forming part of a cylinder",
            "CONICAL_SURFACE": "A tapered curved surface forming part of a cone",
            "SPHERICAL_SURFACE": "A curved surface forming part of a sphere",
            "TOROIDAL_SURFACE": "A doughnut-shaped curved surface",
            "SURFACE_OF_REVOLUTION": "A surface created by rotating a curve",
            "B_SPLINE_SURFACE_WITH_KNOTS": "A complex free-form surface",
            "UNKNOWN_SURFACE": "A surface of unspecified type"
        }
        return descriptions.get(surface_type, "A geometric surface")
    
    def _get_surface_class(self, surface_type: str) -> str:
        """Classify surface as planar, curved, or complex"""
        if surface_type == "PLANE":
            return "planar"
        elif surface_type in ["CYLINDRICAL_SURFACE", "CONICAL_SURFACE", "SPHERICAL_SURFACE", "TOROIDAL_SURFACE"]:
            return "curved"
        else:
            return "complex"
    
    def _calculate_perimeter(self, edges: List[Dict[str, Any]]) -> float:
        """Calculate approximate perimeter from edges"""
        perimeter = 0.0
        for edge in edges:
            if edge.get("geometry"):
                geom = edge["geometry"]
                if geom.get("type") == "LINE":
                    # Calculate line length from vertices
                    vertices = edge.get("vertices", [])
                    if len(vertices) >= 2:
                        v1, v2 = vertices[0].get("coordinates", [0,0,0]), vertices[1].get("coordinates", [0,0,0])
                        length = sum([(v2[i] - v1[i])**2 for i in range(3)]) ** 0.5
                        perimeter += length
                elif geom.get("type") == "CIRCLE":
                    # Calculate circumference
                    radius = geom.get("properties", {}).get("radius", 0)
                    perimeter += 2 * 3.14159 * radius
        return round(perimeter, 2)
    
    def _calculate_approximate_volume(self, shell_data: Dict[str, Any]) -> float:
        """Calculate approximate volume using bounding box method"""
        all_vertices = []
        for face in shell_data.get("faces", []):
            for vertex in face.get("vertices", []):
                coords = vertex.get("coordinates")
                if coords and len(coords) == 3:
                    all_vertices.append(coords)
        
        if len(all_vertices) < 8:
            return 0.0
        
        # Calculate bounding box
        xs = [v[0] for v in all_vertices]
        ys = [v[1] for v in all_vertices]
        zs = [v[2] for v in all_vertices]
        
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        dz = max(zs) - min(zs)
        
        # Approximate as box volume (this is rough estimate)
        volume = dx * dy * dz
        return round(volume, 2)
    
    def _extract_surface_description(self, face_entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract surface description from face entity"""
        # Look for surface reference in attributes
        attrs = face_entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "reference":
                ref_id = value.get("ref")
                if ref_id and ref_id in self.entities:
                    surface_entity = self.entities[ref_id]
                    surface_type = surface_entity["type"]
                    
                    # Handle different surface types
                    if surface_type in ['PLANE', 'CYLINDRICAL_SURFACE', 'CONICAL_SURFACE', 
                                    'SPHERICAL_SURFACE', 'TOROIDAL_SURFACE',
                                    'SURFACE_OF_REVOLUTION', 'SURFACE_OF_LINEAR_EXTRUSION',
                                    'B_SPLINE_SURFACE_WITH_KNOTS']:
                        
                        surface_data = {
                            "type": surface_type,
                            "properties": {}
                        }
                        
                        # Extract surface properties
                        surface_attrs = surface_entity.get("attributes", {})
                        
                        # For cylindrical/conical/spherical surfaces, extract radius
                        if 'RADIUS' in str(surface_attrs):
                            for attr_val in surface_attrs.values():
                                if isinstance(attr_val, dict) and attr_val.get("type") == "float":
                                    surface_data["properties"]["radius"] = attr_val.get("value")
                        
                        # For toroidal surface, extract major and minor radius
                        if surface_type == 'TOROIDAL_SURFACE':
                            float_values = [
                                v.get("value") for v in surface_attrs.values()
                                if isinstance(v, dict) and v.get("type") == "float"
                            ]
                            if len(float_values) >= 2:
                                surface_data["properties"]["major_radius"] = float_values[0]
                                surface_data["properties"]["minor_radius"] = float_values[1]
                        
                        # For conical surface, extract angle
                        if surface_type == 'CONICAL_SURFACE':
                            for attr_val in surface_attrs.values():
                                if isinstance(attr_val, dict) and attr_val.get("type") == "float":
                                    surface_data["properties"]["angle"] = attr_val.get("value")
                        
                        # Extract axis placement
                        for attr_val in surface_attrs.values():
                            if isinstance(attr_val, dict) and attr_val.get("type") == "reference":
                                axis_ref = attr_val.get("ref")
                                if axis_ref and axis_ref in self.entities:
                                    axis_entity = self.entities[axis_ref]
                                    if 'AXIS' in axis_entity["type"] or 'PLACEMENT' in axis_entity["type"]:
                                        surface_data["properties"]["axis_placement"] = self._extract_axis_placement(axis_entity)
                        
                        return surface_data
        
        return None
    
    def _extract_axis_placement(self, axis_entity: Dict[str, Any]) -> Dict[str, Any]:
        """Extract axis placement 3D data"""
        placement_data = {
            "type": axis_entity["type"],
            "location": None,
            "axis": None,
            "ref_direction": None
        }
        
        attrs = axis_entity.get("attributes", {})
        
        # Extract location (Cartesian point)
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "reference":
                ref_id = value.get("ref")
                if ref_id and ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    if ref_entity["type"] == 'CARTESIAN_POINT':
                        coords = self._extract_coordinates(ref_entity)
                        if coords:
                            placement_data["location"] = coords
                    elif ref_entity["type"] == 'DIRECTION':
                        direction = self._extract_direction(ref_entity)
                        if direction:
                            placement_data["axis"] = direction
        
        return placement_data
    
    def _extract_coordinates(self, point_entity: Dict[str, Any]) -> Optional[List[float]]:
        """Extract XYZ coordinates from Cartesian point"""
        coords = []
        attrs = point_entity.get("attributes", {})
        
        # Look for coordinate values
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
        
        return coords if len(coords) == 3 else None
    
    def _extract_direction(self, direction_entity: Dict[str, Any]) -> Optional[List[float]]:
        """Extract direction ratios"""
        return self._extract_coordinates(direction_entity)
    
    def _extract_edge_loops(self, face_entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract edge loops from face"""
        loops = []
        attrs = face_entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "reference":
                ref_id = value.get("ref")
                if ref_id and ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    if 'LOOP' in ref_entity["type"]:
                        loops.append(ref_entity)
            elif isinstance(value, dict) and value.get("type") == "nested":
                # Check nested for loop references
                for nested_val in value.get("values", []):
                    if isinstance(nested_val, dict) and nested_val.get("type") == "reference":
                        ref_id = nested_val.get("ref")
                        if ref_id and ref_id in self.entities:
                            ref_entity = self.entities[ref_id]
                            if 'LOOP' in ref_entity["type"]:
                                loops.append(ref_entity)
        
        return loops
    
    def _extract_edges_from_loop(self, loop_entity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract edges from edge loop"""
        edges = []
        attrs = loop_entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict):
                if value.get("type") == "reference":
                    ref_id = value.get("ref")
                    if ref_id and ref_id in self.entities:
                        edge_entity = self.entities[ref_id]
                        if 'EDGE' in edge_entity["type"]:
                            edge_data = self._build_edge_data(edge_entity)
                            if edge_data:
                                edges.append(edge_data)
                elif value.get("type") == "nested":
                    for nested_val in value.get("values", []):
                        if isinstance(nested_val, dict) and nested_val.get("type") == "reference":
                            ref_id = nested_val.get("ref")
                            if ref_id and ref_id in self.entities:
                                edge_entity = self.entities[ref_id]
                                if 'EDGE' in edge_entity["type"]:
                                    edge_data = self._build_edge_data(edge_entity)
                                    if edge_data:
                                        edges.append(edge_data)
        
        return edges
    
    def _build_edge_data(self, edge_entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build edge data with meaningful geometry and vertices"""
        edge_data = {
            "id": edge_entity["id"],
            "name": f"Edge {edge_entity['id']}",
            "type": edge_entity["type"],
            "curve_type": None,
            "description": None,
            "vertices": [],
            "geometry": None,
            "properties": {}
        }
        
        # Extract edge curve geometry
        attrs = edge_entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "reference":
                ref_id = value.get("ref")
                if ref_id and ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    
                    # Extract curve type
                    if ref_entity["type"] in ['LINE', 'CIRCLE', 'ELLIPSE', 'B_SPLINE_CURVE_WITH_KNOTS']:
                        edge_data["curve_type"] = ref_entity["type"]
                        edge_data["geometry"] = self._extract_curve_geometry(ref_entity)
                        edge_data["description"] = self._get_edge_description(ref_entity["type"])
                        edge_data["properties"] = self._get_edge_properties(ref_entity)
                    
                    # Extract vertices
                    if ref_entity["type"] == 'VERTEX_POINT':
                        coords = self._extract_coordinates(ref_entity)
                        if coords:
                            edge_data["vertices"].append({
                                "type": "VERTEX_POINT",
                                "coordinates": coords,
                                "label": f"Vertex at ({coords[0]:.2f}, {coords[1]:.2f}, {coords[2]:.2f})"
                            })
                    
                    # Check for oriented edge
                    if 'ORIENTED' in ref_entity["type"]:
                        oriented_edge = self._extract_oriented_edge(ref_entity)
                        if oriented_edge:
                            edge_data.update(oriented_edge)
        
        # Calculate edge length if possible
        if edge_data["geometry"] and edge_data["vertices"]:
            edge_data["properties"]["length"] = self._calculate_edge_length(edge_data)
        
        return edge_data
    
    def _get_edge_description(self, curve_type: str) -> str:
        """Get human-readable description of edge type"""
        descriptions = {
            "LINE": "A straight line segment between two points",
            "CIRCLE": "A circular arc with constant radius",
            "ELLIPSE": "An elliptical curve with major and minor axes",
            "B_SPLINE_CURVE_WITH_KNOTS": "A smooth free-form curve"
        }
        return descriptions.get(curve_type, "A geometric curve")
    
    def _get_edge_properties(self, curve_entity: Dict[str, Any]) -> Dict[str, Any]:
        """Extract meaningful properties from curve"""
        props = {
            "curve_type": curve_entity["type"]
        }
        
        attrs = curve_entity.get("attributes", {})
        
        # Extract radius for circles
        if curve_entity["type"] == "CIRCLE":
            for attr_val in attrs.values():
                if isinstance(attr_val, dict) and attr_val.get("type") == "float":
                    props["radius"] = attr_val.get("value")
                    break
        
        # Extract axes for ellipses
        if curve_entity["type"] == "ELLIPSE":
            float_values = [
                v.get("value") for v in attrs.values()
                if isinstance(v, dict) and v.get("type") == "float"
            ]
            if len(float_values) >= 2:
                props["major_axis"] = float_values[0]
                props["minor_axis"] = float_values[1]
        
        return props
    
    def _calculate_edge_length(self, edge_data: Dict[str, Any]) -> float:
        """Calculate approximate edge length"""
        vertices = edge_data.get("vertices", [])
        geometry = edge_data.get("geometry")
        
        if not geometry or len(vertices) < 2:
            return 0.0
        
        if geometry["type"] == "LINE":
            # Calculate distance between two vertices
            v1, v2 = vertices[0]["coordinates"], vertices[-1]["coordinates"]
            length = sum([(v2[i] - v1[i])**2 for i in range(3)]) ** 0.5
            return round(length, 2)
        
        elif geometry["type"] == "CIRCLE":
            # Calculate arc length (assuming full circle for now)
            radius = geometry.get("properties", {}).get("radius", 0)
            return round(2 * 3.14159 * radius, 2)
        
        return 0.0
    
    def _extract_curve_geometry(self, curve_entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract curve geometry (line, circle, ellipse, etc.)"""
        geometry = {
            "type": curve_entity["type"],
            "properties": {}
        }
        
        attrs = curve_entity.get("attributes", {})
        
        # Extract radius for circles
        if curve_entity["type"] == 'CIRCLE':
            for attr_val in attrs.values():
                if isinstance(attr_val, dict):
                    if attr_val.get("type") == "float":
                        geometry["properties"]["radius"] = attr_val.get("value")
                    elif attr_val.get("type") == "reference":
                        ref_id = attr_val.get("ref")
                        if ref_id and ref_id in self.entities:
                            axis_entity = self.entities[ref_id]
                            if 'AXIS' in axis_entity["type"]:
                                geometry["properties"]["axis_placement"] = self._extract_axis_placement(axis_entity)
        
        # Extract major/minor axes for ellipse
        if curve_entity["type"] == 'ELLIPSE':
            float_values = [
                v.get("value") for v in attrs.values()
                if isinstance(v, dict) and v.get("type") == "float"
            ]
            if len(float_values) >= 2:
                geometry["properties"]["major_axis"] = float_values[0]
                geometry["properties"]["minor_axis"] = float_values[1]
        
        # Extract axis placement
        for attr_val in attrs.values():
            if isinstance(attr_val, dict) and attr_val.get("type") == "reference":
                ref_id = attr_val.get("ref")
                if ref_id and ref_id in self.entities:
                    axis_entity = self.entities[ref_id]
                    if 'AXIS' in axis_entity["type"]:
                        geometry["properties"]["axis_placement"] = self._extract_axis_placement(axis_entity)
        
        return geometry
    
    def _extract_oriented_edge(self, oriented_entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract oriented edge data"""
        attrs = oriented_entity.get("attributes", {})
        
        for key, value in attrs.items():
            if isinstance(value, dict) and value.get("type") == "reference":
                ref_id = value.get("ref")
                if ref_id and ref_id in self.entities:
                    edge_entity = self.entities[ref_id]
                    if 'EDGE' in edge_entity["type"]:
                        return self._build_edge_data(edge_entity)
        
        return None
    
    def _extract_assembly_structure(self):
        """Extract assembly structure from entities using B-Rep hierarchy"""
        processing_log.info("assembly_structure_extraction_started",
                        total_entities=len(self.entities))
        
        # Use B-Rep hierarchy as the primary structure
        if self.brep_hierarchy and self.brep_hierarchy.get('solids'):
            root_node = {
                "id": str(uuid.uuid4()),
                "name": self.file_path.stem,
                "type": "STEP_MODEL",
                "children": [],
                "properties": {
                    "file": self.file_path.name,
                    "total_solids": self.brep_hierarchy.get('total_solids', 0),
                    "total_faces": self.brep_hierarchy.get('total_faces', 0)
                }
            }
            
            # Add solids as children
            for solid in self.brep_hierarchy['solids'][:10]:  # Limit solids
                solid_node = self._create_solid_node(solid)
                if solid_node:
                    root_node["children"].append(solid_node)
            
            self.structure = [root_node]
        else:
            # Fallback to old method if no B-Rep hierarchy found
            self._extract_assembly_structure_fallback()
        
        processing_log.info("assembly_structure_extraction_completed",
                        total_nodes=len(self.structure))
    
    def _create_solid_node(self, solid: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create assembly tree node from solid"""
        solid_node = {
            "id": solid["id"],
            "name": f"Solid {solid['id']}",
            "type": "SOLID",
            "children": [],
            "properties": {
                "solid_type": solid.get("type", "MANIFOLD_SOLID_BREP")
            }
        }
        
        # Add shells
        for shell in solid.get("shells", []):
            shell_node = {
                "id": shell["id"],
                "name": f"Shell {shell['id']}",
                "type": "SHELL",
                "children": []
            }
            
            # Add faces (limit for performance)
            for face in shell.get("faces", [])[:20]:
                face_node = self._create_face_node(face)
                if face_node:
                    shell_node["children"].append(face_node)
            
            solid_node["children"].append(shell_node)
        
        return solid_node
    
    def _create_face_node(self, face: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create face node with edges and vertices"""
        face_node = {
            "id": face["id"],
            "name": f"{face.get('surface_type', 'Face')} {face['id']}",
            "type": "FACE",
            "children": [],
            "properties": {
                "surface_type": face.get("surface_type"),
                "edge_count": len(face.get("edges", [])),
                "vertex_count": len(face.get("vertices", []))
            }
        }
        
        # Group edges by type
        edge_types = {}
        for edge in face.get("edges", []):
            edge_type = edge.get("curve_type", 'UNKNOWN')
            if edge_type not in edge_types:
                edge_types[edge_type] = []
            edge_types[edge_type].append(edge)
        
        # Create edge group nodes
        for edge_type, edges in edge_types.items():
            edge_group_node = {
                "id": f"{face['id']}_{edge_type}",
                "name": f"{edge_type.replace('_', ' ').title()} ({len(edges)})",
                "type": "EDGE_GROUP",
                "children": []
            }
            
            # Add individual edges
            for edge in edges[:10]:  # Limit edges per group
                edge_node = {
                    "id": edge["id"],
                    "name": f"Edge {edge['id']}",
                    "type": "EDGE",
                    "children": [],
                    "properties": {
                        "curve_type": edge.get("curve_type"),
                        "vertex_count": len(edge.get("vertices", []))
                    }
                }
                
                # Add vertices
                for vertex in edge.get("vertices", [])[:5]:  # Limit vertices
                    vertex_node = {
                        "id": f"{edge['id']}_vertex",
                        "name": "Vertex",
                        "type": "VERTEX",
                        "properties": {
                            "coordinates": vertex.get("coordinates")
                        }
                    }
                    edge_node["children"].append(vertex_node)
                
                edge_group_node["children"].append(edge_node)
            
            face_node["children"].append(edge_group_node)
        
        return face_node
    
    def _extract_assembly_structure_fallback(self):
        """Fallback assembly structure extraction if B-Rep fails"""
        root_node = {
            "id": str(uuid.uuid4()),
            "name": self.file_path.stem,
            "type": "ASSEMBLY",
            "children": [],
            "properties": {"file": self.file_path.name}
        }
        
        # Group by types
        type_groups: Dict[str, List[Dict[str, Any]]] = {}
        for entity_id, entity in self.entities.items():
            entity_type = entity["type"]
            if entity_type not in type_groups:
                type_groups[entity_type] = []
            type_groups[entity_type].append(entity)
        
        # Add top entity types
        for entity_type, entities in list(type_groups.items())[:20]:
            if len(entities) > 0:
                type_node = {
                    "id": str(uuid.uuid4()),
                    "name": entity_type.replace('_', ' ').title(),
                    "type": "TYPE_GROUP",
                    "children": [
                        {
                            "id": entity["id"],
                            "name": f"{entity_type}_{entity['id']}",
                            "type": "ENTITY",
                            "children": [],
                            "properties": {
                                "entity_data": entity
                            }
                        }
                        for entity in entities[:5]
                    ],
                    "properties": {
                        "count": len(entities)
                    }
                }
                root_node["children"].append(type_node)
        
        self.structure = [root_node]
    
    def _build_hierarchy_from_references_old(
        self, 
        entities: List[Dict[str, Any]], 
        all_type_groups: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Build hierarchy based on entity references (OLD METHOD - kept for compatibility)"""
        children = []
        processed_ids = set()
        
        # Find entities that are referenced by others (these are likely parents)
        reference_counts = {}
        for entity in entities:
            entity_id = entity["id"]
            ref_count = 0
            
            # Count how many times this entity is referenced
            for other_entity in entities + sum(all_type_groups.values(), []):
                if entity_id in other_entity.get("references", []):
                    ref_count += 1
            
            reference_counts[entity_id] = ref_count
        
        # Sort by reference count (most referenced first = likely root nodes)
        sorted_entities = sorted(
            entities, 
            key=lambda e: reference_counts.get(e["id"], 0), 
            reverse=True
        )
        
        # Create nodes
        for entity in sorted_entities[:15]:  # Limit to top 15
            if entity["id"] in processed_ids:
                continue
                
            node = {
                "id": str(uuid.uuid4()),
                "name": f"{entity['type']}_{entity['id']}",
                "type": "INSTANCE",
                "children": [],
                "properties": {
                    "entity_id": entity["id"],
                    "entity_type": entity["type"],
                    "attributes": entity.get("attributes", {})
                }
            }
            
            # Add direct references as children
            for ref_id in entity.get("references", [])[:5]:  # Limit children
                if ref_id in self.entities:
                    ref_entity = self.entities[ref_id]
                    child_node = {
                        "id": str(uuid.uuid4()),
                        "name": f"{ref_entity['type']}_{ref_id}",
                        "type": "REFERENCE",
                        "children": [],
                        "properties": {
                            "entity_id": ref_id,
                            "entity_type": ref_entity["type"]
                        }
                    }
                    node["children"].append(child_node)
            
            children.append(node)
            processed_ids.add(entity["id"])
        
        return children
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by its ID"""
        return self.entities.get(entity_id)
    
    def get_references(self, entity_id: str) -> List[str]:
        """Get all entities referenced by given entity"""
        entity = self.entities.get(entity_id)
        if entity:
            return entity.get("references", [])
        return []
    
    def get_referenced_by(self, entity_id: str) -> List[str]:
        """Get all entities that reference the given entity"""
        referencing = []
        for eid, entity in self.entities.items():
            if entity_id in entity.get("references", []):
                referencing.append(eid)
        return referencing
