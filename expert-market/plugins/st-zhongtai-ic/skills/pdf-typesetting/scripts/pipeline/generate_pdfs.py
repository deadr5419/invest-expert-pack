# -*- coding: utf-8 -*-
"""
generate_pdfs.py — 研报 PDF 生成器主版（reportlab 管线，scripts/pipeline/，2026-08-17 收口）
说明:
  - 本管线为 reportlab 自包含实现，用于「简单版」或需快速出 PDF 的场景。
  - 深度报告（含封面/目录/缩进）首选 xhtml2pdf 管线: scripts/pipeline/md2pdf_pro.py
  - 默认不生成 PDF（2026-08-17 用户拍板）：交付默认 MD+HTML+Word；本脚本仅在显式要求 PDF 时调用。
用法:
  python generate_pdfs.py [--out-dir <目录>] [--deep-md <深度.md>] [--onep-md <一页纸.md>]
                           [--qa-config "名称,股本,单位"] [--no-qa]
  --out-dir 缺省为当前目录；--deep-md/--onep-md 缺省自动探测（*深度研究*.md / 一页纸*.md）
  封面标题/副标题/数据快照从 MD 头部自动解析（parse_cover 同源逻辑）
  生成后自动调用 qa_check.py（主版: scripts/pipeline/qa_check.py）审计，QA_PASS 才允许交付
"""
import os, re, subprocess, sys, argparse

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, ListFlowable, ListItem
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

SIMHEI = r"C:\Windows\Fonts\simhei.ttf"
MSYH = r"C:\Windows\Fonts\msyh.ttc"
pdfmetrics.registerFont(TTFont("SimHei", SIMHEI))
pdfmetrics.registerFont(TTFont("MSYH", MSYH))

HERE = os.path.dirname(os.path.abspath(__file__))

styles = getSampleStyleSheet()
C_RED = colors.HexColor("#C0392B"); C_DARK = colors.HexColor("#0F172A")
C_GRAY = colors.HexColor("#64748B"); C_LINE = colors.HexColor("#CBD5E1")
C_LIGHT = colors.HexColor("#F1F5F9"); C_BLUE = colors.HexColor("#1D4ED8")

TITLE = ParagraphStyle("T", parent=styles["Normal"], fontName="SimHei", fontSize=20, leading=28,
                       textColor=C_DARK, alignment=TA_CENTER, spaceAfter=10)
SUBTITLE = ParagraphStyle("ST", parent=styles["Normal"], fontName="MSYH", fontSize=10.5, leading=16,
                          textColor=C_GRAY, alignment=TA_CENTER, spaceAfter=4)
H1 = ParagraphStyle("H1", parent=styles["Normal"], fontName="SimHei", fontSize=15, leading=21,
                    textColor=C_DARK, spaceBefore=6, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=styles["Normal"], fontName="SimHei", fontSize=12.5, leading=18,
                    textColor=C_BLUE, spaceBefore=10, spaceAfter=5)
H3 = ParagraphStyle("H3", parent=styles["Normal"], fontName="SimHei", fontSize=11, leading=16,
                    textColor=C_DARK, spaceBefore=7, spaceAfter=4)
BODY = ParagraphStyle("B", parent=styles["Normal"], fontName="MSYH", fontSize=9.5, leading=15.5,
                      textColor=colors.HexColor("#1E293B"), alignment=TA_LEFT, spaceAfter=4)
QUOTE = ParagraphStyle("Q", parent=BODY, fontSize=9, leading=14.5, textColor=C_GRAY,
                       leftIndent=10, borderPadding=(4,6,4,6), backColor=C_LIGHT)
CELL = ParagraphStyle("C", parent=BODY, fontSize=8, leading=11.5, alignment=TA_LEFT, spaceAfter=0)
CELLH = ParagraphStyle("CH", parent=BODY, fontName="SimHei", fontSize=8, leading=11.5,
                       textColor=colors.white, alignment=TA_LEFT, spaceAfter=0)
DISCLAIMER = ParagraphStyle("D", parent=BODY, fontSize=8.5, leading=13,
                            textColor=C_RED, borderPadding=(6,8,6,8),
                            borderColor=C_RED, borderWidth=1)
BODY_C = ParagraphStyle("BC", parent=BODY, fontSize=7.6, leading=11, spaceAfter=1.8, alignment=TA_LEFT)
H2_C = ParagraphStyle("H2C", parent=H2, fontSize=10.5, leading=14, spaceBefore=4, spaceAfter=2)
CELL_C = ParagraphStyle("CC", parent=CELL, fontSize=6.8, leading=9.5, spaceAfter=0)
CELLH_C = ParagraphStyle("CHC", parent=CELL_C, fontName="SimHei", textColor=colors.white)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def md_inline(t):
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t


