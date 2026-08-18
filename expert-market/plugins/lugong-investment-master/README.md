# 超级鹿鼎公 · 价值投资大师

以雪球大V"超级鹿鼎公"（挖地瓜的超级鹿鼎公）十四年公开投资观点蒸馏出的分析型专家。输出其观点/框架，非投资建议。

## 类型

Agent 型（单个 AI 专家）

## 功能

- **十六字体系**：价值选股、趋势选时、估值定仓、波动降本
- **选股六大硬标准**：垄断属性、ROE、现金流、股息率、分红率、负债率、央企优先
- **估值测算**：价值之锚（8-9%分红底锚）、DDM、周期PE分档、买入价7-8折
- **仓位纪律**：分档仓位上限、左侧分批、做T纪律、止盈止损铁律
- **行业与标的观点库**：煤炭/电力/电解铝/银行/公用事业/港股红利（含精读观点159条）
- **表达还原**：军语比喻、口癖、标题党模式的表达DNA
- **可回测规则**：7 组观点规则化清单（标注"未经回测验证"）

## 使用示例

- "鹿鼎公会怎么看现在的中国神华？"
- "用鹿鼎公的框架分析一下淮北矿业"
- "当前市场高股息收息股怎么选？"

## 参考资料

专家包内置 skill（`skills/lugong-value-invest/`）12 个 references：
framework（十六字/选股标准）、targets（标的观点）、quotes（语录）、backtest-rules（可回测规则）、methodology（M1-M12）、archive-2014-2023（原典）、viewpoints-elite（159条精读）、expression-dna（表达DNA）、knowledge-boundary（知识边界）、conflicts（冲突表）、timeline（时间线）、sources（来源置信度）

## 头像

头像已自动生成在 `avatars/` 目录下。如需替换为自定义头像，要求：
- 格式：PNG（推荐）或 JPG
- 尺寸：512×512 px
- 大小：单张不超过 500KB

## 安装

将专家包目录放到专家目录下：

```
C:\Users\Administrator\.workbuddy\plugins\marketplaces\my-experts\plugins/lugong-investment-master/
```

然后运行注册命令使其可见：

```bash
python3 scripts/register_expert.py <expert-dir>
```

## 打包分享

```bash
zip -r lugong-investment-master.zip lugong-investment-master/
```
