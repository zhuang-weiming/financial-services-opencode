# alpha-engine-v21 — Design Document / 设计文档

> Slim design doc — full V21.0 release notes are in
> `references/release-notes-{zh,en}.md`.

---

## 1. Strategy (EN)

V21 is a 2-factor A-share long-only portfolio:

```
V21 score = lv × 0.15 + wt_mom × 0.85
              ↑            ↑
          low-vol       LazyBear WaveTrend
          12-month      momentum oscillator
          rolling σ(r)  (close-only adaptation, N1=10w, N2=21w)
```

Both factors are ranked cross-sectionally within the post-filter valid pool
(after OB / liquidity / bad-returns filters) using `rank(pct=True,
na_option='keep')` to (0, 1), then weighted-summed.

### Filters applied before scoring

| Filter | Threshold | Purpose |
|---|---|---|
| Adaptive OB (by mcap) | `WT1 > 53 + 40 × mcap_pct` | Drop overbought names; small caps get relaxed threshold |
| Liquidity | `mcap ≥ 2e9 CNY` | Exclude micro-caps |
| Bad-returns (last month) | `|r_last_month| ≤ 0.40` | Drop data-quality outliers without look-ahead |
| Industry cap | `max 3 stocks per SW1 industry` | Diversify within selection |

### Selection

Top 10 by composite score, max 3 per SW1 industry, equal-weight.

---

## 1. 策略（中文）

V21 是一个 2 因子 A 股多头组合：

```
V21 评分 = lv × 0.15 + wt_mom × 0.85
              ↑            ↑
          低波动异常       懒熊 WaveTrend
          12 个月滚动      动量振荡器
          σ(r)（取负）    (close-only 适配，N1=10 周, N2=21 周)
```

两个因子在 OB / 流动性 / 坏收益过滤后的"有效池"内做**截面** `rank(pct=True,
na_option='keep')` 归一到 (0, 1)，再加权求和。**不是**对全 A 股做截面排序。

### 评分前过滤

| 过滤器 | 阈值 | 目的 |
|---|---|---|
| 自适应 OB（按市值） | `WT1 > 53 + 40 × mcap_pct` | 剔除超买股；小盘股阈值放宽 |
| 流动性 | `市值 ≥ 20 亿` | 排除微盘股 |
| 坏收益（上一月） | `\|r 上月\| ≤ 0.40` | 剔除数据质量异常股（无前视） |
| 行业上限 | `SW1 一级行业最多 3 只` | 持仓行业分散 |

### 选股

按复合评分选前 10 名，单行业最多 3 只，等权。

---

## 2. Backtest performance / 回测表现

### Full sample (192 months, 2010-01 → 2026-06) / 全样本

These are V21.0's published numbers with `transaction_cost=False`. The skill
default is `TC=true`, so re-runs will produce slightly lower Sharpe.

| Metric | V21.0 (TC=off) |
|---|---|
| Sharpe (annual) | 0.869 |
| NAV | 27.93 |
| Annual return | 23.1 % |
| Max drawdown | −34.6 % |
| Positive months | 97/192 (51 %) |
| Avg turnover | 0.73 |

### Statistical battery (n_configs=5)

| Test | V21.0 value | Decision |
|---|---|---|
| `z_iid` p | 0.0003 | PASS @ 1 % |
| `z_nw` (Newey-West) p | 0.0001 | PASS @ 1 % |
| Bonferroni (n=5) | 0.0015 | PASS @ 1 % |
| Bootstrap 95 % CI | [0.564, 1.372] | lower > 0 ✓ |
| P(SR > 0) | 1.0000 | PASS |
| **DSR (deflated)** | **1.0000** | multiple-test extreme winner |

### IS / OOS split (cutoff 2017-12-31)

| Segment | Sharpe |
|---|---|
| IS (2010-2017) | +0.665 |
| **OOS (2018-2026)** | **+1.076** |

OOS > IS is a strong anti-overfitting signal.

### Sub-samples / 子样本

| Period | Sharpe |
|---|---|
| 2010-2014 | +0.506 |
| 2015-2018 | +0.798 |
| 2019-2021 | +1.202 |
| 2022-2025 | +1.296 |
| 2026 (Jan-Jun) | +0.539 (observation only) |

