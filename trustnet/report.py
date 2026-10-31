"""Human-readable reports. Optionally uses a local open-weight LLM (Ollama)
to rephrase the structured results; falls back to rule-based text when no
model endpoint is reachable. Decisions themselves are always deterministic."""
from __future__ import annotations

import json
import os
import urllib.request


def build_markdown(result: dict, sim_source: str | None = None) -> str:
    s = result["summary"]
    lines = [
        "# Trust Network — Evaluation Report",
        "",
        f"**Simulation:** `{sim_source or 'n/a'}`",
        "",
        f"- Projects: **{s['projects']}**",
        f"- Contributors: **{s['contributors']}**",
        f"- Incoming PRs: **{s['prs']}**",
        f"- Allowed: **{s['allowed']}**",
        f"- Flagged: **{s['flagged']}**",
        f"- Coordinated campaigns detected: **{s['campaigns']}**",
        "",
        "## Detected campaigns",
        "",
    ]
    if not result["campaigns"]:
        lines.append("None.")
    for i, c in enumerate(result["campaigns"], 1):
        lines.append(f"### Campaign {i}")
        lines.append(f"- **Evidence:** {c['evidence']}")
        lines.append(
            f"- Accounts: {', '.join(c['contributors'])} "
            f"(all young: {c['all_accounts_young']})"
        )
        lines.append(f"- PRs flagged: {', '.join(c['pr_ids'])}")
        lines.append("")
    lines += ["## Per-PR verdicts", "", "| PR | Contributor | Project | Decision | Score | Reasons |", "|---|---|---|---|---|---|"]
    for v in result["verdicts"]:
        reasons = "; ".join(v["reasons"]).replace("|", "/")
        lines.append(
            f"| {v['pr']} | {v['contributor']} | {v['project']} | "
            f"**{v['decision']}** | {v['score']} | {reasons} |"
        )
    return "\n".join(lines) + "\n"


def llm_summary(
    facts: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float = 15.0,
) -> str | None:
    """Ask a local open-weight model to summarize results in plain English.

    Returns None if no endpoint is reachable (callers fall back to rules).
    """
    model = model or os.environ.get("TRUSTNET_LLM_MODEL", "qwen2.5:3b")
    base_url = base_url or os.environ.get("TRUSTNET_LLM_BASE_URL", "http://localhost:11434")
    prompt = (
        "You are a trust-network analyst for open-source maintainers. "
        "Summarize these evaluation results in 3-5 short bullet points, in plain English. "
        "Keep every number accurate. Do not add claims that are not in the data.\n\n"
        + facts
    )
    payload = json.dumps(
        {"model": model, "prompt": prompt, "stream": False}
    ).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read()).get("response")


def rule_based_summary(result: dict) -> str:
    s = result["summary"]
    bullets = [
        f"- {s['flagged']} of {s['prs']} incoming PRs were flagged.",
        f"- {s['campaigns']} coordinated spam campaign(s) detected.",
    ]
    if s["campaigns"]:
        bullets.append(
            f"- Largest signal: {result['campaigns'][0]['evidence']}."
        )
    bullets.append(
        f"- {s['allowed']} PRs were allowed, including newcomers with no reputation data."
    )
    return "\n".join(bullets)
