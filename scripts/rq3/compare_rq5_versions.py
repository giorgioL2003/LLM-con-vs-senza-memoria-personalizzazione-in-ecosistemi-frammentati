#!/usr/bin/env python3
"""Confronto fra due versioni della configurazione di RQ5 / SC06.

Legge le valutazioni gia' prodotte da `evaluate_rq5.py` per due versioni e le
mette a fianco, per modello. Non rilegge le risposte grezze, non le corregge e
non ricalcola nessun giudizio: conta soltanto righe gia' giudicate.

Oltre alle metriche del protocollo aggiunge una diagnosi mirata al motivo per
cui la v1.1 esiste: quante etichette composte sono state **divise, abbreviate o
private del prefisso**. La diagnosi e' descrittiva e resta fuori dalle metriche
congelate; si applica alla sola condizione sufficiente, dove esistono etichette
attese, e alle sole celle con output conforme.

Una etichetta attesa `E` non restituita si considera frammentata quando il
modello ha restituito un valore `V` che:

  - coincide con una delle parti di `E` separate da ` - ` (divisione o
    rimozione del prefisso), oppure
  - e' una sottostringa propria di `E` (abbreviazione).

Uso:
    python3 scripts/rq3/compare_rq5_versions.py \\
        --split development \\
        --config-a data/rq3/config/rq5_sc06_v1.json \\
        --config-b data/rq3/config/rq5_sc06_v1_1.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq5_common as common  # noqa: E402
import summarize_rq5 as summarizer  # noqa: E402


def label_fragmentation(rows):
    """Etichette composte divise, abbreviate o private del prefisso."""
    out = Counter()
    examples = []
    for row in rows:
        if row["condition"] != "sufficient" or not row["format_ok"]:
            continue
        expected = set(row["expected_values"])
        predicted = set(row["predicted_normalized"])
        extra = predicted - expected
        missing = expected - predicted
        hit = False
        for label in missing:
            parts = {part.strip() for part in label.split(" - ")} if " - " in label else set()
            for value in extra:
                if value in parts:
                    out["split_or_prefix_dropped"] += 1
                    hit = True
                    if len(examples) < 8:
                        examples.append({"model_tag": row["model_tag"],
                                         "expected": label,
                                         "returned": sorted(predicted)})
                elif value != label and value in label:
                    out["abbreviated"] += 1
                    hit = True
        if hit:
            out["cells"] += 1
    return out, examples


def composite_labels(rows):
    """Quante etichette attese contengono un prefisso seguito da trattino."""
    return sum(1 for row in rows if row["condition"] == "sufficient"
               for label in row["expected_values"] if " - " in label)


def timings(rows, model):
    durations = sorted(
        (row.get("ollama_metrics") or {}).get("total_duration", 0) / 1e9
        for row in rows
        if row["model_tag"] == model and row["response_status"] == "ok"
        and (row.get("ollama_metrics") or {}).get("total_duration")
    )
    speeds = sorted(
        (row["ollama_metrics"]["eval_count"] / (row["ollama_metrics"]["eval_duration"] / 1e9))
        for row in rows
        if row["model_tag"] == model
        and (row.get("ollama_metrics") or {}).get("eval_count")
        and (row.get("ollama_metrics") or {}).get("eval_duration")
    )
    if not durations:
        return {}
    return {
        "responses": len(durations),
        "median_seconds": statistics.median(durations),
        "p95_seconds": durations[int(0.95 * (len(durations) - 1))],
        "median_tokens_per_second": statistics.median(speeds) if speeds else None,
    }


def _rate(rows, model, metric, condition, family=None):
    subset = [
        row for row in rows
        if row["model_tag"] == model and row["condition"] == condition
        and (family is None or row["family"] == family)
        and summarizer.in_denominator(metric, row)
    ]
    numerator = summarizer.METRICS[metric][2]
    count = sum(1 for row in subset if numerator(row))
    return count, len(subset)


def collect(rows, models):
    out = {}
    for model in models:
        entry = {
            "exact_match_sufficient": _rate(rows, model, "exact_match", "sufficient"),
            "exact_match_sufficient_asset": _rate(
                rows, model, "exact_match", "sufficient", "asset"),
            "correct_abstention": _rate(rows, model, "correct_abstention", "insufficient"),
            "format_error_sufficient": _rate(rows, model, "format_error", "sufficient"),
            "format_error_insufficient": _rate(rows, model, "format_error", "insufficient"),
            "unsupported_sufficient": _rate(rows, model, "unsupported_value", "sufficient"),
            "unsupported_insufficient": _rate(
                rows, model, "unsupported_value", "insufficient"),
            "cross_case_sufficient": _rate(
                rows, model, "cross_case_intrusion", "sufficient"),
            "cross_case_insufficient": _rate(
                rows, model, "cross_case_intrusion", "insufficient"),
        }
        fragmentation, _examples = label_fragmentation(
            [row for row in rows if row["model_tag"] == model])
        entry["label_fragmentation"] = dict(fragmentation)
        entry["timings"] = timings(rows, model)
        out[model] = entry
    return out


LABELS = [
    ("exact_match_sufficient", "Exact Match (sufficiente)"),
    ("exact_match_sufficient_asset", "Exact Match famiglia asset"),
    ("correct_abstention", "Astensione corretta"),
    ("format_error_sufficient", "Errori di formato (suff.)"),
    ("format_error_insufficient", "Errori di formato (insuff.)"),
    ("unsupported_sufficient", "Valori non supportati (suff.)"),
    ("unsupported_insufficient", "Valori non supportati (insuff.)"),
    ("cross_case_sufficient", "Intrusioni fra casi (suff.)"),
    ("cross_case_insufficient", "Intrusioni fra casi (insuff.)"),
]


def _pct(pair):
    count, total = pair
    return f"{count}/{total}" + (f" ({count / total * 100:.1f}%)" if total else "")


def render(name_a, name_b, summary_a, summary_b, models, fragments):
    lines = [f"# RQ5 / SC06 — confronto {name_a} contro {name_b}", "",
             "Stessi dati, stesso split, stessi distrattori, stesso oracle. "
             "Cambia soltanto l'istruzione di sistema.", ""]
    for model in models:
        lines += [f"## {model}", "",
                  f"| Metrica | {name_a} | {name_b} |", "|---|---|---|"]
        for key, label in LABELS:
            lines.append(f"| {label} | {_pct(summary_a[model][key])} "
                         f"| {_pct(summary_b[model][key])} |")
        frag_a = summary_a[model]["label_fragmentation"]
        frag_b = summary_b[model]["label_fragmentation"]
        for key, label in (("split_or_prefix_dropped", "Etichette divise o senza prefisso"),
                           ("abbreviated", "Etichette abbreviate"),
                           ("cells", "Celle con almeno una frammentazione")):
            lines.append(f"| {label} | {frag_a.get(key, 0)} | {frag_b.get(key, 0)} |")
        time_a, time_b = summary_a[model]["timings"], summary_b[model]["timings"]

        def fmt(entry, field, digits=2):
            value = entry.get(field)
            return "n/d" if value is None else f"{value:.{digits}f}"

        lines += [
            f"| Tempo mediano (s) | {fmt(time_a, 'median_seconds')} "
            f"| {fmt(time_b, 'median_seconds')} |",
            f"| Tempo p95 (s) | {fmt(time_a, 'p95_seconds')} | {fmt(time_b, 'p95_seconds')} |",
            f"| Token/s mediani | {fmt(time_a, 'median_tokens_per_second', 1)} "
            f"| {fmt(time_b, 'median_tokens_per_second', 1)} |",
            f"| Risposte con tempi | {time_a.get('responses', 0)} "
            f"| {time_b.get('responses', 0)} |",
            "",
        ]
    if fragments:
        lines += ["## Esempi di frammentazione osservata", ""]
        for item in fragments:
            lines.append(f"- {item['version']} — {item['model_tag']}: atteso "
                         f"`{item['expected']}`, restituito `{item['returned']}`")
        lines.append("")
    lines += [
        "## Come leggere questo confronto",
        "",
        "- La v1.1 non cambia dataset, domande, distrattori, oracle, modelli, "
        "parametri, schema o metriche: l'unica differenza e' l'istruzione.",
        "- Lo scopo dichiarato della v1.1 e' togliere un'ambiguita' sul formato "
        "delle etichette, non far salire un punteggio.",
        "- Lo split di sviluppo e' 12 episodi: serve a controllare il "
        "meccanismo, non a stabilire un risultato.",
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", required=True, choices=common.SPLITS)
    parser.add_argument("--config-a", required=True)
    parser.add_argument("--config-b", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    config_a = common.load_config(args.config_a)
    config_b = common.load_config(args.config_b)
    models = [model["ollama_tag"] for model in config_a["models"]]
    if models != [model["ollama_tag"] for model in config_b["models"]]:
        raise SystemExit("le due configurazioni non usano gli stessi modelli")

    rows_a = common.read_jsonl(
        common.results_dir(config_a) / args.split / "evaluations.jsonl")
    rows_b = common.read_jsonl(
        common.results_dir(config_b) / args.split / "evaluations.jsonl")
    summary_a, summary_b = collect(rows_a, models), collect(rows_b, models)

    examples = []
    for name, rows in ((config_a["config_id"], rows_a), (config_b["config_id"], rows_b)):
        _counts, found = label_fragmentation(rows)
        for item in found[:4]:
            examples.append({"version": name, **item})

    text = render(config_a["config_id"], config_b["config_id"],
                  summary_a, summary_b, models, examples)
    out = Path(args.out) if args.out else (
        common.results_dir(config_b) / args.split / "CONFRONTO_VERSIONI.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    common.dump_json(out.with_suffix(".json"), {
        "split": args.split,
        "version_a": config_a["config_id"],
        "version_b": config_b["config_id"],
        "composite_expected_labels": {
            config_a["config_id"]: composite_labels(rows_a),
            config_b["config_id"]: composite_labels(rows_b),
        },
        "cells": {config_a["config_id"]: len(rows_a), config_b["config_id"]: len(rows_b)},
        config_a["config_id"]: summary_a,
        config_b["config_id"]: summary_b,
    })
    print(text)
    print(f"Scritti {out} e {out.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
