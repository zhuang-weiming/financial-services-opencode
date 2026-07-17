# WIF v5.9 数据更新流程 (DATA UPDATE PROCEDURE)

> **版本**: 2026-07-16
> **适用范围**: 任何需要更新 WIF v5.9 数据到新日期的场景
> **文档目的**: 沉淀 2026-07-16 首次数据更新的全部经验教训，确保未来更新可复现。

---

## 一、更新前准备

### 1.1 检查项

```bash
# 1. 当前 WIF 数据日期
ls /Users/weimingzhuang/Documents/source_code/financial-services-opencode/example/wif-framework/data/_merged_prices_*.csv

# 2. 当前回测引擎的 DATA_DIR 路径
grep "^DATA_DIR" /Users/weimingzhuang/Documents/source_code/financial-services-opencode/example/wif-framework/data/WIF_v59_Backtest.py

# 3. 可用工具
echo "FRED_API_KEY set: $([ -n "$FRED_API_KEY" ] && echo YES || echo NO)"
python3 -c "import yfinance; print('yfinance:', yfinance.__version__)"
python3 -c "import pandas; print('pandas:', pandas.__version__)"
pip list 2>&1 | grep -E "fredapi|akshare|yfinance"
```

### 1.2 环境与依赖

**必备**:
- Python 3.10+
- pandas >= 2.0
- numpy >= 1.24
- yfinance >= 0.2 (备用)
- fredapi (可选用，公开 CSV 不需要 API key)

