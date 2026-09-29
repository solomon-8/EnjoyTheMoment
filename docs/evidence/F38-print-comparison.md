[← 研究与事实台账](../research.md) · [收藏正文](../../book/26-collecting.md)

# F38 两件同题版画：记录、图像与比较的边界

- **核读日期**：2026-09-30（UTC+08:00）。
- **来源类型**：`artwork_record_and_image`，馆方对象记录、官方图像及另行说明的工艺教学。
- **作品**：Rembrandt（伦勃朗），*Christ Crucified between the Two Thieves: The Three Crosses*，中文简称《三个十字架》。
- **用途**：比较具体对象和图面，解释作品、材料、实物与数字文件不能混成一层；不是鉴定、定价或收藏效果研究。

## 1. 两件对象的直接记录

读取大都会艺术博物馆两份完整对象 API JSON，均 HTTP 200：

| 本章标签与记录 | 馆方字段 |
| --- | --- |
| A · [对象 354631](https://collectionapi.metmuseum.org/public/collection/v1/objects/354631) | 馆藏号 41.1.31；日期 1653；`Drypoint printed on vellum`；印版约 38.1 × 43.8 厘米，承载物约 38.4 × 44.3 厘米 |
| B · [对象 359757](https://collectionapi.metmuseum.org/public/collection/v1/objects/359757) | 馆藏号 41.1.33；日期 `ca. 1660`；`Drypoint`；承载物约 38.2 × 44.4 厘米 |

两件作者字段均为 Rembrandt (Rembrandt van Rijn)，署名均为 `Gift of Felix M. Warburg and his family, 1941`。中文字段是本书转述与取舍，不是馆方授权译文。

正文使用 `dimensions` 展示字段中的厘米数。A 的 `measurements` 还提供更多小数位，不能据此说馆方实物测量精度更高。A 也列装裱尺寸，正文未拿它与 B 的承载物尺寸比较。B 的日期显示“约 1660”，后台起止年份另为 1655 与 1665，本书保留“约”，不把中间值写成精确制作年份。

API 记录没有给出正文可直接采用的版态编号或完整改版过程。相关馆方普通网页与历史文章候选本次返回 429，未读取正文；因此没有凭记忆把这两件对应到第几版态，也没有声称从图像恢复了同一印版的全部修改步骤。两个 A、B 标签只为本章比较，不是历史编号。

作为候选另读取芝加哥艺术博物馆[对象 80077](https://api.artic.edu/api/v1/artworks/80077)、[对象 75508](https://api.artic.edu/api/v1/artworks/75508)；其 `description`、`publication_history`、`provenance_text` 均为空，不能补足上述缺口。正文不使用这两件的图像、尺寸或其他材料，也不把重复题名当同一实物的证据。搜索结果条数不代表作品的完整版本数量。

## 2. 实际视觉核读的图像

分别下载上述 API `primaryImageSmall` 指向的官方 JPEG：

- A：[DT11821.jpg](https://images.metmuseum.org/CRDImages/dp/web-large/DT11821.jpg)，599 × 522 像素，140,671 字节。
- B：[DP815615.jpg](https://images.metmuseum.org/CRDImages/dp/web-large/DP815615.jpg)，599 × 519 像素，125,843 字节。

两份图像均 HTTP 200，已实际打开并核看全图。正文保存原下载字节，不重新编码、不裁切、不调色、不补绘；浏览器可以按容器缩放显示。文件映射与署名另见[图像表](../../assets/art/README.md)。

本书直接观察中央十字架、前景人物与空地、贯穿线条及右侧暗区。关于目光路径、被包围感、交错与可辨认的文字是本书解释，不是原作者心理、创作动机、观众眼动或幸福效果研究。没有核查每一处微小线条，也没有把数字颜色、画面亮度或缺边转成原作品相判断。

## 3. 公开使用状态与不可混用的许可

两个对象的 `isPublicDomain` 均为真。[馆方 API 文档](https://metmuseum.github.io/)说明此字段指作品处于公有领域，API 提供开放数据与相应公有领域图像；`primaryImageSmall` 为较低分辨率主图。

另读馆方 [Open Access 仓库 README](https://github.com/metmuseum/openaccess/blob/master/README.md)，其中的 CC0 数据集声明不包含图像本身。因此本书不以 CSV 的许可代替图像依据，而同时保留具体对象的公有领域字段、图像来自该对象 API 的链路和原始署名。没有将第三方作品改称本项目 MIT 原创，馆方未为本项目背书。

馆方资料会更新；对象 ID 和馆藏号用于定位本次所读对象，更新时间不是制作日期或收购日期。本书不是馆方所有藏品数据的完整镜像。

## 4. 干刻教学与已读 F14 的关系

本次重读 V&A [What is print?](https://www.vam.ac.uk/articles/what-is-print) 的开头定义、Etching 与 Drypoint 段落，页面仍显示 2024-04-17 更新。F14 已使用同一页面作一般版画说明；这里追加核对的工艺段落不算第二个独立机构来源。

干刻段解释线直接进入金属，毛刺留在边缘并能带墨，产生柔软、模糊的线感。本书只用这层概念帮助观看，不提供金属刻制、酸液、溶剂或印刷操作步骤。

页面关于另一件伦勃朗作品的改版与后来印制，不能未经核验转到本章的两件《三个十字架》上；本书没有作这种转移。也没有把技术定义当作识别每一处图像痕迹的可靠鉴定法，未观看页面嵌入视频或转载 V&A 配图。

返回[收藏正文](../../book/26-collecting.md)；版数与留样另见 [F14](F14-editions.md)。
