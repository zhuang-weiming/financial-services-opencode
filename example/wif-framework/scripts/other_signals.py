"""
other_signals.py — the NON-WIF timing skills, run on the same real data.

Answers "其他 skill 给出的信号情况如何" with computed values rather than prose.

Covered (skill -> signal implemented):
  vibe-trading-correlation-regime  -> Markov regime switching (statsmodels
                                      MarkovRegression, same model class as
                                      quantlib.timeseries.fit_markov_regime)
                                      + rolling cross-asset correlations
  llmquant-risk                    -> tail risk: historical VaR/CVaR 95/99,
                                      max drawdown, VIX regime percentile
  vibe-trading-volatility          -> realised vol 20d/60d + percentile
  vibe-trading-sentiment-analysis  -> Fear & Greed (external, passed in)
  llmquant-rates-fx                -> curve shape (level/slope)
  vibe-trading-us-etf-flow         -> sector relative strength vs SPY
  llmquant-prediction-markets      -> NOT AVAILABLE (credits/network) - stated

Data: example/wif-framework/data/_merged_prices_20260911.csv (4926 rows, to 2026-09-11)
Run:  python3 example/wif-framework/scripts/other_signals.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(os.path.dirname(HERE), "data")
sys.path.insert(0, HERE)
from wif_now import build_matrix          # noqa: E402  (no implicit file ordering)
AS_OF = "2026-09-11"

# external readings (Tier-1 MCP this session)
EXT = {
    "vix_spot": 15.84, "fear_greed": 57, "f29_bp": 151, "hy_oas_bp": 271,
    "hy_oas_date": "2026-07-15",
    "dgs10": 4.95, "dgs30": 5.37, "dgs2": 4.62, "nfci": -0.56, "stlfsi": -0.7884,
    "dxy_broad": 118.0732, "wti": 97.26,
}


def pct_rank(s: pd.Series, v: float) -> float:
    s = s.dropna()
    return float((s < v).mean() * 100) if len(s) else float("nan")


def main():
    prices = build_matrix().ffill()       # built in-process; writes nothing
    ret = prices.pct_change(fill_method=None)
    spy = ret["SPY"].dropna()
    out = {"as_of": AS_OF, "n_obs": int(len(prices))}

    print("=" * 100)
    print(f"其他 skill 的信号 — 真实数据 {prices.index.min().date()} → {prices.index.max().date()}")
    print("=" * 100)

    # ---------- 1. vibe-trading-correlation-regime : Markov regime ----------
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    win = spy.iloc[-1500:]
    mod = MarkovRegression(win.values, k_regimes=2, trend="c", switching_variance=True)
    fit = mod.fit(disp=False)
    probs = np.asarray(fit.smoothed_marginal_probabilities)
    sig_idx = [i for i, n in enumerate(mod.param_names) if n.startswith("sigma2")]
    ann_vol = [float(np.sqrt(fit.params[i]) * np.sqrt(252)) for i in sig_idx]
    order = list(np.argsort(ann_vol))                      # ascending volatility
    cur_raw = int(np.argmax(probs[-1]))
    cur = order.index(cur_raw)                             # 0 = calm, 1 = turbulent
    trans = np.asarray(fit.regime_transition)              # (k, k, T)
    dur = [1.0 / (1.0 - trans[o, o, -1]) for o in order]
    print("\n1) vibe-trading-correlation-regime / llmquant-risk — 区制（SPY 日收益，近 1500 日）")
    for i, o in enumerate(order):
        nm = "平静 calm" if i == 0 else "动荡 turbulent"
        print(f"   区制{i} {nm:14s} 年化波动 {ann_vol[o]*100:5.1f}%   期望持续 {dur[i]:5.1f} 日")
    print(f"   当前区制 = **{cur}（{'平静' if cur==0 else '动荡'}）**，平滑概率 {probs[-1][cur_raw]*100:.1f}%")
    out["markov"] = dict(regime=cur, label="calm" if cur == 0 else "turbulent",
                         prob=float(probs[-1][cur_raw]),
                         ann_vol_calm=ann_vol[order[0]], ann_vol_turb=ann_vol[order[1]],
                         duration_calm=dur[0], duration_turb=dur[1], window_days=len(win))

    # ---------- 2. correlation regime ----------
    print("\n2) 相关性 regime（60 日滚动）")
    c_spy_tlt = ret["SPY"].rolling(60).corr(ret["TLT"])
    c_spy_gld = ret["SPY"].rolling(60).corr(ret["GLD"])
    c_spy_bnd = ret["SPY"].rolling(60).corr(ret["BND"])
    for nm, c in [("SPY/TLT", c_spy_tlt), ("SPY/GLD", c_spy_gld), ("SPY/BND", c_spy_bnd)]:
        cur_v = c.iloc[-1]
        print(f"   {nm:8s} 当前 {cur_v:+.2f}  历史分位 {pct_rank(c, cur_v):4.0f}%")
    # correlation breakdown = -z of SPY/GLD 20d corr (WIF's own CSI component)
    c_gld20 = ret["SPY"].rolling(20).corr(ret["GLD"])
    z = (c_gld20 - c_gld20.rolling(60).mean()) / c_gld20.rolling(60).std()
    print(f"   SPY/GLD 20日相关 z = {z.iloc[-1]:+.2f}  （WIF 用 -z 作 CSI 分量）")
    out["corr"] = dict(spy_tlt=float(c_spy_tlt.iloc[-1]), spy_gld=float(c_spy_gld.iloc[-1]),
                       spy_bnd=float(c_spy_bnd.iloc[-1]), z_spy_gld_20d=float(z.iloc[-1]))

    # ---------- 3. vibe-trading-volatility : realised vol percentile ----------
    print("\n3) vibe-trading-volatility — 已实现波动分位（年化）")
    for w in (20, 60):
        rv = spy.rolling(w).std() * np.sqrt(252)
        v = rv.iloc[-1]
        print(f"   SPY {w:2d}日已实现波动 = {v*100:4.1f}%  历史分位 {pct_rank(rv, v):4.0f}%")
    vix = prices["VIX"]
    print(f"   VIX = {EXT['vix_spot']:.2f}  历史分位 {pct_rank(vix, EXT['vix_spot']):4.0f}% "
          f"（1990-2026 全样本以外的本矩阵 2007 起）")
    out["vol"] = dict(spy_rv20=float((spy.rolling(20).std()*np.sqrt(252)).iloc[-1]),
                      spy_rv60=float((spy.rolling(60).std()*np.sqrt(252)).iloc[-1]),
                      vix=EXT["vix_spot"], vix_pctile=pct_rank(vix, EXT["vix_spot"]))

    # ---------- 4. llmquant-risk : tail risk ----------
    print("\n4) llmquant-risk — 尾部风险（SPY 全样本 / 近 3 年）")
    for label, series in [("全样本 2007-", spy), ("近3年", spy.iloc[-756:])]:
        for q in (0.95, 0.99):
            var = float(np.percentile(series, (1 - q) * 100))
            cvar = float(series[series <= var].mean())
            print(f"   {label:12s} {int(q*100)}% 1日 VaR {var*100:+.2f}%  CVaR {cvar*100:+.2f}%")
    eq = (1 + spy).cumprod()
    dd = eq / eq.cummax() - 1
    print(f"   当前 SPY 回撤 {dd.iloc[-1]*100:+.1f}% ；历史最深 {dd.min()*100:+.1f}%")
    out["tail"] = dict(var95_1d=float(np.percentile(spy, 5)), cvar95_1d=None,
                       cur_dd=float(dd.iloc[-1]), max_dd=float(dd.min()))
    out["tail"]["cvar95_1d"] = float(spy[spy <= np.percentile(spy, 5)].mean())

    # ---------- 5. llmquant-rates-fx : curve ----------
    print("\n5) llmquant-rates-fx — 曲线形态")
    s2, s10, s30 = EXT["dgs2"], EXT["dgs10"], EXT["dgs30"]
    print(f"   2Y {s2:.2f}%  10Y {s10:.2f}%  30Y {s30:.2f}%")
    print(f"   10Y-2Y = {s10-s2:+.2f} (未倒挂) ｜ 30Y-10Y = {s30-s10:+.2f} (陡峭)")
    print(f"   DXY broad {EXT['dxy_broad']:.2f} ｜ WTI ${EXT['wti']:.2f}")
    out["rates"] = dict(dgs2=s2, dgs10=s10, dgs30=s30, slope_10y2y=round(s10-s2, 2),
                        slope_30y10y=round(s30-s10, 2))

    # ---------- 6. us-etf-flow : sector relative strength ----------
    print("\n6) vibe-trading-us-etf-flow — 行业相对强弱（相对 SPY，60 日）")
    for t in ["XLE", "QQQ", "GLD", "TLT"]:
        if t in prices.columns:
            rel = (prices[t] / prices["SPY"])
            rs = rel.iloc[-1] / rel.iloc[-61] - 1
            print(f"   {t:4s} 相对 SPY 60 日 {rs*100:+6.1f}%")
            out.setdefault("rel_strength", {})[t] = float(rs)

    # ---------- 7. credit cross-check ----------
    print("\n7) 信用交叉验证（我上轮标记的待办）")
    print(f"   投资级 BAA10Y = {EXT['f29_bp']} bp（2026-09-10，132 日收窄）")
    print(f"   高收益 HY OAS = {EXT['hy_oas_bp']} bp（{EXT['hy_oas_date']}，⚠️ 本地仅 37 行）")
    print("   → 两者都在低位（IG 151 / HY 271 bp）⇒ 信用市场整体无 stress")
    print("   → 但 HY 数据停在 7/15，无法确认 8-9 月是否同步走阔 ⚠️")

    # ---------- 8. unavailable ----------
    print("\n8) 无法取得（如实说明）")
    print("   llmquant-prediction-markets / polymarket : 额度用尽 + 网络超时")
    print("   llmquant-risk 的 fear score               : 该 MCP 无此工具；用 F&G 57 替代")
    print("   GARCH 前向波动                            : 本机缺 arch 包（quantlib 侧有 fit_garch）")

    out["credit"] = dict(baa10y_bp=EXT["f29_bp"], hy_oas_bp=EXT["hy_oas_bp"],
                         hy_oas_date=EXT["hy_oas_date"])
    out["unavailable"] = ["prediction-markets (credits/network)", "fear-score tool",
                          "garch (arch not installed locally)"]

    with open(os.path.join(DATADIR, f"other_signals_{AS_OF.replace('-','')}.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    _out = os.path.join(DATADIR, f"other_signals_{AS_OF.replace('-', '')}.json")
    print(f"\nWROTE {_out}")


if __name__ == "__main__":
    main()
