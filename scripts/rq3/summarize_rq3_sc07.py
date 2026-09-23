#!/usr/bin/env python3
"""Riepilogo di RQ3 / SC07: metriche, confronto appaiato, bootstrap per episodio.

Legge `evaluations.jsonl` (una riga per cella attesa, comprese quelle mancanti)
e produce, per condizione, ogni metrica con numeratore e denominatore
dichiarati. Il confronto e' appaiato per domanda: differenza in punti
percentuali `shared_interleaved - separated`. L'intervallo al 95% ricampiona
episodi interi (10.000 ripetizioni, seed della configurazione); le sei
domande di un episodio non sono osservazioni indipendenti. Nessun p-value.

Scrive in `results/rq3/sc07/v1/<split>/`:
  summary.json                 sempre
  summary.csv, SINTESI.md      per lo split `evaluation` (anche per
                               `development` con --all-outputs)

Uso:
    python3 scripts/rq3/summarize_rq3_sc07.py --split evaluation
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402

# metrica -> (regola del denominatore, filtro del denominatore, numeratore)
METRICS = {
    "exact_match": ("tutte le celle attese", lambda r: True, lambda r: r["exact_match"]),
    "evidence_reachable": ("tutte le celle attese", lambda r: True, lambda r: r["evidence_reachable"]),
    "retrieval_success": ("tutte le celle attese", lambda r: True, lambda r: r["retrieval_success"]),
    "missing_response": ("tutte le celle attese", lambda r: True, lambda r: r["response_status"] != "ok"),
    "format_error": ("celle con risposta", lambda r: r["response_status"] == "ok", lambda r: not r["format_ok"]),
    "null_answer": ("celle con formato valido", lambda r: r["format_ok"], lambda r: r["is_null"]),
    "null_despite_evidence": ("celle con formato valido ed evidenza recuperata",
                              lambda r: r["format_ok"] and r["retrieval_success"], lambda r: r["is_null"]),
    "supported_answer": ("celle con valore non null", lambda r: r["format_ok"] and not r["is_null"],
                         lambda r: bool(r["supported"])),
    "cross_activity_confusion": ("celle con valore non null errato",
                                 lambda r: r["format_ok"] and not r["is_null"] and not r["exact_match"],
                                 lambda r: bool(r["cross_activity_confusion"])),
    "cross_activity_confusion_all_cells": ("tutte le celle attese", lambda r: True,
                                           lambda r: bool(r["cross_activity_confusion"])),
}
BOOTSTRAP_METRICS = ("exact_match", "retrieval_success")


def rate(num, den):
    return num / den if den else None


def metric_counts(rows, metric):
    _, keep, numerator = METRICS[metric]
    subset = [r for r in rows if keep(r)]
    num = sum(1 for r in subset if numerator(r))
    return {"numerator": num, "denominator": len(subset), "rate": rate(num, len(subset))}


def contamination(rows):
    num = sum(r["contamination_count"] for r in rows)
    den = sum(r["retrieved_messages"] for r in rows)
    return {"numerator": num, "denominator": den, "rate": rate(num, den),
            "denominator_rule": "messaggi recuperati"}


def condition_block(rows, config):
    block = {}
    for metric, (rule, _, _) in METRICS.items():
        block[metric] = {**metric_counts(rows, metric), "denominator_rule": rule}
    block["context_contamination"] = contamination(rows)
    order = config["evaluation"]["error_attribution_order"]
    block["error_attribution"] = {c: sum(1 for r in rows if r["error_category"] == c) for c in order}
    block["cells"] = len(rows)
    return block


def breakdown(rows, key, config):
    result = {}
    for value in sorted({r[key] for r in rows}):
        subset = [r for r in rows if r[key] == value]
        result[value] = {
            condition: {
                "exact_match": metric_counts([r for r in subset if r["condition"] == condition], "exact_match"),
                "retrieval_success": metric_counts([r for r in subset if r["condition"] == condition], "retrieval_success"),
                "context_contamination": contamination([r for r in subset if r["condition"] == condition]),
            }
            for condition in config["conditions"]["order"]
        }
    return result


def paired_table(rows):
    by_q = defaultdict(dict)
    for r in rows:
        by_q[r["question_id"]][r["condition"]] = r["exact_match"]
    table = {"both_correct": 0, "only_separated": 0, "only_shared_interleaved": 0, "neither": 0}
    for pair in by_q.values():
        a, b = pair.get("separated", False), pair.get("shared_interleaved", False)
        key = ("both_correct" if a and b else "only_separated" if a else
               "only_shared_interleaved" if b else "neither")
        table[key] += 1
    table["pairs"] = len(by_q)
    return table


def bootstrap_draws(n_episodes, repetitions, seed):
    rng = random.Random(seed)
    return [[rng.randrange(n_episodes) for _ in range(n_episodes)] for _ in range(repetitions)]


def paired_bootstrap(rows, metric, draws, base="separated", other="shared_interleaved"):
    """Differenza `other - base` in punti percentuali, IC 95% per episodio."""
    _, keep, numerator = METRICS[metric]
    per_episode = defaultdict(lambda: {base: [0, 0], other: [0, 0]})
    for r in rows:
        if r["condition"] not in (base, other) or not keep(r):
            continue
        slot = per_episode[r["episode_id"]][r["condition"]]
        slot[0] += 1 if numerator(r) else 0
        slot[1] += 1
    episodes = sorted(per_episode)
    if not episodes:
        return None
    nb = [per_episode[e][base][0] for e in episodes]
    db = [per_episode[e][base][1] for e in episodes]
    no = [per_episode[e][other][0] for e in episodes]
    do = [per_episode[e][other][1] for e in episodes]
    if not sum(db) or not sum(do):
        return None
    point = (sum(no) / sum(do) - sum(nb) / sum(db)) * 100
    diffs = []
    for index in draws:
        dbs, dos = sum(db[i] for i in index), sum(do[i] for i in index)
        if not dbs or not dos:
            continue
        diffs.append((sum(no[i] for i in index) / dos - sum(nb[i] for i in index) / dbs) * 100)
    diffs.sort()
    return {
        "metric": metric,
        "effect_pp": point,
        "direction": f"{other} - {base}",
        "ci95_low_pp": diffs[int(0.025 * (len(diffs) - 1))] if diffs else None,
        "ci95_high_pp": diffs[int(0.975 * (len(diffs) - 1))] if diffs else None,
        "episodes": len(episodes),
        "valid_resamples": len(diffs),
    }


def generation_block(rows, config):
    """Chiamate reali, celle riusate e modello realmente usato."""
    present = [r for r in rows if r["response_status"] == "ok"]
    models = {}
    for r in present:
        models[r.get("model_used") or "?"] = models.get(r.get("model_used") or "?", 0) + 1
    return {
        "cells_with_response": len(present),
        "model_calls": sum(1 for r in present if r.get("generation_kind") == "model_call"),
        "reused_identical_prompt": sum(1 for r in present if r.get("generation_kind") == "reused_identical_prompt"),
        "model_used_counts": models,
        "cells_with_model_used_different_from_requested": sum(
            1 for r in present if r.get("model_used") != config["model"]["model_id"]),
        "note": "Le celle riusate hanno la stessa risposta di una cella con prompt identico e non sono chiamate aggiuntive.",
    }


def summarize(config, rows, split):
    comparison = config["evaluation"]["paired_comparison"]
    conditions = config["conditions"]["order"]
    episodes = sorted({r["episode_id"] for r in rows})
    draws = bootstrap_draws(len(episodes), comparison["bootstrap_repetitions"], comparison["bootstrap_seed"])
    # Le estrazioni sono indici sugli episodi ordinati: stesse estrazioni per ogni metrica.
    summary = {
        "config_id": config["config_id"],
        "split": split,
        "model": {k: config["model"].get(k) for k in ("display_name", "model_id", "access_channel")},
        "generation": generation_block(rows, config),
        "cells_expected": len(rows),
        "episodes": len(episodes),
        "by_condition": {c: condition_block([r for r in rows if r["condition"] == c], config) for c in conditions},
        "paired_exact_match": paired_table(rows),
        "paired_differences": {m: paired_bootstrap(rows, m, draws) for m in BOOTSTRAP_METRICS},
        "by_question_type": breakdown(rows, "question_type", config),
        "by_ecosystem": breakdown(rows, "ecosystem", config),
        "bootstrap": {"repetitions": comparison["bootstrap_repetitions"], "seed": comparison["bootstrap_seed"],
                      "unit": "episode", "p_values": False},
        "limits": config["scope"]["excluded_claims"],
    }
    return summary


def write_csv(path, summary):
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scope", "group", "condition", "metric", "numerator", "denominator", "rate"])
        for condition, block in summary["by_condition"].items():
            for metric, value in block.items():
                if isinstance(value, dict) and "numerator" in value:
                    writer.writerow(["overall", "all", condition, metric, value["numerator"],
                                     value["denominator"], value["rate"]])
        for scope in ("by_question_type", "by_ecosystem"):
            for group, per_condition in summary[scope].items():
                for condition, metrics in per_condition.items():
                    for metric, value in metrics.items():
                        writer.writerow([scope, group, condition, metric, value["numerator"],
                                         value["denominator"], value["rate"]])


def _pct(value):
    return "n/d" if value is None else f"{100 * value:.1f}%"


def write_markdown(path, summary):
    sep, shared = summary["by_condition"]["separated"], summary["by_condition"]["shared_interleaved"]
    lines = [
        f"# RQ3 / SC07 — sintesi ({summary['split']})",
        "",
        f"Modello: {summary['model']['display_name']} (`{summary['model']['model_id']}`, "
        f"{summary['model']['access_channel']}). Celle attese: {summary['cells_expected']}; "
        f"episodi: {summary['episodes']}.",
        "",
        "| Metrica | Memoria separata | Memoria condivisa | Denominatore |",
        "|---|---:|---:|---|",
    ]
    for metric in list(METRICS) + ["context_contamination"]:
        a, b = sep[metric], shared[metric]
        lines.append(f"| {metric} | {a['numerator']}/{a['denominator']} ({_pct(a['rate'])}) | "
                     f"{b['numerator']}/{b['denominator']} ({_pct(b['rate'])}) | {a['denominator_rule']} |")
    gen = summary["generation"]
    lines += ["", f"Chiamate reali: {gen['model_calls']}; celle con prompt identico riusato: "
              f"{gen['reused_identical_prompt']}; modelli usati: {gen['model_used_counts']}."]
    lines += ["", "## Confronto appaiato", ""]
    table = summary["paired_exact_match"]
    lines.append(f"Coppie: {table['pairs']}; entrambe corrette {table['both_correct']}, solo separata "
                 f"{table['only_separated']}, solo condivisa {table['only_shared_interleaved']}, "
                 f"nessuna {table['neither']}.")
    lines.append("")
    for metric, diff in summary["paired_differences"].items():
        if diff is None:
            continue
        low = "n/d" if diff["ci95_low_pp"] is None else f"{diff['ci95_low_pp']:+.1f}"
        high = "n/d" if diff["ci95_high_pp"] is None else f"{diff['ci95_high_pp']:+.1f}"
        lines.append(f"- {metric}: {diff['effect_pp']:+.1f} punti ({diff['direction']}), "
                     f"IC 95% bootstrap per episodio [{low}; {high}], {diff['episodes']} episodi.")
    lines += ["", "## Attribuzione degli errori", "",
              "| Categoria | Separata | Condivisa |", "|---|---:|---:|"]
    for category in sep["error_attribution"]:
        lines.append(f"| {category} | {sep['error_attribution'][category]} | {shared['error_attribution'][category]} |")
    lines += ["", "## Limiti", ""]
    lines += [f"- Non si dimostra: {claim}." for claim in summary["limits"]]
    lines += ["- Una sola generazione per cella: la variabilità stocastica del modello non è misurata.",
              "- Nessun p-value."]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(config, split, repo_root=common.REPO_ROOT, all_outputs=False):
    results = common.results_dir(config, split, repo_root)
    rows = common.read_jsonl(results / "evaluations.jsonl")
    summary = summarize(config, rows, split)
    common.dump_json(results / "summary.json", summary)
    if split == "evaluation" or all_outputs:
        write_csv(results / "summary.csv", summary)
        write_markdown(results / "SINTESI.md", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", required=True, choices=common.SPLITS)
    parser.add_argument("--all-outputs", action="store_true")
    args = parser.parse_args(argv)
    summary = run(common.load_config(), args.split, all_outputs=args.all_outputs)
    for condition, block in summary["by_condition"].items():
        em = block["exact_match"]
        print(f"{condition:<20} exact match {em['numerator']}/{em['denominator']} ({_pct(em['rate'])})")
    diff = summary["paired_differences"]["exact_match"]
    if diff:
        print(f"differenza {diff['direction']}: {diff['effect_pp']:+.1f} pp "
              f"[{diff['ci95_low_pp']:+.1f}; {diff['ci95_high_pp']:+.1f}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
