#!/usr/bin/env python3
"""Costruzione degli input di generazione per C0, C1, C2 e FULL_HISTORY.

Lo script prepara soltanto *cosa verra' inviato al modello*: non chiama nessun
LLM, non genera risposte e non calcola metriche end-to-end. Per ogni domanda
del pilot produce quattro prompt indipendenti, uno per modalita'.

Da dove arrivano i contesti:
  - C0: nessun messaggio. Il contesto dichiara esplicitamente l'assenza di
    informazioni precedenti;
  - C1 e C2: esattamente i `retrieved_message_ids` gia' salvati in
    `results/retrieval_pilot.jsonl`, nell'ordine restituito dal retrieval. Il
    retrieval non viene rieseguito e i suoi risultati non vengono corretti;
  - FULL_HISTORY: controllo diagnostico, non una quarta condizione. Contiene
    tutti i messaggi dell'utente delle Sessioni 1-4 in ordine cronologico,
    senza retrieval. I messaggi dell'assistente restano esclusi perche' non
    introducono fatti autorevoli e non sono indicizzati nelle altre modalita'.

Nel prompt non entra nulla dell'oracle: niente risposta attesa, fatti
obbligatori, evidenze richieste, raggiungibilita', classificazione o esiti dei
dry run. `reachable` e `retrieval_success` restano nella riga JSONL come campi
diagnostici, fuori dal prompt.

Ogni prova e' indipendente: un prompt contiene una sola domanda, non riporta
risposte di prove precedenti e non modifica lo stato dello scenario.

Uso:
    python3 scripts/build_generation_inputs.py

Lo script non modifica i file di input. Scrive una riga JSON per input in
`results/generation_inputs.jsonl`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIO_DIR = REPO_ROOT / "data" / "scenarios"
RETRIEVAL_PATH = REPO_ROOT / "results" / "retrieval_pilot.jsonl"
OUTPUT_PATH = REPO_ROOT / "results" / "generation_inputs.jsonl"

MODES = ("C0", "C1", "C2", "FULL_HISTORY")
RETRIEVED_MODES = ("C1", "C2")
HISTORY_ROLE = "user"

# Modalita' diagnostica: eredita `reachable` da C2 e non ha retrieval.
FULL_HISTORY = "FULL_HISTORY"
FULL_HISTORY_REFERENCE_CONDITION = "C2"

INSTRUCTIONS = (
    "Rispondi utilizzando soltanto le informazioni presenti nel contesto.\n"
    "Non utilizzare conoscenze esterne e non inventare informazioni.\n"
    "Se il contesto non contiene tutte le informazioni necessarie, dichiara "
    "che le informazioni disponibili non sono sufficienti.\n"
    "Fornisci una risposta breve e diretta."
)

EMPTY_CONTEXT = "Nessuna informazione precedente disponibile."

# Domanda di cui stampare la traccia leggibile: serve a distinguere un errore
# di retrieval dall'incapacita' del modello di rispondere.
TRACE_QUESTION_ID = "SC02-Q6"
TRACE_MODES = ("C1", "C2", FULL_HISTORY)


# --------------------------------------------------------------------------
# Caricamento
# --------------------------------------------------------------------------

def load_scenarios(directory=SCENARIO_DIR):
    paths = sorted(Path(directory).glob("scenario_*.json"))
    scenarios = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            scenarios.append(json.load(handle))
    return scenarios


def load_retrieval(path=RETRIEVAL_PATH):
    """Righe del pilot indicizzate per (scenario_id, question_id, condition)."""
    path = Path(path)
    if not path.exists():
        raise SystemExit(
            "File del retrieval mancante: %s. Eseguire prima "
            "scripts/run_retrieval_pilot.py." % path
        )
    index = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            index[(row["scenario_id"], row["question_id"], row["condition"])] = row
    return index


def message_texts(scenario):
    """message_id -> contenuto, per tutti i messaggi dello scenario."""
    texts = {}
    for session in scenario["sessions"]:
        for message in session["messages"]:
            texts[message["message_id"]] = message["content"]
    return texts


def full_history_ids(scenario):
    """Messaggi dell'utente delle Sessioni 1-4, in ordine cronologico."""
    entries = []
    for session in scenario["sessions"]:
        for message in session["messages"]:
            if message["role"] != HISTORY_ROLE:
                continue
            entries.append((session["order"], message["order"], message["message_id"]))
    entries.sort()
    return [message_id for _session_order, _message_order, message_id in entries]


# --------------------------------------------------------------------------
# Costruzione del prompt
# --------------------------------------------------------------------------

