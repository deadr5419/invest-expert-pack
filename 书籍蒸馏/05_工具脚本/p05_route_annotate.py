# -*- coding: utf-8 -*-
"""P0-5 档1-②：westock/neodata 两技能×两包 SKILL.md 追加三源链路路由声明（幂等）"""
import io, os, hashlib

PLUGINS = r"C:/Users/Administrator/.workbuddy/plugins/marketplaces/my-experts/plugins"
PACKS = ["st-zhongtai-ic", "sector-equity-research"]

SEC = """

## 数据源路由（三源链路，2026-08-17 治理声明）

本技能是投委会流程内的数据查询入口，与其他数据源的分工如下（用户 2026-08-16 拍板的三源链路）：

| 层 | 数据源 | 定位 | 用途 |
|---|---|---|---|
| 实时层 | 本技能（westock / neodata） | 盘中/快照/分钟/自然语言搜索，免费无限 | 投委会高频查询主入口 |
| 批量层 | Tushare | 历史K线/财务/因子/回测 | 大批量历史数据 |
| 精核层 | Wind | H股/美股/宏观EDB/公告/权威背书 | 报告引用/权威核验（1000积分/天） |

**路由纪律**：能本技能覆盖的不用下层；Tushare 能覆盖的历史批量优先 Tushare 不浪费 Wind 积分；冲突优先级 = 用户当下显式指令 > 流程指定 > skill 专用 > 三源兜底；Wind 价格指标批量合并 ≤50 标的/次、探针先行、并发 ≤10。
"""

def append_if_absent(path, marker):
    with io.open(path, encoding="utf-8") as f:
        txt = f.read()
    if marker in txt:
        print("[跳过]", path)
        return False
    txt = txt.rstrip("\n") + "\n" + SEC
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[写入]", path)
    return True

for pack in PACKS:
    for skill in ["westock", "neodata-financial-search"]:
        append_if_absent(os.path.join(PLUGINS, pack, "skills", skill, "SKILL.md"), "数据源路由（三源链路")

# 一致性校验
def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()
for skill in ["westock", "neodata-financial-search"]:
    a = os.path.join(PLUGINS, PACKS[0], "skills", skill, "SKILL.md")
    b = os.path.join(PLUGINS, PACKS[1], "skills", skill, "SKILL.md")
    print("校验 %s 两包一致: %s" % (skill, "OK" if md5(a) == md5(b) else "FAIL"))
print("完成")
