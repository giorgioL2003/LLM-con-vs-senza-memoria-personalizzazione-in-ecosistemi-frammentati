#!/usr/bin/env python3
"""Verifica offline del confronto U / GER. Nessuna chiamata a nessun modello.

Che cosa fa, nell'ordine:

  1. controlla lo scenario di sviluppo SC05 (nove sessioni) e le sue domande;
  2. costruisce la memoria di U per SC05 con il **codice vero**
     (`build_memory_updates.py`) leggendo **fixture dichiarate** al posto delle
     risposte del modello: le operazioni vengono davvero applicate o rifiutate;
  3. esegue il retrieval di U e di GER sullo **stesso stato**, sulle **stesse
     domande**, con lo **stesso budget** — su SC05 e sugli stati gia' salvati di
     SC03 e SC04, dichiarando a GER la sessione raggiunta;
  4. verifica le proprieta' essenziali di GER (quote, riutilizzo, nessun
     doppione, nessun troncamento, ranking calcolato prima della divisione,
     stato non modificato);
  5. costruisce i prompt di U, GER e FULL_HISTORY per SC05 senza inviarli;
  6. scrive una traccia leggibile con elementi selezionati, livello, punteggio,
     consumo del budget e motivi di esclusione.

Gli output finiscono in `results/rq2/ger_dev/` e **non sono risultati
sperimentali**: la memoria di SC05 nasce da fixture scritte a mano, non dal
modello. FULL_HISTORY resta un controllo diagnostico fuori dal budget.

Uso:
    python3 scripts/rq2/run_ger_check.py
    python3 scripts/rq2/run_ger_check.py --out results/rq2/ger_dev_prova
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import build_memory_updates as memory  # noqa: E402
import hierarchical_memory as ger  # noqa: E402
import fixture_replay  # noqa: E402
import run_retrieval_rq2 as retrieval_rq2  # noqa: E402
import build_generation_inputs_rq2 as generation_inputs  # noqa: E402

FIXTURE_DIR = rq2.REPO_ROOT / "tests" / "fixtures" / "rq2"
SC05 = rq2.GER_SCENARIO_ID
SC05_FACTS = FIXTURE_DIR / "scenario_05_facts_fixture.jsonl"
SC05_UPDATES = FIXTURE_DIR / "scenario_05_update_answers_fixture.json"

# Ogni versione delle regole scrive in una cartella propria: la verifica delle
# regole 0.1 resta leggibile in `results/rq2/ger_dev/` e non viene sovrascritta.
DEFAULT_OUT_DIR = rq2.RQ2_RESULTS_DIR / "ger_dev_v2"
OUT_DIR = DEFAULT_OUT_DIR
LABEL = "fixture-ger (nessuna chiamata al modello)"

# Stati gia' salvati di U, versione di riferimento dichiarata in
# MEMORIA_GERARCHICA.md. GER li legge e non li scrive mai.
REAL_STATES = {
    "scenario_03": {
        "facts": rq2.RQ2_RESULTS_DIR / "facts" / "scenario_03_facts.jsonl",
        "state": rq2.RQ2_RESULTS_DIR / "memory_repair_v3" / "scenario_03_state.json",
    },
    "scenario_04": {
        "facts": rq2.RQ2_RESULTS_DIR / "facts" / "scenario_04_facts.jsonl",
        "state": rq2.RQ2_RESULTS_DIR / "sc04_repair_v3" / "scenario_04_state.json",
    },
}


def declare_session_reached(scenario_id, entries, errors):
    """Sessione raggiunta da dichiarare a GER, con il suo controllo.

    Questi stati sono costruiti su **tutte** le sessioni della conversazione,
    quindi la sessione raggiunta e' l'ultima dello scenario. Non lo si da' per
    scontato: se lo stato si fermasse prima, sarebbe uno stato intermedio e
    prendere l'ultima sessione dello scenario sarebbe sbagliato.
    """
    sessioni = len(rq2.load_scenario(scenario_id)["sessions"])
    con_voci = ger.last_session_order(entries)
    if con_voci > sessioni:
        errors.append("%s: lo stato cita la sessione %d, lo scenario ne ha %d"
                      % (scenario_id, con_voci, sessioni))
        return None
    if con_voci < sessioni:
        errors.append(
            "%s: lo stato arriva alla sessione %d su %d. E' uno stato intermedio: "
            "la sessione raggiunta va dichiarata a mano, non dedotta dallo scenario."
            % (scenario_id, con_voci, sessioni))
        return None
    return sessioni

MODES = ["U", "GER"]


def step(number, title):
    print()
    print("=" * 78)
    print("%d. %s" % (number, title))
    print("=" * 78)


# --------------------------------------------------------------------------
# 1. Lo scenario di sviluppo
# --------------------------------------------------------------------------

FORBIDDEN_SCENARIO_KEYS = ("questions", "expected_answer", "mandatory_facts", "oracle",
                           "expected_operations", "expected_state")


def check_scenario(errors):
    import json
    with open(rq2.SCENARIO_SOURCES[SC05][1], "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    for key in FORBIDDEN_SCENARIO_KEYS:
        if key in raw:
            errors.append("il file delle conversazioni di SC05 contiene '%s'" % key)

    scenario = rq2.load_scenario(SC05)
    sessions = rq2.sessions_in_order(scenario)
    seen = set()
    for index, session in enumerate(sessions, start=1):
        if session["order"] != index:
            errors.append("SC05 / %s: order incoerente" % session["session_id"])
        for position, message in enumerate(session["messages"], start=1):
            if message["order"] != position:
                errors.append("SC05 / %s: order incoerente" % message["message_id"])
            if message["message_id"] in seen:
                errors.append("SC05: message_id duplicato %s" % message["message_id"])
            seen.add(message["message_id"])

    questions = rq2.load_questions(SC05)
    for question in questions:
        if question["category"] not in rq2.ALLOWED_CATEGORIES:
            errors.append("%s: categoria non ammessa" % question["question_id"])
        for fact in question["required_facts"]:
            for message_id in fact["source_message_ids"]:
                if message_id not in seen:
                    errors.append("%s: evidenza su un messaggio inesistente (%s)"
                                  % (question["question_id"], message_id))
    if not any(q["expected_behavior"] == rq2.BEHAVIOR_ABSTAIN for q in questions):
        errors.append("SC05: manca la domanda sull'informazione mai fornita")

    budget = rq2.budget_tokens()
    history = rq2.message_items(scenario)
    history_tokens = sum(item["tokens"] for item in history)
    if history_tokens <= budget:
        errors.append("SC05: la storia (%d token) non supera il budget (%d)"
                      % (history_tokens, budget))

    print("sessioni: %d | messaggi utente: %d | domande: %d" % (len(sessions), len(history), len(questions)))
    print("storia completa: %d token contro un budget di %d (%.1f volte)"
          % (history_tokens, budget, history_tokens / budget))
    print("domande: %s" % ", ".join("%s/%s" % (q["question_id"].split("-")[-1], q["category"])
                                    for q in questions))
    return scenario, questions


# --------------------------------------------------------------------------
# 2. La memoria di U per SC05, dalle fixture, con il codice vero
# --------------------------------------------------------------------------

def build_sc05_state(scenario, config, errors):
    facts = rq2.read_jsonl(SC05_FACTS)
    runner = fixture_replay.make_runner(SC05_UPDATES)
    operations, entries, log = memory.run(scenario, facts, config, runner=runner,
                                          repair_attempts=0)
    log["label"] = LABEL
    log["fixture_sources"] = {"facts": rq2.relative(SC05_FACTS), "updates": rq2.relative(SC05_UPDATES)}

    rejected = [op for op in operations if not op["applied"]]
    if rejected:
        errors.append("SC05: la fixture normale non deve produrre rifiuti (%d)" % len(rejected))

    out = OUT_DIR / "memory"
    rq2.write_jsonl(operations, memory.operations_path(SC05, out))
    rq2.write_json(memory.state_document(SC05, entries, config, LABEL), memory.state_path(SC05, out))
    rq2.write_json(log, memory.log_path(SC05, out))

    last = ger.last_session_order(entries)
    levels = {level: [e for e in entries if ger.entry_level(e, last) == level] for level in ger.LEVELS}
    print("operazioni: %d proposte, %d applicate, %d rifiutate"
          % (len(operations), log["applied_count"], log["rejected_count"]))
    print("voci: %d (%d attive, %d in archivio di U)"
          % (len(entries), len([e for e in entries if e["status"] == rq2.STATE_ACTIVE]),
             len([e for e in entries if e["status"] != rq2.STATE_ACTIVE])))
    print("ultima sessione nello stato: %d | finestra di recenza: %d sessioni"
          % (last, ger.RECENCY_WINDOW_SESSIONS))
    for level in ger.LEVELS:
        print("  %-9s %2d voci  (sessioni %s)"
              % (level, len(levels[level]),
                 sorted({e["session_order"] for e in levels[level]})))
    if not levels[ger.LEVEL_ARCHIVE]:
        errors.append("SC05: nessuna voce e' passata in archivio: la partizione non e' esercitata")
    if not levels[ger.LEVEL_RECENT]:
        errors.append("SC05: nessuna voce recente")

    # Vecchio non significa superato, e viceversa: si guarda che i due assi
    # siano davvero indipendenti su questo scenario.
    vecchie_valide = [e for e in levels[ger.LEVEL_ARCHIVE] if e["status"] == rq2.STATE_ACTIVE]
    recenti_superate = [e for e in levels[ger.LEVEL_RECENT] if e["status"] != rq2.STATE_ACTIVE]
    print("  voci in archivio ancora attive: %d | voci recenti gia' superate o ritirate: %d"
          % (len(vecchie_valide), len(recenti_superate)))
    if not vecchie_valide:
        errors.append("SC05: nessuna voce vecchia ancora valida: il caso interessante non c'e'")
    return memory.state_path(SC05, out), entries


# --------------------------------------------------------------------------
# 3-4. Retrieval e proprieta'
# --------------------------------------------------------------------------

def state_fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def check_properties(rows, entries_by_scenario, budget, errors):
    """Proprieta' essenziali di GER, verificate sulle righe prodotte."""
    by_key = {(r["scenario_id"], r["question_id"], r["mode"]): r for r in rows}

    for (scenario_id, question_id, mode), row in sorted(by_key.items()):
        if mode != "GER":
            continue
        where = "%s %s" % (scenario_id, question_id)
        u_row = by_key.get((scenario_id, question_id, "U"))

        ids = row["selected_item_ids"]
        if len(ids) != len(set(ids)):
            errors.append("%s: GER ha selezionato due volte lo stesso elemento" % where)

        total = sum(item["tokens"] for item in row["selected"])
        if total != row["context_tokens"]:
            errors.append("%s: token del contesto incoerenti" % where)
        # R5 delle regole 0.2: nessuna eccezione, nemmeno per il primo elemento.
        if total > budget:
            errors.append("%s: GER supera il budget (%d su %d)" % (where, total, budget))
        if row["budget_exceeded_by_first_item"]:
            errors.append("%s: GER non deve avere eccezioni sul primo elemento" % where)
        for item_id in row["ger_excluded_over_budget"]:
            if item_id in row["selected_item_ids"]:
                errors.append("%s: %s e' oltre il budget ma e' stato selezionato"
                              % (where, item_id))
        if row["ger_session_reached_source"] != ger.SESSION_SOURCE_DECLARED:
            errors.append("%s: la sessione raggiunta non e' stata dichiarata" % where)

        block = "\n".join(item["render"] for item in row["selected"])
        if row["selected"] and rq2.count_tokens(block) != row["context_tokens"]:
            errors.append("%s: il blocco formattato non misura i token dichiarati" % where)

        quota = row["ger_quota_tokens"]
        if sum(quota.values()) != budget:
            errors.append("%s: le quote non sommano al budget" % where)
        for level, report in row["ger_levels"].items():
            fase1 = sum(item["tokens"] for item in row["selected"]
                        if item["level"] == level
                        and next(d for d in row["ger_decisions"]
                                 if d["item_id"] == item["item_id"])["phase"] == 1)
            if fase1 > quota[level]:
                errors.append("%s: il livello %s supera la propria quota in fase 1" % (where, level))
            if report["used_tokens"] < 0:
                errors.append("%s: consumo negativo sul livello %s" % (where, level))

        # entrambi i gruppi vengono interrogati: la dimensione dei due gruppi e'
        # sempre nota, anche quando uno dei due non ha candidati con punteggio.
        if set(row["ger_level_sizes"]) != set(ger.LEVELS):
            errors.append("%s: GER non ha interrogato tutti e due i livelli" % where)

        # nessun troncamento: la riga selezionata e' quella dell'elemento intero
        entries = entries_by_scenario[scenario_id]
        values = {e["entry_id"]: e["value"] for e in entries}
        for item in row["selected"]:
            if values[item["item_id"]] not in item["render"]:
                errors.append("%s: la riga di %s non contiene il testo intero"
                              % (where, item["item_id"]))

        if u_row is None:
            continue
        if u_row["budget_exceeded_by_first_item"]:
            errors.append("%s: l'eccezione di U si e' attivata proprio in un caso di confronto"
                          % where)
        # informazioni disponibili identiche a U: stessa politica di lettura,
        # stesso numero di voci leggibili
        if u_row["reading_scope"] != row["reading_scope"]:
            errors.append("%s: ambito di lettura diverso fra U e GER" % where)
        if u_row["readable_items"] != row["readable_items"]:
            errors.append("%s: U e GER non leggono lo stesso numero di voci" % where)
        # ranking calcolato prima della divisione: stessi punteggi voce per voce
        u_scores = {item["item_id"]: item["score"] for item in u_row["ranking"]}
        for item in row["ranking"]:
            if abs(u_scores.get(item["item_id"], -1) - item["score"]) > 1e-9:
                errors.append("%s: punteggio diverso da U su %s" % (where, item["item_id"]))
                break


