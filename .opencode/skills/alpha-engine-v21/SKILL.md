---
name: alpha-engine-v21
description: |
  [EN] alpha-engine-v21 — A-share alpha research toolkit. Two capabilities:
  (1) V21 alpha strategy: LazyBear WaveTrend momentum (85%) + 12-month low-volatility (15%), top-10 monthly rebalance long-only A-share portfolio backtest with walk-forward OOS and Deflated Sharpe Ratio validation. Bundled HDF5 covers 2010-2026 (192 months, 3060 stocks).
  (2) Single-stock WaveTrend indicator: compute WT1/WT2 from daily OHLC, or look up pre-computed monthly WT1/WT2 from the bundled HDF5 for consistency with the backtest.
  Use for A-share cross-sectional alpha combination research, single-stock WT screening, or V21 strategy reproducibility audits.

  [中文] alpha-engine-v21 —— A 股 alpha 研究工具集。两大能力：
  (1) V21 alpha 策略：懒熊 WaveTrend 动量 (85%) + 12 月低波动 (15%)，月度调仓 Top-10 多头组合回测，含滚动样本外验证和 Deflated Sharpe Ratio 检验。内置 HDF5 覆盖 2010-2026（192 个月，3060 只股票）。
  (2) 单股 WaveTrend 指标计算：从日频 OHLC 计算 WT1/WT2，或从内置 HDF5 查询预计算的月度 WT1/WT2（保证与回测一致）。
  用于 A 股截面 alpha 组合研究、单股 WT 筛选、或 V21 策略可复现性审计。
category: strategy
---

# alpha-engine-v21 — A-share Alpha Toolkit / A 股 Alpha 工具集

> **TL;DR** — A production-grade A-share alpha engine built on the V21.0 release
> of `22_Alpha投资框架/02_大陆用户版/v21`. Two scripts you actually use:
>
> 1. `scripts/run_backtest.py` — full strategy backtest (TC modelling on by default).
> 2. `scripts/wave_trend.py` — single-stock LazyBear WaveTrend indicator.
>
> Data lives in `data/data_v20.h5` (19 MB, 192 months × 3060 stocks). See
> `references/release-notes-{zh,en}.md` for the full V21.0 release notes.

---

## EN — When to use this skill

| You want to … | Use this |
|---|---|
| Re-run / reproduce the V21 alpha backtest | `python3 scripts/run_backtest.py --periods --walkforward` |
| Get sub-samples + IS/OOS split | `python3 scripts/run_backtest.py --periods` |
| Roll the strategy through time | `python3 scripts/run_backtest.py --walkforward` |
| Compute WaveTrend for one ticker from a CSV | `python3 scripts/wave_trend.py --ticker NAME --csv prices.csv --plot` |
| Read pre-computed monthly WT from the H5 | `python3 scripts/wave_trend.py --ticker 600519-CN --from-h5` |
| Override the H5 location | `--data-path /path/to/data_v20.h5` 或 `$V21_DATA_H5` |
| TC 关闭（仅研究） | `--no-tc` |

### ⚠ WaveTrend 完整历史原则

`wave_trend.py --csv` 模式下，WT1 / WT2 是从**传入价格序列的每一根 K 线**
（从上市日到最新一根）计算的。**不要**预先截断成"最近 12 个月"或"最近 5 年"。
EMA 结构（N2 = 105 个交易日）需要长历史上下文才能产生稳定的、跨股票可比的
WT1 值。

| 模式 | 使用的数据范围 |
|---|---|
| `--from-h5 --ticker X` | H5 已存储从每只股票上市日开始的完整价格计算出的 WT1（1990-12-31 → 2026-07-31，因上市日而异）。 |
| `--csv prices.csv` | 你传入的全部 bars —— 必须涵盖上市日到今天，WT1 才与 V21 可比。CLI 会打印 `[input] N bars span: YYYY-MM-DD → YYYY-MM-DD` 供你审计。 |

JSON 输出中的 `wt1_pct_rank_12m` / `wt1_pct_rank_5y` 字段仅是**描述性参考**
（当前 WT1 在近期历史中的百分位），**不是** WT1 的计算依据。WT1 本身永远来自完整历史。

### ⚠ WaveTrend full-history principle

