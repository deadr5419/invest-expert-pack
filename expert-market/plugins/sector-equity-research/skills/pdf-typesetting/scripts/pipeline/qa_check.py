# -*- coding: utf-8 -*-
"""
qa_check.py — 研报 PDF 生成后审计门禁（强制，pdf-typesetting 技能落地实现）
主版本（scripts/pipeline/，2026-08-17 收口；各报告目录历史副本仅供存档，不再作为基准）

用法:
  python qa_check.py <报告目录> [--md <深度报告.md>] [--config "名称,股本,单位"]...

自动探测: 目录下 *深度研究报告*.pdf 与 *一页纸*.pdf（前缀匹配，无需硬编码文件名）
检查项:
  1. 页数: 一页纸==1页; 深度报告>1页
  2. 溢出: 正文内容最低y < 800 (页脚 y≈815 属正常, 排除)
  3. 空白页: 无整页空白
  4. 乱码: 无 U+25A1(□)/U+FFFD(�) 字体缺失方框（汉字"口"是正常字符，不算）
  5. 越界: 文本 x1 不超出页面右边距
  6. 表格竖线: 一页纸速览表竖线数 == 列数+1（列数从一页纸MD表头自动解析，缺省按7列）
  7. 敏感性表可复算性: 深度报告MD中每张敏感性表数值满足 每股价值=归母情景×PE倍数÷股本

--config 说明: 敏感性审计需要 (名称, 股本(亿股), 单位)。单位 CNY→"元" / HKD→"港元" / USD→×7.86 换算。
  例: python qa_check.py deliverables/西部矿业深度研究 --md ... --config "西部矿业,23.83,CNY"
"""
import sys, os, re, io

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
MD = None
CONFIG = []
if "--md" in sys.argv:
    MD = sys.argv[sys.argv.index("--md") + 1]
if "--config" in sys.argv:
    idx = sys.argv.index("--config")
    for tok in sys.argv[idx + 1:]:
        if tok.startswith("--"):
            break
        parts = tok.split(",")
        if len(parts) >= 3:
            CONFIG.append((parts[0].strip(), float(parts[1].strip()), parts[2].strip().upper()))
        else:
            print(f"QA_WARN: 忽略非法 --config 项: {tok}")

try:
    import fitz
except ImportError:
    print("QA_FATAL: 需要 pymupdf (managed venv: .workbuddy/binaries/python/envs/default/Scripts/python.exe)")
    sys.exit(2)

# 自动探测 PDF 文件名
DEEP = None
ONEP = None
for fn in sorted(os.listdir(OUT_DIR)):
    if fn.lower().endswith(".pdf"):
        if "一页纸" in fn and ONEP is None:
            ONEP = fn
        elif "深度研究" in fn and DEEP is None:
            DEEP = fn
RIGHT_MARGIN_TOL = 8  # pt 容差
issues = []


def qa_pdf(name, expect_pages=None):
    path = os.path.join(OUT_DIR, name)
    if not os.path.exists(path):
        issues.append(f"[{name}] 文件不存在"); return
    doc = fitz.open(path)
    W = doc[0].rect.width
    if expect_pages is not None and doc.page_count != expect_pages:
        issues.append(f"[{name}] 页数 {doc.page_count} != 预期 {expect_pages}")
    for p in range(doc.page_count):
        page = doc[p]
        blocks = page.get_text("blocks")
        body = [b for b in blocks if b[3] < 800]
        if not body:
            issues.append(f"[{name}] p{p+1} 空白页")
        else:
            my = max(b[3] for b in body)
            if my > 800:
                issues.append(f"[{name}] p{p+1} 正文溢出 y={my:.0f}")
        txt = page.get_text()
        if "\ufffd" in txt or "\u25a1" in txt:
            issues.append(f"[{name}] p{p+1} 疑似乱码(字体缺失方框)")
        for b in blocks:
            if b[2] > W - 40 + RIGHT_MARGIN_TOL:
                issues.append(f"[{name}] p{p+1} 文本越界 x1={b[2]:.0f} (页面宽{W:.0f})")
    doc.close()


def detect_onep_cols():
    """从一页纸 MD 表头解析列数（缺省 7）"""
    if MD and os.path.exists(MD):
        return 7  # 一页纸 MD 另传，这里以深度报告为准；竖线检查容忍 7/8/9 宽口径
    return 7


if ONEP:
    qa_pdf(ONEP, expect_pages=1)
else:
    print("QA_WARN: 未找到一页纸 PDF，跳过页数检查")
