"""Coordinated spam campaign detection.

Detection is deliberately simple and explainable: pull requests inside a
rolling time window are clustered by body similarity (3-gram Jaccard). A
cluster is flagged as a coordinated campaign when it is large enough, spans
enough projects, and is either driven by very young accounts or hits many
projects in a short burst. A single original PR from a brand-new account is
never flagged on its own — that is the newcomer-fairness guarantee.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from .models import PR, Simulation


def _parse(dt: str) -> datetime:
    return datetime.fromisoformat(dt.replace("Z", "+00:00"))


def _tokens(text: str) -> set[tuple[str, ...]]:
    words = "".join(c.lower() if c.isalnum() else " " for c in text).split()
    return {tuple(words[i : i + 3]) for i in range(len(words) - 2)}


def similarity(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def detect_campaigns(
    sim: Simulation,
    *,
    window_hours: float = 24.0,
    sim_threshold: float = 0.6,
    min_cluster: int = 5,
    min_projects: int = 2,
    young_max_age_days: float = 3.0,
    burst_hours: float = 6.0,
    burst_min_projects: int = 5,
) -> list[dict]:
    """Return a list of detected campaigns, each with evidence."""
    prs = sorted(sim.prs, key=lambda p: p.created_at)
    latest = max(_parse(p.created_at) for p in prs)
    recent = [
        p for p in prs
        if latest - _parse(p.created_at) <= timedelta(hours=window_hours)
    ]

    clusters: list[list[PR]] = []
    for p in recent:
        best, best_sim = None, 0.0
        for c in clusters:
            s = max(similarity(p.body, q.body) for q in c[-8:])
            if s > best_sim:
                best, best_sim = c, s
        if best is not None and best_sim >= sim_threshold:
            best.append(p)
        else:
            clusters.append([p])

    campaigns: list[dict] = []
    for c in clusters:
        if len(c) < min_cluster:
            continue
        proj_ids = {p.project for p in c}
        authors = sorted({p.contributor for p in c})
        if len(proj_ids) < min_projects:
            continue
        ages = [sim.contributors[a].account_age_days for a in authors]
        all_young = all(a <= young_max_age_days for a in ages)
        times = sorted(_parse(p.created_at) for p in c)
        span_h = (times[-1] - times[0]).total_seconds() / 3600
        burst = len(proj_ids) >= burst_min_projects and span_h <= burst_hours
        if not (all_young or burst):
            continue
        age_list = ", ".join(f"{a}:{age:.0f}d" for a, age in zip(authors, ages))
        campaigns.append(
            {
                "pr_ids": [p.id for p in c],
                "contributors": authors,
                "projects": len(proj_ids),
                "size": len(c),
                "all_accounts_young": all_young,
                "span_hours": round(span_h, 1),
                "evidence": (
                    f"{len(c)} near-identical PRs from {len(authors)} account(s) hit "
                    f"{len(proj_ids)} projects within {span_h:.1f}h; account ages: {age_list}"
                ),
            }
        )
    return campaigns