`wave_trend.py --csv` computes WT1 / WT2 from **the entire price series you
pass in** — from the stock's listing date to the latest bar. Do NOT
pre-truncate to "last 12 months" or "last 5 years"; the EMA structure
(N2 = 105 trading days) depends on long-history context to produce stable,
cross-sectionally comparable WT1 values.

| Mode | What it uses |
|---|---|
| `--from-h5 --ticker X` | H5 stores WT1 computed from each stock's full pre-bundled price history (1990-12-31 → 2026-07-31, depending on listing date). |
| `--csv prices.csv` | Whatever bars you pass in — must span from listing date to today for V21-comparable WT1. The CLI prints `[input] N bars span: YYYY-MM-DD → YYYY-MM-DD` so you can audit this. |

The summary fields `wt1_pct_rank_12m` / `wt1_pct_rank_5y` in the JSON
output are **descriptive context only** — they show where current WT1 sits
relative to recent history, but the WT1 value itself comes from the
full-history computation.

### V21 Headline metrics (192-month sample, 2010-2026)

| Metric | Value |
|---|---|
| Sharpe (annual) | 0.869 |
| NAV | 27.93 |
| Annualised return | 23.1 % |
| Max drawdown | −34.6 % |
| OOS Sharpe (2018-2026) | 1.076 |
| DSR (n_configs=5) | 1.000 |

> ⚠ These numbers are the **V21.0 research release** with `transaction_cost=False`.
> The skill-port default is `transaction_cost=True`, so re-running on bundled data
> will produce a *slightly lower* Sharpe. This is intentional — production honesty.

---

## 中文 — 何时使用此 skill

| 你想做的事 | 用法 |
|---|---|
| 复现 V21 alpha 回测 | `python3 scripts/run_backtest.py --periods --walkforward` |
| 子样本 + IS/OOS 切分 | `python3 scripts/run_backtest.py --periods` |
| 滚动样本外验证 | `python3 scripts/run_backtest.py --walkforward` |
| 用 CSV 计算单股 WaveTrend | `python3 scripts/wave_trend.py --ticker NAME --csv prices.csv --plot` |
| 从 H5 查预计算月度 WT | `python3 scripts/wave_trend.py --ticker 600519-CN --from-h5` |
| 覆盖 HDF5 路径 | `--data-path /path/to/data_v20.h5` 或 `$V21_DATA_H5` |
| TC 关闭（仅研究） | `--no-tc` |

### V21 头条指标（192 月样本，2010-2026）

| 指标 | 数值 |
|---|---|
| Sharpe（年化） | 0.869 |
| NAV | 27.93 |
| 年化收益 | 23.1 % |
| 最大回撤 | −34.6 % |
| OOS Sharpe（2018-2026） | 1.076 |
| DSR（n_configs=5） | 1.000 |

> ⚠ 这些数字是 V21.0 **研究发布版**（`transaction_cost=False`）的产物。
> Skill 移植版的默认是 `transaction_cost=True`，所以在捆绑数据上重跑会产生
> *略低* 的 Sharpe。这是刻意的——生产诚信优先。

---

## Inputs and outputs

### Inputs

| Input | Source | Notes |
|---|---|---|
| `data/data_v20.h5` | Bundled 19 MB HDF5 | 192 months × 3060 stocks, baostock-repaired |
| `config/v21_config.json` | This skill | Single source of truth for weights + filters |
| `--data-path PATH` | CLI override | Bypasses bundled default |
| `V21_DATA_H5` | Env var | Useful in CI / Docker |

### Outputs (written to `results/`)

| File | Contents |
|---|---|
| `equity_v21.csv` | Monthly NAV curve + drawdown |
| `trades_v21.csv` | 189 rebalance records with stock names + SW1 industry |
| `v21_authoritative_results.json` | Metrics + statistical battery + sub-samples + walk-forward |
| `v21_authoritative_results.v1_release.json` | The V21.0 release numbers (TC=off), kept for audit |

### Inputs (wave_trend.py)

| Mode | Required | Optional |
|---|---|---|
| `--csv path` | `date,close` columns | `open,high,low,volume` ignored |
| `--from-h5` | `--ticker 600519-CN` | — |

---

## Architecture / 架构

