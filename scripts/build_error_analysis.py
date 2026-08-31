#!/usr/bin/env python3
"""Analisi causale dei due fallimenti del pilot (step 3).

Ricostruisce, per i due casi gia' approvati dallo studente, la traccia completa
che va dal perimetro della memoria fino alla risposta del modello, e le associa
la prima causa osservabile nella pipeline (EXPERIMENT.md, sezione 11).

Le tracce sono estratte dai file gia' esistenti; le sole informazioni dichiarate
a mano sono le cause approvate e la motivazione finale, raccolte in
`APPROVED_CASES`. Lo script controlla poi che quelle dichiarazioni siano
coerenti con le tracce: non puo' inventare una causa che i dati non mostrano.

Lo script legge soltanto. Non modifica scenari, oracle, retrieval, input,
risposte generate, classificazioni o metriche dello step 2; non chiama modelli
e non ricalcola le metriche.

FULL_HISTORY resta un controllo diagnostico: non compare mai come condizione di
un caso, ma solo nel campo `diagnostic_reference` di SC02-Q6/C2.

Uso:
    python3 scripts/build_error_analysis.py
    python3 scripts/build_error_analysis.py --check    # valida senza scrivere

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

SCENARIO_DIR = REPO_ROOT / "data" / "scenarios"
RETRIEVAL_PATH = REPO_ROOT / "results" / "retrieval_pilot.jsonl"
GENERATION_INPUTS_PATH = REPO_ROOT / "results" / "generation_inputs.jsonl"
GENERATION_PATH = REPO_ROOT / "results" / "generation_pilot.jsonl"
EVALUATION_PATH = REPO_ROOT / "results" / "evaluation_pilot.jsonl"

ANALYSIS_JSONL_PATH = REPO_ROOT / "results" / "error_analysis_pilot.jsonl"
ANALYSIS_MD_PATH = REPO_ROOT / "pilot" / "error_analysis_pilot.md"

# Condizioni sperimentali principali. FULL_HISTORY non e' una condizione.
CONDITIONS = ("C0", "C1", "C2")
DIAGNOSTIC_MODE = "FULL_HISTORY"

# Vocabolario delle cause: EXPERIMENT.md, sezione 11, riportato nel campo
# `error_origin` della sezione 13.
CAUSES = {
    "reachability": "evidenza irraggiungibile: il perimetro della condizione non contiene le informazioni necessarie",
    "retrieval": "evidenza raggiungibile ma non recuperata: fallimento del retrieval o del ranking",
    "answer": "evidenza recuperata ma risposta non corretta: fallimento di lettura, ragionamento o generazione",
    "benchmark": "domanda o oracle difettosi: ambiguita' o errore nel benchmark",
}

# Ordine della pipeline: la causa principale e' la prima che si osserva.
CAUSE_ORDER = ("reachability", "retrieval", "answer", "benchmark")


# --------------------------------------------------------------------------
# Casi approvati dallo studente
#
# Cause e motivazione sono decisioni umane e non sono deducibili dai file:
# vengono dichiarate qui e poi verificate contro le tracce estratte.
# --------------------------------------------------------------------------

APPROVED_CASES = (
    {
        "case_id": "SC02-Q6/C1",
        "scenario_id": "scenario_02",
        "question_id": "SC02-Q6",
        "condition": "C1",
        "primary_cause": "reachability",
        "secondary_cause": "answer",
        "secondary_cause_description": (
            "comportamento di risposta scorretto: il modello non si e' astenuto "
            "nonostante il contesto fosse insufficiente"
        ),
        "benchmark_defect": False,
        "rationale": (
            "In C1 il perimetro contiene la sola Sessione 4: la regola dei 15 minuti, "
            "fissata in Sessione 2, non e' accessibile. La prima causa osservabile e' "
            "quindi il perimetro della memoria. A questa si aggiunge una causa "
            "secondaria di risposta: le istruzioni chiedevano di dichiarare "
            "l'insufficienza del contesto, ma il modello ha risposto ugualmente, "
            "reinterpretando il test pendente come una verifica della consegna "
            "dell'email e del tempo di arrivo. Nessuno dei due elementi compare "
            "nell'evidenza accessibile: da qui `unsupported_claim: true`. La domanda "
            "e l'oracle sono corretti e non richiedono modifiche."
        ),
        "use_diagnostic_reference": False,
    },
    {
        "case_id": "SC02-Q6/C2",
        "scenario_id": "scenario_02",
        "question_id": "SC02-Q6",
        "condition": "C2",
        "primary_cause": "retrieval",
        "secondary_cause": None,
        "secondary_cause_description": None,
        "benchmark_defect": False,
        "rationale": (
            "In C2 tutte e quattro le sessioni sono accessibili e l'evidenza completa "
            "e' raggiungibile. Con `top_k=2` il retrieval ha selezionato SC02-S4-U1 e "
            "SC02-S3-U1, lasciando fuori SC02-S2-U1, l'unico messaggio che enuncia la "
            "regola dei 15 minuti. SC02-S3-U1 rinvia al limite senza ripeterlo "
            "(\"il limite di validita' stabilito nella sessione precedente\"), quindi il "
            "contesto recuperato non permetteva di indicare il numero. La risposta "
            "riconosce il collegamento con l'email consegnata in ritardo ma omette il "
            "rifiuto del link e il limite numerico: e' parziale, non inventata. La "
            "prima causa osservabile e' il ranking del retrieval e non esiste una "
            "causa secondaria di risposta."
        ),
        "use_diagnostic_reference": True,
    },
)


# --------------------------------------------------------------------------
# Lettura dei file
# --------------------------------------------------------------------------


def load_jsonl(path):
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
    digest = hashlib.sha256()
    digest.update(Path(path).read_bytes())
    return digest.hexdigest()


def load_question(scenario_id, question_id):
    """Domanda e oracle, letti dallo scenario senza modificarlo."""
    scenario = json.loads((SCENARIO_DIR / ("%s.json" % scenario_id)).read_text(encoding="utf-8"))
    for question in scenario["questions"]:
        if question["question_id"] == question_id:
            return question
    raise KeyError("domanda %s assente da %s" % (question_id, scenario_id))


def find(records, mode_field, scenario_id, question_id, mode):
    for record in records:
        if (
            record.get("scenario_id") == scenario_id
            and record.get("question_id") == question_id
            and record.get(mode_field) == mode
        ):
            return record
    return None


# --------------------------------------------------------------------------
# Costruzione della traccia
# --------------------------------------------------------------------------


def build_case(case, sources):
    """Unisce la dichiarazione approvata con la traccia estratta dai file."""
    scenario_id = case["scenario_id"]
    question_id = case["question_id"]
    condition = case["condition"]

    question = load_question(scenario_id, question_id)
    retrieval = find(sources["retrieval"], "condition", scenario_id, question_id, condition)
    generation = find(sources["generation"], "mode", scenario_id, question_id, condition)
    evaluation = find(sources["evaluation"], "mode", scenario_id, question_id, condition)
    inputs = find(sources["inputs"], "mode", scenario_id, question_id, condition)

    if retrieval is None or generation is None or evaluation is None or inputs is None:
        raise KeyError("traccia incompleta per %s" % case["case_id"])

    required = list(retrieval["required_evidence_ids"])
    accessible = list(retrieval["accessible_message_ids"])
    retrieved = list(retrieval["retrieved_message_ids"])

    # Le due forme di evidenza mancante corrispondono alle prime due cause
    # della sezione 11 e servono a verificare la causa dichiarata.
    unreachable_evidence = [e for e in required if e not in accessible]
    not_retrieved_evidence = [e for e in required if e in accessible and e not in retrieved]

    row = {
        "case_id": case["case_id"],
        "scenario_id": scenario_id,
        "question_id": question_id,
        "condition": condition,
        "question_text": question["text"],
        "expected_answer": question["expected_answer"],
        "reachable": retrieval["reachable"],
        "retrieval_success": retrieval["retrieval_success"],
        "accessible_message_ids": accessible,
        "retrieved_message_ids": retrieved,
        "retrieval_scores": retrieval["retrieval_scores"],
        "top_k": retrieval["top_k"],
        "required_evidence_ids": required,
        "unreachable_evidence_ids": unreachable_evidence,
        "not_retrieved_evidence_ids": not_retrieved_evidence,
        "mandatory_facts": list(question["mandatory_facts"]),
        "missing_mandatory_facts": list(evaluation["missing_mandatory_facts"]),
        "model_answer": generation["model_answer"],
        "expected_behavior": evaluation["expected_behavior"],
        "answer_class": evaluation["answer_class"],
        "obsolete_used": evaluation["obsolete_used"],
        "unsupported_claim": evaluation["unsupported_claim"],
        "primary_cause": case["primary_cause"],
        "primary_cause_description": CAUSES[case["primary_cause"]],
        "secondary_cause": case["secondary_cause"],
        "secondary_cause_description": case["secondary_cause_description"],
        "benchmark_defect": case["benchmark_defect"],
        "rationale": case["rationale"],
        "diagnostic_reference": None,
    }

    if case["use_diagnostic_reference"]:
        diagnostic_generation = find(
            sources["generation"], "mode", scenario_id, question_id, DIAGNOSTIC_MODE
        )
        diagnostic_evaluation = find(
            sources["evaluation"], "mode", scenario_id, question_id, DIAGNOSTIC_MODE
        )
        diagnostic_inputs = find(
            sources["inputs"], "mode", scenario_id, question_id, DIAGNOSTIC_MODE
        )
        row["diagnostic_reference"] = {
            "mode": DIAGNOSTIC_MODE,
            "note": (
                "Controllo diagnostico, non una condizione sperimentale: mostra che con "
                "tutta l'evidenza nel contesto il modello risponde in modo completo, "
                "quindi il fallimento di C2 non e' un fallimento di generazione."
            ),
            "context_message_ids": list(diagnostic_inputs["context_message_ids"]),
            "model_answer": diagnostic_generation["model_answer"],
            "answer_class": diagnostic_evaluation["answer_class"],
        }

    return row


# --------------------------------------------------------------------------
# Validazione
# --------------------------------------------------------------------------


def validate_case(row):
    """Le cause dichiarate devono essere sostenute dalla traccia estratta."""
    errors = []
    case_id = row["case_id"]

    if row["condition"] not in CONDITIONS:
        errors.append(
            "[E-CONDITION] %s: '%s' non e' una condizione sperimentale (%s e' diagnostico)"
            % (case_id, row["condition"], DIAGNOSTIC_MODE)
        )

    if row["primary_cause"] not in CAUSES:
        errors.append("[E-CAUSE] %s: causa principale sconosciuta '%s'" % (case_id, row["primary_cause"]))
        return errors
    if row["secondary_cause"] is not None and row["secondary_cause"] not in CAUSES:
        errors.append(
            "[E-CAUSE] %s: causa secondaria sconosciuta '%s'" % (case_id, row["secondary_cause"])
        )
    if row["secondary_cause"] == row["primary_cause"]:
        errors.append("[E-CAUSE] %s: causa secondaria uguale alla principale" % case_id)

    extra = [e for e in row["retrieved_message_ids"] if e not in row["accessible_message_ids"]]
    if extra:
        errors.append(
            "[E-TRACE] %s: messaggi recuperati fuori dal perimetro: %s" % (case_id, ", ".join(extra))
        )

    # La causa principale e' la prima osservabile nella pipeline.
    if row["primary_cause"] == "reachability":
        if row["reachable"]:
            errors.append(
                "[E-CAUSE-EVIDENCE] %s: causa 'reachability' ma l'evidenza e' raggiungibile" % case_id
            )
        if not row["unreachable_evidence_ids"]:
            errors.append(
                "[E-CAUSE-EVIDENCE] %s: causa 'reachability' senza evidenze fuori dal perimetro"
                % case_id
            )
    elif row["primary_cause"] == "retrieval":
        if not row["reachable"]:
            errors.append(
                "[E-CAUSE-EVIDENCE] %s: causa 'retrieval' ma l'evidenza non e' raggiungibile" % case_id
            )
        if not row["not_retrieved_evidence_ids"]:
            errors.append(
                "[E-CAUSE-EVIDENCE] %s: causa 'retrieval' ma tutte le evidenze accessibili "
                "sono state recuperate" % case_id
            )
    elif row["primary_cause"] == "answer":
        if row["unreachable_evidence_ids"] or row["not_retrieved_evidence_ids"]:
            errors.append(
                "[E-CAUSE-EVIDENCE] %s: causa 'answer' ma l'evidenza obbligatoria non era "
                "tutta nel contesto recuperato" % case_id
            )

    if row["primary_cause"] == "benchmark" and not row["benchmark_defect"]:
        errors.append("[E-BENCHMARK] %s: causa 'benchmark' con benchmark_defect=false" % case_id)
    if row["benchmark_defect"] and "benchmark" not in (row["primary_cause"], row["secondary_cause"]):
        errors.append("[E-BENCHMARK] %s: benchmark_defect=true senza causa 'benchmark'" % case_id)

    if row["answer_class"] not in ("incorrect", "partial"):
        errors.append(
            "[E-CASE] %s: analizzato un caso con answer_class '%s'; l'analisi causale "
            "riguarda i fallimenti" % (case_id, row["answer_class"])
        )

    if row["diagnostic_reference"] is not None:
        if row["diagnostic_reference"]["mode"] != DIAGNOSTIC_MODE:
            errors.append("[E-DIAGNOSTIC] %s: riferimento diagnostico non e' FULL_HISTORY" % case_id)
        if row["primary_cause"] != "retrieval":
            errors.append(
                "[E-DIAGNOSTIC] %s: il controllo diagnostico e' ammesso solo per un "
                "fallimento di retrieval" % case_id
            )

    return errors


def validate_against_evaluation(rows, evaluation):
    """L'analisi non puo' contraddire le classificazioni gia' approvate."""
    errors = []
    index = {(r["scenario_id"], r["question_id"], r["mode"]): r for r in evaluation}
    for row in rows:
        source = index.get((row["scenario_id"], row["question_id"], row["condition"]))
        if source is None:
            errors.append("[E-EVAL-MISSING] %s: nessuna annotazione corrispondente" % row["case_id"])
            continue
        for field in ("reachable", "retrieval_success", "answer_class", "obsolete_used", "unsupported_claim"):
            if row[field] != source[field]:
                errors.append(
                    "[E-EVAL-MATCH] %s: '%s' = %s nell'analisi, %s in evaluation_pilot.jsonl"
                    % (row["case_id"], field, row[field], source[field])
                )
    return errors


