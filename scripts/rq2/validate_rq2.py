#!/usr/bin/env python3
"""Validatore del dataset e della configurazione dell'esperimento principale RQ2.

Controlla soltanto la struttura e la coerenza dei dati: non esegue retrieval,
non chiama modelli e non calcola metriche.

Cosa verifica:
  - conversazioni di SC03 e SC04: quattro sessioni, ordine, identificatori
    unici, ruoli e contenuti;
  - separazione: i file delle conversazioni non contengono domande ne' oracle;
  - annotazioni: sette domande per scenario, categorie ammesse, provenienza dei
    fatti obbligatori valida, informazione assente rappresentata correttamente;
  - overlay di SC01 e SC02: le domande coincidono con quelle del pilot e la
    provenienza ricavata dai fatti coincide con le evidenze gia' dichiarate nel
    pilot (il file del pilot non viene modificato);
  - SC03: operazioni attese ADD/UPDATE/DELETE/NOOP coerenti e stato atteso
    completo;
  - SC04: entita', relazioni e percorsi richiesti coerenti;
  - configurazione: matrice scenario x modalita' uguale a quella della roadmap,
    budget, metodo di conteggio dei token e modalita' dichiarate eseguibili.

Uso:
    python3 scripts/rq2/validate_rq2.py

Codice di uscita: 0 se non ci sono errori, 1 altrimenti. Solo libreria standard.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402

EXPECTED_SESSIONS = 4
EXPECTED_QUESTIONS = 7

# Matrice della roadmap, sezione 3. Scritta qui per poter dire che la
# configurazione non se ne e' allontanata senza che nessuno se ne accorga.
ROADMAP_MATRIX = {
    "scenario_01": ["T", "FULL_HISTORY"],
    "scenario_02": ["T", "F", "FULL_HISTORY"],
    "scenario_03": ["F", "U", "FULL_HISTORY"],
    "scenario_04": ["U", "G", "FULL_HISTORY"],
}
ROADMAP_TOTAL_GENERATIONS = 77

REQUIRED_CATEGORIES = (
    "goal",
    "update_obsolete",
    "completed_activity",
    "pending_activity",
    "cross_session_link",
    "absent_information",
)

# I file delle conversazioni non devono contenere nulla dell'oracle.
FORBIDDEN_SCENARIO_KEYS = (
    "questions",
    "expected_answer",
    "mandatory_facts",
    "required_evidence_ids",
    "oracle",
    "expected_operations",
    "expected_state",
    "graph_annotation",
)

MIN_QUESTIONS_OUTSIDE_LAST_SESSION = 3


# --------------------------------------------------------------------------
# Conversazioni
# --------------------------------------------------------------------------

def validate_sessions(scenario, errors):
    where = scenario["scenario_id"]
    sessions = scenario["sessions"]
    if len(sessions) != EXPECTED_SESSIONS:
        errors.append("[E-COUNT] %s: attese %d sessioni, trovate %d" % (where, EXPECTED_SESSIONS, len(sessions)))

    seen_messages = {}
    seen_sessions = set()
    for index, session in enumerate(sessions, start=1):
        session_id = session["session_id"]
        if session_id in seen_sessions:
            errors.append("[E-DUP] %s: session_id duplicato '%s'" % (where, session_id))
        seen_sessions.add(session_id)
        if session["order"] != index:
            errors.append("[E-ORDER] %s / %s: order %s incoerente con la posizione %d"
                          % (where, session_id, session["order"], index))
        if not session["messages"]:
            errors.append("[E-COUNT] %s / %s: sessione senza messaggi" % (where, session_id))
        for position, message in enumerate(session["messages"], start=1):
            message_id = message["message_id"]
            if message["order"] != position:
                errors.append("[E-ORDER] %s / %s: order %s incoerente con la posizione %d"
                              % (where, message_id, message["order"], position))
            if message["role"] not in ("user", "assistant"):
                errors.append("[E-FIELD] %s / %s: role '%s' non ammesso" % (where, message_id, message["role"]))
            if not message["content"].strip():
                errors.append("[E-FIELD] %s / %s: content vuoto" % (where, message_id))
            if message["session_id"] != session_id:
                errors.append("[E-SESSION] %s / %s: dichiara session_id '%s' ma appartiene a '%s'"
                              % (where, message_id, message["session_id"], session_id))
            if message_id in seen_messages:
                errors.append("[E-DUP] %s: message_id duplicato '%s'" % (where, message_id))
            seen_messages[message_id] = session_id
    return seen_messages


def validate_scenario_file(scenario_id, errors):
    """Controlli sul file grezzo: separazione fra conversazioni e valutazione."""
    origin, path = rq2.SCENARIO_SOURCES[scenario_id]
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if origin != "rq2":
        # SC01 e SC02 restano i file del pilot: contengono l'oracle del pilot e
        # non devono essere modificati. Qui si controlla solo che siano leggibili.
        return
    for key in FORBIDDEN_SCENARIO_KEYS:
        if key in raw:
            errors.append(
                "[E-LEAK] %s (%s): il file delle conversazioni contiene '%s'; "
                "oracle e annotazioni devono stare in data/rq2/annotations/"
                % (scenario_id, path.name, key)
            )
    scope = raw.get("memory_scope", {}).get("accessible_sessions")
    session_ids = [s["session_id"] for s in raw["sessions"]]
    if scope != session_ids:
        errors.append("[E-SCOPE] %s: memory_scope deve elencare tutte le sessioni (%s), trovato %s"
                      % (scenario_id, session_ids, scope))
    if raw.get("frozen") is not False:
        errors.append("[E-STATUS] %s: 'frozen' deve essere false finche' il protocollo non e' congelato" % scenario_id)


# --------------------------------------------------------------------------
# Annotazioni
# --------------------------------------------------------------------------

def validate_questions(scenario_id, questions, messages_by_id, user_message_ids, session_order, errors):
    where = scenario_id
    if len(questions) != EXPECTED_QUESTIONS:
        errors.append("[E-COUNT] %s: attese %d domande, trovate %d" % (where, EXPECTED_QUESTIONS, len(questions)))

    seen = set()
    categories = []
    outside_last = 0
    last_session_order = max(session_order.values()) if session_order else 0

    for question in questions:
        question_id = question["question_id"]
        q_where = "%s / %s" % (where, question_id)
        if question_id in seen:
            errors.append("[E-DUP] %s: question_id duplicato '%s'" % (where, question_id))
        seen.add(question_id)
        categories.append(question["category"])

        if question["category"] not in rq2.ALLOWED_CATEGORIES:
            errors.append("[E-CATEGORY] %s: categoria '%s' non ammessa" % (q_where, question["category"]))
        for field in ("text", "expected_answer"):
            if not str(question[field]).strip():
                errors.append("[E-FIELD] %s: campo '%s' vuoto" % (q_where, field))
        if not question["mandatory_facts"]:
            errors.append("[E-FIELD] %s: mandatory_facts non puo' essere vuoto" % q_where)

        # provenienza dei fatti obbligatori
        fact_keys = set()
        for fact in question["required_facts"]:
            for field in ("fact_key", "text", "source_message_ids", "kind"):
                if field not in fact:
                    errors.append("[E-FACT] %s: fatto obbligatorio privo di '%s'" % (q_where, field))
            if "fact_key" not in fact:
                continue
            if fact["fact_key"] in fact_keys:
                errors.append("[E-DUP] %s: fact_key duplicato '%s'" % (q_where, fact["fact_key"]))
            fact_keys.add(fact["fact_key"])
            if fact.get("kind") not in rq2.ALLOWED_FACT_KINDS:
                errors.append("[E-FACT] %s: kind '%s' non ammesso per '%s'"
                              % (q_where, fact.get("kind"), fact["fact_key"]))
            if not isinstance(fact.get("negated"), bool):
                errors.append("[E-FACT] %s: '%s' deve dichiarare negated booleano"
                              % (q_where, fact["fact_key"]))
            if not fact.get("source_message_ids"):
                errors.append("[E-PROVENANCE] %s: '%s' non dichiara messaggi sorgente"
                              % (q_where, fact["fact_key"]))
            for message_id in fact.get("source_message_ids", []):
                if message_id not in messages_by_id:
                    errors.append("[E-PROVENANCE] %s: '%s' cita il messaggio inesistente '%s'"
                                  % (q_where, fact["fact_key"], message_id))
                elif message_id not in user_message_ids:
                    errors.append("[E-PROVENANCE] %s: '%s' cita '%s', che non e' un messaggio dell'utente"
                                  % (q_where, fact["fact_key"], message_id))

        # informazione mai fornita
        absent = question["category"] == "absent_information"
        if absent == question["fact_present_in_corpus"]:
            errors.append("[E-ABSENT] %s: categoria '%s' e fact_present_in_corpus=%s sono incoerenti"
                          % (q_where, question["category"], question["fact_present_in_corpus"]))
        if not question["fact_present_in_corpus"]:
            if question["required_facts"]:
                errors.append("[E-ABSENT] %s: un'informazione mai fornita non puo' avere fatti obbligatori" % q_where)
            if not str(question.get("evidence_note") or "").strip():
                errors.append("[E-ABSENT] %s: manca evidence_note che documenti l'assenza" % q_where)
            if question["expected_behavior"] != rq2.BEHAVIOR_ABSTAIN:
                errors.append("[E-BEHAVIOR] %s: comportamento atteso deve essere '%s'"
                              % (q_where, rq2.BEHAVIOR_ABSTAIN))
        else:
            if not question["required_facts"]:
                errors.append("[E-ABSENT] %s: fact_present_in_corpus=true ma nessun fatto obbligatorio" % q_where)
            if question["expected_behavior"] != rq2.BEHAVIOR_ANSWER:
                errors.append("[E-BEHAVIOR] %s: comportamento atteso deve essere '%s'"
                              % (q_where, rq2.BEHAVIOR_ANSWER))

        evidence_sessions = {
            messages_by_id[m] for m in question["required_evidence_ids"] if m in messages_by_id
        }
        if question["category"] == "cross_session_link" and len(evidence_sessions) < 2:
            errors.append("[E-CROSS] %s: una domanda cross_session_link deve richiedere evidenze da almeno due sessioni"
                          % q_where)
        orders = {session_order[s] for s in evidence_sessions if s in session_order}
        if orders and min(orders) < last_session_order:
            outside_last += 1

    missing = [c for c in REQUIRED_CATEGORIES if c not in categories]
    if missing:
        errors.append("[E-CATEGORY] %s: fenomeni non coperti dalle domande: %s" % (where, ", ".join(missing)))
    if outside_last < MIN_QUESTIONS_OUTSIDE_LAST_SESSION:
        errors.append(
            "[E-LASTSESSION] %s: solo %d domande richiedono evidenze fuori dall'ultima sessione "
            "(attese almeno %d): l'ultima sessione starebbe riassumendo tutta la storia"
            % (where, outside_last, MIN_QUESTIONS_OUTSIDE_LAST_SESSION)
        )


def validate_overlay(scenario_id, questions, errors):
    """SC01 e SC02: l'overlay non deve alterare l'oracle del pilot."""
    _, pilot_path = rq2.SCENARIO_SOURCES[scenario_id]
    with open(pilot_path, "r", encoding="utf-8") as handle:
        pilot = json.load(handle)
    pilot_questions = {q["question_id"]: q for q in pilot["questions"]}

    if [q["question_id"] for q in questions] != [q["question_id"] for q in pilot["questions"]]:
        errors.append("[E-OVERLAY] %s: l'overlay non elenca le stesse domande del pilot, nello stesso ordine"
                      % scenario_id)

    for question in questions:
        base = pilot_questions.get(question["question_id"])
        if base is None:
            continue
        q_where = "%s / %s" % (scenario_id, question["question_id"])
        if question["required_evidence_ids"] != base["required_evidence_ids"]:
            errors.append(
                "[E-OVERLAY] %s: la provenienza ricavata dai fatti (%s) non coincide con le evidenze del pilot (%s)"
                % (q_where, question["required_evidence_ids"], base["required_evidence_ids"])
            )


# --------------------------------------------------------------------------
# SC03: operazioni e stato attesi
# --------------------------------------------------------------------------

def validate_operations(scenario_id, annotation, messages_by_id, session_order, errors, require_full_policy):
    block = annotation.get("expected_operations")
    if not block:
        if require_full_policy:
            errors.append("[E-OPS] %s: mancano le operazioni attese" % scenario_id)
        return
    operations = block["operations"]
    seen = set()
    previous_order = 0
    by_id = {}
    seen_ops = []

    for operation in operations:
        op_id = operation["op_id"]
        o_where = "%s / %s" % (scenario_id, op_id)
        if op_id in seen:
            errors.append("[E-DUP] %s: op_id duplicato '%s'" % (scenario_id, op_id))
        seen.add(op_id)
        by_id[op_id] = operation
        seen_ops.append(operation["expected_operation"])

        if operation["expected_operation"] not in rq2.ALLOWED_OPERATIONS:
            errors.append("[E-OPS] %s: operazione '%s' non ammessa" % (o_where, operation["expected_operation"]))
        order = session_order.get(operation["session_id"])
        if order is None:
            errors.append("[E-OPS] %s: sessione inesistente '%s'" % (o_where, operation["session_id"]))
        else:
            if order < previous_order:
                errors.append("[E-OPS-ORDER] %s: le operazioni devono essere in ordine cronologico" % o_where)
            previous_order = order
        for message_id in operation["source_message_ids"]:
            if message_id not in messages_by_id:
                errors.append("[E-PROVENANCE] %s: messaggio sorgente inesistente '%s'" % (o_where, message_id))
            elif messages_by_id[message_id] != operation["session_id"]:
                errors.append("[E-PROVENANCE] %s: il messaggio '%s' non appartiene alla sessione dichiarata"
                              % (o_where, message_id))

    for operation in operations:
        target = operation.get("supersedes")
        o_where = "%s / %s" % (scenario_id, operation["op_id"])
        if operation["expected_operation"] in ("UPDATE", "DELETE"):
            if not target:
                errors.append("[E-OPS] %s: %s deve indicare l'operazione che supera"
                              % (o_where, operation["expected_operation"]))
        if operation["expected_operation"] in ("ADD", "NOOP") and target:
            errors.append("[E-OPS] %s: %s non deve superare nessuna operazione"
                          % (o_where, operation["expected_operation"]))
        if target:
            previous = by_id.get(target)
            if previous is None:
                errors.append("[E-OPS] %s: supersedes cita un'operazione inesistente '%s'" % (o_where, target))
            elif previous["claim_key"] != operation["claim_key"]:
                errors.append("[E-OPS] %s: supersedes cita un'operazione con claim_key diverso ('%s')"
                              % (o_where, previous["claim_key"]))

    if require_full_policy:
        for kind in rq2.ALLOWED_OPERATIONS:
            if kind not in seen_ops:
                errors.append("[E-OPS] %s: nessuna operazione attesa di tipo %s" % (scenario_id, kind))


def validate_state(scenario_id, annotation, errors):
    block = annotation.get("expected_state")
    if not block:
        errors.append("[E-STATE] %s: manca lo stato atteso" % scenario_id)
        return
    operations = annotation.get("expected_operations", {}).get("operations", [])
    op_ids = {operation["op_id"] for operation in operations}
    claim_keys = {operation["claim_key"] for operation in operations}
    allowed_status = ("attivo", "superato", "ritirato")

    state_keys = set()
    for entry in block["entries"]:
        s_where = "%s / stato %s" % (scenario_id, entry["claim_key"])
        state_keys.add(entry["claim_key"])
        if entry["status"] not in allowed_status:
            errors.append("[E-STATE] %s: stato '%s' non ammesso" % (s_where, entry["status"]))
        if entry["status"] == "attivo" and entry.get("superseded_by"):
            errors.append("[E-STATE] %s: un fatto attivo non puo' essere superato" % s_where)
        if entry["status"] in ("superato", "ritirato") and not entry.get("superseded_by"):
            errors.append("[E-STATE] %s: un fatto %s deve indicare l'operazione che lo ha reso tale"
                          % (s_where, entry["status"]))
        target = entry.get("superseded_by")
        if target and target not in op_ids:
            errors.append("[E-STATE] %s: superseded_by cita un'operazione inesistente '%s'" % (s_where, target))

    for claim_key in sorted(claim_keys - state_keys):
        errors.append("[E-STATE] %s: il claim '%s' compare fra le operazioni ma non nello stato atteso"
                      % (scenario_id, claim_key))
    for claim_key in sorted(state_keys - claim_keys):
        errors.append("[E-STATE] %s: il claim '%s' compare nello stato atteso ma non fra le operazioni"
                      % (scenario_id, claim_key))


# --------------------------------------------------------------------------
# SC04: entita' e relazioni
# --------------------------------------------------------------------------

def validate_graph(scenario_id, annotation, questions, messages_by_id, errors):
    block = annotation.get("graph_annotation")
    if not block:
        errors.append("[E-GRAPH] %s: mancano entita' e relazioni attese" % scenario_id)
        return
    entities = {entity["entity_id"] for entity in block["entities"]}
    if len(entities) != len(block["entities"]):
        errors.append("[E-DUP] %s: entity_id duplicato" % scenario_id)

    relations = {}
    for relation in block["relations"]:
        relation_id = relation["relation_id"]
        r_where = "%s / %s" % (scenario_id, relation_id)
        if relation_id in relations:
            errors.append("[E-DUP] %s: relation_id duplicato '%s'" % (scenario_id, relation_id))
        relations[relation_id] = relation
        for role in ("subject", "object"):
            if relation[role] not in entities:
                errors.append("[E-GRAPH] %s: %s '%s' non e' un'entita' dichiarata" % (r_where, role, relation[role]))
        if not relation["source_message_ids"]:
            errors.append("[E-GRAPH] %s: relazione senza evidenze sorgente" % r_where)
        for message_id in relation["source_message_ids"]:
            if message_id not in messages_by_id:
                errors.append("[E-PROVENANCE] %s: messaggio sorgente inesistente '%s'" % (r_where, message_id))

    for entity in block["entities"]:
        for message_id in entity["source_message_ids"]:
            if message_id not in messages_by_id:
                errors.append("[E-PROVENANCE] %s / %s: messaggio sorgente inesistente '%s'"
                              % (scenario_id, entity["entity_id"], message_id))

    for question in questions:
        q_where = "%s / %s" % (scenario_id, question["question_id"])
        for relation_id in question["required_relations"]:
            if relation_id not in relations:
                errors.append("[E-GRAPH] %s: relazione richiesta inesistente '%s'" % (q_where, relation_id))
        path = question["required_relation_chain"]
        if not path:
            continue
        for relation_id in path:
            if relation_id not in question["required_relations"]:
                errors.append("[E-GRAPH] %s: la catena cita '%s', che non e' fra le relazioni richieste"
                              % (q_where, relation_id))
        # La catena esplicativa deve essere connessa: due relazioni consecutive
        # condividono almeno un'entita'. Non deve essere un percorso semplice:
        # puo' ripassare da un'entita' gia' incontrata, perche' descrive il
        # racconto richiesto dalla domanda e non lo shortest path del retriever.
        for first, second in zip(path, path[1:]):
            a, b = relations.get(first), relations.get(second)
            if not a or not b:
                continue
            if not ({a["subject"], a["object"]} & {b["subject"], b["object"]}):
                errors.append("[E-GRAPH] %s: la catena esplicativa si interrompe fra '%s' e '%s'"
                              % (q_where, first, second))


# --------------------------------------------------------------------------
# Configurazione
# --------------------------------------------------------------------------

def validate_config(config, errors):
    matrix = config.get("matrix", {})
    for scenario_id, expected in ROADMAP_MATRIX.items():
        entry = matrix.get(scenario_id)
        if not entry:
            errors.append("[E-MATRIX] configurazione: manca la riga di %s" % scenario_id)
            continue
        if list(entry.get("planned", [])) != expected:
            errors.append("[E-MATRIX] %s: modalita' previste %s, la roadmap indica %s"
                          % (scenario_id, entry.get("planned"), expected))
        runnable = list(entry.get("runnable_now", []))
        for mode in runnable:
            if mode not in expected:
                errors.append("[E-MATRIX] %s: '%s' eseguibile ma non prevista dalla matrice" % (scenario_id, mode))
            if not config["modes"].get(mode, {}).get("implemented"):
                errors.append("[E-MATRIX] %s: '%s' dichiarata eseguibile ma non implementata" % (scenario_id, mode))

    extra = set(matrix) - set(ROADMAP_MATRIX) - {"note"}
    if extra:
        errors.append("[E-MATRIX] configurazione: scenari non previsti nella matrice: %s" % ", ".join(sorted(extra)))

    total = sum(EXPECTED_QUESTIONS * len(modes) for modes in ROADMAP_MATRIX.values())
    declared = config.get("expected_generations_when_complete", {}).get("total")
    if total != ROADMAP_TOTAL_GENERATIONS:
        errors.append("[E-MATRIX] configurazione: la matrice produce %d generazioni, la roadmap ne prevede %d"
                      % (total, ROADMAP_TOTAL_GENERATIONS))
    if declared != ROADMAP_TOTAL_GENERATIONS:
        errors.append("[E-MATRIX] configurazione: total dichiarato %s, atteso %d" % (declared, ROADMAP_TOTAL_GENERATIONS))

    budget = config.get("context_budget", {})
    if not isinstance(budget.get("max_tokens"), int) or budget["max_tokens"] <= 0:
        errors.append("[E-BUDGET] configurazione: max_tokens deve essere un intero positivo")
    if rq2.FULL_HISTORY in budget.get("applies_to", []):
        errors.append("[E-BUDGET] configurazione: FULL_HISTORY non deve essere soggetto al budget")
    if rq2.FULL_HISTORY not in budget.get("excluded", []):
        errors.append("[E-BUDGET] configurazione: FULL_HISTORY deve essere dichiarato fuori dal budget")
    for mode in rq2.BUDGETED_MODES:
        if mode not in budget.get("applies_to", []):
            errors.append("[E-BUDGET] configurazione: il budget deve applicarsi anche a %s" % mode)
    try:
        re.compile(budget["token_counting"]["regex"])
    except (KeyError, re.error) as exc:
        errors.append("[E-BUDGET] configurazione: metodo di conteggio dei token non valido (%s)" % exc)
    if not budget.get("selection_rule", {}).get("steps"):
        errors.append("[E-BUDGET] configurazione: manca la regola deterministica di selezione")
    if config.get("frozen") is not False:
        errors.append("[E-STATUS] configurazione: 'frozen' deve essere false in questa fase")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def validate_all(scenario_ids=rq2.SCENARIO_IDS, config=None):
    errors = []
    config = config or rq2.load_config()
    validate_config(config, errors)

    all_message_ids = set()
    all_question_ids = set()

    for scenario_id in scenario_ids:
        validate_scenario_file(scenario_id, errors)
        scenario = rq2.load_scenario(scenario_id)
        messages_by_id = validate_sessions(scenario, errors)
        user_ids = {entry["message_id"] for entry in rq2.user_messages(scenario)}
        session_order = {s["session_id"]: s["order"] for s in scenario["sessions"]}

        duplicated = all_message_ids & set(messages_by_id)
        if duplicated:
            errors.append("[E-DUP] collezione: message_id ripetuti fra scenari: %s" % ", ".join(sorted(duplicated)))
        all_message_ids |= set(messages_by_id)

        annotation = rq2.load_annotation_file(scenario_id)
        if annotation.get("frozen") is not False:
            errors.append("[E-STATUS] %s: le annotazioni devono restare 'frozen': false finche' non sono approvate"
                          % scenario_id)
        if not annotation.get("review_required"):
            errors.append("[E-STATUS] %s: le annotazioni devono dichiarare review_required: true" % scenario_id)

        questions = rq2.load_questions(scenario_id)
        ids = {q["question_id"] for q in questions}
        if ids & all_question_ids:
            errors.append("[E-DUP] collezione: question_id ripetuti: %s" % ", ".join(sorted(ids & all_question_ids)))
        all_question_ids |= ids

        validate_questions(scenario_id, questions, messages_by_id, user_ids, session_order, errors)

        if annotation.get("overlay"):
            validate_overlay(scenario_id, questions, errors)

        if scenario_id == "scenario_03":
            validate_operations(scenario_id, annotation, messages_by_id, session_order, errors,
                                require_full_policy=True)
            validate_state(scenario_id, annotation, errors)
        elif scenario_id == "scenario_04":
            validate_operations(scenario_id, annotation, messages_by_id, session_order, errors,
                                require_full_policy=False)
            validate_graph(scenario_id, annotation, questions, messages_by_id, errors)

    return errors


def main(argv=None):
    config = rq2.load_config()
    errors = validate_all(config=config)

    print("Validazione del dataset RQ2 (configurazione %s, stato: %s)"
          % (config["config_id"], "non congelata" if not config["frozen"] else "congelata"))
    print("-" * 78)
    print("%-13s %-9s %-9s %-9s %-9s %s" % ("scenario", "sessioni", "messaggi", "utente", "domande", "modalita' previste"))
    for scenario_id in rq2.SCENARIO_IDS:
        scenario = rq2.load_scenario(scenario_id)
        questions = rq2.load_questions(scenario_id)
        print("%-13s %-9d %-9d %-9d %-9d %s" % (
            scenario_id,
            len(scenario["sessions"]),
            sum(len(s["messages"]) for s in scenario["sessions"]),
            len(rq2.user_messages(scenario)),
            len(questions),
            ", ".join(rq2.planned_modes(scenario_id, config)),
        ))
    print("-" * 78)

    if errors:
        print("\n%d errore/i di validazione:" % len(errors))
        for error in errors:
            print("  - %s" % error)
        return 1
    print("\nValidazione superata: 4 scenari, 28 domande, nessun errore.")
    print("Le annotazioni di SC01-SC04 restano una bozza da controllare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
