#!/usr/bin/env python3
"""Valutazione deterministica di RQ3 / SC07 (dopo la generazione).

Unisce, soltanto ora, richieste, tracce di retrieval, risposte grezze e oracle.
Scrive una riga per **ogni cella attesa**, anche se la risposta manca o e'
un errore di trasporto. Nessun modello giudice, nessuna correzione manuale.

Per ogni cella:
  - parser rigoroso di `{"value": string|null}` (errore di formato altrimenti);
  - exact match dopo NFC e rimozione degli spazi esterni, maiuscole rilevanti;
  - raggiungibilita' dell'evidenza e successo del retrieval (dalle tracce);
  - contaminazione del contesto (messaggi recuperati di altre attivita');
  - risposta supportata (il valore compare nel contesto recuperato);
  - confusione fra attivita' (valore errato uguale a un fatto di un'altra
    attivita' dello stesso episodio);
  - `null` nonostante l'evidenza recuperata;
  - attribuzione dell'errore nell'ordine della configurazione.
Le celle con `generation_kind="reused_identical_prompt"` sono valutate come
tutte le altre: hanno la stessa risposta della cella con prompt identico.

Uso:
    python3 scripts/rq3/evaluate_rq3_sc07.py --split development
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402
from run_rq3_sc07_claude import last_rows_by_cell  # noqa: E402


def evaluate_cell(config, request, retrieval, oracle_row, episode_facts, response):
    norm = lambda value: common.normalize_value(value, config)  # noqa: E731
    expected = oracle_row["expected_value"]
    row = {
        "cell_id": None,
        "request_id": request["request_id"],
        "split": request["split"],
        "condition": request["condition"],
        "question_id": request["question_id"],
        "episode_id": request["episode_id"],
        "ecosystem": oracle_row["ecosystem"],
        "question_type": request["question_type"],
        "activity": request["activity"],
        "expected_value": expected,
        "evidence_message_id": retrieval["evidence_message_id"],
        "retrieved_message_ids": retrieval["retrieved_message_ids"],
        "evidence_reachable": retrieval["evidence_reachable"],
        "retrieval_success": retrieval["retrieval_success"],
        "retrieved_messages": len(retrieval["retrieved_message_ids"]),
        "contamination_count": retrieval["contamination_count"],
        "contamination_rate": retrieval["contamination_rate"],
        "response_status": "missing",
        "response_text": None,
        "format_ok": False,
        "format_error": None,
        "predicted_value": None,
        "is_null": False,
        "exact_match": False,
        "supported": None,
        "cross_activity_confusion": None,
        "confused_with": None,
        "null_despite_evidence": False,
        "error_category": None,
        "generation_kind": None,
        "reused_from_cell_id": None,
        "model_used": None,
    }
    if response is not None:
        row["cell_id"] = response["cell_id"]
        row["response_status"] = response["status"]
        row["generation_kind"] = response.get("generation_kind")
        row["reused_from_cell_id"] = response.get("reused_from_cell_id")
        row["model_used"] = response.get("model_used")
        if response["status"] == "ok":
            row["response_text"] = response.get("response_text")
            ok, value, error = common.parse_model_output(response.get("response_text"))
            row["format_ok"], row["format_error"] = ok, error
            if ok:
                row["predicted_value"] = value
                row["is_null"] = value is None
                if value is not None:
                    predicted = norm(value)
                    row["exact_match"] = predicted == norm(expected)
                    row["supported"] = predicted != "" and predicted in norm(request["context"])
                    if not row["exact_match"]:
                        matches = sorted(
                            key for key, fact in episode_facts.items()
                            if key[0] != request["activity"] and norm(fact) == predicted
                        )
                        row["cross_activity_confusion"] = bool(matches)
                        row["confused_with"] = [f"{a}.{f}" for a, f in matches] or None
                row["null_despite_evidence"] = value is None and retrieval["retrieval_success"]

    if not row["exact_match"]:
        if row["response_status"] != "ok":
            row["error_category"] = "missing_response"
        elif not row["evidence_reachable"]:
            row["error_category"] = "evidence_unreachable"
        elif not row["retrieval_success"]:
            row["error_category"] = "retrieval"
        elif not row["format_ok"]:
            row["error_category"] = "format"
        else:
            row["error_category"] = "generation"
    order = config["evaluation"]["error_attribution_order"]
    if row["error_category"] and row["error_category"] not in order:
        raise ValueError(f"categoria di errore non dichiarata: {row['error_category']}")
    return row


def evaluate(config, split, repo_root=common.REPO_ROOT):
    model_id = config["model"].get("model_id")
    if not model_id:
        raise ValueError("model.model_id non registrato: impossibile identificare le celle")
    requests = common.read_jsonl(common.requests_path(config, split, repo_root))
    results = common.results_dir(config, split, repo_root)
    retrieval = {(r["condition"], r["question_id"]): r for r in common.read_jsonl(results / "retrieval.jsonl")}
    oracle = {o["question_id"]: o for o in common.load_oracle(config, split, repo_root)}
    facts = {}
    for o in oracle.values():
        facts.setdefault(o["episode_id"], {})[(o["activity"], o["fact"])] = o["expected_value"]
    responses = last_rows_by_cell(results / "raw_responses.jsonl")
    rows = []
    for request in requests:
        cid = common.cell_id(split, model_id, request["condition"], request["question_id"])
        row = evaluate_cell(
            config, request, retrieval[(request["condition"], request["question_id"])],
            oracle[request["question_id"]], facts[request["episode_id"]], responses.get(cid))
        row["cell_id"] = cid
        rows.append(row)
    common.dump_jsonl(results / "evaluations.jsonl", rows)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", required=True, choices=common.SPLITS)
    args = parser.parse_args(argv)
    rows = evaluate(common.load_config(), args.split)
    present = sum(1 for r in rows if r["response_status"] == "ok")
    print(f"{args.split}: {len(rows)} celle attese, {present} con risposta, "
          f"{sum(r['exact_match'] for r in rows)} exact match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
