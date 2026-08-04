#!/usr/bin/env python3
"""Debt-restructuring-by-asset-blowdown - mechanism & sensitivity (research only).
No trading advice. Mechanisms only. Baseline constants validated vs FRED in repo
(1946-74: g_nom 7.4 > i 4.2, real +1.7 positive, debt-dyn model err 0.013 pp/yr).
"""

GDP          = 30.0   # $T nominal
DG0          = 123.0  # Debt/GDP start (percent)
DGT          = 80.0   # target (percent)
EQ_MC        = 57.0   # US equity mkt cap $T
GS10, CPI, G_REAL = 4.30, 3.00, 1.80
G_NOM = G_REAL + CPI          # 4.80
PRIM  = 6.0                   # primary deficit % of GDP


def lo_re(c, r):
    lo = 1 - c
    re = (1 - c) * (1 + r)
    return lo, re


# ---------------- MODEL 1 : crash -> recovery (redistribution) ---------------
def model1(c, r, lam):
    """lam = frac of all equity changing hands at the low (forced selleres -> buyer)."""
    lo, re = lo_re(c, r)
    transfer = EQ_MC * lam * (re - lo)
    fin = (re - 1) * 100
    return transfer, transfer / GDP * 100, fin


# ---------------- MODEL 2 : forced-seller -> sovereign capture ---------------
def model2(c, r, forced_sell):
    lo, re = lo_re(c, r)
    capture = EQ_MC * forced_sell * (re - lo)
    cryst   = EQ_MC * forced_sell * (lo - re)   # <0 = crystallized loss
    return capture, capture / GDP * 100, cryst


# ---------------- MODEL 3 : debt dynamics ------------------
def step_dg(dg, i, g, prim):
    return dg + (i - g) * (dg / 100.0) + prim


def years_to_80(i, g, prim, cap=300):
    d = DG0
    for y in range(1, cap + 1):
        d = step_dg(d, i, g, prim)
        if d <= DGT:
            return y
    return None


def main():
    print("=" * 70)
    print("MODEL 1 : equal crash+recovery = redistribution, not aggregate destruction")
    print("=" * 70)
    for c, r, lam in [(0.40, 0.667, 0.05), (0.40, 0.667, 0.15), (0.55, 0.40, 0.10), (0.30, 0.43, 0.20)]:
        tr, trg, fc = model1(c, r, lam)
        print(f"  crash {c:.0%} rec {r:.1%} lam {lam:.0%}: final mkt {fc:+.1f}%  transfer {tr:6,.0f}T ({trg:4.1f}% GDP)")
    print("  if (1-c)(1+r)=1 market value unchanged -> the 'crash loss' is mark-to-")
    print("  market; it physically moves from forced-seller accounts to bottom-fishers.")

    print()
    print("=" * 70)
    print("MODEL 2 : forced capitulation -> bottom-fishing (sovereign) capture")
    print("=" * 70)
    for fs, c, r in [(0.04, 0.40, 0.67), (0.08, 0.40, 0.67), (0.12, 0.50, 0.33), (0.15, 0.60, 0.25)]:
        cap, capg, cryst = model2(c, r, fs)
        print(f"  forced {fs:.0%} crash {c:.0%} rec {r:.2f}: sovereign capture {cap:7.0f}T ({capg:5.1f}% GDP) | seller crystallized loss {-cryst:6.0f}T")

    print()
    print("=" * 70)
    print("MODEL 3 : Debt/GDP 123% -> 80% via organic g_nominal>i channel")
    print("=" * 70)
    rows = [
        ("baseline (i4.3 g4.8 prim6)",        4.30, 4.80, 6.0),
        ("1946-like (g7.4 i4.2 prim-1.4)",    4.20, 7.40, -1.4),
        ("slow (i3.5 g6.5 prim3)",            3.50, 6.50, 3.0),
        ("slow+deficit-kept (i3.5 g6.5 p6)",  3.50, 6.50, 6.0),
    ]
    for name, i, g, v in rows:
        yt = years_to_80(i, g, v)
        print(f"  {name:<34}: years to 80% = {yt}")

    print()
    print("=" * 70)
    print("MODEL 3b : if sovereign-owned equity re-rating finances the 43pp payoff")
    print("=" * 70)
    cover_T = (DG0 - DGT) / 100.0 * GDP   # 12.9T of debt to restore value for
    print(f"  need ~{cover_T:.0f}T nominal value to close {(DG0-DGT):.0f}pp")
    for lam_own in [0.10, 0.20, 0.30]:
        R = cover_T / (lam_own * EQ_MC)
        y10 = y15 = None
        for y in range(1, 60):
            if (1 + 0.10) ** y >= (1 + R):
                y10 = y; break
        for y in range(1, 60):
            if (1 + 0.15) ** y >= (1 + R):
                y15 = y; break
        print(f"  sovereign owns {lam_own:.0%} of equity: market must rise +{R*100:.0f}%; "
              f"at 10%/yr ~ {y10} yr | at 15%/yr ~ {y15} yr")

    print()
    print("=" * 70)
    print("MODEL 2 BACK-SOLVER : how much forced capitulation to actually cover 43pp GDP")
    print("=" * 70)
    need_T = (DG0 - DGT) / 100.0 * GDP
    for c, r in [(0.40, 0.667), (0.40, 1.00), (0.50, 0.60)]:
        lo, re = lo_re(c, r)
        forced_needed = need_T / (EQ_MC * (re - lo))
        print(f"  crash {c:.0%} recovery-to-low-fade {(re-1)*100:+.0f}%: need forced_capitulation "
              f"= {forced_needed:.0%} of ALL equity (capture {need_T:.0f}T)")

    print()
    print("MECHANISM ONLY - not a recommendation. Forced-seller cohort requires a real")
    print("crisis/taper to trigger margin calls; sovereign capture obtains only through")
    print("legal/political channels existing memory flags as blocked (HYP-020/026/027).")


if __name__ == "__main__":
    main()