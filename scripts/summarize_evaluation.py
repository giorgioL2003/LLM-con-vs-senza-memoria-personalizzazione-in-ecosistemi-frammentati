#!/usr/bin/env python3
"""Calcolo deterministico delle metriche aggregate del pilot (step 2).

Legge le 56 annotazioni di `results/evaluation_pilot.jsonl`, le valida contro
il retrieval (`results/retrieval_pilot.jsonl`) e contro gli input di
generazione (`results/generation_inputs.jsonl`), quindi calcola le metriche
aggregate definite nella sezione 10 di `EXPERIMENT.md`.

Lo script non modifica scenari, oracle, input, risultati del retrieval,
risposte generate o classificazioni: legge soltanto. Non chiama modelli e non
esegue l'analisi causale dei fallimenti (sezione 11), che appartiene allo
step 3.

C0, C1 e C2 sono le sole condizioni sperimentali principali. `FULL_HISTORY`
resta un controllo diagnostico separato e non riceve metriche di retrieval.

Uso:
    python3 scripts/summarize_evaluation.py
    python3 scripts/summarize_evaluation.py --check    # valida senza scrivere

Codice di uscita: 0 se non ci sono errori, 1 altrimenti.
Solo libreria standard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EVALUATION_PATH = REPO_ROOT / "results" / "evaluation_pilot.jsonl"
RETRIEVAL_PATH = REPO_ROOT / "results" / "retrieval_pilot.jsonl"
GENERATION_INPUTS_PATH = REPO_ROOT / "results" / "generation_inputs.jsonl"

METRICS_JSON_PATH = REPO_ROOT / "results" / "metrics_pilot.json"
METRICS_MD_PATH = REPO_ROOT / "pilot" / "metrics_pilot.md"

# Condizioni sperimentali principali.
CONDITIONS = ("C0", "C1", "C2")
# Controllo diagnostico, non una quarta condizione.
DIAGNOSTIC_MODE = "FULL_HISTORY"
ALL_MODES = CONDITIONS + (DIAGNOSTIC_MODE,)

ANSWER_CLASSES = ("complete", "partial", "incorrect", "correct_abstention")
EXPECTED_BEHAVIORS = ("complete_answer", "abstention")

EXPECTED_TOTAL_ANNOTATIONS = 56
EXPECTED_ANNOTATIONS_PER_MODE = 14

# Tipi attesi dei campi usati per le metriche. `retrieval_success` e' l'unico
# campo che puo' valere null (evidenza non raggiungibile).
REQUIRED_FIELDS = {
    "scenario_id": str,
    "question_id": str,
    "mode": str,
    "reachable": bool,
    "expected_behavior": str,
    "answer_class": str,
    "obsolete_used": bool,
    "unsupported_claim": bool,
}

ROUNDING = 6


# --------------------------------------------------------------------------
# Lettura dei file
# --------------------------------------------------------------------------


def load_jsonl(path):
    """Legge un file JSONL e restituisce la lista dei record."""
    records = []
    with open(path, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError("%s riga %d: JSON non valido (%s)" % (path, number, exc))
    return records


def sha256_of(path):
    """Impronta del file di input, per rendere tracciabile il calcolo."""
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def key_of(record, mode_field="mode"):
    return (record.get("scenario_id"), record.get("question_id"), record.get(mode_field))


def label(key):
    return "%s/%s/%s" % key


# --------------------------------------------------------------------------
# Validazione
# --------------------------------------------------------------------------


def validate_rows(annotations):
    """Controlla campi, valori ammessi, duplicati e coerenza interna."""
    errors = []
    seen = set()

    for index, row in enumerate(annotations, start=1):
        if not isinstance(row, dict):
            errors.append("[E-FIELD] riga %d: il record non e' un oggetto JSON" % index)
            continue

        malformed = False
        for field, expected_type in sorted(REQUIRED_FIELDS.items()):
            if field not in row:
                errors.append("[E-FIELD] riga %d: campo mancante '%s'" % (index, field))
                malformed = True
            elif not isinstance(row[field], expected_type):
                errors.append(
                    "[E-FIELD] riga %d: campo '%s' di tipo %s, atteso %s"
                    % (index, field, type(row[field]).__name__, expected_type.__name__)
                )
                malformed = True
        if "retrieval_success" not in row:
            errors.append("[E-FIELD] riga %d: campo mancante 'retrieval_success'" % index)
            malformed = True
        elif row["retrieval_success"] is not None and not isinstance(row["retrieval_success"], bool):
            errors.append(
                "[E-FIELD] riga %d: 'retrieval_success' deve essere true, false o null" % index
            )
            malformed = True
        if malformed:
            continue

        key = key_of(row)
        if key in seen:
            errors.append("[E-DUP] %s: annotazione duplicata" % label(key))
        seen.add(key)

        if row["mode"] not in ALL_MODES:
            errors.append(
                "[E-VALUE] %s: modalita' sconosciuta '%s'" % (label(key), row["mode"])
            )
            continue
        if row["answer_class"] not in ANSWER_CLASSES:
            errors.append(
                "[E-VALUE] %s: answer_class sconosciuta '%s'" % (label(key), row["answer_class"])
            )
        if row["expected_behavior"] not in EXPECTED_BEHAVIORS:
            errors.append(
                "[E-VALUE] %s: expected_behavior sconosciuto '%s'"
                % (label(key), row["expected_behavior"])
            )

        # Sezione 9.2: il recupero e' definito soltanto se l'evidenza e'
        # raggiungibile nel perimetro della modalita'.
        if not row["reachable"] and row["retrieval_success"] is not None:
            errors.append(
                "[E-RETRIEVAL-NULL] %s: evidenza non raggiungibile, "
                "'retrieval_success' deve essere null" % label(key)
            )

        # FULL_HISTORY non applica la procedura di retrieval: e' un controllo
        # diagnostico e non puo' avere un esito di recupero.
        if row["mode"] == DIAGNOSTIC_MODE and row["retrieval_success"] is not None:
            errors.append(
                "[E-DIAGNOSTIC] %s: il controllo diagnostico non ha metriche di retrieval"
                % label(key)
            )

        # Sezione 9.3: l'astensione e' corretta solo se l'evidenza non e'
        # accessibile nella modalita' eseguita.
        if row["answer_class"] == "correct_abstention" and row["reachable"]:
            errors.append(
                "[E-ABSTENTION] %s: 'correct_abstention' con evidenza raggiungibile"
                % label(key)
            )

        expected = "abstention" if not row["reachable"] else "complete_answer"
        if row["expected_behavior"] in EXPECTED_BEHAVIORS and row["expected_behavior"] != expected:
            errors.append(
                "[E-EXPECTED] %s: expected_behavior '%s' incoerente con reachable=%s"
                % (label(key), row["expected_behavior"], row["reachable"])
            )

    return errors


def validate_totals(annotations):
    """Controlla che il pilot contenga esattamente 56 annotazioni, 14 per modalita'."""
    errors = []
    if len(annotations) != EXPECTED_TOTAL_ANNOTATIONS:
        errors.append(
            "[E-COUNT] attese %d annotazioni, trovate %d"
            % (EXPECTED_TOTAL_ANNOTATIONS, len(annotations))
        )
    for mode in ALL_MODES:
        found = sum(1 for row in annotations if row.get("mode") == mode)
        if found != EXPECTED_ANNOTATIONS_PER_MODE:
            errors.append(
                "[E-COUNT] modalita' %s: attese %d annotazioni, trovate %d"
                % (mode, EXPECTED_ANNOTATIONS_PER_MODE, found)
            )
    return errors


