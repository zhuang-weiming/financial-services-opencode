---
name: vibe-trading-gann
description: 江恩理论 (W.D. Gann) 分析引擎 — 角度线(1×1/2×1/1×2)、Square of 9 (价格平方根增量)、时间价格正方 (Time-Price Squaring)、7 规则周期、50% 法则。纯 pandas/math 实现，适用于任意 OHLCV。当用户问"江恩"/"Gann"/"角度线"/"时间之窗"/"平方根支撑压力"时加载；或作为 trend-analysis-multi-algo 协议的第 10 个算法。
category: strategy
---

# 江恩理论 (Gann Analysis)

## 用途

W.D. Gann 的几何/周期方法，全部从数据自动推导（无硬编码价格）：

| 方法 | 含义 |
|---|---|
| **Gann Angles** | 时间-价格几何比率：1×1 = 45°，2×1 更陡 |
| **Square of 9** | 由 √price 增量推导的价格水平 |
| **Time-Price Squaring** | 关键日历窗口（时间与价格"正方"）|
| **Rule of 7** | 以 7 的倍数为市场周期 |
| **50% Rule** | 价格区间的关键中点 |

## 用法

```python
import sys
sys.path.insert(0, ".opencode/skills/vibe-trading-gann/examples")
from spcx_analysis import analyze_gann

result = analyze_gann(df)   # df 需含 date/open/high/low/close
```

或通过多算法协议统一调用：

```bash
python3 .opencode/skills/trend-analysis-multi-algo/scripts/trend_analysis.py --code 601788 --market sh
```

## 输出字段

| 字段 | 含义 |
|---|---|
| `overall_high` / `overall_low` | 区间高低 |
| `recent_low` / `recent_low_date` | 最近 swing 低点 |
| `angles_from_start` / `angles_from_recent_low` | 从起点/近期低点的角度线 |
| `sq9_current` / `sq9_overall_high` / `sq9_overall_low` | Square of 9 水平 |
| `time_windows` | 时间价格正方窗口 |
| `rule_of_7` | 7 规则周期（days / mod7 / interpretation）|
| `50pct_midpoint` / `distance_to_50pct_pct` | 50% 中轴及当前价距中轴百分比 |

## 信号逻辑（多算法协议内）

- 收盘价 > 50% 中轴 → 偏多（+1）；< 中轴 → 偏空（-1）
- 强度固定 0.4（江恩方法主观性强，权重低于 WaveTrend/缠论）

## 失效条件

- 江恩理论缺乏严格统计验证，**主观性强** —— 在多算法协议中权重最低（0.4）
- 角度线依赖起点选择（起点不同 → 结果差异大）
- Square of 9 的水平更像"心理位"而非统计支撑
- **不单独作为交易信号**，仅作辅助参考

## 依赖

纯 `pandas` + `math`，无额外依赖。

## 与多算法协议的关系

本 skill 是 `trend-analysis-multi-algo` 的 **C3 算法**。协议脚本通过
`importlib.util.spec_from_file_location` 直接加载 `examples/spcx_analysis.py`
的 `analyze_gann`，无需安装。
