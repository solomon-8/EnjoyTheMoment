[← 研究与来源](../research.md) · [共同叙事章节](../../book/34-shared-stories.md)

# F32 行动、骰子与后果

- **核读日期**：2026-09-30（本地时区 UTC+08:00）。
- **来源类型**：`game_rules_and_original_probability`。
- **性质**：游戏设计者开放发布的规则说明，加本书独立计算。不是玩家行为研究，也不是心理效果研究。
- **用途**：第 34 章区分行动目标、处境、效果、骰池与后果。只解释指定机制，不构成完整入门规则。
- **取得与核读**：直接取得下列网站页面正文，核读所列部分；没有购买、核读完整商业书、参加游戏或观看实况。

## 1. 规则来源及采用范围

来源为 *Blades in the Dark* 官方网站的 System Reference Document（SRD）。作者 John Harper，产品方 One Seven Design。下列页面没有被本书赋予虚构的独立版本号；以本次取得的内容为准，不称已经核对所有印刷版和后续勘误。

| 页面 | 实际采用部分 |
| --- | --- |
| [The Core System](https://bladesinthedark.com/core-system) | Judgment calls、Rolling the Dice；通常取最高、零或负骰取两颗最低、不能大成功 |
| [Action Roll](https://bladesinthedark.com/action-roll) | 开头的检定条件、目标和行动、处境与效果、掷骰裁定、三种处境结果表 |
| [Setting Position & Effect](https://bladesinthedark.com/setting-position-effect) | 处境与效果作为分开变量，受到行动和局面影响 |
| [Consequences & Harm](https://bladesinthedark.com/consequences-harm) | 效果降低、麻烦、失去机会、更坏处境；麻烦不能否定成功 |
| [Resistance & Armor](https://bladesinthedark.com/resistance-armor) | 抵抗自动有效，减轻还是避免由主持者依局面决定，检定决定压力代价 |

中文的“处境”“效果”“完全成功”“大成功”等是本文说明用语，附英文时便于回到原文，不声称代表官方中文版本。

**关键限制**：

- 处境决定后果严重性等问题，不直接改成成功概率的统一数值；效果也不是骰子数量。
- 4—5 的具体处理随处境而异。controlled 的分支允许撤回、改用不同做法；其他后果还可能降低效果。正文船长例子只采用 risky/standard 下“达成并加入麻烦”这一种解释。
- 1—3 不宜一概译成“什么都没发生”；原文允许依据局面仍产生某些效果，具体由主持者裁定。
- 抵抗不是“骰子成功了才有效”，也不保证所有后果都被完全取消。本文没有教授完整压力、创伤、护甲或恢复系统，不把局部规则当完整玩法。
- 并非所有行动都需要检定；没有危险或麻烦、预期直接能完成的事，不应为了每一步都有随机性而擅自加规则。

## 2. 本书计算与验证

概率表假设标准六面骰公平且相互独立，仅检查普通骰池中最高结果的分类，不是现场观测，也不涉及玩家水平。

| 最高结果 | 一颗骰：6 种有序结果 | 两颗骰：36 种有序结果 |
| --- | --- | --- |
| 1—3 | 3 | 9 |
| 4—5 | 2 | 16 |
| 至少一颗 6，包含大成功 | 1 | 11 |

两颗骰中，恰好一颗 6 有 10 种，两颗都为 6 有 1 种。最后一行已含大成功，不能再把 1/36 加到 11/36 上。百分数保留两位时会有四舍五入；分数为精确值。

正文的计算由枚举全部结果核对，并另检查公式：

- 最高值不超过 3：3²/6²。
- 最高值为 4 或 5：(5²−3²)/6²。
- 至少一个 6：(6²−5²)/6²。

这些关系说明增加骰子时结果类别如何重新分配，不证明“快乐增加多少”。零或负骰的特殊机制取最低值，不能使用上述两骰概率。

## 3. 原创解释与边界

会说谎的钟、修钟匠、船长和码头均为本书原创虚构，不是原作角色、设定或实况故事。处境/效果对照为简化说明，不是官方裁定；“拿到登船许可但要负责看钟”的后果只是可讨论的一种叙事选择。

规则检定与现实停止权的区别是本书的规范判断，不把规则中的压力、后果或资源解释为真人必须承受的条件。不据这些材料声称角色扮演能改善社交、心理健康、认知能力或主观幸福。

## 4. 许可与署名

已读取[官方许可页](https://bladesinthedark.com/licensing)。其 SRD 采用 [CC BY 3.0 Unported](https://creativecommons.org/licenses/by/3.0/)，不等于整本商业规则书、世界设定、插图或商标也按同样条件开放。本文只转述规则，不复制原作设定或使用官方及 Forged in the Dark 标识。

中文解释和场景是本书改写，非官方译本；本项目与 One Seven Design 无合作或背书关系。以下采用许可页要求的署名文本，亦随第 34 章和仓库许可文件保留：

This work is based on Blades in the Dark (found at http://www.bladesinthedark.com/), product of One Seven Design, developed and authored by John Harper, and licensed for our use under the Creative Commons Attribution 3.0 Unported license (http://creativecommons.org/licenses/by/3.0/).

[返回第 34 章](../../book/34-shared-stories.md)
