"""Co-sell account mapping: overlap between our accounts and partner customers."""
from collections import defaultdict


def overlap(data):
    ours = {a["domain"]: a for a in data["accounts"]}
    open_dom = {o["domain"] for o in data["opportunities"] if o["stage"] not in ("closed_won", "closed_lost")}
    by_p = defaultdict(set)
    for pa in data["partner_accounts"]:
        by_p[pa["partner_id"]].add(pa["domain"])
    res = []
    for p in data["partners"]:
        doms = by_p[p["id"]]
        shared = sorted(d for d in doms if d in ours)
        rows = []
        for d in shared:
            a = ours[d]
            kind = "existing_customer" if a["customer"] else ("open_opportunity" if d in open_dom else "whitespace")
            rows.append({"domain": d, "account": a["name"], "kind": kind})
        res.append({"partner_id": p["id"], "partner": p["name"], "partner_accounts": len(doms),
                    "shared": len(shared), "overlap_pct": round(100 * len(shared) / len(doms), 1) if doms else 0.0,
                    "whitespace": sum(1 for r in rows if r["kind"] == "whitespace"),
                    "open_opportunity": sum(1 for r in rows if r["kind"] == "open_opportunity"),
                    "existing_customer": sum(1 for r in rows if r["kind"] == "existing_customer"),
                    "accounts": rows})
    return sorted(res, key=lambda x: (-x["whitespace"], x["partner_id"]))


def multi_partner_accounts(data):
    """Accounts claimed by 2+ partners: route carefully."""
    c = defaultdict(set)
    for pa in data["partner_accounts"]:
        c[pa["domain"]].add(pa["partner_id"])
    return {d: sorted(v) for d, v in c.items() if len(v) > 1 and d.startswith("acct")}
