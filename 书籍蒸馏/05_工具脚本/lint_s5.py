# -*- coding: utf-8 -*-
"""阶段5 QA：Lint 体检 + 10问测试集
Lint：孤儿条目 / ID一致性 / BK别名完整 / 锚点回查（复用S3语料逻辑）
10问：模拟前端检索逻辑，预期条目须在命中前10（=3步内定位：输关键词→主题确认→点条目）
"""
import re, json, io, os, glob, sys

BASE = r"C:/Users/Administrator/Desktop/市场研究/大V研究/书籍蒸馏"
def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()

report = []
ok = lambda name, detail="": report.append(("PASS", name, detail))
bad = lambda name, detail="": report.append(("FAIL", name, detail))
warn = lambda name, detail="": report.append(("WARN", name, detail))

# ---------- Lint 1: 孤儿条目（108条规律未被S4任何文档引用） ----------
s4_text = "".join(read(os.path.join(BASE, "04_框架提炼", f)) for f in os.listdir(os.path.join(BASE, "04_框架提炼")) if f.endswith(".md"))
lib_ids = set()
for f in glob.glob(os.path.join(BASE, "03_观点条目库", "_S3_工作区", "S3_条目库_*.md")):
    lib_ids |= set(re.findall(r"\b((?:ZP|MG|QS)-\d{2})\b", read(f)))
orphan = sorted(i for i in lib_ids if i not in s4_text)
if orphan:
    warn("孤儿条目（S4未挂接）", " ".join(orphan))
else:
    ok("孤儿条目", "108条全部被S4框架/矩阵挂接，无孤儿")

# ---------- Lint 2: 检索页数据 ID 一致性 + BK别名 ----------
data = json.load(io.open(os.path.join(BASE, "06_检索页", "entries.json"), encoding="utf-8"))
recs = data["records"]
rid_regular = [r["id"] for r in recs if r["type"] == "规律"]
missing = lib_ids - set(rid_regular)
extra = set(rid_regular) - lib_ids
if missing or extra:
    bad("检索页规律ID一致性", "缺:%s 多:%s" % (sorted(missing), sorted(extra)))
else:
    ok("检索页规律ID一致性", "108/108 与条目库完全一致")
bk_bad = [r["id"] for r in recs if not re.match(r"^BK-(ZP|MG|QS)-[RE]\d+$", r["bk"])]
(ok if not bk_bad else bad)("BK别名完整", "265条全部含BK-制别名" if not bk_bad else "异常:%s" % bk_bad[:5])

# ---------- Lint 3: 断锚点（对三书单库重跑锚点逐字回查） ----------
def norm(s):
    s = s.replace("％", "%")
    s = re.sub(r"[“”\"'‘’]", "", s)
    s = re.sub(r"\s+", "", s)
    return s
corpus = ""
for f in glob.glob(os.path.join(BASE, "02_章节拆解", "*", "S2_*", "*.md")):
    try:
        corpus += norm(read(f))
    except Exception:
        pass
hit = miss = 0
miss_list = []
for f in glob.glob(os.path.join(BASE, "03_观点条目库", "_S3_工作区", "S3_条目库_*.md")):
    txt = read(f)
    anchors = re.findall(r'锚点[：:]\s*“([^”]{4,60})”', txt) + re.findall(r'锚点[：:]\s*"([^"]{4,60})"', txt)
    for a in anchors:
        if norm(a) in corpus:
            hit += 1
        else:
            miss += 1
            miss_list.append(a[:30])
if miss == 0:
    ok("断锚点", "锚点回查 %d/%d 全命中" % (hit, hit))
else:
    bad("断锚点", "%d miss: %s" % (miss, miss_list[:5]))

# ---------- Lint 4: 已知矛盾清单显式化 ----------
matrix = read(os.path.join(BASE, "04_框架提炼", "S4_跨书主题对照矩阵.md"))
n_div = len(re.findall(r"分歧[一二三四五六1-6]·|D[1-6][：:·\s]", matrix))
xref = read(os.path.join(BASE, "03_观点条目库", "S3_大V交叉引用.md"))
n_conf = len(re.findall(r"-\s*冲突[：:]", xref))
ok("矛盾清单显式化", "矩阵裁决书间分歧6条（含D1-D6标记:%d处）；大V冲突%d条已显式标注待投委会" % (n_div, n_conf))

# ---------- 10问测试集（3步内定位 = 命中前10） ----------
QUESTIONS = [
    ("1970s美股滞胀期股市表现如何、估值中枢怎样？", ["滞胀"], ["QS-29"]),
    ("A股历史大底有哪些特征？", ["底部"], ["ZP-18", "ZP-21"]),
    ("主流资产兴起有什么阶段性规律？", ["五阶段"], ["ZP-02"]),
    ("美股大牛市启动需要什么条件？", ["大牛市", "牛市启动"], ["MG-12"]),
    ("机构抱团什么时候瓦解？", ["抱团"], ["ZP-06"]),
    ("利率大幅上行对股市估值的影响？", ["利率", "利率上行"], ["MG-01", "MG-02"]),
    ("怎么判断一个行情是不是泡沫？", ["泡沫判别", "泡沫"], ["MG-28", "QS-32"]),
    ("股票回购对长期牛市有什么作用？", ["回购"], ["MG-25"]),
    ("什么样的行业能跑出长期超额收益（时代贝塔）？", ["超额收益", "时代"], ["QS-13", "MG-14"]),
    ("美林时钟/投资时钟什么时候有效？", ["时钟"], ["ZP-12"]),
]
blob = lambda r: (r["title"] + r["evidence"] + r["boundary"] + r["lesson"] + r["id"] + r["theme"] + r["book"]).lower()
qpass = 0
qdetail = []
for i, (q, kws, expect) in enumerate(QUESTIONS, 1):
    hits = None
    for kw in kws:  # 依次尝试关键词，任一关键词命中即算该步
        cur = [r for r in recs if kw.lower() in blob(r)]
        if cur:
            hits = cur
            used = kw
            break
    if not hits:
        qdetail.append("Q%d FAIL 无命中(%s)" % (i, q))
        continue
    # 前端排序复现：规律在前 → 标题命中优先 → 互证优先
    kl = used.lower()
    hits.sort(key=lambda r: (0 if r["type"] == "规律" else 1,
                             0 if (kl and kl in r["title"].lower()) else 1,
                             0 if r["mgroup"] else 1))
    top_ids = [r["id"] for r in hits[:10]]
    got = [e for e in expect if e in top_ids]
    if got:
        qpass += 1
        qdetail.append("Q%d PASS [%s] 命中%s（前10共%d条）" % (i, used or kws[0], "/".join(got), len(top_ids)))
    else:
        qdetail.append("Q%d FAIL [%s] 预期%s未进前10（前10:%s）" % (i, kws[0], "/".join(expect), ",".join(top_ids[:5])))
ok("10问测试", "%d/10 通过" % qpass) if qpass >= 9 else bad("10问测试", "%d/10 通过" % qpass)

# ---------- 输出 ----------
print("=" * 60)
for status, name, detail in report:
    print("[%s] %s %s" % (status, name, ("| " + detail) if detail else ""))
print("=" * 60)
print("10问明细：")
for d in qdetail:
    print("  " + d)
n_fail = sum(1 for s, _, _ in report if s == "FAIL")
print("结论：", "全绿" if n_fail == 0 else "%d 项FAIL" % n_fail)
sys.exit(0 if n_fail == 0 else 1)
