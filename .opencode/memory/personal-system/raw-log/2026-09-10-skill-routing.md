# 2026-09-10 — Skill 路由覆盖率治理（三层架构 + 清单自动生成）

> **本次产出**：`.opencode/scripts/gen_skill_manifest.py` + `.opencode/instructions/skill-manifest.md` + 路由表补全 + 2 个覆盖率测试 + gann skill 修复
> **状态标签**：NEW_ARCHITECTURE（三层路由）+ COVERAGE_FIX（139/184 → 184/184）+ CONSOLIDATION（gann / _shared）
> **触发**：用户问"像趋势分析这样的 skill 需要路由注册，那么其他众多 skill 是否也需要？而不是让用户记住每个 skill 的名字？"

---

## 1. 审计结果（问题确认）

| 项 | 数量 |
|---|---:|
| 全部 skill | 184 |
| 原路由已覆盖 | 139（75.5%）|
| **未覆盖** | **45（24.5%）** |
| ├─ 可路由但未注册 | 36 |
| ├─ 工具/元 skill（应豁免）| 7 |
| └─ 损坏/无 SKILL.md | 2（`_shared`, `gann`）|

**关键发现**：用户刚指出的趋势算法（`vibe-trading-candlestick` / `vibe-trading-chanlun` / `vibe-trading-technical-basic`）正在未注册列表中 —— 证明"用户必须记住 skill 名"是真问题。

## 2. 架构决策：不是"手工注册 184 个"，而是三层

```
Layer 1  意图 → subagent      wealth-guide-router.md（手写，~20 subagent，高质量）
Layer 2  skill 发现层         skill-manifest.md（自动生成，184 skill 全覆盖）
Layer 3  覆盖率测试           tests/test_skills.py::test_skill_routing_coverage
```

**核心洞察**：`SKILL.md` 的 frontmatter `description` **本身就是路由元数据**。自动解析生成清单后，所有 skill 天然可被语义匹配发现 —— 无需逐条手工登记。

- **Layer 1（决策层）** 保持手写：意图 → subagent 的权威映射，质量优先
- **Layer 2（发现层）** 自动生成：保证零遗漏
- **Layer 3（治理）** CI 断言：新增 skill 未注册 → 测试失败

## 3. 交付物

| 文件 | 内容 |
|---|---|
| `.opencode/scripts/gen_skill_manifest.py` | 自动生成清单 + 覆盖率检查（`--check` 退出码非零）|
| `.opencode/instructions/skill-manifest.md` | 184 skill 清单（214 行，自动生成）|
| `wealth-guide-router.md` | 新增三层架构说明 + "补充 Skill 注册"节（36 skill 按意图分组）|
| `tests/test_skills.py` | 新增 `test_skill_routing_coverage` + `test_skill_manifest_fresh` |
| `vibe-trading-gann/SKILL.md` | 新建（gann 有可用代码但缺描述文件，重命名目录对齐规范）|
| `_shared/README.md` | 标注旧版 8 框架 runner 已被 `trend-analysis-multi-algo` 取代 |

## 4. 36 个补注册 skill（按意图分组）

估值方法 / 基本面筛选 / 股息分析 / 基金分析 / 行业轮动 / A股资金面 / 策略类(ML·配对·季节性·执行·分钟) / 策略导出(Pine·vnpy) / 数据源补充(OKX·CCXT·SEC·QVeris) / 私有公司研究 / 瓶颈猎手 / 深度公司系列 / 研究纪律·目标 / 地缘风险·微观结构·监管·社媒 / Crypto进阶(DeFi·代币) / 个人系统(personal-trading-system·buy-ladder·sell-ladder) / 交易复盘(交割单·影子账户) / 趋势算法(10 算法协议)

## 5. 附带整合（发现重叠后）

1. **`_shared/run_technical_analysis.py`**（旧版 8 框架 runner）与新 `trend-analysis-multi-algo`（10 算法）重叠 → 旧版标注 deprecated，指向新 skill
2. **`gann`** → 重命名 `vibe-trading-gann` + 新建 SKILL.md + 整合为**第 10 个算法**（原协议 9 个遗漏了江恩）
3. **`_shared`** → 归类为"内部共享资源目录（非 skill）"，不计入覆盖率缺口

## 6. 验证

```
覆盖率: 184/184 (100%)   ← 原 139/184
  ├─ 可路由但未注册: 0
  ├─ 工具/元 skill: 0
  └─ 内部共享目录: 1 (_shared)

测试套件: 1369 total / 1339 passed / 2 failed (pre-existing: MP-1b 内存命名 + QB-2 BT 目录)
新增测试: test_skill_routing_coverage [PASS] / test_skill_manifest_fresh [PASS]

趋势协议: 10 算法全部跑通 (新增江恩)
```

## 7. 5-Why Why 5（本结论最弱处）

**最薄弱：** Layer 2 的"自动清单"只解决了**发现**问题，没有解决**匹配质量**问题 —— `description` 的语义匹配依赖 LLM 判断，若两个 skill 的 description 相似（如 `vibe-trading-sec-edgar` vs `vibe-trading-edgar-sec-filings`，名字和描述几乎重复），agent 可能加载错的那个。**清单保证"零遗漏"，但不保证"选对"。** 真正的质量仍依赖 Layer 1 手写路由表的精度，以及 skill 本身的 description 是否写得有区分度。下一步应：(a) 检测 description 高度相似的 skill 对（冗余审计）；(b) 给 Layer 2 加"加载后自检"（skill 内容是否匹配任务）。

## 8. 待办

- [ ] description 冗余审计（如 sec-edgar vs edgar-sec-filings 这类近重复）
- [ ] 把 `gen_skill_manifest.py --check` 接入 CI（当前仅测试套件覆盖）
- [ ] `_shared/run_technical_analysis.py` 考虑直接删除（完全被新 skill 取代）
- [ ] MP-1b / QB-2 两个 pre-existing 测试失败单独修复（与本次无关，但已挂账多次）
