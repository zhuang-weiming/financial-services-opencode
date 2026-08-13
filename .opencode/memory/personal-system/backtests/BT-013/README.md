# BT-013 — BUY_LADDER 信号有效性 · 可达性 + 事件研究

- **日期:** 2026-08-13 (首跑)
- **执行者:** wealth-guide (P0 路径, bt013_signal_study.py)
- **动机:** 用户问 "buy-ladder 需要什么整理 / 什么算法累计分数 / 回测如何" — 对标 sell 侧 BT-011/012 双分数定案路径
- **假设:** BUY_LADDER 当前固定比例阈值 (0.65/0.42 × max_score) 在真实信号分布下可能不可达; 且 buy 侧信号权重可能与实证 alpha 倒挂
- **数据源 (零新下载):** BT-011 `signal_cache_v2.parquet` (200 池, 2024-10-08 ~ 2026-08-13) + `data/market/daily/<code>.csv` (200/200 本地齐全)
- **方法:**
  1. **可达性:** 对 89,845 条 code-date 观测, 按 `score = 2·ev_pos + 1·tr_pos − 2·ev_neg` 计算, 用声明阈值 (0.65/0.42×20=13.0/8.4) 和近似 4 事件版 (0.65/0.42×16=10.4/6.7) 两套做阶段判定
  2. **事件研究:** 信号 `>0` 触发日 (code,date) t → 未来 20/60 交易日 log 收益; 基准 = 同日同池全部股票平均未来收益 (截面基准, 消除市场 beta); `α = 触发组均值 − 当日截面基准`; 单样本 t-test (α vs 0); 分全期 / 2025 牛 / 2026 弱

## 结果

### 1. 分数可达性 — 阶段判定完全锁死

| 版本 | 声明阈值 | 全期 n | P90 | P99 | max | 阶段1 | 阶段2 |
|:--|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| V_A 当前 (2 事件可算, 8 趋势) | 13.0 / 8.4 | 89845 | 3.0 | 4.0 | 6.0 | **0 (0.00%)** | **0 (0.00%)** |
| V_B 近似 4 事件 (含 vpr/scx) | 10.4 / 6.7 | 89845 | 3.0 | 4.0 | 7.0 | **0 (0.00%)** | 1 (0.00%) |

→ 两年 89,845 个 code-date 观测里 **阶段 1 (击球区) 一次都没触发过**; score 极值 6~7 远低于任意下限阈值.

### 2. 信号触发率 — 5 个死灯 + 2 个近死灯 + 活跃度分化

| 类别 | 信号 (pos 触发率, 全期) |
|:--|:--|
| 显式死灯 (cache 置零, 无 peer) | multi_factor 0% · sector_relative 0% · factor_research 0% · pair_trading 0% |
| 死灯 (缓存全 0, 需另查生产) | **smc 0%** |
| 近死灯 (触发率 <1%) | **turnover_anomaly 0.086%** · ichimoku 0.53% |
| 活跃 | ml_strategy 33% · harmonic 34% · alpha_zoo 24% · technical_basic 21% · candlestick 18% · chanlun 14% · ad_line 13% · alpha_engine_v21 6.9% |

### 3. 事件研究 — 截面超额 α20 (触发后 20 日, 跑赢同池平均)

**全期显著正:** `alpha_zoo +0.64% (p<1e-4)` · `technical_basic +0.31% (p=0.025)` · `ad_line +0.29% (p=0.058)` · `candlestick +0.23% (p=0.063)` [后两者边际]

**全期显著负 (反指):** `chanlun −1.61% (p<1e-4, t=−12)` · `turnover_anomaly −4.47% (n=65)` · `volatility −0.82%` · `harmonic −0.26%` · `end_count −0.27%`

**中性:** ml_strategy · alpha_engine_v21 · ichimoku

### 4. Regime 依赖 (分年)

| 信号 | 2025 牛 α20 | 2026 弱 α20 | 判定 |
|:--|:--:|:--:|:--|
| **alpha_zoo** | +0.77% ✓ | +1.23% (α60 +3.67%) ✓ | **两年都有效 (唯一)** |
| **technical_basic** | +0.12% ✗ | **+1.30% (α60 +5.18%)** ✓ | **弱市专用** |
| **candlestick** | −0.03% ✗ | +0.79% ✓ | 弱市有效 |
| **ad_line** | +0.11% ✗ | +0.81% ✓ | 弱市有效 |
| **chanlun** | −1.77% ✗ | −1.61% ✗ | **两年都是强反指** |

## 结论

