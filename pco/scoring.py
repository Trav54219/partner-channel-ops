"""Partner scoring and tiering: fit, pipeline, activity."""
from datetime import date, timedelta

WEIGHTS = {"fit": 0.30, "pipeline": 0.50, "activity": 0.20}
TIERS = [(75, "platinum"), (55, "gold"), (35, "silver"), (0, "registered")]
TIER_RANK = {"registered": 0, "silver": 1, "gold": 2, "platinum": 3}


def fit_score(p):
    return round(min(100, p["icp_overlap"] * 70 + min(p["certified_reps"], 6) * 5), 1)


def pipeline_values(data):
    """Return {pid: (sourced_won_plus_open, influenced)} weighting open at stage-agnostic face value."""
    out = {p["id"]: [0.0, 0.0] for p in data["partners"]}
    for o in data["opportunities"]:
        if o["stage"] == "closed_lost":
            continue
        if o["source_partner"]:
            out[o["source_partner"]][0] += o["amount"]
        for t in o["touches"]:
            out[t["partner_id"]][1] += o["amount"]
    return out


def activity_score(pid, data, window=90):
    cutoff = date.fromisoformat(data["as_of"]) - timedelta(days=window)
    n = sum(1 for a in data["activities"]
            if a["partner_id"] == pid and date.fromisoformat(a["date"]) >= cutoff)
    return round(min(100, n * 10), 1)


def tier_for(score):
    for floor, name in TIERS:
        if score >= floor:
            return name


def score_partners(data):
    pv = pipeline_values(data)
    raw = {pid: s + 0.4 * i for pid, (s, i) in pv.items()}
    top = max(raw.values()) or 1.0
    rows = []
    for p in data["partners"]:
        f = fit_score(p)
        pl = round(raw[p["id"]] / top * 100, 1)
        ac = activity_score(p["id"], data)
        total = round(f * WEIGHTS["fit"] + pl * WEIGHTS["pipeline"] + ac * WEIGHTS["activity"], 1)
        rows.append({"id": p["id"], "name": p["name"], "fit": f, "pipeline": pl,
                     "activity": ac, "score": total, "tier": tier_for(total),
                     "sourced": pv[p["id"]][0], "influenced": pv[p["id"]][1]})
    return sorted(rows, key=lambda r: (-r["score"], r["id"]))
