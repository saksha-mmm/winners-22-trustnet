# TrustNet — Decentralized Trust Network for Open Source Contributions

**Hacktoberfest 2026 · Hack Day Sonipat · Problem 07 · Team winner's 22**

TrustNet lets open-source projects share trust signals **without a central
authority**: each project publishes who it vouches for, who it denounces, and
which other projects it trusts. From that, the network detects coordinated
spam campaigns that are invisible to any single maintainer — and it does it
without unfairly blocking honest newcomers.

## Why this matters

AI-assisted tooling has made it easy to mass-produce low-quality PRs. A
coordinated campaign (like the Hacktoberfest 2020 spam wave) may hit dozens of
repositories at once; a maintainer watching one repo sees nothing. TrustNet
finds the pattern **across** projects, exactly as the brief describes:
*vouched by Project B, which you trust → let in; X's denounce is ignored, you
don't trust X; 38 near-identical PRs from 3-day-old accounts hit 40 projects
in 2 hours → flagged, with the evidence.*

## Quickstart

```bash
pip install -e ".[dev]"

# 1. Generate the demo simulation (the official evaluation scenario)
trustnet demo --out examples/sim_30_projects.json

# 2. Run the full evaluation: per-PR verdicts + campaign detection
trustnet run examples/sim_30_projects.json \
  --json examples/output_report.json \
  --report examples/output_report.md

# Optional: add a plain-English summary from a local open-weight model (Ollama)
trustnet run examples/sim_30_projects.json --llm

# Inspect one PR
trustnet evaluate examples/sim_30_projects.json pr-001
```

No API keys, no external services, no network required. Everything is
deterministic and reproducible.

## How trust works

1. **Trust graph.** Each project trusts itself (1.0) and declares weighted
   trust in other projects, e.g. `"trusts": {"project-b": 0.8}`.
2. **Propagation with damping.** Trust flows along edges; every hop beyond the
   first is multiplied by a damping factor (0.5) so distant opinions never
   outweigh direct ones. Between two projects we keep the **best path**:
   `trust_A(C) = max over paths of product(weights) × 0.5^(hops−1)`.
3. **Reputation aggregation.** From project A's point of view, contributor c's
   score is `Σ trust_A(Q) × rep_Q(c)` over all reachable projects Q, where a
   vouch is +1 and a denounce is −1. Unknown contributors score 0.
4. **Verdict.** `score ≥ +0.5 → allow (trusted)`; `score ≤ −0.5 → flag
   (distrusted)`; anything else → **allow with a neutral note** — this is the
   newcomer-fairness guarantee: no reputation data is never a reason to block.

## How campaign detection works

PRs inside a rolling 24-hour window are clustered by body similarity
(3-gram Jaccard ≥ 0.6). A cluster is a *coordinated campaign* when it is large
(≥ 5 PRs), spans ≥ 2 projects, and is either driven entirely by accounts
≤ 3 days old or hits ≥ 5 projects within 6 hours. Every flag ships with
quantified evidence (PR ids, accounts, ages, time span). A single original PR
from a brand-new account is never flagged.

## Evaluation reproduction

The simulation in `examples/sim_30_projects.json` reproduces the official
evaluation scenario: 30 projects with existing vouch/denouncement lists,
74 incoming PRs, a coordinated campaign (12 bots · 60 near-identical PRs ·
20 projects · ~2 hours), and 4 legitimate newcomers. `pytest` asserts the
rubric end-to-end:

- every campaign PR is flagged,
- every newcomer PR is allowed,
- every flag carries evidence,
- runs are deterministic.

## AI model usage

The engine is fully deterministic. An optional open-weight model
(`qwen2.5:3b` via Ollama by default; override with `TRUSTNET_LLM_BASE_URL` /
`TRUSTNET_LLM_MODEL`) rephrases results into a plain-English summary. When no
endpoint is reachable the report falls back to rule-based text, so correctness
never depends on the model. No closed-model APIs are used.

## Repository structure

```
trustnet/          core package (models, trust, campaign, evaluate, report, cli)
tests/             unit + end-to-end rubric tests
examples/          simulation input + actual outputs produced by this project
.github/           PR template + CI workflow
```

MIT licensed. Every change ships via PR with CI (GitHub Actions runs the full
test suite on every PR).
