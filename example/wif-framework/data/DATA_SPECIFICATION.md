# WIF v5.9 数据规范说明 (DATA SPECIFICATION)

> **版本**: 2026-07-16
> **适用范围**: WIF (Wealth Investment Framework) v5.9 / v6.8.1 P0 修复版
> **文档目的**: 完整定义 WIF 回测引擎所需的全部数据的字段、单位、格式、来源、更新频率、更新方法。任何对数据的修改都必须严格遵循本规范。

---

## 一、数据总览

```
data/
├── _merged_prices_20260716.csv              # ★ 回测引擎核心数据文件 (4926 行 × 10 列)
├── etf_timeseries_20260716.csv             # ETF 时序矩阵 (26 行 × 40 列) - 仅增量
├── WIF_v59_Backtest.py                     # 回测引擎 (含 2 个 PATCH 2026-07-16)
├── WIF_v59_Report_20260716.html            # 回测 HTML 报告
├── WIF_v59_nav_20260716.csv                # 净值时序
├── WIF_v59_trade_log_20260716_HSCBC.csv    # 交易日志
├── data_source_metadata_20260716.json      # 数据源元数据
├── vix_metadata_20260716.json              # VIX 数据元数据 + 已知限制
└── tickers_20260716/                        # 单 ticker CSV (48 个文件)
    ├── SPY_20260609_20260716.csv            # ETF 价格 (Adj Close)
    ├── DGS10_2007_2026.csv                  # FRED 利率 (Close)
    ├── VIX_spot_20260609_20260716.csv      # VIX (VIX)
    ├── CreditSpread_BAA_1986_2026.csv      # 信用利差 (CreditSpread_bp)
    └── ... (48 个文件)
```

---

## 二、数据层级与回测引擎读取规则

### 2.1 回测引擎 `load_raw_etf` 函数的标准列名规范

```python
def load_raw_etf(path, ticker):
    # ... 加载 Date 索引 ...
    if 'Adj Close' in df.columns:
        col = 'Adj Close'         # ← ETF 价格的唯一合法列名
    elif 'Close' in df.columns:
        col = 'Close'             # ← FRED 利率的唯一合法列名
    else:
        raise ValueError(...)    # ← 严格模式: 任何不符预期的列名立即报错
    adj = df[col].ffill()
```

### 2.2 WIF v5.9 数据层级表

| 层级 | 读取方式 | 列名规范 | 数据源 |
|:---:|:---|:---|:---|
| **Tier 1** | `pd.read_csv` + 自定义读取 | 固定列名 (如 `CreditSpread_bp`) | 直接 CSV |
| **Tier 2** | `load_raw_etf()` (glob + sorted last) | `Adj Close` (ETF) 或 `Close` (FRED) | glob 模式 `{TICKER}_*.csv` |

---

## 三、各文件详细字段规范

### 3.1 `_merged_prices_20260716.csv` ★ 核心数据

| 字段 | 类型 | 单位 | 取值范围 | 数据来源 | 更新频率 |
|:---|:---|:---|:---|:---|:---|
| `Date` | string (YYYY-MM-DD) | — | 2007-01-03 ~ 更新日 | — | 交易日 |
| `SPY` | float | USD | ~50 ~ 1377 | Morningstar MCP (HS793) / yfinance | 日 |
| `BND` | float | USD | ~40 ~ 135 | 同上 | 日 |
| `GLD` | float | USD | ~60 ~ 496 | 同上 | 日 |
| `TLT` | float | USD | ~46 ~ 199 | 同上 | 日 |
| `VTI` | float | USD | ~25 ~ 579 | 同上 | 日 |
| `QQQ` | float | USD | ~22 ~ 881 | 同上 | 日 |
| `XLE` | float | USD | ~9 ~ 118 | 同上 | 日 |
| `VIX` | float | Index Points | ~9 ~ 83 | FRED VIXCLS / CBOE | 日 |
| `SHV` | float | USD | ~82 ~ 148 | Morningstar MCP / yfinance | 日 |
| `VIXTERM` | float | Index Points | -6.7 ~ +23.8 | VIX - VIX3M (CBOE) | 日 |

**约束**:
- 形状: 4926 行 × 10 列（2007-01-03 起到更新日）
- 缺失值: 必须为 0（ffill 处理）
- 数据时区: 所有日期为 `pd.Timestamp` 无时区

### 3.2 ETF 单 ticker CSV (`tickers_20260716/{TICKER}_20260609_20260716.csv`)

| 字段 | 类型 | 单位 | 说明 |
|:---|:---|:---|:---|
| `Date` | string (YYYY-MM-DD) | — | 交易日 |
| `Adj Close` | float | USD | 含分红/拆股调整后的收盘价 |

