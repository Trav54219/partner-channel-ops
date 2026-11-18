"""Onboarding checklist tracker."""
from datetime import date

from .data import ONBOARDING_STEPS

STALL_DAYS = 45


def status(partner, done, as_of, steps=ONBOARDING_STEPS):
    req = [s for s in steps if s["required"]]
    req_done = [s for s in req if s["key"] in done]
    pct = round(100 * len(req_done) / len(req), 1)
    missing = [s["label"] for s in req if s["key"] not in done]
    joined = date.fromisoformat(partner["joined"])
    last = max([date.fromisoformat(v) for v in done.values()], default=joined)
    idle = (as_of - last).days
    if not missing:
        state = "complete"
    elif idle > STALL_DAYS:
        state = "stalled"
    else:
        state = "in_progress"
    return {"id": partner["id"], "name": partner["name"], "required_pct": pct,
            "state": state, "missing_required": missing, "days_since_progress": idle}


def tracker(data):
    as_of = date.fromisoformat(data["as_of"])
    return [status(p, data["onboarding"].get(p["id"], {}), as_of) for p in data["partners"]]
