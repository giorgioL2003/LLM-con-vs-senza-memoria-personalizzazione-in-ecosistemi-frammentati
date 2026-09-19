#!/usr/bin/env python3
"""Valutazione della prova `budget-per-scenario-v1`: schede e riepiloghi.

Due usi, uno dopo l'altro.

**`--dossier`** stampa, per ogni risposta, tutto quello che serve a giudicarla e
nient'altro: la domanda, la risposta attesa, i fatti obbligatori dell'oracle del
pilot, i `required_facts` di RQ2 con la loro provenienza, l'informazione
obsoleta da non usare, **le righe di contesto realmente fornite al modello** e
la risposta generata. Serve a rileggere ogni risposta da capo, non a ricopiare
giudizi.

**`--judgments`** prende il file dei giudizi scritti a mano, li unisce ai campi
che si calcolano da soli (token, elementi, provenienza, sorgenti) e produce:

  - `valutazioni_budget_per_scenario.jsonl`, una riga per risposta, con lo
    stesso schema della raccolta esistente (`completezza-supporto-1`);
  - `riepilogo_budget_per_scenario.json`, i conteggi e le metriche per
    scenario e modalita'.

I giudizi restano **proposti**: `annotation_source` lo dichiara in ogni riga.

Distinzione tenuta separata ovunque, perche' e' quella che si presta di piu' a
essere confusa:

  - `evidence_provenance_complete_auto` — il *messaggio sorgente* del fatto e'
    fra quelli citati dal contesto. Calcolata dal codice.
  - `rq2_fact_coverage_in_context` — il *fatto* si legge davvero nel testo delle
    righe fornite. Verificata a mano, riga per riga.

La prima puo' essere completa mentre la seconda non lo e': un messaggio puo'
entrare nel contesto tramite un fatto che ne conserva solo una parte.

Uso:
    python3 scripts/rq2/build_evaluation_budget_variant.py --dossier
    python3 scripts/rq2/build_evaluation_budget_variant.py --judgments giudizi.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402

NEW_DIR = rq2.RQ2_RESULTS_DIR / "budget_per_scenario_v1"
VARIANT_CONFIG = rq2.REPO_ROOT / "data" / "rq2" / "config" / "experiment_rq2_budget_per_scenario.json"
ANSWERS = NEW_DIR / "generation_dev_budget_per_scenario.jsonl"

LABEL = "budget-per-scenario-v1"
RULE = "completezza-supporto-1"
ANNOTATION_SOURCE = "valutazione_assistita_proposta_non_approvata"

SCENARIOS = ("scenario_02", "scenario_03", "scenario_04")
GENERATED = {
    "scenario_02": ("T", "F"),
    "scenario_03": ("F", "U"),
    "scenario_04": ("T", "U", "G"),
}

CLASSES = ("completa", "parziale", "errata", "astensione corretta")


def _key(row):
    return (row["scenario_id"], row["question_id"], row["mode"])


def load_all():
    answers = {}
    for row in rq2.read_jsonl(ANSWERS):
        if row.get("error") is None and row.get("model_answer"):
            answers[_key(row)] = row      # l'ultima riga vale
    retrieval, inputs = {}, {}
    for scenario_id in SCENARIOS:
        suffix = scenario_id.replace("scenario_", "sc")
        for row in rq2.read_jsonl(NEW_DIR / ("retrieval_%s.jsonl" % suffix)):
            retrieval[_key(row)] = row
        for row in rq2.read_jsonl(NEW_DIR / ("generation_inputs_%s.jsonl" % suffix)):
            inputs[_key(row)] = row
    questions = {}
    for scenario_id in SCENARIOS:
        for question in rq2.load_questions(scenario_id):
            questions[(scenario_id, question["question_id"])] = question
    return answers, retrieval, inputs, questions


def expected_keys():
    keys = []
    for scenario_id in SCENARIOS:
        for question in rq2.load_questions(scenario_id):
            for mode in GENERATED[scenario_id]:
                keys.append((scenario_id, question["question_id"], mode))
    return keys


# --------------------------------------------------------------------------
# Schede da leggere
# --------------------------------------------------------------------------

def print_dossier(answers, retrieval, questions, only=None):
    for key in expected_keys():
        if only and key[0] != only:
            continue
        scenario_id, question_id, mode = key
        question = questions[(scenario_id, question_id)]
        answer = answers.get(key)
        row = retrieval[key]

        print("=" * 100)
        print("%s | %s | %s   [%s, atteso: %s]"
              % (scenario_id, question_id, mode, question["category"], question["expected_behavior"]))
        print("=" * 100)
        print("DOMANDA: %s" % question["text"])
        print("ATTESA : %s" % question["expected_answer"])
        print("FATTI OBBLIGATORI (oracle del pilot): %s" % " | ".join(question["mandatory_facts"]))
        if question["required_facts"]:
            print("REQUIRED_FACTS RQ2:")
            for fact in question["required_facts"]:
                print("   [%s] %s   (da %s)"
                      % (fact["fact_key"], fact["text"], ", ".join(fact["source_message_ids"])))
        if question["obsolete_information"]:
            print("DA NON USARE: %s" % " | ".join(question["obsolete_information"]))
        if question["accepted_equivalents"]:
            print("EQUIVALENTI AMMESSI: %s" % " | ".join(question["accepted_equivalents"]))
        print("-" * 100)
        print("CONTESTO FORNITO (%d elementi, %d token, budget %s):"
              % (row["context_items"], row["context_tokens"], rq2.budget_label(row["budget_tokens"])))
        for item in row["selected"]:
            print("   %s" % item["render"])
        print("   [provenienza: %s]" % ", ".join(row["context_provenance_message_ids"]))
        print("   [evidenza per provenienza completa: %s]" % row["evidence_provenance_complete"])
        print("-" * 100)
        print("RISPOSTA:")
        print(answer["model_answer"] if answer else "  *** MANCANTE ***")
        print()


# --------------------------------------------------------------------------
# Righe di valutazione
# --------------------------------------------------------------------------

def build_rows(judgments, answers, retrieval, inputs, questions):
    rows, problems = [], []
    for key in expected_keys():
        scenario_id, question_id, mode = key
        name = "%s|%s|%s" % key
        judgment = judgments.get(name)
        if judgment is None:
            problems.append("giudizio mancante per %s" % name)
            continue
        answer = answers.get(key)
        if answer is None:
            problems.append("risposta mancante per %s" % name)
            continue
        row = retrieval[key]
        question = questions[(scenario_id, question_id)]

        detail = judgment.get("rq2_fact_detail", {})
        fact_keys = [f["fact_key"] for f in question["required_facts"]]
        for fact_key in fact_keys:
            if fact_key not in detail:
                problems.append("%s: manca il dettaglio del fatto %s" % (name, fact_key))
        extra = [k for k in detail if k not in fact_keys]
        if extra:
            problems.append("%s: dettaglio di fatti inesistenti: %s" % (name, ", ".join(extra)))

        in_context = sum(1 for k in fact_keys if detail.get(k, {}).get("in_context"))
        in_answer = sum(1 for k in fact_keys if detail.get(k, {}).get("in_answer"))
        total = len(fact_keys)

        answer_class = judgment["answer_class"]
        if answer_class not in CLASSES:
            problems.append("%s: classe sconosciuta '%s'" % (name, answer_class))
        supported = judgment["supported_by_original_conversation"]
        complete_and_supported = (answer_class == "completa" and supported is True)
        if judgment.get("counts_as_complete_and_supported") not in (None, complete_and_supported):
            problems.append("%s: counts_as_complete_and_supported incoerente con classe e supporto" % name)

        rows.append({
            "analysis_revision": "r1",
            "annotation_source": ANNOTATION_SOURCE,
            "answer_class": answer_class,
            "answer_class_candidates": judgment.get("answer_class_candidates"),
            "answer_class_suspended": bool(judgment.get("answer_class_suspended")),
            "budget_applies": row["budget_applies"],
            "budget_tokens": row["budget_tokens"],
            "cause_note": judgment.get("cause_note"),
            "classification_rule": RULE,
            "config_id": "rq2-dev-0.2-budget-per-scenario",
            "context_item_ids": list(row["selected_item_ids"]),
            "context_items": row["context_items"],
            "context_tokens": row["context_tokens"],
            "counts_as_complete_and_supported": complete_and_supported,
            "effort": answer["effort"],
            "error_origin": judgment.get("error_origin", "nessuno"),
            "evidence_provenance_complete_auto": row["evidence_provenance_complete"],
            "evidence_retrieved_content_verified": True,
            "expected_behavior": question["expected_behavior"],
            "faithful_to_received_context": judgment["faithful_to_received_context"],
            "label": LABEL,
            "memory_items": row["memory_items"],
            "memory_unit": row["memory_unit"],
            "mode": mode,
            "model_used": answer["model_used"],
            "obsolete_used": judgment["obsolete_used"],
            "oracle_rq2_required_fact_keys": fact_keys,
            "pilot_mandatory_coverage_in_answer": judgment["pilot_mandatory_coverage_in_answer"],
            "pilot_mandatory_facts": list(question["mandatory_facts"]),
            "question_category": question["category"],
            "question_id": question_id,
            "rationale": judgment["rationale"],
            "reachable": bool(question["fact_present_in_corpus"]),
            "retrieval_performed": True,
            "rq2_fact_coverage_in_answer": "%d/%d" % (in_answer, total),
            "rq2_fact_coverage_in_context": "%d/%d" % (in_context, total),
            "rq2_fact_detail": detail,
            "scenario_id": scenario_id,
            "stopped_by": row["stopped_by"],
            "supported_by_original_conversation": supported,
            "trace_ref": {
                "scenario": rq2.relative(rq2.SCENARIO_SOURCES[scenario_id][1]),
                "oracle_e_annotazione_rq2": "data/rq2/annotations/%s_rq2.json" % scenario_id,
                "configurazione": "data/rq2/config/experiment_rq2_budget_per_scenario.json",
                "retrieval": "results/rq2/budget_per_scenario_v1/retrieval_%s.jsonl"
                             % scenario_id.replace("scenario_", "sc"),
                "prompt_e_contesto": "results/rq2/budget_per_scenario_v1/generation_inputs_%s.jsonl"
                                     % scenario_id.replace("scenario_", "sc"),
                "risposte": "results/rq2/budget_per_scenario_v1/generation_dev_budget_per_scenario.jsonl",
                "fatti": row.get("facts_source"),
                "stato_memoria": row.get("state_source"),
                "grafo": row.get("graph_source"),
            },
            "unsupported_claim": judgment["unsupported_claim"],
            "wrong_abstention": judgment.get("wrong_abstention", False),
        })
    return rows, problems


# --------------------------------------------------------------------------
# Riepilogo
# --------------------------------------------------------------------------

def _rate(num, den, nota=None):
    entry = {"numeratore": num, "denominatore": den,
             "valore": round(num / den, 4) if den else None,
             "percentuale": round(100.0 * num / den, 1) if den else None}
    if nota:
        entry["nota"] = nota
    return entry


def summarize(rows):
    riepilogo = {}
    for scenario_id in SCENARIOS:
        per_mode = {}
        for mode in GENERATED[scenario_id]:
            subset = [r for r in rows if r["scenario_id"] == scenario_id and r["mode"] == mode]
            if not subset:
                continue
            n = len(subset)
            classi = {c: sum(1 for r in subset if r["answer_class"] == c) for c in CLASSES}
            classi["sospese"] = sum(1 for r in subset if r["answer_class_suspended"])

            raggiungibili = [r for r in subset if r["reachable"]]
            recuperate = [r for r in raggiungibili
                          if r["rq2_fact_coverage_in_context"].split("/")[0]
                          == r["rq2_fact_coverage_in_context"].split("/")[1]]
            complete = [r for r in subset if r["counts_as_complete_and_supported"]]
            astensioni = [r for r in subset if r["expected_behavior"] == rq2.BEHAVIOR_ABSTAIN]

            per_mode[mode] = {
                "N_c": n,
                "classi": classi,
                "budget": rq2.budget_label(subset[0]["budget_tokens"]),
                "token_contesto_medi": round(sum(r["context_tokens"] for r in subset) / n, 1),
                "elementi_contesto_medi": round(sum(r["context_items"] for r in subset) / n, 1),
                "ReachabilityRate": _rate(
                    len(raggiungibili), n,
                    "perimetro = intero scenario in tutte le modalita'; dipende solo dall'oracle"),
                "RetrievalSuccess_condizionato_alla_raggiungibilita": _rate(
                    len(recuperate), len(raggiungibili),
                    "verificato sul CONTENUTO delle righe di contesto contro i fact_key RQ2, "
                    "non sulla provenienza"),
                "CompleteAnswerRate": _rate(
                    len(complete), n, "risposte complete E supportate / N_c"),
                "AnswerSuccess_condizionato_al_recupero": _rate(
                    sum(1 for r in recuperate if r["counts_as_complete_and_supported"]),
                    len(recuperate),
                    "risposte complete e supportate / domande con i fatti richiesti presenti "
                    "nel CONTENUTO del contesto"),
                "CorrectAbstentionRate": _rate(
                    sum(1 for r in astensioni if r["answer_class"] == "astensione corretta"),
                    len(astensioni), "denominatore piccolo: leggere come conteggio, non come percentuale"),
                "ObsoleteUseRate": _rate(sum(1 for r in subset if r["obsolete_used"]), n),
                "UnsupportedClaimRate": _rate(sum(1 for r in subset if r["unsupported_claim"]), n),
                "WrongAbstentionRate": _rate(sum(1 for r in subset if r["wrong_abstention"]), n),
            }
        riepilogo[scenario_id] = per_mode
    return riepilogo


def main(argv=None):
    parser = argparse.ArgumentParser(description="Schede e riepiloghi della prova sul budget.")
    parser.add_argument("--dossier", action="store_true")
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--judgments", default=None)
    parser.add_argument("--out", default=str(NEW_DIR / "valutazioni_budget_per_scenario.jsonl"))
    parser.add_argument("--summary", default=str(NEW_DIR / "riepilogo_budget_per_scenario.json"))
    args = parser.parse_args(argv)

    answers, retrieval, inputs, questions = load_all()

    if args.dossier:
        print_dossier(answers, retrieval, questions, args.scenario)
        return 0

    if not args.judgments:
        print("Serve --dossier oppure --judgments.", file=sys.stderr)
        return 1

    with open(args.judgments, encoding="utf-8") as handle:
        judgments = json.load(handle)

    rows, problems = build_rows(judgments, answers, retrieval, inputs, questions)
    if problems:
        print("Problemi nei giudizi:", file=sys.stderr)
        for problem in problems:
            print("  - %s" % problem, file=sys.stderr)
        return 1

    rq2.write_jsonl(sorted(rows, key=lambda r: (r["scenario_id"], r["question_id"], r["mode"])), args.out)
    riepilogo = {
        "scheda": "Variante budget per scenario — SC02, SC03, SC04",
        "revisione": "r1",
        "data": "2026-09-19",
        "stato": "valutazioni assistite PROPOSTE, non approvate; prova di sviluppo; "
                 "riepilogo numerico PROVVISORIO",
        "prova": "una sola esecuzione per cella, nessuna replica",
        "configurazione": "rq2-dev-0.2-budget-per-scenario: nessun tetto su SC02-SC04, 200 token su SC05",
        "modello": "claude-sonnet-5, effort medium",
        "criterio": RULE,
        "avvertenza": "Le differenze rispetto alle prove con rq2-dev-0.1 sono osservate, non spiegate: "
                      "una sola generazione per condizione, e il modello varia anche a parita' di contesto.",
        "riepilogo_per_scenario": summarize(rows),
    }
    rq2.write_json(riepilogo, args.summary)

    print("Valutazioni scritte in %s (%d righe)." % (rq2.relative(Path(args.out)), len(rows)))
    print("Riepilogo scritto in %s." % rq2.relative(Path(args.summary)))
    for scenario_id, modes in riepilogo["riepilogo_per_scenario"].items():
        for mode, dati in modes.items():
            print("  %-13s %-4s %s | complete e supportate %d/%d"
                  % (scenario_id, mode, dati["classi"],
                     dati["CompleteAnswerRate"]["numeratore"], dati["N_c"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
