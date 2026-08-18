# -*- coding: utf-8 -*-
"""P0-5 ③④⑤ 按测试结论执行：
④ idea-generation 独有内容（六类筛选清单+主题扫描）并入 westock，两包删除 idea-generation
⑤ neodata IC/SER 副本移除（用户级 v1.1.0 为超集）；IC .neodata_token 缓存一并移除
③ event-scenario-analyzer 保留（不动）
"""
import io, os, shutil, hashlib

PLUGINS = r"C:/Users/Administrator/.workbuddy/plugins/marketplaces/my-experts/plugins"
PACKS = ["st-zhongtai-ic", "sector-equity-research"]
BK = r"C:/Users/Administrator/.workbuddy/backups/P0-5_20260817"

# ---- 1. 备份 ----
for pack in PACKS:
    for s in ["idea-generation", "neodata-financial-search"]:
        src = os.path.join(PLUGINS, pack, "skills", s)
        if os.path.exists(src):
            dst = os.path.join(BK, s + "_" + pack)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print("[备份]", s, pack)
tok = os.path.join(PLUGINS, "st-zhongtai-ic", "skills", ".neodata_token")
if os.path.exists(tok):
    shutil.copy2(tok, os.path.join(BK, "neodata_token_IC缓存"))
    print("[备份] .neodata_token")

# ---- 2. westock 追加筛选方法论 ----
SEC_SCREEN = """

## 选股筛选方法论（2026-08-17 由 idea-generation 并入）

> 条件选股的两层用法：westock-tool 负责"按条件筛出候选"，本节负责"用什么条件、怎么组织筛选"。筛选出的是候选不是结论，每只都需基本面验证（screens surface candidates, not conclusions）。

### Step 1: 定义搜索参数（向用户确认）
方向（多/空/双向）· 市值（大/中/小/微）· 行业 · 风格（价值/成长/质量/特殊情形/事件驱动）· 地域 · 主题（AI/出海/老龄化等）

### Step 2: 六类量化筛选清单（阈值参考）
**价值类**：P/E 低于行业中位 / EV/EBITDA 低于历史均 / FCF 收益率>5% / P/B<1.5 / 90天内内部人买入 / 股息率高于市场均
**成长类**：收入增速>15% YoY / 盈利增速>20% YoY / 收入加速（增速提升） / 利润率扩张 / ROIC>15% / 净留存率>110%（SaaS）
**质量类**：连续5年+收入增长 / 利润率稳定或扩张 / ROE>15% / 低负债率 / 高FCF转化 / 内部人持股>5%
**空头类**：收入下滑或增速减速 / 利润率压缩 / 应收/存货增速超收入 / 内部人卖出 / 无依据的估值溢价 / 高做空+基本面恶化 / 会计红旗（审计变更/重述）
**特殊情形类**：次新/SPAC 解禁到期 / 12个月内分拆 / 重组出清 / 激进投资者介入 / 弱势公司管理层变更

### Step 3: 主题扫描（thematic sweep）
1. 先立主题论点（如"AI 基建支出 2026 加速"）2. 画价值链：谁直接/间接受益 3. 区分纯玩与分散暴露 4. 判断哪些已 price in 5. 找市场还没连起来的二阶受益者

### Step 4: 候选呈现（简表）
公司名 + 多/空 + 一句话论点 + 指标表（市值/EV-EBITDA/P-E/收入增速/EBITDA利润率/FCF收益率）+ 论点3-5条（为何错价/市场漏了什么/兑现催化）+ 关键风险 + 下一步

### 纪律
- 筛选是候选生成不是结论，每个产出都需基本面深挖
- 好机会常在交叉处（质量公司因暂时逆风落到价值价）
- 避免拥挤交易（查持仓/做空/覆盖券商数）
- 逆向想法必须有催化——过早没有催化等于做错
- 长期跟踪命中率：哪些筛选/方法真正出过好票
- 空头需要更高确定性：时点更难、风险不对称
"""

def append_westock(path):
    with io.open(path, encoding="utf-8") as f:
        txt = f.read()
    if "选股筛选方法论" in txt:
        print("[跳过]", path)
        return
    txt = txt.rstrip("\n") + "\n" + SEC_SCREEN
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[westock并入]", path)

# ---- 3. 微调 westock 路由注释行（去掉 neodata） ----
def fix_route(path):
    with io.open(path, encoding="utf-8") as f:
        txt = f.read()
    new = txt.replace("本技能（westock / neodata）", "本技能（westock）")
    if new != txt:
        with io.open(path, "w", encoding="utf-8") as f:
            f.write(new)
        print("[路由注释微调]", path)

# ---- 4. 删除 ----
for pack in PACKS:
    for s in ["idea-generation", "neodata-financial-search"]:
        d = os.path.join(PLUGINS, pack, "skills", s)
        if os.path.exists(d):
            shutil.rmtree(d)
            print("[删除]", s, pack)
if os.path.exists(os.path.join(PLUGINS, "st-zhongtai-ic", "skills", ".neodata_token")):
    os.remove(os.path.join(PLUGINS, "st-zhongtai-ic", "skills", ".neodata_token"))
    print("[删除] IC .neodata_token 缓存")

for pack in PACKS:
    append_westock(os.path.join(PLUGINS, pack, "skills", "westock", "SKILL.md"))
    fix_route(os.path.join(PLUGINS, pack, "skills", "westock", "SKILL.md"))

# ---- 5. 全量校验 ----
def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()
ic = os.path.join(PLUGINS, "st-zhongtai-ic", "skills")
ser = os.path.join(PLUGINS, "sector-equity-research", "skills")
ic_s = sorted(s for s in os.listdir(ic) if os.path.isdir(os.path.join(ic, s)))
ser_s = sorted(s for s in os.listdir(ser) if os.path.isdir(os.path.join(ser, s)))
print("\nIC技能:", len(ic_s), "| SER技能:", len(ser_s))
print("仅IC有(三家大V):", sorted(set(ic_s) - set(ser_s)))
diff = [s for s in set(ic_s) & set(ser_s) if md5(os.path.join(ic, s, "SKILL.md")) != md5(os.path.join(ser, s, "SKILL.md"))]
print("两包同技能不一致:", diff if diff else "无（全部一致）")
print("完成")
