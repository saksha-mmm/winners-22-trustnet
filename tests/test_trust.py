"""Tests for trust propagation: transitivity, damping, and evidence."""
import pytest

from trustnet.models import Contributor, Project
from trustnet.trust import contributor_score, trust_vector


def test_self_trust_is_one():
    projects = {"a": Project(id="a", name="A")}
    assert trust_vector("a", projects) == {"a": 1.0}


def test_first_hop_undamped_and_transitive_hops_damped():
    projects = {
        "a": Project(id="a", name="A", trusts={"b": 0.8}),
        "b": Project(id="b", name="B", trusts={"c": 0.5}),
        "c": Project(id="c", name="C"),
    }
    tv = trust_vector("a", projects)
    assert tv["b"] == pytest.approx(0.8)
    # a -> b -> c: 0.8 * 0.5, damped once for the second hop
    assert tv["c"] == pytest.approx(0.8 * 0.5 * 0.5)


def test_best_path_wins():
    projects = {
        "a": Project(id="a", name="A", trusts={"b": 0.9, "d": 0.3}),
        "b": Project(id="b", name="B", trusts={"c": 0.1}),
        "d": Project(id="d", name="D", trusts={"c": 0.8}),
        "c": Project(id="c", name="C"),
    }
    tv = trust_vector("a", projects)
    # a -> d -> c: 0.3 * 0.8 * 0.5 = 0.12 beats a -> b -> c: 0.9 * 0.1 * 0.5 = 0.045
    assert tv["c"] == pytest.approx(0.12)


def test_vouch_from_trusted_project_adds_score_with_evidence():
    projects = {
        "a": Project(id="a", name="A", trusts={"b": 0.9}),
        "b": Project(id="b", name="B", vouches=["dev1"]),
    }
    contributors = {"dev1": Contributor(id="dev1", account_age_days=100)}
    score, evidence = contributor_score("dev1", "a", projects, contributors)
    assert score == pytest.approx(0.9)
    assert any("vouch by B" in e for e in evidence)


def test_unknown_contributor_scores_neutral():
    projects = {"a": Project(id="a", name="A", trusts={"b": 0.9})}
    contributors = {}
    score, evidence = contributor_score("ghost", "a", projects, contributors)
    assert score == 0.0
    assert evidence == []
