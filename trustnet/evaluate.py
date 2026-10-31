"""Per-PR evaluation: allow / flag with evidence, plus the full pipeline."""
from __future__ import annotations

from .campaign import detect_campaigns
from .models import PR, Simulation
from .trust import contributor_score

ALLOW_THRESHOLD = 0.5   # aggregate score >= this  -> explicit trust
FLAG_THRESHOLD = -0.5   # aggregate score <= this  -> explicit distrust


def evaluate_pr(pr: PR, sim: Simulation, campaign_map: dict[str, str]) -> dict:
    score, evidence = contributor_score(
        pr.contributor, pr.project, sim.projects, sim.contributors
    )
    project_name = sim.projects[pr.project].name

    if pr.id in campaign_map:
        return {
            "pr": pr.id,
            "contributor": pr.contributor,
            "project": project_name,
            "decision": "flag",
            "score": round(score, 3),
            "reasons": [f"campaign: {campaign_map[pr.id]}"] + evidence,
        }

    if score <= FLAG_THRESHOLD:
        return {
            "pr": pr.id,
            "contributor": pr.contributor,
            "project": project_name,
            "decision": "flag",
            "score": round(score, 3),
            "reasons": evidence
            + [f"aggregate score {score:.2f} <= {FLAG_THRESHOLD}"],
        }

    note = []
    if not evidence:
        note = [
            "no reputation data — neutral trust; allowed by default (newcomer fairness)"
        ]
    return {
        "pr": pr.id,
        "contributor": pr.contributor,
        "project": project_name,
        "decision": "allow",
        "score": round(score, 3),
        "reasons": evidence + note,
    }


def run_pipeline(sim: Simulation) -> dict:
    """Evaluate every PR and detect coordinated campaigns."""
    campaigns = detect_campaigns(sim)
    campaign_map = {pid: c["evidence"] for c in campaigns for pid in c["pr_ids"]}
    verdicts = [evaluate_pr(p, sim, campaign_map) for p in sim.prs]

    allowed = [v for v in verdicts if v["decision"] == "allow"]
    flagged = [v for v in verdicts if v["decision"] == "flag"]
    campaign_prs = sorted(campaign_map)
    summary = {
        "projects": len(sim.projects),
        "contributors": len(sim.contributors),
        "prs": len(verdicts),
        "allowed": len(allowed),
        "flagged": len(flagged),
        "campaigns": len(campaigns),
        "campaign_prs": campaign_prs,
    }
    return {"summary": summary, "campaigns": campaigns, "verdicts": verdicts}
