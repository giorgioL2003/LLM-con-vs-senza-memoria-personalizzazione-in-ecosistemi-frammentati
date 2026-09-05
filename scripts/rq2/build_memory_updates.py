#!/usr/bin/env python3
"""Costruzione della memoria con aggiornamenti (architettura U).

U **non riestrae nulla**: parte esattamente dagli stessi fatti candidati
prodotti dall'estrattore di F (`scripts/rq2/extract_facts.py`) e decide, fatto
per fatto e in ordine cronologico, una sola operazione fra:

  - **ADD**: informazione nuova;
  - **UPDATE**: sostituisce un fatto precedente riferito allo stesso oggetto e
    ambito; il fatto superato resta in archivio con il collegamento alla nuova
    versione;
  - **DELETE**: rende inattiva un'informazione ritirata, senza sostituzione;
  - **NOOP**: la memoria non cambia, per esempio davanti a una conferma
    equivalente.

Che cosa vede il costruttore:
  - i fatti candidati della sessione in lavorazione;
  - lo stato corrente della memoria (fatti attivi);
  - l'archivio storico (fatti superati e ritirati), necessario per riconoscere
    un aggiornamento.

Che cosa NON vede mai: domande di valutazione, oracle, operazioni attese, stato
atteso, relazioni attese, sessioni future.

Il modello propone l'operazione; **applicarla allo stato e' compito del codice**,
non del modello, cosi' l'evoluzione della memoria e' verificabile.

Se una proposta non e' applicabile, il codice non la aggiusta: puo' pero'
chiedere al modello di **riproporla** mostrandogli lo stato aggiornato (vedi
`repair_attempts`). Anche la riproposta viene applicata o rifiutata con le stesse
regole, e la proposta rifiutata resta negli artefatti.

Una proposta non applicabile viene **rifiutata in blocco**, non aggiustata:
  - un ADD o un NOOP devono avere `target_entry_id` nullo;
  - un UPDATE o un DELETE devono indicare un `target_entry_id` che esiste, e'
    ancora attivo e ha lo stesso `claim_key` dell'operazione;
  - se manca anche una sola di queste condizioni l'operazione viene rifiutata e
    lo stato resta identico: non si cerca un target sostitutivo e non si
    trasforma l'operazione in ADD.

Il rifiuto non e' un errore dello script ma un **errore di gestione della
memoria** da contare come tale: l'operazione resta negli artefatti con
`applied: false` e `rejection_reason`, e le impronte dello stato prima e dopo
dimostrano che nulla e' cambiato.

Politica di lettura dichiarata (usata dal retrieval di U):
  - domande sullo stato corrente: soltanto fatti **attivi**;
  - domande storiche o sui cambiamenti: fatti attivi, superati e ritirati, ognuno
    con lo stato scritto nel contesto.
La scelta fra le due dipende dal testo della domanda tramite `question_scope()`,
una regola deterministica basata su marcatori linguistici. L'oracle non entra in
questa decisione.

Uso:
    python3 scripts/rq2/build_memory_updates.py --scenario scenario_03 --dry-run
    python3 scripts/rq2/build_memory_updates.py --scenario scenario_03
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import extract_facts  # noqa: E402

sys.path.insert(0, str(rq2.SCRIPTS_DIR))
import run_generation as gen  # noqa: E402

MEMORY_DIR = rq2.RQ2_RESULTS_DIR / "memory"

UPDATE_INSTRUCTIONS = (
    "Sei il componente che tiene aggiornata la memoria di un caso distribuito su piu' conversazioni.\n"
    "Ricevi i fatti gia' estratti da una nuova conversazione e devi decidere come la memoria deve cambiare.\n"
    "\n"
    "Per OGNI fatto nuovo scegli una sola operazione:\n"
    "- ADD: l'informazione e' nuova e non riguarda nessun fatto gia' in memoria.\n"
    "- UPDATE: l'informazione sostituisce un fatto gia' in memoria riferito allo stesso oggetto e\n"
    "  allo stesso ambito (per esempio la stessa decisione, la stessa ipotesi, la stessa attivita').\n"
    "- DELETE: l'informazione ritira un fatto gia' in memoria senza sostituirlo.\n"
    "- NOOP: la memoria non deve cambiare, per esempio davanti a una conferma equivalente di\n"
    "  qualcosa che c'e' gia'.\n"
    "\n"
    "Regole:\n"
    "1. Usa `claim_key` per dire di quale oggetto parla il fatto: e' un'etichetta breve in minuscolo,\n"
    "   con i trattini al posto degli spazi. Riusa lo stesso claim_key di un fatto gia' in memoria\n"
    "   quando parli dello stesso oggetto e ambito.\n"
    "2. Nel messaggio ci sono due elenchi di identificatori diversi, che non vanno mai confusi:\n"
    "   - gli identificatori elencati sotto «Fatti nuovi da valutare» sono gli unici valori\n"
    "     ammessi nel campo `fact_id`;\n"
    "   - gli identificatori elencati sotto «Stato corrente della memoria» e «Archivio» sono le\n"
    "     voci di memoria, e sono gli unici valori ammessi nel campo `target_entry_id`.\n"
    "   Non usare mai un identificatore di fatto nuovo come `target_entry_id`, e non usare mai un\n"
    "   identificatore di voce di memoria come `fact_id`.\n"
    "3. UPDATE e DELETE devono indicare in `target_entry_id` una voce presa da «Stato corrente\n"
    "   della memoria»: deve essere ancora attiva e avere lo stesso `claim_key` dell'operazione.\n"
    "   Le voci elencate in «Archivio» non sono piu' modificabili. Un fatto nuovo che non ha\n"
    "   ancora una voce in memoria non puo' essere il bersaglio di un UPDATE o di un DELETE: se\n"
    "   l'informazione e' nuova, l'operazione e' un ADD.\n"
    "4. ADD e NOOP lasciano `target_entry_id` a null.\n"
    "5. Le operazioni vengono applicate una alla volta, nell'ordine in cui le elenchi, e una voce\n"
    "   appena superata non e' piu' un bersaglio valido. Se piu' fatti nuovi riguardano lo stesso\n"
    "   oggetto gia' in memoria, indica `target_entry_id` soltanto nella prima operazione che lo\n"
    "   supera; per i fatti successivi scegli l'operazione adatta rispetto al risultato di quella,\n"
    "   per esempio NOOP se e' una conferma equivalente o ADD se riguarda un oggetto distinto.\n"
    "6. Non inventare informazioni: `value` deve poter essere ricavato dal fatto nuovo.\n"
    "7. Conserva le negazioni: se il fatto dice che qualcosa non e' avvenuto o non e' stato\n"
    "   determinato, `value` deve dirlo.\n"
    "8. In `reason` scrivi in una frase perche' hai scelto quell'operazione.\n"
    "\n"
    "Rispondi soltanto con un array JSON, un elemento per fatto nuovo, senza testo prima o dopo:\n"
    "{\"fact_id\": \"...\", \"operation\": \"ADD\", \"claim_key\": \"...\", \"value\": \"...\",\n"
    " \"target_entry_id\": null, \"reason\": \"...\"}\n"
)

REPAIR_INSTRUCTIONS = (
    "Alcune proposte precedenti non sono state applicate perche' non valide.\n"
    "Lo stato qui sotto e' quello **attuale**, cioe' dopo le operazioni gia' applicate: e' lo\n"
    "stato su cui verranno applicate le tue nuove proposte.\n"
    "Riproponi una sola operazione per ciascuno dei fatti elencati, coerente con questo stato e\n"
    "con le regole sopra. Se nessuna voce esistente e' un bersaglio valido, scegli l'operazione\n"
    "che descrive davvero il fatto invece di forzare un UPDATE.\n"
    "Rispondi con un array JSON anche quando il fatto da rivalutare e' uno solo: in quel caso\n"
    "l'array ha un solo elemento.\n"
)

# Versione delle istruzioni: cambia quando cambia il testo del prompt di U, cosi'
# ogni artefatto dice con quali istruzioni e' stato prodotto.
INSTRUCTIONS_VERSION = "u-instructions-0.3"

# Quante volte, dopo la prima passata, si puo' chiedere al modello di riproporre
# le operazioni rifiutate mostrandogli lo stato aggiornato. 0 = comportamento
# della prima prova reale (una sola passata per sessione).
DEFAULT_REPAIR_ATTEMPTS = 1

NO_STATE = "(memoria vuota: nessun fatto attivo)"
NO_ARCHIVE = "(archivio vuoto: nessun fatto superato o ritirato)"

# --------------------------------------------------------------------------
# Politica di lettura: stato corrente o storia
# --------------------------------------------------------------------------

SCOPE_CURRENT = "current"
SCOPE_HISTORY = "history"

# Marcatori che rendono la domanda storica o sui cambiamenti. Sono confrontati
# in minuscolo sul solo testo della domanda: nessun accesso all'oracle.
HISTORY_MARKERS = (
    "superat",
    "precedent",
    "inizial",
    "in origine",
    "in passato",
    "storic",
    "cambia",
    "modifica",
    "sostitu",
    "ritirat",
    "non e' piu'",
    "non è più",
    "e' ancora",
    "è ancora",
    "ancora un",
    "prima ipotesi",
    "prima decisione",
)


def question_scope(question_text):
    """Regola deterministica: storia oppure stato corrente.

    Basta un marcatore per passare allo storico. La regola e' volutamente
    prudente in quella direzione: aggiungere i fatti superati con lo stato
    scritto costa contesto, ometterli rende impossibile rispondere a una domanda
    sui cambiamenti.
    """
    lowered = question_text.lower()
    for marker in HISTORY_MARKERS:
        if marker in lowered:
            return SCOPE_HISTORY
    return SCOPE_CURRENT


def readable_entries(entries, scope):
    """Fatti leggibili in quell'ambito, in ordine di memoria."""
    if scope == SCOPE_HISTORY:
        allowed = set(rq2.ALLOWED_STATES)
    else:
        allowed = {rq2.STATE_ACTIVE}
    return [entry for entry in entries if entry["status"] in allowed]


