# -*- coding: utf-8 -*-
"""
md2pdf_pro.py — 专业中文研报 PDF 生成器（xhtml2pdf 管线，reportlab 内核）
借鉴 doc-typeset 研报模板规范：封面 / 首行缩进 2em / 段距行高 / 评级总览表 / 页脚页码
用法: python md2pdf_pro.py <input.md> <output.pdf>
依赖: markdown + xhtml2pdf（已装）
"""
import os, re, sys
import markdown

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


def _patch_xhtml2pdf_cjk():
    """xhtml2pdf CJK word-wrap 混型修复：CJK 断行下 words 为 str，
    其内部 b' '.join(words) 抛 TypeError(bytes/str 混拼)——统一转 str 拼接。
    覆盖 _left/_center/_right/_justify 四条行绘制路径（X 变体仅在特定情形启用，暂不处理）。"""
    import xhtml2pdf.reportlab_paragraph as _rp
    _join = lambda ws: " ".join(w.decode("utf-8", "ignore") if isinstance(w, bytes) else w for w in ws)

    def _left(tx, offset, _e, words, _l=0):
        _rp.setXPos(tx, offset); tx._textOut(_join(words), 1); _rp.setXPos(tx, -offset); return offset

    def _center(tx, offset, e, words, _l=0):
        m = offset + 0.5 * e; _rp.setXPos(tx, m); tx._textOut(_join(words), 1); _rp.setXPos(tx, -m); return m

    def _right(tx, offset, e, words, _l=0):
        m = offset + e; _rp.setXPos(tx, m); tx._textOut(_join(words), 1); _rp.setXPos(tx, -m); return m

    def _justify(tx, offset, e, words, last=0):
        _rp.setXPos(tx, offset)
        text = _join(words)
        if last:
            tx._textOut(text, 1)
        else:
            n = len(words) - 1
            if n:
                tx.setWordSpace(e / float(n)); tx._textOut(text, 1); tx.setWordSpace(0)
            else:
                tx._textOut(text, 1)
        _rp.setXPos(tx, -offset)
        return offset

    _rp._leftDrawParaLine = _left
    _rp._centerDrawParaLine = _center
    _rp._rightDrawParaLine = _right
    _rp._justifyDrawParaLine = _justify


_patch_xhtml2pdf_cjk()

# 注册中文字体（xhtml2pdf 稳定路径：内置 CID 宋体）
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
pdfmetrics.registerFontFamily("STSong-Light", normal="STSong-Light",
                              bold="STSong-Light", italic="STSong-Light", boldItalic="STSong-Light")

