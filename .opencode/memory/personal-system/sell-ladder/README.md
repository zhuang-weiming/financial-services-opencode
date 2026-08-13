# SELL_LADDER — 14 Skill 信号驱动的卖出框架

> **状态:** v3.7 (2026-08-13, **DUAL-SCORE 双分数落地** — BT-011/012 实证结论: 2026 弱市最优 V4+thr_mid / 2025 牛市最优 V0+thr_lo, 无单一算法通吃, 双分数并列输出由大盘 regime 决定采用哪个)
> **位置:** `.opencode/memory/personal-system/sell-ladder/` (永久能力)
> **协议层:** `.opencode/skills/sell-ladder/SKILL.md` (subagent 加载入口)
> **核心:** 用 14 skill 信号矩阵 + 5 动能结束标志 + 3 阶段框架替代纯价格/时间触发
> **哲学:** 卖出的艺术 = 让利润奔跑 + 多信号共振 + 时间兜底
> **有效性:** BT-008 — v2.0 REJECTED (factor_research 死灯), v2.1 PARTIALLY_SUPPORTED (阶段1持有有效、下跌识别有效; 阶段3阈值待v2.2优化)
>
> **⚠️ v3.6 已知局限**:
> - **smc 信号**严格对齐 Vibe-Trading canonical (swing_length=10, close_break=True, ChoCH/BOS + FVG 同向, FVG 过滤用 `>=0/<=0` 含零)。该算法依赖未来 bar 确认摆动点, 导致 A 股日K上**最后一根 bar 几乎不可能触发结构事件**。实测触发率 = 0% (100 只 × 12 信号全为 0)。**Vibe-Trading 原版即如此, 本项目完整对齐, 不做窜改。**
> - **structure_break 永久死亡**: 由于 smc 触发率 = 0%, `check_momentum_end_signals` 中的 `structure_break` 永远为 False。这意味着 5 大动能结束标志中只有 4 个可触发 (`wt1_cross_down`, `volume_divergence`, `volatility_drop` + 备用), **end_count 上限从 5 降到 4**。
> - **chanlun** 已升级为 Vibe-Trading canonical 5 函数完整版 (`cxt_bi_base_V230228` + `cxt_first_buy/sell_V221126` + `cxt_three_bi_V230618` + `cxt_five_bi_V230619`), 使用 czsc 0.10.12 (纯 Python 模式, `CZSC_USE_PYTHON=1` + rs_czsc stub)。触发率实测 35% (100 只)。0.9.7 缺 3 个函数、1.0.1 删除 signals.cxt, 不可用。
> - **factor_research** v3.6 重写: 完整对齐 Vibe-Trading canonical `factor_analysis` 工具。factor = 4 个基础信号 (momentum/reversal/volatility/volume_ratio, 与 multi-factor 同一组 canonical 因子), fwd = 20d shift(-20) 前向收益率, IC = 截面 Spearman (factor_df.rank.corrwith(fwd_df.rank, axis=1, method='pearson'))。最终 IC mean = 4 个因子 IC mean 的等权平均。多标路径 (peer ≥ 5) 与 单标路径 (4 因子 vs fwd20 Spearman) 都实现。阈值: \|IC mean\| > 0.05 → 强信号, ±0.03 ~ ±0.05 → 基本预测力, 其余 → 0。
> - **pair_trading** 完整实现 Vibe-Trading canonical (lookback=60, entry_z=2.0, exit_z=0.5)。
> - **volatility** canonical 低波做多 / 高波做空 (均值回归)。
> - **multi_factor** 4 因子 z-score 等权, ±0.1 死区。
> - **alpha_engine_v21** 严格按用户原创 LazyBear Pine Script 实现 (hlc3 输入, n1=10, n2=21, SMA(4) wt2, obLevel1=60/obLevel2=53, osLevel1=-60/osLevel2=-53, **cross() 严格语义** —— 仅在 WT1 与 WT2 真正交叉瞬间投票, 频率降低但信号质量提升, 与 LazyBear 原版一致)。
> - **sector_relative** 仅使用 `SECTOR_ETF_MAP_LOCAL` (已验证的持仓↔板块 ETF 映射)。无映射标的 → sector_relative 返回 healthy=False, 不参与投票。