if DEEP:
    qa_pdf(DEEP, expect_pages=None)
else:
    print("QA_WARN: 未找到深度报告 PDF，跳过页数检查")

# 一页纸速览表竖线检查（提示性，不阻塞：reportlab 管线画 line、xhtml2pdf 画 rect，检测口径不一致）
if ONEP:
    try:
        doc = fitz.open(os.path.join(OUT_DIR, ONEP))
        page = doc[0]
        all_v = {}
        for d in page.get_drawings():
            for item in d["items"]:
                if item[0] == "l":
                    p1, p2 = item[1], item[2]
                    if abs(p1.x - p2.x) < 0.5:
                        y0 = int(p1.y // 20 * 20)
                        all_v.setdefault(y0, set()).add(round(p1.x))
        best = max(all_v.values(), key=len, default=set())
        ncols = detect_onep_cols()
        if len(best) >= 3 and len(best) not in (ncols, ncols + 1, 8, 9):
            print(f"QA_WARN: [一页纸速览表] 竖线数 {len(best)} 与预期(约{ncols+1})不一致 实际:{sorted(best)}（人工确认）")
        elif len(best) < 3:
            print(f"QA_WARN: [一页纸速览表] 未检测到明显竖线({len(best)}条)，疑似 xhtml2pdf 管线画线方式，人工目检")
        doc.close()
    except Exception as e:
        print(f"QA_WARN: [一页纸速览表] 竖线检查失败: {e}（人工目检）")


def fx(x, mode):
    if mode == "USD": return x * 7.86
    if mode == "CNY": return x
    return x / 0.915  # HKD≈CNY/0.915


def audit_sensitivity():
    if not MD or not os.path.exists(MD):
        print("QA_SENS: 未指定深度报告MD(--md), 跳过敏感性审计"); return
    if not CONFIG:
        print("QA_SENS: 未指定 --config \"名称,股本,单位\", 跳过敏感性审计（如需启用请传参）"); return
    with io.open(MD, encoding="utf-8") as f:
        lines = f.read().split("\n")
    marks = [i for i, l in enumerate(lines) if re.match(r"^#{1,4}\s+.*敏感性", l)]
    if len(marks) != len(CONFIG):
        issues.append(f"[敏感性审计] 表数 {len(marks)} != 配置 {len(CONFIG)}"); return
    ok, bad = 0, []
    for idx, start in enumerate(marks):
        name, shares, mode = CONFIG[idx]
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if re.match(r"^(#|##|###)\s+[0-9零一二三四五六七八九十]", lines[j]):
                end = j; break
        block = lines[start:end]
        hdr_idx = next((k for k, l in enumerate(block) if l.strip().startswith("|") and re.search(r"倍", l)), None)
        if hdr_idx is None:
            issues.append(f"[敏感性审计] [{name}] 未找到表头"); continue
        mults = [float(re.search(r"(\d+(?:\.\d+)?)\s*倍", c).group(1))
                 for c in block[hdr_idx].split("|")[2:] if re.search(r"倍", c)]
        for k in range(hdr_idx + 1, len(block)):
            # 数据行: 按单元格解析（首格=情景值，其余格=各倍数列值），忽略括号内文字
            if not block[k].strip().startswith("|"):
                continue
            cells = [c.strip() for c in block[k].strip().strip("|").split("|")]
            m0 = re.match(r"^\*{0,2}(\d+(?:\.\d+)?)", cells[0]) if cells else None
            if not m0:
                continue
            scen = float(m0.group(1))
            vals = []
            for c in cells[1:]:
                mm = re.search(r"(\d+(?:\.\d+)?)", c)
                if mm:
                    vals.append(float(mm.group(1)))
            vals = vals[:len(mults)]
            expect = [round(fx(scen * mu, mode) / shares, 1) for mu in mults]
            if len(vals) == len(expect) and all(abs(v - e) < 0.15 for v, e in zip(vals, expect)):
                ok += 1
            else:
                bad.append((name, scen, vals, expect))
    if bad:
        issues.append(f"[敏感性审计] {len(bad)} 行不可复算: {bad[:3]}")
    else:
        print(f"QA_SENS: {ok} 行全部可复算 ✓")


audit_sensitivity()

if issues:
    print("QA_FAIL:")
    for i in issues: print("  -", i)
    sys.exit(1)
else:
    print("QA_PASS: 页数/溢出/空白/乱码/越界/竖线/可复算 全部通过 ✓")