def split_row(line):
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_cover_info(md_lines):
    """封面元信息解析（与 md2pdf_pro/md2html_full 同源逻辑）"""
    info = {"brand": "", "title": "", "subtitle": "", "meta": [], "disclaimer": ""}
    for ln in md_lines[:24]:
        s = ln.strip()
        m = re.match(r"^#\s+(.+)$", s)
        if m and not info["brand"]:
            info["brand"] = m.group(1).strip(); continue
        m = re.match(r"^##\s+(.+)$", s)
        if m and not info["title"]:
            if m.group(1).strip() not in ("封面", "封面页", "封面信息", "封面元信息"):
                info["title"] = m.group(1).strip(); continue
        m = re.match(r"^> (.+)$", s)
        if m:
            t = m.group(1).strip()
            if "免责" in t:
                if not info["disclaimer"]: info["disclaimer"] = t
            elif t.startswith("**数据快照") or t.startswith("**数据来源") or t.startswith("**署名"):
                info["meta"].append(t.replace("**", ""))
            elif not info["subtitle"]:
                info["subtitle"] = t.replace("**", "")
    return info


def parse_blocks(md_text):
    lines = md_text.split("\n"); blocks = []; i = 0; n = len(lines)
    while i < n:
        line = lines[i].rstrip()
        if not line.strip():
            i += 1; continue
        if re.match(r"^-{3,}$", line.strip()):
            blocks.append(("hr", None)); i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            blocks.append(("h", (len(m.group(1)), md_inline(m.group(2))))); i += 1; continue
        if line.lstrip().startswith("|") and i + 1 < n and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i+1].strip()):
            header = split_row(line); i += 2; rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i])); i += 1
            blocks.append(("table", (header, rows))); continue
        if line.startswith(">"):
            q = []
            while i < n and lines[i].strip().startswith(">"):
                q.append(re.sub(r"^>\s?", "", lines[i]).strip()); i += 1
            blocks.append(("quote", "\n".join(q))); continue
        if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+[.、)]\s+", line):
            items = []
            while i < n:
                l2 = lines[i].rstrip()
                mm2 = re.match(r"^\s*[-*]\s+(.*)$", l2)
                mm3 = re.match(r"^\s*\d+[.、)]\s+(.*)$", l2)
                if mm2 or mm3:
                    items.append((mm2.group(1) if mm2 else mm3.group(1)).strip()); i += 1
                elif l2.strip() and not l2.startswith("#") and not l2.startswith("|") and not l2.startswith(">") and not re.match(r"^-{3,}$", l2.strip()):
                    if items:
                        items[-1] += " " + l2.strip(); i += 1
                    else:
                        break
                else:
                    break
            blocks.append(("list", items)); continue
        para = [line.strip()]; i += 1
        while i < n and lines[i].strip() and not lines[i].startswith("#") and not lines[i].lstrip().startswith("|") \
              and not lines[i].startswith(">") and not re.match(r"^-{3,}$", lines[i].strip()) \
              and not re.match(r"^\s*[-*]\s+", lines[i]) and not re.match(r"^\s*\d+[.、)]\s+", lines[i]):
            para.append(lines[i].strip()); i += 1
        blocks.append(("para", " ".join(para)))
    return blocks


def make_table(header, rows, compact=False):
    cell = CELL_C if compact else CELL
    cellh = CELLH_C if compact else CELLH
    avail = (A4[0] - 2.2*cm) if compact else (A4[0] - 3.2*cm)
    def text_width(s):
        s = re.sub(r"<[^>]+>", "", s)
        return sum(1.0 if ord(ch) > 0x2E80 else 0.55 for ch in s)
    ncol = len(header)
    col_w = []
    for j in range(ncol):
        m = max(text_width(md_inline(txt)) for txt in ([header[j]] + [r[j] for r in rows if j < len(r)]))
        col_w.append(max(m, 4))
    is_rating = (not compact) and ncol >= 7 and "评级依据" in header and ("目标价区间" in header or "保守目标价中值" in header)
    if is_rating:
        basis_idx = header.index("评级依据")
        col_w[basis_idx] = min(col_w[basis_idx], 30)
        cellh = ParagraphStyle("CHR", fontName="SimHei", fontSize=7.5, leading=10,
                               textColor=colors.white, alignment=TA_LEFT, spaceAfter=0)
        cell = ParagraphStyle("CR", parent=CELL, fontSize=7.5, leading=10)
    total = sum(col_w)
    widths = [avail * c / total for c in col_w]
    min_w = 1.0*cm if is_rating else (1.2*cm if compact else 1.6*cm)
    max_w = 6.0*cm if is_rating else (5.0*cm if compact else 5.2*cm)
    widths = [min(max(w, min_w), max_w) for w in widths]
    scale = ((avail - 6) if compact else avail) / sum(widths)
    widths = [w * scale for w in widths]
    data = [[Paragraph(md_inline(c), cellh) if c else Paragraph("", cellh) for c in header]]
    for r in rows:
        data.append([Paragraph(md_inline(r[j]), cell) if j < len(r) and r[j] else Paragraph("", cell)
                     for j in range(ncol)])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    if is_rating:
        t.canSplit = False; t.keepWithNext = True
    pad = 2 if compact else 3
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_DARK),
        ("GRID", (0,0), (-1,-1), 0.4, C_LINE),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_LIGHT]),
        ("TOPPADDING", (0,0), (-1,-1), pad), ("BOTTOMPADDING", (0,0), (-1,-1), pad),
        ("LEFTPADDING", (0,0), (-1,-1), 4), ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]))
    return t


