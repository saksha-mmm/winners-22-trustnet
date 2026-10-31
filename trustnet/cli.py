"""Command-line interface.

Commands:
  trustnet demo --out <file> [--seed N]      generate the demo simulation
  trustnet run <sim.json> [--report out.md] [--json out.json] [--llm]
  trustnet campaign <sim.json>               detect campaigns only
  trustnet evaluate <sim.json> <pr_id>       evaluate a single PR
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .campaign import detect_campaigns
from .evaluate import evaluate_pr, run_pipeline
from .report import build_markdown, llm_summary, rule_based_summary
from .sim import demo_simulation, load_simulation


def _load_sim(path: str):
    try:
        return load_simulation(path)
    except (OSError, KeyError, TypeError) as exc:
        print(f"error: cannot load simulation {path!r}: {exc}", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trustnet",
        description="Decentralized trust network for open-source contributions (Problem 07)",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="generate the demo simulation")
    d.add_argument("--out", required=True, help="output JSON path")
    d.add_argument("--seed", type=int, default=42)

    r = sub.add_parser("run", help="evaluate all PRs and detect campaigns")
    r.add_argument("sim", help="simulation JSON")
    r.add_argument("--report", help="write markdown report to this path")
    r.add_argument("--json", help="write JSON results to this path")
    r.add_argument("--llm", action="store_true", help="try local LLM summary (Ollama)")

    c = sub.add_parser("campaign", help="detect coordinated campaigns only")
    c.add_argument("sim")

    e = sub.add_parser("evaluate", help="evaluate a single PR")
    e.add_argument("sim")
    e.add_argument("pr_id")

    args = parser.parse_args(argv)

    if args.cmd == "demo":
        sim = demo_simulation(args.seed)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(sim.to_dict(), f, indent=2)
        print(
            f"wrote {args.out} ({len(sim.projects)} projects, "
            f"{len(sim.contributors)} contributors, {len(sim.prs)} PRs)"
        )
        return 0

    sim = _load_sim(args.sim)

    if args.cmd == "campaign":
        for c in detect_campaigns(sim):
            print(f"- {c['evidence']}")
            print(f"  PRs: {', '.join(c['pr_ids'])}")
        return 0

    if args.cmd == "evaluate":
        pr = next((p for p in sim.prs if p.id == args.pr_id), None)
        if pr is None:
            print(f"error: PR {args.pr_id!r} not found", file=sys.stderr)
            return 1
        cmap = {pid: c["evidence"] for c in detect_campaigns(sim) for pid in c["pr_ids"]}
        verdict = evaluate_pr(pr, sim, cmap)
        print(json.dumps(verdict, indent=2))
        return 0

    # run
    result = run_pipeline(sim)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"wrote {args.json}")

    summary_text = "\n".join(
        f"{v['pr']}: {v['decision']} ({'; '.join(v['reasons'])})" for v in result["verdicts"]
    )
    if args.llm:
        llm = llm_summary(summary_text)
        if llm:
            print("## LLM summary\n" + llm)
        else:
            print("## LLM summary (model unreachable — rule-based)\n" + rule_based_summary(result))
    else:
        print("## Summary\n" + rule_based_summary(result))

    if args.report:
        md = build_markdown(result, sim_source=args.sim)
        if args.llm:
            llm = llm_summary(summary_text)
            if llm:
                md += "\n## AI summary (open model)\n\n" + llm + "\n"
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
