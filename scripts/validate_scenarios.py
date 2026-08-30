#!/usr/bin/env python3
"""Validatore degli scenari del pilot (formato JSON).

Controlla che i file `data/scenarios/*.json` siano una conversione fedele e
coerente degli scenari, degli oracle e delle matrici di raggiungibilita'
descritti nei documenti Markdown del pilot.

Il validatore non esegue retrieval, non chiama modelli e non calcola metriche
sperimentali: verifica soltanto la struttura dei dati e la coerenza della
raggiungibilita' teorica dichiarata.

Uso:
    python3 scripts/validate_scenarios.py
    python3 scripts/validate_scenarios.py data/scenarios/scenario_01.json

Codice di uscita: 0 se non ci sono errori, 1 altrimenti.
Solo libreria standard.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCENARIO_DIR = REPO_ROOT / "data" / "scenarios"

CONDITIONS = ("C0", "C1", "C2")

ALLOWED_CATEGORIES = (
    "goal",
    "update_obsolete",
    "completed_activity",
    "pending_activity",
    "local_information",
    "cross_session_link",
    "absent_information",
)

ABSENT_CATEGORY = "absent_information"

EXPECTED_SESSIONS_PER_SCENARIO = 4
EXPECTED_QUESTIONS_PER_SCENARIO = 7

BEHAVIOR_REACHABLE = "Risposta completa"
BEHAVIOR_UNREACHABLE = "Astensione"

# Copertura attesa (pilot_summary.md, sezione 2).
EXPECTED_COVERAGE = {
    "scenario_01": {"C0": 0, "C1": 2, "C2": 6},
    "scenario_02": {"C0": 0, "C1": 3, "C2": 6},
}
EXPECTED_TOTAL_COVERAGE = {"C0": 0, "C1": 5, "C2": 12}
EXPECTED_TOTAL_QUESTIONS = 14

SCENARIO_FIELDS = {
    "scenario_id": str,
    "title": str,
    "version": str,
    "source_files": list,
    "conditions": dict,
    "expected_reachability_totals": dict,
    "sessions": list,
    "questions": list,
}

SESSION_FIELDS = {
    "session_id": str,
    "order": int,
    "title": str,
    "messages": list,
}

MESSAGE_FIELDS = {
    "message_id": str,
    "order": int,
    "role": str,
    "content": str,
    "session_id": str,
}

QUESTION_FIELDS = {
    "question_id": str,
    "category": str,
    "text": str,
    "expected_answer": str,
    "mandatory_facts": list,
    "required_evidence_ids": list,
    "obsolete_information": list,
    "accepted_equivalents": list,
    "reachability": dict,
    "expected_behavior_when_unreachable": str,
    "fact_present_in_corpus": bool,
    "expected_behavior_by_condition": dict,
}

ALLOWED_ROLES = ("user", "assistant")


def _check_fields(obj, spec, where, errors):
    """Verifica presenza e tipo dei campi obbligatori. True se tutti presenti."""
    ok = True
    if not isinstance(obj, dict):
        errors.append("[E-FIELD] %s: atteso un oggetto JSON, trovato %s" % (where, type(obj).__name__))
        return False
    for name, expected_type in spec.items():
        if name not in obj:
            errors.append("[E-FIELD] %s: campo obbligatorio mancante '%s'" % (where, name))
            ok = False
            continue
        value = obj[name]
        # bool e' sottoclasse di int: va distinto esplicitamente.
        if expected_type is int and isinstance(value, bool):
            errors.append("[E-FIELD] %s: campo '%s' deve essere int, trovato bool" % (where, name))
            ok = False
            continue
        if not isinstance(value, expected_type):
            errors.append(
                "[E-FIELD] %s: campo '%s' deve essere %s, trovato %s"
                % (where, name, expected_type.__name__, type(value).__name__)
            )
            ok = False
    return ok


def _check_unique(values, kind, where, errors):
    seen = set()
    for value in values:
        if value in seen:
            errors.append("[E-DUP] %s: %s duplicato '%s'" % (where, kind, value))
        seen.add(value)


def load_scenario(path):
    """Carica uno scenario da file JSON."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_scenario(scenario, source=None, repo_root=REPO_ROOT):
    """Valida un singolo scenario. Restituisce la lista degli errori trovati."""
    errors = []
    where = str(source) if source else "scenario"
    if not _check_fields(scenario, SCENARIO_FIELDS, where, errors):
        return errors

    scenario_id = scenario["scenario_id"]
    where = "%s (%s)" % (scenario_id, source) if source else scenario_id

    # --- 1. file sorgente dichiarati -------------------------------------
    for rel in scenario["source_files"]:
        if not isinstance(rel, str):
            errors.append("[E-SOURCE-FILE] %s: source_files deve contenere stringhe" % where)
            continue
        if repo_root is not None and not (Path(repo_root) / rel).exists():
            errors.append("[E-SOURCE-FILE] %s: file sorgente inesistente '%s'" % (where, rel))

    # --- 2. sessioni e messaggi ------------------------------------------
    sessions = scenario["sessions"]
    if len(sessions) != EXPECTED_SESSIONS_PER_SCENARIO:
        errors.append(
            "[E-COUNT] %s: attese %d sessioni, trovate %d"
            % (where, EXPECTED_SESSIONS_PER_SCENARIO, len(sessions))
        )

    session_ids = []
    messages_by_id = {}
    for index, session in enumerate(sessions):
        s_where = "%s / sessione #%d" % (where, index + 1)
        if not _check_fields(session, SESSION_FIELDS, s_where, errors):
            continue
        session_id = session["session_id"]
        session_ids.append(session_id)
        s_where = "%s / %s" % (where, session_id)
        if session["order"] != index + 1:
            errors.append(
                "[E-ORDER] %s: order %s incoerente con la posizione %d"
                % (s_where, session["order"], index + 1)
            )
        if not session["messages"]:
            errors.append("[E-COUNT] %s: la sessione non contiene messaggi" % s_where)
        for m_index, message in enumerate(session["messages"]):
            m_where = "%s / messaggio #%d" % (s_where, m_index + 1)
            if not _check_fields(message, MESSAGE_FIELDS, m_where, errors):
                continue
            message_id = message["message_id"]
            m_where = "%s / %s" % (s_where, message_id)
            if message["order"] != m_index + 1:
                errors.append(
                    "[E-ORDER] %s: order %s incoerente con la posizione %d"
                    % (m_where, message["order"], m_index + 1)
                )
            if message["role"] not in ALLOWED_ROLES:
                errors.append(
                    "[E-FIELD] %s: role '%s' non ammesso (ammessi: %s)"
                    % (m_where, message["role"], ", ".join(ALLOWED_ROLES))
                )
            if not message["content"].strip():
                errors.append("[E-FIELD] %s: content vuoto" % m_where)
            if message["session_id"] != session_id:
                errors.append(
                    "[E-EVIDENCE-SESSION] %s: il messaggio dichiara session_id '%s' ma appartiene a '%s'"
                    % (m_where, message["session_id"], session_id)
                )
            if message_id in messages_by_id:
                errors.append("[E-DUP] %s: message_id duplicato '%s'" % (where, message_id))
            else:
                messages_by_id[message_id] = session_id

    _check_unique(session_ids, "session_id", where, errors)

    # --- 3. perimetri delle condizioni -----------------------------------
    conditions = scenario["conditions"]
    canonical_perimeter = {
        "C0": [],
        "C1": session_ids[-1:],
        "C2": list(session_ids),
    }
    accessible = {}
    for condition in CONDITIONS:
        entry = conditions.get(condition)
        if not isinstance(entry, dict) or not isinstance(entry.get("accessible_sessions"), list):
            errors.append(
                "[E-PERIMETER] %s: condizione '%s' assente o priva di accessible_sessions"
                % (where, condition)
            )
            accessible[condition] = canonical_perimeter[condition]
            continue
        declared = entry["accessible_sessions"]
        accessible[condition] = declared
        unknown = [s for s in declared if s not in session_ids]
        if unknown:
            errors.append(
                "[E-PERIMETER] %s: la condizione %s dichiara sessioni inesistenti: %s"
                % (where, condition, ", ".join(map(str, unknown)))
            )
        if declared != canonical_perimeter[condition]:
            errors.append(
                "[E-PERIMETER] %s: perimetro di %s incoerente: atteso %s, dichiarato %s"
                % (where, condition, canonical_perimeter[condition], declared)
            )

    # --- 4. domande -------------------------------------------------------
    questions = scenario["questions"]
    if len(questions) != EXPECTED_QUESTIONS_PER_SCENARIO:
        errors.append(
            "[E-COUNT] %s: attese %d domande, trovate %d"
            % (where, EXPECTED_QUESTIONS_PER_SCENARIO, len(questions))
        )

    question_ids = []
    categories = []
    coverage = {condition: 0 for condition in CONDITIONS}

    for index, question in enumerate(questions):
        q_where = "%s / domanda #%d" % (where, index + 1)
        if not _check_fields(question, QUESTION_FIELDS, q_where, errors):
            continue
        question_id = question["question_id"]
        question_ids.append(question_id)
        q_where = "%s / %s" % (where, question_id)

        category = question["category"]
        categories.append(category)
        if category not in ALLOWED_CATEGORIES:
            errors.append(
                "[E-CATEGORY] %s: categoria '%s' non ammessa (ammesse: %s)"
                % (q_where, category, ", ".join(ALLOWED_CATEGORIES))
            )

        for name in ("text", "expected_answer", "expected_behavior_when_unreachable"):
            if not question[name].strip():
                errors.append("[E-FIELD] %s: campo '%s' vuoto" % (q_where, name))
        if not question["mandatory_facts"]:
            errors.append("[E-FIELD] %s: mandatory_facts non puo' essere vuoto" % q_where)

        # 4a. le evidenze devono esistere e appartenere alle sessioni dello scenario
        evidence_sessions = []
        for evidence_id in question["required_evidence_ids"]:
            if evidence_id not in messages_by_id:
                errors.append(
                    "[E-EVIDENCE-MISSING] %s: required_evidence_id inesistente '%s'"
                    % (q_where, evidence_id)
                )
                continue
            evidence_session = messages_by_id[evidence_id]
            evidence_sessions.append(evidence_session)
            if evidence_session not in session_ids:
                errors.append(
                    "[E-EVIDENCE-SESSION] %s: l'evidenza '%s' non appartiene alle sessioni dello scenario"
                    % (q_where, evidence_id)
                )
        _check_unique(question["required_evidence_ids"], "required_evidence_id", q_where, errors)

        # 4b. rappresentazione dell'informazione mai fornita
        fact_present = question["fact_present_in_corpus"]
        if (category == ABSENT_CATEGORY) != (not fact_present):
            errors.append(
                "[E-ABSENT] %s: categoria '%s' e fact_present_in_corpus=%s sono incoerenti"
                % (q_where, category, fact_present)
            )
        if not fact_present:
            if question["required_evidence_ids"]:
                errors.append(
                    "[E-ABSENT] %s: un'informazione mai fornita non puo' dichiarare evidenze (%s)"
                    % (q_where, ", ".join(question["required_evidence_ids"]))
                )
            if not str(question.get("evidence_note") or "").strip():
                errors.append(
                    "[E-ABSENT] %s: manca evidence_note che documenti l'assenza dell'informazione" % q_where
                )
        elif not question["required_evidence_ids"]:
            errors.append(
                "[E-ABSENT] %s: fact_present_in_corpus=true ma nessuna evidenza obbligatoria dichiarata"
                % q_where
            )

        # 4c. coerenza della raggiungibilita' dichiarata con i perimetri
        reachability = question["reachability"]
        missing_conditions = [c for c in CONDITIONS if c not in reachability]
        if missing_conditions:
            errors.append(
                "[E-REACH] %s: reachability priva delle condizioni %s"
                % (q_where, ", ".join(missing_conditions))
            )
        for condition in CONDITIONS:
            if condition not in reachability:
                continue
            declared = reachability[condition]
            if not isinstance(declared, bool):
                errors.append(
                    "[E-REACH] %s: reachability[%s] deve essere booleano, trovato %s"
                    % (q_where, condition, type(declared).__name__)
                )
                continue
            if not fact_present:
                # EXPERIMENT.md 9.1: un fatto mai fornito non e' mai raggiungibile.
                expected = False
            else:
                perimeter = set(accessible[condition])
                expected = bool(evidence_sessions) and all(s in perimeter for s in evidence_sessions)
            if declared != expected:
                errors.append(
                    "[E-REACH] %s: reachability[%s] dichiarata %s ma calcolata %s"
                    % (q_where, condition, declared, expected)
                )
            if declared:
                coverage[condition] += 1

            behavior = question["expected_behavior_by_condition"].get(condition)
            expected_behavior = BEHAVIOR_REACHABLE if declared else BEHAVIOR_UNREACHABLE
            if behavior != expected_behavior:
                errors.append(
                    "[E-BEHAVIOR] %s: expected_behavior_by_condition[%s] = %r, atteso %r"
                    % (q_where, condition, behavior, expected_behavior)
                )

    _check_unique(question_ids, "question_id", where, errors)

    missing_categories = [c for c in ALLOWED_CATEGORIES if c not in categories]
    if missing_categories:
        errors.append(
            "[E-CATEGORY] %s: fenomeni non coperti dalle domande: %s"
            % (where, ", ".join(missing_categories))
        )

    # --- 5. copertura attesa dello scenario -------------------------------
    declared_totals = scenario["expected_reachability_totals"]
    for condition in CONDITIONS:
        if declared_totals.get(condition) != coverage[condition]:
            errors.append(
                "[E-COVERAGE] %s: expected_reachability_totals[%s] = %s ma le domande raggiungibili sono %d"
                % (where, condition, declared_totals.get(condition), coverage[condition])
            )
    if declared_totals.get("total_questions") != len(questions):
        errors.append(
            "[E-COVERAGE] %s: expected_reachability_totals[total_questions] = %s ma le domande sono %d"
            % (where, declared_totals.get("total_questions"), len(questions))
        )

    expected = EXPECTED_COVERAGE.get(scenario_id)
    if expected is None:
        errors.append(
            "[E-COVERAGE] %s: nessuna copertura attesa registrata per questo scenario_id" % where
        )
    else:
        for condition in CONDITIONS:
            if coverage[condition] != expected[condition]:
                errors.append(
                    "[E-COVERAGE] %s: %s raggiungibile %d/%d, attesa %d/%d"
                    % (
                        where,
                        condition,
                        coverage[condition],
                        len(questions),
                        expected[condition],
                        EXPECTED_QUESTIONS_PER_SCENARIO,
                    )
                )

    return errors