def format_context(message_ids, texts):
    """Un messaggio per riga, preceduto dal proprio identificatore."""
    if not message_ids:
        return EMPTY_CONTEXT
    return "\n".join("[%s] %s" % (message_id, texts[message_id]) for message_id in message_ids)


def build_prompt(message_ids, texts, question_text):
    return (
        "Istruzioni:\n"
        "%s\n"
        "\n"
        "Contesto:\n"
        "%s\n"
        "\n"
        "Domanda:\n"
        "%s"
    ) % (INSTRUCTIONS, format_context(message_ids, texts), question_text)


def build_row(scenario, question, mode, texts, history_ids, retrieval):
    """Un input indipendente: uno scenario, una domanda, una modalita'."""
    scenario_id = scenario["scenario_id"]
    question_id = question["question_id"]

    if mode == FULL_HISTORY:
        # Controllo diagnostico: nessun retrieval, quindi `retrieval_success`
        # non e' definito. La raggiungibilita' e' quella del perimetro C2,
        # che contiene gli stessi messaggi.
        context_ids = list(history_ids)
        reference = retrieval[(scenario_id, question_id, FULL_HISTORY_REFERENCE_CONDITION)]
        reachable = reference["reachable"]
        retrieval_success = None
    else:
        row = retrieval[(scenario_id, question_id, mode)]
        # Ordine del retrieval conservato cosi' com'e': non va riordinato ne'
        # corretto a mano.
        context_ids = list(row["retrieved_message_ids"])
        reachable = row["reachable"]
        retrieval_success = row["retrieval_success"]

    return {
        "scenario_id": scenario_id,
        "question_id": question_id,
        "mode": mode,
        "context_message_ids": context_ids,
        "prompt": build_prompt(context_ids, texts, question["text"]),
        "model_answer": None,
        "reachable": reachable,
        "retrieval_success": retrieval_success,
    }


def build(scenarios, retrieval):
    rows = []
    for scenario in scenarios:
        texts = message_texts(scenario)
        history_ids = full_history_ids(scenario)
        for question in scenario["questions"]:
            for mode in MODES:
                rows.append(build_row(scenario, question, mode, texts, history_ids, retrieval))
    return rows


# --------------------------------------------------------------------------
# Controlli
# --------------------------------------------------------------------------

