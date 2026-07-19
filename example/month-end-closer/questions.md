# Month-End-Closer Agent — Example Questions

> **Routing trigger keywords:** month-end close, close package, accrual schedule, roll-forward, variance commentary, month end

**Data Files:**
- `data/accrual_schedule.csv` — Accrual schedule
- `data/close_package.json` — Close status

---

## Question 1: Month-End Close Checklist
```
Run the month-end close for March 2024.

Reference: data/accrual_schedule.csv, data/close_package.json

From data/accrual_schedule.csv:
- Cash: $13.5M balanced
- Equity Positions: $2.5M balanced
- Accrued Expenses: $490K vs GL $485K = $5K variance

From data/close_package.json:
- Close Date: 2024-03-31
- Status: in_progress
- Variance Count: 2 (threshold $1K)
- Pending: Accrued Expenses ($5K), Prepaid Assets ($2.5K)

Please:
1) Review variance items
2) Determine root cause
3) Draft journal entries for approvals
4) Update close status
```

## Question 2: Accrual Schedule Review
```
Validate the accrual schedule for March.

Reference: data/accrual_schedule.csv

From data/accrual_schedule.csv:
- Accrued Expenses: $490K ending balance
- Variance vs GL: $5,000

Please:
1) Trace beginning balance
2) Verify additions and reductions
3) Identify variance driver
4) Propose adjustment
```

## Question 3: Run variance commentary for income statement
```
Run the variance commentary for the income statement vs budget for March.

Reference: data/close_package.json, data/accrual_schedule.csv

Please:
1) Compare actual P&L to budget by line item
2) Flag items exceeding 10% variance
3) Explain key drivers of significant variances
4) Draft commentary for management review
```

## Question 4: Premier 月度财务关账检查清单
```
请帮我完成 6 月的个人财务关账检查。

Reference: data/premier_monthly_close.csv, data/close_package.json

From data/premier_monthly_close.csv:
- 6 月收支明细（收入 3 项/支出 8 项/储蓄 1 项）
- 预算 vs 实际对比
- 部分项目有显著差异（娱乐+56%/教育+50%/投资+20%）

From data/close_package.json:
- 参考月末结账清单格式

Please:
1) 逐项对比预算与实际，标记超过 10% 偏差的项目
2) 对每项显著偏差分析原因（一次性/趋势性/季节性/异常）
3) 计算当月储蓄率和累计储蓄率（年初至今）
4) 检查是否有未记录的应收/应付项目
5) 检查投资新增投入是否与计划一致
6) 汇总本月财务状况亮点和需要关注的问题
7) 给出下月的预算调整建议
```

## Question 5: 应计项目对 Premier 投资者意味着什么
```
请解释权责发生制对理解基金收益和税务的影响。

Reference: data/premier_monthly_close.csv, data/accrual_schedule.csv

From data/premier_monthly_close.csv:
- 我的个人记账用的是收付实现制（按实际收支记录）

From data/accrual_schedule.csv:
- 基金层面的应计项目参考

Please:
1) 用通俗语言解释收付实现制 vs 权责发生制的区别
2) 分析我现在用收付实现制记账可能遗漏了什么：
   - 基金应计但未到账的收益
   - 应付但未支付的费用（如信用卡/税费）
   - 预付款项（如预付年费）
3) 做一个收付实现制 vs 权责发生制的对比试算（用我的 6 月数据）
4) 解释基金收益分配中的权责发生制：
   - 基金公布的收益率是哪种核算方法
   - 为什么我看到的收益和实际现金到账有差异？
5) 税务层面的影响：什么时候就基金收益交税？
6) 建议我是否需要切换到权责发生制记账，及如何操作
```
