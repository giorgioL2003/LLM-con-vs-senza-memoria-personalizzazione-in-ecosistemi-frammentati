#!/usr/bin/env python3
"""Valutazione di RQ4 / SC05 (solo dopo la generazione).

Unisce, soltanto ora, richieste, piano, risposte grezze, retrieval, copertura e
oracle. Per ogni cella attesa (anche mancante o in errore) produce una scheda
strutturata con:

  - parser rigoroso dell'output `{"status", "answer"}`;
  - flag automatici: evidenza nel corpus e nel contesto per fatto, stato
    dichiarato rispetto all'atteso dato il contesto, menzione di marcatori
    obsoleti, identificatori o numeri della risposta assenti dal contesto;
  - giudizi qualitativi (classe, fatti, uso di informazioni obsolete,
    affermazioni non supportate) lasciati `null` ed etichettati
    «proposto/in attesa di revisione» finche' lo studente non li approva in
    `results/rq4/sc05/v1/evaluation/annotations.jsonl`.

Nessun modello giudice. Scrive `annotation_template.jsonl` ed
`evaluations.jsonl` in `results/rq4/sc05/v1/evaluation/`.

Uso:
    python3 scripts/rq4/evaluate_rq4.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq4_common as common  # noqa: E402
from run_rq4_ollama import last_rows_by_cell  # noqa: E402

STAGE = "evaluation"


def automatic_flags(config, cell, coverage, parsed):
    answer = (parsed or {}).get("answer") or ""
    markers = config["evaluation"]["obsolete_markers"].get(cell["question_id"], [])
    mentioned = [m for m in markers if m.lower() in answer.lower()]
    candidates = [t for t in common.salient_tokens(answer, config) if t.strip("`") not in cell["context"]]
    expected = coverage["expected_status_given_context"]
    return {
        "evidence_in_corpus": coverage["evidence_in_corpus"],
        "evidence_in_context": coverage["evidence_in_context"],
        "facts_total": coverage["facts_total"],
        "facts_in_corpus": coverage["facts_in_corpus"],
        "facts_in_context": coverage["facts_in_context"],
        "retrieval_loss": coverage["retrieval_loss"],
        "expected_status_given_corpus": coverage["expected_status_given_corpus"],
        "expected_status_given_context": expected,
        "status_matches_expected_given_context": (parsed["status"] == expected) if parsed else None,
        "obsolete_marker_mentioned": mentioned,
        "unsupported_identifier_candidates": candidates,
    }


def pending_judgments(config, oracle_row):
    return {
        "final_class": None,
        "fact_judgments": {f["fact_key"]: None for f in oracle_row["required_facts"]},
        "uses_obsolete_as_current": None,
        "unsupported_claim": None,
        "review_status": config["evaluation"]["human_review"]["pending_label"],
    }


def load_annotations(config, out_root):
    path = Path(out_root) / config["evaluation"]["human_review"]["annotations_file"]
    if not path.exists():
        return {}
    allowed = set(config["evaluation"]["classes"])
    approved = {}
    for row in common.read_jsonl(path):
        if row.get("approved") is True and row.get("final_class") in allowed:
            approved[row["cell_id"]] = row
    return approved


def evaluate(config, out_root=common.REPO_ROOT):
    design = common.design_dir(config, out_root)
    cells = common.read_jsonl(design / "requests.jsonl")
    plan = {p["cell_id"]: p for p in common.read_jsonl(design / "generation_plan.jsonl")}
    coverage = {(c["question_id"], c["condition"]): c for c in common.read_jsonl(design / "retrieval_coverage.jsonl")}
    oracle = {o["question_id"]: o for o in common.load_oracle(config, out_root)}
    out_dir = common.stage_dir(config, STAGE, out_root)
    responses = last_rows_by_cell(out_dir / "raw_responses.jsonl")
    annotations = load_annotations(config, out_root)

    evaluations, template = [], []
    for cell in cells:
        o = oracle[cell["question_id"]]
        cov = coverage[(cell["question_id"], cell["condition"])]
        response = responses.get(cell["cell_id"])
        status = "missing" if response is None else response["status"]
        content = response.get("content") if response and status == "ok" else None
        ok, parsed, error = common.parse_output(content, config) if status == "ok" else (False, None, None)
        row = {
            "cell_id": cell["cell_id"], "model_tag": cell["model_tag"], "condition": cell["condition"],
            "question_id": cell["question_id"], "group": o["group"],
            "generation_kind": plan[cell["cell_id"]]["generation_kind"],
            "reused_from_cell_id": plan[cell["cell_id"]]["reused_from_cell_id"],
            "response_status": status, "content": content,
            "format_ok": ok, "format_error": error,
            "declared_status": parsed["status"] if parsed else None,
            "answer": parsed["answer"] if parsed else None,
            "flags": automatic_flags(config, cell, cov, parsed),
        }
        judgments = pending_judgments(config, o)
        approved = annotations.get(cell["cell_id"])
        if approved:
            judgments = {
                "final_class": approved["final_class"],
                "fact_judgments": approved.get("fact_judgments"),
                "uses_obsolete_as_current": approved.get("uses_obsolete_as_current"),
                "unsupported_claim": approved.get("unsupported_claim"),
                "review_status": "approvato dallo studente",
                "reviewer": approved.get("reviewer"),
            }
        row["judgments"] = judgments
        evaluations.append(row)
        template.append({
            "cell_id": cell["cell_id"], "model_tag": cell["model_tag"], "condition": cell["condition"],
            "question_id": cell["question_id"], "group": o["group"], "question": cell["question"],
            "context": cell["context"], "response_status": status, "raw_content": content,
            "expected_answer": o["expected_answer"], "mandatory_facts": o["mandatory_facts"],
            "obsolete_information": o["obsolete_information"],
            "accepted_equivalents": o["accepted_equivalents"], "flags": row["flags"],
            "allowed_classes": sorted(config["evaluation"]["classes"]),
            "final_class": None, "fact_judgments": {f["fact_key"]: None for f in o["required_facts"]},
            "uses_obsolete_as_current": None, "unsupported_claim": None,
            "reviewer": None, "approved": False, "notes": "",
            "review_status": config["evaluation"]["human_review"]["pending_label"],
        })
    common.dump_jsonl(out_dir / "evaluations.jsonl", evaluations)
    common.dump_jsonl(out_dir / "annotation_template.jsonl", template)
    return evaluations


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    rows = evaluate(common.load_config())
    present = sum(r["response_status"] == "ok" for r in rows)
    reviewed = sum(r["judgments"]["final_class"] is not None for r in rows)
    print(f"{len(rows)} celle attese, {present} con risposta, {reviewed} con giudizio approvato.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
