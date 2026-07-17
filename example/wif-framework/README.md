# WIF v5.9 财富投资框架 - 数据与回测展示

> **版本**: 2026-07-16
> **数据更新日期**: 2026-07-16
> **历史回测**: 2007-01-03 ~ 2026-07-16 (4926 个交易日)

---

## 一、这是什么？

WIF (Wealth Investment Framework) v5.9 是一个**美股基金投资量化方法论**的完整数据 + 回测系统。本目录包含:

- **48 个数据 CSV**（覆盖 40 只 ETF + FRED 宏观数据 + VIX/信用利差）
- **回测引擎** (`WIF_v59_Backtest.py`)
- **完整回测报告** (HTML / NAV / 交易日志)

数据已通过 9 项端到端验证，**与原 v5.9 系统完全一致**（重叠区段零差异验证）。

---

## 二、目录结构

```
example/wif-framework/
├── README.md                                  # 本文件（入口）
└── data/
    ├── README.md                              # 数据说明（轻量版）
    ├── DATA_SPECIFICATION.md                  # ★ 数据规范说明 (字段/单位/格式/来源)
    ├── DATA_UPDATE_PROCEDURE.md               # ★ 数据更新流程 (Step-by-Step)
    ├── _merged_prices_20260716.csv            # 回测引擎核心数据 (4926 行 × 10 列)
    ├── etf_timeseries_20260716.csv             # ETF 时序矩阵 (26 行 × 40 列)
    ├── WIF_v59_Backtest.py                     # 回测引擎 (94KB, 含 2 个 PATCH 2026-07-16)
    ├── WIF_v59_Report_20260716.html            # 回测 HTML 报告 (57KB, 含 Chart.js)
    ├── WIF_v59_nav_20260716.csv                # 净值时序 (4926 行 × 24 列)
    ├── WIF_v59_trade_log_20260716_HSCBC.csv    # 交易日志 (35 笔交易)
    ├── data_source_metadata_20260716.json      # 数据源元数据
    ├── vix_metadata_20260716.json              # VIX 数据元数据 + 已知限制
    └── tickers_20260716/                        # 单 ticker CSV (48 个文件)
        ├── SPY_20260609_20260716.csv            # ETF: Date,Adj Close
        ├── DGS10_2007_2026.csv                  # FRED 利率: Date,Close
        ├── VIX_spot_20260609_20260716.csv      # VIX: Date,VIX
        ├── CreditSpread_BAA_1986_2026.csv      # 信用利差: Date,CreditSpread_bp
        └── ... (45 个其他文件)
```

---

## 三、快速开始

### 3.1 阅读规范（必读）

1. **[DATA_SPECIFICATION.md](./data/DATA_SPECIFICATION.md)** — 数据字段、单位、格式、来源
2. **[DATA_UPDATE_PROCEDURE.md](./data/DATA_UPDATE_PROCEDURE.md)** — 如何更新数据到新日期

### 3.2 查看回测结果

```bash
open example/wif-framework/data/WIF_v59_Report_20260716.html
```

或直接读 `WIF_v59_nav_20260716.csv` 看净值数据。

### 3.3 重跑回测

```bash
cd example/wif-framework/data
python3 WIF_v59_Backtest.py
```

回测引擎会读取 `_merged_prices_20260716.csv` + `tickers_20260716/`，输出新报告。

---

## 四、关键结果（2026-07-16 数据）

### 4.1 WIF v5.9 框架当前市场判定

| 指标 | 当前值 | 阈值 | 状态 |
|:---|:---:|:---|:---:|
| F29 信用利差 (BAA-DGS10) | **182 bp** | >500 = EMERGENCY | ✅ 健康 |
| VIX_spot | **15.67** | >40 = EMERGENCY (F33b) | ✅ 健康 |
| VIXTERM | **+1.43** | 正常区间 -2 ~ +2 | ✅ 健康 |
| Phase 1 判定 | **HEALTHY** | — | ✅ |

### 4.2 WIF v5.9 框架历史回测 (2007-2026)

