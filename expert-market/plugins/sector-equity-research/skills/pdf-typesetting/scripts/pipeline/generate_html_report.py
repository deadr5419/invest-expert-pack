# -*- coding: utf-8 -*-
"""
generate_html_report.py — 组合报告「过程稿」交互 HTML 生成器（主版，scripts/pipeline/，2026-08-17 收口）
定位: 多标的组合报告专用（评级总览表+行业逻辑链+待核事项交互版）；单标的全文版请用 md2html_full.py
用法: python generate_html_report.py <深度报告.md> [输出.html]
产出: 自包含单文件 HTML（内联 CSS/JS，双击即开，无网络依赖）
功能:
  1. 评级总览表: 深底表头 + 评级色编码 + hover 行高亮 + 右侧明细卡 + 表头点击排序
  2. 行业逻辑链: 因果链节点横向流，点击节点展开原文
  3. 待核/STALE/来源标记统计
注: 提取逻辑绑定组合报告模板章节（评级总览/行业全景/待核事项），由 report-skeleton 保证结构一致；
    原基准: deliverables/创新药前十成份股研究/generate_html_report.py（历史副本，仅供存档）
"""
import io, re, sys, os, html

def read_md(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()

def extract_rating_table(md):
    """解析评级总览表（11列表头 + 数据行）"""
    lines = md.split("\n")
    header, rows = None, []
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "覆盖倍数" in line and "评级依据" in line:
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("|"):
                row = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                if len(row) == len(header):
                    rows.append(row)
                j += 1
            break
    return header, rows

def extract_industry_chain(md):
    """解析二、行业全景的 **小节标题** + 正文（因果链节点）"""
    m = re.search(r"## 二、行业全景\n(.*?)(?=\n## 三、)", md, re.S)
    if not m:
        return []
    body = m.group(1)
    parts = re.findall(r"\*\*(.+?)\*\*(.*?)(?=\n\*\*|\Z)", body, re.S)
    nodes = []
    for title, text in parts:
        text = text.strip().replace("\n", " ")
        if text and len(text) > 20:
            nodes.append((title.strip(), text))
    return nodes

def extract_waitlist(md):
    """提取待核清单行"""
    m = re.search(r"## 六、待核事项[^\n]*\n(.*?)(?=\n---|\Z)", md, re.S)
    items = []
    if m:
        for line in m.group(1).split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("•"):
                items.append(line.lstrip("-• ").strip())
    return items

def rating_color(rating):
    r = rating.replace("（", "(").replace("）", ")")
    if "强推" in r: return ("#C81E1E", "#FCEBEB")   # 红 = 看多
    if "谨慎" in r or "回避" in r: return ("#1E7A3C", "#E7F4EA")  # 绿 = 谨慎
    if "贴线" in r: return ("#B45309", "#FEF3C7")   # 橙 = 贴线
    return ("#475569", "#F1F5F9")                    # 灰 = 中性

def build_html(title, subtitle, header, rows, chain, waitlist, staleness):
    col_widths = [70, 78, 74, 60, 56, 56, 56, 70, 66, 60, 9999]
    css_widths = ["7.5%","8%","7.5%","6%","6%","6%","6%","7%","6.5%","6%","auto"]
    thead = "".join(f"<th data-k='{i}' style='width:{w}'>{html.escape(c)}</th>" for i, (c, w) in enumerate(zip(header, css_widths)))
    tbody = ""
    for row in rows:
        color, bg = rating_color(row[2])
        tds = "".join(
            f"<td style='{'background:'+bg+';color:'+color+';font-weight:600;border-radius:4px' if i==2 else ''}'>{html.escape(row[i])}</td>"
            for i in range(len(row)))
        detail = " · ".join(row)
        tbody += f"<tr onclick='showDetail({len(tbody)})' data-detail='{html.escape(detail)}'>{tds}</tr>"
    chain_html = ""
    for idx, (title_c, text) in enumerate(chain):
        chain_html += f"""
        <div class='node' onclick='showChain({idx})'>
          <div class='node-idx'>{idx+1}</div>
          <div class='node-title'>{html.escape(title_c)}</div>
        </div>"""
        if idx < len(chain) - 1:
            chain_html += "<div class='arrow'>→</div>"
    wait_html = "".join(f"<li>{html.escape(w)}</li>" for w in waitlist) if waitlist else "<li>无</li>"
    chain_texts = [html.escape(t) for t, _ in chain]
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Microsoft YaHei","PingFang SC",sans-serif; background: #f5f6f8; color: #1e293b; padding: 24px; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  .hd {{ background: #123a5f; color: #fff; border-radius: 10px; padding: 22px 26px; margin-bottom: 18px; }}
  .hd h1 {{ font-size: 20px; font-weight: 500; }}
  .hd .sub {{ font-size: 12px; color: #b8c9dc; margin-top: 8px; line-height: 1.8; }}
  .card {{ background: #fff; border-radius: 10px; padding: 18px 22px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }}
  .card h2 {{ font-size: 15px; font-weight: 500; margin-bottom: 12px; color: #123a5f; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #123a5f; color: #fff; padding: 9px 8px; text-align: left; font-weight: 500; cursor: pointer; white-space: nowrap; }}
  th:hover {{ background: #1d5284; }}
  td {{ padding: 8px; border-bottom: 1px solid #e8ecf1; }}
  tr:hover td {{ background: #f0f6ff; }}
  tr {{ cursor: pointer; }}
  .tag {{ display: inline-block; font-size: 11px; padding: 1px 8px; border-radius: 9px; margin-right: 6px; }}
  .detail-panel {{ position: fixed; right: 18px; top: 18px; width: 280px; background: #fff; border: 1px solid #d5dce4; border-radius: 10px; padding: 14px 16px; box-shadow: 0 4px 16px rgba(0,0,0,.12); display: none; font-size: 12px; line-height: 1.8; }}
  .chain {{ display: flex; align-items: stretch; flex-wrap: wrap; gap: 6px; margin-top: 6px; }}
  .node {{ flex: 0 0 auto; width: 108px; background: #eef3f9; border: 1px solid #c7d5e4; border-radius: 8px; padding: 10px 8px; text-align: center; cursor: pointer; transition: .15s; }}
  .node:hover {{ background: #dbe9f8; border-color: #123a5f; }}
  .node-idx {{ font-size: 10px; color: #7d8fa3; }}
  .node-title {{ font-size: 12px; margin-top: 4px; font-weight: 500; line-height: 1.4; }}
  .arrow {{ align-self: center; color: #94a3b8; font-size: 16px; padding: 0 1px; }}
  .chain-detail {{ background: #f8fafc; border-left: 3px solid #123a5f; padding: 12px 14px; margin-top: 12px; border-radius: 0 6px 6px 0; font-size: 12.5px; line-height: 1.9; display: none; }}
  ul {{ padding-left: 20px; font-size: 12.5px; line-height: 2; }}
  .foot {{ text-align: center; color: #94a3b8; font-size: 11px; margin-top: 20px; }}
  .badge {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="hd">
    <h1>{html.escape(title)}</h1>
    <div class="sub">{html.escape(subtitle)}</div>
  </div>

  <div class="card">
    <h2>一、评级总览表（公允价值-安全边际体系）<span style="font-size:11px;color:#7d8fa3;font-weight:400">　点击表头排序 · 点击行看明细</span></h2>
    <table id="rt"><thead><tr>{thead}</tr></thead><tbody id="rtbody">{tbody}</tbody></table>
  </div>

  <div class="card">
    <h2>二、行业逻辑链（thesis-first 因果链）</h2>
    <div class="chain">{chain_html}</div>
    <div class="chain-detail" id="chainDetail"></div>
  </div>

  <div class="card">
    <h2>三、待核事项</h2>
    <ul>{wait_html}</ul>
  </div>

  <div class="foot">ST众泰投委会 · 研深行 ｜ 过程稿（HTML 快速迭代版）—— 定稿以 PDF 为准 ｜ {html.escape(staleness)}</div>
</div>

<div class="detail-panel" id="detailPanel"></div>

<script>
const chainTexts = {chain_texts};
function showDetail(k) {{
  const row = document.querySelectorAll('#rtbody tr')[k];
  const txt = row ? row.dataset.detail : '';
  const p = document.getElementById('detailPanel');
  p.innerHTML = '<b style="font-size:13px">该票全行数据</b><br>' + txt.replace(/ · /g, '<br>');
  p.style.display = 'block';
}}
document.addEventListener('click', (e) => {{
  if (!e.target.closest('#rtbody tr')) {{
    const p = document.getElementById('detailPanel');
    if (p && !e.target.closest('.detail-panel')) p.style.display = 'none';
  }}
}});
function showChain(i) {{
  const d = document.getElementById('chainDetail');
  d.style.display = 'block';
  d.textContent = chainTexts[i];
}}
const ths = document.querySelectorAll('#rt th');
ths.forEach((th, k) => th.addEventListener('click', () => {{
  const tbody = document.getElementById('rtbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const dir = th.dataset.dir === '1' ? -1 : 1;
  th.dataset.dir = dir === 1 ? '1' : '0';
  rows.sort((a, b) => {{
    const av = a.children[k].textContent.trim();
    const bv = b.children[k].textContent.trim();
    const an = parseFloat(av.replace('%','').replace('×',''));
    const bn = parseFloat(bv.replace('%','').replace('×',''));
    if (!isNaN(an) && !isNaN(bn)) return dir * (an - bn);
    return dir * av.localeCompare(bv, 'zh');
  }});
  rows.forEach(r => tbody.appendChild(r));
}}));
</script>
</body>
</html>"""

def main():
    md_path = sys.argv[1] if len(sys.argv) > 1 else "深度研究报告_中证港股通创新药前十成份股.md"
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(md_path)[0] + ".html"
    md = read_md(md_path)
    header, rows = extract_rating_table(md)
    chain = extract_industry_chain(md)
    waitlist = extract_waitlist(md)
    title = re.search(r"^#\s*(.+)$", md, re.M).group(1) if re.search(r"^#\s*(.+)$", md, re.M) else "深度研究报告"
    n_wait = len(re.findall(r"\[待核\]", md))
    n_stale = len(re.findall(r"\[STALE\]", md))
    subtitle = f"过程稿 · 交互版 ｜ 评级总览 {len(rows)} 标的 ｜ 行业逻辑链 {len(chain)} 节点 ｜ 待核 {n_wait} 处 / STALE {n_stale} 处"
    html_out = build_html(title, subtitle, header, rows, chain, waitlist, f"待核 {n_wait} · STALE {n_stale}")
    with io.open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"HTML 过程稿已生成: {out_path} ({os.path.getsize(out_path)//1024}KB)")
    print(f"评级表 {len(rows)} 行 · 逻辑链 {len(chain)} 节点 · 待核 {n_wait} · STALE {n_stale}")

if __name__ == "__main__":
    main()
