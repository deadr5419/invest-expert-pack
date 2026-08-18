# AI 部署指令（AI_DEPLOY.md）

> **本文档由部署 AI 读取并执行，人类无需逐条阅读。**
> 你是部署代理，任务是：把本仓库的「投研专家团 + 书籍蒸馏知识库」部署到当前 WorkBuddy 环境。
> 执行完第 3 节全部验收项后才能宣告部署完成。

---

## 0. 部署前检查

1. 确认操作系统类型（Windows / macOS / Linux），`~/.workbuddy` 为通用路径，Windows 下等价 `C:\Users\<用户名>\.workbuddy`。
2. 检查 `~/.workbuddy/plugins/marketplaces/` 是否存在，不存在则创建。
3. 检查其中是否已有 `expert-market` 目录：
   - 无 → 正常部署；
   - 有 → 向用户确认「覆盖更新」还是「保留现有」，不得擅自覆盖。

## 1. 部署专家市场

### 方式 A：文件复制（优先，AI 可全程独立执行）

1. 将仓库根目录下的 `expert-market/` **整个目录**复制到
   `~/.workbuddy/plugins/marketplaces/expert-market/`
   （即最终结构为 `marketplaces/expert-market/plugins/{5个专家包}`，`plugins/` 这一层必须保留）。
2. 复制完成后，告知用户：**重启 WorkBuddy 使专家市场生效**。
3. 用户重启后，检查左侧「专家」是否出现 ST众泰投委会等 5 个专家包：
   - 已出现 → 继续第 2 节；
   - 未出现 → 检查 `~/.workbuddy/plugins/known_marketplaces.json` 是否注册了 `expert-market`；
     若未注册，模仿该文件内既有条目的 JSON 格式，追加一条
     `"expert-market": { "type": "local", "installLocation": "<实际路径>", "description": "投研专家团自定义市场" }`，
     再请用户重启一次。

### 方式 B：zip 导入（方式 A 不可行时回退）

1. 将 `expert-market/` 压缩为 `expert-market.zip`（zip 内根目录即为 `plugins/`）。
2. 指导用户在 WorkBuddy 中：**设置 → 插件市场 → 导入 zip** → 选择该文件。
3. 用户导入完成后继续第 2 节。

## 2. 部署书籍蒸馏知识库

1. **放置位置自由**，默认建议放在用户的研究工作区，例如：
   - Windows：`C:\Users\<用户名>\Desktop\市场研究\大V研究\书籍蒸馏\`
   - macOS/Linux：`~/Desktop/市场研究/大V研究/书籍蒸馏/`
   - 若用户已指定位置，遵从用户。
2. 复制 `书籍蒸馏/` 整个目录时，**必须保持内部结构完整**：
   `03_观点条目库 / 04_框架提炼 / 05_工具脚本 / 06_检索页` 缺一不可
   （`06_检索页/index.html` 通过相对路径 `../03`、`../04` 跳转，拆散即失效）。
3. **回写实际路径（必须执行）**——让使用 AI 无需再问路径：
   - 打开 `expert-market/plugins/st-zhongtai-ic/skills/comps-valuation/SKILL.md`，
     定位包含「入口：」字样且指向 `06_检索页/index.html` 的那一行
     （原文形如：`入口：本仓库 书籍蒸馏/06_检索页/index.html（随专家包一并分发，安装后按本地实际路径打开）`），
     将整行替换为 `入口：<书籍蒸馏实际绝对路径>\06_检索页\index.html（已由部署 AI 写入）`。
   - 对 `expert-market/plugins/st-zhongtai-ic/skills/industry-analysis-method/SKILL.md` 做同样替换
     （定位包含「入口：」且指向 `06_检索页/index.html` 的行，替换规则同上）。
4. 在 `书籍蒸馏/00_安装记录.md` 写入：安装日期、实际绝对路径、部署人。若该文件已存在则追加。

## 3. 部署验收（全部通过才算完成）

逐项检查并记录结果：

- [ ] `~/.workbuddy/plugins/marketplaces/expert-market/plugins/` 下存在 5 个专家包目录
      （st-zhongtai-ic / lugong-investment-master / shanxing-investment-master /
       huishou-utilize-reinvest-expert / sector-equity-research）
- [ ] 5 个专家包内 `.codebuddy-plugin/plugin.json` 均可正常读取
- [ ] 报告管线脚本就位：st-zhongtai-ic 与 sector-equity-research 的
      `skills/pdf-typesetting/scripts/pipeline/` 下存在 7 个文件
      （md2html_full.py / md2docx.py / md2pdf_pro.py / generate_pdfs.py /
       generate_html_report.py / qa_check.py / README.md）
- [ ] 书籍蒸馏 `06_检索页/index.html` 与 `entries.json` 存在
- [ ] 书籍蒸馏 `03_观点条目库/S3_规律条目库.md` 存在
- [ ] 两个技能文件（comps-valuation / industry-analysis-method）内的书籍入口路径已替换为实际绝对路径
- [ ] 原书 `01_原文藏书/` 内 3 本 PDF 完整（周期、估值与人性 / 美股70年 / 全球股市启示录）
- [ ] 部署结果已向用户汇报，并告知需要重启的步骤

## 4. 报告管线运行依赖（AI 执行，一次性）

1. 确认 Python 可用：`python --version`（无 Python 则引导用户安装）。
2. 安装依赖库（缺失才装，用系统推荐的 pip 命令）：
   `pip install reportlab xhtml2pdf python-docx pypdf`
3. 验证：`python -c "import reportlab, xhtml2pdf, docx, pypdf"` 无报错即通过。
4. 若用户环境禁止全局安装（如公司策略），改用 `pip install --user` 或 venv，并在汇报中说明。

## 5. 数据源（账号级资源，AI 只引导、不代配）

- 检查连接器管理界面：「腾讯自选股」连接器是否已连接（实时行情）。
- 检查 Tushare token、Wind key 是否已配置（历史批量 / 权威核验）。
- 未配置 → 引导用户自行注册配置，AI 不得代为创建账号或输入凭据。
- 研报采集类工具（如需）由用户自行决定是否配置。

## 6. 部署完成后，向用户说明使用纪律

1. **大V观点 ≠ 事实**：鹿鼎公/山行/回收再利用的输出标注"XX观点"，供思路参考，不代结论。
2. **引用带 ID**：引用书籍规律须带条目 ID（如 MG-01、QS-31）；现象条目（未过三验）只作线索不作依据。
3. **数据时点**：书籍规律数据截止 2018/2021/2022，引用时标注时点差。
4. **原书 PDF 仅供个人学习**，不可再分发、传播或商用。

---

*部署完成后可将本文件归档到仓库 `_deployed/` 目录，避免重复部署时误读。*