def check(rows, scenarios, retrieval):
    """Controlli finali. Restituisce la lista degli errori trovati."""
    errors = []
    questions = [(s["scenario_id"], q) for s in scenarios for q in s["questions"]]
    expected_rows = len(questions) * len(MODES)

    # 1. numero totale di input.
    if len(rows) != expected_rows:
        errors.append("righe attese %d, trovate %d" % (expected_rows, len(rows)))

    # 2. stesso numero di input per ogni modalita'.
    for mode in MODES:
        count = len([row for row in rows if row["mode"] == mode])
        if count != len(questions):
            errors.append("modalita' %s: attesi %d input, trovati %d" % (mode, len(questions), count))

    by_key = {(row["scenario_id"], row["question_id"], row["mode"]): row for row in rows}
    if len(by_key) != len(rows):
        errors.append("esistono input duplicati per la stessa terna scenario/domanda/modalita'")

    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        texts = message_texts(scenario)
        history_ids = full_history_ids(scenario)
        for question in scenario["questions"]:
            question_id = question["question_id"]
            for mode in MODES:
                row = by_key.get((scenario_id, question_id, mode))
                if row is None:
                    errors.append("input mancante: %s %s %s" % (scenario_id, question_id, mode))
                    continue

                # 3. C0 non contiene messaggi.
                if mode == "C0":
                    if row["context_message_ids"]:
                        errors.append("%s %s C0: il contesto contiene messaggi" % (scenario_id, question_id))
                    if EMPTY_CONTEXT not in row["prompt"]:
                        errors.append("%s %s C0: manca la dichiarazione di contesto vuoto" % (scenario_id, question_id))

                # 4. C1 e C2 identici al retrieval gia' salvato.
                if mode in RETRIEVED_MODES:
                    source = retrieval[(scenario_id, question_id, mode)]
                    if row["context_message_ids"] != source["retrieved_message_ids"]:
                        errors.append(
                            "%s %s %s: contesto diverso dal retrieval salvato" % (scenario_id, question_id, mode)
                        )
                    if row["reachable"] != source["reachable"] or row["retrieval_success"] != source["retrieval_success"]:
                        errors.append(
                            "%s %s %s: campi diagnostici diversi dal retrieval salvato"
                            % (scenario_id, question_id, mode)
                        )

                # 5. FULL_HISTORY: tutti i messaggi dell'utente delle 4 sessioni.
                if mode == FULL_HISTORY:
                    if row["context_message_ids"] != history_ids:
                        errors.append(
                            "%s %s FULL_HISTORY: attesi %s, trovati %s"
                            % (scenario_id, question_id, history_ids, row["context_message_ids"])
                        )
                    reference = retrieval[(scenario_id, question_id, FULL_HISTORY_REFERENCE_CONDITION)]
                    if row["reachable"] != reference["reachable"]:
                        errors.append("%s %s FULL_HISTORY: reachable diverso da C2" % (scenario_id, question_id))
                    if row["retrieval_success"] is not None:
                        errors.append("%s %s FULL_HISTORY: retrieval_success deve essere null" % (scenario_id, question_id))

                # 6. nel prompt non entra nulla dell'oracle.
                if question["expected_answer"] in row["prompt"]:
                    errors.append("%s %s %s: il prompt contiene la risposta attesa" % (scenario_id, question_id, mode))
                for label in ("Risposta attesa", "Fatti obbligatori", "Evidenze", "Raggiungibilit"):
                    if label in row["prompt"]:
                        errors.append(
                            "%s %s %s: il prompt contiene un campo dell'oracle (%s)"
                            % (scenario_id, question_id, mode, label)
                        )

                # 7. indipendenza: una sola domanda, nessuna risposta precedente,
                #    solo messaggi appartenenti allo scenario.
                if row["prompt"].count("Domanda:") != 1:
                    errors.append("%s %s %s: il prompt contiene piu' di una domanda" % (scenario_id, question_id, mode))
                if not row["prompt"].endswith(question["text"]):
                    errors.append("%s %s %s: il prompt non termina con la domanda" % (scenario_id, question_id, mode))
                for other in scenario["questions"]:
                    if other["question_id"] != question_id and other["text"] in row["prompt"]:
                        errors.append(
                            "%s %s %s: il prompt contiene anche la domanda %s"
                            % (scenario_id, question_id, mode, other["question_id"])
                        )
                if row["model_answer"] is not None:
                    errors.append("%s %s %s: model_answer deve essere null" % (scenario_id, question_id, mode))
                for message_id in row["context_message_ids"]:
                    if message_id not in texts:
                        errors.append(
                            "%s %s %s: messaggio %s estraneo allo scenario"
                            % (scenario_id, question_id, mode, message_id)
                        )
                    elif "[%s] %s" % (message_id, texts[message_id]) not in row["prompt"]:
                        errors.append(
                            "%s %s %s: il messaggio %s non compare nel contesto con il suo identificatore"
                            % (scenario_id, question_id, mode, message_id)
                        )

    return errors


# --------------------------------------------------------------------------
# Riepilogo e traccia
# --------------------------------------------------------------------------

def print_summary(rows):
    print("Input di generazione costruiti (nessun modello e' stato chiamato)")
    print("-" * 72)
    print("%-14s %-8s %s" % ("Modalita'", "input", "messaggi nel contesto (min-max)"))
    for mode in MODES:
        mode_rows = [row for row in rows if row["mode"] == mode]
        sizes = [len(row["context_message_ids"]) for row in mode_rows]
        extent = "%d-%d" % (min(sizes), max(sizes)) if sizes else "-"
        print("%-14s %-8d %s" % (mode, len(mode_rows), extent))
    print("-" * 72)
    print("Input totali: %d" % len(rows))


def print_trace(rows):
    traced = [row for row in rows if row["question_id"] == TRACE_QUESTION_ID and row["mode"] in TRACE_MODES]
    if not traced:
        return
    print()
    print("Traccia di %s" % TRACE_QUESTION_ID)
    print("=" * 72)
    order = {mode: index for index, mode in enumerate(TRACE_MODES)}
    for row in sorted(traced, key=lambda item: order[item["mode"]]):
        print()
        print("--- %s | contesto: %s ---" % (row["mode"], ", ".join(row["context_message_ids"]) or "(nessuno)"))
        print(row["prompt"])


def write_jsonl(rows, path=OUTPUT_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def main():
    scenarios = load_scenarios()
    if not scenarios:
        print("Nessuno scenario trovato in %s" % SCENARIO_DIR, file=sys.stderr)
        return 1

    retrieval = load_retrieval()
    rows = build(scenarios, retrieval)

    errors = check(rows, scenarios, retrieval)
    if errors:
        print("Controlli falliti:", file=sys.stderr)
        for error in errors:
            print("  - %s" % error, file=sys.stderr)
        return 1

    path = write_jsonl(rows)
    print_summary(rows)
    print_trace(rows)
    print()
    print("Controlli superati.")
    print("Input scritti in %s (%d righe)." % (path.relative_to(REPO_ROOT), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
