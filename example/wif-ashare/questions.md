# WIF A-Share Cookbook — Example Questions

> **Routing trigger keywords:** A股WIF, MCI, PMI M2, MA60趋势, 沪深300配置, A股象限, Wealth Investment Framework A股, A股资产配置

**Data Files:**
- `data/etf_prices_new.csv` — 4 ETF daily prices (2013-2026, 3095 rows)
- `data/index_csi500_daily.csv` — CSI500 index daily close
- `data/index_tech_399303_daily.csv` — 国证科技指数 daily close
- `data/macro_pmi.csv` — PMI monthly data (2008-2026)
- `data/macro_m2_m1_spread.csv` — M2/M1 monthly data (2008-2026)
- `data/nav_v27.csv` — WIF v2.7 backtest NAV series

**Python package:** `wif_framework.ashare` (MCI / quadrant / MA60 trend / EMERGENCY)

---

## Question 1: 当前A股宏观象限判定
```
请使用 WIF A 股框架 v2.7（MCI + MA60趋势）分析当前 A 股市场。

参考数据:
- data/macro_pmi.csv — 最新 PMI 数据
- data/macro_m2_m1_spread.csv — 最新 M2 数据
- data/etf_prices_new.csv — 沪深300日线

请:
1) 计算当前 MCI = PMI_norm × 0.5 + M2_norm × 0.5
2) 根据 MCI 值判定象限（Q1 ≥ 0.53, Q2 0.47~0.53, Q3 ≤ 0.47）
3) 计算沪深300的MA60趋势偏离度
4) 若趋势偏离 > +7% 或 < -7%，覆盖 MCI 象限
5) 给出当前有效象限和资产配置建议
```

## Question 2: A股WIF v2.7 回测分析
```
分析 WIF v2.7 的 A 股回测结果，评估策略的长期表现。

参考数据:
- data/nav_v27.csv — v2.7每日NAV序列
- data/etf_prices_new.csv — 基准资产价格

从回测结果:
- 回测区间: 2013-2026 (约12.3年)
- 策略: PMI+M2 → MCI → 象限 + MA60趋势覆盖

请:
1) 计算累计收益、年化收益、夏普比率、最大回撤
2) 对比 v2.7 vs v2.5 vs 沪深300分年度表现
3) 分析 MA60 趋势覆盖（方向A）的贡献：触发天数、覆盖场景
4) 识别 EMERGENCY 保护机制的关键事件触发
5) 评估策略的强项和弱项
```

## Question 3: A股WIF MA60参数敏感性
```
对 WIF v2.7 的 MA60 趋势覆盖阈值（±7%进行参数敏感性分析）。

参考数据:
- data/etf_prices_new.csv
- data/index_csi500_daily.csv

请:
1) 解释为什么方向A选择 ±7% 而非 ±5% 或 ±10%
2) 在不同阈值下测试 MA60 覆盖的触发频率
3) 分析 2015 年 MA60 滞后代价（-12.1pp）
4) 评估是否有更优的动态阈值方案
```

## Question 4: 沪深300vs中证500暴露调整
```
分析 WIF v2.7 中沪深300和中证500的配置比例逻辑。

参考数据:
- data/etf_prices_new.csv

请:
1) 解释为什么中证500权重设为沪深300的30%
2) 分析沪深300 vs 中证500在不同市场风格中的表现差异
3) 评估当前市场环境下是否需要调整比例
4) 提出风格轮动（方向G）的改进建议并分析其效果
```

## Question 5: EMERGENCY机制审计
```
审计 WIF A 股框架的 EMERGENCY 三级保护机制。

参考数据:
- data/etf_prices_new.csv — 沪深300日线
- data/nav_v27.csv — 回测结果

请:
1) 列出所有 L1/R20<-8%、L2/R20<-12%、L3/R20<-20% 触发事件
2) 检查每次 EM 的进入和退出日期（谷值相对退出 θ=10%）
3) 评估 EM 在 2015 股灾、2016 熔断、2020 COVID 中的保护效果
4) 分析 EM 带来的上行成本（2019 等年份因 EM 错过的涨幅）
5) 给出 EM 机制改进建议
```
