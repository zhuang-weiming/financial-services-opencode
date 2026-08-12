# SELL_LADDER v2.5 + BUY_LADDER 真实批量验证报告

> **日期:** 2026-08-11
> **范围:** 18 只持仓 × 2 套阶梯（卖出 v2.5 / 买入 v1.1-代码 v3.0）
> **数据:** `data/market/daily/` 集中目录，最新 bar 2026-08-10
> **状态:** 草稿供人工复核 — 不构成交易执行建议

---

## 1. 结论摘要（先给结论）

| 验证项 | 结论 | 置信度 |
|:-------|:-----|:------|
| 包稳定性 | ✅ 18/18 卖出 + 18/18 买入，零崩溃、零异常 | HIGH |
| 框架一致性 | ✅ 核心评分 `score_v22`/`stage_v22` 由 buy 直接复用（`import sell_ladder as sl`），零修改 | HIGH |
| 版本标签一致性 | ⚠️ 存在 3 处已知漂移（见 §5），不声称"完全一致" | MEDIUM |
| 新旧结果对比 | ✅ 5/18 阶段变化，全部可归因于 canonical 对齐（非随机漂移） | HIGH |
| 市场吻合度 | ✅ 唯一 Stage 2 为强动量 601919；降档标的均有弱市/信号翻转支撑 | MEDIUM |

**一句话:** 两个包可以稳定用于 18 只持仓的批量判定；阶段变化是 canonical 对齐的**预期结果**，不是 bug；但 Layer 0 数据仍为文档 fallback，全市场接入前请勿把"18/18 锁定"当作实时 regime 结论。

---

## 2. 包稳定性验证

### 2.1 SELL_LADDER v2.5 批量（`batch_v25_holdings.py`）
- **执行:** 18/18 成功，无异常（n_error=0）
- **结果分布:** Stage 1 = 0 · Stage 2 = 1 (601919 中远海控, 6/14) · Stage 2.5 = 17 · Stage 3 = 0
- **产物:** `runs/2026-08-11/v25_holdings_2026-08-11.json`
- **单标的 CLI 验证:** `sell_ladder.py --ticker 601919 --no-cdmo` 端到端通过（900 bars，16 signals 全计算）
  - ⚠️ `--no-cdmo` 下 sector_relative=错误（无板块数据）→ score 5/14（vs 批量带板块 6/14）→ **同一函数、同一数据，仅输入差异**，非 bug

### 2.2 BUY_LADDER 批量（`batch_v11_holdings.py`）
- **执行:** 18/18 成功（n_locked=18, n_error=0）
- **结果:** 全部"禁入区-Layer0锁定"，每只 0.0s（Layer 0 短路为设计行为）
- **端到端验证（force-unlock 601919）:** Layer 0 强制解锁 → Layer 1 筛子 5/5 → Layer 2 16 信号 + 6 转换 + 0/5 否决 + 2/5 确认 → Stage 4 (禁入区-得分不足, 4/20=20%) ✅ 全链路计算正常

---

## 3. 框架一致性验证（与 vibe-trading canonical）

### 3.1 代码复用证据
- `buy_ladder.py:37` → `import sell_ladder as sl`，直接调用 `sl.calc_*` / `sl.score_v22` / `sl.stage_v22` — **零修改复用**
- 两个包共用同一 `data_loader.py`（集中目录 → fallback → Sina 落盘）

### 3.2 卖出 v2.5 分级计票（与 BT-008 实证一致）
| 项 | 值 |
|:---|:---|
| 事件信号 ×2 | candlestick, chanlun, turnover_anomaly |
| 趋势信号 ×1 | 8 项（alpha_engine_v21, ml_strategy, technical_basic, ichimoku, smc, alpha_zoo, factor_research, multi_factor, volatility, harmonic, pair_trading, sector_relative, ad_line 中计 8 票） |
| max | 14 |
| thr1 (0.65) | 9.1 → Stage 1 |
| thr2 (0.42) | 5.88 → Stage 2 |
| 阶段 2.5 | 得分 < 5.88 且 end_count < 3 |
| end_count | 5 大动能结束标志 |