def validate_all(rows, evaluation):
    errors = []
    seen = set()
    for row in rows:
        if row["case_id"] in seen:
            errors.append("[E-DUP] %s: caso duplicato" % row["case_id"])
        seen.add(row["case_id"])
        errors.extend(validate_case(row))
    errors.extend(validate_against_evaluation(rows, evaluation))
    return errors


# --------------------------------------------------------------------------
# Riepilogo leggibile
# --------------------------------------------------------------------------


def _ids(values):
    return ", ".join("`%s`" % v for v in values) if values else "nessuno"


def _case_block(row):
    lines = [
        "## Caso %s" % row["case_id"],
        "",
        "**Prima causa osservabile:** %s - %s  " % (row["primary_cause"], row["primary_cause_description"]),
    ]
    if row["secondary_cause"]:
        lines.append(
            "**Causa secondaria:** %s - %s  "
            % (row["secondary_cause"], row["secondary_cause_description"])
        )
    else:
        lines.append("**Causa secondaria:** nessuna  ")
    lines.extend(
        [
            "**Classe della risposta (gia' approvata):** `%s`  " % row["answer_class"],
            "**Affermazioni non supportate:** %s  "
            % ("si" if row["unsupported_claim"] else "no"),
            "**Uso di informazioni obsolete:** %s  " % ("si" if row["obsolete_used"] else "no"),
            "**Difetto del benchmark:** %s" % ("si" if row["benchmark_defect"] else "no"),
            "",
            "### Domanda e oracle",
            "",
            "> %s" % row["question_text"],
            "",
            "Risposta attesa: %s" % row["expected_answer"],
            "",
            "Fatti obbligatori: %s" % "; ".join(row["mandatory_facts"]),
            "",
            "### Traccia",
            "",
            "| Passaggio | Valore |",
            "|---|---|",
            "| Evidenze obbligatorie | %s |" % _ids(row["required_evidence_ids"]),
            "| Messaggi accessibili nella condizione | %s |" % _ids(row["accessible_message_ids"]),
            "| Messaggi recuperati (top_k=%d) | %s |" % (row["top_k"], _ids(row["retrieved_message_ids"])),
            "| Evidenza raggiungibile | %s |" % ("si" if row["reachable"] else "no"),
            "| Retrieval riuscito | %s |"
            % ({True: "si", False: "no", None: "non applicabile"}[row["retrieval_success"]]),
            "| Evidenze fuori dal perimetro | %s |" % _ids(row["unreachable_evidence_ids"]),
            "| Evidenze accessibili ma non recuperate | %s |" % _ids(row["not_retrieved_evidence_ids"]),
            "| Comportamento atteso | %s |" % row["expected_behavior"],
            "| Fatti obbligatori mancanti nella risposta | %s |"
            % ("; ".join(row["missing_mandatory_facts"]) or "nessuno"),
            "",
            "### Risposta del modello",
            "",
            "> %s" % row["model_answer"],
            "",
        ]
    )

    if row["diagnostic_reference"] is not None:
        diagnostic = row["diagnostic_reference"]
        lines.extend(
            [
                "### Controllo diagnostico %s" % diagnostic["mode"],
                "",
                diagnostic["note"],
                "",
                "Contesto ricevuto: %s  " % _ids(diagnostic["context_message_ids"]),
                "Classe della risposta: `%s`" % diagnostic["answer_class"],
                "",
                "> %s" % diagnostic["model_answer"],
                "",
            ]
        )

    lines.extend(["### Motivazione finale", "", row["rationale"], ""])
    return lines


