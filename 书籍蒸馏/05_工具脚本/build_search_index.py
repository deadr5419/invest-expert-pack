# -*- coding: utf-8 -*-
"""阶段5：书籍蒸馏检索页构建脚本
解析三书条目库+合并总库主题/互证+大V交叉引用 → 06_检索页/index.html（单文件内嵌JSON）
"""
import re, json, os, io

BASE = r"C:/Users/Administrator/Desktop/市场研究/大V研究/书籍蒸馏"
WS = os.path.join(BASE, "03_观点条目库")
OUT_DIR = os.path.join(BASE, "06_检索页")

BOOKS = {
    "ZP": ("周期估值与人性", "周期、估值与人性（凌鹏2022）", "A股2005-2022"),
    "MG": ("美股70年", "美股70年（燕翔2019）", "美股1948-2018"),
    "QS": ("全球股市启示录", "全球股市启示录（燕翔2022）", "全球跨市场·截止2021"),
}

def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()

# ---------- 1. 解析三书单书条目库（108条） ----------
def parse_book(prefix):
    name = BOOKS[prefix][0]
    path = os.path.join(WS, "_S3_工作区", "S3_条目库_%s.md" % name)
    text = read(path)
    entries = []
    # 按 ### [ID] 标题切分
    blocks = re.split(r"\n### \[", text)
    for blk in blocks[1:]:
        m = re.match(r"((?:ZP|MG|QS)-\d{2})\]\s*(.+)", blk)
        if not m:
            continue
        eid, title = m.group(1), m.group(2).strip()
        body = blk
        def field(fname):
            fm = re.search(r"- %s[：:]\s*(.+?)(?=\n- [^\s]|\n### |\Z)" % fname, body, re.S)
            return fm.group(1).strip() if fm else ""
        # 单书库章节主题（## 一、xxx）作备用主题
        entries.append({
            "id": eid, "title": title,
            "evidence": field("证据"),
            "source": field("出处"),
            "cutoff": field("数据截止"),
            "boundary": field("适用边界"),
            "conflict": field("冲突或印证"),
            "lesson": field("反面教训"),
            "verify": field("三验记录"),
            "used": field("使用后印证"),
        })
    return entries

all_entries = []
for pre in ("ZP", "MG", "QS"):
    es = parse_book(pre)
    assert len(es) > 0, pre + " 解析为空"
    all_entries.extend(es)
print("规律条目解析:", len(all_entries))

# ---------- 2. 合并总库：主题归属 + 互证组 ----------
merged = read(os.path.join(WS, "S3_规律条目库.md"))
theme_map = {}   # id -> 合并库八大主题
cur_theme = None
for line in merged.split("\n"):
    tm = re.match(r"##\s*[①②③④⑤⑥⑦⑧\d]+[、.]?\s*(.+?)（?\d*条", line)
    if tm:
        t = tm.group(1).strip()
        cur_theme = None if ("统计" in t or "总览" in t or "索引" in t) else t
        continue
    # 正文行中的条目ID也归入当前主题（覆盖互证块：块内ID在正文）
    if cur_theme:
        for i in re.findall(r"\b((?:ZP|MG|QS)-\d{2})\b", line):
            theme_map.setdefault(i, cur_theme)
# 互证块：### 【跨书互证 Mxx·...】 后的块内所有 ID 归组
mgroup_map = {}
cur_m = None
for line in merged.split("\n"):
    mm = re.match(r"###\s*【跨书互证\s*(M\d+)", line)
    if mm:
        cur_m = mm.group(1)
        continue
    if line.startswith("### "):
        cur_m = None if not re.match(r"###\s*【跨书互证", line) else cur_m
        continue
    if cur_m:
        for i in re.findall(r"\b((?:ZP|MG|QS)-\d{2})\b", line):
            mgroup_map.setdefault(i, cur_m)
print("主题归属:", len(theme_map), "| 互证组标记:", len(mgroup_map))

