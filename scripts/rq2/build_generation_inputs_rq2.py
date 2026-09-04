#!/usr/bin/env python3
"""Costruzione degli input di generazione di RQ2 per T, F e FULL_HISTORY.

Prepara soltanto *cosa verra' inviato al modello*: non chiama nessun LLM e non
calcola metriche. Il runner delle chiamate resta quello gia' usato dal pilot,
`scripts/run_generation.py`, che accetta un file di input e un file di uscita.

Da dove arriva il contesto:
  - T, F, U e G: esattamente le righe salvate dal retrieval RQ2, nell'ordine in
    cui sono state selezionate. Il retrieval non viene rieseguito, e le righe
    non vengono riformattate: e' lo stesso testo su cui e' stato applicato il
    budget, quindi il contesto inviato al modello coincide con quello contato;
  - FULL_HISTORY: tutti i messaggi dell'utente dello scenario in ordine
    cronologico, senza retrieval e fuori dal budget delle altre modalita'.

Il prompt comune e' quello del pilot: stesse istruzioni, stessa struttura
"Istruzioni / Contesto / Domanda". Cambia soltanto che cosa c'e' nel contesto,
che e' esattamente la variabile studiata da RQ2.

Nel prompt non entra nulla delle annotazioni: niente risposta attesa, fatti
obbligatori, evidenze richieste, operazioni, relazioni o comportamento atteso.

Ogni prova e' indipendente: un prompt contiene una sola domanda e le risposte
non aggiornano la memoria delle prove successive.

Uso:
    python3 scripts/rq2/build_generation_inputs_rq2.py --scenario scenario_02
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402

sys.path.insert(0, str(rq2.SCRIPTS_DIR))
import build_generation_inputs as pilot_inputs  # noqa: E402  (prompt comune)

DEFAULT_RETRIEVAL = rq2.RQ2_RESULTS_DIR / "retrieval_rq2.jsonl"
DEFAULT_OUT = rq2.RQ2_RESULTS_DIR / "generation_inputs_rq2.jsonl"

# Istruzioni e dichiarazione di contesto vuoto: identiche al pilot, importate
# invece che ricopiate, cosi' non possono divergere.
INSTRUCTIONS = pilot_inputs.INSTRUCTIONS
EMPTY_CONTEXT = pilot_inputs.EMPTY_CONTEXT

RETRIEVAL_MODES = ("T", "F", "U", "G")


def format_context(renders):
    """Blocco di contesto: le righe gia' formattate dal retrieval, in ordine.

    Non si riformatta nulla: la riga che finisce nel prompt e' la stessa su cui
    il retrieval ha applicato il budget.
    """
    if not renders:
        return EMPTY_CONTEXT
    return "\n".join(renders)


def build_prompt(context, question_text):
    return (
        "Istruzioni:\n"
        "%s\n"
        "\n"
        "Contesto:\n"
        "%s\n"
        "\n"
        "Domanda:\n"
        "%s"
    ) % (INSTRUCTIONS, context, question_text)


def build(scenario_ids, config, retrieval_rows, modes_override=None):
    retrieval = {(r["scenario_id"], r["question_id"], r["mode"]): r for r in retrieval_rows}
    rows = []
    skipped = []

    for scenario_id in scenario_ids:
        scenario = rq2.load_scenario(scenario_id)
        questions = rq2.load_questions(scenario_id)
        history = rq2.message_items(scenario)
        history_ids = [item["item_id"] for item in history]
        history_renders = [item["render"] for item in history]
        history_tokens = sum(item["tokens"] for item in history)
        history_content = sum(item["content_tokens"] for item in history)
        runnable = modes_override if modes_override is not None else rq2.runnable_modes(scenario_id, config)

        for question in questions:
            for mode in runnable:
                if mode == rq2.FULL_HISTORY:
                    rows.append(
                        {
                            "scenario_id": scenario_id,
                            "question_id": question["question_id"],
                            "mode": mode,
                            "context_item_ids": list(history_ids),
                            "context_provenance_message_ids": list(history_ids),
                            "context_tokens": history_tokens,
                            "context_content_tokens": history_content,
                            "context_overhead_tokens": history_tokens - history_content,
                            "budget_applies": False,
                            "budget_tokens": None,
                            "retrieval_used": False,
                            "retrieval_label": None,
                            "reading_scope": None,
                            "prompt": build_prompt(format_context(history_renders), question["text"]),
                            "model_answer": None,
                        }
                    )
                    continue

                if mode not in RETRIEVAL_MODES:
                    skipped.append((scenario_id, mode, "modalita' non prevista dal retrieval"))
                    continue

                row = retrieval.get((scenario_id, question["question_id"], mode))
                if row is None:
                    skipped.append((scenario_id, mode, "retrieval mancante per %s" % question["question_id"]))
                    continue

                renders = [item["render"] for item in row["selected"]]
                rows.append(
                    {
                        "scenario_id": scenario_id,
                        "question_id": question["question_id"],
                        "mode": mode,
                        "context_item_ids": list(row["selected_item_ids"]),
                        "context_provenance_message_ids": list(row["context_provenance_message_ids"]),
                        "context_tokens": row["context_tokens"],
                        "context_content_tokens": row["context_content_tokens"],
                        "context_overhead_tokens": row["context_overhead_tokens"],
                        "budget_applies": True,
                        "budget_tokens": row["budget_tokens"],
                        "retrieval_used": True,
                        "retrieval_label": row["label"],
                        "reading_scope": row.get("reading_scope"),
                        "prompt": build_prompt(format_context(renders), question["text"]),
                        "model_answer": None,
                    }
                )
    return rows, skipped


# --------------------------------------------------------------------------
# Controlli
# --------------------------------------------------------------------------

ORACLE_LABELS = ("Risposta attesa", "Fatti obbligatori", "Evidenze", "Raggiungibilit",
                 "Comportamento atteso", "Operazione attesa", "Relazioni richieste")


def check(rows, scenario_ids, config, retrieval_rows):
    errors = []
    retrieval = {(r["scenario_id"], r["question_id"], r["mode"]): r for r in retrieval_rows}
    by_key = {(r["scenario_id"], r["question_id"], r["mode"]): r for r in rows}
    if len(by_key) != len(rows):
        errors.append("esistono input duplicati per la stessa terna scenario/domanda/modalita'")

    for scenario_id in scenario_ids:
        scenario = rq2.load_scenario(scenario_id)
        questions = rq2.load_questions(scenario_id)
        texts = {m["message_id"]: m["content"] for m in rq2.message_index(scenario).values()}
        history_ids = [entry["message_id"] for entry in rq2.user_messages(scenario)]

        for question in questions:
            question_id = question["question_id"]
            for mode in {r["mode"] for r in rows if r["scenario_id"] == scenario_id}:
                row = by_key.get((scenario_id, question_id, mode))
                if row is None:
                    errors.append("input mancante: %s %s %s" % (scenario_id, question_id, mode))
                    continue
                where = "%s %s %s" % (scenario_id, question_id, mode)

                # 1. il contesto e' esattamente quello salvato dal retrieval
                if mode in RETRIEVAL_MODES:
                    source = retrieval[(scenario_id, question_id, mode)]
                    if row["context_item_ids"] != source["selected_item_ids"]:
                        errors.append("%s: contesto diverso dal retrieval salvato" % where)
                    if row["context_tokens"] != source["context_tokens"]:
                        errors.append("%s: token del contesto diversi dal retrieval salvato" % where)
                    # 2. budget rispettato dal blocco realmente inserito nel prompt
                    budget = source["budget_tokens"]
                    block = format_context([item["render"] for item in source["selected"]])
                    counted = rq2.count_tokens(block) if source["selected"] else 0
                    if counted != row["context_tokens"]:
                        errors.append("%s: il blocco di contesto misura %d token, ne erano stati contati %d"
                                      % (where, counted, row["context_tokens"]))
                    if counted > budget and not source["budget_exceeded_by_first_item"]:
                        errors.append("%s: contesto di %d token oltre il budget di %d"
                                      % (where, counted, budget))
                    for item in source["selected"]:
                        if item["render"] not in row["prompt"]:
                            errors.append("%s: la riga di contesto %s non compare nel prompt"
                                          % (where, item["item_id"]))

                # 3. FULL_HISTORY: tutti i messaggi utente, in ordine, fuori budget
                if mode == rq2.FULL_HISTORY:
                    if row["context_item_ids"] != history_ids:
                        errors.append("%s: FULL_HISTORY deve contenere tutti i messaggi utente in ordine" % where)
                    if row["context_tokens"] <= rq2.budget_tokens(config):
                        errors.append("%s: FULL_HISTORY dovrebbe superare il budget delle altre modalita'" % where)
                    if row["budget_applies"]:
                        errors.append("%s: FULL_HISTORY non deve essere soggetto al budget" % where)
                    if row["retrieval_used"]:
                        errors.append("%s: FULL_HISTORY non deve usare il retrieval" % where)

                # 4. ordine cronologico dei messaggi in FULL_HISTORY
                if mode == rq2.FULL_HISTORY:
                    positions = [history_ids.index(m) for m in row["context_item_ids"]]
                    if positions != sorted(positions):
                        errors.append("%s: FULL_HISTORY non e' in ordine cronologico" % where)

                # 5. niente oracle nel prompt
                if question["expected_answer"] in row["prompt"]:
                    errors.append("%s: il prompt contiene la risposta attesa" % where)
                for label in ORACLE_LABELS:
                    if label in row["prompt"]:
                        errors.append("%s: il prompt contiene un campo delle annotazioni (%s)" % (where, label))
                for other in questions:
                    if other["question_id"] != question_id and other["text"] in row["prompt"]:
                        errors.append("%s: il prompt contiene anche la domanda %s" % (where, other["question_id"]))

                # 6. una sola domanda, nessuna risposta precedente
                if row["prompt"].count("Domanda:") != 1:
                    errors.append("%s: il prompt contiene piu' di una domanda" % where)
                if not row["prompt"].endswith(question["text"]):
                    errors.append("%s: il prompt non termina con la domanda" % where)
                if row["model_answer"] is not None:
                    errors.append("%s: model_answer deve essere null" % where)

                # 7. provenienza valida: ogni messaggio citato appartiene allo scenario
                for message_id in row["context_provenance_message_ids"]:
                    if message_id not in texts:
                        errors.append("%s: il contesto cita il messaggio estraneo %s" % (where, message_id))
    return errors


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def print_summary(rows):
    print("%-13s %-13s %-7s %-11s %-8s %-9s %s"
          % ("scenario", "modalita'", "input", "elementi", "contenuto", "overhead", "budget"))
    keys = []
    for row in rows:
        key = (row["scenario_id"], row["mode"])
        if key not in keys:
            keys.append(key)
    for scenario_id, mode in keys:
        subset = [r for r in rows if r["scenario_id"] == scenario_id and r["mode"] == mode]
        items = sum(len(r["context_item_ids"]) for r in subset) / len(subset)
        content = sum(r["context_content_tokens"] for r in subset) / len(subset)
        overhead = sum(r["context_overhead_tokens"] for r in subset) / len(subset)
        budget = "%d token" % subset[0]["budget_tokens"] if subset[0]["budget_applies"] else "fuori budget"
        print("%-13s %-13s %-7d %-11.1f %-8.1f %-9.1f %s"
              % (scenario_id, mode, len(subset), items, content, overhead, budget))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Costruisce gli input di generazione di RQ2.")
    parser.add_argument("--scenario", action="append", default=None)
    parser.add_argument("--retrieval", default=str(DEFAULT_RETRIEVAL))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--modes", nargs="*", default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = rq2.load_config()
    scenario_ids = args.scenario or list(rq2.SCENARIO_IDS)

    retrieval_path = Path(args.retrieval)
    if not retrieval_path.exists():
        print("File del retrieval mancante: %s. Eseguire prima scripts/rq2/run_retrieval_rq2.py."
              % rq2.relative(retrieval_path), file=sys.stderr)
        return 1
    retrieval_rows = rq2.read_jsonl(retrieval_path)

    rows, skipped = build(scenario_ids, config, retrieval_rows, args.modes)
    if not rows:
        print("Nessun input costruito.", file=sys.stderr)
        return 1

    errors = check(rows, scenario_ids, config, retrieval_rows)
    if errors:
        print("Controlli falliti:", file=sys.stderr)
        for error in errors:
            print("  - %s" % error, file=sys.stderr)
        return 1

    path = rq2.write_jsonl(rows, args.out)
    print("Input di generazione RQ2 (nessun modello e' stato chiamato)")
    print("-" * 78)
    print_summary(rows)
    print("-" * 78)
    for scenario_id, mode, reason in sorted(set(skipped)):
        print("saltato: %s / %s — %s" % (scenario_id, mode, reason))
    print("Controlli superati.")
    print("Input scritti in %s (%d righe)." % (rq2.relative(path), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