def state_items(entries, scope):
    """Elementi di contesto di U, con lo stato temporale gia' scritto."""
    items = []
    for entry in readable_entries(entries, scope):
        render = rq2.render_state_entry(
            entry["entry_id"], entry["status"], entry["source_message_ids"], entry["value"]
        )
        items.append(
            rq2.make_item(
                item_id=entry["entry_id"],
                text=entry["value"],
                render=render,
                session_order=entry["session_order"],
                item_order=entry["order"],
                source_message_ids=entry["source_message_ids"],
                source_fact_ids=entry["source_fact_ids"],
                unit="fatto con stato",
                state=entry["status"],
                extra={"claim_key": entry["claim_key"]},
            )
        )
    items.sort(key=lambda item: (item["session_order"], item["item_order"]))
    return items


# --------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------

def format_state(entries):
    active = [e for e in entries if e["status"] == rq2.STATE_ACTIVE]
    if not active:
        return NO_STATE
    return "\n".join(
        "[%s] (%s) %s" % (entry["entry_id"], entry["claim_key"], entry["value"]) for entry in active
    )


def format_archive(entries):
    archived = [e for e in entries if e["status"] != rq2.STATE_ACTIVE]
    if not archived:
        return NO_ARCHIVE
    return "\n".join(
        "[%s] (%s) %s — %s" % (entry["entry_id"], entry["claim_key"], entry["value"], entry["status"])
        for entry in archived
    )


