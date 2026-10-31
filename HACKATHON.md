# HACKATHON

## Team
- **Team name:** winner's 22

## Members
- Saksham

## Problem statement
**Problem 07: Decentralized Trust Network for Open Source Contributions**

AI-powered tools have made it easy to mass-produce low-quality or spam pull requests,
and coordinated campaigns target many projects at once. A pattern visible across
hundreds of repositories stays invisible to a single maintainer. We are building a
decentralized trust network where projects publicly share vouch/denouncement records,
exchange trust information without any central authority, detect coordinated spam
campaigns across projects, and still evaluate honest newcomers fairly.

## AI models used
- **qwen2.5:3b via Ollama (default) or any OpenAI-compatible local/server endpoint
  via `TRUSTNET_LLM_BASE_URL`** — used to turn the engine's structured verdicts into a
  plain-English summary in the markdown report.
  Why: open-weight and runs locally or on the event's model server; it only *explains*
  results — every allow/flag decision is produced by the deterministic trust engine, so
  correctness never depends on the model, and the tool falls back to rule-based text
  when no model endpoint is reachable.
- (No closed-model APIs are used anywhere in this project.)

## Why we picked this problem
The evaluation scenario — a simulated network of 20–50 projects with vouch lists,
denouncement lists, incoming PRs, a coordinated spam campaign, and legitimate newcomers
— can be reproduced exactly, so we can measure our own precision/recall before judging.
The solution is fully local and deterministic (no API keys, no external services), it
addresses the real Hacktoberfest-2020-style spam problem described in the brief, and
its trade-offs (trust propagation, damping, newcomer fairness) make for a strong
design discussion.
