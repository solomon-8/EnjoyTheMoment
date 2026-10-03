[← 研究与来源](../research.md) · [共同叙事章节](../../book/34-shared-stories.md)

# F33 特征、麻烦与共同叙事

- **核读日期**：2026-10-03（本地时区 UTC+08:00）。
- **来源类型**：`official_game_srd`。
- **性质**：*Fate Condensed* 官方开放规则文档；不是游戏效果试验、访谈或真人游玩观察。
- **用途**：第 34 章的人物特征、创造优势、麻烦提议、世界共识、主持职责及现实边界讨论。

## 1. 来源不是只有网页

先取得 Fate SRD 网站的 [Getting Started](https://fate-srd.com/fate-condensed/getting-started)、[Aspects and Fate Points](https://fate-srd.com/fate-condensed/aspects-and-fate-points)、[Taking Action, Rolling the Dice](https://fate-srd.com/fate-condensed/taking-action-rolling-dice) 与 [Being the Game Master](https://fate-srd.com/fate-condensed/being-game-master) 网页。

随后读取 [Evil Hat 产品页](https://evilhat.com/product/fate-condensed/)指向的[官方许可入口](https://fate-srd.com/official-licensing-fate)。许可入口明确说明：网页为便于展示作过调整，应使用下载的官方 SRD 文件作为改编底本。

因此本书实际取得该页链接的 [CC-BY SRDs ZIP](https://fate-srd.com/downloads/CC-BY-SRDs.zip)，读取其中：

`CC-BY SRDs/Fate-Condensed-SRD-CC-BY.html`

核读范围为版权与署名、Define Your Setting、Aspects、Aspects Are Always True、Taking Action, Rolling the Dice 的开头、Invoking Aspects、Outcomes 的四类门槛、Create an Advantage 的全部结果分支、Boosts、Compels 与其子节、Being the Game Master 的职责及 Safety Tools。**没有核读整个 ZIP 的其他游戏文件，也没有完成该文档所有可选规则和商业书的逐项比对。**

当前核读文件为159,103字节，SHA-256：`a0f556ce2415fe4dc88ff71e56755bb92e113a52f8041bda69b759b63782544e`。这是下载文件的身份记录，不代表官方版本号、最后修订时间或规则效果认证。

文件头标明 *Fate Condensed ©2020 Evil Hat Productions, LLC.*，正文仍有 `page XX` 占位页码；不能用它提供不存在的精确书页引用。它是本次取得的官方 SRD，不虚构小版本号或认为 2020 年版权就是文件最后更新时间。

## 2. 采用内容和不得简化掉的条件

### 世界共识与特征

规则要求设定与人物概念符合共同建立的世界。aspect 是描述人、物、局面等重要特点的短语，其在故事中的真实性不以是否花命运点为前提；但不能随意写一个特征就取消既有规则和设定。

本章把 aspect 译称“特征”，是说明用语，未核验或冒充任何官方中文译本。修钟匠的“从不把委托物留在身后”为本书自拟，不是来源例子。

### 调用与检定

四颗 Fate 骰结果相加，再加技能等修正；调用相关特征通常花命运点或用免费调用，可选择加 2 或重掷全部四骰等效果。特征本身的成立与机械加成不同，不能因“特征总是真的”就擅自取消调用成本。

正文 `+、0、−、+` 的和为 +1，加技能 2 得 3，再加 2 得 5；难度 4 与这一组骰面均为本书原创算例，不是来源实况。没有因此承诺每次调用都成功，也不把两套系统的骰子读取方式混合。

<a id="f33-create-advantage"></a>

### 创造优势：创造新特征、发现已有特征、利用已知特征

Create an Advantage 把改变情境、发现信息与利用已知条件纳入同一行动类别，但要求先说明针对新特征还是已有特征。行动须符合故事条件；作用于对手时，对手可防御，其他情形通常对固定难度，也可能由主持者裁定存在主动对抗。不能把想要的短语写下来，就当它已经成立。

Outcomes 定义门槛：最终行动结果低于难度或对抗结果为失败，相同为平局，高出1或2为普通成功，高出至少3为 succeed with style。创造优势的分支如下；两张表是同一份规则的转述，不是独立实验：

| 针对新特征 | 源规则的结果 |
| --- | --- |
| 失败 | 不建立特征；或付代价建立，但敌对方得到免费调用，最终特征可能需改写得对敌对方有利 |
| 平局 | 不建立新特征，得到一个 boost |
| 普通成功 | 建立情境特征，得到一次免费调用 |
| 高出至少3的成功 | 建立情境特征，得到两次免费调用 |

| 针对已有特征 | 当前已知 | 当前未知 |
| --- | --- | --- |
| 失败 | 敌对方得到一次免费调用 | 敌对方可选择揭示该特征，并得到一次免费调用 |
| 平局 | 得到一次免费调用 | 得到一个 boost，该特征仍未知 |
| 普通成功 | 得到一次免费调用 | 揭示该特征，并得到一次免费调用 |
| 高出至少3的成功 | 得到两次免费调用 | 揭示该特征，并得到两次免费调用 |

Boosts 段把 boost 说明为特别短暂或轻微情境的一类特征：只能免费调用一次，用后消失；不能用命运点再次调用，也不能 compel。未使用时会在相应优势不存在后消失，不保留到场景结束之后；有叙事理由时可以转给同伴。不能把获得 boost 当作已经揭示原来未知的特征。

免费调用不花命运点，也可以交给同伴使用；但源规则并未因此取消叙事相关性。Aspects Are Always True 段要求已经成立的特征得到承认，直到事情改变而使它不再成立。用掉一次免费调用不自动抹去特征；反过来，特征仍在不等于机械加成可以无限免费领取。

### 钟箱支线与“临时改真相”的原创边界

正文的暗记、厚布、震动声与钟不愿登船的理由，都是本书原创虚构。暗记先设为实际存在且角色尚未知，厚布先设为在这个虚构世界中有相应作用；两条支线分别开始，不构成真实游玩记录、器材说明或对所有故事的默认事实。

本书用它们比较发现与改变，不把“发现新信息”扩张成可以任意改写已确定的答案。既定谜底、共同确认的事实与留待共同创作的空白三分，是本书对约定的分析，不是 SRD 中同名的分类，也不是禁止主持者即兴的官方纪律。现实边界需要删改情节时，不以虚构一致性阻拦。

### Compel 的提议、资源与撤回

原文说明，相关特征可以引出麻烦提议；接受时获得命运点，正常拒绝需花自己的命运点，零点时不能这样拒绝。规则也明确，不合适的提议可经大家认可撤回，不让被提议者承担费用。

不能只摘“可以拒绝”而删去资源条件，也不能只摘“零点不能拒绝”而删去不合适提议的撤回，以及另列的现实安全边界。

麻烦要形成新的行动或局面，不仅是否定选项。事件型与决定型的来源不同，都需要实际情节变化。本文没有复制来源人物或长段范例，没有把“任意制造冲突”包装成系统要求。

### 主持职责与现实边界

主持者裁定规则、安排场景与非玩家角色；同时应回应玩家选择、分配发挥机会。安全工具段落要求关注或异议优先处理，并简介 X-Card 与 Script Change。

本章只采用“现实顾虑必须被处理”和“可删改、暂停叙述”的框架，不声称完整核验两个工具的原始说明、版本或有效性。没有观看演示，也没有把列举工具当作安全保证。本文进一步主张不适请求不由游戏内资源结算、不要求披露个人经历，这是本书规范判断，不是上述来源测得的效果。

## 3. 网页与官方文件的差异

下载文件与网页不是两项相互独立的依据，而是同一规则的不同呈现。

本次直接观察到：网页页脚的 *Fate Condensed* 署名列出 PK Sullivan、Lara Turner、Fred Hicks、Richard Bellingham、Robert Hanz、Sophie Lagacé；下载文件要求的署名还包括 **Leonard Balsera 和 Ryan Macklin**。本书按官方文件保留后者完整名单，不凭网页页脚缩减作者。

网页补充的跳转和澄清块不自动等同原始 SRD 内容；本章关键规则回到下载文件核读。未据此声称网页整体错误或已做全量校勘。

旧 `www.faterpg.com/licensing/` 地址在本次直接请求中出现证书主机名不匹配；未关闭证书验证，改沿产品页可用的官方许可入口取得文档。候选 credits 页面返回 404，没有将未取得的页面当作作者核验来源。

## 4. 许可与署名

该官方 SRD 文件按 [CC BY 3.0 Unported](https://creativecommons.org/licenses/by/3.0/) 使用，下面按文件头要求保留署名。Fate 商标、官方标识、字体及其他作品不因此变成本项目素材；本书没有使用这些标识或字体，也不宣称官方合作或审核。

中文规则转述及原创例子为本书改写，不是官方中文译本。原创价值论述与第三方规则内容的来源和许可分开，见仓库许可文件及[来源与致谢](../sources.md)。

This work is based on Fate Condensed (found at http://www.faterpg.com/), a product of Evil Hat Productions, LLC, developed, authored, and edited by PK Sullivan, Lara Turner, Leonard Balsera, Fred Hicks, Richard Bellingham, Robert Hanz, Ryan Macklin, and Sophie Lagacé, and licensed for our use under the Creative Commons Attribution 3.0 Unported license (http://creativecommons.org/licenses/by/3.0/).

[返回第 34 章](../../book/34-shared-stories.md)
