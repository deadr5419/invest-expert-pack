# -*- coding: utf-8 -*-
"""
阶段0 · 原文规范化脚本（文本版管线）
功能：按 PDF 书签切章 → 清洗（去页码/水印）→ 输出 S0 逐章 MD + 章-页锚点 JSON + 验收报告
用法：python stage0_normalize.py <书名代码> <PDF路径> <输出目录>
产物：
  <输出目录>/S0_全文/NN_章节名.md          逐章洁净全文（含页码锚点标记）
  <输出目录>/S0_anchor.json               章-页码区间映射（机器可读）
  <输出目录>/S0_验收报告.md               乱码率/空章/字数统计
"""
import sys, json, re, os
import pymupdf

def clean_text(raw: str) -> str:
    """清洗：去行首尾空白、去独立页码行、去常见水印行"""
    lines = raw.split('\n')
    out = []
    for ln in lines:
        s = ln.strip()
        if not s:
            out.append('')
            continue
        if re.fullmatch(r'\d{1,4}', s):          # 独立页码行
            continue
        if re.fullmatch(r'[-—–_\s]{2,}', s):     # 分隔线
            continue
        if '微信' in s and ('公众号' in s or '扫码' in s):
            continue                              # 公众号水印
        if s.startswith('本书由') or '扫码关注' in s:
            continue
        out.append(s)
    txt = '\n'.join(out)
    txt = re.sub(r'\n{3,}', '\n\n', txt)          # 压缩连续空行
    return txt.strip()

def main():
    book_code, pdf_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    doc = pymupdf.open(pdf_path)
    toc = doc.get_toc()
    print(f'书签条数: {len(toc)}')

    # 只取一级章节（level==1），个别书可能有 level 2 小节，一级足够切章
    chapters = [(lvl, title, page) for lvl, title, page in toc]
    lvl1 = [(t, p) for l, t, p in chapters if l == 1]
    print(f'一级章节: {len(lvl1)}')

    os.makedirs(os.path.join(out_dir, 'S0_全文'), exist_ok=True)
    anchor = {'book_code': book_code, 'total_pages': doc.page_count, 'chapters': []}
    report = []
    for i, (title, p_start) in enumerate(lvl1, 1):
        p_end = (lvl1[i][1] - 1) if i < len(lvl1) else doc.page_count  # 下一章起始页-1（书签页为1基）
        pg_from = max(p_start - 1, 0)   # 转0基
        pg_to = min(p_end, doc.page_count)
        raw = ''.join(doc[pg].get_text() for pg in range(pg_from, pg_to))
        txt = clean_text(raw)
        # 安全文件名
        safe = re.sub(r'[\\/:*?"<>|·、\s]+', '_', title)[:40]
        fname = f'{i:02d}_{safe}.md'
        header = (f'# {title}\n\n'
                  f'> 书：{book_code} | 章 {i} | 原书页码 {p_start}-{p_end}（书签页）\n\n')
        with open(os.path.join(out_dir, 'S0_全文', fname), 'w', encoding='utf-8') as f:
            f.write(header + txt + '\n')
        # 乱码检测：替换符与私用区字符
        bad = sum(1 for ch in txt if ch == '\ufffd' or 0xE000 <= ord(ch) <= 0xF8FF)
        rate = bad / max(len(txt), 1) * 100
        report.append((fname, title, p_start, p_end, len(txt), rate))
        anchor['chapters'].append({'no': i, 'title': title, 'pdf_page_1based': [p_start, p_end],
                                   'chars': len(txt), 'file': fname})
    with open(os.path.join(out_dir, 'S0_anchor.json'), 'w', encoding='utf-8') as f:
        json.dump(anchor, f, ensure_ascii=False, indent=1)

    # 验收报告
    total_chars = sum(r[4] for r in report)
    max_rate = max(r[5] for r in report)
    empty = [r[0] for r in report if r[4] < 200]
    with open(os.path.join(out_dir, 'S0_验收报告.md'), 'w', encoding='utf-8') as f:
        f.write(f'# S0 验收报告 · {book_code}\n\n'
                f'- 总页数 {doc.page_count}，切出章节 {len(report)}，总字数 {total_chars:,}\n'
                f'- 最高单章乱码率 {max_rate:.4f}%（阈值 0.1%）\n'
                f'- 疑似空章（<200字）：{empty if empty else "无"}\n\n'
                f'| # | 文件 | 原书页 | 字数 | 乱码率% |\n|---|---|---|---|---|\n')
        for fn, t, a, b, c, r in report:
            f.write(f'| {fn[:2]} | {t} | {a}-{b} | {c:,} | {r:.4f} |\n')
    print(f'完成：{len(report)} 章 | 总字数 {total_chars:,} | 最高乱码率 {max_rate:.4f}% | 空章 {len(empty)}')
    doc.close()

if __name__ == '__main__':
    main()
