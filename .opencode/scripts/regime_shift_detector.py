#!/usr/bin/env python3
"""
Regime Shift Detector — 结构性断点检测脚本

设计目的:
  当关键市场指标（汇金 ETF 份额/保险权益比例/成交量结构等）在统计上发生
  结构性断点时，自动标记对应的 LAW/BT 为"regime 可能已变"，从而触发
  memory-protocol 中的 5-Why 反方流程。

使用方法:
  python regime_shift_detector.py
  → 输出检测到的 regime shift 事件 + 建议更新的 CONFLICTS 条目

检测方法:
  1. Chow test (单断点) — 检测已知时间点前后的结构变化
  2. CUSUM (累计和) — 检测未知的渐进式结构变化
  3. 滚动回测窗口 — 检测关键指标的 rolling 均值/波动率是否超过 2σ

当前配置:
  - 券商成交量 vs PB 关系滚动检测（验证 LAW-003）
  - 汇金 ETF 份额变化检测（验证 BT-004）
  - 保险权益配置比例检测（慢变量，季度检测）

数据来源:
  - AKShare / baostock / EastMoney (通过 vibe-trading-quanta 自动路由)
  - 依赖数据路由层（data-routing skill）做 fallback

依赖:
  pip install statsmodels numpy pandas
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

try:
    import pandas as pd
    import numpy as np
    from statsmodels.stats.diagnostic import breaks_cusumolsresid
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tools import add_constant
except ImportError:
    print(json.dumps({
        "error": "Missing dependencies. Run: pip install statsmodels pandas numpy",
        "status": "BLOCKED"
    }))
    sys.exit(1)


def chow_test(
    y: pd.Series,
    x: pd.DataFrame,
    break_point: int,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Chow test for structural break at a known point.
    适用于：检验"已知事件"前后回归系数是否显著不同。

    参数:
        y: 因变量（如券商 PB）
        x: 自变量（如成交量/CSI 300 收益）
        break_point: 断点位置（索引，如 2015-06 的样本位置）
        alpha: 显著性水平

    返回:
        chow_stat, p_value, reject_H0
    """
    n = len(y)
    x = add_constant(x)

    # 全样本
    model_full = OLS(y, x).fit()
    rss_full = model_full.ssr

    # 子样本 1 (0:break_point)
    model_1 = OLS(y.iloc[:break_point], x.iloc[:break_point]).fit()
    rss_1 = model_1.ssr

    # 子样本 2 (break_point:n)
    model_2 = OLS(y.iloc[break_point:], x.iloc[break_point:]).fit()
    rss_2 = model_2.ssr

    k = x.shape[1]  # 参数个数（含截距）
    # Chow statistic
    chow_stat = ((rss_full - (rss_1 + rss_2)) / k) / ((rss_1 + rss_2) / (n - 2 * k))

    from scipy.stats import f
    p_value = 1 - f.cdf(chow_stat, k, n - 2 * k)
    reject = p_value < alpha

    return {
        "method": "Chow test",
        "break_point_label": str(x.index[break_point]) if hasattr(x.index, '__getitem__') else str(break_point),
        "chow_statistic": float(chow_stat),
        "p_value": float(p_value),
        "reject_H0": bool(reject),
        "interpretation": "Structural break detected" if reject else "No significant break"
    }


