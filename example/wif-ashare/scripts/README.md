# WIF v2.7（A股）脚本 — 规范位置

| 脚本 | 作用 | 输出 |
|---|---|---|
| `ashare_now.py` | 用 `ashare.py` 原函数跑当前 A股读数（MCI → 象限 → MA60 覆盖 → EMERGENCY → 权重）| `data/ashare_assessment_<date>.json` |

复跑：`python3 example/wif-ashare/scripts/ashare_now.py`

## 数据新鲜度（2026-09-11 快照）
- `macro_pmi.csv` — **PMI 到 2026-08（49.8）**，仓内 9/1 更新
- `macro_m2_m1_spread.csv` — M2 到 2026-06（8.0%），**滞后 2 个月**
- `data/_increments/hs300_tencent_20260911.csv` — HS300 85 个交易日（Tier-1 Tencent）
- `etf_prices_new.csv` — 截至 2026-04-22（仅回测用）

## 阈值（来自 `ashare.py`，勿手改）
```
MCI = 0.5×clamp((PMI-47)/6) + 0.5×clamp((M2-6)/9)
Q1 ≥ 0.53 | Q2 0.47~0.53 | Q3 ≤ 0.47
MA60 趋势覆盖 ±7%（>+7% 强制 Q1；<-7% 强制 Q3）
EMERGENCY: R20<-8% L1 | <-12% L2 | <-20% L3
优先级：EM > MA60 > MCI
```
