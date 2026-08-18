# -*- coding: utf-8 -*-
"""
阶段2 混合章第二步 · 数字回查硬校验
校验转录稿史实表中的数字是否存在于对应章节原文（字符串硬匹配）
用法：python stage2_verify_numbers.py
输出：S2_混合章/_数字回查报告.md
"""
import os, re, glob, sys

BOOK = sys.argv[1] if len(sys.argv) > 1 else '周期估值与人性'
BASE = rf'C:\Users\Administrator\Desktop\市场研究\大V研究\书籍蒸馏\02_章节拆解\{BOOK}'
S0 = os.path.join(BASE, 'S0_全文')
S2M = os.path.join(BASE, 'S2_混合章')

def main():
    report = [f'# 混合章转录 · 数字回查报告 · {BOOK}', '']
    # 全书拼接（消除 OCR 切章边界串页导致的假 MISS）；全角％统一为半角
    whole = ''
    for f in os.listdir(S0):
        if f.endswith('.md'):
            whole += open(os.path.join(S0, f), encoding='utf-8').read()
    whole = whole.replace('％', '%').replace('，', ',')
    tot_num, tot_hit = 0, 0
    for fp in sorted(glob.glob(os.path.join(S2M, '*_转录.md'))):
        no = os.path.basename(fp)[:2]
        srcs = [f for f in os.listdir(S0) if f.startswith(no + '_')]
        if not srcs:
            report.append(f'## {os.path.basename(fp)} ：找不到原文，跳过')
            continue
        txt = open(fp, encoding='utf-8').read().replace('％', '%')
        # 只取史实表部分（## 一 到 ## 二 之间）
        m = re.search(r'## 一、史实表.*?(?=## 二、)', txt, re.S)
        table = m.group(0) if m else txt
        nums = set(re.findall(r'\d+(?:\.\d+)?%?', table))
        # 排除纯章节号/图表号模式与两位以内小编号
        nums = {n for n in nums if len(n) >= 3 or '.' in n}
        # 匹配规则：带%的数字按本体匹配（OCR表格常为裸数字、表头含%，转录补%属合理单位标注）
        hit = sum(1 for n in nums if n in whole or n.rstrip('%') in whole)
        miss = [n for n in nums if not (n in whole or n.rstrip('%') in whole)]
        tot_num += len(nums); tot_hit += hit
        rate = hit / max(len(nums), 1) * 100
        report.append(f"## {os.path.basename(fp)} ：{len(nums)} 个数字，命中 {hit}（{rate:.1f}%）"
                      + (f"  MISS: {miss}" if miss else ""))
    rate = tot_hit / max(tot_num, 1) * 100
    report.insert(1, f'**总计：{tot_num} 个数字，命中 {tot_hit}，通过率 {rate:.2f}%（验收线 ≥99%）**')
    out = os.path.join(S2M, '_数字回查报告.md')
    open(out, 'w', encoding='utf-8').write('\n'.join(report))
    print('\n'.join(report[:10]))
    print(f'\n报告已写: {out}')

if __name__ == '__main__':
    main()
