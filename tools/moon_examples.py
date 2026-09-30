#!/usr/bin/env python3
"""Original planar four-position rotation model; not a lunar ephemeris."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Mathematical coordinates: x right, y up. Positive quarter turn is anticlockwise.
POSITIONS = ((1, 0), (0, 1), (-1, 0), (0, -1))


def quarter_turn(vector):
    x, y = vector
    return -y, x


def frames(synchronous):
    """Unit positions/directions. No illumination, physical libration or horizon."""
    if not isinstance(synchronous, bool):
        raise TypeError("synchronous must be a boolean")
    result = []
    for i, (x, y) in enumerate(POSITIONS, 1):
        toward_earth = (-x, -y)
        marker = toward_earth if synchronous else (-1, 0)
        dot = sum(a * b for a, b in zip(marker, toward_earth))
        result.append({"number": i, "position": (x, y), "marker": marker,
                       "earth_alignment": dot})
    return result


def svg():
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1480" '
        'viewBox="0 0 720 1480" role="img" aria-labelledby="title desc">',
        '<title id="title">朝向地球，需要绕行也转身</title>',
        '<desc id="desc">原创圆轨道四位置双模型。上图标记朝向依次左下右上，始终朝地；'
        '下图标记一直朝图左，从地球看依次朝地、侧向、背地、另一侧向。不是月相图。</desc>',
        '<rect width="720" height="1480" fill="#fff8ed"/>',
        '<g fill="#302d26" font-family="PingFang SC,Noto Sans CJK SC,sans-serif">',
        '<text x="36" y="58" font-size="35" font-weight="700">朝向地球，需要绕行也转身</text>',
        '<text x="36" y="103" font-size="27">按1 → 2 → 3 → 4 → 1读；图左方向不变</text>',
    ]
    for sync, cy, heading_y, label in (
        (True, 408, 168, "上图 · 同一面始终朝地"),
        (False, 1048, 808, "下图 · 相对图纸不自转"),
    ):
        name = "synchronous" if sync else "no-spin"
        parts.append(f'<text x="36" y="{heading_y}" font-size="32" font-weight="700">{label}</text>')
        parts.append(f'<circle cx="360" cy="{cy}" r="162" fill="none" '
                     'stroke="#9c9387" stroke-width="3" stroke-dasharray="9 9"/>')
        parts.append(f'<circle cx="360" cy="{cy}" r="46" fill="#b8d6d3"/>')
        parts.append(f'<text x="360" y="{cy + 10}" font-size="29" text-anchor="middle">地球</text>')
        label_offsets = ((67, 10), (67, 10), (-67, 10), (0, 75))
        for frame, (lx, ly) in zip(frames(sync), label_offsets):
            px, py = frame["position"]
            mx, my = frame["marker"]
            cx, sy = 360 + px * 162, cy - py * 162
            dx, dy = mx * 28, -my * 28
            parts.append(
                f'<g data-panel="{name}" data-position="{frame["number"]}" '
                f'data-marker-x="{mx}" data-marker-y="{my}">'
                f'<circle cx="{cx}" cy="{sy}" r="41" fill="#e8d9be" stroke="#302d26" stroke-width="2"/>'
                f'<line x1="{cx}" y1="{sy}" x2="{cx+dx}" y2="{sy+dy}" '
                f'stroke="#302d26" stroke-width="4"/>'
                f'<circle cx="{cx+dx}" cy="{sy+dy}" r="8" fill="#302d26"/>'
                f'<text x="{cx+lx}" y="{sy+ly}" font-size="33" font-weight="700" '
                f'text-anchor="middle">{frame["number"]}</text></g>')
        conclusion = ("标记转向：左 → 下 → 右 → 上" if sync
                      else "标记从头到尾朝图左，不跟着圆心转")
        parts.append(f'<text x="36" y="{cy + 296}" font-size="29">{conclusion}</text>')
    parts.extend([
        '<text x="36" y="1400" font-size="27">黑点是同一面上的标记，不是光照或阴影</text>',
        '<text x="36" y="1444" font-size="26">理想圆轨道／均匀运动／俯视；大小距离不按比例</text>',
        '</g></svg>',
    ])
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-svg", action="store_true")
    args = parser.parse_args()
    for mode in (True, False):
        print("synchronous" if mode else "no-spin", frames(mode))
    if args.write_svg:
        (ROOT / "assets/media/moon-rotation.svg").write_text(svg(), encoding="utf-8")


if __name__ == "__main__":
    main()
