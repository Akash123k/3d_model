"""
B-Rep geometry parser based on brep.py
Parses STEP files and builds entity tree with references
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from datetime import datetime


class BRepGeometryParser:
    """Parser for STEP files using brep.py methodology"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.reverse_refs: Dict[str, List[str]] = defaultdict(list)
        self.brep_tree: List[Dict[str, Any]] = []
        
    def parse(self) -> Dict[str, Any]:
        """Parse STEP file and build B-Rep tree"""
        # Parse entities
        self._parse_step_file()
        
        # Build reverse reference map
        self._build_reverse_references()
        
        # Find components (solids)
        components = self._find_components()
        
        # Build tree for each component
        for comp_id in components[:5]:  # Limit to 5 components for performance
            tree = self._build_tree(comp_id)
            self.brep_tree.append(tree)
        
        # Extract all coordinates for bounding box
        all_coords = self._extract_all_coordinates()
        bbox = self._compute_bounding_box(all_coords)
        
        return {
            "entities": self.entities,
            "brep_tree": self.brep_tree,
            "total_components": len(components),
            "bounding_box": bbox,
            "file_size": self.file_path.stat().st_size,
            "filename": self.file_path.name
        }
    
    def _parse_step_file(self):
        """Parse STEP file entities"""
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Pattern to match STEP entities: #123 = ENTITY_NAME (...)
        pattern = re.compile(r'#(\d+)\s*=\s*([A-Z_]+)\s*\((.*?)\);', re.S)
        
        for match in pattern.finditer(content):
            eid = f"#{match.group(1)}"
            etype = match.group(2)
            raw = match.group(3)
            
            # Extract references
            refs = re.findall(r'#\d+', raw)
            
            # Extract coordinates for CARTESIAN_POINT
            coords = None
            if etype == "CARTESIAN_POINT":
                nums = re.findall(r'[-+]?\d*\.\d+|\d+', raw)
                if len(nums) >= 3:
                    coords = [float(nums[0]), float(nums[1]), float(nums[2])]
            
            self.entities[eid] = {
                "id": eid,
                "type": etype,
                "refs": refs,
                "coords": coords,
                "raw_data": raw.strip()
            }
    
    def _build_reverse_references(self):
        """Build reverse reference map (who references this entity)"""
        for eid, entity in self.entities.items():
            for ref in entity["refs"]:
                self.reverse_refs[ref].append(eid)
    
    def _find_components(self) -> List[str]:
        """Find top-level solid components"""
        component_types = [
            "MANIFOLD_SOLID_BREP",
            "CLOSED_SHELL",
            "SHELL_BASED_SURFACE_MODEL"
        ]
        
        return [
            eid for eid, entity in self.entities.items()
            if entity["type"] in component_types
        ]
    
    def _build_tree(self, root_id: str, max_depth: int = 10) -> Dict[str, Any]:
        """Build hierarchical tree from root entity"""
        visited = set()
        
        root_node = {
            "id": root_id,
            "type": self.entities[root_id]["type"],
            "label": f"{root_id} [{self.entities[root_id]['type']}]",
            "children": [],
            "depth": 0
        }
        
        queue = deque([(root_id, root_node, 0)])
        
        while queue:
            current_id, current_node, depth = queue.popleft()
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            entity = self.entities.get(current_id)
            if not entity:
                continue
            
            # Get both forward references and backward references
            neighbors = entity["refs"] + self.reverse_refs.get(current_id, [])
            
            for neighbor_id in neighbors:
                if neighbor_id not in self.entities or neighbor_id in visited:
                    continue
                
                neighbor_entity = self.entities[neighbor_id]
                
                child_node = {
                    "id": neighbor_id,
                    "type": neighbor_entity["type"],
                    "label": f"{neighbor_id} [{neighbor_entity['type']}]",
                    "children": [],
                    "depth": depth + 1
                }
                
                # Add coordinates if available
                if neighbor_entity["coords"]:
                    child_node["coords"] = neighbor_entity["coords"]
                
                current_node["children"].append(child_node)
                queue.append((neighbor_id, child_node, depth + 1))
        
        return root_node
    
    def _extract_all_coordinates(self) -> List[List[float]]:
        """Extract all Cartesian points"""
        coords_list = []
        for entity in self.entities.values():
            if entity["type"] == "CARTESIAN_POINT" and entity["coords"]:
                coords_list.append(entity["coords"])
        return coords_list
    
    def _compute_bounding_box(self, coords_list: List[List[float]]) -> Optional[Dict[str, Any]]:
        """Compute bounding box from coordinates"""
        if not coords_list:
            return None
        
        xs = [p[0] for p in coords_list]
        ys = [p[1] for p in coords_list]
        zs = [p[2] for p in coords_list]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        
        return {
            "min": [min_x, min_y, min_z],
            "max": [max_x, max_y, max_z],
            "dimensions": [max_x - min_x, max_y - min_y, max_z - min_z]
        }