```
alpha-engine-v21/
├── SKILL.md                                  ← this file
├── README.md                                 ← slim bilingual design doc
├── config/
│   └── v21_config.json                       ← weights + filters + data path
├── data/
│   └── data_v20.h5                           ← bundled 192-month A-share HDF5
├── scripts/
│   ├── alpha_engine.py                       ← BacktestConfig + run_backtest + filters + score_v21
│   ├── run_backtest.py                       ← CLI: full / periods / walkforward
│   ├── statistical_tests.py                  ← Z-test + Bonferroni + bootstrap + DSR
│   ├── data_loader.py                        ← HDF5 path resolution + structure check
│   └── wave_trend.py                         ← single-stock LazyBear WT
├── results/                                 ← sample outputs (V21.0 release numbers)
│   ├── equity_v21.csv
│   ├── trades_v21.csv
│   └── v21_authoritative_results.v1_release.json
└── references/
    ├── release-notes-zh.md                   ← V21.0 release notes (Chinese)
    └── release-notes-en.md                   ← V21.0 release notes (English translation)
```

### Engine dependencies

* `pandas`, `numpy`, `scipy`, `h5py` (already in `vibe-trading-quanta` requirements)
* `matplotlib` — optional, only for `--plot` in wave_trend.py
* `vibe_trading_quanta.backtest.validation.deflated_sharpe_ratio` — the DSR
  function (added upstream as part of this skill's integration)

---

## Path resolution / 路径解析

`data_loader.resolve_data_path()` checks in order:

1. `path` argument (programmatic callers)
2. `$V21_DATA_H5` env var (CI / deployment)
3. `config/v21_config.json` `data_h5` field (skill-level)
4. `<skill_root>/data/data_v20.h5` (bundled default)

The first one that exists wins. If none exist, a clear `FileNotFoundError`
listing all candidates is raised.

---

## Statistical battery / 统计检验

`statistical_tests.honest_statistical_tests(returns, n_configs=5)` returns:

| Test | Source | Notes |
|---|---|---|
| `sharpe`, `sharpe_annual` | periodic Sharpe | `sr_periodic × √12` for monthly |
| `n_months` | `len(returns)` | 192 in V21 |
| `skewness`, `kurtosis_total` | Pearson | `kurtosis_total = excess + 3` |
| `z_iid`, `p_iid` | standard normal Z | IID assumption |
| `z_nw`, `p_nw` | Newey-West HAC | `nw_lags = n^(1/4)` |
| `p_bonferroni` | `min(p_iid × n_configs, 1)` | conservative multiple-test correction |
| `bootstrap_ci_95` | block bootstrap, block=12, seed=42 | 10 000 resamples |
| `bootstrap_p_positive` | P(SR_annual > 0) under bootstrap | |
| `dsr` | López de Prado (2018) Eqs 12.7-12.8 | **delegated to `vibe_trading_quanta.backtest.validation.deflated_sharpe_ratio`** |

---

## Differences from V21.0 release / 与 V21.0 发布版的差异

| Area | V21.0 release | alpha-engine-v21 skill |
|---|---|---|
| `transaction_cost` default | `false` (research simplification) | **`true` (production honest)** |
| Path resolution | Hardcoded absolute path | Env var → config → bundled default |
| Scoring variants | v8 / v30 / v31 / v32 (V19 baseline included) | **Only `score_v21`** (V21 strategy) |
| DSR computation | Inline in `honest_statistical_tests` | Delegated to `vibe_trading_quanta.backtest.validation.deflated_sharpe_ratio` |
| Language | Chinese docstrings + comments | **English docstrings** (bilingual SKILL.md / README.md / release notes) |
| Single-stock WT | Not available | **`wave_trend.py`** — compute or H5 lookup |

---

## Pitfalls / 常见陷阱

* **TC default change** — if you compare to V21.0 numbers, either pass `--no-tc`
  or accept the lower (more honest) Sharpe.
* **`close_7d` is ≈ `prices`** — the H5's "7-day execution-price shift" was not
  actually implemented in V21.0; backtest returns are effectively monthly
  price ratios. See `references/release-notes-en.md` §Execution-Price Caveat.
* **2008-2009 not in sample** — V21 data starts 2010-01; GFC coverage is
  absent. Don't claim GFC robustness.
* **2025+ mcap is price-derived** — the H5's 2025 market-cap is imputed from
  Dec-2024 reference × price-ratio, not direct observation. This is documented
  in the V21.0 release notes.
* **DSR ≠ forecast** — DSR tells you the strategy is unlikely to be pure luck;
  it says nothing about whether the alpha will persist. The skill does no live
  trading.