def format_new_facts(facts):
    return "\n".join(
        "[%s] %s (tipo: %s, negato: %s, da: %s)"
        % (fact["fact_id"], fact["text"], fact.get("kind", ""),
           "si" if fact.get("negated") else "no", ", ".join(fact["source_message_ids"]))
        for fact in facts
    )


def build_session_prompt(new_facts, entries):
    return (
        "Istruzioni:\n"
        "%s\n"
        "\n"
        "Stato corrente della memoria:\n"
        "%s\n"
        "\n"
        "Archivio dei fatti superati o ritirati:\n"
        "%s\n"
        "\n"
        "Fatti nuovi da valutare:\n"
        "%s"
    ) % (UPDATE_INSTRUCTIONS, format_state(entries), format_archive(entries), format_new_facts(new_facts))


def format_rejected(rejected):
    """Proposte non applicate, con il motivo del rifiuto.

    Contiene soltanto quello che il modello ha gia' proposto e la ragione tecnica
    del rifiuto: nessuna informazione dell'oracle e nessun suggerimento su quale
    operazione scegliere.
    """
    return "\n".join(
        "[%s] proposta: %s su %s (target: %s) — non applicata: %s"
        % (operation["source_fact_ids"][0] if operation["source_fact_ids"] else "?",
           operation["proposed_operation"] or "?",
           operation["claim_key"] or "?",
           operation["target_entry_id"] or "null",
           operation["rejection_reason"])
        for operation in rejected
    )


