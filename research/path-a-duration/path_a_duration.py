"""Path A 慢剧本: 需要多久解决债务？美国社会能忍受多久？"""
import numpy as np

def run(G, I, PD, years=40, D0=1.25):
    """Δ(D/G) = (I - G)*D/G + primary_deficit ; 返回 D/G 逐年序列."""
    D = D0
    series = [D]
    for _ in range(years):
        D = D + (I - G) * D + PD
        series.append(D)
    return series

def years_to_target(series, target):
    for y, d in enumerate(series):
        if d <= target:
            return y
    return None

targets = {"到100%": 1.00, "到60%": 0.60}

print("="*68)
print("情景A1: 1946-74 同机制 (g=7%, i=4.72%, primary surplus 0.44%)")
s = run(0.07, 0.0472, -0.0044, years=30)
print(f"  30年终端 D/G = {s[-1]*100:.1f}%")
for t,tv in targets.items():
    yy = years_to_target(s, tv); print(f"  {t}: {('{:.0f}年'.format(yy) if yy else '>30年')}")

print("\n情景B: 2026基线 (g=4.5%, i=4.5%, primary deficit 6.84%)")
s = run(0.045, 0.045, +0.0684, years=10)
print(f"  10年后 D/G = {s[-1]*100:.1f}%  (仍恶化) | 15年后 = {run(0.045,0.045,+0.0684,15)[-1]*100:.1f}%")

print("\n情景C: 慢速抑制起点 (g=3.5%, i=2.5%, PD deficit 6.8%)")
s = run(0.035, 0.025, +0.068, years=10)
print(f"  10年后 D/G = {s[-1]*100:.1f}%" )

print("\n情景D: 增长消化+财政纪律 (g=7%, i=4%, PD surplus 1%)")
s = run(0.07, 0.04, -0.01, years=30)
for t,tv in targets.items():
    yy = years_to_target(s, tv); print(f"  {t}: {('{:.0f}年'.format(yy) if yy else '>30年')} (30年后 {s[-1]*100:.0f}%)")

print("\n情景E: 大通胀快剧本 (g_nom=9%, i=5%, PD deficit 4%)")
s = run(0.09, 0.05, +0.04, years=12)
for t,tv in targets.items():
    yy = years_to_target(s, tv); print(f"  {t}: {('{:.0f}年'.format(yy) if yy else '>12年')} (12年后 {s[-1]*100:.0f}%)")