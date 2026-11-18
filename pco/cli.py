import argparse
import json

from . import attribution, commission, cosell, data as dat, dealreg, onboarding, qbr, scoring
from datetime import date


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pco")
    ap.add_argument("cmd", choices=["score", "onboarding", "dealreg", "cosell", "attribution", "fees", "qbr"])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--partner", default="P01")
    a = ap.parse_args(argv)
    d = dat.generate(a.seed)
    sc = scoring.score_partners(d)
    tiers = {r["id"]: r["tier"] for r in sc}
    if a.cmd == "score":
        for r in sc:
            print(f"{r['id']} {r['name']:<16} {r['tier']:<10} {r['score']:>5}  fit {r['fit']} pipe {r['pipeline']} act {r['activity']}")
    elif a.cmd == "onboarding":
        for r in onboarding.tracker(d):
            print(f"{r['id']} {r['state']:<12} {r['required_pct']:>5}%  {', '.join(r['missing_required'])}")
    elif a.cmd == "dealreg":
        for r in dealreg.decide(d["registrations"], d["opportunities"], d["accounts"], tiers, date.fromisoformat(d["as_of"])):
            print(f"{r['id']} {r['partner_id']} {r['status']:<14} {r['reason']}")
    elif a.cmd == "cosell":
        for r in cosell.overlap(d):
            print(f"{r['partner_id']} shared {r['shared']:>3}/{r['partner_accounts']:<3} whitespace {r['whitespace']}")
    elif a.cmd == "attribution":
        print(json.dumps({"totals": attribution.totals(d), "by_partner": attribution.report(d)}, indent=2))
    elif a.cmd == "fees":
        for k, v in sorted(commission.by_partner(commission.calculate(d, tiers)).items()):
            print(k, v)
    elif a.cmd == "qbr":
        print(qbr.build(d, a.partner))


if __name__ == "__main__":
    main()