1. **BUY_LADDER 当前 = 功能性锁死.** 固定比例阈值 `0.65/0.42×max` 两年零触发阶段 1; 不是"v1.1 保守", 是计票结构到不了任何买点. 这复现了 sell 侧 BT-011 同一失效模式 (固定比例阈值 vs regime 依赖信号分布).
2. **权重结构与实证 alpha 完全倒挂 (Get-It-Backwards 风险):**
   - 事件信号 ×2 (chanlun −1.61%、turnover −4.47%) = **最强反指却拿最高权重**
   - 趋势信号 ×1 (alpha_zoo +0.64%、technical_basic +0.31%) = **唯一正 α 却拿最低权重**
   - 这与 buy 侧哲学自洽: buy 靠"动量启动/趋势延续" (LAW-001), 而 chanlun 三买是左侧反转抄底 → 与"不预测底部"核心约束直接冲突.
3. **买入信号有效排序 (事件 α):** `alpha_zoo > technical_basic > [candlestick≈ad_line]` >> 其他 ≈ 0/负. 弱市信号面比牛市宽 (4 个显著正 vs 1 个).
4. **P0-a/P0-b 已回答三层整理需求:**
   - 修死灯 (smc/multi_factor/sector_relative 需确认生产路径; turnover 稀有)
   - 权重重排 (负 α 出加分, 正 α 晋升)
   - 绝对阈值 (基于可达分布而非 0.65/0.42×max)

## 局限 (Adversarial Review)

- **最可能出错处:** ① 死灯是 **BT-011 缓存口径** (multi_factor/sector_relative/factor_research 无 peer 显式置零, bt011_engine.py:91) — 不代表 buy_ladder 生产传 peer 路径一定为 0, 需单独验证; ② smc 缓存 0% 可能因逐日全量计算慢/swing 不触发, 也需生产复核.
- **样本:** 仅 2024-10~2026-08 两年 (2025 牛 + 2026 弱), **无 2018/2022 深熊样本**; 不可外推到系统性熊市.
- **截面基准未风险调整:** α = 跑赢同池等权平均, 非绝对收益; buy 触发日偏市场低位时同池平均同步下行, α 可能高估.
- **重叠样本:** 20/60 日未来收益序列重叠, t 检验 p 值**低估** (非独立样本); 结论用于**排序/方向**, 不作精确显著性.
- **无交易成本/滑点/T+1 摩擦** (A 股 T+1 买入当日不可卖, 20 日收益持有端点不受影响但成本未计).
- **trigger 用 signal>0 单点**, 未模拟 buy_ladder 的 Layer 0 regime 闸门 & Layer 1 筛选; 全池 200 只含非持仓股.
- **n=65 (turnover_anomaly) / n=473 (ichimoku)** 小样本, 置信度低.

## 分拆验证建议 (P1+)

1. **生产路径死灯复核:** 单跑 `buy_ladder.py calc_smc/calc_multi_factor/calc_sector_relative` 传 peer, 确认是否真 0 还是缓存退化.
2. **chanlun 深度反指检验:** 分 三买/其他 signal 细分, 确认是否"三买后追高"结构性问题 (三买在上升中继, 而 cache 信号为 +1 多含反转残差).
3. **弱市买入分原型:** `score_w = alpha_zoo + technical_basic + candlestick + ad_line` (四信号 2026 均正 α), 绝对阈值取分布 (如 ≥2/3/4), 回测 2026 触发后 20/60 日 excess vs 全池.
4. **牛市买入分原型:** `score_b = alpha_zoo × 双权重 + technical_basic` (2025 仅 alpha_zoo 显著), 与弱市分对比 regime 切换.
5. **加 Layer 0 闸门后重测:** 仅在大盘解锁期计数, 看是否提升 α (buy 侧天然优势).

## 5-Why 交叉引用

- **sell 侧 BT-011/012:** 同构发现 "固定比例阈值 regime 失效" → buy 侧复现同一病根 (V4/V0 双分数不是 sell 专属, 是整套个人系统的病灶).
- **LAW-001 vs chanlun:** buy-ladder 哲学 = 动量延续 (LAW-001) + "不预测底部"; 事件研究证明 chanlun 三买(反转左则) 与 LAW-001 冲突 → 触发一次性反指检验, 若成立则从 buy 信号矩阵移入否决/预警.

---

*结果文件: results/signal_trigger_rates.csv · results/event_study_alpha.csv · results/score_reachability.csv · results/summary.json*
*重建: `python3 bt013_signal_study.py` (零下载, 约 2-4 分钟)*
