"""End-to-end tests on the demo simulation (the official evaluation scenario).

The demo contains: 30 projects, vouch lists, denouncement lists, incoming
PRs, a coordinated spam campaign (12 young bot accounts, 60 near-identical
PRs across 20 projects within ~2 hours), and 4 legitimate newcomers.

Expectations (the rubric):
- every campaign PR is flagged;
- every legitimate newcomer PR is allowed (fairness);
- every flagged PR carries evidence.
"""
from trustnet.evaluate import run_pipeline
from trustnet.sim import demo_simulation


def test_all_campaign_prs_are_flagged():
    sim = demo_simulation()
    result = run_pipeline(sim)
    bot_prs = {p.id for p in sim.prs if p.contributor.startswith("bot-")}
    flagged = {v["pr"] for v in result["verdicts"] if v["decision"] == "flag"}
    assert bot_prs <= flagged, f"campaign PRs missed: {bot_prs - flagged}"


def test_legitimate_newcomers_are_allowed():
    sim = demo_simulation()
    result = run_pipeline(sim)
    newcomer_prs = {p.id for p in sim.prs if p.contributor.startswith("newbie-")}
    flagged = {v["pr"] for v in result["verdicts"] if v["decision"] == "flag"}
    assert not (newcomer_prs & flagged), "newcomers were unfairly flagged"


def test_every_flag_carries_evidence():
    sim = demo_simulation()
    result = run_pipeline(sim)
    for v in result["verdicts"]:
        if v["decision"] == "flag":
            assert v["reasons"], f"{v['pr']} flagged without reasons"


def test_campaign_report_has_quantified_evidence():
    sim = demo_simulation()
    result = run_pipeline(sim)
    assert result["campaigns"], "expected at least one detected campaign"
    c = result["campaigns"][0]
    assert c["size"] >= 5
    assert c["projects"] >= 2
    assert "near-identical" in c["evidence"]
    assert "account ages" in c["evidence"]


def test_deterministic_runs():
    r1 = run_pipeline(demo_simulation())
    r2 = run_pipeline(demo_simulation())
    assert r1["summary"] == r2["summary"]
    assert r1["verdicts"] == r2["verdicts"]
