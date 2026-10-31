"""Simulation loading and the deterministic demo simulation.

The demo reproduces the official evaluation scenario: a network of 30 projects
with existing vouch lists, denouncement lists, incoming pull requests, a
coordinated spam campaign (12 bot accounts, 60 near-identical PRs across 20
projects within ~2 hours), and 4 legitimate newcomers with no reputation.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from .models import Contributor, PR, Project, Simulation

BASE_TIME = datetime.fromisoformat("2026-10-31T20:00:00+00:00")


def load_simulation(path: str | Path) -> Simulation:
    with open(path, encoding="utf-8") as f:
        return Simulation.from_dict(json.load(f))


def demo_simulation(seed: int = 42, n_projects: int = 30) -> Simulation:
    rng = random.Random(seed)

    projects: dict[str, Project] = {}
    for i in range(n_projects):
        pid = f"project-{i + 1}"
        projects[pid] = Project(id=pid, name=f"Project {i + 1}")

    # Each project trusts 3 others with weights in [0.5, 0.9].
    for pid, p in projects.items():
        others = [q for q in projects if q != pid]
        for qid in rng.sample(others, 3):
            p.trusts[qid] = round(rng.uniform(0.5, 0.9), 2)

    # 20 established contributors with long account histories.
    contributors: dict[str, Contributor] = {}
    for j in range(20):
        cid = f"dev-{j + 1}"
        contributors[cid] = Contributor(id=cid, account_age_days=rng.uniform(200, 2000))

    # 12 bot accounts: young accounts driving the coordinated campaign.
    bot_ids = [f"bot-{k}" for k in range(1, 13)]
    for cid in bot_ids:
        contributors[cid] = Contributor(id=cid, account_age_days=rng.uniform(1.0, 3.0))

    # 4 legitimate newcomers with no established reputation.
    newcomer_ids = [f"newbie-{m}" for m in range(1, 5)]
    for cid in newcomer_ids:
        contributors[cid] = Contributor(id=cid, account_age_days=rng.uniform(0.5, 5.0))

    # Existing vouch lists: every project vouches 4 established devs.
    for p in projects.values():
        for cid in rng.sample(list(dev for dev in contributors if dev.startswith("dev-")), 4):
            p.vouches.append(cid)

    # Existing denouncement lists: every project denounces 2 bot accounts.
    for p in projects.values():
        for cid in rng.sample(bot_ids, 2):
            p.denounces.append(cid)

    prs: list[PR] = []
    counter = 0

    def make_pr(pid: str, cid: str, title: str, body: str, dt: datetime) -> PR:
        nonlocal counter
        counter += 1
        return PR(
            id=f"pr-{counter:03d}",
            project=pid,
            contributor=cid,
            title=title,
            body=body,
            created_at=dt.isoformat(),
        )

    t0 = BASE_TIME

    # Coordinated campaign: near-identical bodies from young accounts across many projects.
    template = (
        "Hi maintainers! I added a small improvement to optimize performance and fix a bug. "
        "Please merge this PR quickly, it would really help my Hacktoberfest goals. Thanks!"
    )
    target_projects = [f"project-{i + 1}" for i in range(20)]
    for k, bot in enumerate(bot_ids):
        for s in range(5):
            pid = target_projects[(k * 5 + s) % len(target_projects)]
            body = template + (" " * (k % 3))  # cosmetic-only variation
            prs.append(
                make_pr(
                    pid, bot, "Improve performance and fix bug", body,
                    t0 + timedelta(minutes=rng.randint(0, 110)),
                )
            )

    # Legitimate newcomers: original bodies, one project each. Must NOT be flagged.
    for m, cid in enumerate(newcomer_ids):
        body = (
            f"Documentation fix for {projects[f'project-{m + 1}'].name}: corrected the "
            "setup guide in README to match the current install steps."
        )
        prs.append(
            make_pr(
                f"project-{m + 1}", cid, "Fix README setup guide", body,
                t0 + timedelta(minutes=30 + m),
            )
        )

    # Established contributors: original, distinct bodies.
    for j in range(10):
        cid = f"dev-{j + 1}"
        pid = f"project-{(j % n_projects) + 1}"
        body = f"Adds unit tests for the parser module and fixes a race in worker shutdown (case {j})."
        prs.append(
            make_pr(pid, cid, "Add parser tests", body, t0 + timedelta(hours=j))
        )

    return Simulation(projects=projects, contributors=contributors, prs=prs)