**可选**:
- FRED_API_KEY (注册 https://fred.stlouisfed.org/docs/api/api_key.html)
- akshare (A 股 fallback)
- Morningstar MCP (Tier 1 首选)
- FactSet MCP (Tier 1 备选)

### 1.3 地理限制

⚠️ **关键**: 如果在中国大陆，Yahoo Finance 直接被拦（"Yahoo's suite of services will no longer be accessible from mainland China"）。这意味着:
- yfinance 会持续触发 rate limit (即使不在大陆也会偶发)
- Yahoo 直接 HTTP 请求会返回 sad-panda 页面
- **必须用 Morningstar MCP 或 FRED 作为主数据源**

---

## 二、Step-by-Step 更新流程

### Step 1: 拉取数据（按优先级）

#### 1.1 ETF 时序 (Morningstar MCP HS793)

```python
# Morningstar MCP 调用（每批最多 10 个 ticker）
import asyncio
morningstar_ids = {
    "SPY": "FEUSA00001", "BND": "FOUSA06C1Y", "GLD": "FEUSA04AD2", ...
}
# 分批调用 morningstar-data-tool 的 HS793 datapoint
# 参数: start_date=YYYY-MM-DD, end_date=YYYY-MM-DD
# 输出: 时序数据列表 [(date, value), ...]
```

**关键点**:
- 每次最多 10 个 ticker (超过会被截断)
- HS793 是 "Daily Return Index"，已含分红再投资（等同于 Adjusted Close）
- 数据延迟 1 天（如 7/16 早晨调用，最新数据到 7/15）

#### 1.2 FRED 利率 (公共 CSV 直链)

```python
import urllib.request

def fetch_fred(series_id, start='20260609', end='20260716'):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start}&coed={end}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8')

# FRED 关键系列
fred_series = {
    "DGS10":  "10年期国债收益率 (%)",
    "T10YIE": "10年期盈亏平衡通胀率 (%)",
    "BAMLH0A0HYM2": "ICE BofA US HY OAS 利差 (%)",
    "VIXCLS": "CBOE VIX 每日收盘",
    "BAA":    "Moody's Baa 企业债收益率 (%) - 月度",
}
```

**关键点**:
- **不需要 API key**（公共 CSV 端点）
- 月度数据（BAA, CPI, UNRATE）会返回全历史，需要自己过滤日期
- VIXCLS 是 VIX 官方数据，等同 CBOE 收盘
- BAA 是月度滞后（最新发布点 2026-06-01 = 6.00%），需要外推

#### 1.3 VIX3M Proxy (Morningstar MCP)

⚠️ **关键限制**: Morningstar MCP 不支持 `^VIX3M` ticker（`^` 前缀被拒）。

**代理方案**: 用 **ProShares VIX Mid-Term Futures ETF (VIXM)** 作为代理。

```python
# Morningstar ID
VIXM_ID = "F00000LI7D"  # ProShares VIX Mid-Term Futures ETF

# ⚠️ 警告: VIXM ETF 价格 (USD) ≠ VIX3M 指数 (Index Points)
# 数值范围完全不同，但历史相关性 > 0.85
# 在生产环境应替换为 CBOE ^VIX3M 直接数据
```

#### 1.4 yfinance (备用 - 经常被限速)

```python
import yfinance as yf
import time

# 经常触发 YFRateLimitError
# 解决方案: 多次重试 + 退避
for ticker in tickers:
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        # ...
    except Exception as e:
        if 'RateLimit' in str(e):
            time.sleep(60)
            # 重试
```

---

### Step 2: 写入标准格式 CSV

#### 2.1 命名约定

```
格式: {TICKER}_2026MMDD_2026MMDD.csv
例: SPY_20260609_20260716.csv
```

⚠️ **每次更新都用最新日期作为结束日期**，不覆盖原文件。

#### 2.2 列名规范（严格）

| 数据类型 | 列名 | 例子 |
|:---|:---|:---|
| ETF 价格 | `Date,Adj Close` | SPY_20260609_20260716.csv |
| FRED 利率 | `Date,Close` | DGS10_2007_2026.csv |
| VIX | `Date,VIX` | VIX_spot_20260609_20260716.csv |
| VIX3M proxy | `Date,VIX3M` | VIX3M_proxy_VIXM_20260609_20260716.csv |
| VIXTERM | `Date,VIXTERM` | VIXTERM_20260609_20260716.csv |
| Credit Spread | `Date,CreditSpread_bp` | CreditSpread_BAA_1986_2026.csv |

**为什么 `Adj Close` 而非 `Close`**:
- WIF v5.9 的 `load_raw_etf` 函数标准: `col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'`
- WIF 设计文档 v5.2-patch 说明: "yfinance auto_adjust=True 替代 Adj Close"
- **但回测引擎的 glob 模式读取的 CSV 文件实际用的就是 `Adj Close`**（早期 yfinance 命名保留）
- 任何用 `Close` 的 ETF CSV 都会被 fallback 到 `Close`（语义等价但格式不一致）

#### 2.3 单位规范（严格）

| 数据 | 单位 | 列表示例 | 错误示例 |
|:---|:---|:---|:---|
| ETF 价格 | USD | `1369.98` (1369.98 美元) | `13.6998` |
| 利率 (DGS10, T10YIE, BAA) | **百分比 (%)** | `4.20` (4.20%) | `0.042` |
| 信用利差 | **bp (基点)** | `180.0` (180 bp = 1.80%) | `1.80` |
| VIX / VIX3M / VIXTERM | Index Points | `15.67` (15.67 点) | `0.1567` |

⚠️ **最常见的错误**: 把利率当小数存 (例如 DGS10=0.042 而非 4.20)。这会让 CSI 计算中的 Z-score 完全错误。

---

### Step 3: 合并 `_merged_prices_2026MMDD.csv`

```python
import pandas as pd
from pathlib import Path

# 1. 读原文件
orig = pd.read_csv(ORIG_DATA_DIR / "_merged_prices.csv", parse_dates=['Date'], index_col='Date')

# 2. 读新数据
new = pd.read_csv(NEW_DATA_DIR / "etf_timeseries_2026MMDD.csv", parse_dates=['Date'], index_col='Date')
new_vix = pd.read_csv(NEW_DATA_DIR / "VIX_spot_*.csv", parse_dates=['Date'], index_col='Date')
new_vixterm = pd.read_csv(NEW_DATA_DIR / "VIXTERM_*.csv", parse_dates=['Date'], index_col='Date')

# 3. 合并: concat + dedup (新数据覆盖旧数据) + ffill
combined = pd.concat([orig, new, new_vix, new_vixterm])
combined = combined[~combined.index.duplicated(keep='last')]  # 新覆盖旧
combined = combined.sort_index().ffill()

# 4. 写出
combined.to_csv(OUT_DATA_DIR / "_merged_prices_2026MMDD.csv", index_label='Date')
```

**关键点**:
- 用 `keep='last'` 让新数据覆盖旧数据（而不是反过来）
- 排序后 ffill 处理节假日导致的缺失
- 检查: NaN 数必须为 0

---

### Step 4: 交叉验证（强制）

```python
# 1. 重叠区段零差异
orig = pd.read_csv(ORIG / "_merged_prices.csv", parse_dates=['Date'], index_col='Date')
new = pd.read_csv(OUT / "_merged_prices_2026MMDD.csv", parse_dates=['Date'], index_col='Date')
overlap = orig.index[-5:]
max_diff = max(
    abs(new.loc[d, c] - orig.loc[d, c])
    for d in overlap for c in orig.columns if d in new.index
)
assert max_diff < 1e-6, f"❌ Cross-validation failed: max_diff={max_diff}"

# 2. 列名规范
for f in (OUT / "tickers_2026MMDD").glob("*.csv"):
    base = f.name.split("_")[0]
    h = open(f).readline().strip()
    if base in ETF_TICKERS and h != "Date,Adj Close":
        raise ValueError(f"❌ {f.name}: ETF must use 'Adj Close', got {h!r}")
    if base in ["DGS10","T10YIE","BAMLH0A0HYM2","BAA"] and h != "Date,Close":
        raise ValueError(f"❌ {f.name}: FRED must use 'Close', got {h!r}")

# 3. NaN 数为 0
assert new.isna().sum().sum() == 0, f"❌ {new.isna().sum().sum()} NaN values"
```

**为什么必须验证**:
- 没有验证就可能引入**静默错误**（如单位错、列名错）
- 这种错误在生产环境里可能要等几个月才被发现

---

### Step 5: 修改 WIF_v59_Backtest.py 并跑通

#### 5.1 需要的 Patches

```python
# PATCH 1: load_raw_etf 严格模式 (移除静默 fallback)
# 在原代码:
#     col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
# 改为:
if 'Adj Close' in df.columns:
    col = 'Adj Close'
elif 'Close' in df.columns:
    col = 'Close'
else:
    raise ValueError(
        f"Cannot find price column in {path}. "
        f"Expected 'Adj Close' (ETF) or 'Close' (FRED). "
        f"Found columns: {list(df.columns)}"
    )

# PATCH 2: pandas 2.x resample 'M' -> 'ME'
# 在原代码:
#     monthly_idx = prices.resample('M').last().index
# 改为:
try:
    monthly_idx = prices.resample('ME').last().index
except ValueError:
    monthly_idx = prices.resample('M').last().index
```

⚠️ **绝对不要**用"取第一个非 Date 列"作为 fallback——这是**反模式**。理由见 DATA_SPECIFICATION.md 第 8 节。

#### 5.2 修改路径

```python
# 修改 WIF_v59_Backtest.py 的路径常量
OUT_DIR  = '/path/to/v5.9_backtest_2026MMDD'
DATA_DIR = '/path/to/v5.9_backtest_2026MMDD/data'
```

#### 5.3 跑回测

```bash
cd /path/to/v5.9_backtest_2026MMDD
python3 WIF_v59_Backtest.py 2>&1 | tail -30
```

**期望输出**:
```
v5.9 调仓次数: 4 次 | 累计成本: $XXX
v6.8.1 调仓次数: 4 次 | 累计成本: $XXX
...
✅ 对比报告已保存: WIF_v59_Report_20260608.html
```

---

### Step 6: 复制产物到本项目

```bash
PROJ=/Users/weimingzhuang/Documents/source_code/financial-services-opencode/example/wif-framework/data
cp /path/to/v5.9_backtest_2026MMDD/WIF_v59_Backtest.py $PROJ/
cp /path/to/v5.9_backtest_2026MMDD/WIF_v59_Report_*.html $PROJ/WIF_v59_Report_2026MMDD.html
cp /path/to/v5.9_backtest_2026MMDD/WIF_v59_nav_*.csv $PROJ/WIF_v59_nav_2026MMDD.csv
cp /path/to/v5.9_backtest_2026MMDD/WIF_v59_trade_log_*.csv $PROJ/WIF_v59_trade_log_2026MMDD_HSCBC.csv
```

---

## 三、经验教训（沉淀）

### 3.1 错误 1: 静默 fallback 掩盖列名错误

**问题**: 我最初版本的 `load_raw_etf` patch:
```python
else:
    col = [c for c in df.columns if c != 'Date'][0]  # ← 取第一个非 Date 列
```

**为什么错**: 如果未来 WIF 上游数据源新增了"Volume"或"Adj Volume"列，fallback 就会**错误地**把"Adj Volume"当成价格列。这种静默错误在生产环境中会造成灾难性的误算。

**正确做法**: 严格模式 — 列名不符预期时立即报错。

### 3.2 错误 2: 数据单位混用

**问题**: FRED 利率系列 (`DGS10`/`T10YIE`/`BAA`) 单位是 **百分比 (%)**，不是小数。最初我把 DGS10 = 4.20 存成 4.20 是对的，但如果是 0.042 (小数形式)，CSI 计算的 Z-score 会变成**100 倍的偏移**。

**正确做法**: 在 DATA_SPECIFICATION.md 第 3.3 节明确标注所有数据的单位，并在验证脚本中检查数值范围（DGS10 应在 0.5-5.0%，不会是 0.005-0.05）。

### 3.3 错误 3: VIX3M 数据缺失未显式记录

**问题**: Morningstar MCP 不支持 `^VIX3M` ticker，必须用 VIXM ETF 代理。但 ETF 价格 (USD, 14-16 区间) 跟 VIX3M 指数 (Index Points, 13-25 区间) **完全不同**。

**正确做法**: 
- 在 vix_metadata_20260716.json 中**显式标注**这是 proxy，不是真值
- 在 DATA_SPECIFICATION.md 第 3.4 节说明这个代理关系
- 未来生产环境应替换为 CBOE 原始 VIX3M 数据

### 3.4 错误 4: FRED 公共 CSV 月度数据的行为

**问题**: FRED 公共 CSV 端点对**日级数据**（如 DGS10, VIXCLS）严格按 `cosd`/`coed` 时间范围返回；但对**月度数据**（如 BAA, CPI, UNRATE）会返回全历史。

**正确做法**: 拉月度数据后自己按日期过滤（不要依赖 URL 参数）。

### 3.5 经验: yfinance 限速严重

**问题**: yfinance 经常触发 `YFRateLimitError`，即使在不同时区也会偶发。

**正确做法**:
- 把 Morningstar MCP 作为 Tier 1 首选，yfinance 仅作 Tier 3 兜底
- 如果必须用 yfinance，加入重试+退避逻辑

### 3.6 经验: 7/16 当日数据时效性差异

**重要发现**: 2026-07-16 当日不同数据源的可用性:

| 数据源 | 7/16 当日数据 |
|:---|:---:|
| Morningstar MCP | ✅ |
| FRED T10YIE | ✅ |
| VIX3M proxy (VIXM ETF) | ✅ |
| FRED VIXCLS | ❌ (T+1 滞后) |
| FRED DGS10 | ❌ (T+1 滞后) |
| FRED BAMLH0A0HYM2 | ❌ (T+1 滞后) |
| FRED BAA | ❌ (月度滞后，最新 6/1) |

**正确做法**: 在 `_merged_prices_2026MMDD.csv` 中，最后一日的 VIX/VIXTERM/DGS10 等字段是 **ffill 值**（前一日的值），必须在 vix_metadata 和 DATA_SPECIFICATION 中显式标注。

### 3.7 经验: 文件路径硬编码问题

**问题**: 原 WIF_v59_Backtest.py 硬编码 `/Users/hello/Documents/Obsidian Vault/...`，跨用户/跨机器不可移植。

**正确做法**:
- 创建 `v5.9_backtest_2026MMDD/` 子目录独立运行（不动原文件）
- 复制脚本到子目录，修改 DATA_DIR/OUT_DIR 指向子目录
- 跑完后把脚本 + 报告复制到本项目 `data/`
- 这样原 v5.9 目录完全不变

---

## 四、常见问题 (FAQ)

### Q1: 某个 ticker 在 Morningstar 找不到怎么办？
A: 用 `morningstar-id-lookup-tool` 找到 Morningstar ID，或 fallback 到 yfinance。如果都失败，跳过这个 ticker 但记录在 metadata 中。

### Q2: FRED 数据某天缺失怎么办？
A: 用前一日的值填充（ffill）。但必须在 metadata 中标注缺失日期。

### Q3: BAA 是月度数据，怎么办？
A: 用最新月度值外推到所有后续日期。明确标注外推范围（如 2026-06-09 起外推自 2026-06-01）。

### Q4: 回测引擎跑出负的 Sharpe 或异常值？
A: 检查数据的**单位**和**列名**。80% 的错误是单位问题（如 DGS10 用 4.20 vs 0.042）。

### Q5: `_merged_prices_2026MMDD.csv` 最后一行的 VIX 是 NaN？
A: FRED VIXCLS 是 T+1 发布。最新数据通常滞后 1 天。如果必须是 NaN，用 ffill 填充前一交易日值。

### Q6: VIX3M proxy 跟真实 VIX3M 差多少？
A: 历史相关性 > 0.85，但绝对值不同（VIXM ETF 是 14-16 区间，VIX3M 指数是 13-25 区间）。生产环境应替换为 CBOE 原始数据。

### Q7: 多个 ETF CSV 的列名不一致（有的 `Adj Close` 有的 `Close`）？
A: **严格按 WIF 标准**：ETF = `Adj Close`，FRED = `Close`。不一致会导致静默 fallback 到 `Close`，虽然语义等价，但破坏了工程严谨性。

---

## 五、修订历史

| 日期 | 版本 | 变更 |
|:---|:---|:---|
| 2026-07-16 | v1 | 首次建立完整更新流程（基于 2026-07-16 数据更新） |