### Walk-forward OOS (12-month non-overlapping tests, 36-month train)

13 windows: mean WF Sharpe **0.939**, 12/13 positive, none below −0.5.

---

## 3. Engine flow / 引擎主循环

```
for each month t in 2010-01 … 2026-06:
    if t < warmup:        NAV flat at 1.0
    if t corrupt:         cash 1 month (currently no months flagged corrupt)

    hist = last 24 months of prices
    ob_keep  = adaptive OB filter on wt1 / mcap
    liq_pass = mcap ≥ 2e9 filter
    bad_pass = last-month |r| ≤ 0.40 filter (NO look-ahead)
    valid    = intersection of all three

    score = score_v21(prev_date, valid, hist_valid, wt1, wt2, mcap, ind_map)
    top_n = select_top_n(score, valid, ind_map, n_hold=10, max_per_ind=3)

    ret = mean(close_7d[t][top_n] / close_7d[t-1][top_n] - 1)
    if transaction_cost and trades > 0:
        ret -= tc  # bilateral commission + small-cap impact surcharge

    NAV[t] = NAV[t-1] * (1 + ret)
```

---

## 4. Risk model / 风险模型

| Component | V21 setting |
|---|---|
| Transaction cost | **`true` by default in skill** (V21.0 was `false`) |
| Liquidity filter | retained |
| Adaptive OB filter | retained |
| Bad-returns filter | retained (last-month only — anti-look-ahead) |
| Industry cap | retained (max 3 per SW1 industry) |
| Cash reserve | none (always 10/10 invested) |
| Slippage | not modelled |
| Stamp tax | included in `compute_tc_with_impact` (A-share sell-only) |
| Stop-loss / trailing | none (alpha is the stop) |

### `compute_tc_with_impact` (per turnover)

* Base bilateral rate: 0.18 % (commission 万2.5 + transfer fee 万0.1 + stamp tax 万5 sell)
* Small-cap surcharge: positions with mcap < 5e9 carry an extra 0.5 %×2 to model
  market-impact in less liquid names
* Weighted by `traded_count / n_hold`

---

## 5. Data / 数据

| Dataset | Source | Coverage |
|---|---|---|
| Prices | V19 base + baostock fill for 2024 frozen months | 2010-01 → 2026-06 |
| Market cap | V19 + baostock fill for 2010-2014 / 2024; price-derived for 2025+ | 2010-01 → 2026-06 |
| Industry | SW1 mapping (JSON attr) | static |
| Stock names | Chinese names (JSON attr) | static |
| WT1 / WT2 monthly | Pre-computed from daily closes (LazyBear N1=50, N2=105) | matches price panel |
| Close_7d | Same as `prices` (94 % identical) | ⚠ not a real 7-day shift |
| Bad returns mask | Pre-computed data-quality flags | matches price panel |

---

## 6. Limitations / 重要限制

These limitations are inherited from V21.0 and persist in the skill port:

1. **`close_7d` ≈ `prices`** — the H5's "month-end + 7 trading days" execution
   timing was not actually implemented; backtest returns are effectively
   month-on-month price ratios.
2. **2008-2009 missing** — data starts 2010-01; GFC coverage absent.
3. **2025+ mcap is price-derived** — Dec-2024 reference × price-ratio. Less
   reliable for newly-listed or split-adjusted names.
4. **High turnover (0.73)** — 10-name rotation each month requires real-money
   liquidity; paper-trade first.
5. **`transaction_cost` change** — V21.0 numbers use TC=off; this skill's
   default is TC=on. Use `--no-tc` to reproduce V21.0.
6. **A-share only** — the H5 schema is A-share specific. US/HK/crypto need a
   different data pipeline.

---

## 7. References / 引用

* **WaveTrend** — LazyBear, TradingView community indicator (public domain).
* **DSR** — López de Prado, *Advances in Financial Machine Learning* (2018),
  Eqs 12.7-12.8.
* **Newey-West HAC** — Newey & West (1987).
* **A-share low-volatility anomaly** — 王志强 et al., A 股横截面异象研究系列.
