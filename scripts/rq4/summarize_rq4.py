#!/usr/bin/env python3
"""Riepilogo di RQ4 / SC05.

Legge `evaluations.jsonl` e produce conteggi separati per modello B,
condizione e gruppo di domanda, sempre con numeratore e denominatore. Non
media mai domande dipendenti dal passaggio, controlli e informazione assente
in un solo punteggio. I giudizi qualitativi entrano soltanto se approvati
dallo studente; altrimenti sono contati come «in attesa di revisione».

Scrive `summary.json`, `summary.csv` e `SINTESI.md` in
`results/rq4/sc05/v1/evaluation/`.

Uso:
    python3 scripts/rq4/summarize_rq4.py
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq4_common as common  # noqa: E402

STAGE = "evaluation"


def ratio(num, den):
    return {"numerator": num, "denominator": den, "rate": (num / den) if den else None}


def block(rows, config):
    present = [r for r in rows if r["response_status"] == "ok"]
    parsed = [r for r in present if r["format_ok"]]
    reviewed = [r for r in rows if r["judgments"]["final_class"] is not None]
    return {
        "cells": len(rows),
        "responses": ratio(len(present), len(rows)),
        "missing_or_error": ratio(len(rows) - len(present), len(rows)),
        "format_error": ratio(len(present) - len(parsed), len(present)),
        "declared_answered": ratio(sum(r["declared_status"] == "answered" for r in parsed), len(parsed)),
        "declared_insufficient": ratio(sum(r["declared_status"] == "insufficient" for r in parsed), len(parsed)),
        "status_matches_expected_given_context": ratio(
            sum(bool(r["flags"]["status_matches_expected_given_context"]) for r in parsed), len(parsed)),
        "evidence_facts_in_corpus": ratio(sum(r["flags"]["facts_in_corpus"] for r in rows),
                                          sum(r["flags"]["facts_total"] for r in rows)),
        "evidence_facts_in_context": ratio(sum(r["flags"]["facts_in_context"] for r in rows),
                                           sum(r["flags"]["facts_total"] for r in rows)),
        "obsolete_marker_flagged": ratio(sum(bool(r["flags"]["obsolete_marker_mentioned"]) for r in parsed), len(parsed)),
        "unsupported_identifier_flagged": ratio(
            sum(bool(r["flags"]["unsupported_identifier_candidates"]) for r in parsed), len(parsed)),
        "human_review": {
            "reviewed": ratio(len(reviewed), len(rows)),
            "pending": len(rows) - len(reviewed),
            "classes": {c: ratio(sum(r["judgments"]["final_class"] == c for r in reviewed), len(reviewed))
                        for c in config["evaluation"]["classes"]},
            "uses_obsolete_as_current": ratio(sum(r["judgments"]["uses_obsolete_as_current"] is True for r in reviewed),
                                              len(reviewed)),
            "unsupported_claim": ratio(sum(r["judgments"]["unsupported_claim"] is True for r in reviewed), len(reviewed)),
        },
    }


def paired(rows, config):
    """Domanda per domanda, condivisa contro separata, entro lo stesso modello."""
    result = {}
    for tag in config["runtime"]["model_order"]:
        per_q = {}
        for r in rows:
            if r["model_tag"] != tag:
                continue
            per_q.setdefault(r["question_id"], {})[r["condition"]] = {
                "group": r["group"], "declared_status": r["declared_status"],
                "expected_status_given_context": r["flags"]["expected_status_given_context"],
                "facts_in_context": r["flags"]["facts_in_context"], "facts_total": r["flags"]["facts_total"],
                "final_class": r["judgments"]["final_class"],
            }
        result[tag] = per_q
    return result


def summarize(config, rows):
    summary = {"config_id": config["config_id"], "cells": len(rows), "by_model": {}, "paired": paired(rows, config),
               "rule": config["evaluation"]["forbidden_aggregation"]}
    for tag in config["runtime"]["model_order"]:
        per_model = {}
        for condition in config["conditions"]["order"]:
            per_model[condition] = {
                group: block([r for r in rows if r["model_tag"] == tag and r["condition"] == condition
                              and r["group"] == group], config)
                for group in common.GROUPS
            }
        summary["by_model"][tag] = per_model
    return summary


def _flat(prefix, value, out):
    if isinstance(value, dict) and "numerator" in value:
        out.append((prefix, value["numerator"], value["denominator"], value["rate"]))
    elif isinstance(value, dict):
        for key, inner in value.items():
            _flat(f"{prefix}.{key}" if prefix else key, inner, out)


def write_outputs(config, summary, out_dir):
    common.dump_json(out_dir / "summary.json", summary)
    with (out_dir / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["model", "condition", "group", "metric", "numerator", "denominator", "rate"])
        for tag, per_model in summary["by_model"].items():
            for condition, groups in per_model.items():
                for group, metrics in groups.items():
                    rows = []
                    _flat("", metrics, rows)
                    for metric, num, den, rate in rows:
                        writer.writerow([tag, condition, group, metric, num, den, rate])
    lines = ["# RQ4 / SC05 — sintesi", "", summary["rule"], ""]
    for tag, per_model in summary["by_model"].items():
        lines += [f"## {tag}", "", "| Condizione | Gruppo | Risposte | Formato errato | Stato atteso dato il contesto "
                  "| Fatti nel contesto | Revisionate |", "|---|---|---:|---:|---:|---:|---:|"]
        for condition, groups in per_model.items():
            for group, m in groups.items():
                f = lambda r: f"{r['numerator']}/{r['denominator']}"  # noqa: E731
                lines.append(f"| {condition} | {group} | {f(m['responses'])} | {f(m['format_error'])} | "
                             f"{f(m['status_matches_expected_given_context'])} | {f(m['evidence_facts_in_context'])} | "
                             f"{f(m['human_review']['reviewed'])} |")
        lines.append("")
    lines += ["I giudizi qualitativi non approvati restano «in attesa di revisione» e non entrano nei conteggi delle classi."]
    (out_dir / "SINTESI.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(config, out_root=common.REPO_ROOT):
    out_dir = common.stage_dir(config, STAGE, out_root)
    rows = common.read_jsonl(out_dir / "evaluations.jsonl")
    summary = summarize(config, rows)
    write_outputs(config, summary, out_dir)
    return summary


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    summary = run(common.load_config())
    print(f"Celle riepilogate: {summary['cells']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
