"""Partner-sourced vs influenced attribution. Closed-won only counts as revenue; open is pipeline."""
from collections import defaultdict


def report(data):
    rows = defaultdict(lambda: {"sourced_won": 0, "sourced_open": 0, "influenced_won": 0,
                                "influenced_open": 0, "deals_sourced": 0, "deals_influenced": 0})
    for o in data["opportunities"]:
        if o["stage"] == "closed_lost":
            continue
        bucket = "won" if o["stage"] == "closed_won" else "open"
        if o["source_partner"]:
            r = rows[o["source_partner"]]
            r[f"sourced_{bucket}"] += o["amount"]
            r["deals_sourced"] += 1
        seen = set()
        for t in o["touches"]:
            pid = t["partner_id"]
            if pid == o["source_partner"] or pid in seen:
                continue  # a partner is never both sourced and influenced on the same deal
            seen.add(pid)
            r = rows[pid]
            r[f"influenced_{bucket}"] += o["amount"]
            r["deals_influenced"] += 1
    return dict(rows)


def totals(data):
    won = [o for o in data["opportunities"] if o["stage"] == "closed_won"]
    total = sum(o["amount"] for o in won)
    sourced = sum(o["amount"] for o in won if o["source_partner"])
    influenced = sum(o["amount"] for o in won if not o["source_partner"] and o["touches"])
    return {"closed_won": total, "partner_sourced": sourced, "partner_influenced_only": influenced,
            "sourced_pct": round(100 * sourced / total, 1) if total else 0.0,
            "touched_pct": round(100 * (sourced + influenced) / total, 1) if total else 0.0}
