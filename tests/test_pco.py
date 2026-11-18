from datetime import date
from decimal import Decimal

from pco import attribution, commission, cosell, data as dat, dealreg, onboarding, qbr, scoring

AS_OF = date(2026, 9, 30)


def test_seed_deterministic():
    assert dat.generate(3) == dat.generate(3)
    assert dat.generate(3) != dat.generate(4)


def test_scores_bounded_and_tiers_consistent():
    for r in scoring.score_partners(dat.generate()):
        assert 0 <= r["score"] <= 100
        assert r["tier"] == scoring.tier_for(r["score"])


def test_tier_boundaries():
    assert scoring.tier_for(75) == "platinum"
    assert scoring.tier_for(74.9) == "gold"
    assert scoring.tier_for(0) == "registered"


def test_onboarding_states():
    p = {"id": "P", "name": "X", "joined": "2026-01-01"}
    allreq = {s["key"]: "2026-02-01" for s in dat.ONBOARDING_STEPS}
    assert onboarding.status(p, allreq, AS_OF)["state"] == "complete"
    assert onboarding.status(p, {}, AS_OF)["state"] == "stalled"
    recent = {"agreement": "2026-09-20"}
    s = onboarding.status(p, recent, AS_OF)
    assert s["state"] == "in_progress" and s["required_pct"] == 20.0


ACC = [{"domain": "a.example", "customer": False}, {"domain": "c.example", "customer": True}]


def reg(i, pid, dom, amt=10000, sub="2026-09-01", act=False):
    return {"id": i, "partner_id": pid, "domain": dom, "amount": amt, "submitted": sub, "activity_since_submit": act}


def run(regs, opps=(), tiers=None):
    return {d["id"]: d for d in dealreg.decide(regs, list(opps), ACC, tiers or {"P1": "gold", "P2": "gold", "P3": "registered"}, AS_OF)}


def test_conflict_first_registration_wins():
    d = run([reg("R1", "P1", "a.example"), reg("R2", "P2", "a.example", sub="2026-09-05")])
    assert d["R1"]["status"] == "auto_approved"
    assert d["R2"]["status"] == "rejected" and "conflicts" in d["R2"]["reason"]


def test_customer_and_existing_pipeline_rejected():
    assert run([reg("R1", "P1", "c.example")])["R1"]["status"] == "rejected"
    opp = {"domain": "a.example", "stage": "qualified", "source_partner": None, "created": "2026-08-01"}
    assert run([reg("R1", "P1", "a.example")], [opp])["R1"]["status"] == "rejected"


def test_approval_limits():
    assert run([reg("R1", "P1", "a.example", amt=200000)])["R1"]["status"] == "manual_review"
    assert run([reg("R1", "P3", "a.example")])["R1"]["status"] == "manual_review"


def test_expiry_and_extension():
    r = reg("R1", "P1", "a.example", sub="2026-06-01")
    assert dealreg.expiry(r) == date(2026, 8, 30)
    assert run([r])["R1"]["status"] == "expired"
    r2 = reg("R2", "P1", "a.example", sub="2026-06-01", act=True)
    assert dealreg.expiry(r2) == date(2026, 9, 29)
    r3 = reg("R3", "P1", "a.example", sub="2026-07-15")
    assert run([r3])["R3"]["status"] == "auto_approved"


def test_expired_does_not_block_new():
    d = run([reg("R1", "P1", "a.example", sub="2026-05-01"), reg("R2", "P2", "a.example", sub="2026-09-10")])
    assert d["R1"]["status"] == "expired" and d["R2"]["status"] == "auto_approved"


def test_cosell_counts_add_up():
    d = dat.generate()
    for r in cosell.overlap(d):
        assert r["shared"] == r["whitespace"] + r["open_opportunity"] + r["existing_customer"]
        assert r["shared"] <= r["partner_accounts"]


def tiny():
    return {"opportunities": [
        {"id": "O1", "stage": "closed_won", "amount": 100000, "source_partner": "P1",
         "touches": [{"partner_id": "P1", "touch": "intro"}, {"partner_id": "P2", "touch": "demo_assist"}]},
        {"id": "O2", "stage": "closed_won", "amount": 50000, "source_partner": None,
         "touches": [{"partner_id": "P2", "touch": "intro"}]},
        {"id": "O3", "stage": "closed_won", "amount": 50000, "source_partner": None, "touches": []},
        {"id": "O4", "stage": "qualified", "amount": 10000, "source_partner": "P1", "touches": []}]}


def test_attribution_no_double_count():
    r = attribution.report(tiny())
    assert r["P1"]["sourced_won"] == 100000 and r["P1"].get("influenced_won", 0) == 0
    assert r["P2"]["influenced_won"] == 150000
    t = attribution.totals(tiny())
    assert t["closed_won"] == 200000 and t["partner_sourced"] == 100000
    assert t["partner_influenced_only"] == 50000 and t["touched_pct"] == 75.0


def test_commission_rates_cap_and_clawback():
    assert commission.fee("sourced", "gold", 100000) == Decimal("10000.00")
    assert commission.fee("sourced", "platinum", 200000) == Decimal("15000.00")  # capped
    tiers = {"P1": "gold", "P2": "silver"}
    lines = commission.calculate(tiny(), tiers)
    assert commission.by_partner(lines) == {"P1": Decimal("10000.00"), "P2": Decimal("1500.00")}
    lines = commission.calculate(tiny(), tiers, churned={"O1": (date(2026, 1, 1), date(2026, 3, 1))})
    assert commission.by_partner(lines)["P1"] == Decimal("0.00")
    late = commission.calculate(tiny(), tiers, churned={"O1": (date(2026, 1, 1), date(2026, 8, 1))})
    assert commission.by_partner(late)["P1"] == Decimal("10000.00")


def test_qbr_markdown():
    d = dat.generate()
    md = qbr.build(d, "P01")
    assert md.startswith("# QBR:") and "Synthetic data" in md
    for h in ["## Scorecard", "## Pipeline", "## Co-sell", "## Onboarding", "## Fees", "## Actions"]:
        assert h in md
