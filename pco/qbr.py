"""QBR markdown generator."""
from datetime import date

from . import attribution, commission, cosell, onboarding, scoring


def money(x):
    return f"${x:,.0f}"


def build(data, pid):
    scores = {r["id"]: r for r in scoring.score_partners(data)}
    tiers = {k: v["tier"] for k, v in scores.items()}
    p = next(x for x in data["partners"] if x["id"] == pid)
    s = scores[pid]
    att = attribution.report(data).get(pid, {})
    ov = next(x for x in cosell.overlap(data) if x["partner_id"] == pid)
    ob = next(x for x in onboarding.tracker(data) if x["id"] == pid)
    fees = commission.by_partner(commission.calculate(data, tiers)).get(pid, 0)
    rank = [r["id"] for r in scoring.score_partners(data)].index(pid) + 1
    g = att.get
    L = [f"# QBR: {p['name']} ({p['id']})", "",
         f"_As of {data['as_of']}. Synthetic data._", "",
         "## Scorecard", "",
         "| Metric | Value |", "|---|---|",
         f"| Tier | {s['tier']} |", f"| Overall score | {s['score']} (rank {rank} of {len(scores)}) |",
         f"| Fit / Pipeline / Activity | {s['fit']} / {s['pipeline']} / {s['activity']} |", "",
         "## Pipeline", "",
         "| | Won | Open |", "|---|---|---|",
         f"| Sourced | {money(g('sourced_won', 0))} | {money(g('sourced_open', 0))} |",
         f"| Influenced | {money(g('influenced_won', 0))} | {money(g('influenced_open', 0))} |", "",
         "## Co-sell", "",
         f"{ov['shared']} of {ov['partner_accounts']} partner accounts are in our account list "
         f"({ov['overlap_pct']}%): {ov['whitespace']} whitespace, {ov['open_opportunity']} with open opportunities, "
         f"{ov['existing_customer']} existing customers.", "",
         "## Onboarding", "",
         f"Required steps {ob['required_pct']}% complete ({ob['state']})."]
    if ob["missing_required"]:
        L.append("Outstanding: " + "; ".join(ob["missing_required"]) + ".")
    L += ["", "## Fees", "", f"Fees accrued on closed-won deals: {money(fees)}.", "", "## Actions", ""]
    acts = []
    if ov["whitespace"]:
        acts.append(f"Pick the top whitespace accounts ({ov['whitespace']} available) for a joint account plan.")
    if ob["missing_required"]:
        acts.append("Close out required onboarding steps before the next registration.")
    if s["activity"] < 30:
        acts.append("Activity is low; schedule a joint call and one enablement session.")
    if not acts:
        acts.append("Maintain cadence; review tier eligibility next quarter.")
    L += [f"- {a}" for a in acts]
    return "\n".join(L) + "\n"
