import re
import sys

def parse_step(file):
    with open(file, "r", errors="ignore") as f:
        content = f.read()

    pattern = re.compile(r'#(\d+)\s*=\s*([A-Z_]+)\s*\((.*?)\);', re.S)

    entities = {}

    for m in pattern.finditer(content):
        eid = f"#{m.group(1)}"
        etype = m.group(2)
        refs = re.findall(r'#\d+', m.group(3))

        entities[eid] = {
            "type": etype,
            "refs": refs
        }

    return entities


def build_reverse(entities):
    reverse = {}
    for eid, e in entities.items():
        for r in e["refs"]:
            reverse.setdefault(r, []).append(eid)
    return reverse


def build_full_tree(entities):

    reverse = build_reverse(entities)

    def traverse(eid, visited=None, depth=0):
        if visited is None:
            visited = set()

        if eid in visited or depth > 10:
            return None

        visited.add(eid)

        e = entities.get(eid)
        if not e:
            return None

        node = {
            "id": eid,
            "type": e["type"],
            "children": []
        }

        # forward refs
        for r in e["refs"]:
            child = traverse(r, visited.copy(), depth + 1)
            if child:
                node["children"].append(child)

        # reverse refs (IMPORTANT 🔥)
        for r in reverse.get(eid, []):
            child = traverse(r, visited.copy(), depth + 1)
            if child:
                node["children"].append(child)

        return node

    # start from top-level entities
    roots = [eid for eid, e in entities.items() if e["type"] in [
        "MANIFOLD_SOLID_BREP",
        "CLOSED_SHELL",
        "SHELL_BASED_SURFACE_MODEL"
    ]]

    if not roots:
        roots = list(entities.keys())[:5]

    tree = []
    for r in roots:
        t = traverse(r)
        if t:
            tree.append(t)

    return tree


def print_tree(node, depth=0):
    print("  " * depth + f"{node['id']} [{node['type']}]")

    for c in node.get("children", []):
        print_tree(c, depth + 1)


def main():
    file = sys.argv[1]

    print("🔍 Parsing...\n")

    entities = parse_step(file)
    print("Total entities:", len(entities))

    tree = build_full_tree(entities)

    print("\n🌳 FULL TREE:\n")

    for t in tree:
        print_tree(t)
        print("-" * 50)


if __name__ == "__main__":
    main()