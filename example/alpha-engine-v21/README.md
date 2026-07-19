# alpha-engine-v21 Cookbook

**Sample questions** for the `alpha-engine-v21` skill. Routes through `alpha-researcher` / `backtest-builder` / `factor-researcher` (subagents load the skill on-demand).

## Trigger keywords

Wealth-Guide routes to the alpha-researcher (which then loads the skill) when the
question contains any of:

- **English**: "V21", "alpha engine v21", "lazybear", "WaveTrend", "WT1", "WT2", "low-vol A-share", "Deflated Sharpe Ratio", "A-share monthly alpha", "Wall Street momentum alpha"
- **中文**: "V21", "懒熊振荡器", "低波动 A 股", "动量 alpha", "A 股月频 alpha", "Deflated Sharpe 检验"

## Skill location

`.opencode/skills/alpha-engine-v21/` — bundled HDF5 (`data/data_v20.h5`, 19 MB) +
Python scripts (`run_backtest.py`, `wave_trend.py`, etc.).

## Data Files

| File | Purpose |
|---|---|
| `data/v21_release_summary.csv` | Headline metrics from V21.0 release (TC=off) — verification target |
| `data/v21_subperiods.csv` | Sub-sample Sharpe (2010-2014, 2015-2018, etc.) + IS/OOS |
| `data/v21_paper_trade_demo.json` | Sample top-10 picks from a real paper-trade (2026-04-30 → 2026-06-30) |
| `data/sample_wt_input_moutai.csv` | Synthesized 24-year daily closes for WaveTrend demo |
| `data/sample_wt_input_truncated.csv` | 252-day truncated CSV — **educational only** (shows what NOT to do) |
| `data/wt_summary_demo.json` | Sample output of `wave_trend.py --csv --json` |
| `data/h5_health_check_demo.json` | Sample `data_loader.health_check()` output |
| `data/v21_dsr_demo.json` | DSR values across hypothetical n_configs |

## Other resources

- `references/release-notes-zh.md` — V21.0 中文原始发布说明
- `references/release-notes-en.md` — English translation
- `README.md` in skill directory — slim bilingual design doc
- `SKILL.md` in skill directory — main skill manifest (loaded by agents)