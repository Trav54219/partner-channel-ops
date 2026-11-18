"""Deal registration engine: conflicts, approval rules, expiry."""
from datetime import date, timedelta

from .scoring import TIER_RANK

REG_DAYS = 90
EXTENSION_DAYS = 30
AUTO_LIMIT = {"registered": 0, "silver": 25000, "gold": 75000, "platinum": 150000}


def expiry(reg, as_of=None):
    """Registration expires 90 days after submit; one 30-day extension if partner logged activity."""
    sub = date.fromisoformat(reg["submitted"])
    days = REG_DAYS + (EXTENSION_DAYS if reg.get("activity_since_submit") else 0)
    return sub + timedelta(days=days)


def decide(regs, opps, accounts, tiers, as_of):
    """Process registrations oldest-first. Returns list of decisions.

    Rules, in order:
      1. expired registration -> expired (does not block others)
      2. account is an existing customer -> rejected
      3. our own opportunity on the domain created before submit -> rejected (existing pipeline)
      4. an earlier live approved/pending registration by another partner -> conflict, rejected
      5. clean and amount <= tier auto limit -> auto_approved
      6. otherwise -> manual_review
    """
    customers = {a["domain"] for a in accounts if a["customer"]}
    open_opps = [o for o in opps if o["stage"] not in ("closed_lost",)]
    live = {}  # domain -> reg that holds the claim
    out = []
    for r in sorted(regs, key=lambda x: (x["submitted"], x["id"])):
        sub = date.fromisoformat(r["submitted"])
        exp = expiry(r)
        d = {"id": r["id"], "partner_id": r["partner_id"], "domain": r["domain"],
             "expires": exp.isoformat()}
        if exp < as_of:
            d.update(status="expired", reason=f"expired {exp.isoformat()}")
        elif r["domain"] in customers:
            d.update(status="rejected", reason="account is an existing customer")
        elif any(o["domain"] == r["domain"] and not o["source_partner"]
                 and date.fromisoformat(o["created"]) < sub for o in open_opps):
            d.update(status="rejected", reason="existing direct pipeline predates registration")
        elif r["domain"] in live and live[r["domain"]] != r["partner_id"]:
            d.update(status="rejected", reason=f"conflicts with earlier registration by {live[r['domain']]}")
        else:
            tier = tiers.get(r["partner_id"], "registered")
            if r["amount"] <= AUTO_LIMIT[tier] and TIER_RANK[tier] >= 1:
                d.update(status="auto_approved", reason=f"clean, within {tier} limit")
            else:
                d.update(status="manual_review", reason=f"amount or tier ({tier}) needs review")
            live.setdefault(r["domain"], r["partner_id"])
        out.append(d)
    return out