def render_markdown(rows, sources):
    lines = [
        "# Analisi causale dei fallimenti del pilot",
        "",
        "**Stato:** risultati del pilot, non conclusioni finali.  ",
        "**Ambito:** step 3 - origine dei due problemi emersi nella valutazione.",
        "",
        "Documento generato da `scripts/build_error_analysis.py`; il risultato",
        "machine-readable e' `results/error_analysis_pilot.jsonl`.",
        "",
        "Ogni fallimento e' ricondotto alla **prima causa osservabile** nella pipeline,",
        "secondo la sezione 11 di `EXPERIMENT.md`:",
        "",
    ]
    for position, name in enumerate(CAUSE_ORDER, start=1):
        lines.append("%d. `%s` - %s;" % (position, name, CAUSES[name]))
    lines.extend(
        [
            "",
            "I due casi analizzati sono gli unici fallimenti del pilot: le altre 54 prove",
            "sono risposte complete o astensioni corrette. Le classificazioni sono quelle",
            "gia' approvate e non vengono riviste qui; questo documento aggiunge soltanto",
            "l'origine dell'errore.",
            "",
            "Gli errori sono conservati come risultati reali del pilot: il retriever non e'",
            "stato corretto e la domanda non e' stata modificata.",
            "",
            "`FULL_HISTORY` non e' una condizione sperimentale. Compare una sola volta,",
            "come controllo diagnostico del caso SC02-Q6/C2, per distinguere un fallimento",
            "di retrieval da un fallimento di generazione.",
            "",
            "## Sintesi",
            "",
            "| Caso | Classe | Causa principale | Causa secondaria | Fatto non supportato | Difetto del benchmark |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| %s | `%s` | `%s` | %s | %s | %s |"
            % (
                row["case_id"],
                row["answer_class"],
                row["primary_cause"],
                "`%s`" % row["secondary_cause"] if row["secondary_cause"] else "nessuna",
                "si" if row["unsupported_claim"] else "no",
                "si" if row["benchmark_defect"] else "no",
            )
        )
    lines.append("")

    for row in rows:
        lines.extend(_case_block(row))

    lines.extend(["## Sorgenti", "", "| File | SHA-256 |", "|---|---|"])
    for name, digest in sorted(sources.items()):
        lines.append("| `%s` | `%s` |" % (name, digest))

    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def build_analysis():
    """Estrae e valida le due tracce. Restituisce (rows, sources, errors)."""
    sources = {
        "retrieval": load_jsonl(RETRIEVAL_PATH),
        "inputs": load_jsonl(GENERATION_INPUTS_PATH),
        "generation": load_jsonl(GENERATION_PATH),
        "evaluation": load_jsonl(EVALUATION_PATH),
    }
    rows = [build_case(case, sources) for case in APPROVED_CASES]
    errors = validate_all(rows, sources["evaluation"])
    digests = {
        str(path.relative_to(REPO_ROOT)): sha256_of(path)
        for path in (
            SCENARIO_DIR / "scenario_02.json",
            RETRIEVAL_PATH,
            GENERATION_INPUTS_PATH,
            GENERATION_PATH,
            EVALUATION_PATH,
        )
    }
    return rows, digests, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="valida le tracce senza scrivere i file"
    )
    args = parser.parse_args(argv)

    rows, digests, errors = build_analysis()
    if errors:
        print("%d errore/i di validazione:" % len(errors))
        for error in errors:
            print("  - %s" % error)
        return 1

    print("Validazione superata: %d casi analizzati." % len(rows))
    for row in rows:
        print(
            "  %-12s classe=%-9s causa=%-12s secondaria=%-8s unsupported=%s"
            % (
                row["case_id"],
                row["answer_class"],
                row["primary_cause"],
                row["secondary_cause"] or "nessuna",
                "si" if row["unsupported_claim"] else "no",
            )
        )

    if args.check:
        print("\n--check: nessun file scritto.")
        return 0

    ANALYSIS_JSONL_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    ANALYSIS_MD_PATH.write_text(render_markdown(rows, digests), encoding="utf-8")
    print(
        "\nScritti:\n  %s\n  %s"
        % (
            ANALYSIS_JSONL_PATH.relative_to(REPO_ROOT),
            ANALYSIS_MD_PATH.relative_to(REPO_ROOT),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
