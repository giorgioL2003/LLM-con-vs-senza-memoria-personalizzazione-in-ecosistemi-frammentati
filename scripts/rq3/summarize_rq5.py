#!/usr/bin/env python3
"""Riepilogo dei risultati di RQ5 / SC06.

Legge `evaluations.jsonl` e non lo modifica: qui non si giudica nulla, si
contano soltanto righe gia' giudicate.

Produce, sempre separati per modello, condizione e famiglia di domanda:

  - Exact Match nella condizione sufficiente;
  - Correct Abstention nella condizione insufficiente;
  - precisione e richiamo delle etichette (solo sufficiente);
  - valori non supportati, confusione fra casi, errori di formato;
  - numeratore e denominatore di ogni tasso, con la regola del denominatore.

Il confronto fra i due modelli e' appaiato e usa il bootstrap per episodio
dichiarato nella configurazione: 10.000 ricampionamenti di interi episodi con
seme 20260922, differenza assoluta in punti percentuali, intervallo al 95%.
Le nove domande dello stesso episodio non sono repliche indipendenti e non
vengono ricampionate singolarmente. Non vengono calcolati p-value.

Sufficiente e insufficiente non vengono fusi in un unico punteggio e SC06 non
viene mediato con SC01-SC05.

Uso:
    python3 scripts/rq3/summarize_rq5.py --split evaluation
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import random
import statistics
import sys
from array import array
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq5_common as common  # noqa: E402

ALL_FAMILIES = "tutte"

# metrica -> (condizione, regola del denominatore, funzione numeratore)
METRICS = {
    "exact_match": (
        "sufficient", "celle attese",
        lambda row: bool(row.get("exact_match")),
    ),
    "correct_abstention": (
        "insufficient", "celle attese",
        lambda row: bool(row.get("correct_abstention")),
    ),
    "format_error": (
        None, "celle attese",
        lambda row: bool(row.get("format_error")),
    ),
    "unsupported_value": (
        None, "celle con output conforme",
        lambda row: bool(row.get("has_unsupported_value")),
    ),
    "cross_case_intrusion": (
        None, "celle con output conforme e confusione rilevabile",
        lambda row: bool(row.get("cross_case_intrusion")),
    ),
}

PRIMARY = ("exact_match", "correct_abstention")


def in_denominator(metric, row):
    """Quali celle entrano nel denominatore di una metrica."""
    condition = METRICS[metric][0]
    if condition and row["condition"] != condition:
        return False
    if metric in ("exact_match", "correct_abstention", "format_error"):
        return True
    if metric == "unsupported_value":
        return bool(row["format_ok"])
    if metric == "cross_case_intrusion":
        return bool(row["format_ok"]) and bool(row["cross_case_detectable"])
    return False


def rate_table(rows, models):
    """Tassi per (modello, condizione, famiglia, metrica)."""
    table = []
    families = sorted({row["family"] for row in rows})
    for model in models:
        for condition in common.CONDITIONS:
            for family in [ALL_FAMILIES] + families:
                subset = [
                    row for row in rows
                    if row["model_tag"] == model and row["condition"] == condition
                    and (family == ALL_FAMILIES or row["family"] == family)
                ]
                for metric, (metric_condition, rule, numerator) in METRICS.items():
                    if metric_condition and metric_condition != condition:
                        continue
                    denominator = [row for row in subset if in_denominator(metric, row)]
                    count = sum(1 for row in denominator if numerator(row))
                    table.append({
                        "model_tag": model,
                        "condition": condition,
                        "family": family,
                        "metric": metric,
                        "numerator": count,
                        "denominator": len(denominator),
                        "rate": (count / len(denominator)) if denominator else None,
                        "denominator_rule": rule,
                    })
                if condition == "sufficient":
                    table += _label_scores(subset, model, condition, family)
    return table


def _label_scores(subset, model, condition, family):
    """Precisione e richiamo micro, sulle sole celle con output conforme."""
    parsed = [row for row in subset if row["format_ok"]]
    tp = sum(row["true_positives"] or 0 for row in parsed)
    fp = sum(row["false_positives"] or 0 for row in parsed)
    fn = sum(row["false_negatives"] or 0 for row in parsed)
    rows = []
    for metric, count, total in (
        ("label_precision", tp, tp + fp),
        ("label_recall", tp, tp + fn),
    ):
        rows.append({
            "model_tag": model, "condition": condition, "family": family,
            "metric": metric, "numerator": count, "denominator": total,
            "rate": (count / total) if total else None,
            "denominator_rule": "etichette, celle con output conforme",
        })
    return rows


# --------------------------------------------------------------------------
# Bootstrap appaiato per episodio
# --------------------------------------------------------------------------

def _draws(episode_count, repetitions, seed):
    rng = random.Random(seed)
    return [
        array("H", [rng.randrange(episode_count) for _ in range(episode_count)])
        for _ in range(repetitions)
    ]


def paired_bootstrap(rows, metric, model_a, model_b, repetitions, seed, draws=None):
    """Differenza in punti percentuali fra due modelli, con intervallo al 95%.

    L'unita' di ricampionamento e' l'episodio: si estraggono episodi interi,
    con reimmissione, e si ricalcolano i due tassi su tutte le loro celle.
    """
    per_episode = defaultdict(lambda: {model_a: [0, 0], model_b: [0, 0]})
    numerator = METRICS[metric][2]
    for row in rows:
        if row["model_tag"] not in (model_a, model_b):
            continue
        if not in_denominator(metric, row):
            continue
        slot = per_episode[row["episode_id"]][row["model_tag"]]
        slot[0] += 1 if numerator(row) else 0
        slot[1] += 1

    episodes = sorted(per_episode)
    if not episodes:
        return None
    num_a = array("l", [per_episode[e][model_a][0] for e in episodes])
    den_a = array("l", [per_episode[e][model_a][1] for e in episodes])
    num_b = array("l", [per_episode[e][model_b][0] for e in episodes])
    den_b = array("l", [per_episode[e][model_b][1] for e in episodes])

    total_a, total_b = sum(den_a), sum(den_b)
    if not total_a or not total_b:
        return None
    point = (sum(num_a) / total_a - sum(num_b) / total_b) * 100

    if draws is None:
        draws = _draws(len(episodes), repetitions, seed)
    differences = []
    for index in draws:
        da = sum(map(den_a.__getitem__, index))
        db = sum(map(den_b.__getitem__, index))
        if not da or not db:
            continue
        differences.append(
            (sum(map(num_a.__getitem__, index)) / da
             - sum(map(num_b.__getitem__, index)) / db) * 100
        )
    differences.sort()
    low = differences[int(0.025 * (len(differences) - 1))]
    high = differences[int(0.975 * (len(differences) - 1))]
    return {
        "metric": metric,
        "model_a": model_a,
        "model_b": model_b,
        "effect_pp": point,
        "ci95_low_pp": low,
        "ci95_high_pp": high,
        "episodes_resampled": len(episodes),
        "repetitions": len(differences),
        "seed": seed,
        "unit": "episodio",
        "p_values": False,
    }


# --------------------------------------------------------------------------
# Prestazioni locali
# --------------------------------------------------------------------------

def performance(rows, models):
    out = []
    for model in models:
        durations, speeds = [], []
        for row in rows:
            if row["model_tag"] != model:
                continue
            metrics = row.get("ollama_metrics") or {}
            total = metrics.get("total_duration")
            if row["response_status"] == "ok" and total:
                durations.append(total / 1e9)
            count, elapsed = metrics.get("eval_count"), metrics.get("eval_duration")
            if count and elapsed:
                speeds.append(count / (elapsed / 1e9))
        entry = {
            "model_tag": model,
            "responses_with_timing": len(durations),
            "median_total_seconds": statistics.median(durations) if durations else None,
            "p95_total_seconds": (
                sorted(durations)[min(int(0.95 * (len(durations) - 1)), len(durations) - 1)]
                if durations else None
            ),
            "median_tokens_per_second": statistics.median(speeds) if speeds else None,
            "warmup_excluded": True,
            "note": "risultato secondario ed esplorativo",
        }
        out.append(entry)
    return out


# --------------------------------------------------------------------------
# Uscite
# --------------------------------------------------------------------------

def write_csv(path, split, table):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["split", "model_tag", "condition", "family", "metric",
              "numerator", "denominator", "rate", "denominator_rule"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in table:
            writer.writerow({"split": split, **{k: row[k] for k in fields[1:]}})


def _percent(value):
    return "n/d" if value is None else f"{value * 100:.1f}%"


def write_markdown(path, split, config, table, bootstrap, timings, counts):
    models = [model["ollama_tag"] for model in config["models"]]
    names = {m["ollama_tag"]: m["display_name"] for m in config["models"]}
    lines = [
        f"# RQ5 / SC06 — sintesi ({split})",
        "",
        f"Configurazione `{config['config_id']}`. "
        f"Celle attese: {counts['expected']}; con risposta: {counts['ok']}; "
        f"errori di formato: {counts['format_error']}; mancanti: {counts['missing']}.",
        "",
        "Le due condizioni restano separate: non esiste un punteggio unico di SC06 "
        "e SC06 non viene mediato con SC01-SC05.",
        "",
        "## Metriche principali",
        "",
        "| Condizione | Metrica | Modello | Tasso | Numeratore | Denominatore |",
        "|---|---|---|---:|---:|---:|",
    ]
    for metric in PRIMARY:
        condition = METRICS[metric][0]
        for model in models:
            row = next(
                (r for r in table if r["metric"] == metric and r["model_tag"] == model
                 and r["family"] == ALL_FAMILIES and r["condition"] == condition), None
            )
            if row:
                lines.append(
                    f"| {condition} | {metric} | {names[model]} | {_percent(row['rate'])} "
                    f"| {row['numerator']} | {row['denominator']} |"
                )
    lines += ["", "## Confronto appaiato fra i due modelli", ""]
    if bootstrap:
        lines += [
            f"Differenza assoluta in punti percentuali, {names[models[0]]} meno "
            f"{names[models[1]]}. Intervallo al 95% da bootstrap di "
            f"{config['evaluation']['paired_comparison']['bootstrap_repetitions']} "
            "campioni di episodi interi; nessun p-value.",
            "",
            "| Condizione | Metrica | Famiglia | Differenza (pp) | IC 95% |",
            "|---|---|---|---:|---|",
        ]
        for entry in bootstrap:
            lines.append(
                f"| {entry['condition']} | {entry['metric']} | {entry['family']} "
                f"| {entry['effect_pp']:+.1f} "
                f"| [{entry['ci95_low_pp']:+.1f}, {entry['ci95_high_pp']:+.1f}] |"
            )
    else:
        lines.append("Nessun confronto calcolabile: mancano risposte per un modello.")

    lines += ["", "## Metriche secondarie", "",
              "| Condizione | Metrica | Modello | Tasso | Num. | Den. | Denominatore |",
              "|---|---|---|---:|---:|---:|---|"]
    for row in table:
        if row["family"] != ALL_FAMILIES or row["metric"] in PRIMARY:
            continue
        lines.append(
            f"| {row['condition']} | {row['metric']} | {names[row['model_tag']]} "
            f"| {_percent(row['rate'])} | {row['numerator']} | {row['denominator']} "
            f"| {row['denominator_rule']} |"
        )

    lines += ["", "## Prestazioni locali", "",
              "Risultato secondario ed esplorativo; il riscaldamento e' escluso.",
              "",
              "| Modello | Mediana (s) | 95º percentile (s) | Token/s (mediana) | Risposte |",
              "|---|---:|---:|---:|---:|"]
    for entry in timings:
        def fmt(value, digits=2):
            return "n/d" if value is None else f"{value:.{digits}f}"
        lines.append(
            f"| {names[entry['model_tag']]} | {fmt(entry['median_total_seconds'])} "
            f"| {fmt(entry['p95_total_seconds'])} "
            f"| {fmt(entry['median_tokens_per_second'], 1)} "
            f"| {entry['responses_with_timing']} |"
        )

    lines += [
        "",
        "## Limiti dichiarati",
        "",
        "- Il confronto riguarda due copie quantizzate eseguite in locale, non le "
        "famiglie Gemma e Llama in generale.",
        "- Una generazione deterministica per cella non e' una replica stocastica.",
        "- La confusione fra casi e' riportata solo sul sottoinsieme in cui e' "
        "rilevabile; le altre domande non dimostrano la sua assenza.",
        "- `size_vram` di Ollama e' un'allocazione dichiarata dal runtime, non il "
        "picco di RAM misurato.",
        "- Tokenizzazione e template interni restano propri di ogni modello.",
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", required=True, choices=common.SPLITS)
    parser.add_argument("--config", default=str(common.CONFIG_PATH))
    parser.add_argument("--results-dir", default=None,
                        help="predefinita: la directory della versione in configurazione")
    parser.add_argument("--evaluations", default=None)
    parser.add_argument("--no-bootstrap", action="store_true",
                        help="salta il confronto appaiato (controlli rapidi)")
    args = parser.parse_args(argv)

    config = common.load_config(args.config)
    results_dir = (Path(args.results_dir) if args.results_dir
                   else common.results_dir(config)) / args.split
    evaluations_path = Path(args.evaluations) if args.evaluations else (
        results_dir / "evaluations.jsonl"
    )
    rows = common.read_jsonl(evaluations_path)
    models = [model["ollama_tag"] for model in config["models"]]

    counts = {
        "expected": len(rows),
        "ok": sum(1 for row in rows if row["response_status"] == "ok"),
        "format_error": sum(1 for row in rows if row["format_error"]),
        "missing": sum(1 for row in rows if row["response_status"] == "missing"),
    }
    table = rate_table(rows, models)

    paired = config["evaluation"]["paired_comparison"]
    bootstrap = []
    if not args.no_bootstrap and len(models) == 2:
        families = sorted({row["family"] for row in rows})
        episode_count = len({row["episode_id"] for row in rows})
        draws = _draws(
            episode_count, paired["bootstrap_repetitions"], paired["bootstrap_seed"]
        ) if episode_count else []
        for metric in PRIMARY:
            condition = METRICS[metric][0]
            for family in [ALL_FAMILIES] + families:
                subset = [
                    row for row in rows
                    if row["condition"] == condition
                    and (family == ALL_FAMILIES or row["family"] == family)
                ]
                entry = paired_bootstrap(
                    subset, metric, models[0], models[1],
                    paired["bootstrap_repetitions"], paired["bootstrap_seed"],
                    draws if family == ALL_FAMILIES else None,
                )
                if entry:
                    entry.update({"condition": condition, "family": family})
                    bootstrap.append(entry)

    timings = performance(rows, models)
    summary = {
        "config_id": config["config_id"],
        "split": args.split,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "models": config["models"],
        "counts": counts,
        "metrics": table,
        "paired_bootstrap": bootstrap,
        "performance": timings,
        "judge_model_used": False,
        "forbidden_aggregation": config["evaluation"]["forbidden_aggregation"],
        "independence_rule": config["evaluation"]["independence_rule"],
    }
    common.dump_json(results_dir / "summary.json", summary)
    write_csv(results_dir / "summary.csv", args.split, table)
    write_markdown(results_dir / "SINTESI.md", args.split, config, table, bootstrap,
                   timings, counts)

    print(f"celle valutate: {counts['expected']} (con risposta {counts['ok']})")
    for metric in PRIMARY:
        for model in models:
            row = next(
                (r for r in table if r["metric"] == metric and r["model_tag"] == model
                 and r["family"] == ALL_FAMILIES), None
            )
            if row:
                print(f"  {metric:20s} {model:14s} {_percent(row['rate'])} "
                      f"({row['numerator']}/{row['denominator']})")
    print(f"Scritti summary.json, summary.csv e SINTESI.md in {results_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
