# 2026-09-10 — 新增 non-price-evidence skill（4 维非价格证据层）

> **本次产出**：`.opencode/skills/non-price-evidence/`（SKILL.md + scripts/fetch_evidence.py + references/data-sources.md）+ 路由注册 + 与趋势协议交叉链接
> **状态标签**：NEW_SKILL + INDEPENDENCE_FIX（解决 trend-analysis-multi-algo 的"伪共识"Why 5）
> **触发**：用户同意 (A) 建 non-price-evidence skill，含可运行脚本，复用已验证的源

---

## 1. 解决的问题

`trend-analysis-multi-algo` 的 10 个算法**全部读同一 OHLCV 序列** → 共识度是**伪独立**（该协议自己的 Why 5 已披露）。真正独立的验证需要**非价格维度**。

## 2. 四维矩阵 + 实测源

| 维度 | 脚本内（Python 直连）| 需 MCP（agent 调用）|
|---|---|---|
| **成交量结构** | 腾讯 OHLCV 计算（换手/量比/OBV/AD/量价分布/波动）| 分钟线/逐笔/Level2 |
| **资金流向** | 东财 datacenter（两融/股东户数/龙虎榜/大宗/解禁/北向）| A股主力净流入/美股13F/Form4/Crypto链上 |
| **基本面** | 东财 datacenter（财务指标/一致预期）| 三大报表/SEC文本/Morningstar |
| **宏观** | akshare（中国 CPI/PPI/M2/社融/GDP + HYP-029 触发监控）| 美国宏观 FRED/Polymarket |

## 3. 实测验证的数据源（2026-09-10）

**✅ 可用（Python 直连）：**
- 腾讯 `web.ifzq.gtimg.cn`（行情）
- 东财 `datacenter-web`（两融/股东户数/龙虎榜/大宗/解禁/北向/财务指标/一致预期）
- 东财 `push2`（实时行情）
- akshare `macro_china_*`（CPI/PPI/M2/社融/GDP）

**✅ 可用（MCP，0 credits）：**
- `llmquant-data_macro_*`（FRED ~50 series）
- `llmquant-data_sec_13f_*`（机构持仓）
- `llmquant-data_sec_filing_browse/read`（10-K/Q/8-K）
- Morningstar MCP（分析师报告/数据/筛选/持仓）

**❌ 不可用（实测）：**
- `vibe-trading` MCP 全部超时
- 东财 `push2his`（资金流）IP 被限
- `llmquant-data` news/etf_holdings（credits 耗尽）
- FRED 直连超时

## 4. 端到端交叉验证演示（601788 光大证券）

```
价格层 (10 算法):  偏多2/中性5/偏空3 → 中性/分歧; 加权 -0.67
  空: 缠论▼ SMC▼ 江恩▼    多: 技术投票▲ 艾略特▲
  时间尺度: short -1 / mid +1 / long 0

非价格层 (4 维度):
  成交量: 缩量 (20/60=0.67), 量价背离 ⚠️
  资金流: 两融 31.44亿 (5日 +0.01 平), 股东户数 16.89万 (环比 +0.1%), 北向 1.65%
  基本面: 2026H1 净利 22.29亿, 同比 +91.1%, ROE 3.28%
  宏观: 中国 8月 CPI +0.8% / PPI +3.8% / M2 +7.7% (HYP-029 触发 1/3)
```

**交叉验证结论**：
- 价格短期偏空（缠论/SMC/江恩）+ 缩量 + 量价背离 → **短期弱势确认**
- 但基本面净利 **+91.1%** 强劲 → **基本面与价格显著背离**（延续 thesis 记录的"Q1 净利 +42% vs 股价 -16%"矛盾）
- 两融持平 + 股东户数不变 → 资金面中性（无杠杆进场也无撤退）
- **综合：短期弱势 + 中期基本面支撑 = 分歧/等待，与价格层"中性/分歧"一致**

## 5. 交付物

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 4 维矩阵 + MCP 分工 + 交叉验证规则 + 陷阱 |
| `scripts/fetch_evidence.py` | 统一采集器（4 维度，Python 直连，~380 行）|
| `references/data-sources.md` | 四维 × 全市场 × 工具 × 认证 × 实测状态完整矩阵 |
| 路由表 | `non-price-evidence` 注册（factor-researcher / market-router）|
| 趋势协议 | SKILL.md 新增交叉验证段 |

## 6. 验证

```
覆盖率: 185/185 (100%)  ← 新增 1 skill
测试套件: 1374 total / 1344 passed / 2 failed (pre-existing)
新增测试: routing_coverage [PASS] / skill_manifest [PASS]
脚本: py_compile OK; 601788 + 600519 双股票实测通过
```

## 7. 5-Why Why 5（本结论最弱处）

**最薄弱：** 本 skill 的"独立性"是**相对**的，不是绝对的 —— 成交量结构虽非价格本身，但与价格**同源**（都来自交易数据），真正完全独立的只有基本面/宏观/机构持仓。且脚本内覆盖的主要是 **A股**；美股/港股/日韩的非价格维度**大量依赖 MCP**，而 MCP 当前存在超时/额度问题 —— **若 MCP 不可用，非价格层对非 A 股标的的实际覆盖会大幅缩水**。这意味着"独立验证"在 A 股最完整，在美股是"半可用"，在其他市场基本缺失。

## 8. 待办

- [ ] 补美股非价格维度：`vibe-trading-sec-edgar` Form 4 接入脚本（免鉴权）
- [ ] 补换手率（东财 push2 f168）
- [ ] 修复 `vibe-trading` MCP 超时（排查服务端）
- [ ] `llmquant-data` credits 充值确认（news/etf_holdings）
- [ ] 把两协议串成统一入口（`stock-deep-dive` 的维度 2 + 新增维度 8）
- [ ] 用两协议重跑光大证券完整分析，更新 thesis
