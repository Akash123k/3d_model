#!/usr/bin/env python3
"""
Test script to verify B-Rep geometry parser integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend/app'))

from services.brep_geometry_parser import BRepGeometryParser

def test_parser(step_file):
    """Test the B-Rep parser with a STEP file"""
    print(f"Testing B-Rep parser with: {step_file}")
    print("=" * 60)
    
    if not os.path.exists(step_file):
        print(f"❌ File not found: {step_file}")
        return False
    
    try:
        parser = BRepGeometryParser(step_file)
        result = parser.parse()
        
        print(f"✅ Parsing successful!")
        print(f"\n📊 Statistics:")
        print(f"   Total entities: {len(result['entities'])}")
        print(f"   Total components: {result['total_components']}")
        print(f"   B-Rep trees: {len(result['brep_tree'])}")
        
        if result['bounding_box']:
            print(f"\n📦 Bounding Box:")
            print(f"   Min: {result['bounding_box']['min']}")
            print(f"   Max: {result['bounding_box']['max']}")
            print(f"   Dimensions: {result['bounding_box']['dimensions']}")
        
        print(f"\n🌳 Component Trees:")
        for i, tree in enumerate(result['brep_tree'][:2], 1):
            print(f"\n   === Component {i} ===")
            print_tree_recursive(tree, 0)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def print_tree_recursive(node, depth=0):
    """Print tree node recursively"""
    indent = "  " * depth
    label = node.get('label', node.get('id', 'Unknown'))
    
    # Add coordinates if available
    coords_str = ""
    if node.get('coords') and len(node['coords']) == 3:
        coords = node['coords']
        coords_str = f" ({coords[0]:.2f}, {coords[1]:.2f}, {coords[2]:.2f})"
    
    print(f"{indent}{label}{coords_str}")
    
    # Print first few children to avoid spam
    children = node.get('children', [])
    for i, child in enumerate(children[:5]):
        print_tree_recursive(child, depth + 1)
    
    if len(children) > 5:
        print(f"{indent}  ... and {len(children) - 5} more children")

if __name__ == "__main__":
    # Test files to try
    test_files = [
        "test_files/small_cube.step",
        "fan-design-11.snapshot.1/Fan.stp",
        "3 DOFs Robot Arm.STEP"
    ]
    
    # Find first available test file
    test_file = None
    for tf in test_files:
        if os.path.exists(tf):
            test_file = tf
            break
    
    if not test_file:
        print("❌ No test files found. Please provide a STEP file path.")
        print("Usage: python3 test_brep_parser.py /path/to/file.step")
        sys.exit(1)
    
    success = test_parser(test_file)
    sys.exit(0 if success else 1)
