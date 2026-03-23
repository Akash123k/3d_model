#!/usr/bin/env python3
"""Debug script to trace B-Rep hierarchy extraction"""

import sys
import os
# Prevent pydantic validation error by removing VITE_API_URL
if 'VITE_API_URL' in os.environ:
    del os.environ['VITE_API_URL']

sys.path.insert(0, '/home/venom/akash/3d_model/backend')

from app.services.step_parser_optimized import OptimizedSTEPParser
import json

def debug_fan_step():
    print("=" * 80)
    print("DEBUGGING Fan.stp B-Rep HEXTRACTION")
    print("=" * 80)
    
    parser = OptimizedSTEPParser('/home/venom/akash/3d_model/fan-design-11.snapshot.1/Fan.stp', max_workers=4)
    data = parser.parse()
    
    print(f"\n✓ Total entities parsed: {len(data['entities'])}")
    print(f"✓ B-Rep solids found: {len(data['brep_hierarchy'].get('solids', []))}")
    print(f"✓ Total faces in B-Rep: {data['brep_hierarchy'].get('total_faces', 0)}")
    
    # Detailed tracing
    if not data['brep_hierarchy'].get('solids'):
        print("\n❌ ERROR: No solids found in B-Rep hierarchy!")
        return
    
    solid = data['brep_hierarchy']['solids'][0]
    print(f"\n--- Analyzing first solid: {solid['id']} ---")
    print(f"  Shells: {len(solid.get('shells', []))}")
    
    if not solid.get('shells'):
        print("  ❌ ERROR: No shells in solid!")
        return
    
    shell = solid['shells'][0]
    print(f"  Shell ID: {shell['id']}")
    print(f"  Faces in shell: {len(shell.get('faces', []))}")
    
    if not shell.get('faces'):
        print("  ❌ ERROR: No faces in shell!")
        # Check what face_refs were found
        shell_entity = parser.entities.get(shell['id'])
        if shell_entity:
            attrs = shell_entity.get('attributes', {})
            print(f"  Shell attributes keys: {list(attrs.keys())}")
            for key, value in attrs.items():
                print(f"    {key}: type={type(value).__name__}, value={str(value)[:100]}")
        return
    
    face = shell['faces'][0]
    print(f"\n  --- Analyzing first face: {face['id']} ---")
    print(f"  Surface type: {face.get('surface_type', 'UNKNOWN')}")
    print(f"  Edges in face: {len(face.get('edges', []))}")
    print(f"  Vertices in face: {face.get('total_vertices', 0)}")
    
    if not face.get('edges') or len(face['edges']) == 0:
        print("  ❌ ERROR: No edges in face!")
        # Check what edge_refs were found
        face_entity = parser.entities.get(face['id'])
        if face_entity:
            print(f"  Face entity type: {face_entity['type']}")
            attrs = face_entity.get('attributes', {})
            print(f"  Face attributes: {list(attrs.keys())}")
            for key, value in attrs.items():
                if isinstance(value, dict):
                    print(f"    {key}: type={value.get('type')}, id={value.get('id') or value.get('value', 'N/A')[:50]}")
                else:
                    print(f"    {key}: {type(value).__name__} = {str(value)[:100]}")
        return
    
    edge = face['edges'][0]
    print(f"\n  --- Analyzing first edge: {edge['id']} ---")
    print(f"  Curve type: {edge.get('curve_type', 'UNKNOWN')}")
    print(f"  Vertices in edge: {len(edge.get('vertices', []))}")
    
    if not edge.get('vertices') or len(edge['vertices']) == 0:
        print("  ❌ ERROR: No vertices in edge!")
        edge_entity = parser.entities.get(edge['id'])
        if edge_entity:
            print(f"  Edge entity type: {edge_entity['type']}")
            attrs = edge_entity.get('attributes', {})
            print(f"  Edge attributes: {list(attrs.keys())}")
            for key, value in attrs.items():
                if isinstance(value, dict):
                    print(f"    {key}: type={value.get('type')}, ", end='')
                    if value.get('type') == 'nested':
                        print(f"nested_values_count={len(value.get('values', []))}")
                        # Show first few nested values
                        for i, nv in enumerate(value.get('values', [])[:3]):
                            if isinstance(nv, dict):
                                print(f"      [{i}]: type={nv.get('type')}, id={nv.get('id', 'N/A')}")
                    else:
                        print(f"id={value.get('id') or value.get('value', 'N/A')[:50]}")
                else:
                    print(f"    {key}: {type(value).__name__} = {str(value)[:100]}")
        return
    
    vertex = edge['vertices'][0]
    print(f"\n  ✓ SUCCESS: First vertex coordinates: {vertex.get('coordinates', [])}")
    print("\n✓✓✓ B-Rep extraction is WORKING correctly!")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    total_faces = 0
    total_edges = 0
    total_vertices = 0
    faces_with_edges = 0
    edges_with_vertices = 0
    
    for solid in data['brep_hierarchy']['solids']:
        for shell in solid.get('shells', []):
            for face in shell.get('faces', []):
                total_faces += 1
                if face.get('edges') and len(face['edges']) > 0:
                    faces_with_edges += 1
                    for edge in face['edges']:
                        total_edges += 1
                        if edge.get('vertices') and len(edge['vertices']) > 0:
                            edges_with_vertices += 1
                            total_vertices += len(edge['vertices'])
    
    print(f"Total faces: {total_faces}")
    print(f"Faces WITH edges: {faces_with_edges} ({faces_with_edges/total_faces*100:.1f}%)" if total_faces > 0 else "N/A")
    print(f"Edges WITH vertices: {edges_with_vertices} ({edges_with_vertices/total_edges*100:.1f}%)" if total_edges > 0 else "N/A")
    print(f"Total edges across all faces: {total_edges}")
    print(f"Total vertices across all faces: {total_vertices}")
    
    if faces_with_edges == 0:
        print("\n❌ CRITICAL ISSUE: NO FACES HAVE EDGES - This is why 3D viewer shows nothing!")
    elif edges_with_vertices == 0:
        print("\n❌ CRITICAL ISSUE: NO EDGES HAVE VERTICES - This is why 3D viewer shows nothing!")
    else:
        print(f"\n✓✓✓ DATA LOOKS GOOD! {total_vertices} vertices available for mesh generation!")

if __name__ == '__main__':
    debug_fan_step()