def coverage_of(scenario):
    """Domande raggiungibili per condizione, secondo la raggiungibilita' dichiarata."""
    counts = {condition: 0 for condition in CONDITIONS}
    for question in scenario.get("questions", []):
        reachability = question.get("reachability", {})
        for condition in CONDITIONS:
            if reachability.get(condition) is True:
                counts[condition] += 1
    return counts


def validate_collection(scenarios, sources=None, repo_root=REPO_ROOT):
    """Valida l'insieme degli scenari, inclusi i controlli globali."""
    errors = []
    sources = sources or [None] * len(scenarios)
    for scenario, source in zip(scenarios, sources):
        errors.extend(validate_scenario(scenario, source=source, repo_root=repo_root))

    scenario_ids = [s.get("scenario_id") for s in scenarios if isinstance(s, dict)]
    _check_unique(scenario_ids, "scenario_id", "collezione", errors)

    all_session_ids, all_message_ids, all_question_ids = [], [], []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        for session in scenario.get("sessions", []):
            if not isinstance(session, dict):
                continue
            all_session_ids.append(session.get("session_id"))
            for message in session.get("messages", []):
                if isinstance(message, dict):
                    all_message_ids.append(message.get("message_id"))
        for question in scenario.get("questions", []):
            if isinstance(question, dict):
                all_question_ids.append(question.get("question_id"))
    _check_unique(all_session_ids, "session_id", "collezione", errors)
    _check_unique(all_message_ids, "message_id", "collezione", errors)
    _check_unique(all_question_ids, "question_id", "collezione", errors)

    # Copertura complessiva attesa: solo quando la collezione e' quella del pilot.
    if sorted(filter(None, scenario_ids)) == sorted(EXPECTED_COVERAGE):
        total_questions = sum(len(s.get("questions", [])) for s in scenarios)
        totals = {condition: 0 for condition in CONDITIONS}
        for scenario in scenarios:
            for condition, value in coverage_of(scenario).items():
                totals[condition] += value
        if total_questions != EXPECTED_TOTAL_QUESTIONS:
            errors.append(
                "[E-COVERAGE] collezione: attese %d domande complessive, trovate %d"
                % (EXPECTED_TOTAL_QUESTIONS, total_questions)
            )
        for condition in CONDITIONS:
            if totals[condition] != EXPECTED_TOTAL_COVERAGE[condition]:
                errors.append(
                    "[E-COVERAGE] collezione: %s raggiungibile %d/%d, attesa %d/%d"
                    % (
                        condition,
                        totals[condition],
                        total_questions,
                        EXPECTED_TOTAL_COVERAGE[condition],
                        EXPECTED_TOTAL_QUESTIONS,
                    )
                )
    return errors


