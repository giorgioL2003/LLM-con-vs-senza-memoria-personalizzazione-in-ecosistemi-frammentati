#!/usr/bin/env python3
"""Costruzione delle richieste di RQ3 / SC07.

Per ogni domanda e condizione usa **esattamente** i messaggi gia' salvati in
`results/rq3/sc07/v1/<split>/retrieval.jsonl` (`retrieved_message_ids`,
nell'ordine del retrieval): il retrieval non viene rieseguito e dal file
di retrieval non si legge nessun campo dell'oracle (evidenza, successo).

Il prompt e' composto da `prompt.system` e `prompt.user_template` della
configurazione; il contesto e' `[rank] testo del messaggio`, una riga per
messaggio recuperato. Fra le due condizioni cambiano soltanto i messaggi
recuperati, quindi il contesto.

Scrive in `data/rq3/sc07_design_v1/`:
  development_requests.jsonl   36 richieste (18 domande x 2 condizioni)
  evaluation_requests.jsonl    240 richieste (120 domande x 2 condizioni)
  development_call_plan.jsonl  per cella: chiamata reale o riuso di un prompt identico
  evaluation_call_plan.jsonl   (23 chiamate reali su 36 celle; 139 su 240)
  build_manifest.json          hash di configurazione, sorgente, artefatti e script

Uso:
    python3 scripts/rq3/build_rq3_sc07_requests.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402

# Campi del file di retrieval che la costruzione delle richieste puo' leggere.
RETRIEVAL_FIELDS_USED = ("split", "condition", "question_id", "retrieved_message_ids")

SC07_SCRIPTS = (
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
)


def build_requests(config, episodes, questions, retrieval_rows):
    contents = {m["message_id"]: m["content"] for e in episodes for m in e["messages"]}
    question_by_id = {q["question_id"]: q for q in questions}
    requests = []
    for row in retrieval_rows:
        view = {field: row[field] for field in RETRIEVAL_FIELDS_USED}
        question = question_by_id[view["question_id"]]
        ids = list(view["retrieved_message_ids"])
        context = common.render_context(config, [contents[i] for i in ids])
        system, user = common.build_prompt(config, context, question["text"])
        requests.append({
            "request_id": common.request_id(view["split"], view["condition"], question["question_id"]),
            "config_id": config["config_id"],
            "split": view["split"],
            "condition": view["condition"],
            "question_id": question["question_id"],
            "episode_id": question["episode_id"],
            "question_type": question["question_type"],
            "activity": question["activity"],
            "question": question["text"],
            "context_message_ids": ids,
            "context": context,
            "system": system,
            "user": user,
            "prompt_sha256": common.prompt_sha256(system, user),
        })
    order = {c: i for i, c in enumerate(config["conditions"]["order"])}
    requests.sort(key=lambda r: (r["question_id"], order[r["condition"]]))
    return requests


def artifact_hashes(paths, repo_root):
    return {common.rel(p, repo_root): common.sha256_file(p) for p in paths}


def run(config, repo_root=common.REPO_ROOT, config_path=common.CONFIG_PATH):
    design = common.design_dir(config, repo_root)
    episodes = common.read_jsonl(design / "episodes.jsonl")
    questions = common.read_jsonl(design / "questions.jsonl")
    counts = {}
    for split in common.SPLITS:
        retrieval = common.read_jsonl(common.results_dir(config, split, repo_root) / "retrieval.jsonl")
        requests = build_requests(
            config,
            [e for e in episodes if e["split"] == split],
            [q for q in questions if q["split"] == split],
            retrieval,
        )
        common.dump_jsonl(common.requests_path(config, split, repo_root), requests)
        plan = common.plan_calls(config, requests)
        common.dump_jsonl(common.call_plan_path(config, split, repo_root), plan)
        model_calls = sum(1 for p in plan if p["generation_kind"] == "model_call")
        counts[split] = {
            "episodes": sum(1 for e in episodes if e["split"] == split),
            "questions": sum(1 for q in questions if q["split"] == split),
            "requests": len(requests),
            "cells": len(plan),
            "model_calls": model_calls,
            "reused_cells": len(plan) - model_calls,
        }

    artifacts = [design / name for name in (
        "source_manifest.json", "eligibility_audit.json", "candidates.jsonl", "exclusions.jsonl",
        "selection.jsonl", "episodes.jsonl", "questions.jsonl", "message_provenance.jsonl",
        "development_oracle.jsonl", "evaluation_oracle.jsonl",
        "development_requests.jsonl", "evaluation_requests.jsonl",
        "development_call_plan.jsonl", "evaluation_call_plan.jsonl",
    )]
    retrieval_files = [common.results_dir(config, s, repo_root) / "retrieval.jsonl" for s in common.SPLITS]
    manifest = {
        "config_id": config["config_id"],
        "config_path": common.rel(config_path, repo_root),
        "config_sha256": common.sha256_file(config_path),
        "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_commit": config["source"]["commit"],
        "snapshot_sha256": config["source"]["snapshot_sha256"],
        "counts": counts,
        "artifacts_sha256": artifact_hashes(artifacts, repo_root),
        "retrieval_sha256": artifact_hashes(retrieval_files, repo_root),
        "scripts_sha256": artifact_hashes([common.REPO_ROOT / s for s in SC07_SCRIPTS], common.REPO_ROOT),
        "separation": {
            "conversations": "episodes.jsonl",
            "questions": "questions.jsonl",
            "requests_without_oracle": ["development_requests.jsonl", "evaluation_requests.jsonl"],
            "oracle": ["development_oracle.jsonl", "evaluation_oracle.jsonl"],
            "provenance": ["message_provenance.jsonl", "selection.jsonl", "candidates.jsonl"],
            "retrieval_traces": [common.rel(p, repo_root) for p in retrieval_files],
        },
        "model": common.model_configuration(config),
        "model_config_sha256": common.model_config_sha256(config),
        "reuse_rule": config["generation"]["reuse_identical_prompts"]["rule"],
        "model_calls_executed": 0,
    }
    common.dump_json(design / "build_manifest.json", manifest)
    return manifest


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    manifest = run(common.load_config())
    for split, c in manifest["counts"].items():
        print(f"{split}: {c['episodes']} episodi, {c['questions']} domande, {c['cells']} celle, "
              f"{c['model_calls']} chiamate reali, {c['reused_cells']} celle con prompt identico riusato")
    print("Manifest: data/rq3/sc07_design_v1/build_manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
