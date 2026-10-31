"""Data model: projects, contributors, pull requests, and the simulation they live in."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class Contributor:
    id: str
    account_age_days: float = 0.0


@dataclass
class Project:
    id: str
    name: str
    trusts: dict[str, float] = field(default_factory=dict)  # project_id -> weight in (0, 1]
    vouches: list[str] = field(default_factory=list)        # contributor ids trusted by this project
    denounces: list[str] = field(default_factory=list)      # contributor ids distrusted by this project


@dataclass
class PR:
    id: str
    project: str
    contributor: str
    title: str
    body: str
    created_at: str  # ISO-8601


@dataclass
class Simulation:
    projects: dict[str, Project]
    contributors: dict[str, Contributor]
    prs: list[PR]

    def to_dict(self) -> dict:
        return {
            "projects": [asdict(p) for p in self.projects.values()],
            "contributors": [asdict(c) for c in self.contributors.values()],
            "prs": [asdict(pr) for pr in self.prs],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Simulation":
        projects = {p["id"]: Project(**p) for p in data["projects"]}
        contributors = {c["id"]: Contributor(**c) for c in data["contributors"]}
        prs = [PR(**pr) for pr in data["prs"]]
        return cls(projects=projects, contributors=contributors, prs=prs)