def validate_against_retrieval(annotations, retrieval):
    """Le annotazioni non possono contraddire i risultati del retrieval."""
    errors = []
    index = {key_of(row, "condition"): row for row in retrieval}
    for row in annotations:
        if row.get("mode") not in CONDITIONS:
            continue
        key = key_of(row)
        source = index.get(key)
        if source is None:
            errors.append("[E-RETRIEVAL-MISSING] %s: nessuna riga in retrieval_pilot.jsonl" % label(key))
            continue
        if source.get("reachable") != row.get("reachable"):
            errors.append(
                "[E-RETRIEVAL-MATCH] %s: reachable=%s nell'annotazione, %s nel retrieval"
                % (label(key), row.get("reachable"), source.get("reachable"))
            )
        if source.get("retrieval_success") != row.get("retrieval_success"):
            errors.append(
                "[E-RETRIEVAL-MATCH] %s: retrieval_success=%s nell'annotazione, %s nel retrieval"
                % (label(key), row.get("retrieval_success"), source.get("retrieval_success"))
            )
    return errors


def validate_against_inputs(annotations, generation_inputs):
    """Ogni annotazione deve corrispondere a una prova effettivamente eseguita."""
    errors = []
    index = {key_of(row): row for row in generation_inputs}
    for row in annotations:
        key = key_of(row)
        source = index.get(key)
        if source is None:
            errors.append("[E-INPUT-MISSING] %s: nessuna riga in generation_inputs.jsonl" % label(key))
            continue
        if source.get("reachable") != row.get("reachable"):
            errors.append(
                "[E-INPUT-MATCH] %s: reachable incoerente con generation_inputs.jsonl" % label(key)
            )
        if source.get("retrieval_success") != row.get("retrieval_success"):
            errors.append(
                "[E-INPUT-MATCH] %s: retrieval_success incoerente con generation_inputs.jsonl"
                % label(key)
            )
    missing = sorted(set(index) - {key_of(row) for row in annotations})
    for key in missing:
        errors.append("[E-INPUT-MISSING] %s: prova eseguita ma non annotata" % label(key))
    return errors


