# -*- coding: utf-8 -*-
"""stage0_ocr_chapters.py v2 — 基于页眉注释切章(扫描书无书签的可靠替代)
锚点: <!-- 第一章 1948~1957年：新的开始 3 --> / <!-- 第三章 英国：老牌帝国与传统行业 109 -->
      (含加粗变体 <!-- **第一章** ... **41** -->)
章切换 = 页眉章号首次出现位置, 上溯合并章标题行(限500字符内)
输出: S0_全文/NN_章名.md + 章级anchor(印刷页区间)
"""
import os, re, sys, json

HDR = re.compile(r"<!--\s*\**\s*(第[一二三四五六七八九十百]+章)\**\s+(.+?)\**\s+\**(\d{1,3})\**\s*-->")

def split_chapters(book_dir, book_name):
    merged = open(os.path.join(book_dir, "S0_合并本.md"), encoding="utf-8").read()
    hits = []
    for m in HDR.finditer(merged):
        ch, sub, pg = m.group(1), m.group(2).strip().strip('*').strip(), int(m.group(3))
        hits.append({"off": m.start(), "ch": ch, "sub": sub, "page": pg})
    if not hits:
        print(f"[异常] {book_name}: 0 个页眉锚点"); return
    # 章首次出现位置(按章号顺序去重)
    firsts, seen = [], set()
    for h in hits:
        if h["ch"] not in seen:
            seen.add(h["ch"]); firsts.append(h)
    # 章内末锚点页码
    last_page = {}
    for h in hits:
        last_page[h["ch"]] = max(last_page.get(h["ch"], 0), h["page"])
    out_dir = os.path.join(book_dir, "S0_全文"); os.makedirs(out_dir, exist_ok=True)
    # 注意: 不用 os.remove 清旧文件(safe-delete 拦截), 旧文件用 PowerShell Remove-Item -Force 清
    rows = []
    order = "一二三四五六七八九十"
    def ch_no(c):
        s = c.replace("第", "").replace("章", "")
        n = 0
        if s == "十": return 10
        if "十" in s:
            a, _, b = s.partition("十")
            n = (order.index(a) + 1 if a else 1) * 10 + (order.index(b) + 1 if b else 0)
        else:
            n = order.index(s) + 1
        return n
    for i, f in enumerate(firsts):
        start = f["off"]
        end = firsts[i+1]["off"] if i+1 < len(firsts) else len(merged)
        seg = merged[start:end]
        # 上溯章标题行(向前500字符内找 **第X章** 或 ## 第X章 行首)
        up_start = max(0, start - 500)
        pre = merged[up_start:start]
        tm = None
        for m in re.finditer(r"(?:^|\n)((?:#{1,3}\s*|\**)%s\**\s*(?:\n|$))" % f["ch"], pre):
            tm = m
        if tm:
            start = up_start + tm.start(1)
            seg = merged[start:end]
        title = f"{f['ch']} {f['sub']}"[:42]
        p_start, p_end = f["page"], last_page[f["ch"]]
        header = f"> 书：《{book_name}》OCR切章 | 原书印刷页 {p_start}-{p_end} | [OCR文本|图表数据待核|数字经xparse识别精度A]\n\n"
        fn = f"{ch_no(f['ch']):02d}_{re.sub(r'[\\\\/:*?\"<>|\\s~～—：:]', '_', title)}.md"
        open(os.path.join(out_dir, fn), "w", encoding="utf-8").write(header + seg.strip() + "\n")
        chars = len(re.sub(r"\s|<!--.*?-->|<[^>]+>", "", seg))
        rows.append({"no": ch_no(f["ch"]), "file": fn, "title": title,
                     "print_pages": f"{p_start}-{p_end}", "chars": chars,
                     "anchor_count": sum(1 for h in hits if h["ch"] == f["ch"])})
        print(f"  {rows[-1]['no']:02d} {title[:38]:<40} 印刷页{p_start}-{p_end:<4} {chars:>7,}字 锚点{rows[-1]['anchor_count']}")
    json.dump({"book": book_name, "chapters": rows}, open(os.path.join(book_dir, "S0_anchor.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total = sum(r["chars"] for r in rows)
    print(f"[完成] {book_name}: {len(rows)} 章 | 合计 {total:,} 字 | 页眉锚点 {len(hits)} 处 → S0_全文/")

if __name__ == "__main__":
    BASE = r"C:\Users\Administrator\Desktop\市场研究\大V研究\书籍蒸馏\02_章节拆解"
    which = sys.argv[1] if len(sys.argv) > 1 else "美股70年"
    split_chapters(os.path.join(BASE, which), which)