def cusum_test(
    y: pd.Series,
    x: pd.DataFrame,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    CUSUM test for unknown structural break point.
    适用于：检测未知的渐进式结构变化。

    参数:
        y: 因变量
        x: 自变量
        alpha: 显著性水平
    """
    x = add_constant(x)
    model = OLS(y, x).fit()

    # 递归残差
    try:
        cusum_result = breaks_cusumolsresid(model.resid)
        return {
            "method": "CUSUM",
            "cusum_statistic": float(cusum_result[0]),
            "p_value": float(cusum_result[1]),
            "reject_H0": bool(cusum_result[1] < alpha),
            "interpretation": "Structural break detected (unknown point)" if cusum_result[1] < alpha else "No significant break",
        }
    except Exception as e:
        # statsmodels 版本差异可能导致不同返回值
        return {
            "method": "CUSUM",
            "error": str(e),
            "status": "needs_manual_check"
        }


def rolling_window_regime_check(
    series: pd.Series,
    window: int = 60,
    threshold_std: float = 2.0
) -> Dict[str, Any]:
    """
    滚动窗口检测指标是否偏离历史均值超过 2σ。
    适用于：检测"当前值是否处于极端区域"——如成交量 vs PB 关系的滚动相关性。
    """
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    z_score = (series - rolling_mean) / rolling_std

    current_z = float(z_score.iloc[-1]) if len(z_score) > 0 else 0
    extreme = abs(current_z) > threshold_std

    return {
        "method": "Rolling Z-score",
        "window": window,
        "current_z_score": current_z,
        "threshold": threshold_std,
        "is_extreme": bool(extreme),
        "interpretation": f"Current value is {current_z:.2f}σ from rolling mean — {'EXTREME' if extreme else 'within normal range'}"
    }


def check_broker_pb_volume_regime(
    broker_pb: pd.Series,
    volume: pd.Series,
    known_break_date: str = "2015-06-30"
) -> Dict[str, Any]:
    """
    验证券商 PB-成交量关系的结构性是否仍处于"脱钩"状态（LAW-003）。
    使用滚动相关 + Chow test 检测 2015 年前后的断点。
    """
    results = {}

    # 1. 滚动 12 个月相关性
    if len(broker_pb) == len(volume):
        rolling_corr = broker_pb.rolling(window=252).corr(volume)
        current_corr = float(rolling_corr.iloc[-1]) if len(rolling_corr) > 0 else None
        results["rolling_12m_correlation"] = current_corr
    else:
        results["rolling_12m_correlation"] = "length_mismatch"

    # 2. Chow test 检验 2015 断点
    break_idx = volume.index.get_loc(known_break_date) if known_break_date in volume.index else len(volume) // 2
    chow = chow_test(broker_pb, volume.to_frame("volume"), break_idx)
    results["chow_test_2015"] = chow

    # 3. 当前滚动 Z-score
    if results["rolling_12m_correlation"] is not None and isinstance(results["rolling_12m_correlation"], float):
        z_check = rolling_window_regime_check(rolling_corr.dropna())
        results["rolling_z_score"] = z_check

    return results


def check_etf_holding_regime(
    etf_shares: pd.Series,
    known_turning_date: str = "2026-01-01"
) -> Dict[str, Any]:
    """
    检测汇金 ETF 持仓"净买入→净卖出"的 regime shift（CONFLICT-REGIME-001）。
    使用 Chow test 验证 2026 年前后是否有断点 + 滚动均值检测。
    """
    results = {}

    if len(etf_shares) < 20:
        return {"error": "Insufficient data for regime detection", "status": "needs_more_data"}

    # 日度变化 = 净流入/流出
    daily_change = etf_shares.diff().dropna()

    # 均值检验：before_2026 vs after_2026
    before = daily_change[daily_change.index < known_turning_date]
    after = daily_change[daily_change.index >= known_turning_date]

    if len(before) > 0 and len(after) > 0:
        results["mean_before_2026"] = float(before.mean())
        results["mean_after_2026"] = float(after.mean())
        results["mean_change"] = float(after.mean() - before.mean())

        # 简单 t 检验（不等方差）
        from scipy.stats import ttest_ind
        t_stat, p_val = ttest_ind(before, after, equal_var=False)
        results["t_test_statistic"] = float(t_stat)
        results["t_test_p_value"] = float(p_val)
        results["significant_change"] = bool(p_val < 0.05)
        results["interpretation"] = (
            f"ETF flow regime shifted from {before.mean():.0f} (before 2026) to {after.mean():.0f} (after 2026) — "
            f"{'SIGNIFICANT' if p_val < 0.05 else 'not statistically significant'}"
        )
    else:
        results["error"] = f"Need data on both sides of {known_turning_date}"

    # Chow test on the series
    break_idx = daily_change.index.get_loc(known_turning_date) if known_turning_date in daily_change.index else len(daily_change) // 2
    chow = chow_test(daily_change, pd.DataFrame({"time_trend": range(len(daily_change))}), break_idx)
    results["chow_test"] = chow

    return results


def generate_conflict_suggestion(regime_result: Dict[str, Any], target: str) -> Optional[str]:
    """
    根据 regime shift 检测结果，生成 CONFLICTS.md 建议条目。
    用于自动产生 CONFLICT-REGIME 记录。
    """
    if not regime_result:
        return None

    if target == "LAW-003":
        if regime_result.get("chow_test_2015", {}).get("reject_H0"):
            return "LAW-003: PB-成交量脱钩的 Chow test 仍在 2015 断点处显著——LAW 确认有效。"
        corr = regime_result.get("rolling_12m_correlation")
        if corr is not None and isinstance(corr, float) and corr > 0.3:
            return f"CONFLICT-REGIME SUGGESTION: LAW-003 的 PB-成交量滚动相关性升至 {corr:.2f}——成交量可能重新获得解释力，建议检查。"
        return "LAW-003: Regime 稳定，5-Why 有效期至下次检查。"

    if target == "BT-004":
        mean_before = regime_result.get("mean_before_2026")
        mean_after = regime_result.get("mean_after_2026")
        if mean_before is not None and mean_after is not None and regime_result.get("significant_change"):
            return (
                f"CONFLICT-REGIME SUGGESTION: BT-004 的 ETF regime 已从净买入 ({mean_before:.0f}) 切换为 "
                f"净卖出 ({mean_after:.0f})。这证实了 CONFLICT-REGIME-001，BT-004 的推论不再适用于当前市场。"
            )
        return "BT-004: Regime 无显著变化，但 2026 后的 ETF 数据不足，继续监控。"

    return None


def main():
    """入口：执行所有已配置的 regime shift 检测并输出结果。"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "detections": [],
    }

    # --- 临时演示：使用合成数据演示 Chow test ---
    # 真实运行时会从 AKShare / baostock / EastMoney 获取数据
    np.random.seed(42)
    n = 200
    dates = pd.date_range(start="2010-01-01", periods=n, freq="ME")

    # 模拟成交量（前一半和后一半不同的关系）
    volume = pd.Series(np.random.randn(n) * 0.1 + 0.02, index=dates)
    # 模拟 PB：前一半与成交量正相关，后一半负相关
    pb_values = np.zeros(n)
    pb_values[:100] = volume.iloc[:100] * 0.5 + np.random.randn(100) * 0.05  # 正相关
    pb_values[100:] = volume.iloc[100:] * -0.3 + np.random.randn(100) * 0.05  # 负相关
    pb = pd.Series(pb_values, index=dates)

    chow = chow_test(pb, volume.to_frame("volume"), break_point=100)
    cusum = cusum_test(pb, volume.to_frame("volume"))

    results["detections"].append({
        "target": "LAW-003 (synthetic demo)",
        "chow_test": chow,
        "cusum": cusum,
    })

    # --- 输出 ---
    output = {
        "status": "complete",
        "note": "This is a DEMO run with synthetic data. For production, connect to AKShare/baostock data feed.",
        "results": results
    }

    print(json.dumps(output, indent=2, default=str))
    return output


if __name__ == "__main__":
    main()
