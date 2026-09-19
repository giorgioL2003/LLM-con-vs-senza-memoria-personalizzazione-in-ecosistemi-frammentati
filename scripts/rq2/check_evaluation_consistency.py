#!/usr/bin/env python3
"""Controlli di coerenza fra artefatti e sintesi della prova sul budget.

Verifica che i numeri riportati nei documenti si ritrovino nei file, e che i
file siano coerenti fra loro. Non giudica le risposte: controlla i conteggi.

  1. **conteggi**: 49 risposte, 49 valutazioni, una per ogni cella prevista,
     nessun duplicato, nessun errore di chiamata, nessuna risposta vuota;
  2. **modello ed effort**: tutte le righe dichiarano `claude-sonnet-5` /
     `medium`, come le prove precedenti;
  3. **valutazione ↔ retrieval**: token, elementi e identificatori di ogni
     valutazione coincidono con la riga di retrieval da cui vengono;
  4. **valutazione ↔ risposta**: ogni valutazione ha la sua risposta;
  5. **riepilogo ↔ valutazioni**: i conteggi per classe e le metriche del
     riepilogo si ricalcolano dalle righe;
  6. **coerenza interna del criterio**: `counts_as_complete_and_supported` vale
     esattamente quando la classe e' `completa` e la risposta e' supportata;
  7. **provenienza vs contenuto**: elenca i casi in cui la provenienza e'
     completa ma i fatti richiesti non sono tutti nel contesto. Non e' un
     errore: e' la distinzione da non perdere;
  8. **artefatti storici intatti**: le impronte registrate in
     `RACCOLTA_RISULTATI/*/fonti_*.json` non devono essere cambiate.

Uso:
    python3 scripts/rq2/check_evaluation_consistency.py
"""

from __future__ import annotations

import glob
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402

NEW_DIR = rq2.RQ2_RESULTS_DIR / "budget_per_scenario_v1"
GENERATED = {
    "scenario_02": ("T", "F"),
    "scenario_03": ("F", "U"),
    "scenario_04": ("T", "U", "G"),
}
CLASSES = ("completa", "parziale", "errata", "astensione corretta")


def expected_keys():
    keys = set()
    for scenario_id, modes in GENERATED.items():
        for question in rq2.load_questions(scenario_id):
            for mode in modes:
                keys.add((scenario_id, question["question_id"], mode))
    return keys


