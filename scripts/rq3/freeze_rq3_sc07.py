#!/usr/bin/env python3
"""Congelamento della valutazione finale di RQ3 / SC07.

Scrive `results/rq3/sc07/v1/evaluation/freeze_manifest.json` con gli SHA-256
di configurazione, build manifest, richieste e oracle della valutazione,
retrieval, piano delle chiamate, evaluation gate, risposte grezze, run
manifest, valutazioni, riepiloghi e script usati, insieme ai conteggi previsti
e ottenuti e al modello richiesto e realmente usato. Si rifiuta di congelare
se le 240 celle non sono tutte concluse o se il validatore offline non passa.

Con `--verify` non scrive nulla: ricalcola ogni hash del manifest e controlla
che coincida.

Uso:
    python3 scripts/rq3/freeze_rq3_sc07.py
    python3 scripts/rq3/freeze_rq3_sc07.py --verify
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402
import run_rq3_sc07_claude as runner  # noqa: E402
import validate_rq3_sc07_inputs as validator  # noqa: E402

SCRIPTS = (
    "scripts/run_retrieval_pilot.py",
    "scripts/run_generation.py",
    "scripts/rq3/rq3_sc07_common.py",
    "scripts/rq3/acquire_rq3_sc07_source.py",
    "scripts/rq3/select_rq3_sc07_advisories.py",
    "scripts/rq3/build_rq3_sc07_episodes.py",
    "scripts/rq3/run_rq3_sc07_retrieval.py",
    "scripts/rq3/build_rq3_sc07_requests.py",
    "scripts/rq3/validate_rq3_sc07_inputs.py",
    "scripts/rq3/run_rq3_sc07_claude.py",
    "scripts/rq3/evaluate_rq3_sc07.py",
    "scripts/rq3/summarize_rq3_sc07.py",
    "scripts/rq3/freeze_rq3_sc07.py",
    "tests/test_rq3_sc07.py",
)


def manifest_path(config):
    return common.results_dir(config, "evaluation") / "freeze_manifest.json"


def artifact_paths(config):
    design = common.design_dir(config)
    results = common.results_dir(config, "evaluation")
    return {
        "configuration": common.CONFIG_PATH,
        "build_manifest": design / "build_manifest.json",
        "evaluation_requests": common.requests_path(config, "evaluation"),
        "evaluation_oracle": common.oracle_path(config, "evaluation"),
        "retrieval": results / "retrieval.jsonl",
        "retrieval_summary": results / "retrieval_summary.json",
        "call_plan": common.call_plan_path(config, "evaluation"),
        "evaluation_gate": runner.evaluation_gate_path(config),
        "raw_responses": results / "raw_responses.jsonl",
        "run_manifest": results / "run_manifest.json",
        "evaluations": results / "evaluations.jsonl",
        "summary_json": results / "summary.json",
        "summary_csv": results / "summary.csv",
        "sintesi_md": results / "SINTESI.md",
    }


def build(config):
    results = common.results_dir(config, "evaluation")
    plan = common.read_jsonl(common.call_plan_path(config, "evaluation"))
    rows = common.read_jsonl(results / "raw_responses.jsonl")
    last = runner.last_rows_by_cell(results / "raw_responses.jsonl")
    ok = [r for r in last.values() if r["status"] == "ok"]
    if len(plan) != config["counts"]["evaluation"]["cells"] or len(ok) != len(plan):
        raise SystemExit(f"congelamento rifiutato: {len(ok)}/{len(plan)} celle concluse")
    checks = validator.validate(config)
    if not checks.ok:
        raise SystemExit("congelamento rifiutato: il validatore offline non passa")
    calls = [r for r in rows if r.get("generation_kind") == "model_call"]
    runs = common.read_json(results / "run_manifest.json")["runs"]
    counts = config["counts"]["evaluation"]
    return {
        "status": "frozen_after_evaluation",
        "config_id": config["config_id"],
        "frozen_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "split": "evaluation",
        "counts": {
            "cells_expected": counts["cells"],
            "cells_obtained": len(ok),
            "model_calls_expected": counts["model_calls"],
            "model_calls_succeeded": sum(1 for r in calls if r["status"] == "ok"),
            "model_calls_failed": sum(1 for r in calls if r["status"] == "error"),
            "reused_cells_expected": counts["reused_cells"],
            "reused_cells_obtained": sum(1 for r in ok if r["generation_kind"] == "reused_identical_prompt"),
            "runs": len(runs),
        },
        "model": {
            "display_name": config["model"]["display_name"],
            "requested": config["model"]["model_id"],
            "used": sorted({r.get("model_used") for r in ok}),
            "access_channel": config["model"]["access_channel"],
            "effort": config["generation"]["parameters"]["effort"],
            "fallback_model": config["model"]["fallback_model"],
            "cli_versions": sorted({run.get("cli_version") for run in runs}),
        },
        "validator": {"checks": len(checks.results), "passed": sum(r["ok"] for r in checks.results)},
        "artifacts_sha256": {name: {"path": common.rel(path), "sha256": common.sha256_file(path)}
                             for name, path in artifact_paths(config).items()},
        "scripts_sha256": {path: common.sha256_file(common.REPO_ROOT / path) for path in SCRIPTS},
        "note": "Hash registrati dopo evaluate, summarize e validate. Nessun modello giudice.",
    }


def verify(config):
    manifest = common.read_json(manifest_path(config))
    problems = []
    entries = [(v["path"], v["sha256"]) for v in manifest["artifacts_sha256"].values()]
    entries += list(manifest["scripts_sha256"].items())
    for path, expected in entries:
        actual = common.sha256_file(common.REPO_ROOT / path)
        if actual != expected:
            problems.append(f"{path}: {actual} != {expected}")
    return len(entries), problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    config = common.load_config()
    if not args.verify:
        common.dump_json(manifest_path(config), build(config))
        print(f"Scritto {common.rel(manifest_path(config))}")
    total, problems = verify(config)
    for problem in problems:
        print(f"DIVERSO: {problem}")
    print(f"Hash verificati: {total - len(problems)}/{total}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