def build_repair_prompt(rejected_facts, rejected_ops, entries):
    return (
        "Istruzioni:\n"
        "%s\n"
        "%s\n"
        "Stato corrente della memoria:\n"
        "%s\n"
        "\n"
        "Archivio dei fatti superati o ritirati:\n"
        "%s\n"
        "\n"
        "Proposte non applicate:\n"
        "%s\n"
        "\n"
        "Fatti da rivalutare:\n"
        "%s"
    ) % (UPDATE_INSTRUCTIONS, REPAIR_INSTRUCTIONS, format_state(entries), format_archive(entries),
         format_rejected(rejected_ops), format_new_facts(rejected_facts))


# --------------------------------------------------------------------------
# Applicazione delle operazioni allo stato
# --------------------------------------------------------------------------

def _new_entry(entry_id, operation, fact, claim_key, value, order):
    return {
        "entry_id": entry_id,
        "claim_key": claim_key,
        "value": value,
        "status": rq2.STATE_ACTIVE,
        "source_fact_ids": [fact["fact_id"]],
        "source_message_ids": list(fact["source_message_ids"]),
        "session_id": fact["session_id"],
        "session_order": fact["session_order"],
        "order": order,
        "created_by_op": operation["op_id"],
        "superseded_by_op": None,
        "superseded_by_entry": None,
    }


