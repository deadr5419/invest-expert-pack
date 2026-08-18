# -*- coding: utf-8 -*-
"""P0-5 侦查：提取两包全部技能 description，识别冗余候选"""
import io, os, re

base = r'C:/Users/Administrator/.workbuddy/plugins/marketplaces/my-experts/plugins'
packs = ['st-zhongtai-ic', 'sector-equity-research']

def get_desc(path):
    txt = io.open(path, encoding='utf-8').read()
    fm = txt.split('---', 2)
    if len(fm) < 2:
        return '(无frontmatter)'
    m = re.search(r'description:\s*[|>\-]?\s*\n?\s*(.+?)(?=\n---|\n\w+:|\Z)', fm[1], re.S)
    if not m:
        return '(无description)'
    d = m.group(1).strip().strip('|').strip().strip('"')
    d = re.sub(r'\s+', ' ', d)
    return d[:170]

allinfo = {}
for pack in packs:
    sk = os.path.join(base, pack, 'skills')
    print('=' * 15, pack, '=' * 15)
    for s in sorted(os.listdir(sk)):
        f = os.path.join(sk, s, 'SKILL.md')
        if not os.path.exists(f):
            continue
        d = get_desc(f)
        allinfo.setdefault(s, {})[pack] = d
        print(' [%s] %s' % (s, d))

# 两包差异
print('\n=== 两包技能差异 ===')
ic = set(os.listdir(os.path.join(base, packs[0], 'skills')))
ser = set(os.listdir(os.path.join(base, packs[1], 'skills')))
print('仅IC有:', sorted(ic - ser - {'.neodata_token'}))
print('仅SER有:', sorted(ser - ic))
