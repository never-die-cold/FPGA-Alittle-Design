# EdgeSight 展示海报（A1 雏形）

> 历史海报：保留 2026-10-27 的界面和验证口径。当前网页端、r6 实板对照及验收边界以 [plan.md §3.1](../../plan.md#31-当前状态) 为准。

## 文件

| 文件 | 说明 |
|:---|:---|
| `poster.html` | 海报源文件（A1 竖版，CSS 排版） |
| `EdgeSight-poster-A1.pdf` | 单页 A1 PDF（594×841 mm） |
| `poster-preview.png` | 100 dpi 预览图 |
| `assets/board.jpg` | PYNQ-Z2 板卡实拍（取自 2026-10-27 现场照片） |
| `assets/exe.png` | EXE 界面截图（模拟后端 / PROTOTYPE） |

## 设计

- 开本：A1 竖版 594×841 mm，四边留白约 24–34 mm。
- 配色：暖白纸底、深墨蓝正文、单一青绿强调色；结果区用深色块形成视觉锚点。
- 结构：大标题与一句话定位 → 四项硬指标 → 板卡实拍 → 系统架构 → 板上结果 → 软件与记录 → 验证与证据。
- 字体：正文/标题用 Microsoft YaHei，数字用 Arial（均为本机打印安全字体）。
- 所有数字取自仓库证据；PROVISIONAL、多目标修复未上板、EXE 手动/CSV 未完成均在图中标注，不写成整机验收通过。

## 重新生成

```bat
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-sandbox ^
  --user-data-dir="%CD%\sim\build\chrome-poster" --no-pdf-header-footer --virtual-time-budget=5000 ^
  --print-to-pdf="%CD%\docs\poster\EdgeSight-poster-A1.pdf" ^
  "file:///%CD:\=/%/docs/poster/poster.html"
```

预览图：

```bat
py -c "import pymupdf; d=pymupdf.open(r'docs\poster\EdgeSight-poster-A1.pdf'); d[0].get_pixmap(dpi=100).save(r'docs\poster\poster-preview.png')"
```

## 打印建议

- A1 竖版，哑粉纸 157 g/m² 或覆哑膜；有展板条件时用 5 mm 泡沫板。
- PDF 为矢量文字，图片为板卡实拍与 EXE 截图；板卡图在 A1 尺寸下约 178 dpi，1 m 观看距离足够。若要求 300 dpi 印刷，需要补拍更高分辨率板卡图。
- 若比赛要求 A0，可将 `@page` 与 `.poster` 的 594×841 mm 等比改为 841×1189 mm，或直接按 141% 缩放打印；文字与图片会整体放大。

## 待补 / 可选

- 参赛队伍名称、学校/指导教师信息：当前按技术文档口径未写学校；如海报模板要求，可在页脚补一行。
- 二维码（仓库/演示视频）：当前只放仓库 URL，未生成二维码，避免扫码指向未定地址。
- EXE 实机运行照片：当前用模拟后端截图并标注 PROTOTYPE；拿到实机照片后可替换 `assets/exe.png`。
- 正式模型精度、多目标修复包上板后，更新“板上结果”和“验证与证据”两块。
