#!/usr/bin/env python3
"""Funzioni condivise dell'esperimento principale RQ2.

Questo modulo tiene in un posto solo le cose che tutti gli script di RQ2 devono
fare allo stesso modo:

  - trovare i dati giusti, senza toccare quelli del pilot;
  - separare le *conversazioni* (unico input ammesso per costruire la memoria)
    dalle *annotazioni di valutazione* (domande, oracle, operazioni, relazioni);
  - costruire gli elementi di contesto nella forma *esatta* in cui finiranno
    nel prompt, e contarne i token con il metodo dichiarato in
    `data/rq2/config/experiment_rq2.json`;
  - applicare la stessa regola deterministica di selezione entro il budget.

Il ranking TF-IDF non viene riscritto: si riusano le funzioni gia' provate del
pilot (`scripts/run_retrieval_pilot.py`). Cambia soltanto cosa viene messo in
classifica (messaggi per T, fatti per F) e come si taglia la classifica (budget
in token invece di top-k fisso).

Nessuna funzione di questo modulo scrive nella cartella `results/` del pilot.
Solo libreria standard.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import run_retrieval_pilot as pilot_rag  # noqa: E402  (riuso del ranking del pilot)

# --------------------------------------------------------------------------
# Percorsi: RQ2 scrive soltanto sotto data/rq2 e results/rq2
# --------------------------------------------------------------------------

PILOT_SCENARIO_DIR = REPO_ROOT / "data" / "scenarios"
RQ2_SCENARIO_DIR = REPO_ROOT / "data" / "rq2" / "scenarios"
RQ2_ANNOTATION_DIR = REPO_ROOT / "data" / "rq2" / "annotations"
RQ2_CONFIG_PATH = REPO_ROOT / "data" / "rq2" / "config" / "experiment_rq2.json"
RQ2_RESULTS_DIR = REPO_ROOT / "results" / "rq2"

SCENARIO_IDS = ("scenario_01", "scenario_02", "scenario_03", "scenario_04")

# Da dove arrivano le conversazioni di ogni scenario.
#   - SC01 e SC02 sono quelli del pilot e vengono letti in sola lettura;
#   - SC03 e SC04 sono nuovi e vivono sotto data/rq2.
SCENARIO_SOURCES = {
    "scenario_01": ("pilot", PILOT_SCENARIO_DIR / "scenario_01.json"),
    "scenario_02": ("pilot", PILOT_SCENARIO_DIR / "scenario_02.json"),
    "scenario_03": ("rq2", RQ2_SCENARIO_DIR / "scenario_03.json"),
    "scenario_04": ("rq2", RQ2_SCENARIO_DIR / "scenario_04.json"),
}

ANNOTATION_PATHS = {
    scenario_id: RQ2_ANNOTATION_DIR / ("%s_rq2.json" % scenario_id)
    for scenario_id in SCENARIO_IDS
}

MODES = ("T", "F", "U", "G", "FULL_HISTORY")
BUDGETED_MODES = ("T", "F", "U", "G")
FULL_HISTORY = "FULL_HISTORY"

INDEXED_ROLE = "user"

# Categorie ammesse per le domande di RQ2: le sette del pilot piu' due
# fenomeni introdotti da SC03 e SC04.
ALLOWED_CATEGORIES = (
    "goal",
    "update_obsolete",
    "completed_activity",
    "pending_activity",
    "local_information",
    "cross_session_link",
    "absent_information",
    "retracted_information",
    "declared_unknown",
)

ALLOWED_FACT_KINDS = (
    "osservazione",
    "ipotesi",
    "conferma",
    "decisione",
    "stato",
    "ritiro",
    "relazione",
)

ALLOWED_OPERATIONS = ("ADD", "UPDATE", "DELETE", "NOOP")

# Stati di un fatto nella memoria di U (e di un arco nel grafo di G).
STATE_ACTIVE = "attivo"
STATE_SUPERSEDED = "superato"
STATE_RETRACTED = "ritirato"
ALLOWED_STATES = (STATE_ACTIVE, STATE_SUPERSEDED, STATE_RETRACTED)

BEHAVIOR_ANSWER = "Risposta completa"
BEHAVIOR_ABSTAIN = "Astensione"


# --------------------------------------------------------------------------
# Configurazione
# --------------------------------------------------------------------------

def load_config(path=RQ2_CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def budget_tokens(config=None):
    config = config or load_config()
    return int(config["context_budget"]["max_tokens"])


def token_regex(config=None):
    config = config or load_config()
    return re.compile(config["context_budget"]["token_counting"]["regex"])


_DEFAULT_TOKEN_RE = None


def count_tokens(text, config=None):
    """Conteggio dei token dichiarato nella configurazione.

    Non e' il tokenizzatore del modello: e' l'unita' di misura del progetto,
    deterministica e senza dipendenze. Serve a dare a T, F, U e G esattamente
    lo stesso budget.
    """
    global _DEFAULT_TOKEN_RE
    if config is None:
        if _DEFAULT_TOKEN_RE is None:
            _DEFAULT_TOKEN_RE = token_regex()
        pattern = _DEFAULT_TOKEN_RE
    else:
        pattern = token_regex(config)
    return len(pattern.findall(text))


# --------------------------------------------------------------------------
# Conversazioni (unico input ammesso per costruire la memoria)
# --------------------------------------------------------------------------

def load_scenario(scenario_id):
    """Conversazioni dello scenario, senza domande e senza oracle.

    Per SC01 e SC02 il file del pilot viene letto e ridotto alle sole sessioni:
    le domande e l'oracle del pilot non escono da questa funzione, cosi' non
    possono finire per sbaglio nell'estrattore o nel prompt.
    """
    if scenario_id not in SCENARIO_SOURCES:
        raise KeyError("scenario sconosciuto: %s" % scenario_id)
    origin, path = SCENARIO_SOURCES[scenario_id]
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return {
        "scenario_id": raw["scenario_id"],
        "title": raw.get("title", ""),
        "origin": origin,
        "source_file": str(path.relative_to(REPO_ROOT)),
        "sessions": raw["sessions"],
    }


def load_scenarios(scenario_ids=SCENARIO_IDS):
    return [load_scenario(scenario_id) for scenario_id in scenario_ids]


def user_messages(scenario):
    """Messaggi indicizzabili in ordine cronologico, con i loro token."""
    entries = []
    for session in scenario["sessions"]:
        for message in session["messages"]:
            if message["role"] != INDEXED_ROLE:
                continue
            entries.append(
                {
                    "message_id": message["message_id"],
                    "session_id": session["session_id"],
                    "session_order": session["order"],
                    "message_order": message["order"],
                    "content": message["content"],
                    "tokens": count_tokens(message["content"]),
                }
            )
    entries.sort(key=lambda entry: (entry["session_order"], entry["message_order"]))
    return entries


def message_index(scenario):
    """message_id -> messaggio, per tutti i messaggi (anche dell'assistente)."""
    index = {}
    for session in scenario["sessions"]:
        for message in session["messages"]:
            index[message["message_id"]] = message
    return index


def sessions_in_order(scenario):
    return sorted(scenario["sessions"], key=lambda session: session["order"])


# --------------------------------------------------------------------------
# Annotazioni di valutazione (mai in input a memoria, retrieval o risposta)
# --------------------------------------------------------------------------

def load_annotation_file(scenario_id):
    with open(ANNOTATION_PATHS[scenario_id], "r", encoding="utf-8") as handle:
        return json.load(handle)


def _derive_evidence_ids(required_facts):
    """Messaggi sorgente dei fatti obbligatori, senza duplicati e in ordine."""
    ordered = []
    for fact in required_facts:
        for message_id in fact["source_message_ids"]:
            if message_id not in ordered:
                ordered.append(message_id)
    return ordered


def load_questions(scenario_id):
    """Domande normalizzate, uguali per tutte le architetture.

    SC03 e SC04 hanno l'oracle completo nel file di annotazione. SC01 e SC02
    tengono l'oracle originale nel file del pilot, che non viene modificato: il
    file di RQ2 e' un *overlay* che aggiunge soltanto la scomposizione in fatti
    con provenienza.
    """
    annotation = load_annotation_file(scenario_id)
    overlay = bool(annotation.get("overlay"))

    if overlay:
        _, pilot_path = SCENARIO_SOURCES[scenario_id]
        with open(pilot_path, "r", encoding="utf-8") as handle:
            pilot = json.load(handle)
        pilot_questions = {q["question_id"]: q for q in pilot["questions"]}
        extra = {q["question_id"]: q for q in annotation["questions"]}
    else:
        pilot_questions = {}
        extra = {}

    questions = []
    source_list = annotation["questions"]
    for entry in source_list:
        question_id = entry["question_id"]
        if overlay:
            base = pilot_questions.get(question_id)
            if base is None:
                raise KeyError(
                    "%s: l'overlay RQ2 cita una domanda assente dal file del pilot" % question_id
                )
            merged = {
                "question_id": question_id,
                "scenario_id": scenario_id,
                "category": base["category"],
                "text": base["text"],
                "expected_answer": base["expected_answer"],
                "mandatory_facts": list(base["mandatory_facts"]),
                "required_facts": list(entry.get("required_facts", [])),
                "obsolete_information": list(base["obsolete_information"]),
                "accepted_equivalents": list(base["accepted_equivalents"]),
                "fact_present_in_corpus": base["fact_present_in_corpus"],
                "expected_behavior": (
                    BEHAVIOR_ANSWER if base["fact_present_in_corpus"] else BEHAVIOR_ABSTAIN
                ),
                "evidence_note": entry.get("evidence_note") or base.get("evidence_note"),
                "required_relations": list(entry.get("required_relations", [])),
                "required_relation_chain": list(entry.get("required_relation_chain", [])),
                "required_state_keys": list(entry.get("required_state_keys", [])),
                "pilot_required_evidence_ids": list(base["required_evidence_ids"]),
                "source": "pilot + overlay RQ2",
            }
        else:
            merged = {
                "question_id": question_id,
                "scenario_id": scenario_id,
                "category": entry["category"],
                "text": entry["text"],
                "expected_answer": entry["expected_answer"],
                "mandatory_facts": list(entry["mandatory_facts"]),
                "required_facts": list(entry.get("required_facts", [])),
                "obsolete_information": list(entry.get("obsolete_information", [])),
                "accepted_equivalents": list(entry.get("accepted_equivalents", [])),
                "fact_present_in_corpus": entry["fact_present_in_corpus"],
                "expected_behavior": entry["expected_behavior"],
                "evidence_note": entry.get("evidence_note"),
                "required_relations": list(entry.get("required_relations", [])),
                "required_relation_chain": list(entry.get("required_relation_chain", [])),
                "required_state_keys": list(entry.get("required_state_keys", [])),
                "pilot_required_evidence_ids": None,
                "source": "annotazione RQ2",
            }
        merged["required_evidence_ids"] = _derive_evidence_ids(merged["required_facts"])
        questions.append(merged)

    # `extra` serve solo a segnalare overlay con domande in piu': la lista di
    # riferimento resta quella del file di annotazione.
    del extra
    return questions


# --------------------------------------------------------------------------
# Matrice scenario x modalita'
# --------------------------------------------------------------------------

def planned_modes(scenario_id, config=None):
    config = config or load_config()
    return list(config["matrix"][scenario_id]["planned"])


def runnable_modes(scenario_id, config=None):
    config = config or load_config()
    return list(config["matrix"][scenario_id]["runnable_now"])


def matrix_rows(config=None):
    config = config or load_config()
    rows = []
    for scenario_id in SCENARIO_IDS:
        entry = config["matrix"][scenario_id]
        rows.append((scenario_id, list(entry["planned"]), list(entry["runnable_now"])))
    return rows


# --------------------------------------------------------------------------
# Elementi di contesto
# --------------------------------------------------------------------------
#
# Un "elemento" e' una riga del blocco di contesto, gia' scritta come finira'
# nel prompt. Il budget si applica a questa riga intera, non al solo testo:
# identificatori, provenienza, stato temporale e relazioni occupano posto nel
# contesto inviato al modello esattamente come le parole del contenuto.

def make_item(item_id, text, render, session_order, item_order,
              source_message_ids, source_fact_ids=None, unit="", state=None, extra=None):
    """Elemento di contesto con il conteggio separato di contenuto e overhead."""
    content_tokens = count_tokens(text)
    total_tokens = count_tokens(render)
    item = {
        "item_id": item_id,
        "text": text,
        "render": render,
        "content_tokens": content_tokens,
        "overhead_tokens": total_tokens - content_tokens,
        "tokens": total_tokens,
        "session_order": session_order,
        "item_order": item_order,
        "source_message_ids": list(source_message_ids),
        "source_fact_ids": list(source_fact_ids or []),
        "unit": unit,
        "state": state,
    }
    if extra:
        item.update(extra)
    return item


def render_message(message_id, content):
    """Riga di contesto di T e di FULL_HISTORY."""
    return "[%s] %s" % (message_id, content)


def render_fact(fact_id, source_message_ids, text):
    """Riga di contesto di F: identificatore, provenienza, testo."""
    return "[%s | da: %s] %s" % (fact_id, ", ".join(source_message_ids), text)


def render_state_entry(entry_id, state_label, source_message_ids, text):
    """Riga di contesto di U: si aggiunge lo stato temporale del fatto."""
    return "[%s | %s | da: %s] %s" % (entry_id, state_label, ", ".join(source_message_ids), text)


def render_node(node_id, label, source_message_ids):
    """Riga di contesto di G per un nodo iniziale."""
    return "[NODO %s | %s | da: %s]" % (node_id, label, ", ".join(source_message_ids))


def render_edge(edge_id, subject, relation, obj, state_label, source_message_ids):
    """Riga di contesto di G per un arco attraversato."""
    return "[%s | %s -%s-> %s | %s | da: %s]" % (
        edge_id, subject, relation, obj, state_label, ", ".join(source_message_ids)
    )


def message_items(scenario):
    """Elementi di T: un messaggio dell'utente per riga."""
    items = []
    for entry in user_messages(scenario):
        items.append(
            make_item(
                item_id=entry["message_id"],
                text=entry["content"],
                render=render_message(entry["message_id"], entry["content"]),
                session_order=entry["session_order"],
                item_order=entry["message_order"],
                source_message_ids=[entry["message_id"]],
                unit="messaggio",
            )
        )
    return items


def context_block(items):
    """Blocco di contesto come finisce nel prompt.

    I token del blocco coincidono con la somma dei token degli elementi: il
    metodo di conteggio ignora gli spazi, quindi gli a capo non aggiungono
    nulla. E' il motivo per cui il budget puo' essere applicato elemento per
    elemento senza discostarsi dal contesto reale.
    """
    return "\n".join(item["render"] for item in items)


# --------------------------------------------------------------------------
# Ranking e selezione entro il budget
# --------------------------------------------------------------------------

def rank_items(query_text, items):
    """Classifica completa degli elementi di memoria per una domanda.

    Riusa il TF-IDF del pilot. `items` e' una lista di dizionari con almeno
    `item_id`, `text`, `session_order` e `item_order`. Il risultato e' la stessa
    lista, ordinata, con i campi `score` e `rank` aggiunti.
    """
    if not items:
        return []

    documents_tokens = [pilot_rag.tokenize(item["text"]) for item in items]
    idf = pilot_rag._idf(documents_tokens)
    document_vectors = [
        pilot_rag._vector(tokens, idf, restrict_to_vocabulary=False) for tokens in documents_tokens
    ]
    query_vector = pilot_rag._vector(
        pilot_rag.tokenize(query_text), idf, restrict_to_vocabulary=True
    )

    scored = []
    for index, item in enumerate(items):
        entry = dict(item)
        entry["score"] = round(pilot_rag._cosine(query_vector, document_vectors[index]), 6)
        scored.append(entry)

    # Parita' risolta dall'ordine di comparsa nello scenario: deterministico.
    scored.sort(key=lambda entry: (-entry["score"], entry["session_order"], entry["item_order"]))
    for position, entry in enumerate(scored, start=1):
        entry["rank"] = position
    return scored


def select_within_budget(ranked, budget, min_score_exclusive=0.0):
    """Regola di selezione dichiarata in experiment_rq2.json.

    Prefisso del ranking: si aggiunge finche' si sta nel budget e ci si ferma
    al primo elemento che non entra. Nessun troncamento. Se il primo elemento
    supera da solo il budget viene incluso ugualmente e segnalato.

    Il costo di un elemento e' `tokens`, cioe' i token della riga gia'
    formattata: contenuto piu' identificatore, provenienza, stato e relazioni.
    """
    selected = []
    total = 0
    stopped_by = None
    first_item_exceeds = False

    for entry in ranked:
        if entry["score"] <= min_score_exclusive:
            stopped_by = {"item_id": entry["item_id"], "reason": "punteggio nullo"}
            break
        tokens = entry["tokens"]
        if total + tokens <= budget:
            selected.append(entry)
            total += tokens
            continue
        if not selected:
            # Garanzia minima: il contesto non resta vuoto per colpa di un solo
            # elemento troppo lungo.
            selected.append(entry)
            total += tokens
            first_item_exceeds = True
        stopped_by = {"item_id": entry["item_id"], "reason": "non entra nel budget"}
        break

    return {
        "selected": selected,
        "context_tokens": total,
        "content_tokens": sum(entry.get("content_tokens", entry["tokens"]) for entry in selected),
        "overhead_tokens": sum(entry.get("overhead_tokens", 0) for entry in selected),
        "budget_tokens": budget,
        "stopped_by": stopped_by,
        "budget_exceeded_by_first_item": first_item_exceeds,
        "examined": len(ranked),
    }


# --------------------------------------------------------------------------
# Utilita' di scrittura
# --------------------------------------------------------------------------

def write_jsonl(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def read_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def relative(path):
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
