"""Record every scenario into web/public/runs/ for the static site.

    uv run python scripts/record.py              # real model (local Ollama gemma4:e4b unless a key is set)
    uv run python scripts/record.py --no-model   # deterministic fallbacks only
    uv run python scripts/record.py c1-archana   # one case

Model calls are cached on disk, so re-recording is fast and reproducible.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lienline.agents import Gate
from lienline.money import inr
from lienline.pipeline import rebuild_index, run_case, save
from lienline.simulate import SCENARIOS, load

RUNS = Path(__file__).resolve().parents[2] / "web" / "public" / "runs"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cases", nargs="*", default=list(SCENARIOS), help="case ids (default: all)")
    parser.add_argument("--no-model", action="store_true", help="use the deterministic fallbacks only")
    parser.add_argument("--out", type=Path, default=RUNS)
    args = parser.parse_args()

    gate_mode = False if args.no_model else None
    failed = 0
    for case_id in args.cases:
        gate = Gate.auto(gate_mode)
        if not args.no_model and not gate.enabled:
            print("No model backend is available; pass --no-model to record fallbacks.", file=sys.stderr)
            return 2
        run = run_case(load(case_id), gate)
        path = save(run, args.out)
        held_before = sum(d.current_hold for d in run.decisions)
        held_after = sum(d.amount for d in run.decisions)
        print(f"{'ok  ' if run.verification.passed else 'FAIL'} {case_id}: lost {inr(run.complaint.amount_lost)}, "
              f"held {inr(held_before)} -> {inr(held_after)}, {run.model.calls} model calls "
              f"({run.model.backend}), {len(run.events)} events, t={run.events[-1].t:.1f}s -> {path.name}")
        failed += not run.verification.passed
    rebuild_index(args.out, SCENARIOS)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
