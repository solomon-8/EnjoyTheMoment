#!/usr/bin/env python3
"""An offline invitation, not a happiness score. Python 3.9+, stdlib only."""

import argparse
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence


ROOT = Path(__file__).resolve().parents[1]
ENERGY = {"low": 0, "medium": 1, "high": 2}
COMPANY = {"solo", "social", "either"}
FIELDS = ("现在做", "想得到", "付出", "换小份", "散场线", "性质")
HEADER = re.compile(r"^### (J\d{3,}) · (.+)$", re.MULTILINE)
META = re.compile(r"^<!-- pick: (.+) -->$", re.MULTILINE)
ANCHOR = re.compile(r'^<a id="(j\d{3,})"></a>$', re.MULTILINE)


@dataclass(frozen=True)
class Card:
    id: str
    title: str
    minutes: int
    budget: int
    company: str
    energy: str
    path: Path
    body: str

    @property
    def reference(self) -> str:
        return "{0}#{1}".format(self.path.as_posix(), self.id.lower())


def load_cards(root: Path = ROOT) -> List[Card]:
    """Read canonical Markdown and fail visibly if the catalog is malformed."""
    cards = []
    seen = set()
    for path in sorted((root / "book").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        headings = list(HEADER.finditer(text))
        metadata = list(META.finditer(text))
        anchors = ANCHOR.findall(text)
        if not (len(headings) == len(metadata) == len(anchors)):
            raise ValueError("{0}: 卡片标题、元数据和锚点数量不一致".format(path.name))
        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            block = text[heading.end():end]
            matches = list(META.finditer(block))
            if len(matches) != 1:
                raise ValueError("{0}: 每张卡须恰有一份元数据".format(path.name))
            data = json.loads(matches[0].group(1))
            required = {"id", "minutes", "budget", "company", "energy"}
            if not isinstance(data, dict) or set(data) != required:
                raise ValueError("{0}: 筛选字段不完整或有未知字段".format(path.name))
            card_id = heading.group(1)
            if data["id"] != card_id or card_id in seen:
                raise ValueError("{0}: 编号重复或标题与元数据不符".format(card_id))
            if anchors[index] != card_id.lower():
                raise ValueError("{0}: 锚点与编号不符".format(card_id))
            # Require the anchor immediately before this heading, not merely somewhere.
            expected_anchor = '<a id="{0}"></a>'.format(card_id.lower())
            if not text[:heading.start()].rstrip().endswith(expected_anchor):
                raise ValueError("{0}: 标题前缺少对应锚点".format(card_id))
            for key in ("minutes", "budget"):
                if type(data[key]) is not int or data[key] < 0:
                    raise ValueError("{0}: {1} 须为非负整数".format(card_id, key))
            if data["minutes"] == 0:
                raise ValueError("{0}: minutes 必须大于零".format(card_id))
            if (
                not isinstance(data["company"], str)
                or not isinstance(data["energy"], str)
                or data["company"] not in COMPANY
                or data["energy"] not in ENERGY
            ):
                raise ValueError("{0}: 无效的同伴或精力标签".format(card_id))
            for field in FIELDS:
                field_pattern = r"^- \*\*" + re.escape(field) + r"\*\*：\S.+$"
                if len(re.findall(field_pattern, block, re.MULTILINE)) != 1:
                    raise ValueError("{0}: 缺少或重复正文栏 {1}".format(card_id, field))
            body = META.sub("", block)
            body = ANCHOR.sub("", body).strip()
            seen.add(card_id)
            cards.append(Card(
                id=card_id, title=heading.group(2), minutes=data["minutes"],
                budget=data["budget"], company=data["company"], energy=data["energy"],
                path=path.relative_to(root), body=body,
            ))
    if not cards:
        raise ValueError("book/ 中没有可读取的行动卡")
    return cards


def filter_cards(
    catalog: Sequence[Card], minutes: int, budget: int,
    company: str = "any", energy: str = "high",
) -> List[Card]:
    """No ranking: match the main activity's stated allowance only."""
    if minutes < 0 or budget < 0:
        raise ValueError("时间和预算不能为负数")
    if company not in COMPANY | {"any"} or energy not in ENERGY:
        raise ValueError("无效的筛选条件")
    return [
        card for card in catalog
        if card.minutes <= minutes
        and card.budget <= budget
        and ENERGY[card.energy] <= ENERGY[energy]
        and (company == "any" or card.company in {company, "either"})
    ]


def nonnegative(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("请输入非负整数") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("请输入非负整数")
    return number


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="从本地菜单挑一件。随机结果不是命令；不喜欢就换。"
    )
    parser.add_argument("--minutes", type=nonnegative, default=30, help="时间上限，默认 30 分钟")
    parser.add_argument("--budget", type=nonnegative, default=0, help="新增人民币预算上限，默认 0 元")
    parser.add_argument("--company", choices=("any", "solo", "social"), default="any",
                        help="solo 不需要同伴；social 适合一起；默认 any")
    parser.add_argument("--energy", choices=tuple(ENERGY), default="high",
                        help="最高参与负担；high 包含所有等级，不是只选高负担")
    parser.add_argument("--list", action="store_true", help="列出全部匹配卡片，不随机抽取")
    parser.add_argument("--seed", type=int, default=None, help="可选固定随机种子，方便复现")
    args = parser.parse_args(argv)
    try:
        cards = filter_cards(load_cards(), args.minutes, args.budget, args.company, args.energy)
    except (OSError, ValueError) as exc:
        parser.exit(2, "目录读取失败：{0}\n".format(exc))
    print("享受当下 · Enjoy The Moment")
    print("预算是主方案的人民币预留上限，不是实时价格；活动并不保证有效。")
    if not cards:
        print("没有符合主方案上限的卡片。不必加钱或加时间；可直接读“换小份”，也可以今天不做。")
        return 0
    if args.list:
        print("匹配 {0} 张（按编号，不是推荐顺序）：".format(len(cards)))
        for card in cards:
            print("{0} · {1} | ≤{2} 分钟 / ≤¥{3} | {4}".format(
                card.id, card.title, card.minutes, card.budget, card.reference))
        return 0
    card = random.Random(args.seed).choice(cards)
    print("\n{0} · {1}\n".format(card.id, card.title))
    print(card.body)
    print("\n原文：{0}".format(card.reference))
    print("不想做就换。今天什么都不额外安排，也可以。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