def validate_all(annotations, retrieval, generation_inputs):
    errors = validate_rows(annotations)
    errors.extend(validate_totals(annotations))
    errors.extend(validate_against_retrieval(annotations, retrieval))
    errors.extend(validate_against_inputs(annotations, generation_inputs))
    return errors


# --------------------------------------------------------------------------
# Metriche
# --------------------------------------------------------------------------


def ratio(numerator, denominator):
    """Metrica come numeratore/denominatore/valore.

    Con denominatore zero la metrica non e' calcolabile: il valore e' `null`,
    mai zero (EXPERIMENT.md, sezioni 10.2 e 10.4).
    """
    value = None if denominator == 0 else round(numerator / denominator, ROUNDING)
    return {"numerator": numerator, "denominator": denominator, "value": value}


def metrics_for(rows, with_retrieval_metrics=True):
    """Metriche aggregate di una modalita'.

    `with_retrieval_metrics=False` per il controllo diagnostico FULL_HISTORY,
    che non applica la procedura di retrieval.
    """
    total = len(rows)
    reachable = [row for row in rows if row["reachable"]]
    unreachable = [row for row in rows if not row["reachable"]]
    counts = {name: sum(1 for row in rows if row["answer_class"] == name) for name in ANSWER_CLASSES}

    summary = {
        "total_trials": total,
        "reachable_questions": len(reachable),
        "unreachable_questions": len(unreachable),
        "answer_class_counts": counts,
        "answer_class_proportions": {
            name: ratio(counts[name], total) for name in ANSWER_CLASSES
        },
        "reachability_rate": ratio(len(reachable), total),
        "complete_answer_rate": ratio(counts["complete"], total),
        "correct_abstention_rate": ratio(counts["correct_abstention"], len(unreachable)),
        "obsolete_information_use_rate": ratio(
            sum(1 for row in rows if row["obsolete_used"]), total
        ),
        "unsupported_claim_rate": ratio(
            sum(1 for row in rows if row["unsupported_claim"]), total
        ),
    }

    if with_retrieval_metrics:
        retrieved = [row for row in reachable if row["retrieval_success"] is True]
        summary["retrieval_success_rate"] = ratio(len(retrieved), len(reachable))
        summary["answer_success_rate"] = ratio(
            sum(1 for row in retrieved if row["answer_class"] == "complete"), len(retrieved)
        )

    return summary


def summarize(annotations):
    """Riepilogo completo: condizioni principali piu' controllo diagnostico."""
    by_mode = {mode: [row for row in annotations if row["mode"] == mode] for mode in ALL_MODES}
    return {
        "status": "risultati del pilot, non conclusioni finali",
        "scope": (
            "step 2 - metriche aggregate delle 56 annotazioni; "
            "l'analisi causale dei fallimenti (EXPERIMENT.md sezione 11) non e' inclusa"
        ),
        "definitions_reference": "EXPERIMENT.md, sezioni 9, 10 e 13",
        "sources": {},
        "totals": {
            "annotations": len(annotations),
            "questions": len(sorted({row["question_id"] for row in annotations})),
            "scenarios": len(sorted({row["scenario_id"] for row in annotations})),
        },
        "conditions": {mode: metrics_for(by_mode[mode]) for mode in CONDITIONS},
        "diagnostic": {
            "note": (
                "FULL_HISTORY e' un controllo diagnostico separato, non una quarta "
                "condizione sperimentale: non applica la procedura di retrieval e "
                "non ha metriche di retrieval."
            ),
            DIAGNOSTIC_MODE: metrics_for(by_mode[DIAGNOSTIC_MODE], with_retrieval_metrics=False),
        },
    }


