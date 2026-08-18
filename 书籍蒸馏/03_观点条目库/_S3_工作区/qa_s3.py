# -*- coding: utf-8 -*-
"""S3 QA：schema完整性 + ID守恒 + 锚点逐字回查S0全文"""
import glob
import os
import re
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WS = os.path.join(BASE, '03_观点条目库', '_S3_工作区')
FINAL = os.path.join(BASE, '03_观点条目库', 'S3_规律条目库.md')

FIELDS = ['证据', '出处', '数据截止', '适用边界', '冲突或印证', '反面教训', '使用后印证', '三验记录']

# --- 1. 单书条目库 schema 完整性 ---
books = ['周期估值与人性', '美股70年', '全球股市启示录']
schema_fail = []
all_ids = []
for b in books:
    p = os.path.join(WS, 'S3_条目库_%s.md' % b)
    text = open(p, encoding='utf-8').read()
    blocks = re.split(r'\n(?=### \[)', text)
    n = 0
    for blk in blocks:
        m = re.match(r'### \[([ZMQ][PSG]-\d+)\]', blk)
        if not m:
            continue
        n += 1
        all_ids.append(m.group(1))
        for f in FIELDS:
            if ('- %s：' % f) not in blk and ('- %s:' % f) not in blk:
                schema_fail.append('%s 缺字段[%s]' % (m.group(1), f))
    print('%s: %d 条' % (b, n))

# --- 2. ID 守恒：最终库应含全部 108 ID ---
final_text = open(FINAL, encoding='utf-8').read()
missing = [i for i in all_ids if ('[%s]' % i) not in final_text]
print('ID守恒: %d/%d （缺失: %s）' % (len(all_ids) - len(missing), len(all_ids), missing or '无'))

# --- 3. 锚点逐字回查 S0 全文 ---
def norm(s):
    s = s.replace('％', '%')
    s = re.sub(r'[“”‘”"\']', '', s)
    s = re.sub(r'\s+', '', s)
    return s

corpus = {}
for b, d in [('周期估值与人性', '周期估值与人性'), ('美股70年', '美股70年'), ('全球股市启示录', '全球股市启示录')]:
    parts = []
    for pat in ['01_原文藏书/%s/**/*.md' % d, '02_章节拆解/%s/S0_全文/**/*.md' % d, '02_章节拆解/%s/S0_合并本.md' % d]:
        for f in glob.glob(os.path.join(BASE, pat), recursive=True):
            try:
                parts.append(open(f, encoding='utf-8').read())
            except Exception:
                pass
    corpus[b] = norm(''.join(parts))
    print('语料 %s: %d 字符' % (b, len(corpus[b])))

pre = {'Z': '周期估值与人性', 'M': '美股70年', 'Q': '全球股市启示录'}
hit = miss = 0
miss_list = []
# 逐条目回查（按条目所在书选语料）
entry_blocks = re.split(r'\n(?=### \[)', final_text)
for blk in entry_blocks:
    m = re.match(r'### \[([ZMQ])', blk)
    if not m:
        continue
    book = pre[m.group(1)]
    for a in re.findall(r'锚点[：:]\s*"([^"]{4,60})"', blk):
        na = norm(a)
        if any(na in corpus[b] for b in ('周期估值与人性', '美股70年', '全球股市启示录')):
            hit += 1
        else:
            miss += 1
            miss_list.append(a[:30])
print('锚点回查: 命中 %d / %d（命中率 %.1f%%）' % (hit, hit + miss, 100.0 * hit / max(1, hit + miss)))
for a in miss_list[:15]:
    print("  MISS", a)

print('schema缺失: %d 处' % len(schema_fail))
for s in schema_fail[:10]:
    print('  ', s)
print('QA_DONE')