| 指标 | v5.9 (有摩擦) | v5.9 (无摩擦) | v6.8.1 (有摩擦) | SPY |
|:---|:---:|:---:|:---:|:---:|
| 累计收益 | **+1332.4%** | +1349.7% | +991.3% | +1283.0% |
| 年化收益 | +14.61% | +14.67% | +13.42% | +16.48% |
| 夏普比率 | +1.00 | +1.01 | +0.79 | +0.61 |
| 最大回撤 | -21.1% | -21.1% | -30.1% | -55.2% |
| 调仓次数 | 4 | 4 | 4 | — |
| 累计成本 | $113,888 | — | $230,359 | — |

### 4.3 v5.9 vs v5.8.2 baseline (历史对比)

| 版本 | 累计净收益 | MDD | 调仓次数 |
|:---|:---:|:---:|:---:|
| v5.8.2 baseline (无 P0 修复) | +1082.6% | -20.4% | 29 |
| v5.9 (本次更新) | **+1332.4%** | -21.1% | 4 |

注: v5.9 的累计收益比 v5.8.2 baseline 高 250 pp，但最大回撤略高、净收益是 v5.9 = v5.8 + P0 修复（CSI Hysteresis + F29>500bp 硬拦截）。

---

## 五、数据来源矩阵

### Tier 1 (机构 / 首选)
- **Morningstar MCP**: 40 只 ETF 时序 (HS793 = Daily Return Index)
- **FRED VIXCLS**: VIX 官方收盘数据

### Tier 2 (免费 / 备选)
- **FRED 公共 CSV**: DGS10 / T10YIE / BAMLH0A0HYM2 / BAA 等宏观利率
- **yfinance**: 备用（经常被限速）

### Tier 3 (代理 / 兜底)
- **VIXM ETF**: VIX3M proxy（CBOE ^VIX3M 不被 Morningstar 支持）

详细对比见 [DATA_SPECIFICATION.md § 4.3](./data/DATA_SPECIFICATION.md)。

---

## 六、强制验证清单（更新数据后必跑）

```bash
cd example/wif-framework/data

# 1. CSV 表头合规
python3 -c "
import pandas as pd
from pathlib import Path
DATA = Path('tickers_20260716')
issues = []
ETF = ['SPY','BND','GLD','TLT','VTI','QQQ','XLE','SHV','AGG','EEM','EFA','HYG','IEF',
       'IJH','IJR','IWM','LQD','PDBC','MTUM','QUAL','MOAT','NOBL','HDV','VNQ','VEA',
       'VWO','SCHD','SLV','SPLV','USMV','VB','VGT','VIG','VYM','XLB','XLF','XLP',
       'XLRE','XLU','XLV']
for t in ETF:
    f = DATA / f'{t}_20260609_20260716.csv'
    h = open(f).readline().strip()
    if h != 'Date,Adj Close':
        issues.append(f'{f.name}: {h}')
print('✅ ETF headers OK' if not issues else f'❌ {issues}')
"

# 2. 交叉验证 (与原数据 0% 差异)
python3 -c "
import pandas as pd
orig = pd.read_csv('PATH/TO/ORIG/_merged_prices.csv', parse_dates=['Date'], index_col='Date')
new = pd.read_csv('_merged_prices_20260716.csv', parse_dates=['Date'], index_col='Date')
overlap = orig.index[-5:]
max_diff = max(abs(new.loc[d,c] - orig.loc[d,c]) for d in overlap for c in orig.columns if d in new.index)
print(f'✅ 0% diff' if max_diff < 1e-6 else f'❌ max diff: {max_diff}')
"

# 3. 重跑回测
python3 WIF_v59_Backtest.py
```

---

## 七、已知限制

1. **VIX3M 是 proxy** (用 VIXM ETF 价格代替 CBOE ^VIX3M) — 见 `vix_metadata_20260716.json`
2. **BAA 是月度数据** (最新发布点 2026-06-01 = 6.00%) — 2026-07 用 6.00% 外推
3. **FRED T+1 滞后** — 2026-07-16 的 VIX/DGS10/BAMLH0A0HYM2 在当日还未发布，用 7/15 数据 ffill
4. **回测引擎限制** — 回测引擎不实现 Component CVaR / HRP / Expert Funnel（采用简化等权模拟）

---

## 八、修订历史

| 日期 | 变更 |
|:---|:---|
| 2026-07-16 | 数据更新到 2026-07-16，生成 DATA_SPECIFICATION.md 和 DATA_UPDATE_PROCEDURE.md |
| 2026-06-09 | v5.9 原始发布（P0 修复版，CSI Hysteresis + F29>500bp 硬拦截） |