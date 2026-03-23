# 


import re
import sys
from collections import defaultdict, deque

# ---------- PARSE STEP ----------
def parse_step(file):
    with open(file, "r", errors="ignore") as f:
        content = f.read()

    pattern = re.compile(r'#(\d+)\s*=\s*([A-Z_]+)\s*\((.*?)\);', re.S)

    entities = {}

    for m in pattern.finditer(content):
        eid = f"#{m.group(1)}"
        etype = m.group(2)
        raw = m.group(3)

        refs = re.findall(r'#\d+', raw)

        coords = None
        if etype == "CARTESIAN_POINT":
            nums = re.findall(r'[-+]?\d*\.\d+|\d+', raw)
            if len(nums) >= 3:
                coords = [float(nums[0]), float(nums[1]), float(nums[2])]

        entities[eid] = {
            "type": etype,
            "refs": refs,
            "coords": coords
        }

    return entities


# ---------- BUILD REVERSE ----------
def build_reverse(entities):
    reverse = defaultdict(list)
    for eid, e in entities.items():
        for r in e["refs"]:
            reverse[r].append(eid)
    return reverse


# ---------- FIND COMPONENTS ----------
def find_components(entities):
    return [
        eid for eid, e in entities.items()
        if e["type"] in [
            "MANIFOLD_SOLID_BREP",
            "CLOSED_SHELL",
            "SHELL_BASED_SURFACE_MODEL"
        ]
    ]


# ---------- EXTRACT ALL COORDS ----------
def extract_all_coords(start, entities):
    visited = set()
    queue = deque([start])
    coords_list = []

    while queue:
        eid = queue.popleft()

        if eid in visited:
            continue

        visited.add(eid)

        e = entities.get(eid)
        if not e:
            continue

        if e["type"] == "CARTESIAN_POINT" and e["coords"]:
            coords_list.append(e["coords"])

        for r in e["refs"]:
            queue.append(r)

    return coords_list


# ---------- BUILD TREE ----------
def build_tree(root, entities, reverse):

    visited = set()
    queue = deque()

    root_node = {
        "id": root,
        "type": entities[root]["type"],
        "children": []
    }

    queue.append((root, root_node))

    while queue:
        current_id, current_node = queue.popleft()

        if current_id in visited:
            continue

        visited.add(current_id)

        e = entities.get(current_id)
        if not e:
            continue

        neighbors = e["refs"] + reverse[current_id]

        for n in neighbors:
            if n not in entities:
                continue

            child = {
                "id": n,
                "type": entities[n]["type"],
                "children": []
            }

            coords = extract_all_coords(n, entities)
            if coords:
                child["coords"] = coords[:2]  # limit display

            current_node["children"].append(child)

            if n not in visited:
                queue.append((n, child))

    return root_node


# ---------- PRINT TREE ----------
def print_tree(node, depth=0):

    line = f"{node['id']} [{node['type']}]"

    if "coords" in node:
        line += f" {node['coords']}"

    print("  " * depth + line)

    for c in node.get("children", []):
        print_tree(c, depth + 1)


# ---------- BOUNDING BOX ----------
def compute_bbox(entities):

    points = []

    for e in entities.values():
        if e["type"] == "CARTESIAN_POINT" and e["coords"]:
            points.append(e["coords"])

    if not points:
        print("\n❌ No points found")
        return

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    print("\n📦 BOUNDING BOX\n")
    print("Min:", (min_x, min_y, min_z))
    print("Max:", (max_x, max_y, max_z))

    print("\n📏 Dimensions:")
    print("Width  (X):", max_x - min_x)
    print("Height (Y):", max_y - min_y)
    print("Depth  (Z):", max_z - min_z)


# ---------- MAIN ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python step_final.py file.step")
        return

    file = sys.argv[1]

    print("\n🔍 Parsing STEP...\n")

    entities = parse_step(file)
    reverse = build_reverse(entities)

    print("Total entities:", len(entities))

    components = find_components(entities)
    print("Components found:", len(components))

    print("\n🌳 COMPONENT TREE:\n")

    for comp in components[:2]:
        print(f"\n=== COMPONENT {comp} ===\n")

        tree = build_tree(comp, entities, reverse)
        print_tree(tree)

        print("-" * 60)

    # 🔥 Bounding box
    compute_bbox(entities)


if __name__ == "__main__":
    main()  