def main():
    errors, notes = [], []

    answers = rq2.read_jsonl(NEW_DIR / "generation_dev_budget_per_scenario.jsonl")
    evaluations = rq2.read_jsonl(NEW_DIR / "valutazioni_budget_per_scenario.jsonl")
    with open(NEW_DIR / "riepilogo_budget_per_scenario.json", encoding="utf-8") as handle:
        summary = json.load(handle)

    retrieval = {}
    for scenario_id in GENERATED:
        suffix = scenario_id.replace("scenario_", "sc")
        for row in rq2.read_jsonl(NEW_DIR / ("retrieval_%s.jsonl" % suffix)):
            retrieval[(row["scenario_id"], row["question_id"], row["mode"])] = row

    # 1. conteggi
    attesi = expected_keys()
    chiavi_risposte = [(r["scenario_id"], r["question_id"], r["mode"]) for r in answers]
    chiavi_valutazioni = [(r["scenario_id"], r["question_id"], r["mode"]) for r in evaluations]

    if len(answers) != 49:
        errors.append("risposte: %d righe, ne erano previste 49" % len(answers))
    if len(evaluations) != 49:
        errors.append("valutazioni: %d righe, ne erano previste 49" % len(evaluations))
    if len(set(chiavi_risposte)) != len(chiavi_risposte):
        errors.append("risposte: esistono righe duplicate per la stessa cella")
    if len(set(chiavi_valutazioni)) != len(chiavi_valutazioni):
        errors.append("valutazioni: esistono righe duplicate per la stessa cella")
    if set(chiavi_risposte) != attesi:
        errors.append("risposte: celle mancanti %s, celle in piu' %s"
                      % (sorted(attesi - set(chiavi_risposte)), sorted(set(chiavi_risposte) - attesi)))
    if set(chiavi_valutazioni) != attesi:
        errors.append("valutazioni: celle mancanti %s, celle in piu' %s"
                      % (sorted(attesi - set(chiavi_valutazioni)),
                         sorted(set(chiavi_valutazioni) - attesi)))

    for row in answers:
        dove = "%s %s %s" % (row["scenario_id"], row["question_id"], row["mode"])
        if row.get("error"):
            errors.append("%s: errore di chiamata registrato" % dove)
        if not row.get("model_answer"):
            errors.append("%s: risposta vuota" % dove)
        # 2. modello ed effort
        if row.get("model_used") != "claude-sonnet-5" or row.get("model_requested") != "claude-sonnet-5":
            errors.append("%s: modello %s / richiesto %s"
                          % (dove, row.get("model_used"), row.get("model_requested")))
        if row.get("effort") != "medium":
            errors.append("%s: effort %s" % (dove, row.get("effort")))

    risposte_per_chiave = {(r["scenario_id"], r["question_id"], r["mode"]): r for r in answers}

    for row in evaluations:
        key = (row["scenario_id"], row["question_id"], row["mode"])
        dove = "%s %s %s" % key

        # 3. valutazione <-> retrieval
        source = retrieval.get(key)
        if source is None:
            errors.append("%s: manca la riga di retrieval" % dove)
        else:
            if row["context_tokens"] != source["context_tokens"]:
                errors.append("%s: token del contesto %s, nel retrieval %s"
                              % (dove, row["context_tokens"], source["context_tokens"]))
            if row["context_items"] != source["context_items"]:
                errors.append("%s: elementi %s, nel retrieval %s"
                              % (dove, row["context_items"], source["context_items"]))
            if row["context_item_ids"] != source["selected_item_ids"]:
                errors.append("%s: identificatori del contesto diversi dal retrieval" % dove)
            if row["budget_tokens"] != source["budget_tokens"]:
                errors.append("%s: budget %s, nel retrieval %s"
                              % (dove, row["budget_tokens"], source["budget_tokens"]))

        # 4. valutazione <-> risposta
        answer = risposte_per_chiave.get(key)
        if answer is None:
            errors.append("%s: manca la risposta" % dove)
        elif row["model_used"] != answer["model_used"]:
            errors.append("%s: modello diverso fra valutazione e risposta" % dove)

        # 6. coerenza interna del criterio
        atteso = row["answer_class"] == "completa" and row["supported_by_original_conversation"] is True
        if row["counts_as_complete_and_supported"] != atteso:
            errors.append("%s: counts_as_complete_and_supported=%s ma classe=%s e supporto=%s"
                          % (dove, row["counts_as_complete_and_supported"],
                             row["answer_class"], row["supported_by_original_conversation"]))
        if row["answer_class"] not in CLASSES:
            errors.append("%s: classe sconosciuta %s" % (dove, row["answer_class"]))
        if row["annotation_source"] != "valutazione_assistita_proposta_non_approvata":
            errors.append("%s: i giudizi devono restare dichiarati come proposti" % dove)
        if row["obsolete_used"] and row["answer_class"] == "completa":
            errors.append("%s: usa informazione obsoleta ma e' classificata completa" % dove)

        # 7. provenienza vs contenuto
        got, total = (row["rq2_fact_coverage_in_context"] or "0/0").split("/")
        if row["evidence_provenance_complete_auto"] and int(got) != int(total):
            notes.append("%s: provenienza completa ma fatti nel contesto %s/%s"
                         % (dove, got, total))

    # 5. riepilogo <-> valutazioni
    for scenario_id, modes in summary["riepilogo_per_scenario"].items():
        for mode, dati in modes.items():
            subset = [r for r in evaluations
                      if r["scenario_id"] == scenario_id and r["mode"] == mode]
            dove = "%s %s" % (scenario_id, mode)
            if dati["N_c"] != len(subset):
                errors.append("%s: riepilogo dichiara N_c=%d, righe %d" % (dove, dati["N_c"], len(subset)))
            for classe in CLASSES:
                atteso = sum(1 for r in subset if r["answer_class"] == classe)
                if dati["classi"][classe] != atteso:
                    errors.append("%s: riepilogo dichiara %d '%s', righe %d"
                                  % (dove, dati["classi"][classe], classe, atteso))
            complete = sum(1 for r in subset if r["counts_as_complete_and_supported"])
            if dati["CompleteAnswerRate"]["numeratore"] != complete:
                errors.append("%s: CompleteAnswerRate dichiara %d, righe %d"
                              % (dove, dati["CompleteAnswerRate"]["numeratore"], complete))
            somma = sum(dati["classi"][c] for c in CLASSES)
            if somma != dati["N_c"]:
                errors.append("%s: le classi sommano a %d invece di %d" % (dove, somma, dati["N_c"]))

    # 8. artefatti storici intatti
    intatti = modificati = 0
    visti = set()
    for path in sorted(glob.glob(str(rq2.REPO_ROOT / "RACCOLTA_RISULTATI" / "*" / "fonti_*.json"))):
        with open(path, encoding="utf-8") as handle:
            fonti = json.load(handle)
        for relativo, impronta in fonti["letti_in_sola_lettura"].items():
            if relativo in visti:
                continue
            visti.add(relativo)
            file_path = rq2.REPO_ROOT / relativo
            if not file_path.exists():
                errors.append("artefatto storico mancante: %s" % relativo)
                continue
            if hashlib.sha256(file_path.read_bytes()).hexdigest() != impronta:
                errors.append("artefatto storico MODIFICATO: %s" % relativo)
                modificati += 1
            else:
                intatti += 1

    print("Controlli di coerenza — prova budget-per-scenario-v1")
    print("=" * 78)
    print("risposte: %d | valutazioni: %d | celle previste: %d" % (len(answers), len(evaluations), len(attesi)))
    print("artefatti storici verificati: %d intatti, %d modificati" % (intatti, modificati))
    print("-" * 78)
    if notes:
        print("Provenienza completa ma fatti richiesti mancanti nel contesto (non e' un errore,")
        print("e' la distinzione da tenere separata):")
        for nota in notes:
            print("  - %s" % nota)
        print("-" * 78)
    if errors:
        print("Controlli falliti:")
        for error in errors:
            print("  - %s" % error)
        return 1
    print("Tutti i controlli superati.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
