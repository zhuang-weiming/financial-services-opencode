# 2026-09-10 — 新增 trend-analysis-multi-algo skill（9 算法趋势分析协议）

> **本次产出**：`.opencode/skills/trend-analysis-multi-algo/`（SKILL.md + scripts/trend_analysis.py + references/algorithms.md）+ 4 处路由注册
> **状态标签**：NEW_SKILL + METHODOLOGY_FIX（修复"单算法趋势分析"缺陷）
> **触发**：用户指出 "蜡烛图，艾略特波浪，缠论，等等很多的趋势算法都应该被启动才对" + 同意 (A) 写成 skill

---

## 1. 问题（被用户指出）

**2026-09-10 光大证券趋势分析初版只跑了 WaveTrend + 均线**，遗漏：
- 缠论（顶分型 @ 9/4 + 中枢 [14.15, 14.78]）
- SMC（BOS 熊 @ 7/27 + 8/20 看涨 OB）
- 蜡烛图（9/7 看空吞没）
- 艾略特波浪（5 浪下跌完成 → 潜在见底）
- 一目均衡表、谐波、技术三维投票

→ 结论偏差：初版"中性偏弱"实际应为"**中性/分歧**（short -1 / mid +1）"。

## 2. 交付物

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 协议说明：9 算法矩阵 + 输出解读 + 系统衔接 + 陷阱 |
| `scripts/trend_analysis.py` | 统一执行器（9 算法，~600 行）|
| `references/algorithms.md` | 每算法公式/参数/信号逻辑/失效条件 |

**9 算法：**
- 动量层：A1 WaveTrend (V21 N1=50/N2=105) + A2 技术三维投票
- 形态层：B1 蜡烛图(TA-Lib) + B2 缠论(czsc) + B3 艾略特 + B4 谐波 + B5 图表形态(MCP)
- 结构层：C1 SMC/ICT + C2 一目均衡表
- 汇总裁决：信号矩阵 + 分歧分析 + 时间尺度分层 + 独立性质检

**依赖：** pandas/numpy/requests + TA-Lib + czsc + smartmoneyconcepts + pyharmonics(可选) —— **全部已安装**（无新增依赖）。

## 3. 关键技术决策

1. **WaveTrend 口径修正**：月度 WT 必须是"日线计算后按月采样"，**不是**在月线序列上重算（后者因 EMA(105) 长度不足产生 980 的失真值）。实测与 H5 存储值吻合（-38.42 vs H5 -39.61，偏差来自腾讯 640 根上限）。
2. **czsc 0.10.x API 适配**：`ZS(bis)` 返回**单个**中枢对象（非列表）→ 脚本改用"3 笔重叠"手动检测全部中枢。
3. **独立性质检**：明确标注 "9/9 算法基于同一 OHLCV 序列 = 同一数据的多种变换，不是独立证据" —— 防止伪共识。

## 4. 验证

```
601788 光大证券: 偏多2/中性5/偏空2 → 中性/分歧; 加权 -0.27; scale={short:-1, mid:+1, long:0}
600030 中信证券: 偏多3/中性3/偏空3 → 中性/分歧; 加权 -0.40
000001 平安银行: 偏多6/中性1/偏空2 → 偏多;     加权 +2.36
CSV 模式: ✅ 通过
```

## 5. 路由注册（4 处）

- `.opencode/instructions/wealth-guide-router.md` — Skill Registry 新增行
- `.opencode/agents/wealth-guide/agents/wealth-guide.md` — Skill Routing Hints + Notable skills + 路由矩阵
- `.opencode/agents/alpha-researcher/agents/alpha-researcher.md` — 新增 §5 Single-Stock Trend Analysis
- `.opencode/skills/stock-deep-dive/SKILL.md` — 维度 2 技术分析改为首选加载此 skill

## 6. 5-Why Why 5（本结论最弱处）

**最薄弱：** 9 个算法全部读同一 OHLCV 价格序列 —— 我称之为"多算法交叉验证"有夸大之嫌；真正的独立验证需要成交量结构、资金流向（主力/北向/两融）、基本面、宏观等**非价格维度**。协议里已加"独立性质检"字段强制标注，但这只是**披露**问题而非**解决**问题 —— 若要让趋势结论真正稳健，下一步应把资金流/基本面作为**独立维度**并入协议（目前仅在 stock-deep-dive 的 7 维框架里作为平行维度存在，未与 9 算法汇总裁决耦合）。

## 7. 待办

- [ ] 把 B5 图表形态（MCP `pattern_recognition`）接入脚本（当前需手工调用）
- [ ] 把资金流/基本面作为独立维度并入汇总裁决（解决 Why 5）
- [ ] 用此协议重跑光大证券完整分析，更新 `theses/601788_光大证券.md`（2026-07-22 版本）
- [ ] 考虑给协议加"回测验证层"（9 算法信号的历史 forward return 统计）
