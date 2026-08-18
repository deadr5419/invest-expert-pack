# -*- coding: utf-8 -*-
"""convert_tail.py — Windows OCR尾批转换 + GBK乱码修复
1. tail_txt/pXXX.txt (Windows OCR) -> S0_ocr_raw/p0480-0501.md (xparse批产物格式)
   清洗: 去中文间空格 / 剔无汉字行(图表轴标签) / 修"图N一M" / 构造页眉注释锚点
2. 修复 p0468-0479.md 尾部 UTF-8→GBK 误解码段 (round-trip还原)
"""
import os, re

BASE = r'C:\Users\Administrator\Desktop\市场研究\大V研究\书籍蒸馏'
TXT_DIR = r'C:\mkt_ocr_tmp\tail_txt'
RAW_DIR = os.path.join(BASE, '02_章节拆解', '全球股市启示录', 'S0_ocr_raw')
CH_TITLE = '第十一章 价值投资分析框架总结'
PAGE_OFFSET = 11  # 印刷页码 = PDF页 - 11 (p479->468 已验证)

CJK = r'\u4e00-\u9fff'

def despace(s: str) -> str:
    """去除中文之间、中文与中文标点之间的空格"""
    s = re.sub(rf'(?<=[{CJK}]) +(?=[{CJK}])', '', s)
    s = re.sub(rf'(?<=[{CJK}]) +(?=[，。：；、！？“”（）])', '', s)
    s = re.sub(rf'(?<=[，。：；、！？“”（）]) +(?=[{CJK}])', '', s)
    return s

def clean_line(s: str) -> str:
    s = despace(s)
    s = re.sub(r'图(\s*\d+\s*)一(\s*\d+)', r'图\1-\2', s)  # 图11一9 -> 图11-9
    s = re.sub(r'表(\s*\d+\s*)一(\s*\d+)', r'表\1-\2', s)
    return s.strip()

def is_junk_line(s: str) -> bool:
    """无汉字的行 = 图表轴标签/页码/纯符号 -> 剔除"""
    body = re.sub(r'[\s\d.,%：:，。、；()（）\-—～~/|·]+', '', s)
    if not body:
        return True  # 纯数字符号
    if not re.search(f'[{CJK}]', s):
        return True  # 无任何汉字(字母/数字/符号行)
    if len(s) <= 2 and re.search(r'\d', s):
        return True  # 短噪声行(如"4河"页眉残迹)
    return False

def fix_gbk_mojibake(txt: str) -> tuple[str, int]:
    """round-trip修复UTF-8->GBK误解码段"""
    fixed_lines, nfix = [], 0
    for ln in txt.splitlines():
        if re.search(f'[{CJK}]', ln):
            try:
                b = ln.encode('gbk', errors='strict')
                restored = b.decode('utf-8', errors='strict')
                cjk_ratio = len(re.findall(f'[{CJK}]', restored)) / max(len(restored), 1)
                if cjk_ratio > 0.4:
                    fixed_lines.append(restored)
                    nfix += 1
                    continue
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        fixed_lines.append(ln)
    return '\n'.join(fixed_lines), nfix

# ---------- 1. 尾批转换 ----------
out_parts, stats = [], {'junk': 0, 'lines': 0}
for p in range(480, 502):
    fp = os.path.join(TXT_DIR, f'p{p}.txt')
    if not os.path.exists(fp):
        raise FileNotFoundError(fp)
    raw = open(fp, encoding='utf-8-sig').read()
    print_page = p - PAGE_OFFSET
    # 页眉注释锚点 (切章脚本依赖此格式)
    out_parts.append(f'<!-- {CH_TITLE} {print_page} -->')
    kept = []
    for ln in raw.splitlines():
        s = clean_line(ln)
        if not s:
            continue
        # 剔除页眉章名行/页脚书名行(已有统一锚点)
        if re.fullmatch(r'第十一章.*', s) or '全球股市启示录：行情脉络与板块轮动' == s:
            continue
        if is_junk_line(s):
            stats['junk'] += 1
            continue
        kept.append(s)
        stats['lines'] += 1
    # 图表页/近空页占位
    if not kept:
        out_parts.append('[图表|待核]')
    else:
        out_parts.append('\n'.join(kept))
    out_parts.append('')

tail_md = '\n'.join(out_parts)
out_fp = os.path.join(RAW_DIR, 'p0480-0501.md')
open(out_fp, 'w', encoding='utf-8').write(tail_md)
print(f'尾批转换完成 -> {out_fp}')
print(f'  保留正文行 {stats["lines"]} | 剔除图表标签/页码行 {stats["junk"]}')
print(f'  尾批字符数 {len(re.sub(chr(10), "", tail_md)):,}')

# ---------- 2. 修复 p0468-0479.md GBK乱码段 ----------
prev_fp = os.path.join(RAW_DIR, 'p0468-0479.md')
txt = open(prev_fp, encoding='utf-8').read()
fixed, nfix = fix_gbk_mojibake(txt)
if nfix:
    open(prev_fp, 'w', encoding='utf-8').write(fixed)
    print(f'GBK乱码修复: p0468-0479.md 还原 {nfix} 行')
else:
    print('GBK乱码修复: 未检出(可能已干净)')

# 顺手扫全书所有批产物有无同类乱码
import glob
total_susp = 0
for fp in sorted(glob.glob(os.path.join(RAW_DIR, 'p*.md'))):
    t = open(fp, encoding='utf-8').read()
    _, n = fix_gbk_mojibake(t)
    if n and os.path.basename(fp) != 'p0468-0479.md':
        open(fp, 'w', encoding='utf-8').write(_)
        print(f'  另修: {os.path.basename(fp)} 还原 {n} 行')
        total_susp += n
print(f'全书批产物乱码扫描完成, 另修复 {total_susp} 行')