def show_trace(rows, questions, scenario_id, handle):
    by_question = {}
    for row in rows:
        if row["scenario_id"] != scenario_id:
            continue
        by_question.setdefault(row["question_id"], {})[row["mode"]] = row

    for question in questions:
        pair = by_question.get(question["question_id"])
        if not pair or "GER" not in pair:
            continue
        g, u = pair["GER"], pair.get("U")
        sel = g["selection"] if "selection" in g else None
        handle.write("\n## %s — %s\n\n" % (question["question_id"], question["category"]))
        handle.write("**Domanda:** %s\n\n" % question["text"])
        handle.write("Sessione raggiunta: %d (%s) | finestra recente: sessioni %d-%d\n\n"
                     % (g["ger_session_reached"], g["ger_session_reached_source"],
                        g["ger_recency_window"][0], g["ger_recency_window"][1]))
        handle.write("Ambito di lettura: `%s` | voci leggibili: %d | "
                     "recenti %d, in archivio %d | quote: %d / %d token\n\n"
                     % (g["reading_scope"], g["readable_items"],
                        g["ger_level_sizes"][ger.LEVEL_RECENT],
                        g["ger_level_sizes"][ger.LEVEL_ARCHIVE],
                        g["ger_quota_tokens"][ger.LEVEL_RECENT],
                        g["ger_quota_tokens"][ger.LEVEL_ARCHIVE]))
        rec = g["ger_levels"][ger.LEVEL_RECENT]
        arc = g["ger_levels"][ger.LEVEL_ARCHIVE]
        handle.write("Consumo: recente %d/%d, archivio %d/%d, spazio riutilizzato %d "
                     "(disponibile %d), totale %d/%d token.\n\n"
                     % (rec["used_tokens"], rec["quota_tokens"],
                        arc["used_tokens"], arc["quota_tokens"],
                        g["ger_reuse"]["used_tokens"], g["ger_reuse"]["available_tokens"],
                        g["context_tokens"], g["budget_tokens"]))

        handle.write("| rango | elemento | livello | stato | punt. | token | esito | motivo |\n")
        handle.write("|---:|---|---|---|---:|---:|---|---|\n")
        stati = {item["item_id"]: item for item in g["ranking"]}
        del stati
        nulli = 0
        for decision in g["ger_decisions"]:
            if decision["reason"] == ger.REASON_ZERO_SCORE:
                nulli += 1
                continue
            esito = ("**selezionato** (fase %s)" % decision["phase"]
                     if decision["outcome"] == "selezionato" else "escluso")
            handle.write("| %d | `%s` | %s | %s | %.3f | %d | %s | %s |\n"
                         % (decision["rank"], decision["item_id"], decision["level"],
                            _state_of(g, decision["item_id"]),
                            decision["score"], decision["tokens"], esito, decision["reason"]))
        handle.write("\n%d elementi con punteggio nullo, esclusi come in U.\n\n" % nulli)

        if u:
            solo_u = [i for i in u["selected_item_ids"] if i not in g["selected_item_ids"]]
            solo_g = [i for i in g["selected_item_ids"] if i not in u["selected_item_ids"]]
            handle.write("**Confronto con U** (stesso stato, stesse voci leggibili, stesso budget): "
                         "U %d elementi / %d token, GER %d elementi / %d token. "
                         "Solo in U: %s. Solo in GER: %s.\n\n"
                         % (len(u["selected_item_ids"]), u["context_tokens"],
                            len(g["selected_item_ids"]), g["context_tokens"],
                            ", ".join("`%s`" % i for i in solo_u) or "nessuno",
                            ", ".join("`%s`" % i for i in solo_g) or "nessuno"))

        handle.write("**Evidenze richieste** (la provenienza e' automatica, il contenuto va letto):\n\n")
        if not question["required_facts"]:
            handle.write("- nessuna: la risposta corretta e' un'astensione.\n")
        for fact in question["required_facts"]:
            handle.write("- *%s* — attesa dal livello indicato nell'annotazione, da `%s`:\n"
                         % (fact["text"], ", ".join(fact["source_message_ids"])))
            for mode, row in (("U", u), ("GER", g)):
                if row is None:
                    continue
                trovati = [item for item in row["selected"]
                           if all(m in item["source_message_ids"] for m in fact["source_message_ids"])]
                if not trovati:
                    handle.write("  - %s: nessun elemento con quella provenienza.\n" % mode)
                    continue
                for item in trovati:
                    handle.write("  - %s: `%s` → %s\n" % (mode, item["item_id"], item["render"]))
        handle.write("\n")


