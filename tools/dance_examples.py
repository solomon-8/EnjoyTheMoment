#!/usr/bin/env python3
"""Reproduce C27's finite notation and probabilities, not choreography or efficacy."""
import argparse
from fractions import Fraction
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATERIAL = ("P", "Q", "R")
STARTS = {"unison": (0, 0, 0), "canon": (0, 1, 2)}


def timeline(starts, width=5):
    if any(start < 0 or start + len(MATERIAL) > width for start in starts):
        raise ValueError("Sequence must fit the observation window")
    return tuple(tuple(MATERIAL[t - start] if start <= t < start + 3 else "."
                       for t in range(width)) for start in starts)


def allowed_orders():
    return tuple(p for p in permutations(MATERIAL) if p.index("P") < p.index("Q"))


def distributions():
    orders = allowed_orders()
    uniform_order = {p: Fraction(1, len(orders)) for p in orders}
    first_letters = sorted({p[0] for p in orders})
    uniform_first = {
        p: Fraction(1, len(first_letters)) /
        sum(q[0] == p[0] for q in orders) for p in orders
    }
    return uniform_order, uniform_first


def response_sequences(first):
    """Two stipulated rules, not a classifier for real dancers or intentions."""
    if first not in ("P", "R"):
        raise ValueError("This two-step model only permits P or R first")
    return {
        "fixed": (first, "Q"),
        "conditional": (first, {"P": "Q", "R": "S"}[first]),
    }


def svg():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1080" '
        'viewBox="0 0 720 1080" role="img" aria-labelledby="title desc">',
        '<title id="title">同一材料的齐做与依次进入</title>',
        '<desc id="desc">横向五格时间，纵向甲乙丙。齐做同时在第1至3格做PQR；'
        '依次进入分别从第1、2、3格开始，第3格从上到下为R、Q、P。'
        '圆点只表示不执行这段材料，不是静止指令。</desc>',
        '<rect width="720" height="1080" fill="#fff8ed"/>',
        '<g font-family="PingFang SC, Noto Sans CJK SC, sans-serif" fill="#27251f">',
        '<text x="360" y="60" text-anchor="middle" font-size="33" font-weight="700">'
        '动作材料没换，时间关系换了</text>',
        '<text x="360" y="104" text-anchor="middle" font-size="29">'
        '每人做一次 P → Q → R；每项占一格</text>',
    ]
    for name, top, title in (("unison", 160, "齐做：一起开始，一起结束"),
                             ("canon", 590, "依次进入：同一刻处在不同阶段")):
        parts.append(f'<text x="40" y="{top}" font-size="30" font-weight="700">{title}</text>')
        for col in range(5):
            parts.append(f'<text x="{142 + 112 * col}" y="{top + 49}" text-anchor="middle" '
                         f'font-size="29">{col + 1}</text>')
        for row, cells in enumerate(timeline(STARTS[name])):
            y = top + 69 + row * 88
            parts.append(f'<text x="42" y="{y + 55}" font-size="31">{"甲乙丙"[row]}</text>')
            for col, value in enumerate(cells):
                x = 87 + col * 112
                fill = "#f1e5d4" if value != "." else "#fff8ed"
                parts.append(f'<g data-panel="{name}" data-row="{row}" data-slot="{col + 1}" '
                             f'data-value="{value}"><rect x="{x}" y="{y}" width="110" height="86" '
                             f'fill="{fill}" stroke="#a39580" stroke-width="1.5"/>'
                             f'<text x="{x + 55}" y="{y + 56}" text-anchor="middle" '
                             f'font-size="38" font-weight="700">{"·" if value == "." else value}</text></g>')
        footer = ("第3格：三人都是 R；第4、5格均为空" if name == "unison"
                  else "第3格：甲是 R，乙是 Q，丙是 P")
        parts.append(f'<text x="40" y="{top + 377}" font-size="27">{footer}</text>')
    parts.extend([
        '<text x="40" y="1022" font-size="27">· 仅表示未做这段材料，不规定姿势</text>',
        '<text x="40" y="1060" font-size="25">原创关系图；不是动作教程，也不是作品舞谱</text>',
        '</g></svg>',
    ])
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-svg", action="store_true",
                        help="Write the original diagram; PNG rendering is a separate step.")
    args = parser.parse_args()
    for name, starts in STARTS.items():
        print(name, timeline(starts))
    for distribution in distributions():
        print({"".join(k): str(v) for k, v in distribution.items()})
    if args.write_svg:
        (ROOT / "assets/media/dance-time-grid.svg").write_text(svg(), encoding="utf-8")


if __name__ == "__main__":
    main()