**命名约定**:
- 格式: `{TICKER}_20260609_20260716.csv`
- glob 模式: `{TICKER}_*.csv` (回测引擎读取最新一个)
- 列名 **必须**为 `Adj Close`（不可为 `Close` 或其他）

**涉及 ETF** (40 只): SPY, BND, GLD, TLT, VTI, QQQ, XLE, SHV, AGG, EEM, EFA, HYG, IEF, IJH, IJR, IWM, LQD, PDBC, MTUM, QUAL, MOAT, NOBL, HDV, VNQ, VEA, VWO, SCHD, SLV, SPLV, USMV, VB, VGT, VIG, VYM, XLB, XLF, XLP, XLRE, XLU, XLV

### 3.3 FRED 利率类 CSV (`tickers_20260716/{SERIES}_*.csv`)

| 文件 | 字段 | 类型 | 单位 | 取值范围 | FRED 代码 |
|:---|:---|:---|:---|:---|:---|
| `DGS10_2007_2026.csv` | `Date`, `Close` | float | % (百分比) | 0.5 ~ 5.0 | DGS10 |
| `T10YIE_2007_2026.csv` | `Date`, `Close` | float | % (百分比) | 0.5 ~ 3.0 | T10YIE |
| `BAMLH0A0HYM2_2007_2026.csv` | `Date`, `Close` | float | % (OAS 利差) | 2.0 ~ 12.0 | BAMLH0A0HYM2 |
| `BAA_daily_2026.csv` | `Date`, `Close` | float | % (Moody's Baa Yield) | 3.11 ~ 12.04 (历史 1986-2026) | BAA (月度数据, 外推) |

**关键约束**:
- 列名 **必须**为 `Close`（与 ETF 的 `Adj Close` 严格区分）
- 单位: 都是**百分比 (%)**，不是小数 (e.g., DGS10 = 4.20 表示 4.20%)
- BAA 是**月度数据**，2026-07-01 之后用最新发布值 (6.00%) 外推

### 3.4 VIX 系列 CSV

#### `VIX_spot_20260609_20260716.csv`

| 字段 | 类型 | 单位 | 取值范围 | 数据源 |
|:---|:---|:---|:---|:---|
| `Date` | string | — | 2026-06-09 ~ 更新日 | FRED VIXCLS |
| `VIX` | float | Index Points | 9 ~ 83 | FRED VIXCLS |

**注意**: FRED VIXCLS 数据 **滞后 1 天发布**。更新当日 (2026-07-16) 取数据时，最新数据通常到 T-1。

#### `VIX3M_proxy_VIXM_20260609_20260716.csv` ⚠️ 注意代理关系

| 字段 | 类型 | 单位 | 取值范围 | 数据源 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `Date` | string | — | 2026-06-09 ~ 更新日 | Morningstar MCP (F00000LI7D) | — |
| `VIX3M` | float | USD | ~14 ~ 16 | ProShares VIX Mid-Term Futures ETF | **ETF 价格 ≠ VIX3M 指数** |

**重要代理关系说明**:
- 真值应是 CBOE `^VIX3M` 指数
- Morningstar MCP 不支持 `^VIX3M` ticker (`^` 前缀被拒)
- 我们用 **ProShares VIX Mid-Term Futures ETF (VIXM)** 的价格作为代理
- **数值范围完全不同**: VIX3M 指数通常在 13-25 区间，VIXM ETF 价格在 14-16 区间
- **历史相关性**: 高（>0.85）但非 1:1
- **生产环境应替换**: 当可访问 CBOE/FRED 原始 VIX3M 时，应替换此代理

#### `VIXTERM_20260609_20260716.csv`

| 字段 | 类型 | 单位 | 公式 |
|:---|:---|:---|:---|
| `Date` | string | — | — |
| `VIXTERM` | float | Index Points | `VIX - VIX3M_proxy` |

**WIF v5.9 公式定义** (官方):
$$VIXTERM = VIX_{spot} - VIX3M_{CBOE}$$

**实际计算**: 用 VIX3M proxy 代替 VIX3M，差异在 proxy 已知范围内。

### 3.5 信用利差 CSV (`CreditSpread_BAA_1986_2026.csv`)

| 字段 | 类型 | 单位 | 公式 | 数据源 |
|:---|:---|:---|:---|:---|
| `Date` | string | — | — | — |
| `CreditSpread_bp` | float | **bp (基点)** | `(BAA% - DGS10%) × 100` | FRED BAA - FRED DGS10 |

**WIF v5.9 用此作为 F29 信用利差指标**，触发阈值:
- `< 150 bp` → 极度乐观
- `150-300 bp` → 正常区间
- `300-500 bp` → 信用紧张 (WARNING 阈值)
- `500-700 bp` → 高收益债危机 (EMERGENCY 硬触发)
- `> 700 bp` → 金融危机

**历史关键参考点**:
- 1987-10-19 黑色星期一: BAA 12.04% (历史最高)
- 2008-12-04 雷曼峰值: CreditSpread 616.0 bp (触发 EMERGENCY)
- 2020-03-23 COVID 峰值: CreditSpread 431.0 bp (WARNING 边缘)
- 2020-12-31: BAA 3.11% (历史最低)

---

## 四、数据更新规则

### 4.1 更新触发条件
满足任一即应触发数据更新:
1. 自然日超过 7 天
2. 关键宏观数据 (F29/VIX/VIXTERM) 变化显著 (>5% 阈值突破)
3. 用户主动询问 "美股当前状态"
4. 距上次更新 ≥ 1 个交易日（交易时段内）

### 4.2 更新方法

```
Step 1: 拉取数据
   ├─ Tier 1 (机构): Morningstar MCP (HS793) - 40 ETF
   ├─ Tier 1 (机构): FRED VIXCLS - VIX 官方
   ├─ Tier 2 (免费): FRED 公共 CSV 直链 - 利率
   └─ Tier 3 (代理): VIXM ETF - VIX3M proxy

Step 2: 写入文件
   ├─ 命名: {TICKER}_20260609_20260716.csv (用最新日期)
   ├─ 列名: ETF=Adj Close, FRED=Close, VIX=自定义
   └─ 不覆盖原文件，只新增带日期后缀的新文件

Step 3: 合并 _merged_prices.csv
   ├─ 读原文件
   ├─ concat 新数据 (后缀命名版本)
   ├─ 按 Date dedup (新数据覆盖旧数据)
   ├─ ffill 填充缺失
   └─ 写出 _merged_20260716.csv

Step 4: 交叉验证
   ├─ 重叠区段 (新数据前 5 天 vs 原数据后 5 天) 必须 0% 差异
   ├─ NaN 数必须为 0
   └─ 所有 ETF 列名必须为 Adj Close (非 Close)

Step 5: 重跑回测
   ├─ 修改 WIF_v59_Backtest.py 路径指向 v5.9_backtest_20260716/
   ├─ 跑 WIF_v59_Backtest.py
   └─ 验证: 与原结果应一致（数据驱动，结果不应变化）

Step 6: 复制产物到本项目
   ├─ WIF_v59_Backtest.py (含 2 个 PATCH)
   ├─ WIF_v59_Report_20260716.html
   ├─ WIF_v59_nav_20260716.csv
   └─ WIF_v59_trade_log_20260716_HSCBC.csv
```

### 4.3 数据源优先级

| 数据 | Tier 1 首选 | Tier 2 备选 | Tier 3 兜底 |
|:---|:---|:---|:---|
| ETF 价格 | Morningstar MCP HS793 | yfinance | — |
| VIX | FRED VIXCLS | CBOE 官网 | yfinance ^VIX |
| VIX3M | ~~CBOE ^VIX3M~~ | FRED VIXCLS series | VIXM ETF (proxy) |
| F29 信用利差 | FRED BAMLC0A0CMTY | FRED BAA + DGS10 计算 | BAMLH0A0HYM2 (OAS) |
| 10Y Treasury | FRED DGS10 | yfinance ^TNX | — |
| 10Y 通胀预期 | FRED T10YIE | — | — |
| 实际利率 | FRED DFII10 | DGS10 - T10YIE (计算) | — |
| BAA 收益率 | FRED BAA | — | — |
| HY 信用利差 | FRED BAMLH0A0HYM2 | — | — |

### 4.4 多源交叉验证 (强制)

**3 源交叉验证规则**: 每个关键数据点必须有 ≥ 2 个独立数据源比对。

| 数据 | 源 1 | 源 2 | 验证方法 |
|:---|:---|:---|:---|
| ETF 价格 | Morningstar HS793 | yfinance | 重叠 5 天，应 0% 差异 |
| VIX | FRED VIXCLS | yfinance ^VIX | 重叠 5 天，应 0% 差异 |
| 10Y Treasury | FRED DGS10 | Morningstar HP010 (TTM Yield) | 方向一致，量级一致 |
| BAA 信用利差 | FRED BAA - DGS10 | FRED BAMLH0A0HYM2 | 方向一致 |

---

## 五、已知数据限制（必须显式记录）

### 5.1 数据时效性限制

| 数据源 | 发布时间 | 2026-07-16 当日数据状态 |
|:---|:---|:---|
| Morningstar MCP | 实时 (T) | ✅ 有 |
| FRED VIXCLS | T+1 收盘 | ❌ 7/16 数据 7/17 才发布 |
| FRED DGS10 | T+1 | ❌ 7/16 数据 7/17 才发布 |
| FRED T10YIE | T+1 | ✅ 有 (Bloomberg 实时源) |
| FRED BAMLH0A0HYM2 | T+1 | ❌ 7/16 数据 7/17 才发布 |
| FRED BAA | 月度滞后 (下月初) | ❌ 最新发布点 2026-06-01 |
| VIXM ETF | 实时 (T) | ✅ 有 |

### 5.2 处理方法

**当数据源 T+1 滞后时**，在 `_merged_prices_20260716.csv` 中：
- `2026-07-16` 的 `VIX`/`VIXTERM`/`DGS10` 等字段是 **ffill 值**（即 7/15 的值）
- 这个处理方法必须**显式标注**（见 vix_metadata_20260716.json）

**当 BAA 月度滞后时**：
- `2026-06-09` 起的 `BAA` 用 2026-06-01 的 6.00% 外推
- `2026-05-31` 及之前用 2026-05-01 的 6.10% 外推

### 5.3 数据源缺失时的 fallback

如果某 Tier 1 数据源完全不可用，按以下顺序降级:

```
Morningstar MCP → yfinance (限速风险) → akshare / baostock (但 A 股) → 不更新
FRED VIXCLS → CBOE 官网 → yfinance ^VIX
FRED BAA → ICE BofA BAMLC0A0CMTY (OAS) → BAMLH0A0HYM2 (OAS) → 计算代理
```

---

## 六、与 WIF v5.9 设计文档的对应关系

| 设计文档 (v5.9.md) | 数据文件 | 公式定义 |
|:---|:---|:---|
| F01 (年化收益率) | `prices.pct_change().mean() * 252` | 基于 _merged_prices |
| F02 (年化波动率) | `prices.pct_change().std() * sqrt(252)` | 基于 _merged_prices |
| F03 (夏普) | `(ret - rf) / vol` | 基于 _merged_prices |
| F04 (MDD) | `(prices / prices.cummax() - 1).min()` | 基于 _merged_prices |
| F07 (巴菲特指标) | `Wilshire 5000 / GDP` | 暂未集成 (需 WILL5000INDFC) |
| F29 (信用利差) | `CreditSpread_bp` | `CreditSpread_BAA_1986_2026.csv` |
| F31 (实际利率) | `DGS10 - T10YIE` (计算) | DGS10_2007_2026.csv + T10YIE_2007_2026.csv |
| F33 (VIXTERM) | `VIX_spot - VIX3M` | VIX_spot.csv + VIX3M_proxy.csv |
| F33b (VIX 动量) | VIX > 40 且 10日涨幅 > 100% | 基于 VIX_spot |
| F36 (CVaR) | `(returns[returns < quantile(0.05)].mean()` | 基于 _merged_prices |
| F40 (WCI 财富集中度) | 财富 top 1% / 财富总量 | 暂未集成 (需外部数据源) |

---

## 七、强制验证项（每次更新后必须跑）

```bash
# 1. CSV 表头合规
python3 -c "
import pandas as pd
from pathlib import Path
DATA = Path('example/wif-framework/data')
issues = []
for f in (DATA / 'tickers_20260716').glob('*.csv'):
    base = f.name.split('_')[0]
    h = open(f).readline().strip()
    if base in ['SPY','BND',...] and h != 'Date,Adj Close':
        issues.append(f'{f.name}: {h}')
    if base in ['DGS10','T10YIE','BAMLH0A0HYM2','BAA'] and h != 'Date,Close':
        issues.append(f'{f.name}: {h}')
print('✅ All CSV headers compliant' if not issues else f'❌ {len(issues)} issues: {issues}')
"

# 2. 与原数据零差异
python3 -c "
import pandas as pd
orig = pd.read_csv('ORIG/_merged_prices.csv', parse_dates=['Date'], index_col='Date')
new = pd.read_csv('data/_merged_prices_20260716.csv', parse_dates=['Date'], index_col='Date')
overlap = orig.index[-5:]
max_diff = max(abs(new.loc[d,c] - orig.loc[d,c]) for d in overlap for c in orig.columns if d in new.index)
assert max_diff < 1e-6, f'❌ max diff: {max_diff}'
print('✅ Cross-validation: 0% difference')
"

# 3. NaN 数必须为 0
python3 -c "
import pandas as pd
m = pd.read_csv('data/_merged_prices_20260716.csv', parse_dates=['Date'], index_col='Date')
assert m.isna().sum().sum() == 0, f'❌ {m.isna().sum().sum()} NaN values'
print('✅ No NaN values')
"

# 4. Backtest 跑通
cd example/wif-framework/data && python3 WIF_v59_Backtest.py 2>&1 | tail -10
```

---

## 八、修订历史

| 日期 | 版本 | 变更 |
|:---|:---|:---|
| 2026-07-16 | v1 | 首次建立完整数据规范（基于 2026-07-16 数据更新） |