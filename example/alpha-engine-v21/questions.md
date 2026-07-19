# alpha-engine-v21 Skill — Example Questions

> **Routing trigger keywords:** V21, alpha engine v21, lazybear, WaveTrend, WT1, WT2, low-vol A-share, Deflated Sharpe Ratio, A-share monthly alpha, lazybear 振荡器, 低波动 A 股, A 股月频 alpha, 华尔街动量 alpha
>
> Wealth-Guide dispatches to `alpha-researcher` / `backtest-builder` / `factor-researcher`,
> which load the `alpha-engine-v21` skill via the `skill` tool.

**Data Files (in `data/`):**

- `v21_release_summary.csv` — V21.0 published headline metrics (TC=off)
- `v21_subperiods.csv` — Sub-sample Sharpe + IS/OOS splits
- `v21_paper_trade_demo.json` — Sample top-10 paper-trade picks
- `sample_wt_input_moutai.csv` — Synthesized 24-year daily closes for WaveTrend demo
- `sample_wt_input_truncated.csv` — 252-day truncated CSV (educational: shows what NOT to do)
- `wt_summary_demo.json` — Sample `wave_trend.py --csv --json` output
- `h5_health_check_demo.json` — Sample HDF5 health-check output
- `v21_dsr_demo.json` — DSR sensitivity table across n_configs

---

## Question 1: 复现 V21.0 发布版数字 — A 股 WT 动量 + 低波动 alpha 策略

```
我想复现 alpha-engine-v21 skill 的 V21.0 发布版回测数字。

Reference: data/v21_release_summary.csv, data/v21_subperiods.csv

V21 策略 = 懒熊 WaveTrend 动量 (85%) + 12 月低波动 (15%)，月度调仓 Top-10 多头。
V21.0 发布数字 (TC=off, 192 月)：
  - Sharpe 0.869, NAV 27.93, DD -34.6%
  - IS Sharpe 0.665, OOS Sharpe 1.076
  - DSR = 1.000 (López de Prado, n_configs=5)
  - 13 窗口 walk-forward 平均 Sharpe 0.939

Please:
1) 加载 skill: skill("alpha-engine-v21")
2) 用 --no-tc 跑一次完整回测，验证 Sharpe ≈ 0.869 ± 0.01
3) 加 --periods 跑子样本，确认 4 段 (2010-2014/2015-2018/2019-2021/2022-2025) 都为正
4) 加 --walkforward 跑 13 窗口，确认 12/13 为正
5) 报告完整 IS/OOS 切分 (cutoff = 2017-12-31)
6) 用 statistical_tests.py 看 Bonferroni p 和 DSR
7) 解释 V21.0 数字 vs skill 默认 TC=on 数字的差异
```

---

## Question 2: 单股 WaveTrend 计算 — 茅台 2001 年上市至今的动量周期

```
我想看 600519-CN (贵州茅台) 上市以来的完整 WaveTrend 周期。

Reference: data/sample_wt_input_moutai.csv (24 年日线, 2001-08-27 → 2025-01-01)

⚠️ 重要原则：WaveTrend 必须从上市日开始用完整历史计算，不要只截取最近 1 年或 5 年。
   EMA 结构 (N2=105 个交易日) 需要长历史才能产生稳定的、跨股票可比的 WT1 值。

Please:
1) 加载 skill: skill("alpha-engine-v21")
2) 用 wave_trend.py 计算茅台的 WT1 / WT2：
   python3 scripts/wave_trend.py --csv data/sample_wt_input_moutai.csv --ticker 600519-CN --json --plot
3) 报告：
   - 当前 WT1 / WT2 值
   - 24 年 WT1 的 min/max/mean（横跨多个牛熊周期）
   - 当前 WT1 在 12 月/5 年的百分位（描述性参考，不是计算依据）
   - 当前的 regime 分类（超买/多头/空头/超卖）
4) 用 --plot 画出 close + WT1 + WT2 双面板图
5) 对比：如果你把数据截断到最近 252 天再算 WT1，差异有多大？
   （可以跑 data/sample_wt_input_truncated.csv 看效果——后者是教学反例）
6) 解释 N1=50 / N2=105 这两个参数的含义和半衰期
```

---

## Question 3: Deflated Sharpe Ratio 检验 — V21 的 0.87 SR 在多重检验后还站得住吗？

```
我想对 V21 策略的 Sharpe = 0.869 做 Deflated Sharpe Ratio 检验，
确认它不是从 5 个变体中"挑出来"的过拟合结果。

Reference: data/v21_dsr_demo.json (sample DSR table), data/v21_release_summary.csv

V21.0 报告的 DSR = 1.000，但我想自己重新跑一遍，
并且理解 DSR 公式对 n_configs 的敏感性。

Please:
1) 加载 skill: skill("alpha-engine-v21")
2) 用 statistical_tests.py 调用 vibe_trading_quanta.backtest.validation.deflated_sharpe_ratio()
3) 用 v21_authoritative_results.json 的月度收益序列作为输入
4) 扫描 n_configs ∈ {1, 5, 10, 50, 100, 500, 1000}
5) 报告每个 n_configs 对应的：
   - sr_observed (年化)
   - sr_benchmark (随机试验下的临界值)
   - dsr (观察 SR > sr_benchmark 的概率)
6) 解释：
   - DSR=1.0 在 n_configs=5 意味着什么？
   - 当 n_configs=1000 时 DSR 仍 > 0.97，结论如何变化？
   - 为什么 DSR ≠ "alpha 会持续"？
7) 对比 v21_dsr_demo.json (toy) 和你跑出来的实际数字
```

