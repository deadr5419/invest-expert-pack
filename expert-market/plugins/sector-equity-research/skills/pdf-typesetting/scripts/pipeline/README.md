# scripts/pipeline/ — 投委会研报流水线脚本主库

> 2026-08-17 收口。**本目录是研报产出流水线脚本的唯一主版本**；此前散落在各报告交付目录（如 `deliverables/创新药前十成份股研究/`）的同名脚本均为历史副本，仅供存档与对比，**不再作为基准**，勿在新任务中引用。

## 管线总览

```
研报采集(fxbaogao) → 投委会(Phase0-3) → 研深行产出 MD → 排版交付
排版交付链（本目录）:
  MD ─┬─ md2html_full.py  → 单标的全文 HTML（默认）
     ├─ md2docx.py       → Word .docx（默认）
     ├─ generate_html_report.py → 组合报告交互版 HTML（组合任务用）
     └─ md2pdf_pro.py    → PDF（xhtml2pdf，**按需**，见下）
     + qa_check.py       → PDF/内容审计门禁（generate_pdfs.py 生成后自动调用）
```

## 默认不生成 PDF（2026-08-17 用户拍板）

- **默认交付 = MD + HTML + Word**；**PDF 仅在用户显式要求时生成**。
- 深度报告 PDF（封面/目录/缩进齐全）→ `md2pdf_pro.py`（xhtml2pdf 管线，STSong-Light，内置 sanitize_gbk）。
- 简单版/快速 PDF → `generate_pdfs.py`（reportlab 管线）。
- 任何 PDF 生成后必须过 `qa_check.py` 门禁（QA_PASS 才允许交付）。

## 脚本清单与调用规范

| 脚本 | 管线 | 用法 | 依赖 |
|---|---|---|---|
| `md2html_full.py` | MD→全文 HTML | `python md2html_full.py <报告.md> [输出.html] [--compact]` | markdown |
| `md2docx.py` | MD→Word | `python md2docx.py <报告.md> <输出.docx>` | python-docx |
| `md2pdf_pro.py` | MD→PDF(深度) | `python md2pdf_pro.py <报告.md> [--compact]`（可加输出路径参数） | markdown+xhtml2pdf |
| `generate_pdfs.py` | MD→PDF(reportlab) | `python generate_pdfs.py --out-dir <目录> [--deep-md] [--onep-md] [--qa-config "名称,股本,单位"] [--no-qa]` | reportlab |
| `generate_html_report.py` | MD→组合报告交互HTML | `python generate_html_report.py <组合报告.md> [输出.html]` | 无（纯 stdlib） |

> ⚠️ `generate_html_report.py` 的提取正则绑定组合报告模板列头（"覆盖倍数/评级依据"等，report-skeleton 曾用 11 列版）。2026-08-15 两锚分列后列头已变，**该脚本在现模板下会因表头不匹配报错（原版同样），待下一个组合报告任务时按最新模板适配**；单标的全文 HTML 请用 `md2html_full.py`。
| `qa_check.py` | PDF 审计门禁 | `python qa_check.py <报告目录> [--md <深度.md>] [--config "名称,股本,单位"]` | pymupdf(fitz) |

Python 环境：managed venv `C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe`。
注意：venv 未装 xhtml2pdf——跑 `md2pdf_pro.py` 需先 `pip install xhtml2pdf`（或使用含该包的环境）。

## 解析同源纪律

`parse_cover / split_body` 逻辑在 `md2pdf_pro.py`、`md2html_full.py`、`generate_pdfs.py`（parse_cover_info）三处同源。**改动一处必须三处同步**（generate_pdfs.py 的 parse_cover_info 已独立内联，注意比对）。

## QA 门禁（pdf-typesetting 技能落地）

- `qa_check.py` 覆盖：页数 / 正文溢出 / 空白页 / 乱码方框(U+25A1/U+FFFD) / 文本越界 / 一页纸表格竖线 / 敏感性表可复算。
- 敏感性审计需 `--config "名称,股本,单位"`（单位: CNY/HKD/USD），与 `comps-valuation/scripts/recalc_sensitivity.py` 同口径。
- 历史上复制演化的 qa_check 曾残留创新药 CONFIG（西部矿业版即中招），主版已参数化根治。

## 历史副本（保留不删，仅供存档）

| 脚本 | 历史位置 | 说明 |
|---|---|---|
| generate_pdfs.py | 创新药前五/前十、电解铝、腾讯0812/0814、阿里 | 各版本主题参数硬编码、样式微演化 |
| qa_check.py | 创新药前十、电解铝、腾讯0812/0814、阿里、西部矿业 | 敏感性 CONFIG 各自残留（西部矿业版含创新药 CONFIG bug） |
| generate_html_report.py | 创新药前十、腾讯0814 | 组合报告交互版演化 |

## 变更记录

- 2026-08-17：收口建立本目录；qa_check/generate_pdfs 参数化主版；默认不生成 PDF。