CSS = """
@page { size: A4; margin: 1.8cm 1.7cm 1.9cm; }
body { font-family: "STSong-Light"; font-size: 10.5pt; line-height: 1.7; color: #1E293B;
       -pdf-word-wrap: CJK; }

/* ===== 封面 ===== */
.cover { text-align: center; }
.cover-brand { font-size: 11pt; color: #64748B; margin-bottom: 40pt; }
.cover-category { font-size: 10.5pt; color: #64748B; letter-spacing: 2pt; margin: 30pt 0 14pt; }
.cover-title { font-size: 23pt; font-weight: bold; color: #0F172A; margin: 0 0 14pt; line-height: 1.3; }
.cover-subtitle { font-size: 14pt; color: #1D4ED8; margin-bottom: 30pt; }
.cover-meta { font-size: 9.5pt; color: #64748B; line-height: 1.9; }
.cover-meta p { text-indent: 0; margin: 2pt 0; }
.cover-disclaimer { margin: 24pt 8pt 0; border: 1px solid #C0392B; color: #C0392B;
                    padding: 8pt 12pt; font-size: 8.5pt; line-height: 1.6; text-align: left; }
.cover-disclaimer p { text-indent: 0; }
.cover-break { page-break-before: always; }

/* ===== 目录 ===== */
.toc-title { font-size: 16pt; font-weight: bold; color: #0F172A;
             border-bottom: 2px solid #1D4ED8; padding-bottom: 4pt; margin-bottom: 10pt; }
.toc-item { font-size: 10.5pt; margin: 3pt 0; }
.toc-sub { font-size: 9.5pt; color: #64748B; padding-left: 16pt; margin: 2pt 0; }
.toc-break { page-break-before: always; }

/* ===== 正文 ===== */
h1 { font-size: 16.5pt; color: #0F172A; margin: 0 0 10pt; padding-bottom: 4pt;
     border-bottom: 2px solid #1D4ED8; }
h1.chapter { page-break-before: always; }
h2 { font-size: 13.5pt; color: #1D4ED8; margin: 16pt 0 8pt; padding-left: 8pt;
     border-left: 4px solid #1D4ED8; }
h3 { font-size: 11.5pt; color: #0F172A; margin: 12pt 0 6pt; }
h4 { font-size: 10.5pt; margin: 8pt 0 4pt; }
p { text-indent: 2em; margin: 0 0 5pt; text-align: justify; }
p.no-indent, li p, blockquote p, .cover p { text-indent: 0; }

ul, ol { margin: 4pt 0 6pt; padding-left: 22pt; }
li { margin: 2pt 0; }

table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 8pt;
        -pdf-word-wrap: CJK; }

/* ===== compact 模式（一页纸）===== */
body.compact { font-size: 9.5pt; line-height: 1.5; }
body.compact h1 { font-size: 13pt; page-break-before: auto; margin: 0 0 6pt; }
body.compact table { font-size: 8pt; margin: 4pt 0; }
body.compact p { margin: 3pt 0; }
th, td { border: 1px solid #CBD5E1; padding: 4pt 6pt; vertical-align: top; text-align: left; }
th { background: #0F172A; color: white; font-weight: bold; }
tr.row1 td { background: #F1F5F9; }

blockquote { margin: 6pt 0; padding: 6pt 12pt; border-left: 4px solid #9DB8E6;
             background: #F2F6FC; color: #33475B; }
code { font-family: "STSong-Light"; font-size: 9pt; background: #F0F0F0; }
pre { background: #F6F8FA; padding: 8pt; }
hr { border: 0; border-top: 1px solid #CBD5E1; margin: 12pt 0; }
"""

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# 非 GBK 字符兜底替换（STSong-Light 只覆盖 GBK，emoji 等会渲染成方框）
_GBK_FALLBACK = {
    "✅": "√", "✔": "√", "☑": "√",
    "❌": "×", "✘": "×", "☒": "×",
    "⚠": "△", "❗": "!", "❓": "?",
    "➜": "→", "➤": "→", "➢": "→",
    "−": "-", "–": "-", "—": "-", "～": "~", "〜": "~",
    "\ufe0f": "", "\u200b": "", "\u200e": "", "\u200f": "", "\u00a0": " ",
}

def sanitize_gbk(s):
    out = []
    for ch in s:
        if ch in _GBK_FALLBACK:
            r = _GBK_FALLBACK[ch]
            if r:
                out.append(r)
        else:
            try:
                ch.encode("gbk")
                out.append(ch)
            except UnicodeEncodeError:
                pass  # 丢弃无法渲染的字符
    return "".join(out)

def parse_cover(md_lines):
    info = {"brand": "", "title": "", "subtitle": "", "category": "", "meta": [], "disclaimer": ""}
    for ln in md_lines[:24]:
        s = ln.strip()
        m = re.match(r"^#\s+(.+)$", s)
        if m and not info["brand"]:
            info["brand"] = m.group(1).strip(); continue
        m = re.match(r"^##\s+(.+)$", s)
        if m and not info["title"]:
            info["title"] = m.group(1).strip(); continue
        m = re.match(r"^> (.+)$", s)
        if m:
            t = m.group(1).strip()
            if "免责" in t or t.startswith("⚠️"):
                if not info["disclaimer"]: info["disclaimer"] = t
            elif t.startswith("**数据快照") or t.startswith("**数据来源") or t.startswith("**署名"):
                info["meta"].append(t)
            elif not info["category"]:
                info["category"] = t
    return info