---

## 目录结构

```
.opencode/memory/personal-system/sell-ladder/
├── README.md                       ← 本文件 (使用说明)
├── requirements.txt                ← Python 依赖 (已装, 不会重头安装)
├── sell_ladder.py                  ← 统一入口脚本
├── backtest_seed_2026.py           ← walk-forward 回测脚本 (BT-008)
├── data/                           ← 永久本地数据
│   ├── raw_daily_300725.csv        ← 300725 药石科技日线 (Sina API)
│   ├── wt_daily_300725.csv         ← 300725 LazyBear WaveTrend (V21 计算)
│   ├── wt_daily_300725_last60.csv  ← 300725 近 60 日
│   ├── cross-data/                 ← CDMO 同业 (4 个)
│   │   ├── 002821_凯莱英.csv
│   │   ├── 603259_药明康德.csv
│   │   ├── 300759_康龙化成.csv
│   │   └── 300363_博腾股份.csv
│   └── tech-pool/                  ← 科技股池 (BT-008, 6 只, Sina API)
│       ├── 688256_寒武纪.csv
│       ├── 688981_中芯国际.csv
│       ├── 002371_北方华创.csv
│       ├── 300308_中际旭创.csv
│       ├── 688041_海光信息.csv
│       └── 603501_韦尔股份.csv
├── runs/                           ← 历史跑过的结果
│   └── YYYY-MM-DD/
│       ├── sell_ladder_300725_YYYY-MM-DD.json
│       ├── sell_ladder_002821_YYYY-MM-DD.json
│       ├── backtest_<ticker>_<variant>.csv   ← 回测时间线
│       ├── backtest_summary_<variant>.json   ← 回测汇总
│       └── analysis-report.md
└── README-data.md                  ← 数据更新说明 (Sina API / akshare)
```

---

## 一键安装

```bash
pip install -r requirements.txt
```

所有依赖已配置好, 重跑不会重新下载。

---

## 一键运行

```bash
# 300725 药石科技 (默认加载 4 个 CDMO 同业)
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 300725 --cost 36.62

# 其他股票 (默认加载 CDMO 同业)
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 002821 --cost 130.00

# 加速模式 (不加载同业)
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 300725 --cost 36.62 --no-cdmo

# 含股数 (用于计算实际金额)
python3 .opencode/memory/personal-system/sell-ladder/sell_ladder.py --ticker 300725 --cost 36.62 --shares 10000

# 回测验证 (BT-008: 2026 科技股行情, 双变体对比)
python3 .opencode/memory/personal-system/sell-ladder/backtest_seed_2026.py --variant v2.0
python3 .opencode/memory/personal-system/sell-ladder/backtest_seed_2026.py --variant v2.1
```

---

## 输出

每次运行输出:
- 14 skill 信号矩阵 (5 强动能 / 4 辅助 / 3 数据 / 2 框架)
- 5 动能结束标志触发状态
- 3 阶段判定 (强动能期 / 衰减期 / 结束期)
- **DUAL-SCORE 双分数 (v3.7)** — 弱市震荡分(V4+thr_mid) 与 牛市上涨分(V0+thr_lo) 并列输出, 各带建议阶段/仓位; 大盘 regime 标签 (510300 vs MA60 ±7%) 提示采用哪个
- 5 维卖出触发矩阵 (价格/时间/信号/动能/估值/宏观)

**双保存:**
- 永久: `runs/YYYY-MM-DD/sell_ladder_{ticker}_{date}.json` (历史记录)
- 临时: `out/sell_ladder_runs/YYYY-MM-DD/sell_ladder_{ticker}.json` (本次查看)

---

## 14 Skill 信号矩阵

### A. 5 个强动能信号 (动能健康度)

