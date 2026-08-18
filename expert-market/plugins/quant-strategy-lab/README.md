# 量化策略研习社（Quant Strategy Lab）

专注 A股与港股的策略回测与量化研讨，从红利择时打磨到新策略拓展，零代码也能严谨验证交易想法。

## 类型

Team 型（多角色协作团队）· 金融投资类

## 团队成员

| 角色 | 花名 | 职责 |
|------|------|------|
| 首席策略官（主理人） | 何执舟 | 需求拆解、编排调度、结果解读、研讨规划 |
| 量化工程师 | 寇豆码 | 拉数据、写回测代码、跑回测、出图表 |
| 策略分析师 | 甄红利 | 选股筛选、策略设计、基本面与事件分析 |
| 风控官 | 严过关 | 回撤/夏普/胜率评估、仓位与止损建议 |

## 工具链

- 主数据源：westock-mcp（腾讯自选股，已连接）— A股/港股行情、财报、研报、龙虎榜、北向、技术指标
- 补充数据：tushare（已配 token）— A股分红、复权、深度财务
- 选股引擎：westock tool_filter / tool_strategy / tool_ranking
- 知识教学：wb-finance-skill、neodata-financial-search
- 回测引擎：由量化工程师用 Python 自实现

## 使用示例

- 帮我把红利低波择时策略系统化，A股过去5年回测一下
- 对比几只高股息港股ETF的持有收益和回撤
- 我想拓展策略类型，先回测一个双均线动量策略看看

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\Administrator\.workbuddy\plugins\marketplaces\my-experts\plugins/quant-strategy-lab/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r quant-strategy-lab.zip quant-strategy-lab/
```