### 3.3 canonical 参数核对（20:30 P1 完成后状态）
| 组件 | canonical 值 | 本次运行验证 |
|:-----|:-------------|:-------------|
| alpha_engine_v21 | LazyBear 经典 hlc3, N1=10 N2=21, OB=60/OS=-60, WT1=EMA(CI,21), WT2=SMA(WT1,4) | 601919: WT1=+42.43, Zone=H 40-60 ✅ |
| candlestick | 9 处修正（shooting_star 入 BEAR 等） | 601919: 20d score=1 ✅ |
| ml_strategy | 真 sklearn walk-forward (RF100/depth5, 10 特征) | 601919: ML=-0.14 (prob_up=0.43) ✅ |
| smc | ChoCH 优先 + FVG 同 bar 过滤, swing=10 | 601919: 无结构信号 ✅ |
| multi_factor | 4 因子 z 等权和 (momentum, -reversal, -volatility, volume_ratio) | 601919: composite=+0.45 ✅ |
| ichimoku | 事件触发 (tk_cross) | 601919: 无交叉事件 → 0 ✅ |
| harmonic | D 回撤锚点 X→A 修正 | 601919: B=85%, D=155% ✅ |

---

## 4. 新旧版本对比（2026-08-10 旧 vs 2026-08-11 新）

| 标的 | 旧阶段 | 新阶段 | 变化 | 归因 |
|:-----|:-------|:-------|:-----|:-----|
| 300725 药石科技 | Stage 1 | Stage 2.5 | ↓ 2 档 | candlestick +1→0（更严格）、ml_strategy +1→−1（真 ML 预测短期反转）、WT1 7.67→0（hlc3） |
| 300142 沃森生物 | Stage 2 | Stage 2.5 | ↓ 1 档 | candlestick +1→−1、ml_strategy +1→−1、smc +1→0、sector_relative −1 |
| 601669 中国电建 | Stage 3 | Stage 2.5 | ↑ 2 档 | smc −1 消失（canonical 重写后无结构信号） |
| 601688 华泰证券 | Stage 3 | Stage 2.5 | ↑ 1 档 | smc −1 消失 |
| 601919 中远海控 | Stage 2 | Stage 2 | 稳定 | 6/14 强动量唯一 |
| 其余 13 只 | Stage 2.5 | Stage 2.5 | 稳定 | — |

**关键洞察:** 4 只变化全部源于 20:30 P1 的 canonical 对齐（smc bug 修复 + ml 真实现 + multi_factor 对齐），**不是随机漂移**。smc 修复消除了 2 只券商/基建的假结构破坏信号（升级合理）；ml 真实现让 2 只高动量医药股出现 −1 反转票（降档，但注意单票 ML 仅为 1/16 票，BT-002 已证其有效性受限）。

---

## 5. 发现的问题（如实披露）

| # | 严重度 | 问题 | 位置 | 影响 |
|:--|:-------|:-----|:-----|:-----|
| 1 | LOW | CLI 显示标签过期："SELL_LADDER v2.4 阶段判定" + "趋势信号: {n}/9 正 (含 ad_line)"，实际 v2.5 用 8 票（score_v22 正确，仅 print 字符串旧） | sell_ladder.py:1174-1175 | 仅显示误导，决策逻辑正确 |
| 2 | LOW | 版本号漂移：buy_ladder.py 代码头 v3.0 vs README.md/batch_v11_holdings.py v1.1；buy 结果 header 打印"v1.1" | buy_ladder.py:853 | 文档与代码不一致，影响审计 |
| 3 | MEDIUM | BUY Layer 0 的 MCI=0.386 / 国家队=-89.0% / MA60=-2.66% 来自 CHINA_FRAMEWORK 文档 fallback，**非实时数据刷新**（raw-log P1 遗留项） | buy_ladder.py Layer 0 | "18/18 锁定"是设计内结果，但 regime 数值不实时 |
| 4 | LOW | 结果目录按 `datetime.now()` 而非数据最后日期保存（buy 跑在 08-11 但 JSON 落在 runs/2026-08-10/） | buy_ladder.py | 归档目录易混淆 |
| 5 | LOW | Layer 1 market_cap 为 None 占位（"None亿 → 🟢" 通过），README 已标注"待接入" | buy_ladder.py Layer 1 | 筛子含占位逻辑，接入前勿信市值门槛 |

