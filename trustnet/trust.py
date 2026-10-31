"""Trust propagation across projects.

Model: each project fully trusts itself (trust = 1.0) and trusts other
projects with an explicit weight w in (0, 1]. Trust is transitive along trust
edges, but each hop beyond the first is damped by DAMPING to stop far-away
opinions from outweighing direct ones:

    trust_A(B)      = w(A -> B)
    trust_A(C)      = max over paths of  product(weights) * DAMPING^(hops - 1)

A contributor's aggregate score from a project's point of view is the sum,
over every project whose opinion reaches the viewer, of
trust(viewer -> Q) * reputation_Q(contributor), where reputation is +1 for a
vouch and -1 for a denounce. Unknown contributors score 0 — they are treated
neutrally, which is the newcomer-fairness guarantee.
"""
from __future__ import annotations

from .models import Contributor, Project

DAMPING = 0.5
MAX_DEPTH = 4


def trust_vector(viewer: str, projects: dict[str, Project]) -> dict[str, float]:
    """Best-path trust from `viewer` to every reachable project."""
    best: dict[str, float] = {viewer: 1.0}

    def walk(current: str, score: float, depth: int, visited: frozenset[str]) -> None:
        if depth > MAX_DEPTH:
            return
        for nxt, weight in projects[current].trusts.items():
            if nxt in visited or nxt not in projects:
                continue
            candidate = score * weight * (DAMPING if depth > 0 else 1.0)
            if candidate > best.get(nxt, 0.0):
                best[nxt] = candidate
            walk(nxt, candidate, depth + 1, visited | {nxt})

    walk(viewer, 1.0, 0, frozenset({viewer}))
    return best


def contributor_score(
    contributor_id: str,
    viewer_project: str,
    projects: dict[str, Project],
    contributors: dict[str, Contributor],
) -> tuple[float, list[str]]:
    """Aggregate reputation of `contributor_id` seen from `viewer_project`.

    Returns (score, evidence_lines). Positive = trusted, negative = distrusted.
    """
    tv = trust_vector(viewer_project, projects)
    score = 0.0
    evidence: list[str] = []
    for pid, t in sorted(tv.items(), key=lambda kv: -kv[1]):
        p = projects[pid]
        if contributor_id in p.vouches:
            score += t
            evidence.append(f"+1 vouch by {p.name} (trust {t:.2f})")
        if contributor_id in p.denounces:
            score -= t
            evidence.append(f"-1 denounce by {p.name} (trust {t:.2f})")
    return score, evidence
