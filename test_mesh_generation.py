#!/usr/bin/env python3
"""Test mesh generation from B-Rep data"""

import sys
import os
if 'VITE_API_URL' in os.environ:
    del os.environ['VITE_API_URL']

sys.path.insert(0, '/home/venom/akash/3d_model/backend')

from app.services.step_parser_optimized import OptimizedSTEPParser
from app.services.mesh_generator import MeshGenerator

def test_mesh_generation():
    print("=" * 80)
    print("TESTING MESH GENERATION FROM Fan.stp")
    print("=" * 80)
    
    # Step 1: Parse STEP file
    print("\n[1/2] Parsing STEP file...")
    parser = OptimizedSTEPParser('/home/venom/akash/3d_model/fan-design-11.snapshot.1/Fan.stp', max_workers=4)
    parsed_data = parser.parse()
    
    print(f"  ✓ Parsed {len(parsed_data['entities'])} entities")
    print(f"  ✓ Found {len(parsed_data['brep_hierarchy'].get('solids', []))} solids")
    print(f"  ✓ Found {parsed_data['brep_hierarchy'].get('total_faces', 0)} faces")
    
    # Step 2: Generate meshes
    print("\n[2/2] Generating meshes...")
    mesh_gen = MeshGenerator(max_workers=4)
    meshes = mesh_gen.generate_meshes(parsed_data.get("brep_hierarchy", {}))
    
    print(f"  ✓ Generated {len(meshes)} mesh objects")
    
    # Analyze mesh quality
    total_vertices = 0
    total_triangles = 0
    meshes_with_vertices = 0
    
    for mesh in meshes:
        vertex_count = len(mesh.get('vertices', [])) // 3
        index_count = len(mesh.get('indices', [])) // 3
        total_vertices += vertex_count
        total_triangles += index_count
        
        if vertex_count > 0:
            meshes_with_vertices += 1
    
    print(f"\n{'='*80}")
    print("MESH GENERATION RESULTS")
    print(f"{'='*80}")
    print(f"Total mesh objects: {len(meshes)}")
    print(f"Meshes WITH vertices: {meshes_with_vertices} ({meshes_with_vertices/len(meshes)*100:.1f}%)" if meshes else "N/A")
    print(f"Total vertices: {total_vertices}")
    print(f"Total triangles: {total_triangles}")
    
    if meshes and meshes_with_vertices > 0:
        print("\n✓✓✓ MESH GENERATION SUCCESSFUL! 3D viewer should work now!")
        
        # Show sample mesh
        if meshes:
            sample = meshes[0]
            print(f"\nSample mesh data:")
            print(f"  Face ID: {sample.get('face_id')}")
            print(f"  Surface type: {sample.get('surface_type')}")
            print(f"  Vertices: {len(sample.get('vertices', [])) // 3}")
            print(f"  Indices: {len(sample.get('indices', [])) // 3}")
            if sample.get('vertices'):
                coords = sample['vertices'][:9]
                print(f"  First 3 vertices: {coords}")
    else:
        print("\n❌ MESH GENERATION FAILED - No usable mesh data generated!")

if __name__ == '__main__':
    test_mesh_generation()
