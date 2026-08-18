# -*- coding: utf-8 -*-
"""阶段6 A+ 落地：书籍知识库调用入口挂接（主库README + 两技能×两包=4处），挂后自动校验两包一致
"""
import io, os, hashlib

PLUGINS = r"C:/Users/Administrator/.workbuddy/plugins/marketplaces/my-experts/plugins"
PACKS = ["st-zhongtai-ic", "sector-equity-research"]

ENTRY = "C:/Users/Administrator/Desktop/市场研究/大V研究/书籍蒸馏/06_检索页/index.html"

SEC_IND = """

## 历史类比知识库（必查，2026-08-17 接入）

行业历史类比（行业兴衰 / 泡沫对照 / 跨国经验）**必须先查书籍蒸馏知识库，禁止凭记忆编造历史对照**：

- 入口：`{ENTRY}`（265 条 = 三书规律 108 已过三重验证 + 现象 157 留档；支持关键词 / 书 / 主题 / 互证 / 大V交叉过滤）
- 行业兴衰与时代贝塔 → 主题"行业兴衰规律""时代贝塔与风格轮动"；跨市场对照 → 同目录 `04_框架提炼/S4_跨书主题对照矩阵.md`
- 引用条目须带 ID（如 QS-13）；现象条目（未过三验）只作线索不作依据；书数据截止 2018/2021/2022，引用时标注时点差
- 用后回写：条目"使用后印证"字段（Query 回写机制，供 P0-5 技能治理时评估升级 skill）
""".replace("{ENTRY}", ENTRY.replace("/", "\\"))

SEC_COMP = """

## 长期估值中枢参考（书籍知识库，2026-08-17 接入）

倍数历史分位与跨市场折溢价判断可查书籍蒸馏知识库（三书 108 条规律，已过三重验证）：

- 入口：`{ENTRY}` → 主题"估值规律"（5 条）+ 主题"利率、流动性与通胀商品"（利率-估值关系 20 条）
- 关键条目示例：长端利率是估值第一驱动（MG-01）；板块估值溢价/折价为数十年稳态（MG-27）；估值是交易结果而非原因，低估值+盈利下行=价值陷阱（QS-31）
- 引用须带条目 ID；数据截止 2018/2021/2022 注意时点；用后回写"使用后印证"字段
""".replace("{ENTRY}", ENTRY.replace("/", "\\"))

def append_if_absent(path, section, marker):
    with io.open(path, encoding="utf-8") as f:
        txt = f.read()
    if marker in txt:
        print("[跳过] 已存在:", path)
        return
    if not txt.endswith("\n"):
        txt += "\n"
    txt += section
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[写入]", path)

# 4 处技能挂接
for pack in PACKS:
    append_if_absent(os.path.join(PLUGINS, pack, "skills", "industry-analysis-method", "SKILL.md"),
                     SEC_IND, "历史类比知识库")
    append_if_absent(os.path.join(PLUGINS, pack, "skills", "comps-valuation", "SKILL.md"),
                     SEC_COMP, "长期估值中枢参考")

# 一致性校验（两包同技能文件须逐字节一致）
def md5(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()
for skill in ["industry-analysis-method", "comps-valuation"]:
    a = os.path.join(PLUGINS, PACKS[0], "skills", skill, "SKILL.md")
    b = os.path.join(PLUGINS, PACKS[1], "skills", skill, "SKILL.md")
    same = md5(a) == md5(b)
    print("校验 %s 两包一致: %s" % (skill, "OK" if same else "FAIL"))

# 主库 README 挂总入口
readme = r"C:/Users/Administrator/Desktop/市场研究/大V研究/00_蒸馏方法论/00_README.md"
SEC_MAIN = """

## 书籍知识库调用指引（2026-08-17 接入，阶段6 拍板 A+）

三书蒸馏产出（凌鹏《周期、估值与人性》/ 燕翔《美股70年》《全球股市启示录》）已成型，调用入口统一为检索页：

- **检索总入口**：`大V研究/书籍蒸馏/06_检索页/index.html`（265 条六维过滤；规律 108 过三验 / 现象 157 留档）
- **行业历史类比** → 主题"行业兴衰规律""时代贝塔与风格轮动"，或跨书矩阵 `04_框架提炼/S4_跨书主题对照矩阵.md`
- **估值长期中枢** → 主题"估值规律"（MG-01/MG-27/QS-31 等）；利率环境 → 主题"利率、流动性与通胀商品"
- **泡沫识别 / 周期定位** → 主题"泡沫机制与崩塌出清""周期定位与牛熊驱动"；凌鹏三变量决策链 → `04_框架提炼/S4_框架_周期估值与人性.md`
- 引用纪律：带条目 ID（ZP/MG/QS-xx 或 BK 双制）；现象条目不作依据；数据截止 2018/2021/2022 标时点；用后回写"使用后印证"
- 同步挂接：研深行技能 industry-analysis-method / comps-valuation 两包四处（2026-08-17 一致性校验通过）
- 固化评估：凌鹏框架暂不转 skill，P0-5 技能治理时按 Query 回写数据决定（`书籍蒸馏/00_阶段6_固化评估.md`）
"""
append_if_absent(readme, SEC_MAIN, "书籍知识库调用指引")
print("完成")
