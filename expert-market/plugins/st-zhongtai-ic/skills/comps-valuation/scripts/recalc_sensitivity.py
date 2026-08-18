# -*- coding: utf-8 -*-
"""
敏感性表可复算性审计工具（ST众泰投委会 · comps-valuation 配套）
用法：python recalc_sensitivity.py <报告.md> [--config 名称=股本,类型;...]

用途：对报告中的全部"敏感性分析"表做可复算性校验——
  表内每个格子的数值必须等于：情景值 × 倍数 × 汇率换算 ÷ 股本。
  统一口径规则（pdf-typesetting/comps-valuation 铁律）：
    - 人民币 → 港元：÷ 0.915（1 港元 ≈ 0.915 人民币）
    - 美元收入 → 港元：× 7.86
    - A 股人民币口径：× 1（不换汇）
  默认配置（中证港股通创新药前十成份股，2026-08-12）：
    药明生物=41.45,HKD; 百济=15.42,USD; 信达=17.44,HKD; 康德=29.84,CNY;
    康方=9.21,HKD; 石药=115.2,HKD; 翰森=59.5,HKD; 中生=187.05,HKD;
    三生=25.38,HKD; 科伦=2.41,HKD
输出：每张表逐行通过/失败清单 + 汇总结论（全部可复算 ✓ / 存在不一致 ⚠）
"""
import io, re, sys

DEFAULT_CONFIG = [
    ("药明生物", 41.45, "HKD"), ("百济", 15.42, "USD"), ("信达", 17.44, "HKD"),
    ("康德", 29.84, "CNY"), ("康方", 9.21, "HKD"), ("石药", 115.2, "HKD"),
    ("翰森", 59.5, "HKD"), ("中生", 187.05, "HKD"), ("三生", 25.38, "HKD"),
    ("科伦", 2.41, "HKD"),
]

def fx(x, mode):
    if mode == "USD": return x * 7.86
    if mode == "CNY": return x
    return x / 0.915

def audit(fn, config):
    with io.open(fn, encoding="utf-8") as f:
        lines = f.read().split("\n")
    marks = [i for i, l in enumerate(lines) if "敏感性分析" in l]
    if len(marks) != len(config):
        print(f"警告：找到 {len(marks)} 张敏感性表，配置 {len(config)} 组——检查 --config 是否匹配表序！")
    ok, bad = 0, []
    for idx, start in enumerate(marks):
        if idx >= len(config):
            break
        name, shares, mode = config[idx]
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if re.match(r"^(#|##|###)\s+[0-9零一二三四五六七八九十]", lines[j]):
                end = j; break
        block = lines[start:end]
        try:
            hdr_idx = next(k for k, l in enumerate(block) if l.strip().startswith("|") and re.search(r"倍", l))
            mults = [float(re.search(r"(\d+(?:\.\d+)?)\s*倍", c).group(1))
                     for c in block[hdr_idx].split("|")[2:] if re.search(r"倍", c)]
            for k in range(hdr_idx + 1, len(block)):
                m = re.match(r"^\|?\s*(\d+(?:\.\d+)?)\s*（", block[k].strip())
                if not m: continue
                scen = float(m.group(1))
                unit = "元" if mode == "CNY" else "港元"
                vals = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*" + unit, block[k])]
                expect = [round(fx(scen * mu, mode) / shares, 1) for mu in mults]
                if len(vals) == len(expect) and all(abs(v - e) < 0.15 for v, e in zip(vals, expect)):
                    ok += 1
                else:
                    bad.append((name, scen, vals, expect))
        except Exception as e:
            bad.append((name, "解析异常", str(e), ""))
    print(f"可复算校验: {ok} 行通过 / {len(bad)} 行不通过")
    for b in bad:
        print("  异常:", b)
    print("结论:", "全部可复算 ✓" if not bad else "存在不一致 ⚠（须修复后重生成）")
    return not bad

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    fn = sys.argv[1]
    cfg = DEFAULT_CONFIG
    for arg in sys.argv[2:]:
        if arg.startswith("--config="):
            parts = arg.split("=", 1)[1].split(";")
            cfg = [(p.split("=")[0], float(p.split("=")[1].split(",")[0]), p.split(",")[1]) for p in parts]
    sys.exit(0 if audit(fn, cfg) else 1)
