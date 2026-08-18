# -*- coding: utf-8 -*-
"""阶段5：由 entries.json 生成 06_检索页/index.html（单文件内嵌数据）"""
import json, io, os

OUT = r"C:/Users/Administrator/Desktop/市场研究/大V研究/书籍蒸馏/06_检索页"
data = json.load(io.open(os.path.join(OUT, "entries.json"), encoding="utf-8"))
records = data["records"]; stats = data["stats"]

books = sorted(set(r["book"] for r in records))
themes = [t for t in sorted(set(r["theme"] for r in records)) if t != "现象记录（未过三验）"] + ["现象记录（未过三验）"]

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>书籍蒸馏知识库检索 · v1</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f5f5f7; color: #222; font-size: 14px; }
header { background: linear-gradient(135deg, #4a3a1a, #8a6a2d); color: #fff; padding: 18px 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
header h1 { font-size: 18px; font-weight: 500; }
header .sub { font-size: 12px; opacity: 0.85; margin-top: 4px; }
.container { max-width: 1150px; margin: 16px auto; padding: 0 16px; }
.panel { background: #fff; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.search-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.search-row input, .search-row select { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; background: #fff; }
.search-row input[type=text] { flex: 1; min-width: 220px; }
.stats { display: flex; gap: 14px; font-size: 12px; color: #666; padding: 6px 0; flex-wrap: wrap; }
.stats .pill { background: #f6f1e6; padding: 4px 10px; border-radius: 12px; }
.stats .pill b { color: #8a6a2d; font-weight: 600; }
.result-list { max-height: 640px; overflow-y: auto; }
.entry { padding: 12px; border-bottom: 1px solid #eee; transition: background 0.15s; }
.entry:hover { background: #fafbfc; }
.entry .head { display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.entry .id { color: #8a6a2d; font-size: 12px; font-family: monospace; font-weight: 600; }
.entry .bk { color: #aaa; font-size: 10px; font-family: monospace; }
.entry .title { font-size: 13.5px; font-weight: 500; color: #333; line-height: 1.5; }
.tag { display: inline-block; font-size: 10px; padding: 1px 7px; border-radius: 3px; margin-right: 4px; color: #fff; }
.tag.book-ZP { background: #2d5a87; } .tag.book-MG { background: #5a8c5a; } .tag.book-QS { background: #8a5a87; }
.tag.type-R { background: #1a3a5c; } .tag.type-E { background: #aaa; }
.tag.mg { background: #c44; } .tag.xr-i { background: #2a8; } .tag.xr-c { background: #c44; } .tag.xr-m { background: #c84; }
.entry .body { margin-top: 6px; font-size: 12.5px; line-height: 1.6; color: #555; }
.entry .body b { color: #333; font-weight: 600; }
.entry .meta { margin-top: 5px; font-size: 11px; color: #999; }
.tag-cloud { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.tag-cloud .tag-chip { padding: 4px 10px; background: #f6f1e6; border-radius: 12px; cursor: pointer; font-size: 12px; }
.tag-cloud .tag-chip:hover { background: #8a6a2d; color: #fff; }
.tag-cloud .tag-chip.active { background: #4a3a1a; color: #fff; }
.info-banner { background: #fff8e1; border-left: 3px solid #f59e0b; padding: 10px 14px; border-radius: 4px; font-size: 12px; margin-bottom: 12px; line-height: 1.7; }
.info-banner a { color: #8a6a2d; }
.empty { text-align: center; color: #999; padding: 40px; }
mark { background: #ffe9a8; }
</style>
</head>
<body>
<header>
  <h1>📚 书籍蒸馏知识库检索</h1>
  <div class="sub">三书 · __TOTAL__ 条记录（规律 108 已过三重验证 + 现象 157 未过门槛留档）· 11 组跨书互证 · 大V交叉 38 条</div>
</header>
<div class="container">
  <div class="info-banner">
    📌 数据源：<code>大V研究\\书籍蒸馏\\03_观点条目库\\</code>（S3_规律条目库 + 三书单库 + 现象记录 + 大V交叉引用）<br>
    🔍 检索维度：关键词（标题/证据/边界/教训）· 书 · 主题 · 类型 · 跨书互证 · 大V交叉 · 点击主题标签快速筛选<br>
    📖 框架层入口：<a href="../04_框架提炼/S4_框架_周期估值与人性.md">凌鹏框架</a> · <a href="../04_框架提炼/S4_框架_燕翔两本.md">燕翔世界观</a> · <a href="../04_框架提炼/S4_跨书主题对照矩阵.md">跨书对照矩阵</a> · <a href="../03_观点条目库/S3_大V交叉引用.md">大V交叉引用</a><br>
    ⚠️ 引用纪律：条目 ID 双制（ZP-01 = BK-ZP-R01）；现象记录未过三验仅作线索不作依据；书数据截止 2018/2021/2022，引用时注意时点。
  </div>
  <div class="panel">
    <div class="search-row">
      <input type="text" id="q" placeholder="关键词,如'滞胀'/'抱团'/'利率'/'回购'/'五阶段'">
      <select id="bookFilter"><option value="">全部书</option></select>
      <select id="themeFilter"><option value="">全部主题</option></select>
      <select id="typeFilter">
        <option value="">全部类型</option><option value="规律">规律(过三验)</option><option value="现象">现象(留档)</option>
      </select>
      <select id="mgFilter">
        <option value="">互证:全部</option><option value="有">仅跨书互证</option><option value="无">无互证</option>
      </select>
      <select id="xrFilter">
        <option value="">大V交叉:全部</option><option value="印证">印证</option><option value="冲突">冲突</option><option value="互补">互补</option><option value="无">无交叉</option>
      </select>
      <button onclick="doSearch()" style="padding:6px 16px;background:#8a6a2d;color:#fff;border:none;border-radius:4px;cursor:pointer;">搜索</button>
      <button onclick="resetFilter()" style="padding:6px 12px;background:#eee;border:none;border-radius:4px;cursor:pointer;">重置</button>
    </div>
  </div>
  <div class="panel"><div class="stats" id="stats"></div></div>
  <div class="panel">
    <h3 style="font-size:13px;color:#666;margin-bottom:8px;">主题速筛（点击）</h3>
    <div class="tag-cloud" id="themeCloud"></div>
  </div>
  <div class="panel">
    <div id="resultInfo" style="font-size:12px;color:#666;margin-bottom:8px;"></div>
    <div class="result-list" id="results"></div>
  </div>
</div>
<script>
const RECORDS = __DATA__;
const BOOK_LIST = __BOOKS__;
const THEME_LIST = __THEMES__;

function esc(s){ if(!s) return ""; return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function hl(s, kw){ const e = esc(s); if(!kw) return e; try{ const r = new RegExp("("+kw.replace(/[.*+?^${}()|[\\]\\\\]/g,"\\\\$&")+")","gi"); return e.replace(r,"<mark>$1</mark>"); }catch(_){ return e; } }

function populateFilters(){
  const bf = document.getElementById('bookFilter'), tf = document.getElementById('themeFilter');
  BOOK_LIST.forEach(b=>{ const o=document.createElement('option'); o.value=b; o.textContent=b; bf.appendChild(o); });
  THEME_LIST.forEach(t=>{ const o=document.createElement('option'); o.value=t; o.textContent=t; tf.appendChild(o); });
}
function renderCloud(){
  const c = document.getElementById('themeCloud');
  c.innerHTML = '';
  THEME_LIST.forEach(t=>{
    const n = RECORDS.filter(r=>r.theme===t).length;
    const chip = document.createElement('span'); chip.className='tag-chip'; chip.textContent = t+" ("+n+")";
    chip.onclick = ()=>{ document.getElementById('themeFilter').value = t; doSearch(); };
    if (document.getElementById('themeFilter').value === t) chip.classList.add('active');
    c.appendChild(chip);
  });
}
function doSearch(){
  const kw = document.getElementById('q').value.trim().toLowerCase();
  const bf = document.getElementById('bookFilter').value;
  const tf = document.getElementById('themeFilter').value;
  const tyf = document.getElementById('typeFilter').value;
  const mgf = document.getElementById('mgFilter').value;
  const xrf = document.getElementById('xrFilter').value;
  let rows = RECORDS.filter(r=>{
    if (bf && r.book!==bf) return false;
    if (tf && r.theme!==tf) return false;
    if (tyf && r.type!==tyf) return false;
    if (mgf==='有' && !r.mgroup) return false;
    if (mgf==='无' && r.mgroup) return false;
    if (xrf==='无' && r.xref) return false;
    if (xrf && xrf!=='无' && !(r.xref&&r.xref.includes(xrf))) return false;
    if (kw){
      const blob = (r.title+r.evidence+r.boundary+r.lesson+r.id+r.theme+r.book).toLowerCase();
      if (!blob.includes(kw)) return false;
    }
    return true;
  });
  // 排序：规律在前 → 标题命中关键词优先 → 互证优先
  const kwLow = kw || "";
  rows.sort((a,b)=>{
    if (a.type!==b.type) return a.type==='规律'?-1:1;
    const at = kwLow && a.title.toLowerCase().includes(kwLow) ? 0:1;
    const bt = kwLow && b.title.toLowerCase().includes(kwLow) ? 0:1;
    if (at!==bt) return at-bt;
    return (b.mgroup?1:0)-(a.mgroup?1:0);
  });
  const nR = rows.filter(r=>r.type==='规律').length, nE = rows.length-nR;
  document.getElementById('resultInfo').textContent = "命中 " + rows.length + " 条（规律 "+nR+" · 现象 "+nE+"）";
  document.getElementById('stats').innerHTML =
    "<span class='pill'>总记录 <b>"+RECORDS.length+"</b></span>"+
    "<span class='pill'>规律 <b>"+RECORDS.filter(r=>r.type==='规律').length+"</b></span>"+
    "<span class='pill'>现象 <b>"+RECORDS.filter(r=>r.type==='现象').length+"</b></span>"+
    "<span class='pill'>跨书互证组 <b>11</b></span>"+
    "<span class='pill'>大V交叉 <b>38</b></span>"+
    "<span class='pill'>数据截止：ZP2022 / MG2018 / QS2021</span>";
  const box = document.getElementById('results');
  if (!rows.length){ box.innerHTML = "<div class='empty'>无命中</div>"; return; }
  box.innerHTML = rows.slice(0,300).map(r=>{
    const pre = r.id.slice(0,2);
    const tags =
      "<span class='tag book-"+pre+"'>"+pre+"</span>"+
      "<span class='tag type-"+(r.type==='规律'?'R':'E')+"'>"+r.type+"</span>"+
      (r.mgroup ? "<span class='tag mg'>互证"+r.mgroup+"</span>" : "")+
      (r.xref ? r.xref.split('/').map(x=>"<span class='tag xr-"+x[0]+(x==='互补'?'m':x==='印证'?'i':'c')+"'>大V·"+x+"</span>").join('') : "");
    let body = "";
    if (r.evidence) body += "<div><b>证据：</b>"+hl(r.evidence.slice(0,400), kw)+(r.evidence.length>400?"…":"")+"</div>";
    if (r.boundary) body += "<div><b>边界：</b>"+hl(r.boundary, kw)+"</div>";
    if (r.lesson && r.lesson!=='无') body += "<div><b>反面教训：</b>"+hl(r.lesson.slice(0,200), kw)+"</div>";
    if (r.type==='现象' && r.detail) body += "<div style='color:#999'>"+hl(r.detail.slice(0,300), kw)+"…</div>";
    const meta = [r.cutoff?"数据截止:"+r.cutoff:"", r.source?"出处:"+r.source.slice(0,120):""].filter(Boolean).join(" · ");
    return "<div class='entry'><div class='head'><span class='id'>"+r.id+"</span><span class='bk'>"+r.bk+"</span>"+tags+
      "</div><div class='title'>"+hl(r.title, kw)+"</div><div class='body'>"+body+"</div>"+(meta?"<div class='meta'>"+esc(meta)+"</div>":"")+"</div>";
  }).join("") + (rows.length>300?"<div class='empty'>仅显示前300条，请收窄条件</div>":"");
  renderCloud();
}
function resetFilter(){ ['q'].forEach(i=>document.getElementById(i).value=''); ['bookFilter','themeFilter','typeFilter','mgFilter','xrFilter'].forEach(i=>document.getElementById(i).value=''); doSearch(); }
document.getElementById('q').addEventListener('keydown', e=>{ if(e.key==='Enter') doSearch(); });
populateFilters(); doSearch();
</script>
</body>
</html>
"""

html = (HTML
        .replace("__DATA__", json.dumps(records, ensure_ascii=False))
        .replace("__BOOKS__", json.dumps(books, ensure_ascii=False))
        .replace("__THEMES__", json.dumps(themes, ensure_ascii=False))
        .replace("__TOTAL__", str(len(records))))
with io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("index.html 已生成:", os.path.getsize(os.path.join(OUT, "index.html")), "bytes")
