"""Seeded synthetic data generator. Same seed -> identical output."""
import random
from datetime import date, timedelta

AS_OF = date(2026, 9, 30)
TYPES = ["referral", "reseller", "integrator", "technology"]
ADJ = ["North", "Blue", "Iron", "Bright", "Summit", "Harbor", "Cedar", "Atlas", "Vector", "Pine"]
NOUN = ["works", "labs", "group", "logic", "partners", "systems", "forge", "stack", "path", "grid"]
STAGES = ["prospecting", "qualified", "proposal", "closed_won", "closed_lost"]
TOUCHES = ["intro", "co_sell_call", "demo_assist", "technical_validation", "exec_sponsor"]
ACTS = ["webinar", "joint_call", "training", "lead_share", "event"]


def generate(seed=7, n_partners=12, n_accounts=120):
    r = random.Random(seed)
    names = set()
    while len(names) < n_partners:
        names.add(f"{r.choice(ADJ)}{r.choice(NOUN)}")
    partners = []
    for i, n in enumerate(sorted(names)):
        partners.append({
            "id": f"P{i+1:02d}", "name": n.capitalize(), "type": r.choice(TYPES),
            "icp_overlap": round(r.uniform(0.1, 1.0), 2),
            "certified_reps": r.randint(0, 8),
            "joined": (AS_OF - timedelta(days=r.randint(30, 900))).isoformat(),
        })
    accounts = [{"id": f"A{i+1:03d}", "name": f"{r.choice(ADJ)} {r.choice(NOUN)} {i+1}",
                 "domain": f"acct{i+1:03d}.example", "customer": r.random() < 0.15}
                for i in range(n_accounts)]
    partner_accounts = []
    for p in partners:
        k = int(10 + p["icp_overlap"] * 30)
        for a in r.sample(accounts, k):
            partner_accounts.append({"partner_id": p["id"], "domain": a["domain"]})
        for j in range(r.randint(2, 6)):  # accounts we do not have
            partner_accounts.append({"partner_id": p["id"], "domain": f"ext{p['id'].lower()}{j}.example"})
    opps = []
    for i in range(70):
        a = r.choice(accounts)
        src = r.choice(partners)["id"] if r.random() < 0.4 else None
        infl = [{"partner_id": q["id"], "touch": r.choice(TOUCHES)}
                for q in r.sample(partners, r.randint(0, 3)) if q["id"] != src]
        stage = r.choices(STAGES, [2, 3, 2, 3, 2])[0]
        created = AS_OF - timedelta(days=r.randint(5, 300))
        opps.append({"id": f"O{i+1:03d}", "account_id": a["id"], "domain": a["domain"],
                     "amount": r.choice([12000, 24000, 36000, 60000, 90000, 150000]),
                     "stage": stage, "created": created.isoformat(),
                     "source_partner": src, "touches": infl})
    activities = [{"partner_id": r.choice(partners)["id"], "type": r.choice(ACTS),
                   "date": (AS_OF - timedelta(days=r.randint(0, 200))).isoformat()}
                  for _ in range(220)]
    regs = []
    for i in range(30):
        a = r.choice(accounts)
        regs.append({"id": f"R{i+1:03d}", "partner_id": r.choice(partners)["id"],
                     "domain": a["domain"], "amount": r.choice([10000, 25000, 60000, 120000, 200000]),
                     "submitted": (AS_OF - timedelta(days=r.randint(0, 150))).isoformat(),
                     "activity_since_submit": r.random() < 0.5})
    steps = ONBOARDING_STEPS
    onboarding = {}
    for p in partners:
        start = date.fromisoformat(p["joined"])
        done = {}
        n = r.randint(0, len(steps))
        for s in steps[:n]:
            done[s["key"]] = (start + timedelta(days=r.randint(1, 60))).isoformat()
        onboarding[p["id"]] = done
    return {"as_of": AS_OF.isoformat(), "partners": partners, "accounts": accounts,
            "partner_accounts": partner_accounts, "opportunities": opps,
            "activities": activities, "registrations": regs, "onboarding": onboarding}


ONBOARDING_STEPS = [
    {"key": "agreement", "label": "Partner agreement signed", "required": True},
    {"key": "portal", "label": "Portal access provisioned", "required": True},
    {"key": "sales_training", "label": "Sales training completed", "required": True},
    {"key": "tech_cert", "label": "Technical certification", "required": False},
    {"key": "deal_reg_training", "label": "Deal registration walkthrough", "required": True},
    {"key": "joint_plan", "label": "Joint business plan agreed", "required": True},
    {"key": "first_deal", "label": "First registered deal", "required": False},
]