---

## Question 4: 今天 10 万人民币该买哪些股票？V21 实盘模拟

```
我手上有 10 万人民币想做 A 股 alpha 投资。请用 alpha-engine-v21 skill 帮我跑一次
"今天应该买哪些股票"的 paper-trade。

⚠️ 这是 paper-trade，不是真钱。目的是看 V21 引擎在最新完整数据上的输出。

Reference: data/v21_paper_trade_demo.json (sample output from 2026-04-30 selection)

Please:
1) 加载 skill: skill("alpha-engine-v21")
2) 用 data_loader.health_check() 验证 HDF5 完好 (期望：size ≈ 19MB, n_dates=193, n_tickers=3060)
3) 找出 H5 中**数据覆盖率最高**的最近一个完整月份作为 selection_date
   （注意：H5 中奇数月份可能覆盖率仅 41.7%，需要选 ≥90% 的月份）
4) 用 alpha_engine.py 跑：
   - build_universe → adaptive_ob_keep → mcap_filter → bad_returns_filter
   - score_v21 (lv(0.15) + wt_mom(0.85))
   - select_top_n(n_hold=10, max_per_ind=3)
5) **额外生产过滤**：剔除 ST/*ST/退市股、剔除 mcap NaN、剔除开盘价 NaN 的票
6) 列出 Top-10 真实股票名称（用 H5 的 stock_names 映射）+ 行业 + WT1 + V21 评分
7) 按 ¥10,000/只 等权，100 股整手取整，给出实际建仓清单
8) 计算换手成本（双边佣金 + 印花税 + 小盘冲击溢价）
9) 给出 1-2 个月的预期收益区间，并诚实说明"单次结果不能评判策略"
10) 对照 v21_paper_trade_demo.json，看你的输出与样例的差异，解释原因
```

---

## Question 5: V21 与 V19 / V8 baseline 的公平对比——alpha 是否真的来自因子组合

```
我想验证 V21 (lv 0.15 + wt 0.85) 是不是真的比 V19 / V8 baseline 强。
担心是"换因子"或"换数据"造成的伪 alpha，不是权重迁移本身的价值。

Reference: data/v21_release_summary.csv, data/v21_subperiods.csv

V21.0 与 V19 在相同引擎 + 相同数据 + TC=off 下的对比：
  - V19 Sharpe 0.263 (2.50x NAV)
  - V21 Sharpe 0.869 (27.93x NAV)
  - Δ +0.606, +1017%

V21 vs V8 (lv 0.6 + wt 0.4) 在相同引擎下的对比：
  - V8 Sharpe 0.428 (4.16x NAV)
  - V21 Sharpe 0.869 (27.93x NAV)
  - Δ +0.441, +571%
  - 子样本 4/4 V21 胜 OOS Δ +0.610

Please:
1) 加载 skill: skill("alpha-engine-v21")
2) 跑 V21 (lv 0.15 + wt 0.85) → 记 Sharpe_1, NAV_1
3) 跑 V8 baseline (lv 0.6 + wt 0.4) → 记 Sharpe_2, NAV_2
4) 对比两组在以下维度的差异：
   a) 全样本 Sharpe / NAV / MaxDD / 年化
   b) 4 段子样本 (2010-2014/2015-2018/2019-2021/2022-2025)
   c) IS (2010-2017) vs OOS (2018-2026) 切分
5) 关键问题：Δ Sharpe 是不是"无窗口依赖"地稳定（接近 +0.4）？
   如果是 → 强证据支持"权重迁移是结构性的 alpha 来源"
6) OOS 优势 (V21 - V8) vs IS 优势：哪个更大？
   OOS > IS 意味着权重迁移在样本外更显著，反过拟合信号
7) 综合证据：能否声称 V21 比 V8 "显著更好"？
   给出 95% CI 的对比、DSR 增量、Bonferroni 修正后的 p
```

---

## Question 6 (Bonus): H5 数据健康检查 + 数据局限性披露

```
我想验证 alpha-engine-v21 skill 内置的 HDF5 数据是否完好，
并理解 H5 的数据局限性——这关系到策略的可信度。

Reference: data/h5_health_check_demo.json, references/release-notes-zh.md §5

Please:
1) 加载 skill: skill("alpha-engine-v21")
2) 运行 health_check()，期望输出：
   - size_mb ≈ 19
   - n_dates ≈ 193
   - n_tickers ≈ 3060
   - has_wt1 = True
   - has_wt2 = False (H5 没存 WT2，因为 V21 不直接用)
3) 列出 H5 的关键数据局限性（从 release notes §5 提取）：
   - close_7d ≈ prices 94% — 7 天执行价偏移未实现
   - 2008-2009 不在样本 — GFC 时期无覆盖
   - 2025+ mcap 是价格推导估计 — 准确性？
   - 2010-2014 mcap ~57% 缺失 — baostock 限制
4) 这些局限性对 backtest 结果的影响：
   - 7 天未偏移 → 月度调仓约等于月频回报率，实际滑点未建模
   - GFC 缺失 → 策略无法声称"GFC 稳健"
   - 2025+ mcap 推导误差 — 对小盘影响大于大盘
5) 实盘前必须补强的数据：
   - 日度原始价格（用于真正的 7 日执行偏移）
   - 借券利率（用于做空成本建模，V21 不做空）
   - 印花税双边 / 滑点 / 冲击成本细化（V21.0 用简化模型）
6) 综合判断：当前 H5 适合什么样的研究场景？
   (研究/复现 vs 真实生产部署)
```