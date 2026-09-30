#!/usr/bin/env python3
"""Finite checks for C32's original examples; not a difficulty/pleasure model."""

from collections import Counter, deque
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
ROADS = (("A", "B"), ("A", "C"), ("B", "C"),
         ("A", "D"), ("B", "D"), ("C", "D"))
REMOVED_ROAD = ("A", "D")
REDUCED_ROADS = tuple(edge for edge in ROADS if edge != REMOVED_ROAD)
REDUCED_WALK = ("B", "A", "C", "B", "D", "C")
LAMP_MOVES = ((0, 1), (1, 2), (2, 3), (3, 4))
SPLIT_MOVES = ((0, 1), (2, 3), (3, 4))
LAMP_WALK = ("00000", "11000", "10100", "10010", "10001")
POINTS = {"A": (220, 132), "B": (82, 390),
          "C": (358, 390), "D": (220, 292)}


def edges_checked(edges):
    """Only finite undirected simple graphs, no loops or repeated edges."""
    result = tuple(tuple(sorted(edge)) for edge in edges)
    if any(len(edge) != 2 or edge[0] == edge[1] for edge in result):
        raise ValueError("Each road must join two different vertices")
    if len(set(result)) != len(result):
        raise ValueError("Repeated roads are outside this simple-graph model")
    return result


def degrees(edges):
    return dict(Counter(vertex for edge in edges_checked(edges) for vertex in edge))


def trails(edges):
    """Enumerate edge-once walks from every incident vertex, not just one start."""
    edges = edges_checked(edges)
    if not edges:
        return []
    output = []

    def extend(walk, used):
        if len(used) == len(edges):
            output.append(tuple(walk))
            return
        for index, (left, right) in enumerate(edges):
            if index not in used and walk[-1] in (left, right):
                next_vertex = right if walk[-1] == left else left
                extend(walk + [next_vertex], used | {index})

    for start in sorted(degrees(edges)):
        extend([start], set())
    return output


def connected_on_roads(edges):
    edges = edges_checked(edges)
    vertices = set(degrees(edges))
    if not vertices:
        return False
    seen = {min(vertices)}
    pending = list(seen)
    while pending:
        current = pending.pop()
        for left, right in edges:
            if current in (left, right):
                nxt = right if current == left else left
                if nxt not in seen:
                    seen.add(nxt)
                    pending.append(nxt)
    return seen == vertices


def toggle(state, move):
    """0/1 strings, distinct in-range positions; selected bits change together."""
    if not state or any(bit not in "01" for bit in state):
        raise ValueError("Expected a nonempty binary state")
    if len(move) != 2 or len(set(move)) != 2:
        raise ValueError("A move must select exactly two different lamps")
    if any(not isinstance(i, int) or i < 0 or i >= len(state) for i in move):
        raise ValueError("Lamp index out of range")
    result = list(state)
    for i in move:
        result[i] = "1" if result[i] == "0" else "0"
    return "".join(result)


def reachable(start, moves):
    """Complete reachable-state set for this finite binary model."""
    # Validate even when the search would otherwise have no transitions.
    if not start or any(bit not in "01" for bit in start):
        raise ValueError("Expected a nonempty binary state")
    moves = tuple(moves)
    for move in moves:
        toggle(start, move)
    seen = {start}
    pending = deque([start])
    while pending:
        state = pending.popleft()
        for move in moves:
            nxt = toggle(state, move)
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    return seen


def report():
    full = trails(ROADS)
    reduced = trails(REDUCED_ROADS)
    lamps = reachable("00000", LAMP_MOVES)
    split = reachable("00000", SPLIT_MOVES)
    assert not full
    assert REDUCED_WALK in reduced
    assert "10000" not in lamps
    assert "10001" in lamps
    assert "10100" in lamps and "10100" not in split
    assert all(toggle(a, move) == b
               for a, b, move in zip(LAMP_WALK, LAMP_WALK[1:], LAMP_MOVES))
    return {
        "road_degrees": degrees(ROADS),
        "road_trails": len(full),
        "reduced_degrees": degrees(REDUCED_ROADS),
        "reduced_witness": REDUCED_WALK,
        "lamp_reachable": sorted(lamps),
        "split_reachable": sorted(split),
        "lamp_witness": LAMP_WALK,
        "scope": "Finite examples only; no reader or behavioral validation",
    }


def road_svg():
    """Original drawing, independent of any source's diagrams."""
    result = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="440" height="510" '
        'viewBox="0 0 440 510" role="img" aria-labelledby="title desc">',
        '<title id="title">四个地点，六条路</title>',
        '<desc id="desc">A在上方，B在左下，C在右下，D在三角形内部。'
        '道路AB、AC、BC、AD、BD、CD；没有其他交点或道路。'
        '每条路恰好走一次，地点可重复，不要求回到起点。</desc>',
        '<rect width="440" height="510" rx="16" fill="#fff8ec"/>',
        '<g font-family="PingFang SC, Microsoft YaHei, sans-serif" fill="#24231f">',
        '<text x="24" y="42" font-size="26" font-weight="700">四个地点，六条路</text>',
        '<text x="24" y="78" font-size="20">每条路一次，地点可重复</text>',
    ]
    for left, right in ROADS:
        x1, y1 = POINTS[left]
        x2, y2 = POINTS[right]
        result.append(f'<line data-road="{left}{right}" x1="{x1}" y1="{y1}" '
                      f'x2="{x2}" y2="{y2}" stroke="#686158" stroke-width="5"/>')
    for label, (x, y) in POINTS.items():
        result.extend([
            f'<circle cx="{x}" cy="{y}" r="23" fill="#fff8ec" stroke="#b93a20" stroke-width="3"/>',
            f'<text x="{x}" y="{y+8}" font-size="25" text-anchor="middle" font-weight="700">{label}</text>',
        ])
    result.extend([
        '<text x="24" y="453" font-size="20">任选起点，可以不同地点结束</text>',
        '<text x="24" y="483" font-size="18">原创抽象图 · 线长不表示距离</text>',
        '</g></svg>\n',
    ])
    return "\n".join(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-diagram", action="store_true")
    args = parser.parse_args()
    if args.write_diagram:
        (ROOT / "assets/media/puzzle-roads.svg").write_text(road_svg(), encoding="utf-8")
    print(json.dumps(report(), ensure_ascii=False, indent=2))