def _state_of(row, item_id):
    for item in row["selected"]:
        if item["item_id"] == item_id:
            return item["state"]
    return "-"


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def parse_args(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description="Verifica offline di GER: nessuna chiamata a nessun modello.")
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR),
                        help="cartella degli artefatti (default: results/rq2/ger_dev_v2)")
    return parser.parse_args(argv)


def main(argv=None):
    global OUT_DIR
    args = parse_args(argv)
    OUT_DIR = Path(args.out)
    config = rq2.load_config()
    budget = rq2.budget_tokens(config)
    errors = []

    print("Verifica offline di GER — nessun modello e' stato chiamato.")
    print("Etichetta: %s" % LABEL)
    print("Regole: %s | finestra %d sessioni | budget %d token (rigoroso)"
          % (ger.RULES_VERSION, ger.RECENCY_WINDOW_SESSIONS, budget))
    print("Artefatti in %s" % rq2.relative(OUT_DIR))

    step(1, "Scenario di sviluppo SC05")
    scenario, questions = check_scenario(errors)

    step(2, "Memoria di U per SC05, dalle fixture dichiarate, con il codice vero")
    sc05_state_path, sc05_entries = build_sc05_state(scenario, config, errors)

    step(3, "Retrieval di U e di GER sugli stessi stati e sulle stesse domande")
    paths = {SC05: {"facts": str(SC05_FACTS), "state": str(sc05_state_path),
                    "session_reached": declare_session_reached(SC05, sc05_entries, errors)}}
    scenari = [SC05]
    entries_by_scenario = {SC05: sc05_entries}
    fingerprints = {SC05: state_fingerprint(sc05_state_path)}
    for scenario_id, source in REAL_STATES.items():
        if source["facts"].exists() and source["state"].exists():
            entries = memory.load_state(source["state"])
            scenari.append(scenario_id)
            paths[scenario_id] = {
                "facts": str(source["facts"]), "state": str(source["state"]),
                "session_reached": declare_session_reached(scenario_id, entries, errors),
            }
            entries_by_scenario[scenario_id] = entries
            fingerprints[scenario_id] = state_fingerprint(source["state"])
        else:
            print("saltato %s: stato salvato non disponibile" % scenario_id)
    for scenario_id in scenari:
        print("%s: sessione raggiunta dichiarata = %s"
              % (scenario_id, paths[scenario_id]["session_reached"]))

    rows, skipped = retrieval_rq2.run(scenari, config, paths, LABEL, modes=MODES)
    for scenario_id, mode, reason in skipped:
        print("saltato: %s / %s — %s" % (scenario_id, mode, reason))
    retrieval_rq2.print_summary(rows)
    path = rq2.write_jsonl(rows, OUT_DIR / "retrieval_ger.jsonl")
    print("righe di retrieval: %d → %s" % (len(rows), rq2.relative(path)))

    for scenario_id, before in fingerprints.items():
        if state_fingerprint(paths[scenario_id]["state"]) != before:
            errors.append("%s: lo stato e' cambiato durante il retrieval" % scenario_id)
    print("Stati invariati dopo il retrieval: recuperare una voce non la rende recente.")

    step(4, "Proprieta' essenziali di GER")
    check_properties(rows, entries_by_scenario, budget, errors)
    ger_rows = [r for r in rows if r["mode"] == "GER"]
    print("prove GER controllate: %d su %d scenari" % (len(ger_rows), len(scenari)))
    print("budget rispettato in tutte le prove: %s"
          % ("si" if all(r["context_tokens"] <= budget for r in ger_rows) else "NO"))
    usa_archivio = [r for r in ger_rows
                    if any(i["level"] == ger.LEVEL_ARCHIVE for i in r["selected"])]
    usa_recente = [r for r in ger_rows
                   if any(i["level"] == ger.LEVEL_RECENT for i in r["selected"])]
    riuso = [r for r in ger_rows if r["ger_reuse"]["used_tokens"] > 0]
    print("prove con almeno un elemento d'archivio nel contesto: %d/%d" % (len(usa_archivio), len(ger_rows)))
    print("prove con almeno un elemento recente nel contesto:   %d/%d" % (len(usa_recente), len(ger_rows)))
    print("prove in cui lo spazio avanzato e' stato riutilizzato: %d/%d" % (len(riuso), len(ger_rows)))

    step(5, "Prompt di SC05 per U, GER e FULL_HISTORY (costruiti, mai inviati)")
    inputs, input_skipped = generation_inputs.build([SC05], config, rows,
                                                    modes_override=["U", "GER", rq2.FULL_HISTORY])
    input_errors = generation_inputs.check(inputs, [SC05], config, rows)
    errors.extend(input_errors)
    for scenario_id, mode, reason in sorted(set(input_skipped)):
        print("saltato: %s / %s — %s" % (scenario_id, mode, reason))
    generation_inputs.print_summary(inputs)
    path = rq2.write_jsonl(inputs, OUT_DIR / "generation_inputs_sc05.jsonl")
    print("prompt scritti in %s (%d righe, model_answer sempre null)"
          % (rq2.relative(path), len(inputs)))

    step(6, "Traccia leggibile")
    trace_path = OUT_DIR / "traccia_ger_sc05.md"
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with open(trace_path, "w", encoding="utf-8") as handle:
        handle.write("# Traccia di GER su SC05 — verifica offline\n\n")
        handle.write("**Non sono risultati sperimentali.** La memoria di SC05 e' costruita "
                     "da fixture dichiarate (`tests/fixtures/rq2/scenario_05_*`), non dal "
                     "modello, e nessuna risposta e' stata generata.\n\n")
        handle.write("Regole `%s`, finestra %d sessioni, budget %d token, quote %d/%d.\n"
                     % (ger.RULES_VERSION, ger.RECENCY_WINDOW_SESSIONS, budget,
                        ger.quotas(budget)[ger.LEVEL_RECENT], ger.quotas(budget)[ger.LEVEL_ARCHIVE]))
        handle.write("\nLa corrispondenza di provenienza **non** dimostra che il contenuto "
                     "necessario sia nel contesto: le righe selezionate sono riportate per "
                     "intero proprio per poterle leggere.\n")
        show_trace(rows, questions, SC05, handle)
    print("traccia scritta in %s" % rq2.relative(trace_path))

    print()
    print("=" * 78)
    if errors:
        print("CONTROLLI FALLITI (%d):" % len(errors))
        for error in errors:
            print("  - %s" % error)
        return 1
    print("Tutti i controlli superati. Nessuna chiamata al modello, nessun risultato sperimentale.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