# --------------------------------------------------------------------------
# Riepilogo leggibile
# --------------------------------------------------------------------------


def format_percent(metric):
    if metric["value"] is None:
        return "non calcolabile"
    return "%.1f%%" % (metric["value"] * 100)


def format_metric(metric):
    """`num / den = valore (percentuale)`, oppure la ragione della non calcolabilita'."""
    if metric["value"] is None:
        return "null - non calcolabile (denominatore 0)"
    return "%d / %d = %s (%s)" % (
        metric["numerator"],
        metric["denominator"],
        ("%.6f" % metric["value"]).rstrip("0").rstrip("."),
        format_percent(metric),
    )


METRIC_ROWS = (
    ("Reachability Rate", "reachability_rate", "domande raggiungibili / prove totali"),
    (
        "Retrieval Success Rate",
        "retrieval_success_rate",
        "evidenza completa recuperata / domande raggiungibili",
    ),
    ("Complete Answer Rate", "complete_answer_rate", "risposte complete / prove totali"),
    (
        "Answer Success Rate",
        "answer_success_rate",
        "risposte complete con evidenza recuperata / domande con evidenza recuperata",
    ),
    (
        "Correct Abstention Rate",
        "correct_abstention_rate",
        "astensioni corrette / domande non raggiungibili",
    ),
    (
        "Obsolete Information Use Rate",
        "obsolete_information_use_rate",
        "risposte che usano informazioni obsolete / prove totali",
    ),
    (
        "Unsupported Claim Rate",
        "unsupported_claim_rate",
        "risposte con almeno un fatto non supportato / prove totali",
    ),
)


def _mode_block(title, metrics):
    lines = ["### %s" % title, ""]
    lines.append("- prove totali: %d" % metrics["total_trials"])
    lines.append("- domande raggiungibili: %d" % metrics["reachable_questions"])
    lines.append("- domande non raggiungibili: %d" % metrics["unreachable_questions"])
    lines.append("")
    lines.append("| Classe della risposta | Conteggio | Proporzione |")
    lines.append("|---|---|---|")
    for name in ANSWER_CLASSES:
        proportion = metrics["answer_class_proportions"][name]
        lines.append(
            "| %s | %d | %s |"
            % (name, metrics["answer_class_counts"][name], format_metric(proportion))
        )
    lines.append("")
    lines.append("| Metrica | Formula | Numeratore / Denominatore | Valore |")
    lines.append("|---|---|---|---|")
    for name, field, formula in METRIC_ROWS:
        if field not in metrics:
            continue
        metric = metrics[field]
        fraction = "%d / %d" % (metric["numerator"], metric["denominator"])
        value_cell = "null (non calcolabile)" if metric["value"] is None else format_percent(metric)
        lines.append("| %s | %s | %s | %s |" % (name, formula, fraction, value_cell))
    lines.append("")
    return lines