def build_flowables(md_text, compact=False):
    body = BODY_C if compact else BODY
    h2s = H2_C if compact else H2
    fl, toc = [], []
    first_h1 = True
    for typ, payload in parse_blocks(md_text):
        if typ == "h":
            lvl, txt = payload
            if lvl == 1:
                if not first_h1:
                    fl.append(PageBreak())
                first_h1 = False
                fl.append(Paragraph(txt, H1))
                fl.append(HRFlowable(width="100%", thickness=1.2, color=C_BLUE, spaceAfter=8))
                toc.append(("1", txt))
            elif lvl == 2:
                fl.append(Paragraph(txt, h2s)); toc.append(("2", txt))
            else:
                fl.append(Paragraph(txt, H3))
        elif typ == "para":
            if payload:
                fl.append(Paragraph(md_inline(payload), body))
        elif typ == "quote":
            fl.append(Paragraph(md_inline(payload), QUOTE))
        elif typ == "list":
            items = [ListItem(Paragraph(md_inline(it), body), leftIndent=12, value="•") for it in payload]
            fl.append(ListFlowable(items, bulletType="bullet", start="•", bulletFontSize=8 if compact else 9,
                                   leftIndent=14, bulletDedent=8, spaceAfter=3 if compact else 4))
        elif typ == "hr":
            fl.append(HRFlowable(width="100%", thickness=0.8, color=C_LINE, spaceBefore=4, spaceAfter=4))
        elif typ == "table":
            header, rows = payload
            fl.append(make_table(header, rows, compact=compact))
    return fl, toc


def footer(canvas, doc):
    canvas.saveState(); canvas.setFont("MSYH", 7.5); canvas.setFillColor(C_GRAY)
    canvas.drawString(1.6*cm, 1.0*cm, "ST众泰投委会 · 研深行 | 仅供研究参考，不构成个人投资建议")
    canvas.drawRightString(A4[0]-1.6*cm, 1.0*cm, f"第 {doc.page} 页")
    canvas.restoreState()


def build_deep_pdf(OUT_DIR, DEEP_MD, DEEP_PDF):
    with open(os.path.join(OUT_DIR, DEEP_MD), encoding="utf-8") as f:
        md = f.read()
    lines = md.split("\n")
    info = parse_cover_info(lines)
    sep = next((i for i, l in enumerate(lines) if re.match(r"^-{3,}\s*$", l.strip())), len(lines))
    body_md = "\n".join(lines[sep+1:])
    fl, toc = build_flowables(body_md)

    title_text = info["title"] or os.path.splitext(DEEP_MD)[0]
    cover = [
        Spacer(1, 2.4*cm),
        Paragraph(info["brand"] or "ST众泰投委会 · 深度研究",
                  ParagraphStyle("s", parent=SUBTITLE, fontSize=12, spaceAfter=24)),
        Paragraph(title_text, ParagraphStyle("t1", parent=TITLE, fontSize=21, spaceAfter=12)),
    ]
    if info["subtitle"]:
        cover.append(Paragraph(info["subtitle"], ParagraphStyle("t3", parent=SUBTITLE, fontSize=12.5,
                                                                textColor=C_BLUE, spaceAfter=26)))
    for meta in info["meta"]:
        cover.append(Paragraph(meta, SUBTITLE))
    cover += [
        Spacer(1, 1.8*cm),
        Paragraph(info["disclaimer"] or "免责声明：本报告仅供研究参考，不构成个人投资建议。",
                  DISCLAIMER),
        PageBreak(),
    ]
    toc_flow = [Paragraph("目录", ParagraphStyle("toct", parent=H1, fontSize=16)),
                HRFlowable(width="100%", thickness=1.2, color=C_BLUE, spaceAfter=10)]
    for lvl, t in toc:
        if lvl == "1":
            toc_flow.append(Paragraph(md_inline(t), ParagraphStyle("toc1", parent=BODY, fontName="SimHei",
                                                                   fontSize=10.5, spaceBefore=6, spaceAfter=2)))
        else:
            toc_flow.append(Paragraph(md_inline("　└ " + t), ParagraphStyle("toc2", parent=BODY, fontSize=9,
                                                                            textColor=C_GRAY, leftIndent=14)))
    toc_flow.append(PageBreak())

    doc = SimpleDocTemplate(os.path.join(OUT_DIR, DEEP_PDF), pagesize=A4,
                            leftMargin=1.6*cm, rightMargin=1.6*cm, topMargin=1.5*cm, bottomMargin=1.5*cm,
                            title=title_text, author="ST众泰投委会 · 研深行")
    doc.build(cover + toc_flow + fl, onFirstPage=footer, onLaterPages=footer)
    print("深度报告PDF OK:", DEEP_PDF)