| Skill | 健康 | 衰减 | 结束 |
|:---|:---:|:---:|:---:|
| technical-basic (ADX) | > 20 | 20-15 | < 15 |
| ichimoku (云层) | > 0% | 0% ~ -5% | < -5% |
| smc (BOS) | 上升 | 高点降低 | ChoCH |
| alpha-zoo (20d 动量) | > +10% | +10% ~ -5% | < -10% |
| factor-research (截面 IC) | IC mean > +0.05 | \|IC\| ≤ 0.05 | IC mean < -0.05 |

**健康数 X/5 决定阶段**

### B. 4 个辅助信号

- factor-research f2 IC (截面/自相关)
- volatility HV 百分位 (HV<30% = 顶部信号)
- multi-factor 综合分
- elliott-wave 5 浪完成

### C. 3 个数据信号 (PIT 验证)

- WT1 (< -20 弱势 / > 60 超买)
- RSI(14) (> 85 持续 5 日 真正超买)
- BB 位置 (> 130% 极度超买)

### D. 2 个框架信号 (不可协商)

- 化债 deadline 2027-04-30 (强制 100%)
- 化债额度收官 2026-12-31 (减至 50%)

---

## 5 大动能结束标志 (多信号共振)

**真正"动能结束"需要至少 3/5 同时触发:**

| 标志 | 具体触发 |
|:---|:---|
| ① 趋势破坏 | EMA(12) 跌破 + ADX<20 + ichimoku 跌穿云 |
| ② 动量反转 | WT1<-20 + RSI<30 持续 + 20d 动量<-10% |
| ③ 量能背离 | OBV 下降 + 价格新高 (5 日) |
| ④ 结构破坏 | smc ChoCH + chanlun 顶分型 + ichimoku 跌穿云 |
| ⑤ 波动率突变 | HV 100% → 30% (30 日内) |

---

## 3 阶段卖出框架

| 阶段 | 5 强信号 | 5 动能标志 | 建议 |
|:---:|:---:|:---:|:---|
| 1 强动能期 | 5/5 | 0-1/5 | 🟢 持有 100% |
| 2 衰减期 | 3-4/5 | 1-2/5 | 🟡 分批止盈 20-40% |
| 3 结束期 | ≤ 2/5 | 3+/5 | 🔴 大幅减仓 70-100% |

---

## DUAL-SCORE 双分数 (v3.7)

**为什么:** BT-011 (2026 弱市) 最优 = V4 纯事件计票 + thr_mid(3.0/2.0); BT-012 (2025 牛市) 最优 = V0 原版计票 + thr_lo(2.0/1.0)。两年度无单一算法通吃 → 双分数并列输出, 由大盘 regime 决定采用哪个。

| | ① 弱市震荡分 (V4) | ② 牛市上涨分 (V0) |
|:--|:--|:--|
| 计票 | `2·ev_pos − 2·ev_neg` (∈[-6,+6]) | `2·ev_pos + 1·tr_pos − 2·ev_neg` (∈[-6,+14]) |
| 信号 | 3 事件 (candlestick/chanlun/turnover_anomaly), 趋势不参与 | 3 事件 + 8 趋势 (趋势负票不扣分) |
| 阈值 | 3.0 / 2.0 (thr_mid, 2026 实证) | 2.0 / 1.0 (thr_lo, 2025 实证) |
| 阶段 | 各按绝对阈值 + end_count 5 标志判阶段 → 仓位 | 同左 |
| 仓位 | 阶段1→1.0 / 2→0.7 / 2.5→0.8 / 3→0.2 (T+1) | 同左 |

**大盘 regime 标签** (自动计算, 仅供参考, 最终由用户决定):
- `510300 收盘 > MA60 × 1.07` → **牛市** → 建议采用牛市分
- `510300 收盘 < MA60 × 0.93` → **弱市** → 建议采用弱市分
- `|偏离| ≤ 7%` → **模糊区** → 两分并列参考

**实现:** `dual_score.py` (独立模块, sell_ladder.py 自动调用), 结果写入 JSON `dual_score` 字段。
**实证依据:** BT-011 (results/sharpe_scan.csv: 弱市分 = excess +6.27%) + BT-012 (results/bt012_scan_2025.csv: 牛市分 = excess -5.25% 亏最少)。

