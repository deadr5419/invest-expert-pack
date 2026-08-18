# -*- coding: utf-8 -*-
"""生成 S3 A1 分半清单文件（6份）"""
import glob
import os

base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '02_章节拆解'))
ws = os.path.dirname(os.path.abspath(__file__))

books = ['周期估值与人性', '美股70年', '全球股市启示录']
made = []
for b in books:
    files = sorted(f for f in glob.glob(os.path.join(base, b, 'S2_*', '*.md'))
                   if ('提取' in os.path.basename(f) or '拆解' in os.path.basename(f)))
    total = sum(os.path.getsize(f) for f in files)
    target = total / 2
    groups, cur, acc = [], [], 0
    for f in files:
        cur.append(f)
        acc += os.path.getsize(f)
        if acc >= target:
            groups.append(cur)
            cur, acc = [], 0
    if cur:
        groups.append(cur)
    for i, g in enumerate(groups, 1):
        p = os.path.join(ws, 'A1_清单_%s_半%d.txt' % (b, i))
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(g) + '\n')
        made.append((os.path.basename(p), len(g)))

for name, n in made:
    print(name, n, 'files')
print('DONE', len(made))