---

## 6. 市场吻合度核对（截至 2026-08-10 收盘）

| 标的 | 新阶段 | 20d | 60d | 板块背景 | 吻合度 |
|:-----|:-------|:----|:----|:---------|:-------|
| 601919 中远海控 | **2** | +10.8% | +10.4% | 集运强动量 | ✅ 唯一 Stage 2 合理 |
| 300725 药石科技 | 2.5 | +29.9% | +32.6% | CRO 板块 08-07 大涨 (+12.2%) | ⚠️ 高动量但信号弱 — 见 §7 |
| 300142 沃森生物 | 2.5 | −0.5% | −8.2% | 医药 ETF 强势但个股弱 | ✅ |
| 601669 中国电建 | 2.5 | +4.8% | −16.3% | 基建弱修复 | ✅ 升级合理 |
| 601688 华泰证券 | 2.5 | −2.1% | +4.7% | 券商 60d +4.8% 但 20d 平 | ✅ |
| 券商 7 只 + 512000 | 2.5 | 平 | +4.8% | 板块无趋势 | ✅ |
| 600570 恒生电子 | 2.5 | +11.1% | −11.6% | 芯片/软件 ETF 20d −16.4% | ✅ 反弹但板块弱 |
| 300003 乐普医疗 | 2.5 | +8.4% | −3.8% | 医药强但个股滞后 | ✅ |

**结论:** 卖梯子结果与真实行情方向一致；唯一张力点是 300725（月涨 30% 但 Stage 2.5）——这是框架"高分动量+ML 反转票"的保守化输出，end_count=0 故不构成"清仓"信号，动作是"减 40% 观察"。

---

## 7. 5-Why 反方质控摘要

| 层级 | 追问 | 回答 |
|:-----|:-----|:-----|
| Why 1 | 前提 | batch 与 CLI 同一评分函数 + canonical 已生效 |
| Why 2 | 证伪 | 发现 v2.4/9 票标签、v3.0-vs-v1.1 版本漂移、Layer 0 fallback |
| Why 3 | 反转 | 若存在未发现的旧路径 → "框架并非完全统一"成立 |
| Why 4 | 偏误 | 用户期望正面结论 + 三轮验证疲劳 |
| Why 5 | **最薄弱** | Layer 0 数据为 fallback，"18/18 锁定"可能在数据接入后反转 |

**结论:** 核心逻辑一致性经得起检查；"完全一致"的说法需降级为"核心评分一致 + 已知漂移 5 项"。置信度 MEDIUM-HIGH。

---

## 8. 建议下一步

1. **[P1] 版本标签统一**: buy_ladder 全部 v1.1 → v3.0（代码头 853 行 + README + batch + SKILL.md 同步）
2. **[P1] CLI 显示标签修正**: sell_ladder.py:1174-1175 改 v2.5 + "8 票（不含 ad_line）"
3. **[P2] Layer 0 数据自动刷新**: MCI/国家队/MA60 从集中数据实时计算（raw-log 遗留 P1 项，优先级提升）
4. **[P2] 300725 单独复核**: `sell_ladder.py --ticker 300725 --cost 36.62` + combo_layer 闭环，评估 ML −1 单票对高动量股的过度惩罚
5. **[P3] 结果目录按数据日期保存**，避免 08-10/08-11 目录混淆

---

*报告草稿 — 供人工复核。不构成投资建议。*
