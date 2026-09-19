#!/usr/bin/env python3
"""Controlli da fare *prima* di chiamare il modello sulla variante del budget.

Serve a non sprecare chiamate e a non mescolare prove. Verifica, nell'ordine:

  1. **coerenza con la configurazione**: ogni input dichiara il budget dello
     scenario a cui appartiene (nessun tetto per SC02-SC04, 200 token per SC05)
     e l'etichetta della prova;
  2. **contesto uguale al retrieval salvato**: le righe del prompt sono quelle
     selezionate, senza riformattazioni;
  3. **niente oracle nei prompt** e una sola domanda per prompt;
  4. **nessuna risposta gia' presente** negli input (`model_answer` null);
  5. **che cosa e' gia' stato generato**: legge il file delle risposte, se
     esiste, e dice quali celle sono complete, quali in errore e quali mancano,
     cosi' la generazione riprende senza duplicare chiamate;
  6. **identita' degli input da riusare**: SC05 in tutte le modalita' e
     FULL_HISTORY in ogni scenario devono avere prompt identici, carattere per
     carattere, a quelli gia' inviati nelle prove precedenti. Se non lo sono,
     il riuso non e' lecito e lo script lo dice.

Non chiama nessun modello e non scrive nulla, a meno che non si chieda
`--json`.

Uso:
    python3 scripts/rq2/check_before_generation.py
    python3 scripts/rq2/check_before_generation.py --json controllo.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import build_generation_inputs_rq2 as inputs_rq2  # noqa: E402

NEW_DIR = rq2.RQ2_RESULTS_DIR / "budget_per_scenario_v1"
VARIANT_CONFIG = rq2.REPO_ROOT / "data" / "rq2" / "config" / "experiment_rq2_budget_per_scenario.json"
LABEL = "budget-per-scenario-v1"

# Le celle da generare davvero in questa prova.
TO_GENERATE = {
    "scenario_02": ("T", "F"),
    "scenario_03": ("F", "U"),
    "scenario_04": ("T", "U", "G"),
}

# Le celle riusate senza rigenerare, e da dove viene il prompt gia' inviato.
# Il riuso e' lecito solo se il prompt coincide: lo verifica il passo 6.
REUSED = {
    ("scenario_02", "FULL_HISTORY"): "results/rq2/generation_inputs_sc02.jsonl",
    ("scenario_03", "FULL_HISTORY"): "results/rq2/generation_inputs_sc03.jsonl",
    ("scenario_04", "FULL_HISTORY"): "results/rq2/generation_inputs_sc04.jsonl",
    ("scenario_05", "T"): "results/rq2/t_ext_v1/generation_inputs_t_sc05.jsonl",
    ("scenario_05", "U"): "results/rq2/sc05_dev_v1/generation_inputs_sc05.jsonl",
    ("scenario_05", "GER"): "results/rq2/sc05_dev_v1/generation_inputs_sc05.jsonl",
    ("scenario_05", "FULL_HISTORY"): "results/rq2/sc05_dev_v1/generation_inputs_sc05.jsonl",
}

# Da dove arrivano le risposte gia' generate delle celle riusate.
REUSED_ANSWERS = {
    ("scenario_02", "FULL_HISTORY"): "results/rq2/generation_dev_sc02.jsonl",
    ("scenario_03", "FULL_HISTORY"): "results/rq2/generation_dev_sc03.jsonl",
    ("scenario_04", "FULL_HISTORY"): "results/rq2/generation_dev_sc04.jsonl",
    ("scenario_05", "T"): "results/rq2/t_ext_v1/generation_dev_t_sc05.jsonl",
    ("scenario_05", "U"): "results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl",
    ("scenario_05", "GER"): "results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl",
    ("scenario_05", "FULL_HISTORY"): "results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl",
}

SCENARIOS = ("scenario_02", "scenario_03", "scenario_04", "scenario_05")


def _key(row):
    return (row["scenario_id"], row["question_id"], row["mode"])


def load_new_inputs():
    rows = {}
    for scenario_id in SCENARIOS:
        path = NEW_DIR / ("generation_inputs_%s.jsonl" % scenario_id.replace("scenario_", "sc"))
        for row in rq2.read_jsonl(path):
            rows[_key(row)] = row
    return rows


def load_new_retrieval():
    rows = {}
    for scenario_id in SCENARIOS:
        path = NEW_DIR / ("retrieval_%s.jsonl" % scenario_id.replace("scenario_", "sc"))
        for row in rq2.read_jsonl(path):
            rows[_key(row)] = row
    return rows


def check_inputs(new_inputs, new_retrieval, config, errors):
    """Passi 1-4."""
    for key, row in sorted(new_inputs.items()):
        scenario_id, question_id, mode = key
        where = "%s %s %s" % key
        atteso = rq2.budget_tokens(config, scenario_id)

        if row["model_answer"] is not None:
            errors.append("%s: l'input contiene gia' una risposta" % where)

        if mode == rq2.FULL_HISTORY:
            if row["budget_tokens"] is not None or row["budget_applies"] or row["retrieval_used"]:
                errors.append("%s: FULL_HISTORY deve restare fuori dal budget e senza retrieval" % where)
        else:
            if row["budget_tokens"] != atteso:
                errors.append("%s: budget dichiarato %s, la configurazione ne prevede %s"
                              % (where, row["budget_tokens"], atteso))
            if row["budget_applies"] != (atteso is not None):
                errors.append("%s: budget_applies incoerente con il budget dello scenario" % where)
            if not row["retrieval_used"]:
                errors.append("%s: il retrieval e' stato usato e va dichiarato" % where)
            if row["retrieval_label"] != LABEL:
                errors.append("%s: etichetta '%s', attesa '%s'"
                              % (where, row["retrieval_label"], LABEL))

            source = new_retrieval.get(key)
            if source is None:
                errors.append("%s: manca la riga di retrieval corrispondente" % where)
                continue
            if row["context_item_ids"] != source["selected_item_ids"]:
                errors.append("%s: il contesto del prompt non coincide con il retrieval" % where)
            for item in source["selected"]:
                if item["render"] not in row["prompt"]:
                    errors.append("%s: la riga %s non compare nel prompt" % (where, item["item_id"]))

        if row["prompt"].count("Domanda:") != 1:
            errors.append("%s: il prompt contiene piu' di una domanda" % where)
        for etichetta in inputs_rq2.ORACLE_LABELS:
            if etichetta in row["prompt"]:
                errors.append("%s: il prompt contiene un campo delle annotazioni (%s)" % (where, etichetta))


def check_oracle_absent(new_inputs, errors):
    """Passo 3, parte che richiede le annotazioni: nessuna risposta attesa nel prompt."""
    for scenario_id in SCENARIOS:
        questions = rq2.load_questions(scenario_id)
        for question in questions:
            for key, row in new_inputs.items():
                if key[0] != scenario_id or key[1] != question["question_id"]:
                    continue
                if question["expected_answer"] in row["prompt"]:
                    errors.append("%s %s %s: il prompt contiene la risposta attesa" % key)


def generation_state(answers_path, new_inputs):
    """Passo 5: che cosa resta da chiamare."""
    attesi = {key for key in new_inputs
              if key[0] in TO_GENERATE and key[2] in TO_GENERATE[key[0]]}
    fatti, in_errore = {}, {}
    if Path(answers_path).exists():
        for row in rq2.read_jsonl(answers_path):
            key = _key(row)
            if row.get("error") is None and row.get("model_answer"):
                fatti[key] = row
                in_errore.pop(key, None)
            else:
                if key not in fatti:
                    in_errore[key] = row
    return {
        "attesi": sorted(attesi),
        "completati": sorted(fatti),
        "in_errore": sorted(in_errore),
        "da_eseguire": sorted(attesi - set(fatti)),
        "estranei": sorted(set(fatti) - attesi),
    }


def check_reuse(new_inputs, errors):
    """Passo 6: il riuso vale solo se il prompt e' identico."""
    esito = {}
    for (scenario_id, mode), path in sorted(REUSED.items()):
        storico = {}
        full = rq2.REPO_ROOT / path
        if not full.exists():
            errors.append("%s %s: manca il file degli input storici %s" % (scenario_id, mode, path))
            continue
        for row in rq2.read_jsonl(full):
            if (row["scenario_id"], row["mode"]) == (scenario_id, mode):
                storico[row["question_id"]] = row

        nuove = {k[1]: v for k, v in new_inputs.items() if (k[0], k[2]) == (scenario_id, mode)}
        identici, diversi, mancanti = 0, [], []
        for question_id, row in sorted(nuove.items()):
            vecchia = storico.get(question_id)
            if vecchia is None:
                mancanti.append(question_id)
            elif vecchia["prompt"] == row["prompt"]:
                identici += 1
            else:
                diversi.append(question_id)

        risposte = rq2.REPO_ROOT / REUSED_ANSWERS[(scenario_id, mode)]
        risposte_presenti = 0
        if risposte.exists():
            risposte_presenti = sum(
                1 for row in rq2.read_jsonl(risposte)
                if row["scenario_id"] == scenario_id and row["mode"] == mode
                and row.get("error") is None and row.get("model_answer")
            )
        else:
            errors.append("%s %s: manca il file delle risposte storiche %s"
                          % (scenario_id, mode, REUSED_ANSWERS[(scenario_id, mode)]))

        if diversi or mancanti:
            errors.append("%s %s: il riuso NON e' lecito — prompt diversi: %s; mancanti: %s"
                          % (scenario_id, mode, ", ".join(diversi) or "nessuno",
                             ", ".join(mancanti) or "nessuno"))
        if risposte_presenti != len(nuove):
            errors.append("%s %s: %d risposte storiche per %d input da riusare"
                          % (scenario_id, mode, risposte_presenti, len(nuove)))

        esito["%s/%s" % (scenario_id, mode)] = {
            "prompt_identici": identici,
            "prompt_totali": len(nuove),
            "input_storici": path,
            "risposte_storiche": REUSED_ANSWERS[(scenario_id, mode)],
            "risposte_disponibili": risposte_presenti,
            "riuso_lecito": not diversi and not mancanti and risposte_presenti == len(nuove),
        }
    return esito