def build_onepager_pdf(OUT_DIR, ONEP_MD, ONEP_PDF):
    with open(os.path.join(OUT_DIR, ONEP_MD), encoding="utf-8") as f:
        md = f.read()
    fl, _ = build_flowables(md, compact=True)
    def footer_c(canvas, doc):
        canvas.saveState(); canvas.setFont("MSYH", 7)
        canvas.setFillColor(C_GRAY)
        canvas.drawString(1.1*cm, 0.6*cm, "ST众泰投委会 · 研深行 | 仅供研究参考，不构成个人投资建议")
        canvas.drawRightString(A4[0] - 1.4*cm, 0.6*cm, f"第 {doc.page} 页")
        canvas.restoreState()
    doc = SimpleDocTemplate(os.path.join(OUT_DIR, ONEP_PDF), pagesize=A4,
                            leftMargin=1.1*cm, rightMargin=1.1*cm, topMargin=0.8*cm, bottomMargin=0.9*cm,
                            title="一页纸摘要", author="ST众泰投委会 · 研深行")
    doc.build(fl, onFirstPage=footer_c, onLaterPages=footer_c)
    print("一页纸PDF OK:", ONEP_PDF)


def main():
    ap = argparse.ArgumentParser(description="研报 PDF 生成器主版（reportlab 管线，按需调用）")
    ap.add_argument("--out-dir", default=".", help="报告目录（缺省当前目录）")
    ap.add_argument("--deep-md", default=None, help="深度报告 MD（缺省自动探测 *深度研究*.md）")
    ap.add_argument("--onep-md", default=None, help="一页纸 MD（缺省自动探测 一页纸*.md）")
    ap.add_argument("--qa-config", default=None, help='敏感性审计配置: "名称,股本,单位"')
    ap.add_argument("--no-qa", action="store_true", help="跳过 QA 审计")
    args = ap.parse_args()

    OUT_DIR = args.out_dir
    files = sorted(os.listdir(OUT_DIR))
    deep_md = args.deep_md or next((f for f in files if f.endswith(".md") and "深度研究" in f), None)
    onep_md = args.onep_md or next((f for f in files if f.endswith(".md") and "一页纸" in f), None)
    if not deep_md and not onep_md:
        sys.exit(f"QA_FATAL: {OUT_DIR} 下未找到 深度研究*.md / 一页纸*.md")

    if deep_md:
        base = re.sub(r"(深度研究报告|深度研究|深度报告).*", "", deep_md) or os.path.splitext(deep_md)[0]
        deep_pdf = base + "深度研究报告.pdf" if "深度" not in base else os.path.splitext(deep_md)[0] + ".pdf"
        if not deep_pdf.endswith(".pdf"):
            deep_pdf = os.path.splitext(deep_md)[0] + ".pdf"
        build_deep_pdf(OUT_DIR, deep_md, deep_pdf)
    if onep_md:
        onep_pdf = re.sub(r"\.md$", ".pdf", onep_md)
        build_onepager_pdf(OUT_DIR, onep_md, onep_pdf)

    if args.no_qa:
        return
    qa_args = [sys.executable, os.path.join(HERE, "qa_check.py"), OUT_DIR,
               "--md", os.path.join(OUT_DIR, deep_md or "")]
    if args.qa_config:
        qa_args += ["--config", args.qa_config]
    qa = subprocess.run(qa_args, capture_output=True, text=True, timeout=180)
    print(qa.stdout.strip())
    if qa.returncode != 0:
        print(qa.stderr[-800:] if qa.stderr else "")
        print("审计未通过，请修复后重新生成")
        sys.exit(1)


if __name__ == "__main__":
    main()
