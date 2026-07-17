def triple_track_v59(phase1_status: str, macro_quadrant: int) -> tuple:
    if phase1_status == "EMERGENCY":
        return (0.15, 0.55, 0.30)
    elif phase1_status == "WARNING":
        alloc = {1: (0.20, 0.50, 0.30), 2: (0.40, 0.35, 0.25), 3: (0.25, 0.25, 0.50), 4: (0.50, 0.20, 0.30)}
        return alloc.get(macro_quadrant, (0.35, 0.35, 0.30))
    else:
        alloc = {1: (0.30, 0.45, 0.25), 2: (0.75, 0.10, 0.15), 3: (0.30, 0.20, 0.50), 4: (0.65, 0.10, 0.25)}
        return alloc.get(macro_quadrant, (0.45, 0.30, 0.25))


def calc_v68b(phase1_status: str, mci: float, macro_quadrant: int) -> dict:
    if phase1_status == "EMERGENCY":
        return {"stock": 0.0, "fi": 0.70, "gld": 0.30, "xle": 0.0, "pdbc": 0.0}
    if phase1_status == "WARNING":
        eq_map = {1: 0.20, 2: 0.40, 3: 0.25, 4: 0.50}
        eq = min(eq_map.get(macro_quadrant, 0.40), 0.60)
        gld, xle, pdbc = 0.15, 0.09, 0.0
    else:
        eq = min(1.0, max(0.0, 0.50 + max(0, mci) * 0.025))
        gld, xle, pdbc = 0.05, 0.03, 0.0
    alt = gld + xle + pdbc
    if eq + alt > 0.97 and alt > 0:
        sc = (0.97 - eq) / alt
        gld *= sc
        xle *= sc
        pdbc *= sc
        alt = gld + xle + pdbc
    fi = max(0.0, 1.0 - eq - alt - 0.03)
    tot = eq + alt + fi
    return {k: round(v / tot, 4) for k, v in {"stock": eq, "fi": fi, "gld": gld, "xle": xle, "pdbc": pdbc}.items()}


PHASE_ALLOCATION = {
    1: {"name": "Rising", "eq": 0.70, "fi": 0.15, "ra": 0.15, "narrative": "Risk-on: overweight equities, underweight fixed income"},
    2: {"name": "Panic", "eq": 0.15, "fi": 0.55, "ra": 0.30, "narrative": "Capital preservation: SHV + GLD, exit equities"},
    3: {"name": "Fall", "eq": 0.30, "fi": 0.35, "ra": 0.35, "narrative": "Defensive: underweight equities, prefer TLT + commodities"},
    4: {"name": "Recover", "eq": 0.40, "fi": 0.35, "ra": 0.25, "narrative": "Cautious rebuild: moderate equities, watch VIX decline"},
    5: {"name": "Transition", "eq": 0.55, "fi": 0.25, "ra": 0.20, "narrative": "Mixed signals: balanced positioning, tighten bands"},
}


def target_allocation(phase: int) -> dict:
    base = dict(PHASE_ALLOCATION.get(phase, PHASE_ALLOCATION[5]))
    return {
        "phase": phase,
        "name": base["name"],
        "equity": base["eq"],
        "fixed_income": base["fi"],
        "real_assets": base["ra"],
        "narrative": base["narrative"],
    }
