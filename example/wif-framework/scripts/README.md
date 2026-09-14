# WIF scripts — 从 `out/`（临时区）迁入的规范位置

| 脚本 | 作用 | 输出 |
|---|---|---|
| `wif_now.py` | 读官方矩阵 + Tier-1 增量 → 重建矩阵 → 五层读数 | `data/_merged_prices_<date>.csv`, `data/wif_now_latest.json` |
| `wif_assessment.py` | 生成 WIF 相位评估（沿用仓内惯例 schema）| `data/wif_phase_assessment_<date>.json` / `.md` |
| `other_signals.py` | 非 WIF 的择时 skill 信号（Markov 区制 / 尾部 / 波动 / 曲线 / 轮动）| `data/other_signals_<date>.json` |

复跑：
```bash
python3 example/wif-framework/scripts/wif_assessment.py   # 另两个同理
```

## ⚠️ 两个必须保留的修复（都针对**官方文件自带**的缺陷）

1. **`deglitch()`** — 官方 `_merged_prices_20260716.csv` 在 **2026-06-09 换口径**
   （前半段原始收盘 / 后半段复权价，SPY 739→1342 ×1.816）。不修会把 126 日动量虚高，
   象限被误判为 **Q4 Overheat**（假 +41.3%），修正后为 **Q2 Recovery**（+12.1%）。
2. **比例拼接** — Tier-1 取到的是**原始收盘**，官方矩阵是**复权价**（SPY 750.72 vs 1369.98）。
   1:1 拼接会制造 −45% 假跳空。价格用**乘性**对齐，VIXTERM 用**加性**对齐。

**⚠️ VIX / VIXTERM 不参与去抖动** —— 它们单日 ±30-50% 在 2008/2010/2011 是真实的。

**自检：** `build_matrix()` 末尾会打印 `max |1-day move|`；若出现 `⚠️ still has jumps` 说明还有未处理的断裂。
