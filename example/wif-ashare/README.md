# WIF A-Share v2.7 — 中国A股宏观配置策略

## 概述

WIF (Wealth Investment Framework) v2.7 是基于 PMI+M2 宏观数据的 A 股多资产配置策略。回测区间 2013-2026（约 12.3 年），3094 个交易日。

**核心绩效**：累计 +796.3%，年化 +19.56%，夏普 1.233，MDD -18.4%。

## 架构摘要

```
PMI + M2 → MCI → 象限（Q1/Q2/Q3）
MA60 趋势覆盖（±7% 阈值）→ 可能覆盖 MCI 象限
R20 <-8%/-12%/-20% → 触发 L1/L2/L3 EMERGENCY

五资产：沪深300 + 中证500 + 创业板 + 黄金 + 国债
```

详细方法论见 `.opencode/skills/wif-ashare-advisory/SKILL.md`。

## 文件结构

```
example/wif-ashare/
├── README.md
├── v27_engine.py        # 独立回测引擎（动态路径）
└── data/
    ├── etf_prices_new.csv          # 4只ETF前复权日线
    ├── index_csi500_daily.csv      # 中证500指数日线
    ├── index_tech_399303_daily.csv # 国证科技指数日线
    ├── macro_pmi.csv               # PMI月度数据
    ├── macro_m2_m1_spread.csv      # M2/M1增速数据
    └── macro_chip_daily.csv        # 科创芯片588200月度收益
```

## Python 包

核心逻辑已封装为 `wif_framework.ashare` 模块：

```python
from wif_framework.ashare import load_data, run_backtest

result = run_backtest()
print(result["stats"])
# {'cumulative': 796.3, 'geo_cagr': 19.56, ...}
```

### 可调用组件

| 函数 | 说明 |
|:---|:---|
| `compute_mci(pmi, m2)` | 计算宏观景气指数 |
| `mci_to_quadrant(mci)` | MCI → Q1/Q2/Q3 |
| `effective_quadrant(mci_q, trend)` | 叠加 MA60 趋势覆盖 |
| `get_em_weight(r20)` | 获取 EM 级别和权重 |
| `load_data()` | 加载并预处理所有数据 |
| `run_backtest()` | 运行完整回测 |

## 复现回测

```bash
# 方式一（Python 包）
python3 -c "from wif_framework.ashare import run_backtest; print(run_backtest()['stats'])"

# 方式二（独立引擎）
python3 example/wif-ashare/v27_engine.py
```

## 已知局限

- 每日调仓成本 0.3%/次，实际可能更高
- MA60 覆盖在趋势反转期有 8-10 天滞后（2015 年 -12.1pp）
- 科技替换使用指数而非 ETF（略高估 ~0.1pp/年）
- 科创芯片月收益使用 399303 指代（近似替代，实际可用 ETF 日线重算）