def main(argv=None):
    parser = argparse.ArgumentParser(description="Controlli prima della generazione.")
    parser.add_argument("--answers", default=str(NEW_DIR / "generation_dev_budget_per_scenario.jsonl"))
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)

    config = rq2.load_config(VARIANT_CONFIG)
    new_inputs = load_new_inputs()
    new_retrieval = load_new_retrieval()
    errors = []

    check_inputs(new_inputs, new_retrieval, config, errors)
    check_oracle_absent(new_inputs, errors)
    riuso = check_reuse(new_inputs, errors)
    stato = generation_state(args.answers, new_inputs)

    print("Controlli prima della generazione — configurazione %s" % config["config_id"])
    print("=" * 78)
    print("Input letti: %d" % len(new_inputs))
    print("Budget per scenario:")
    for scenario_id in SCENARIOS:
        print("  %-13s %s" % (scenario_id, rq2.budget_label(rq2.budget_tokens(config, scenario_id))))
    print("-" * 78)
    print("Da generare: %d celle-domanda" % len(stato["attesi"]))
    print("  gia' completate: %d" % len(stato["completati"]))
    print("  in errore da rifare: %d" % len(stato["in_errore"]))
    print("  ancora da chiamare: %d" % len(stato["da_eseguire"]))
    if stato["estranei"]:
        print("  ATTENZIONE: %d risposte non previste da questa prova" % len(stato["estranei"]))
    print("-" * 78)
    print("Riuso senza rigenerare:")
    for nome, dati in sorted(riuso.items()):
        print("  %-26s prompt identici %d/%d, risposte disponibili %d — %s"
              % (nome, dati["prompt_identici"], dati["prompt_totali"],
                 dati["risposte_disponibili"],
                 "riuso lecito" if dati["riuso_lecito"] else "RIUSO NON LECITO"))
    print("-" * 78)
    if errors:
        print("Controlli falliti:")
        for error in errors:
            print("  - %s" % error)
    else:
        print("Tutti i controlli superati. Nessuna risposta presente negli input.")

    if args.json:
        rq2.write_json({"errors": errors, "stato_generazione": stato, "riuso": riuso}, args.json)
        print("Esito scritto in %s." % rq2.relative(Path(args.json)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
