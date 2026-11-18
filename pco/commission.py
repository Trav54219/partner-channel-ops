"""Referral fee / commission calculator. Uses Decimal; rates are illustrative assumptions."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

RATES = {  # (tier) -> {kind: rate}
    "registered": {"sourced": Decimal("0.05"), "influenced": Decimal("0")},
    "silver": {"sourced": Decimal("0.08"), "influenced": Decimal("0.01")},
    "gold": {"sourced": Decimal("0.10"), "influenced": Decimal("0.02")},
    "platinum": {"sourced": Decimal("0.12"), "influenced": Decimal("0.03")},
}
CAP_PER_DEAL = Decimal("15000")
CLAWBACK_DAYS = 90


def q(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fee(kind, tier, amount, cap=CAP_PER_DEAL):
    rate = RATES[tier][kind]
    return q(min(Decimal(amount) * rate, cap))


def calculate(data, tiers, churned=None, as_of=None):
    """Fees on closed-won deals. `churned` maps opp_id -> (won_date, churn_date); churn inside
    CLAWBACK_DAYS of win voids the fee."""
    churned = churned or {}
    lines = []
    for o in data["opportunities"]:
        if o["stage"] != "closed_won":
            continue
        parties = []
        if o["source_partner"]:
            parties.append((o["source_partner"], "sourced"))
        for t in o["touches"]:
            if t["partner_id"] != o["source_partner"] and (t["partner_id"], "influenced") not in parties:
                parties.append((t["partner_id"], "influenced"))
        for pid, kind in parties:
            f = fee(kind, tiers[pid], o["amount"])
            voided = False
            if o["id"] in churned:
                won, ch = churned[o["id"]]
                voided = (ch - won).days <= CLAWBACK_DAYS
            lines.append({"opp": o["id"], "partner_id": pid, "kind": kind, "amount": o["amount"],
                          "fee": Decimal("0.00") if voided else f, "clawback": voided})
    return lines


def by_partner(lines):
    out = {}
    for l in lines:
        out[l["partner_id"]] = out.get(l["partner_id"], Decimal("0.00")) + l["fee"]
    return {k: q(v) for k, v in out.items()}
