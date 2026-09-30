"""Original static geometry, not a flocking simulation or empirical bird data."""

from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POINTS = ("A", "B", "C", "D", "E")


def distances(scale):
    scale = Fraction(scale)
    if scale <= 0:
        raise ValueError("scale must be positive")
    return tuple((name, scale * (i + 1)) for i, name in enumerate(POINTS))


def fixed_radius(scale, radius=Fraction(7, 2)):
    radius = Fraction(radius)
    if radius < 0:
        raise ValueError("radius must not be negative")
    return tuple(name for name, distance in distances(scale) if distance <= radius)


def nearest(scale, count=3):
    if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= len(POINTS):
        raise ValueError("count must be an integer from zero to five")
    return tuple(name for name, _ in distances(scale)[:count])


def svg():
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1060" '
             'viewBox="0 0 720 1060" role="img" aria-labelledby="title desc">',
             '<title id="title">距离变大，近邻名次可以不变</title>',
             '<desc id="desc">原创一维点阵。距离从1至5变为2至10，固定阈值3.5内由ABC变为A；'
             '最近三个仍为ABC。起点O不算邻居，不是鸟群实测或仿真。</desc>',
             '<rect width="720" height="1060" fill="#fff8ed"/>',
             '<g fill="#302d26" font-family="PingFang SC,Noto Sans CJK SC,sans-serif">',
             '<text x="30" y="56" font-size="35" font-weight="700">距离变大，近邻名次可以不变</text>',
             '<text x="30" y="106" font-size="28">O是参考点，不算邻居；所有点在同一侧</text>']
    for panel, scale, y in (("compact", 1, 290), ("expanded", 2, 650)):
        selected = fixed_radius(scale)
        ranked = nearest(scale)
        parts += [f'<g data-panel="{panel}" data-scale="{scale}">',
                  f'<text x="30" y="{y - 103}" font-size="32" font-weight="700">'
                  f'{"上图 · 原间距" if scale == 1 else "下图 · 所有距离乘二"}</text>',
                  f'<line x1="60" y1="{y}" x2="675" y2="{y}" stroke="#9c9387" stroke-width="3"/>',
                  f'<line x1="270" y1="{y - 65}" x2="270" y2="{y + 65}" '
                  'stroke="#316e83" stroke-width="3" stroke-dasharray="8 7"/>',
                  f'<text x="287" y="{y - 49}" font-size="28" fill="#316e83">阈值 3.5</text>',
                  f'<circle cx="60" cy="{y}" r="10" fill="#302d26"/>',
                  f'<text x="60" y="{y + 51}" text-anchor="middle" font-size="29">O</text>']
        for name, distance in distances(scale):
            x = 60 + int(distance * 60)
            parts += [f'<g data-point="{name}" data-distance="{distance}" '
                      f'data-fixed="{str(name in selected).lower()}" '
                      f'data-nearest="{str(name in ranked).lower()}">',
                      f'<circle cx="{x}" cy="{y}" r="12" fill="#b34325"/>',
                      f'<text x="{x}" y="{y - 21}" text-anchor="middle" font-size="30">{name}</text>',
                      f'<text x="{x}" y="{y + 51}" text-anchor="middle" font-size="29">{distance}</text>',
                      '</g>']
        parts += [f'<text x="30" y="{y + 116}" font-size="29">距离 ≤ 3.5：{"、".join(selected)}</text>',
                  f'<text x="30" y="{y + 163}" font-size="29">最近三个：{"、".join(ranked)}</text>', '</g>']
    parts += ['<text x="30" y="899" font-size="28">固定阈值：数量改变；固定名次：距离改变</text>',
              '<text x="30" y="949" font-size="28">长度单位任意；三个不是研究测得的鸟数</text>',
              '<text x="30" y="999" font-size="27">静态几何例子，不含飞行、遮挡或感知极限</text>',
              '</g></svg>\n']
    return "\n".join(parts)


if __name__ == "__main__":
    (ROOT / "assets/media/bird-neighbors.svg").write_text(svg())
