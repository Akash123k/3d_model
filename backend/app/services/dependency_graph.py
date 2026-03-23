"""
Dependency graph builder service
Creates graph visualization of STEP entity references
OPTIMIZED WITH MULTITHREADING for large files
"""

from typing import Dict, List, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from app.core.logging import processing_log
from app.models.schemas import GraphNode, GraphEdge


class DependencyGraphBuilder:
    """Builds dependency graph from STEP entities - OPTIMIZED WITH PARALLEL PROCESSING"""
    
    def __init__(self, entities: Dict[str, Dict[str, Any]], max_workers: int = 16):
        self.entities = entities
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.max_workers = max_workers
        self.lock = threading.Lock()
        
        processing_log.info("dependency_graph_builder_initialized",
                          max_workers=max_workers,
                          total_entities=len(entities))
        
    def build(self) -> Dict[str, Any]:
        """
        Build dependency graph from entities using MULTITHREADING
        Returns graph data structure
        """
        processing_log.info("dependency_graph_build_started",
                          total_entities=len(self.entities),
                          max_workers=self.max_workers,
                          parallel_processing="enabled")
        
        try:
            # Create nodes for all entities (parallel processing)
            self._create_nodes_parallel()
            
            # Create edges based on references (parallel processing)
            self._create_edges_parallel()
            
            processing_log.info("dependency_graph_build_completed",
                              total_nodes=len(self.nodes),
                              total_edges=len(self.edges),
                              parallel_efficiency="optimized")
            
            return {
                "nodes": [node.model_dump() if hasattr(node, "model_dump") else node.dict() for node in self.nodes.values()],
                "edges": [edge.model_dump() if hasattr(edge, "model_dump") else edge.dict() for edge in self.edges],
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges)
            }
            
        except Exception as e:
            processing_log.error("dependency_graph_build_failed",
                               error=str(e))
            raise
    
    def _create_nodes_parallel(self):
        """Create graph nodes from entities using multithreading"""
        processing_log.info("parallel_node_creation_started",
                          total_entities=len(self.entities),
                          workers=self.max_workers)
        
        # Split entities into chunks for parallel processing
        entity_items = list(self.entities.items())
        chunk_size = max(len(entity_items) // (self.max_workers * 2), 100)
        chunks = [entity_items[i:i + chunk_size] for i in range(0, len(entity_items), chunk_size)]
        
        processing_log.info("node_processing_chunks_created",
                          chunks=len(chunks),
                          chunk_size=chunk_size)
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._process_node_chunk, chunk) for chunk in chunks]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    with self.lock:
                        self.nodes.update(result)
                    completed += 1
                    if completed % 5 == 0:
                        processing_log.info("node_creation_progress",
                                          completed=completed,
                                          total=len(futures),
                                          percentage=round((completed / len(futures)) * 100, 2))
                except Exception as e:
                    processing_log.error("node_chunk_processing_failed", error=str(e))
        
        # Calculate importance scores (can be done in parallel too)
        self._calculate_importance_parallel()
        
        processing_log.info("parallel_node_creation_completed",
                          total_nodes=len(self.nodes),
                          parallel_efficiency="high")
    
    def _process_node_chunk(self, chunk: List[tuple]) -> Dict[str, GraphNode]:
        """Process a chunk of entities into nodes"""
        local_nodes = {}
        type_counts = {}
        
        for entity_id, entity_data in chunk:
            entity_type = entity_data['type']
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
            
            # Create meaningful label
            label = f"{entity_type}_{entity_id}"
            
            # For common types, use shorter labels
            if type_counts[entity_type] > 50:
                label = f"{entity_type.split('_')[0]}_{entity_id}"
            
            node = GraphNode(
                id=entity_id,
                label=label,
                type=entity_data['type'],
                properties={
                    **entity_data.get('attributes', {}),
                    'references_count': len(entity_data.get('references', [])),
                    'importance': 0  # Will be calculated later
                }
            )
            local_nodes[entity_id] = node
        
        return local_nodes
    
    def _calculate_importance_parallel(self):
        """Calculate node importance scores based on references"""
        importance_scores = {eid: 0 for eid in self.entities.keys()}
        
        # Count references in parallel
        entity_items = list(self.entities.items())
        chunk_size = max(len(entity_items) // self.max_workers, 100)
        chunks = [entity_items[i:i + chunk_size] for i in range(0, len(entity_items), chunk_size)]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._count_references_chunk, chunk) for chunk in chunks]
            
            for future in as_completed(futures):
                try:
                    chunk_scores = future.result()
                    for eid, score in chunk_scores.items():
                        importance_scores[eid] += score
                except Exception as e:
                    processing_log.error("importance_calculation_failed", error=str(e))
        
        # Update node importance
        for entity_id, score in importance_scores.items():
            if entity_id in self.nodes:
                self.nodes[entity_id].properties['importance'] = score
        
        # Log reference statistics
        total_refs = sum(importance_scores.values())
        processing_log.info("dependency_graph_references",
                          total_entities=len(self.entities),
                          total_references=total_refs,
                          avg_refs_per_entity=round(total_refs / max(len(self.entities), 1), 2))
    
    def _count_references_chunk(self, chunk: List[tuple]) -> Dict[str, int]:
        """Count references for a chunk of entities"""
        scores = {}
        for entity_id, entity_data in chunk:
            scores[entity_id] = 0
            for ref_id in entity_data.get('references', []):
                if ref_id in scores:
                    scores[ref_id] += 1
                else:
                    scores[ref_id] = 1
        return scores
    
    def _create_edges_parallel(self):
        """Create edges based on entity references using multithreading"""
        processing_log.info("parallel_edge_creation_started",
                          total_entities=len(self.entities),
                          workers=self.max_workers)
        
        # Split entities into chunks for parallel processing
        entity_items = list(self.entities.items())
        chunk_size = max(len(entity_items) // (self.max_workers * 2), 100)
        chunks = [entity_items[i:i + chunk_size] for i in range(0, len(entity_items), chunk_size)]
        
        processing_log.info("edge_processing_chunks_created",
                          chunks=len(chunks),
                          chunk_size=chunk_size)
        
        all_edges = []
        local_node_updates = {}
        
        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._process_edge_chunk, chunk) for chunk in chunks]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    edges, node_updates = future.result()
                    all_edges.extend(edges)
                    for nid, updates in node_updates.items():
                        if nid not in local_node_updates:
                            local_node_updates[nid] = {'references': set(), 'referenced_by': set()}
                        local_node_updates[nid]['references'].update(updates['references'])
                        local_node_updates[nid]['referenced_by'].update(updates['referenced_by'])
                    completed += 1
                    if completed % 5 == 0:
                        processing_log.info("edge_creation_progress",
                                          completed=completed,
                                          total=len(futures),
                                          percentage=round((completed / len(futures)) * 100, 2))
                except Exception as e:
                    processing_log.error("edge_chunk_processing_failed", error=str(e))
        
        # Add all edges
        self.edges.extend(all_edges)
        
        # Apply node updates
        for node_id, updates in local_node_updates.items():
            if node_id in self.nodes:
                self.nodes[node_id].references.extend(list(updates['references']))
                self.nodes[node_id].referenced_by.extend(list(updates['referenced_by']))
        
        processing_log.info("parallel_edge_creation_completed",
                          total_edges=len(self.edges),
                          parallel_efficiency="high")
    
    def _process_edge_chunk(self, chunk: List[tuple]) -> tuple:
        """Process a chunk of entities into edges"""
        edges = []
        node_updates = {}
        
        for entity_id, entity_data in chunk:
            references = entity_data.get('references', [])
            
            for ref_id in references:
                if ref_id in self.entities:
                    edge = GraphEdge(
                        source=entity_id,
                        target=ref_id,
                        relationship="REFERENCES"
                    )
                    edges.append(edge)
                    
                    # Track node updates
                    if entity_id not in node_updates:
                        node_updates[entity_id] = {'references': set(), 'referenced_by': set()}
                    if ref_id not in node_updates:
                        node_updates[ref_id] = {'references': set(), 'referenced_by': set()}
                    
                    node_updates[entity_id]['references'].add(ref_id)
                    node_updates[ref_id]['referenced_by'].add(entity_id)
        
        return edges, node_updates
    
    def get_subgraph(self, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Get subgraph around a specific entity
        depth: how many levels of connections to include
        """
        if entity_id not in self.entities:
            return {"nodes": [], "edges": []}
        
        visited = set()
        nodes_to_include = {entity_id}
        edges_to_include = []
        
        # BFS to find connected nodes within depth
        current_level = [entity_id]
        for d in range(depth):
            next_level = []
            for eid in current_level:
                if eid in visited:
                    continue
                visited.add(eid)
                
                # Add references
                entity = self.entities.get(eid, {})
                refs = entity.get('references', [])
                for ref in refs:
                    if ref in self.entities and ref not in visited:
                        nodes_to_include.add(ref)
                        next_level.append(ref)
                        edges_to_include.append(GraphEdge(
                            source=eid,
                            target=ref,
                            relationship="REFERENCES"
                        ))
                
                # Add referenced by
                for other_id, other_entity in self.entities.items():
                    if eid in other_entity.get('references', []):
                        if other_id not in visited:
                            nodes_to_include.add(other_id)
                            next_level.append(other_id)
                            edges_to_include.append(GraphEdge(
                                source=other_id,
                                target=eid,
                                relationship="REFERENCES"
                            ))
            
            current_level = next_level
        
        # Filter nodes
        filtered_nodes = [
            self.nodes[nid] 
            for nid in nodes_to_include 
            if nid in self.nodes
        ]
        
        return {
            "nodes": filtered_nodes,
            "edges": edges_to_include,
            "center_node": entity_id
        }