# ---------- 3. 大V交叉引用 ----------
xref = read(os.path.join(WS, "S3_大V交叉引用.md"))
xref_map = {}  # id -> "印证|冲突|互补"（可叠加）
for seg in re.split(r"\n###\s*\[", xref)[1:]:
    m = re.match(r"((?:ZP|MG|QS)-\d{2})\]", seg)
    if not m:
        continue
    eid = m.group(1)
    rels = []
    for kw in ("印证", "冲突", "互补"):
        if re.search(r"-\s*%s[：:]" % kw, seg):
            rels.append(kw)
    if rels:
        xref_map[eid] = "/".join(rels)
print("大V交叉标记:", len(xref_map))

# ---------- 4. 现象记录（降级条目；ZP=### Dxx · 格式，MG/QS=- Jxx · 列表格式） ----------
phen = []
for pre in ("ZP", "MG", "QS"):
    name = BOOKS[pre][0]
    p = os.path.join(WS, "S3_现象记录_%s.md" % name)
    if not os.path.exists(p):
        continue
    text = read(p)
    seen = set()
    # 格式A：### D01 · 标题（ZP）
    for blk in re.split(r"\n###\s*", text)[1:]:
        m = re.match(r"(D\d+)\s*·\s*(.+)", blk)
        if not m:
            continue
        phen.append({
            "id": "%s-%s" % (pre, m.group(1)), "title": m.group(2).strip()[:150],
            "detail": blk.strip()[:2000],
            "book": BOOKS[pre][1], "theme": "现象记录（未过三验）",
        })
        seen.add(m.group(1))
    # 格式B：- J01 · 内容（MG/QS 列表）
    for line in text.split("\n"):
        lm = re.match(r"-\s*([A-Z]\d{1,2})\s*·\s*(.+)", line.strip())
        if not lm or lm.group(1) in seen:
            continue
        phen.append({
            "id": "%s-%s" % (pre, lm.group(1)), "title": lm.group(2).strip()[:300],
            "detail": lm.group(2).strip()[:1500],
            "book": BOOKS[pre][1], "theme": "现象记录（未过三验）",
        })
        seen.add(lm.group(1))
print("现象记录条目:", len(phen))

# ---------- 5. 组装 JSON ----------
records = []
for e in all_entries:
    pre = e["id"][:2]
    records.append({
        "id": e["id"],
        "bk": "BK-%s-R%s" % (pre, e["id"][3:]),
        "book": BOOKS[pre][1],
        "scope": BOOKS[pre][2],
        "theme": theme_map.get(e["id"], "未分组"),
        "title": e["title"],
        "evidence": e["evidence"],
        "source": e["source"],
        "cutoff": e["cutoff"],
        "boundary": e["boundary"],
        "lesson": e["lesson"],
        "verify": e["verify"],
        "used": e["used"],
        "mgroup": mgroup_map.get(e["id"], ""),
        "xref": xref_map.get(e["id"], ""),
        "type": "规律",
    })
for ph in phen:
    pre = ph["id"][:2]
    num = re.sub(r"\D", "", ph["id"][3:]) or "00"
    records.append({
        "id": ph["id"], "bk": "BK-%s-E%s" % (pre, num),
        "book": ph["book"], "scope": "", "theme": ph["theme"],
        "title": ph["title"], "evidence": ph["detail"], "source": "",
        "cutoff": "", "boundary": "", "lesson": "", "verify": "",
        "mgroup": "", "xref": "", "type": "现象",
    })

# 统计
def count_by(key):
    d = {}
    for r in records:
        v = r[key] or "（无）"
        d[v] = d.get(v, 0) + 1
    return d
stats = {
    "total": len(records),
    "books": count_by("book"),
    "themes": count_by("theme"),
    "mgroups": len(set(v for v in mgroup_map.values())),
    "xref_cnt": len(xref_map),
}
print("总记录:", stats)

# ---------- 6. 写 JSON（供 HTML 内嵌与 Lint 复用） ----------
os.makedirs(OUT_DIR, exist_ok=True)
with io.open(os.path.join(OUT_DIR, "entries.json"), "w", encoding="utf-8") as f:
    json.dump({"records": records, "stats": stats}, f, ensure_ascii=False, indent=1)
print("entries.json 已写出")