def default_paths():
    return sorted(DEFAULT_SCENARIO_DIR.glob("scenario_*.json"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Valida gli scenari JSON del pilot.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="file JSON da validare (default: data/scenarios/scenario_*.json)",
    )
    parser.add_argument("--quiet", action="store_true", help="stampa soltanto gli errori")
    args = parser.parse_args(argv)

    paths = [Path(p) for p in args.paths] or default_paths()
    if not paths:
        print("Nessuno scenario trovato in %s" % DEFAULT_SCENARIO_DIR, file=sys.stderr)
        return 1

    scenarios, sources, errors = [], [], []
    for path in paths:
        try:
            scenarios.append(load_scenario(path))
            sources.append(path.name)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append("[E-FIELD] %s: impossibile leggere il JSON (%s)" % (path, exc))

    errors.extend(validate_collection(scenarios, sources=sources))

    if not args.quiet:
        for scenario, source in zip(scenarios, sources):
            counts = coverage_of(scenario)
            print(
                "%-14s %-32s sessioni=%d messaggi=%d domande=%d  raggiungibili C0=%d C1=%d C2=%d"
                % (
                    scenario.get("scenario_id", "?"),
                    source,
                    len(scenario.get("sessions", [])),
                    sum(len(s.get("messages", [])) for s in scenario.get("sessions", [])),
                    len(scenario.get("questions", [])),
                    counts["C0"],
                    counts["C1"],
                    counts["C2"],
                )
            )

    if errors:
        print("\n%d errore/i di validazione:" % len(errors))
        for error in errors:
            print("  - %s" % error)
        return 1

    if not args.quiet:
        print("\nValidazione superata: %d scenario/i senza errori." % len(scenarios))
    return 0


if __name__ == "__main__":
    sys.exit(main())
