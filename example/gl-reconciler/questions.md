# GL-Reconciler Agent — Example Questions

> **Routing trigger keywords:** GL recon, GL reconciliation, break trace, reconciliation, general ledger, subledger, position mismatch, trade date reconciliation

**Data Files:**
- `data/recon_data.csv` - Trade reconciliation data for trade date 2024-03-15
- `data/recon_breaks.json` - Breaks identified with suspected causes and status

---

## Question 1: Trade Date Reconciliation
```
Using data/recon_data.csv, reconcile the general ledger to subledger for trade date 2024-03-15.

Reference: data/recon_data.csv, data/recon_breaks.json (breaks[0], breaks[1])

Breaks identified in data/recon_breaks.json:
- AAPL-US position mismatch: GL 10,000 shares, Subledger 9,500 shares (variance: $50,000)
- MSFT-US missing dividend: GL $25,000, Subledger $0 (variance: $25,000)

Please:
1) Load data/recon_data.csv and data/recon_breaks.json
2) Classify each break by likely cause (timing, system drift, or reclass)
3) Provide root cause analysis for each break
4) Show the transaction-level evidence from the data
```

---

## Question 2: Fixed Income Coupon Reconciliation
```
Run a month-end reconciliation for our fixed income portfolio as of 2024-02-29.

Reference: data/recon_data.csv (CORP-BOND-01 row)

From data/recon_data.csv:
- Account: Accrued Interest
- GL Balance: $45,000
- Subledger Balance: $45,200
- Variance: -$200 (for Financials sector corporate bonds)

Trace the source of this $200 variance for corporate bonds in the Financials sector.

Additional data in data/recon_breaks.json may show patterns from prior periods.
```

---

## Question 3: Cash and Securities Breakdown
```
Our daily reconciliation for 2024-03-20 shows cash position variance of $2.3 million.

Reference: data/recon_data.csv (USD cash account rows), data/recon_breaks.json

Using the data files:
1) Identify which accounts have variances
2) Calculate total variance by asset class
3) Flag any accounts exceeding the $10,000 threshold
4) Draft the exception report for controller review
```

## Question 4: Premier 跨券商账户对账
```
请帮我检查我在多个券商/钱包之间的持仓记录是否一致。

Reference: data/premier_broker_recon.csv

From data/premier_broker_recon.csv:
- 4 个账户（富途融资/现金、盈透、OKX）+ 2 个银行账户
- 覆盖 A股/港股/美股/crypto/银行理财
- 发现 2 处差异：NVDA 少 2 股，ETH 少 0.2 个

Please:
1) 按账户汇总持仓价值和差异
2) 分析两处差异（NVDA 和 ETH）的可能原因（股息再投资/转出/记录错误/未结算交易？）
3) 对每处差异建议排查步骤和解决路径
4) 计算差异金额占总资产的比例，判断严重程度
5) 如果差异超过总资产的 0.5%，建议采取什么纠偏措施
6) 设计一个 Premier 投资者月度对账的简化流程
7) 推荐一个统一管理多账户的工具或方法
```

## Question 5: 股息/分红追踪检查
```
请帮我检查我的持仓中应该收到的股息/分红是否已全部到账。

Reference: data/premier_broker_recon.csv

假设以下股息/分红事件（演示用）：
- 贵州茅台：2026-06-15 除息，每股分红 30 元，我持有 1200 股 → 应收到 36000 元
- Apple：2026-05-12 除息，每股 $0.25，我持有 200 股 → 应收 $50
- 招商银行：2026-07-01 除息，每股分红 1.8 元，我持有 18000 股 → 应收 32400 元

检查记录（假设）：
- 富途账户 2026-06-17 收到茅台分红 36000 元 ✓
- 盈透账户无 Apple 分红记录 ✗
- 富途账户 2026-07-03 收到招行分红 32400 元 ✓

Please:
1) 列出所有应到的股息/分红及预计到账日期
2) 逐笔核实是否已收到（标注 ✓/✗）
3) 对未收到的分红做根源分析：
   - 是否已到账但未区分？
   - 是否被预扣税了？
   - 是否被系统自动再投资了？
4) 对 Apple 分红的缺失给出排查步骤
5) 解释中国/美国不同的股息税政策（A 股免税 vs 美股预扣 10-30%）
6) 建议如何系统化地追踪股息收入
```