---

## 5 维卖出触发矩阵

| 维度 | 触发 | 动作 | 优先级 |
|:---|:---|:---|:---:|
| 价格 | 止盈位 55/60/65/70 元 | 15/20/25/25% 分批 | ⭐⭐⭐ |
| 时间 | 化债额度收官 2026-12-31 | 减至 50% | ⭐⭐⭐ |
| 时间 | 化债 deadline 2027-04-30 | 减至 30% | ⭐⭐⭐ |
| 时间 | 2027-07-01 SELL_LADDER | 100% 清仓 | ⭐⭐⭐ |
| 信号 | 强动能信号 ≤ 3/5 | 减 20% | ⭐⭐ |
| 信号 | 强动能信号 ≤ 2/5 | 再减 20% | ⭐⭐ |
| 动能结束 | 5 标志中 3+ 触发 | 大幅减仓 | ⭐⭐⭐ |
| 估值 | P/FV > 1.5 | 评估卖出 | ⭐ |
| 宏观 | 美债 5Y CDS > 100bp | 全面清仓 | ⭐⭐⭐ |

---

## 卖出的艺术 (Selling Art)

### ❌ 不要 (常见错误)

- 不要预测顶部 ("涨太多了, 该卖了")
- 不要单信号卖出 ("RSI>80 = 卖")
- 不要摸顶 ("BB 122% 超买 = 卖")

### ✅ 要 (正确做法)

- 要让利润奔跑 (5/5 强信号 → 持有)
- 要多信号共振 (3+ 标志触发 → 减仓)
- 要时间兜底 (化债 deadline → 清仓)

---

## 扩展用法

### 加新标的

把数据放到 `data/cross-data/{code}_{name}.csv`, 然后跑:
```bash
python3 sell_ladder.py --ticker 新代码 --cost 成本
```

### 加新 skill

在 `sell_ladder.py` 中:
1. 加 `calc_xxx(df)` 函数
2. 在 `run_sell_ladder()` 主循环加入 `signals['xxx'] = calc_xxx(df)`
3. (可选) 加入 5 强动能信号列表

### 跑历史回测

```bash
# 修改 sell_ladder.py, 用历史 close_date 替换 datetime.now().date()
# 或写一个 batch_run.py 循环多天
```

---

## 关联文件

| 文件 | 关系 |
|:---|:---|
| `sell_ladder.py` | 主入口脚本 (可重跑) |
| `requirements.txt` | 依赖清单 (已装) |
| `README.md` | 本文件 (使用说明) |
| `README-data.md` | 数据更新说明 |
| `runs/YYYY-MM-DD/` | 跑过的结果 (历史快照) |
| `.opencode/memory/personal-system/7.SELL_LADDER.md` | v2.0 完整方法论文档 |
| `.opencode/memory/personal-system/7.1.POSITION_SIZING.md` | 持仓快照 + SELL_LADDER 结果 |
| `.opencode/memory/personal-system/theses/300725_药石科技.md` | 药石 thesis |

---

## 临时输出 (out/)

`out/` 目录用于**本次查看的临时副本**, 不是永久存放:
- `out/sell_ladder_runs/YYYY-MM-DD/sell_ladder_{ticker}.json` (本次 JSON 副本)
- `out/300725_yaoshi/` (历史分析报告, 8/10 一次性)

`out/` 内容会随时间累积, 需要定期清理 (或 git ignore).

---

## 待办

- [ ] 扩展到其他持仓 (300003 乐普 / 002821 凯莱英 / 002601 龙佰 / 600050 联通)
- [ ] 自动每日运行 (cron / opencode schedule)
- [ ] 验证 5 大动能结束标志的历史准确率 (回测)
- [ ] 加入更多 skill (如资金流向 / 北向资金 / 融资融券)
- [ ] 写 batch_run.py 一次跑多个标的

---

*End of README — 2026-08-10*

*v1.0 是"价格梯子", v2.0 是"skill 矩阵". 卖出的艺术 = 让利润奔跑 + 多信号共振 + 时间兜底.*
