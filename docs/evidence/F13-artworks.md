[← 研究与事实台账](../research.md) · [看画正文](../../book/25-looking-at-art.md)

# F13 作品记录：物件事实、数字图像与观看解释

**来源类型：博物馆作品记录及数字复制图。不是现场观展报告、艺术效果实验或通用审美结论。**

## 核读对象

2026-09-29 读取芝加哥艺术博物馆以下三个作品的官方 API 完整对象记录，具体核对题名、作者、日期、材料、尺寸、馆藏号、描述、署名与图像公有领域字段：

| 作品 | 官方记录 | 日期、材料和不含框尺寸 | 馆藏号 |
| --- | --- | --- | --- |
| 梵高《卧室》 | [作品 28560](https://api.artic.edu/api/v1/artworks/28560) | 1889；布面油画；73.6 × 92.3 厘米 | 1926.417 |
| 修拉《大碗岛的星期天下午》 | [作品 27992](https://api.artic.edu/api/v1/artworks/27992) | 1884–1886，边缘补绘 1888–1889；布面油画；207.5 × 308.1 厘米 | 1926.224 |
| 修拉《〈大碗岛的星期天下午〉油画习作》 | [作品 61616](https://api.artic.edu/api/v1/artworks/61616) | 1884；木板油画；15.5 × 24.3 厘米 | 1981.15 |

中文题名为常见译名或本书工作译名，具体对象以记录 ID 和馆藏号为准。《大碗岛》英文题名中的“1884”不表示作品所有部分都在该年完成。

前两件署名为 Helen Birch Bartlett Memorial Collection，习作为 Gift of Mary and Leigh Block。没有推断它们在核读日都正在展出，也没有审核馆藏流转史中的每条文献。

## 馆方说明支持的有限事实

《卧室》的说明区分三个版本：第一版作于 1888 年，芝加哥所藏第二版为 1889 年 9 月，另有较小的第三版。说明并置画面可能呈现的紧张活力与作者想表达安宁的意图。第 25 章据此讨论意图与反应的区别，没有诊断画家精神状态。

《大碗岛》的说明谈到相邻的点、短划与互补色、创作过程中的习作及人物调整。习作说明特别指出其右侧三人组合在完成画中被重新考虑。本书只采用这些范围，没有由图像猜测人物的真实身份或社会关系。

官方 API 的 `description` 字段标为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，其他数据标为 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)，另附馆方使用条款。本书对上述描述作中文转述、缩写和比较，不是馆方授权译文；原始说明及许可声明可从各 API 记录核查。

## 实际看的是哪些图像

馆方网页和 IIIF 图像请求在本次获取时未成功；API 文本可读。因此实际视觉核读使用以下 Wikimedia Commons 数字图像文件，而不是把无法读取的馆方图像说成已经看过：

- 《卧室》：[1926.417 - The Bedroom Vincent van Gogh 1889](https://commons.wikimedia.org/wiki/File:1926.417_-_The_Bedroom_Vincent_van_Gogh_1889.jpg)。文件记录回指馆方作品 28560。
- 《大碗岛》：[Georges Seurat - A Sunday on La Grande Jatte -- 1884 - Google Art Project](https://commons.wikimedia.org/wiki/File:Georges_Seurat_-_A_Sunday_on_La_Grande_Jatte_--_1884_-_Google_Art_Project.jpg)。文件记录将数字来源标为 Google Arts & Culture；不是本书自行拍摄。
- 习作：[Georges Seurat - Oil Sketch for "La Grande Jatte" - 1981.15 - Art Institute of Chicago](https://commons.wikimedia.org/wiki/File:Georges_Seurat_-_Oil_Sketch_for_%22La_Grande_Jatte%22_-_1981.15_-_Art_Institute_of_Chicago.jpg)。文件来源栏回指馆方作品 61616，题名带有对应馆藏号；以题材、人物配置及馆方作品记录交叉核对，不视为独立鉴定。

三个文件的 Commons 记录均标为 Public domain；三个官方作品记录的 `is_public_domain` 也均为真。正文保存轻量本地图像，生成的单文件阅读页将图片内嵌，不热链或加载外部追踪。三张图均缩放并重新编码为 JPEG；没有裁切、调色或 AI 补绘。文件映射见 [图像署名表](../../assets/art/README.md)。

实际核看了三张全图，并以不同显示大小比较前两张的整体关系；未把所有高分辨率区域逐块审核，也没有对颜料、原作表面或历史原色作检测。屏幕颜色、压缩和复制过程可能改变细节；缩放不是现场移动的等价替代。

## 什么属于本书解释

床与墙面的关系、人物和树干的节奏、画面“重量”、习作与完成画的秩序差异，以及展览顺序怎样影响理解，都是本书的描述或推导。可见细节用来约束解释，不把解释写成作者声明。

正文假设的策展安排与观看建议未做读者实验，不证明先看后读、慢看、比较两图或参观展览能提高幸福感。了解一幅作品也不意味着必须喜欢它。
