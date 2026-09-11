#!/usr/bin/env python3
"""Verifica offline dell'estensione T su SC04 e SC05. Nessuna chiamata al modello.

L'estensione aggiunge **Turn-level RAG (T)** come baseline anche a SC04 e SC05,
per confrontare le strategie *dentro* lo stesso scenario:

    SC01  T                SC04  T / U / G
    SC02  T / F            SC05  T / U / GER
    SC03  F / U

con FULL_HISTORY come controllo diagnostico in ogni scenario, fuori dal budget e
separato dalle architetture confrontate a parita' di budget.

Che cosa fa questo script, nell'ordine:

  1. valida dataset, configurazione e blocco `matrix_extension`;
  2. esegue il **retrieval di T** su SC04 e SC05 con il codice gia' in uso
     (`run_retrieval_rq2.py`), senza toccare fatti, stato di U o grafo: T non
     costruisce memoria, quindi l'estensione non richiede nessuna chiamata di
     estrazione, aggiornamento o costruzione del grafo;
  3. costruisce i prompt di T e ne verifica i controlli gia' previsti
     (budget rispettato, contesto uguale a quello contato, niente oracle);
  4. confronta la configurazione delle nuove righe con quella delle prove reali
     gia' salvate e dice **quali risultati esistenti sono riusabili** accanto a
     T e quali no, senza mescolare configurazioni diverse;
  5. controlla che T usi gli **stessi messaggi sorgente temporalmente
     accessibili** delle altre modalita' dello scenario;
  6. verifica per impronta che nessun artefatto precedente sia stato riscritto.

Gli output finiscono in `results/rq2/t_ext_check/`, sono etichettati `fixture` e
**non sono risultati sperimentali**: nessuna risposta viene generata. Le prove
reali dell'estensione vanno in cartelle proprie (`results/rq2/t_ext_v1/`).

Uso:
    python3 scripts/rq2/run_t_extension_check.py
    python3 scripts/rq2/run_t_extension_check.py --out results/rq2/t_ext_prova
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import validate_rq2  # noqa: E402
import build_memory_updates as memory  # noqa: E402
import run_retrieval_rq2 as retrieval_rq2  # noqa: E402
import build_generation_inputs_rq2 as generation_inputs  # noqa: E402
import build_annotation_template_rq2 as annotation_template  # noqa: E402

DEFAULT_OUT_DIR = rq2.RQ2_RESULTS_DIR / "t_ext_check"
LABEL = "fixture-estensione-t (nessuna chiamata al modello)"

# Scenari a cui l'estensione aggiunge davvero una cella.
NEW_SCENARIOS = ("scenario_04", rq2.GER_SCENARIO_ID)

# Prove reali gia' eseguite accanto a cui T andra' letto. Sono *lette* e mai
# riscritte. Ogni voce dichiara da quale prova viene e con quale avvertenza.
REFERENCE_RUNS = {
    "scenario_04": {
        "run_label": "prova-riparazione-u-instructions-0.3 (RQ2.md 9.6)",
        "inputs": rq2.RQ2_RESULTS_DIR / "sc04_repair_v3" / "generation_inputs_sc04_ug.jsonl",
        "answers": rq2.RQ2_RESULTS_DIR / "sc04_repair_v3" / "generation_dev_sc04_ug.jsonl",
        "state": rq2.RQ2_RESULTS_DIR / "sc04_repair_v3" / "scenario_04_state.json",
        "modes": ("U", "G"),
        # FULL_HISTORY non e' stata rigenerata nella riparazione: resta quella
        # della prova precedente. E' un controllo diagnostico e non dipende
        # dallo stato di U, ma appartiene a un'altra esecuzione e va detto.
        "diagnostic_from_other_run": {
            "run_label": "prova SC04 iniziale (RQ2.md 9.3)",
            "answers": rq2.RQ2_RESULTS_DIR / "generation_dev_sc04.jsonl",
            "inputs": rq2.RQ2_RESULTS_DIR / "generation_inputs_sc04.jsonl",
            "modes": (rq2.FULL_HISTORY,),
        },
        "superseded": {
            "answers": rq2.RQ2_RESULTS_DIR / "generation_dev_sc04.jsonl",
            "modes": ("U", "G"),
            "reason": "prova precedente alle istruzioni u-instructions-0.3: stato di U diverso, "
                      "non va messa nella stessa tabella di sc04_repair_v3",
        },
    },
    rq2.GER_SCENARIO_ID: {
        "run_label": "prova-reale-sviluppo-sc05-v1 (RQ2.md 11)",
        "inputs": rq2.RQ2_RESULTS_DIR / "sc05_dev_v1" / "generation_inputs_sc05.jsonl",
        "answers": rq2.RQ2_RESULTS_DIR / "sc05_dev_v1" / "generation_dev_sc05.jsonl",
        "state": rq2.RQ2_RESULTS_DIR / "sc05_dev_v1" / "memory" / "scenario_05_state.json",
        "modes": ("U", "GER", rq2.FULL_HISTORY),
        "diagnostic_from_other_run": None,
        "superseded": None,
    },
}


def step(number, title):
    print()
    print("=" * 78)
    print("%d. %s" % (number, title))
    print("=" * 78)


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def instructions_block(prompt):
    return prompt.split("Istruzioni:\n", 1)[1].split("\n\nContesto:")[0]


def fingerprint_tree(root):
    """Impronta di ogni file gia' presente sotto `root`, ricorsivamente."""
    root = Path(root)
    if not root.exists():
        return {}
    return {
        rq2.relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


# --------------------------------------------------------------------------
# 1. Perimetro: gli stessi messaggi sorgente temporalmente accessibili
# --------------------------------------------------------------------------

def check_perimeter(scenario_id, errors):
    """T deve pescare dagli stessi messaggi su cui e' costruita l'altra memoria.

    T non ha memoria da costruire: la sua unita' e' il messaggio originale. Il
    confronto e' onesto solo se il bacino di T e quello su cui sono stati
    estratti fatti e voci coincidono. Qui si controllano tre cose:

      - T indicizza tutti e soli i messaggi con ruolo `user`, come dichiarato in
        `memory_scope` (nessun messaggio dell'assistente);
      - la provenienza dello stato di U salvato sta dentro quel bacino;
      - lo stato arriva all'ultima sessione dello scenario: se si fermasse prima
        T avrebbe accesso a messaggi che le altre modalita' non hanno mai visto.
    """
    scenario = rq2.load_scenario(scenario_id)
    sessions = len(scenario["sessions"])
    pool = [entry["message_id"] for entry in rq2.user_messages(scenario)]
    items = rq2.message_items(scenario)
    if [item["item_id"] for item in items] != pool:
        errors.append("%s: gli elementi di T non coincidono con i messaggi utente" % scenario_id)

    index = rq2.message_index(scenario)
    for message_id in pool:
        if index[message_id]["role"] != rq2.INDEXED_ROLE:
            errors.append("%s: T indicizzerebbe un messaggio non '%s' (%s)"
                          % (scenario_id, rq2.INDEXED_ROLE, message_id))

    state_path = REFERENCE_RUNS[scenario_id]["state"]
    reached = None
    if not state_path.exists():
        errors.append("%s: stato di riferimento mancante (%s)" % (scenario_id, rq2.relative(state_path)))
    else:
        entries = memory.load_state(state_path)
        fuori = sorted({m for e in entries for m in e["source_message_ids"] if m not in pool})
        if fuori:
            errors.append("%s: lo stato di U cita messaggi fuori dal bacino di T: %s"
                          % (scenario_id, ", ".join(fuori)))
        reached = max((e["session_order"] for e in entries), default=0)
        if reached != sessions:
            errors.append(
                "%s: lo stato di U arriva alla sessione %d su %d. E' uno stato intermedio: "
                "T vedrebbe messaggi che le altre modalita' non hanno mai visto."
                % (scenario_id, reached, sessions))

    print("%-13s sessioni %d | messaggi utente indicizzabili da T: %2d | "
          "ultima sessione nello stato di U: %s"
          % (scenario_id, sessions, len(pool), reached if reached is not None else "?"))
    return pool


# --------------------------------------------------------------------------
# 2. Compatibilita' con le prove gia' eseguite
# --------------------------------------------------------------------------

def compare_run(scenario_id, new_rows, path, modes, run_label, config, errors, warnings):
    """Confronta i parametri di una prova salvata con quelli delle righe di T.

    Confrontabile vuol dire: stesse istruzioni, stesso budget, stesse domande,
    stesso modello ed effort. Se una di queste cambia, le due prove non vanno
    nella stessa tabella.
    """
    if not path.exists():
        warnings.append("%s: prova non disponibile (%s)" % (scenario_id, rq2.relative(path)))
        return None

    rows = [r for r in rq2.read_jsonl(path) if r["mode"] in modes]
    if not rows:
        warnings.append("%s: %s non contiene le modalita' %s"
                        % (scenario_id, rq2.relative(path), ", ".join(modes)))
        return None

    questions = {q["question_id"]: q for q in rq2.load_questions(scenario_id)}
    budget = rq2.budget_tokens(config)
    nostre_istruzioni = sha(generation_inputs.INSTRUCTIONS)
    report = {"path": rq2.relative(path), "run_label": run_label, "modes": sorted({r["mode"] for r in rows}),
              "rows": len(rows), "compatible": True, "problems": []}

    for row in rows:
        dove = "%s %s %s" % (scenario_id, row["question_id"], row["mode"])
        if "prompt" in row:
            if sha(instructions_block(row["prompt"])) != nostre_istruzioni:
                report["problems"].append("%s: istruzioni del prompt diverse" % dove)
            question = questions.get(row["question_id"])
            if question is None:
                report["problems"].append("%s: domanda non piu' presente nell'annotazione" % dove)
            elif not row["prompt"].endswith(question["text"]):
                report["problems"].append("%s: il prompt non termina con la domanda attuale" % dove)
            if row.get("budget_applies") and row.get("budget_tokens") != budget:
                report["problems"].append("%s: budget %s invece di %d"
                                          % (dove, row.get("budget_tokens"), budget))
            if row["mode"] == rq2.FULL_HISTORY and row.get("budget_applies"):
                report["problems"].append("%s: FULL_HISTORY non deve essere soggetto al budget" % dove)
        if "model_used" in row:
            atteso = config["models"]["answer"]
            if row.get("error"):
                report["problems"].append("%s: la prova salvata e' in errore" % dove)
            if row.get("model_requested") != atteso["model"] or row.get("model_used") != atteso["model"]:
                report["problems"].append("%s: modello %s / %s invece di %s"
                                          % (dove, row.get("model_requested"), row.get("model_used"),
                                             atteso["model"]))
            if row.get("effort") != atteso["effort"]:
                report["problems"].append("%s: effort %s invece di %s" % (dove, row.get("effort"),
                                                                         atteso["effort"]))

    # Le righe di T devono coprire esattamente le stesse domande.
    domande_t = {r["question_id"] for r in new_rows}
    domande_prova = {r["question_id"] for r in rows}
    if domande_t != domande_prova:
        report["problems"].append(
            "domande diverse: T copre %s, la prova salvata %s"
            % (", ".join(sorted(domande_t)), ", ".join(sorted(domande_prova))))

    report["compatible"] = not report["problems"]
    if not report["compatible"]:
        errors.extend(report["problems"])
    return report


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Verifica offline dell'estensione T: nessuna chiamata al modello.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR),
                        help="cartella degli artefatti (default: results/rq2/t_ext_check)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    out_dir = Path(args.out)
    config = rq2.load_config()
    budget = rq2.budget_tokens(config)
    errors, warnings = [], []

    print("Verifica offline dell'estensione T — nessun modello e' stato chiamato.")
    print("Etichetta: %s" % LABEL)
    print("Artefatti in %s (NON sono risultati sperimentali)" % rq2.relative(out_dir))

    prima = fingerprint_tree(rq2.RQ2_RESULTS_DIR)

    step(1, "Dataset, configurazione e matrice estesa")
    errors.extend(validate_rq2.validate_all(config=config))
    print("Matrice estesa %s (la matrice originale di %d celle non cambia)"
          % (rq2.matrix_extension(config)["extension_id"],
             config["expected_generations_when_complete"]["total"]))
    print("%-13s %-24s %-22s %s"
          % ("scenario", "a parita' di budget", "controllo diagnostico", "aggiunto qui"))
    for scenario_id, budgeted, diagnostic, added in rq2.extension_matrix_rows(config):
        print("%-13s %-24s %-22s %s"
              % (scenario_id, " / ".join(budgeted), " / ".join(diagnostic), " / ".join(added) or "-"))
    aggiunte = config["matrix_extension"]["added_cells"]
    print("Celle nuove: %d chiamate di risposta, %d di costruzione della memoria "
          "(T recupera i messaggi originali: non c'e' memoria da costruire)."
          % (aggiunte["total_answer_calls"], aggiunte["total_memory_calls"]))

    step(2, "Perimetro: gli stessi messaggi sorgente temporalmente accessibili")
    for scenario_id in NEW_SCENARIOS:
        check_perimeter(scenario_id, errors)

    step(3, "Retrieval di T su SC04 e SC05 (budget %d token, %s)"
         % (budget, config["retrieval"]["method"]))
    rows, skipped = retrieval_rq2.run(list(NEW_SCENARIOS), config, {}, LABEL, modes=["T"])
    for scenario_id, mode, reason in skipped:
        errors.append("saltato %s / %s: %s" % (scenario_id, mode, reason))
    retrieval_rq2.print_summary(rows)
    for row in rows:
        if row["context_tokens"] > budget and not row["budget_exceeded_by_first_item"]:
            errors.append("%s %s: T supera il budget" % (row["scenario_id"], row["question_id"]))
    retrieval_file = out_dir / "retrieval_t.jsonl"
    rq2.write_jsonl(rows, retrieval_file)
    print("righe di retrieval: %d → %s" % (len(rows), rq2.relative(retrieval_file)))

    step(4, "Prompt di T (costruiti, mai inviati)")
    inputs, input_skipped = generation_inputs.build(list(NEW_SCENARIOS), config, rows,
                                                    modes_override=["T"])
    for scenario_id in NEW_SCENARIOS:
        errors.extend(generation_inputs.check(
            [r for r in inputs if r["scenario_id"] == scenario_id], [scenario_id], config, rows))
    for scenario_id, mode, reason in sorted(set(input_skipped)):
        print("saltato: %s / %s — %s" % (scenario_id, mode, reason))
    generation_inputs.print_summary(inputs)
    inputs_file = out_dir / "generation_inputs_t.jsonl"
    rq2.write_jsonl(inputs, inputs_file)
    print("prompt scritti in %s (%d righe, model_answer sempre null)"
          % (rq2.relative(inputs_file), len(inputs)))
    print("istruzioni comuni: %s — le stesse del pilot e di tutte le prove precedenti"
          % sha(generation_inputs.INSTRUCTIONS))

    step(5, "Modello di annotazione delle celle nuove")
    template = annotation_template.build(inputs, rows)
    annotation_template.print_summary(template)
    template_file = out_dir / "annotation_template_t.jsonl"
    rq2.write_jsonl(template, template_file)
    print("scritto in %s (%d righe, tutti i giudizi null)"
          % (rq2.relative(template_file), len(template)))

    step(6, "Che cosa e' riusabile accanto a T, e che cosa no")
    riepilogo = {}
    for scenario_id in NEW_SCENARIOS:
        riferimento = REFERENCE_RUNS[scenario_id]
        righe_t = [r for r in rows if r["scenario_id"] == scenario_id]
        voci = []
        principale = compare_run(scenario_id, righe_t, riferimento["answers"],
                                 riferimento["modes"], riferimento["run_label"],
                                 config, errors, warnings)
        if principale:
            voci.append(dict(principale, uso="riusabile: stessa configurazione"))
        diagnostico = riferimento.get("diagnostic_from_other_run")
        if diagnostico:
            altro = compare_run(scenario_id, righe_t, diagnostico["answers"],
                                diagnostico["modes"], diagnostico["run_label"],
                                config, errors, warnings)
            if altro:
                voci.append(dict(altro, uso="riusabile con avvertenza: viene da un'altra esecuzione"))
                warnings.append(
                    "%s: FULL_HISTORY viene da %s, non dalla prova %s. Non e' un'incompatibilita' di "
                    "configurazione (stesso prompt, stesso modello, e non dipende dallo stato di U) "
                    "ma resta una prova diversa: va indicata come tale nella tabella."
                    % (scenario_id, diagnostico["run_label"], riferimento["run_label"]))
        superata = riferimento.get("superseded")
        if superata and superata["answers"].exists():
            voci.append({
                "path": rq2.relative(superata["answers"]),
                "run_label": "prova superata",
                "modes": list(superata["modes"]),
                "rows": None, "compatible": False, "problems": [superata["reason"]],
                "uso": "NON riusabile nella stessa tabella",
            })
        riepilogo[scenario_id] = voci

        print()
        print("--- %s: T e' nuovo (%d domande); accanto a T ---" % (scenario_id, len(righe_t)))
        for voce in voci:
            print("  %-38s %-14s %s" % (voce["path"], "/".join(voce["modes"]), voce["uso"]))
            for problema in voce["problems"]:
                print("      %s" % problema)

    rq2.write_json({
        "label": LABEL,
        "extension_id": config["matrix_extension"]["extension_id"],
        "config_id": config["config_id"],
        "budget_tokens": budget,
        "instructions_sha256": sha(generation_inputs.INSTRUCTIONS),
        "models": config["models"],
        "new_cells": {scenario_id: {"mode": "T", "questions": len([r for r in rows
                                                                   if r["scenario_id"] == scenario_id])}
                      for scenario_id in NEW_SCENARIOS},
        "reuse": riepilogo,
        "warnings": warnings,
    }, out_dir / "compatibilita.json")
    print()
    print("riepilogo scritto in %s" % rq2.relative(out_dir / "compatibilita.json"))

    step(7, "Nessun artefatto precedente e' stato riscritto")
    dopo = fingerprint_tree(rq2.RQ2_RESULTS_DIR)
    cambiati = sorted(k for k in prima if prima[k] != dopo.get(k))
    scomparsi = sorted(set(prima) - set(dopo))
    if cambiati or scomparsi:
        for nome in cambiati:
            print("MODIFICATO: %s" % nome)
        for nome in scomparsi:
            print("SCOMPARSO: %s" % nome)
        errors.append("la verifica ha toccato artefatti gia' salvati")
    else:
        nuovi = sorted(set(dopo) - set(prima))
        print("%d file gia' presenti confrontati per impronta: tutti invariati." % len(prima))
        print("%d file nuovi, tutti sotto %s." % (len(nuovi), rq2.relative(out_dir)))
        for nome in nuovi:
            if not nome.startswith(rq2.relative(out_dir)):
                errors.append("file nuovo fuori dalla cartella dell'estensione: %s" % nome)

    print()
    print("=" * 78)
    for avviso in warnings:
        print("AVVISO: %s" % avviso)
    if errors:
        print("CONTROLLI FALLITI (%d):" % len(errors))
        for error in errors:
            print("  - %s" % error)
        return 1
    print("Tutti i controlli superati. Nessuna chiamata al modello, nessuna risposta generata.")
    print("Le celle nuove sono %d (7 per SC04 + 7 per SC05), tutte in modalita' T."
          % aggiunte["total_answer_calls"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
