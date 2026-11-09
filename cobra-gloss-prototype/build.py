"""Extract the Cobra Mk III blueprint from the Elite source and write a
standalone, glossy-panel renderer to index.html.

Usage: python3 build.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "..", "1-source-files", "main-sources", "elite-source.asm")


def parse_ship(name):
    text = open(SOURCE, encoding="utf-8", errors="replace").read()
    start = text.index("\n.%s\n" % name)
    end = text.index("\n.SHIP_THARGOID\n", start)
    block = text[start:end]

    def rows(keyword):
        pat = r"^ %s\s+([-\d,\s]+?)\s+\\" % keyword
        return [
            [int(v) for v in m.group(1).split(",")]
            for m in re.finditer(pat, block, re.M)
        ]

    return rows("VERTEX"), rows("EDGE"), rows("FACE")


def face_loops(edges, face):
    """Chain the edges that border `face` on exactly one side into closed loops
    (the face outline); edges with the same face on both sides are details."""
    adj = {}
    for v1, v2, f1, f2, _ in edges:
        if face in (f1, f2) and f1 != f2:
            adj.setdefault(v1, []).append(v2)
            adj.setdefault(v2, []).append(v1)
    loops, seen = [], set()
    for s in sorted(adj):
        if s in seen:
            continue
        loop, cur, prev = [s], s, None
        seen.add(s)
        while True:
            nxt = [n for n in adj[cur] if n != prev and n not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            loop.append(cur)
            seen.add(cur)
        if len(loop) >= 3:
            loops.append(loop)
    return loops


def main():
    verts, edges, faces = parse_ship("SHIP_COBRA_MK_3")
    ship = {
        "vertices": [v[:3] for v in verts],
        "faces": [
            {"normal": f[:3], "loops": face_loops(edges, i)}
            for i, f in enumerate(faces)
        ],
        # edges shared by the same face on both sides are detail lines
        "details": [[e[0], e[1], e[2]] for e in edges if e[2] == e[3]],
    }
    template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    html = template.replace("/*SHIP_DATA*/null", json.dumps(ship))
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote index.html:", len(ship["vertices"]), "vertices,",
          sum(1 for f in ship["faces"] if f["loops"]), "filled faces")


if __name__ == "__main__":
    main()