def split_body(md_text):
    """去掉封面头部（第一个---之前）与目录段"""
    lines = md_text.split("\n")
    sep_idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^-{3,}\s*$", ln.strip()):
            sep_idx = i; break
    body_lines = lines[sep_idx + 1:] if sep_idx is not None else lines
    toc_items, toc_subs, body = [], [], []
    i = 0
    while i < len(body_lines):
        ln = body_lines[i]
        s = ln.strip()
        if re.match(r"^#{1,3}\s+目录\s*$", s):
            j = i + 1
            while j < len(body_lines) and not re.match(r"^-{3,}\s*$", body_lines[j].strip()):
                t = body_lines[j].strip()
                if t.startswith("**") and "：" in t:
                    name, rest = t.split("：", 1)
                    toc_items.append((name.strip("*"), rest.strip()))
                elif t and not t.startswith("#"):
                    toc_subs.append(t)
                j += 1
            i = j + 1; continue
        body.append(ln); i += 1
    return toc_items, toc_subs, "\n".join(body)

def build_html(md_path, compact=False):
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    info = parse_cover(md_text.split("\n"))
    toc_items, toc_subs, body_md = split_body(md_text)

    html_body = markdown.markdown(body_md, extensions=["tables", "fenced_code", "sane_lists"])
    # H1 章节前断页（compact 一页纸模式不断页）
    if not compact:
        html_body = re.sub(r"<h1>(.+?)</h1>",
                           lambda m: f'<h1 class="chapter">{m.group(1)}</h1>'
                                     if not m.group(1).startswith("ST众泰") else f'<h1>{m.group(1)}</h1>',
                           html_body)
    # 表格偶数行加 row1 class（斑马纹，xhtml2pdf 无 :nth-child）
    rows = re.findall(r"<tr>(.*?)</tr>", html_body, re.S)
    idx = 0
    for r in rows:
        if "<td" in r:
            idx += 1
            if idx % 2 == 0:
                html_body = html_body.replace("<tr>" + r + "</tr>", '<tr class="row1">' + r + "</tr>", 1)
            else:
                html_body = html_body.replace("<tr>" + r + "</tr>", "<tr>" + r + "</tr>", 1)

    meta_html = "".join(f"<p>{esc(t.replace('**', ''))}</p>" for t in info["meta"])
    disc = f'<div class="cover-disclaimer">{esc(info["disclaimer"].replace("**", ""))}</div>' if info["disclaimer"] else ""
    if compact:
        cover = ""
        toc = ""
    else:
        cover = f"""
    <div class="cover">
      <div class="cover-brand">{esc(info["brand"])}</div>
      <div class="cover-category">{esc(info["category"])}</div>
      <div class="cover-title">{esc(info["title"])}</div>
      <div class="cover-subtitle">{esc(info["subtitle"])}</div>
      <div class="cover-meta">{meta_html}</div>
      {disc}
    </div>
    <div class="cover-break"></div>"""

        toc_rows = "".join(
            f'<div class="toc-item">{esc(name)} —— {esc(rest)}</div>' for name, rest in toc_items)
        toc_subs_html = "".join(f'<div class="toc-sub">{esc(t)}</div>' for t in toc_subs)
        toc = f"""
    <div class="toc-title">目录</div>
    {toc_rows}{toc_subs_html}
    <div class="toc-break"></div>"""

    body_cls = ' class="compact"' if compact else ""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body{body_cls}>{cover}{toc}{html_body}</body></html>"""
    return sanitize_gbk(html)

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("STSong-Light", 7.5)
    canvas.setFillColorRGB(0.4, 0.45, 0.53)
    canvas.drawString(1.7*cm, 1.0*cm, "ST众泰投委会 · 研深行 | 仅供研究参考，不构成个人投资建议")
    canvas.drawRightString(A4[0]-1.7*cm, 1.0*cm, f"第 {doc.page} 页")
    canvas.restoreState()

def render_pdf(html, pdf_path):
    from xhtml2pdf import pisa
    with open(pdf_path, "wb") as f:
        status = pisa.CreatePDF(html, dest=f, callback=footer, encoding="utf-8")
    if status.err:
        print("[错误] xhtml2pdf 渲染失败")
        return False
    print("PDF OK:", pdf_path, f"({os.path.getsize(pdf_path)} bytes)")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("用法: python md2pdf_pro.py <input.md> <output.pdf> [--compact]")
    md_path, pdf_path = sys.argv[1], sys.argv[2]
    compact = "--compact" in sys.argv[3:]
    html = build_html(md_path, compact=compact)
    if not render_pdf(html, pdf_path):
        sys.exit(1)
