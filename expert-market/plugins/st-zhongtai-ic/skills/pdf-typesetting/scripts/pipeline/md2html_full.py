# -*- coding: utf-8 -*-
"""
md2html_full.py — 深度报告「全文 HTML」生成器（浏览器友好版）
与 md2pdf_pro.py 同源解析（封面/目录/正文），但输出面向浏览器：
  - 自包含单文件、内联 CSS、双击即开、无网络依赖
  - 保留全 Unicode 字符（不做 GBK 兜底，emoji 等不丢失）
  - 标题锚点 + 目录可点击跳转；@media print 保留分页观感
用法: python md2html_full.py <报告.md> [输出.html] [--compact]
依赖: markdown（与 md2pdf_pro 同款；解析函数已内联，无需 xhtml2pdf）
注意: parse_cover/split_body 与 md2pdf_pro.py 保持同源，改动需两处同步
"""
import io, re, sys, os
import html as htmllib
import markdown


def parse_cover(md_lines):
    """封面元信息解析（与 md2pdf_pro.py 同源）"""
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
    """去掉封面头部（第一个---之前）与目录段（与 md2pdf_pro.py 同源）"""
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

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Microsoft YaHei","PingFang SC","SimSun",sans-serif;
       background: #f0f2f5; color: #1e293b; padding: 24px 12px; line-height: 1.75; }
.wrap { max-width: 1000px; margin: 0 auto; }

