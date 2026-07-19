# Fund-Admin Agent — Example Questions

> **Routing trigger keywords:** NAV tie-out, NAV tieout, accrual schedule, roll-forward, variance commentary, fund admin, fund administration, cash flow projection

**Data Files:**
- `data/lp_capital_accounts.csv` — LP capital accounts
- `data/accrual_schedule.json` — Accrual schedule
- `data/nav_tieout.json` — NAV tieout
- `data/roll_forward.json` — Roll-forward
- `data/cash_flow_projection.json` — Cash flow projection

---

## Question 1: NAV Tieout
```
Tie out LP statement to fund NAV pack.

Reference: data/nav_tieout.json, data/lp_capital_accounts.csv

From data/nav_tieout.json:
- NAV Date: 2024-03-31
- Total NAV: $45M
- Harborview: Cleared
- Meridian: $50K variance, pending

From data/lp_capital_accounts.csv:
- Harborview: $25M commitment, NAV $28M
- Meridian: $15M commitment, NAV $16.5M

Please:
1) Recompute LP capital accounts
2) Identify variance source
3) Clear or escalate
4) Confirm final NAV
```

## Question 2: Accrual Schedule Review
```
Review March accrual schedule.

Reference: data/accrual_schedule.json

From data/accrual_schedule.json:
- Management Fee: $125K (pending)
- Audit Fee: $45K (approved)
- Legal Fee: $15K (pending)

Please:
1) Validate entry amounts
2) Cite support documentation
3) Draft journal entries
4) Flag for controller approval
```

## Question 3: Build accrual schedule for month-end close
```
Build the period-end accrual schedule for month-end close. For each accrual, compute the entry, cite the support, and draft the journal entry.

Reference: data/accrual_schedule.json, data/roll_forward.json

Please:
1) List all required accruals for the period
2) Compute each accrual amount with supporting documentation
3) Draft journal entries for controller approval
4) Flag any items requiring manual review
```

## Question 4: 读懂你的基金 NAV 报告
```
作为 Premier 投资者，请帮我解读我的基金持仓的 NAV 报告。

Reference: data/premier_nav_report.csv, data/lp_capital_accounts.csv

From data/premier_nav_report.csv:
- 5 只基金的 2 个时间点（2026-06-30 和 2026-07-15）的 NAV 数据
- 包含：份额净值、总资产净值、各项应计费用、申赎流量

From data/lp_capital_accounts.csv:
- LP 资本账户作为参考格式

Please:
1) 计算每只基金在 6/30 到 7/15 期间的收益率
2) 分析应计费用的合理性（管理费/行政费/业绩报酬占比）
3) 解读申赎流量：哪些基金在净申购、哪些在净赎回，说明什么信号
4) 查看基金的总 NAV 变化是来自投资收益还是来自资金流量
5) 计算加权平均持有成本（从现有数据推导）
6) 如果发现异常（如 NAV 大幅异动），标注并排查原因
7) 生成一份一目了然的基金持仓健康表
```

## Question 5: 基金费用透明度全透视
```
请帮我全面审查持仓基金的费用结构，找出隐性成本。

Reference: data/premier_fee_analysis.csv, data/premier_nav_report.csv

From data/premier_fee_analysis.csv:
- 8 只基金的费率明细（管理/托管/申赎/业绩报酬）
- 与同类中位数和百分位的对比
- 部分基金费率处于行业高位

From data/premier_nav_report.csv:
- 实际计提费用数据

Please:
1) 按综合费率从高到低排列我的持仓基金
2) 每只基金费率与同类中位数对比，标注"偏高/正常/偏低"
3) 计算费率对长期收益的侵蚀效应（假设 10 年持有，费率差异对终值的影响）
4) 识别隐性成本（交易佣金/印花税/冲击成本/资金占用成本）
5) 相同类别的基金（如偏股混合型）中，推荐费率更低的替代品
6) 建议哪些费率高的基金值得继续持有（如果业绩确实好），哪些应该换掉
7) 给出一个"降低费率 50bp"的优化方案及预期收益提升
```
