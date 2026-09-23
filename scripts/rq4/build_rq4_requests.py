#!/usr/bin/env python3
"""Richieste, piano delle generazioni e manifest di RQ4 / SC05.

Usa **esattamente** le righe gia' selezionate in `retrieval.jsonl`
(`selected_renders`, nell'ordine del retrieval): il retrieval non viene
rieseguito e non si legge nessun file dell'oracle o della copertura.

Scrive in `data/rq4/sc05_handoff_v1/`:
  requests.jsonl          28 celle = 2 modelli B x 2 condizioni x 7 domande;
                          prompt identico fra i modelli per stessa domanda e
                          condizione, hash del prompt e della configurazione
  generation_plan.jsonl   per cella: `model_call` o `reused_identical_prompt`
                          (riuso solo entro lo stesso modello)
  smoke_requests.jsonl    una richiesta per modello sulla fixture non SC05
  build_manifest.json     hash di configurazione, sorgenti, artefatti, script
                          e conteggi congelati di chiamate e riusi

Uso:
    python3 scripts/rq4/build_rq4_requests.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq4_common as common  # noqa: E402

RETRIEVAL_FIELDS_USED = ("question_id", "condition", "selected_message_ids", "selected_renders")

RQ4_SCRIPTS = (
    "scripts/run_retrieval_pilot.py",
    "scripts/rq2/rq2_common.py",
    "scripts/rq3/rq5_common.py",
    "scripts/rq3/run_rq5_ollama.py",
    "scripts/rq4/rq4_common.py",
    "scripts/rq4/build_rq4_design.py",
    "scripts/rq4/run_rq4_retrieval.py",
    "scripts/rq4/build_rq4_requests.py",
    "scripts/rq4/validate_rq4_inputs.py",
    "scripts/rq4/run_rq4_ollama.py",
    "scripts/rq4/evaluate_rq4.py",
    "scripts/rq4/summarize_rq4.py",
)


def build_cells(config, questions, retrieval_rows, stage="evaluation"):
    texts = {q["question_id"]: q["text"] for q in questions}
    prompts = {}
    for row in retrieval_rows:
        view = {k: row[k] for k in RETRIEVAL_FIELDS_USED}
        context = common.render_context(config, view["selected_renders"])
        system, user = common.build_prompt(config, context, texts[view["question_id"]])
        prompts[(view["question_id"], view["condition"])] = (view, context, system, user)
    order = {c: i for i, c in enumerate(config["conditions"]["order"])}
    cells = []
    for model_tag in config["runtime"]["model_order"]:
        mc = common.model_config_sha256(config, model_tag)
        for (qid, condition) in sorted(prompts, key=lambda k: (k[0], order[k[1]])):
            view, context, system, user = prompts[(qid, condition)]
            cells.append({
                "cell_id": common.cell_id(stage, model_tag, condition, qid),
                "request_id": common.request_id(condition, qid),
                "config_id": config["config_id"],
                "stage": stage,
                "model_tag": model_tag,
                "condition": condition,
                "question_id": qid,
                "question": texts[qid],
                "context_message_ids": list(view["selected_message_ids"]),
                "context": context,
                "system": system,
                "user": user,
                "prompt_sha256": common.prompt_sha256(system, user),
                "model_config_sha256": mc,
            })
    return cells


def build_smoke(config):
    fixture = config["smoke"]["fixture"]
    context = common.render_context(config, fixture["context_lines"])
    system, user = common.build_prompt(config, context, fixture["question"])
    return [{
        "cell_id": f"smoke|{tag}|{fixture['request_id']}",
        "request_id": fixture["request_id"],
        "config_id": config["config_id"],
        "stage": "smoke",
        "model_tag": tag,
        "context": context,
        "question": fixture["question"],
        "system": system,
        "user": user,
        "prompt_sha256": common.prompt_sha256(system, user),
        "model_config_sha256": common.model_config_sha256(config, tag),
        "note": "fixture esclusa da SC05; non entra nei risultati",
    } for tag in config["runtime"]["model_order"]]


def hashes(paths, root):
    return {common.rel(p, root): common.sha256_file(p) for p in paths}


def run(config, out_root=common.REPO_ROOT, config_path=common.CONFIG_PATH):
    design = common.design_dir(config, out_root)
    questions = common.read_jsonl(design / "questions.jsonl")
    retrieval = common.read_jsonl(design / "retrieval.jsonl")
    cells = build_cells(config, questions, retrieval)
    plan = common.plan_generation(config, cells)
    smoke = build_smoke(config)
    common.dump_jsonl(design / "requests.jsonl", cells)
    common.dump_jsonl(design / "generation_plan.jsonl", plan)
    common.dump_jsonl(design / "smoke_requests.jsonl", smoke)

    calls = [p for p in plan if p["generation_kind"] == "model_call"]
    counts = {
        "cells": len(cells),
        "model_calls": len(calls),
        "reused_cells": len(plan) - len(calls),
        "model_calls_per_model": {tag: sum(1 for p in calls if p["model_tag"] == tag)
                                  for tag in config["runtime"]["model_order"]},
        "distinct_prompts": len({c["prompt_sha256"] for c in cells}),
        "smoke_requests": len(smoke),
    }
    artifacts = [design / n for n in ("source_manifest.json", "messages.jsonl", "questions.jsonl", "oracle.jsonl",
                                       "retrieval.jsonl", "retrieval_coverage.jsonl", "requests.jsonl",
                                       "generation_plan.jsonl", "smoke_requests.jsonl")]
    manifest = {
        "config_id": config["config_id"],
        "config_path": common.rel(config_path, common.REPO_ROOT),
        "config_sha256": common.sha256_file(config_path),
        "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": {name: {"path": path, "sha256": sha} for name, path, sha in common.source_entries(config)},
        "counts": counts,
        "expected_counts": config["counts"],
        "model_config_sha256": {tag: common.model_config_sha256(config, tag) for tag in config["runtime"]["model_order"]},
        "artifacts_sha256": hashes(artifacts, out_root),
        "scripts_sha256": hashes([common.REPO_ROOT / s for s in RQ4_SCRIPTS if (common.REPO_ROOT / s).exists()],
                                 common.REPO_ROOT),
        "separation": {
            "conversations": "messages.jsonl",
            "questions": "questions.jsonl",
            "oracle": "oracle.jsonl",
            "retrieval_without_oracle": "retrieval.jsonl",
            "retrieval_coverage_from_oracle": "retrieval_coverage.jsonl",
            "requests_without_oracle": "requests.jsonl",
            "generation_plan": "generation_plan.jsonl",
        },
        "model_calls_executed": 0,
    }
    common.dump_json(design / "build_manifest.json", manifest)
    return manifest


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    manifest = run(common.load_config())
    c = manifest["counts"]
    print(f"Celle: {c['cells']}  chiamate reali previste: {c['model_calls']} {c['model_calls_per_model']}  "
          f"riusi: {c['reused_cells']}  prompt distinti: {c['distinct_prompts']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