/* ===== 封面 ===== */
.cover { background: linear-gradient(135deg,#0f2740,#123a5f); color: #fff;
         border-radius: 12px; padding: 40px 44px; margin-bottom: 18px; }
.cover-brand { font-size: 12px; color: #9db8e6; letter-spacing: 1px; margin-bottom: 26px; }
.cover-category { font-size: 12px; color: #b8c9dc; margin: 18px 0 10px; }
.cover-title { font-size: 26px; font-weight: 700; line-height: 1.35; margin-bottom: 10px; }
.cover-subtitle { font-size: 15px; color: #7fb3ff; margin-bottom: 24px; line-height: 1.6; }
.cover-meta { font-size: 12px; color: #c8d6e8; line-height: 2; }
.cover-meta p { margin: 0; }
.cover-disclaimer { margin-top: 20px; border: 1px solid #e57373; color: #ffb4b4;
                    border-radius: 6px; padding: 10px 14px; font-size: 11px; line-height: 1.6; }

/* ===== 目录 ===== */
.toc { background: #fff; border-radius: 12px; padding: 22px 28px; margin-bottom: 18px;
       box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.toc-title { font-size: 18px; font-weight: 700; color: #0f172a;
             border-bottom: 2px solid #1d4ed8; padding-bottom: 8px; margin-bottom: 12px; }
.toc-item { font-size: 13px; margin: 5px 0; }
.toc-item a { color: #123a5f; text-decoration: none; }
.toc-item a:hover { color: #1d4ed8; text-decoration: underline; }
.toc-sub { font-size: 12px; color: #64748b; padding-left: 20px; margin: 3px 0; }

/* ===== 正文 ===== */
.body { background: #fff; border-radius: 12px; padding: 30px 36px;
        box-shadow: 0 1px 3px rgba(0,0,0,.06); }
h1 { font-size: 20px; color: #0f172a; margin: 30px 0 14px; padding-bottom: 8px;
     border-bottom: 2px solid #1d4ed8; }
h1:first-child { margin-top: 0; }
h2 { font-size: 16px; color: #1d4ed8; margin: 22px 0 10px; padding-left: 10px;
     border-left: 4px solid #1d4ed8; }
h3 { font-size: 14px; color: #0f172a; margin: 16px 0 8px; }
h4 { font-size: 13px; margin: 12px 0 6px; }
p { margin: 0 0 10px; text-align: justify; }
strong { color: #0f2740; }
ul, ol { margin: 6px 0 10px; padding-left: 26px; }
li { margin: 4px 0; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 12.5px; }
th, td { border: 1px solid #cbd5e1; padding: 7px 9px; vertical-align: top; text-align: left; }
th { background: #0f2740; color: #fff; font-weight: 600; white-space: nowrap; }
tbody tr:nth-child(even) { background: #f1f5f9; }
tr:hover td { background: #eaf1fb; }
blockquote { margin: 10px 0; padding: 10px 16px; border-left: 4px solid #9db8e6;
             background: #f2f6fc; color: #33475b; font-size: 13px; }
blockquote p { margin: 0; }
code { font-family: Consolas,"Courier New",monospace; font-size: 12px;
       background: #f0f0f0; padding: 1px 5px; border-radius: 3px; }
pre { background: #f6f8fa; padding: 12px; border-radius: 6px; overflow-x: auto; }
pre code { background: none; padding: 0; }
hr { border: 0; border-top: 1px solid #cbd5e1; margin: 18px 0; }

.foot { text-align: center; color: #94a3b8; font-size: 11px; margin: 22px 0 8px; }

@media print {
  body { background: #fff; padding: 0; }
  .cover, .toc, .body { box-shadow: none; border-radius: 0; }
  h1 { page-break-before: always; }
  h1:first-child { page-break-before: auto; }
  .cover, .toc { page-break-after: always; }
}
"""


def esc(s):
    return htmllib.escape(s, quote=False)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def build_full_html(md_path, compact=False):
    with io.open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    info = parse_cover(md_text.split("\n"))
    toc_items, toc_subs, body_md = split_body(md_text)

    html_body = markdown.markdown(body_md, extensions=["tables", "fenced_code", "sane_lists"])

    # 标题加锚点 id（h1-h4），并登记 (level, text, id)
    headings = []
    counter = {}

    def _anchor(m):
        lvl = m.group(1)
        inner = m.group(2)
        text = strip_tags(inner).strip()
        counter[text] = counter.get(text, 0) + 1
        hid = "sec-%d" % (len(headings) + 1)
        headings.append((int(lvl), text, hid))
        return '<h%s id="%s">%s</h%s>' % (lvl, hid, inner, lvl)

    html_body = re.sub(r"<h([1-4])>(.+?)</h\1>", _anchor, html_body, flags=re.S)

    name_to_id = {}
    for lvl, text, hid in headings:
        name_to_id.setdefault(text, hid)

    if compact:
        cover_html = ""
        toc_html = ""
    else:
        meta_html = "".join("<p>%s</p>" % esc(t.replace("**", "")) for t in info["meta"])
        disc = ('<div class="cover-disclaimer">%s</div>' % esc(info["disclaimer"].replace("**", ""))
                if info["disclaimer"] else "")
        cover_html = """
    <div class="cover">
      <div class="cover-brand">%s</div>
      <div class="cover-category">%s</div>
      <div class="cover-title">%s</div>
      <div class="cover-subtitle">%s</div>
      <div class="cover-meta">%s</div>
      %s
    </div>""" % (esc(info["brand"]), esc(info["category"]), esc(info["title"]),
                 esc(info["subtitle"]), meta_html, disc)
        toc_rows = []
        for name, rest in toc_items:
            hid = name_to_id.get(name)
            if hid:
                toc_rows.append('<div class="toc-item"><a href="#%s">%s</a> —— %s</div>'
                                % (hid, esc(name), esc(rest)))
            else:
                toc_rows.append('<div class="toc-item">%s —— %s</div>' % (esc(name), esc(rest)))
        # 目录 sub 行：若与正文标题匹配则转可点击链接（兼容 "- 章节" 格式目录）
        toc_subs_lines = []
        for t in toc_subs:
            clean = t.lstrip("-*• ").strip()
            hid = name_to_id.get(clean)
            if hid:
                toc_subs_lines.append('<div class="toc-item"><a href="#%s">%s</a></div>'
                                      % (hid, esc(clean)))
            else:
                toc_subs_lines.append('<div class="toc-sub">%s</div>' % esc(t))
        toc_subs_html = "".join(toc_subs_lines)
        toc_html = """
    <div class="toc">
      <div class="toc-title">目录</div>
      %s%s
    </div>""" % ("".join(toc_rows), toc_subs_html)

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>%s</style>
</head>
<body>
<div class="wrap">
%s%s<div class="body">
%s
</div>
<div class="foot">ST众泰投委会 · 研深行 ｜ 全文 HTML 版（过程稿）—— 定稿以 PDF 为准</div>
</div>
</body>
</html>""" % (esc(info["title"]), CSS, cover_html, toc_html, html_body)
    return html


def main():
    args = sys.argv[1:]
    compact = "--compact" in args
    args = [a for a in args if a != "--compact"]
    if not args:
        sys.exit("用法: python md2html_full.py <报告.md> [输出.html] [--compact]")
    md_path = args[0]
    if len(args) >= 2:
        out_path = args[1]
    else:
        out_path = os.path.splitext(md_path)[0] + ".html"
    html = build_full_html(md_path, compact=compact)
    with io.open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML 全文已生成: %s (%dKB)" % (out_path, os.path.getsize(out_path) // 1024))


if __name__ == "__main__":
    main()