def state_fingerprint(entries):
    """Impronta dello stato: cambia se cambia una qualsiasi voce di memoria.

    Serve a dimostrare che un'operazione rifiutata non ha toccato nulla, senza
    dover conservare due copie intere dello stato per ogni operazione.
    """
    canonical = json.dumps(
        [
            [entry["entry_id"], entry["claim_key"], entry["value"], entry["status"],
             entry["superseded_by_op"], entry["superseded_by_entry"]]
            for entry in entries
        ],
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def check_applicability(operation, entries):
    """Perche' l'operazione non e' applicabile, oppure (None, target).

    Nessuna correzione automatica: o la proposta e' applicabile com'e', o viene
    rifiutata.
    """
    kind = operation["proposed_operation"]
    if kind not in rq2.ALLOWED_OPERATIONS:
        return "operazione non ammessa: %r" % kind, None

    target_id = operation.get("target_entry_id")

    if kind in ("ADD", "NOOP"):
        # Lo schema delle operazioni vuole target_entry_id nullo: un ADD o un
        # NOOP che ne indica uno e' una proposta incoerente, non una sfumatura
        # da tollerare. Viene rifiutata come le altre.
        if target_id:
            return ("%s con target_entry_id valorizzato (%s): lo schema lo vuole nullo"
                    % (kind, target_id)), None
        return None, None

    if not target_id:
        return "%s senza target_entry_id: nessun fatto da superare" % kind, None

    target = next((entry for entry in entries if entry["entry_id"] == target_id), None)
    if target is None:
        return "%s verso un fatto inesistente (%s)" % (kind, target_id), None
    if target["status"] != rq2.STATE_ACTIVE:
        return "%s verso un fatto gia' %s (%s)" % (kind, target["status"], target_id), None
    if target["claim_key"] != operation["claim_key"]:
        return ("%s verso un fatto con claim_key diverso: proposto %r, il fatto %s ha %r"
                % (kind, operation["claim_key"], target_id, target["claim_key"])), None
    return None, target


def apply_operation(operation, fact, entries, order):
    """Applica la proposta allo stato, oppure la rifiuta senza toccare nulla.

    Restituisce il motivo del rifiuto, o None se l'operazione e' stata applicata.
    """
    before = state_fingerprint(entries)
    operation["state_before_fingerprint"] = before
    operation["state_before_active"] = len([e for e in entries if e["status"] == rq2.STATE_ACTIVE])

    rejection, target = check_applicability(operation, entries)
    if rejection is not None:
        operation.update({
            "applied": False,
            "applied_operation": None,
            "rejection_reason": rejection,
            "resulting_entry_id": None,
            "supersedes_entry_id": None,
            "state_after_fingerprint": before,
            "state_after_active": operation["state_before_active"],
        })
        return rejection

    kind = operation["proposed_operation"]
    operation.update({"applied": True, "applied_operation": kind, "rejection_reason": None})

    if kind == "NOOP":
        operation["resulting_entry_id"] = None
        operation["supersedes_entry_id"] = None
    elif kind == "DELETE":
        target["status"] = rq2.STATE_RETRACTED
        target["superseded_by_op"] = operation["op_id"]
        target["superseded_by_entry"] = None
        operation["resulting_entry_id"] = None
        operation["supersedes_entry_id"] = target["entry_id"]
    else:
        entry_id = "%s-M%03d" % (operation["op_id"].split("-OP")[0], order)
        entries.append(_new_entry(entry_id, operation, fact, operation["claim_key"],
                                  operation["value"], order))
        operation["resulting_entry_id"] = entry_id
        if kind == "UPDATE":
            target["status"] = rq2.STATE_SUPERSEDED
            target["superseded_by_op"] = operation["op_id"]
            target["superseded_by_entry"] = entry_id
            operation["supersedes_entry_id"] = target["entry_id"]
        else:
            operation["supersedes_entry_id"] = None

    operation["state_after_fingerprint"] = state_fingerprint(entries)
    operation["state_after_active"] = len([e for e in entries if e["status"] == rq2.STATE_ACTIVE])
    return None


# --------------------------------------------------------------------------
# Esecuzione
# --------------------------------------------------------------------------

def facts_by_session(facts):
    grouped = {}
    for fact in facts:
        grouped.setdefault((fact["session_order"], fact["session_id"]), []).append(fact)
    return [grouped[key] for key in sorted(grouped)]


def register_proposals(proposals, context, entries, counter_box, used,
                       attempt=1, retry_of=None):
    """Trasforma le proposte grezze in operazioni e le applica una alla volta.

    Nessuna proposta viene corretta: o e' applicabile com'e', o viene rifiutata.
    `attempt` e `retry_of` servono soltanto a tracciare le riproposte: la seconda
    proposta e' un'operazione nuova, e quella rifiutata resta com'e'.
    """
    retry_of = retry_of or {}
    facts_by_id = context["facts_by_id"]
    session_facts = context["session_facts"]
    session_id = context["session_id"]
    allowed_messages = context["allowed_messages"]
    produced = []

    for raw in proposals:
        if not isinstance(raw, dict):
            continue
        counter_box["value"] += 1
        counter = counter_box["value"]
        fact_ref = str(raw.get("fact_id", "")).strip()
        fact = facts_by_id.get(fact_ref)
        kind = str(raw.get("operation", "")).strip().upper()
        operation = {
            "op_id": "%s-OP%03d" % (context["prefix"], counter),
            "scenario_id": context["scenario"]["scenario_id"],
            "session_id": session_id,
            "session_order": session_facts[0]["session_order"],
            "order": counter,
            "attempt": attempt,
            "retry_of": retry_of.get(fact_ref),
            "proposed_operation": kind,
            "claim_key": str(raw.get("claim_key", "")).strip(),
            "value": str(raw.get("value", "")).strip(),
            "source_fact_ids": [fact["fact_id"]] if fact else [fact_ref],
            "source_message_ids": list(fact["source_message_ids"]) if fact else [],
            "target_entry_id": raw.get("target_entry_id") or None,
            "reason": str(raw.get("reason", "")).strip(),
            "model_used": used,
            "model_requested": context["model"],
            "effort": context["effort"],
            "config_id": context["config"]["config_id"],
            "instructions_version": INSTRUCTIONS_VERSION,
            "prompt_ref": "%s/%s" % (context["scenario"]["scenario_id"], session_id),
            "raw_proposal": raw,
            "raw_answer_ref": {
                "session_id": session_id,
                "field": ("sessions[].model_answer del registro dell'aggiornamento" if attempt == 1
                          else "sessions[].repair_rounds[].model_answer del registro"),
            },
        }
        problems = []
        if fact is None:
            problems.append("il fatto citato non appartiene a questa sessione")
        for message_id in operation["source_message_ids"]:
            if message_id not in allowed_messages:
                problems.append("messaggio sorgente non ammesso: %s" % message_id)
        operation["provenance_valid"] = not problems
        operation["provenance_problem"] = "; ".join(problems) or None

        if fact is None:
            # Senza il fatto sorgente non si puo' nemmeno provare ad applicare:
            # il rifiuto e' registrato come per gli altri casi.
            fingerprint = state_fingerprint(entries)
            active = len([e for e in entries if e["status"] == rq2.STATE_ACTIVE])
            operation.update({
                "applied": False,
                "applied_operation": None,
                "rejection_reason": "provenienza non valida: %s" % operation["provenance_problem"],
                "resulting_entry_id": None,
                "supersedes_entry_id": None,
                "state_before_fingerprint": fingerprint,
                "state_after_fingerprint": fingerprint,
                "state_before_active": active,
                "state_after_active": active,
            })
        else:
            apply_operation(operation, fact, entries, counter)

        produced.append(operation)

    return produced


def run(scenario, facts, config, dry_run=False, runner=None, model=None, effort=None,
        repair_attempts=0):
    """Aggiornamento della memoria sessione per sessione, in ordine cronologico."""
    model = model or config["models"]["extraction"]["model"]
    effort = effort or config["models"]["extraction"]["effort"]
    prefix = "SC%s" % scenario["scenario_id"].split("_")[-1]

    entries = []
    operations = []
    log_entries = []
    counter_box = {"value": 0}
    cwd = tempfile.mkdtemp(prefix="aggiornamento_") if not dry_run else None
    allowed_messages = {entry["message_id"] for entry in rq2.user_messages(scenario)}

    for session_facts in facts_by_session(facts):
        session_id = session_facts[0]["session_id"]
        prompt = build_session_prompt(session_facts, entries)
        entry_log = {
            "scenario_id": scenario["scenario_id"],
            "session_id": session_id,
            "session_order": session_facts[0]["session_order"],
            "input_fact_ids": [fact["fact_id"] for fact in session_facts],
            "state_before": [e["entry_id"] for e in entries if e["status"] == rq2.STATE_ACTIVE],
            "archive_before": [e["entry_id"] for e in entries if e["status"] != rq2.STATE_ACTIVE],
            "prompt": prompt,
            "model_requested": model,
            "effort": effort,
        }

        if dry_run:
            entry_log.update({"executed": False, "model_answer": None, "model_used": None,
                              "error": None, "parse_error": None, "operations": []})
            log_entries.append(entry_log)
            continue

        call = runner or (lambda p: gen.call_claude(p, cwd, model, effort))
        answer, used, error = call(prompt)
        entry_log.update({"executed": True, "model_answer": answer, "model_used": used, "error": error})
        if error:
            entry_log.update({"parse_error": None, "operations": []})
            log_entries.append(entry_log)
            continue

        proposals, parse_error = extract_facts.parse_facts(answer)
        entry_log["parse_error"] = parse_error

        facts_by_id = {fact["fact_id"]: fact for fact in session_facts}
        context = {
            "facts_by_id": facts_by_id, "session_facts": session_facts, "session_id": session_id,
            "prefix": prefix, "scenario": scenario, "config": config, "model": model,
            "effort": effort, "allowed_messages": allowed_messages,
        }
        session_ops = register_proposals(proposals, context, entries, counter_box, used)

        # Passata di riparazione: le proposte rifiutate tornano al modello con lo
        # stato aggiornato, cioe' quello su cui verrebbero davvero applicate. Il
        # codice non corregge nulla: la riproposta viene applicata o rifiutata con
        # le stesse regole, e la proposta rifiutata resta negli artefatti.
        entry_log["repair_rounds"] = []
        for attempt in range(2, 2 + max(0, repair_attempts)):
            rejected = [op for op in session_ops if op["applied"] is False]
            if not rejected:
                break
            rejected_facts = [facts_by_id[op["source_fact_ids"][0]] for op in rejected
                              if op["source_fact_ids"] and op["source_fact_ids"][0] in facts_by_id]
            if not rejected_facts:
                break
            retry_of = {op["source_fact_ids"][0]: op["op_id"] for op in rejected
                        if op["source_fact_ids"]}
            repair_prompt = build_repair_prompt(rejected_facts, rejected, entries)
            round_log = {
                "attempt": attempt,
                "prompt": repair_prompt,
                "rejected_op_ids": [op["op_id"] for op in rejected],
                "input_fact_ids": [fact["fact_id"] for fact in rejected_facts],
            }
            answer, used_repair, error = call(repair_prompt)
            round_log.update({"model_answer": answer, "model_used": used_repair, "error": error})
            if error:
                round_log.update({"parse_error": None, "operations": []})
                entry_log["repair_rounds"].append(round_log)
                break
            repaired, repair_parse_error = extract_facts.parse_facts(answer)
            round_log["parse_error"] = repair_parse_error
            new_ops = register_proposals(repaired, context, entries, counter_box, used_repair,
                                         attempt=attempt, retry_of=retry_of)
            # La proposta rifiutata resta invariata nel suo esito: si annota
            # soltanto quale riproposta le corrisponde, cosi' la storia e'
            # leggibile in tutte e due le direzioni.
            new_by_fact = {op["source_fact_ids"][0]: op["op_id"] for op in new_ops
                           if op["source_fact_ids"]}
            for op in rejected:
                if op["source_fact_ids"]:
                    op["retried_by"] = new_by_fact.get(op["source_fact_ids"][0])
            round_log["operations"] = [op["op_id"] for op in new_ops]
            entry_log["repair_rounds"].append(round_log)
            session_ops = session_ops + new_ops

        operations.extend(session_ops)
        entry_log["operations"] = [operation["op_id"] for operation in session_ops]
        log_entries.append(entry_log)

    log = {
        "scenario_id": scenario["scenario_id"],
        "source_file": scenario["source_file"],
        "config_id": config["config_id"],
        "model": model,
        "effort": effort,
        "dry_run": dry_run,
        "update_instructions": UPDATE_INSTRUCTIONS,
        "repair_instructions": REPAIR_INSTRUCTIONS if repair_attempts else None,
        "instructions_version": INSTRUCTIONS_VERSION,
        "instructions_sha256": hashlib.sha256(
            (UPDATE_INSTRUCTIONS + REPAIR_INSTRUCTIONS).encode("utf-8")).hexdigest()[:16],
        "code_sha256": hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest()[:16],
        "repair_attempts": repair_attempts,
        "sessions": log_entries,
        "operation_count": len(operations),
        "applied_count": len([o for o in operations if o.get("applied")]),
        "rejected_count": len([o for o in operations if o.get("applied") is False]),
        "repair_round_count": sum(len(e.get("repair_rounds") or []) for e in log_entries),
        "model_calls": len([e for e in log_entries if e.get("executed")])
                       + sum(len(e.get("repair_rounds") or []) for e in log_entries),
    }
    return operations, entries, log


# --------------------------------------------------------------------------
# Percorsi e I/O
# --------------------------------------------------------------------------

def operations_path(scenario_id, out_dir=MEMORY_DIR):
    return Path(out_dir) / ("%s_operations.jsonl" % scenario_id)


def state_path(scenario_id, out_dir=MEMORY_DIR):
    return Path(out_dir) / ("%s_state.json" % scenario_id)


def log_path(scenario_id, out_dir=MEMORY_DIR, dry_run=False):
    suffix = "_update_prompts.json" if dry_run else "_update_log.json"
    return Path(out_dir) / ("%s%s" % (scenario_id, suffix))


def state_document(scenario_id, entries, config, label="esecuzione"):
    return {
        "scenario_id": scenario_id,
        "config_id": config["config_id"],
        "label": label,
        "reading_policy": {
            "current": "soltanto i fatti attivi",
            "history": "fatti attivi, superati e ritirati, ognuno con lo stato scritto nel contesto",
            "markers": list(HISTORY_MARKERS),
            "note": "La scelta dipende soltanto dal testo della domanda: l'oracle non entra nella regola.",
        },
        "current": [entry for entry in entries if entry["status"] == rq2.STATE_ACTIVE],
        "archive": [entry for entry in entries if entry["status"] != rq2.STATE_ACTIVE],
    }


def load_state(path):
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    return document["current"] + document["archive"]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Costruisce la memoria con aggiornamenti (U).")
    parser.add_argument("--scenario", default="scenario_03", choices=list(rq2.SCENARIO_IDS))
    parser.add_argument("--facts", default=None, help="fatti candidati (default: results/rq2/facts/)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out-dir", default=str(MEMORY_DIR))
    parser.add_argument("--label", default="esecuzione")
    parser.add_argument("--repair-attempts", type=int, default=DEFAULT_REPAIR_ATTEMPTS,
                        help="quante volte richiedere al modello le proposte rifiutate, "
                             "mostrandogli lo stato aggiornato (0 = una sola passata)")
    parser.add_argument("--model", default=None)
    parser.add_argument("--effort", default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = rq2.load_config()
    scenario = rq2.load_scenario(args.scenario)

    facts_file = Path(args.facts) if args.facts else extract_facts.facts_path(args.scenario)
    if not facts_file.exists():
        print("Fatti candidati mancanti: %s. Eseguire prima scripts/rq2/extract_facts.py."
              % rq2.relative(facts_file), file=sys.stderr)
        return 1
    facts = rq2.read_jsonl(facts_file)

    operations, entries, log = run(scenario, facts, config, dry_run=args.dry_run,
                                   model=args.model, effort=args.effort,
                                   repair_attempts=args.repair_attempts)
    log["facts_source"] = rq2.relative(facts_file)
    log["label"] = args.label

    out_dir = Path(args.out_dir)
    written_log = rq2.write_json(log, log_path(args.scenario, out_dir, args.dry_run))

    print("Memoria con aggiornamenti — %s" % args.scenario)
    print("fatti candidati: %s" % rq2.relative(facts_file))
    print("modello: %s | effort: %s | %s"
          % (log["model"], log["effort"], "DRY RUN, nessuna chiamata" if args.dry_run else "chiamate reali"))
    print("istruzioni: %s | riproposte per sessione: %d"
          % (log["instructions_version"], args.repair_attempts))
    if args.label != "esecuzione":
        print("ATTENZIONE: etichetta '%s'. Non sono risultati sperimentali." % args.label)
    print("-" * 78)
    for entry in log["sessions"]:
        stato = "prompt costruito" if args.dry_run else (
            "errore: %s" % entry["error"] if entry["error"]
            else "%d operazioni" % len(entry["operations"]))
        print("%-12s fatti=%-3d attivi prima=%-3d %s"
              % (entry["session_id"], len(entry["input_fact_ids"]), len(entry["state_before"]), stato))
    print("-" * 78)
    print("Prompt e configurazione salvati in %s" % rq2.relative(written_log))

    if args.dry_run:
        print("Nessuna operazione prodotta: per costruire davvero, rieseguire senza --dry-run.")
        return 0

    rq2.write_jsonl(operations, operations_path(args.scenario, out_dir))
    rq2.write_json(state_document(args.scenario, entries, config, args.label),
                   state_path(args.scenario, out_dir))

    counts = {}
    for operation in operations:
        counts[operation["proposed_operation"]] = counts.get(operation["proposed_operation"], 0) + 1
    active = len([e for e in entries if e["status"] == rq2.STATE_ACTIVE])
    superseded = len([e for e in entries if e["status"] == rq2.STATE_SUPERSEDED])
    retracted = len([e for e in entries if e["status"] == rq2.STATE_RETRACTED])
    rejected = [o for o in operations if not o["applied"]]
    print("Operazioni proposte: %s" % (", ".join("%s=%d" % item for item in sorted(counts.items())) or "nessuna"))
    print("Applicate: %d | rifiutate: %d" % (len(operations) - len(rejected), len(rejected)))
    riproposte = [o for o in operations if o.get("attempt", 1) > 1]
    if riproposte:
        recuperate = [o for o in riproposte if o["applied"]]
        print("Riproposte dopo un rifiuto: %d, di cui applicate %d (chiamate totali: %d)"
              % (len(riproposte), len(recuperate), log["model_calls"]))
    print("Stato: %d attivi, %d superati, %d ritirati" % (active, superseded, retracted))
    for operation in rejected:
        print("  RIFIUTATA %s (%s): %s"
              % (operation["op_id"], operation["proposed_operation"], operation["rejection_reason"]))
    if rejected:
        print("Le operazioni rifiutate restano negli artefatti e vanno contate come errori di gestione.")
    print("Operazioni in %s" % rq2.relative(operations_path(args.scenario, out_dir)))
    print("Stato in %s" % rq2.relative(state_path(args.scenario, out_dir)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
