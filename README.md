# partner-channel-ops

A small Python toolkit showing how a partnerships / channel / alliances function can be run with explicit, testable rules.

**All data is synthetic**, generated from a seeded random generator (`pco/data.py`). Nothing here is connected to any PRM, co-sell or account-mapping tool (Impartner, PartnerStack, Crossbeam, or others), and no real company, person or result appears anywhere. Rates, thresholds and weights are illustrative assumptions, not benchmarks.

## What is in it

| Module | What it does |
|---|---|
| `scoring.py` | Partner score = 30% fit (ICP overlap, certified reps) + 50% pipeline (sourced + 0.4 x influenced, normalized) + 20% activity (90-day touches). Maps to platinum / gold / silver / registered. |
| `onboarding.py` | Checklist tracker: required-step completion, missing items, stalled after 45 days idle. |
| `dealreg.py` | Deal registration: customer and existing-pipeline conflicts, first-registration-wins between partners, tier-based auto-approval limits, 90-day expiry with one 30-day extension if the partner logged activity. |
| `cosell.py` | Overlap of our accounts with partner accounts, split into whitespace / open opportunity / existing customer. |
| `attribution.py` | Sourced vs influenced, won vs open. A partner is never counted as both on one deal. |
| `commission.py` | Referral fees by tier and type with per-deal cap and 90-day churn clawback, using `Decimal`. |
| `qbr.py` | Per-partner markdown QBR combining all of the above. |

## Run

```
python -m pco score
python -m pco dealreg
python -m pco qbr --partner P03
python -m pytest
```

Standard library only (pytest for tests). Pass `--seed N` to regenerate a different synthetic world.
