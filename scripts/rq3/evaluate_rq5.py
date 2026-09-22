#!/usr/bin/env python3
"""Valutazione deterministica delle risposte di RQ5 / SC06.

Risposte e oracle vengono uniti *soltanto qui*, dopo la generazione. La
valutazione applica la normalizzazione dichiarata nella configurazione — NFC,
rimozione dei soli spazi esterni, maiuscole e minuscole significative, ordine e
duplicati ignorati — e non usa nessun modello giudice.

Viene prodotta una riga per ogni cella attesa: split, tag del modello,
condizione e `question_id`. Le celle fallite o mancanti restano nel file con il
loro stato, perche' i denominatori delle metriche sono le celle attese, non
quelle riuscite. Nulla viene corretto o rigenerato.

Per ogni cella si registrano:

  - `exact_match` nella condizione sufficiente;
  - `correct_abstention` nella condizione insufficiente;
  - conteggi per precisione e richiamo delle etichette (solo sufficiente);
  - valori non supportati;
  - confusione fra casi, soltanto dove l'oracle la dichiara rilevabile;
  - errore di formato, con il motivo.

Uso:
    python3 scripts/rq3/evaluate_rq5.py --split development
    python3 scripts/rq3/evaluate_rq5.py --split evaluation
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq5_common as common  # noqa: E402


def last_response_per_cell(rows):
    """Vale l'ultima riga scritta per ogni cella: i tentativi precedenti restano."""
    last, attempts = {}, Counter()
    for row in rows:
        last[row["cell_id"]] = row
        attempts[row["cell_id"]] += 1
    return last, attempts


def evaluate_cell(config, request, oracle, model_tag, response):
    """Una riga di valutazione. `response` puo' essere None: cella mancante."""
    condition = request["condition"]
    expected = common.normalize_values(oracle["expected_values"], config)
    detectable = common.normalize_values(
        oracle["detectable_cross_case_intrusion_values"], config
    )

    row = {
        "cell_id": common.cell_id(
            request["split"], model_tag, condition, request["question_id"]
        ),
        "request_id": request["request_id"],
        "split": request["split"],
        "model_tag": model_tag,
        "condition": condition,
        "question_id": request["question_id"],
        "episode_id": request["episode_id"],
        "family": oracle["family"],
        "field": oracle["field"],
        "case_alias": oracle["case_alias"],
        "expected_values": sorted(expected),
        "n_expected": len(expected),
        "cross_case_detectable": bool(detectable),
    }

    if response is None:
        status, content = "missing", None
    elif response.get("prompt_sha256") != request["prompt_sha256"]:
        status, content = "stale_prompt", response.get("content")
    else:
        status, content = response.get("status", "error"), response.get("content")

    row["response_status"] = status
    row["raw_content"] = content
    row["attempts"] = response.get("attempts") if response else 0
    row["error"] = response.get("error") if response else None
    row["ollama_metrics"] = response.get("ollama_metrics", {}) if response else {}
    row["done_reason"] = response.get("done_reason") if response else None

    values, reason = (None, "no_response") if status != "ok" else common.parse_model_output(
        content, config
    )
    row["format_ok"] = values is not None
    row["format_error_reason"] = reason
    # Un errore di formato e' un errore osservato: conta come risposta non
    # corretta, non come cella da rifare.
    row["format_error"] = status == "ok" and values is None

    if values is None:
        row.update({
            "predicted_values": None,
            "predicted_normalized": None,
            "n_predicted": None,
            "exact_match": False if condition == "sufficient" else None,
            "correct_abstention": False if condition == "insufficient" else None,
            "true_positives": None,
            "false_positives": None,
            "false_negatives": None,
            "missing_values": None,
            "extra_values": None,
            "has_unsupported_value": None,
            "cross_case_intrusion": None,
            "cross_case_values_returned": None,
        })
        return row

    predicted = common.normalize_values(values, config)
    extra = predicted - expected
    missing = expected - predicted
    intruded = extra & detectable
    row.update({
        "predicted_values": list(values),
        "predicted_normalized": sorted(predicted),
        "n_predicted": len(predicted),
        "exact_match": (predicted == expected) if condition == "sufficient" else None,
        "correct_abstention": (not predicted) if condition == "insufficient" else None,
        "true_positives": len(predicted & expected) if condition == "sufficient" else None,
        "false_positives": len(extra) if condition == "sufficient" else None,
        "false_negatives": len(missing) if condition == "sufficient" else None,
        "missing_values": sorted(missing),
        "extra_values": sorted(extra),
        "has_unsupported_value": bool(extra),
        "cross_case_intrusion": bool(intruded) if detectable else None,
        "cross_case_values_returned": sorted(intruded),
    })
    return row


def evaluate(config, requests, oracle_rows, responses, model_tags):
    oracle_by_request = {row["request_id"]: row for row in oracle_rows}
    last, attempts = last_response_per_cell(responses)
    for row in last.values():
        row["attempts"] = attempts[row["cell_id"]]

    evaluations = []
    for request in requests:
        oracle = oracle_by_request.get(request["request_id"])
        if oracle is None:
            raise ValueError(f"{request['request_id']}: manca la riga di oracle")
        for model_tag in model_tags:
            cell = common.cell_id(
                request["split"], model_tag, request["condition"], request["question_id"]
            )
            evaluations.append(
                evaluate_cell(config, request, oracle, model_tag, last.get(cell))
            )
    return evaluations


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", required=True, choices=common.SPLITS)
    parser.add_argument("--config", default=str(common.CONFIG_PATH))
    parser.add_argument("--inputs-dir", default=None,
                        help="predefinita: la directory della versione in configurazione")
    parser.add_argument("--results-dir", default=None,
                        help="predefinita: la directory della versione in configurazione")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    config = common.load_config(args.config)
    inputs_dir = Path(args.inputs_dir) if args.inputs_dir else common.inputs_dir(config)
    results_dir = (Path(args.results_dir) if args.results_dir
                   else common.results_dir(config)) / args.split

    requests = common.read_jsonl(inputs_dir / f"{args.split}_requests.jsonl")
    oracle_rows = common.read_jsonl(inputs_dir / f"{args.split}_oracle.jsonl")
    responses_path = results_dir / "raw_responses.jsonl"
    responses = common.read_jsonl(responses_path) if responses_path.exists() else []

    model_tags = [model["ollama_tag"] for model in config["models"]]
    evaluations = evaluate(config, requests, oracle_rows, responses, model_tags)

    out_path = Path(args.out) if args.out else results_dir / "evaluations.jsonl"
    common.dump_jsonl(out_path, evaluations)

    status = Counter(row["response_status"] for row in evaluations)
    print(f"celle attese: {len(evaluations)} "
          f"(richieste {len(requests)} x modelli {len(model_tags)})")
    for name, count in sorted(status.items()):
        print(f"  {name:13s} {count}")
    print(f"errori di formato: {sum(1 for row in evaluations if row['format_error'])}")
    print(f"Scritto {out_path}")
    print(f"valutato il {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}, "
          "senza modello giudice")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
