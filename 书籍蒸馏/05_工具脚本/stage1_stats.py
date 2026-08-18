# -*- coding: utf-8 -*-
"""
阶段1 · 客观统计卡脚本
指标：字数 / 数字密度（每千字数字串数）/ 结论句密度（方法论关键词句占比）/ 图表引用数
用法：python stage1_stats.py <S0目录>
输出：<S0目录>/S1_统计卡.md
"""
import sys, os, re, json, glob

KEYWORDS = ['规律', '本质', '核心', '因此', '所以', '启示', '经验', '教训', '不变', '策略',
            '框架', '逻辑', '总结', '规律性', '特征', '共性', '牛市', '熊市', '风格', '切换',
            '估值', '周期', '主线', 'muscle', '记忆']

def strip_meta(txt: str) -> str:
    """跳过头部 > 开头的元信息行与空行（文本版4行/OCR版1行通吃）"""
    lines = txt.split('\n')
    i = 0
    while i < len(lines) and (lines[i].startswith('>') or not lines[i].strip()):
        i += 1
    return '\n'.join(lines[i:])

def main():
    s0_dir = sys.argv[1]
    anchor = json.load(open(os.path.join(s0_dir, 'S0_anchor.json'), encoding='utf-8'))
    rows = []
    for ch in anchor['chapters']:
        fp = os.path.join(s0_dir, 'S0_全文', ch['file'])
        if not os.path.exists(fp):
            continue
        txt = open(fp, encoding='utf-8').read()
        body = strip_meta(txt)
        chars = len(body)
        nums = len(re.findall(r'\d+(\.\d+)?%?', body))
        sents = [s for s in re.split(r'[。！？]', body) if len(s) > 8]
        kw_hits = sum(1 for s in sents if any(k in s for k in KEYWORDS))
        figs = len(re.findall(r'[表图]\s*\d+', body))
        num_den = nums / max(chars / 1000, 0.1)
        kw_den = kw_hits / max(len(sents), 1) * 100
        pages = ch.get('print_pages') or '-'.join(map(str, ch.get('pdf_page_1based', ['?', '?'])))
        rows.append((ch['no'], ch['title'], pages, chars,
                     round(num_den, 1), f'{kw_den:.1f}%', figs))
    book = anchor.get('book', os.path.basename(s0_dir))
    with open(os.path.join(s0_dir, 'S1_统计卡.md'), 'w', encoding='utf-8') as f:
        f.write(f'# S1 客观统计卡 · {book}\n\n'
                '| # | 章节 | 原书页 | 字数 | 数字/千字 | 方法论句% | 图表引 |\n'
                '|---|---|---|---|---|---|---|\n')
        for r in sorted(rows):
            f.write(f'| {r[0]} | {r[1]} | {r[2]} | {r[3]:,} | {r[4]} | {r[5]} | {r[6]} |\n')
    print('统计卡完成', len(rows), '章')

if __name__ == '__main__':
    main()