def render_markdown(summary):
    lines = [
        "# Metriche aggregate del pilot",
        "",
        "**Stato:** risultati del pilot, non conclusioni finali.  ",
        "**Ambito:** step 2 - calcolo delle metriche a partire dalle %d annotazioni gia'"
        % summary["totals"]["annotations"],
        "classificate. L'analisi causale dei fallimenti (EXPERIMENT.md, sezione 11)"
        " non fa parte di questo documento.",
        "",
        "Documento generato da `scripts/summarize_evaluation.py`; il risultato"
        " machine-readable e' `results/metrics_pilot.json`.",
        "Le definizioni delle metriche sono quelle di EXPERIMENT.md, sezioni 9 e 10.",
        "",
        "## Avvertenza",
        "",
        "Questi numeri descrivono un pilot di %d domande su %d scenari."
        % (summary["totals"]["questions"], summary["totals"]["scenarios"]),
        "Il campione e' piccolo, le annotazioni sono una prima classificazione assistita",
        "dall'AI e l'esperimento non e' congelato: i valori servono a verificare che la",
        "pipeline misuri quello che deve misurare, non a sostenere conclusioni finali.",
        "",
        "Quando il denominatore di una metrica e' zero, la metrica non e' calcolabile:",
        "viene riportata come `null` e mai come zero (EXPERIMENT.md, sezioni 10.2 e 10.4).",
        "",
        "## Sorgenti",
        "",
        "| File | SHA-256 |",
        "|---|---|",
    ]
    for name, digest in sorted(summary["sources"].items()):
        lines.append("| `%s` | `%s` |" % (name, digest))
    lines.extend(
        [
            "",
            "## Condizioni sperimentali",
            "",
            "C0, C1 e C2 sono le sole condizioni sperimentali principali.",
            "",
        ]
    )

    for mode in CONDITIONS:
        lines.extend(_mode_block("Condizione %s" % mode, summary["conditions"][mode]))

    lines.extend(
        [
            "## Confronto sintetico tra le condizioni",
            "",
            "| Metrica | C0 | C1 | C2 |",
            "|---|---|---|---|",
        ]
    )
    for name, field, _formula in METRIC_ROWS:
        cells = []
        for mode in CONDITIONS:
            metric = summary["conditions"][mode][field]
            if metric["value"] is None:
                cells.append("null (%d / %d)" % (metric["numerator"], metric["denominator"]))
            else:
                cells.append(
                    "%s (%d / %d)"
                    % (format_percent(metric), metric["numerator"], metric["denominator"])
                )
        lines.append("| %s | %s |" % (name, " | ".join(cells)))

    diagnostic = summary["diagnostic"]
    lines.extend(
        [
            "",
            "## Sezione diagnostica separata: FULL_HISTORY",
            "",
            diagnostic["note"],
            "",
            "I valori qui sotto non vanno confrontati con C0, C1 e C2 come se fossero una",
            "quarta condizione: servono solo a osservare il comportamento del modello quando",
            "riceve l'intero storico senza selezione.",
            "",
        ]
    )
    lines.extend(_mode_block("Controllo %s" % DIAGNOSTIC_MODE, diagnostic[DIAGNOSTIC_MODE]))

    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def build_summary(evaluation_path, retrieval_path, inputs_path):
    """Valida gli input e restituisce (summary, errors). Non scrive nulla."""
    annotations = load_jsonl(evaluation_path)
    retrieval = load_jsonl(retrieval_path)
    generation_inputs = load_jsonl(inputs_path)

    errors = validate_all(annotations, retrieval, generation_inputs)
    if errors:
        return None, errors

    summary = summarize(annotations)
    summary["sources"] = {
        str(Path(path).relative_to(REPO_ROOT)): sha256_of(path)
        for path in (evaluation_path, retrieval_path, inputs_path)
    }
    return summary, []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="valida le annotazioni e calcola le metriche senza scrivere i file",
    )
    args = parser.parse_args(argv)

    summary, errors = build_summary(EVALUATION_PATH, RETRIEVAL_PATH, GENERATION_INPUTS_PATH)
    if errors:
        print("%d errore/i di validazione:" % len(errors))
        for error in errors:
            print("  - %s" % error)
        return 1

    print(
        "Validazione superata: %d annotazioni, %d domande, %d scenari."
        % (
            summary["totals"]["annotations"],
            summary["totals"]["questions"],
            summary["totals"]["scenarios"],
        )
    )
    for mode in CONDITIONS:
        metrics = summary["conditions"][mode]
        print(
            "  %-4s prove=%2d raggiungibili=%2d  reachability=%-14s retrieval=%-14s "
            "complete=%-14s answer=%s"
            % (
                mode,
                metrics["total_trials"],
                metrics["reachable_questions"],
                format_percent(metrics["reachability_rate"]),
                format_percent(metrics["retrieval_success_rate"]),
                format_percent(metrics["complete_answer_rate"]),
                format_percent(metrics["answer_success_rate"]),
            )
        )
    diagnostic = summary["diagnostic"][DIAGNOSTIC_MODE]
    print(
        "  %-4s (diagnostico, senza metriche di retrieval) prove=%2d complete=%s"
        % (DIAGNOSTIC_MODE, diagnostic["total_trials"], format_percent(diagnostic["complete_answer_rate"]))
    )

    if args.check:
        print("\n--check: nessun file scritto.")
        return 0

    METRICS_JSON_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    METRICS_MD_PATH.write_text(render_markdown(summary), encoding="utf-8")
    print(
        "\nScritti:\n  %s\n  %s"
        % (
            METRICS_JSON_PATH.relative_to(REPO_ROOT),
            METRICS_MD_PATH.relative_to(REPO_ROOT),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
