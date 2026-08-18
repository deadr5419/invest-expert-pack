# -*- coding: utf-8 -*-
"""stage0_ocr_post.py — OCR批产物后处理: 合并全书 + 清洗 + 页锚点
输入: 02_章节拆解/<书>/S0_ocr_raw/pXXXX-YYYY.md (batch_ocr.py 产物)
输出: 02_章节拆解/<书>/S0_合并本.md (清洗后全文, 带印刷页码注释锚点)
      02_章节拆解/<书>/S0_anchor.json (印刷页码锚点表)
      02_章节拆解/<书>/S0_验收报告.md
清洗规则:
  1) 公众号水印: 含"韭菜服务区"或"更多书籍请关注"的行 → 删
  2) 页眉页脚组合行: 书名重复行(美股70年1948~2018年美国股市行情复盘 / 全球股市启示录：行情脉络与板块轮动) 且无其他实义内容 → 删
  3) TextIn 云端图片链接 → [图表|待核] 占位(图题行保留)
  4) 保留 <!-- N --> 印刷页码注释 → 提取锚点
"""
import os, re, sys, json, glob

WATERMARK = ["韭菜服务区", "更多书籍请关注", "更多书集请关注"]
TITLE_PAT = {
    "美股70年": re.compile(r"^[\s>#*]*(美股70年)?(1948\s*[~～—\-–]{1,2}2018年美国股市行情复盘)?[\s\d]*$"),
    "全球股市启示录": re.compile(r"^[\s>#*]*(全球股市启示录)?([:：]\s*行情脉络与板块轮动)?[\s\d]*$"),
}
IMG_LINK = re.compile(r"!\[\]\(https://web-api\.textin\.com/ocr_image/[^)]*\)")
PAGE_ANCHOR = re.compile(r"<!--\s*(?:[第]?[\s\S]{0,30}?)?(\d{1,3})\s*-->")

def clean_book(book_key, raw_dir, out_dir, title_pat):
    files = sorted(glob.glob(os.path.join(raw_dir, "p*.md")))
    if not files:
        print(f"[跳过] {book_key}: 无批产物"); return
    merged, anchors, stats = [], [], {"wm": 0, "head": 0, "img": 0, "anchor": 0}
    for fp in files:
        txt = open(fp, encoding="utf-8").read()
        for ln in txt.splitlines():
            s = ln.strip()
            if any(w in s for w in WATERMARK):
                stats["wm"] += 1; continue
            body = re.sub(r"<!--.*?-->", "", s).replace("|", "").replace("#", "").replace(">", "").replace("*", "").strip()
            if body and title_pat.fullmatch(body) and len(body) < 40:
                stats["head"] += 1; continue
            new_ln = IMG_LINK.sub("[图表|待核]", ln)
            if new_ln != ln: stats["img"] += 1
            merged.append(new_ln)
        merged.append("")  # 批间分隔
    full = "\n".join(merged)
    # 页锚点: 注释中独立的1-3位数字(印刷页码)
    for m in re.finditer(r"<!--\s*([^\d>]{0,28}?)(\d{1,3})\s*-->", full):
        ctx, pg = m.group(1).strip(), int(m.group(2))
        if 1 <= pg <= 520:
            anchors.append({"char_off": m.start(), "print_page": pg, "ctx": ctx[:20]})
            stats["anchor"] += 1
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "S0_合并本.md"), "w", encoding="utf-8").write(full)
    json.dump({"book": book_key, "anchors": anchors}, open(os.path.join(out_dir, "S0_anchor.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    body_only = re.sub(r"<!--.*?-->", "", full)
    body_only = re.sub(r"<[^>]+>|\s", "", body_only)
    bad = len(re.findall(r"[\uFFFD\u25A1\u25AF]", body_only))
    rep = [f"# OCR后处理验收 · {book_key}", "",
           f"- 批产物: {len(files)} 个 | 合并后字符: {len(body_only):,}",
           f"- 清洗: 水印行 {stats['wm']} | 书名页眉行 {stats['head']} | 图片链接转占位 {stats['img']}",
           f"- 印刷页码锚点: {stats['anchor']} 处 (覆盖率 {stats['anchor']/len(files)*100:.0f}%批次均摊)",
           f"- 乱码字符: {bad} ({bad/max(len(body_only),1)*100:.3f}%)",
           f"- [图表|待核] 占位: {stats['img']} 处 (图表数据一律待核, 不进正文)"]
    open(os.path.join(out_dir, "S0_验收报告.md"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
    print(f"[完成] {book_key}: {len(files)}批 | 正文字符{len(body_only):,} | 锚点{stats['anchor']} | 水印清{stats['wm']}行 | 乱码{bad}")

if __name__ == "__main__":
    BASE = r"C:\Users\Administrator\Desktop\市场研究\大V研究\书籍蒸馏\02_章节拆解"
    clean_book("美股70年", os.path.join(BASE, "美股70年", "S0_ocr_raw"), os.path.join(BASE, "美股70年"), TITLE_PAT["美股70年"])
    clean_book("全球股市启示录", os.path.join(BASE, "全球股市启示录", "S0_ocr_raw"), os.path.join(BASE, "全球股市启示录"), TITLE_PAT["全球股市启示录"])
