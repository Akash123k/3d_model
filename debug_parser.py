#!/usr/bin/env python3
"""Debug parser output"""

import re
from pathlib import Path

step_file = Path(__file__).parent / "test_files" / "small_cube.step"

with open(step_file, 'r') as f:
    content = f.read()

# Clean content
content_clean = re.sub(r'[\r\n]+', ' ', content)
content_clean = re.sub(r'\s+', ' ', content_clean)

# Pattern
entity_pattern = re.compile(r'#(\d+)\s*=\s*([A-Z_0-9]+)\s*\(([^)]*)\)\s*;')

print("Testing entity extraction:")
print("="*80)

for match in entity_pattern.finditer(content_clean):
    entity_id = f"#{match.group(1)}"
    entity_type = match.group(2)
    attributes_str = match.group(3)
    
    if entity_type in ["CLOSED_SHELL", "ADVANCED_FACE", "CARTESIAN_POINT"]:
        print(f"\n{entity_id} = {entity_type}")
        print(f"  Attributes: {attributes_str}")
