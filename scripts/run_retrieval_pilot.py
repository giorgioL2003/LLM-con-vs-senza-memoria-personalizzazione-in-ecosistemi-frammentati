#!/usr/bin/env python3
"""Prima prova automatica del retrieval Turn-level RAG del pilot.

Lo script esegue soltanto la parte di *recupero*: non costruisce prompt, non
chiama nessun modello e non genera risposte. Serve a misurare se, dato il
perimetro di memoria di una condizione, un retriever elementare mette davvero
nel contesto le evidenze obbligatorie dichiarate dall'oracle.

Retriever: TF-IDF con similarita' del coseno, scritto con la sola libreria
standard di Python.

Regole fissate per il pilot:
  - l'unita' recuperabile e' il singolo messaggio (Turn-level RAG);
  - vengono indicizzati soltanto i messaggi dell'utente: i messaggi
    dell'assistente non introducono fatti autorevoli;
  - la query e' il testo della domanda;
  - testo in minuscolo, tokenizzazione che conserva parole, numeri, trattini
    e underscore;
  - top-k = 2; se il corpus contiene meno di due messaggi vengono restituiti
    tutti quelli disponibili;
  - a parita' di punteggio l'ordine e' deterministico (ordine di sessione e
    poi ordine del messaggio).

Le condizioni non sono ricalcolate qui: vengono lette da
`conditions[...].accessible_sessions` nei file JSON degli scenari. C1 e C2 usano
lo stesso identico algoritmo: cambia soltanto il corpus accessibile.

Uso:
    python3 scripts/run_retrieval_pilot.py

Lo script non modifica i file di input. Scrive una riga JSON per esecuzione in
`results/retrieval_pilot.jsonl`.
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIO_DIR = REPO_ROOT / "data" / "scenarios"
RESULTS_PATH = REPO_ROOT / "results" / "retrieval_pilot.jsonl"

CONDITIONS = ("C0", "C1", "C2")
TOP_K = 2
INDEXED_ROLE = "user"

# Domande cross-session di cui stampare la traccia leggibile.
TRACE_QUESTION_IDS = ("SC01-Q6", "SC02-Q6")

TOKEN_RE = re.compile(r"[a-z0-9_-]+")


# --------------------------------------------------------------------------
# TF-IDF minimale
# --------------------------------------------------------------------------

def tokenize(text):
    """Minuscolo + token di parole, numeri, trattini e underscore."""
    return TOKEN_RE.findall(text.lower())


def _term_counts(tokens):
    counts = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts


def _idf(documents_tokens):
    """idf smussato: ln((1 + N) / (1 + df)) + 1.

    Lo smussamento evita che un termine presente in tutti i documenti (df = N)
    ottenga peso esattamente zero, cosa che con corpus di 4 messaggi
    azzererebbe troppi confronti.
    """
    total = len(documents_tokens)
    document_frequency = {}
    for tokens in documents_tokens:
        for term in set(tokens):
            document_frequency[term] = document_frequency.get(term, 0) + 1
    return {
        term: math.log((1 + total) / (1 + df)) + 1.0
        for term, df in document_frequency.items()
    }


def _vector(tokens, idf, restrict_to_vocabulary):
    """Vettore TF-IDF normalizzato (L2), come dizionario termine -> peso."""
    weights = {}
    for term, count in _term_counts(tokens).items():
        weight = idf.get(term)
        if weight is None:
            if restrict_to_vocabulary:
                continue
            weight = 1.0
        weights[term] = count * weight
    norm = math.sqrt(sum(value * value for value in weights.values()))
    if norm == 0.0:
        return {}
    return {term: value / norm for term, value in weights.items()}


def _cosine(query_vector, document_vector):
    """Coseno fra due vettori gia' normalizzati: e' il prodotto scalare."""
    if len(query_vector) > len(document_vector):
        query_vector, document_vector = document_vector, query_vector
    return sum(value * document_vector.get(term, 0.0) for term, value in query_vector.items())


def retrieve(query_text, corpus, top_k=TOP_K):
    """Ordina il corpus per similarita' con la query e restituisce i primi k.

    `corpus` e' una lista di dizionari con almeno `message_id`, `content`,
    `session_order` e `message_order`. Il risultato e' la lista dei documenti
    selezionati, ciascuno con il punteggio di similarita'.

    Se il corpus contiene meno di `top_k` documenti vengono restituiti tutti.
    """
    if not corpus:
        return []

    documents_tokens = [tokenize(document["content"]) for document in corpus]
    idf = _idf(documents_tokens)
    document_vectors = [_vector(tokens, idf, restrict_to_vocabulary=False) for tokens in documents_tokens]
    query_vector = _vector(tokenize(query_text), idf, restrict_to_vocabulary=True)

    scored = []
    for index, document in enumerate(corpus):
        score = _cosine(query_vector, document_vectors[index])
        scored.append((score, document, index))

    # Ordine deterministico: punteggio decrescente, poi ordine di sessione e
    # di messaggio (cioe' l'ordine in cui i messaggi compaiono nello scenario).
    scored.sort(key=lambda item: (-item[0], item[1]["session_order"], item[1]["message_order"]))

    selected = []
    for score, document, _index in scored[:top_k]:
        entry = dict(document)
        entry["score"] = round(score, 6)
        selected.append(entry)
    return selected


# --------------------------------------------------------------------------
# Perimetri e corpus
# --------------------------------------------------------------------------

def build_corpus(scenario, accessible_session_ids):
    """Messaggi indicizzabili dentro il perimetro, in ordine di scenario."""
    allowed = set(accessible_session_ids)
    corpus = []
    for session in scenario["sessions"]:
        if session["session_id"] not in allowed:
            continue
        for message in session["messages"]:
            if message["role"] != INDEXED_ROLE:
                continue
            corpus.append(
                {
                    "message_id": message["message_id"],
                    "session_id": session["session_id"],
                    "session_order": session["order"],
                    "message_order": message["order"],
                    "content": message["content"],
                }
            )
    corpus.sort(key=lambda document: (document["session_order"], document["message_order"]))
    return corpus


def evaluate(scenario, question, condition):
    """Esegue una combinazione scenario x domanda x condizione."""
    accessible_sessions = scenario["conditions"][condition]["accessible_sessions"]
    corpus = build_corpus(scenario, accessible_sessions)
    retrieved = retrieve(question["text"], corpus)

    retrieved_ids = [document["message_id"] for document in retrieved]
    required_ids = list(question["required_evidence_ids"])
    reachable = bool(question["reachability"][condition])

    # EXPERIMENT.md 9.2: il recupero si misura soltanto quando l'evidenza e'
    # raggiungibile. Una domanda non raggiungibile non e' un successo.
    if reachable:
        retrieval_success = all(evidence in retrieved_ids for evidence in required_ids)
    else:
        retrieval_success = None

    return {
        "scenario_id": scenario["scenario_id"],
        "question_id": question["question_id"],
        "condition": condition,
        "reachable": reachable,
        "accessible_message_ids": [document["message_id"] for document in corpus],
        "retrieved_message_ids": retrieved_ids,
        "required_evidence_ids": required_ids,
        "retrieval_success": retrieval_success,
        # Campi descrittivi, utili a leggere la traccia; non sono metriche.
        "question_category": question["category"],
        "accessible_sessions": list(accessible_sessions),
        "retrieval_scores": {d["message_id"]: d["score"] for d in retrieved},
        "top_k": TOP_K,
    }


def run(scenarios):
    rows = []
    for scenario in scenarios:
        for question in scenario["questions"]:
            for condition in CONDITIONS:
                rows.append(evaluate(scenario, question, condition))
    return rows


# --------------------------------------------------------------------------
# Riepilogo e traccia
# --------------------------------------------------------------------------

def summarize(rows):
    """Aggrega per condizione. Il successo si calcola solo sulle raggiungibili."""
    summary = {}
    for condition in CONDITIONS:
        condition_rows = [row for row in rows if row["condition"] == condition]
        reachable_rows = [row for row in condition_rows if row["reachable"]]
        successes = [row for row in reachable_rows if row["retrieval_success"] is True]
        summary[condition] = {
            "runs": len(condition_rows),
            "reachable": len(reachable_rows),
            "success": len(successes),
        }
    return summary


def print_summary(rows):
    summary = summarize(rows)
    print("Riepilogo del retrieval (top-k = %d, solo messaggi dell'utente)" % TOP_K)
    print("-" * 72)
    print("%-6s %-8s %-14s %s" % ("Cond.", "prove", "raggiungibili", "retrieval riuscito"))
    for condition in CONDITIONS:
        entry = summary[condition]
        if entry["reachable"] == 0:
            # EXPERIMENT.md 10.2: senza domande raggiungibili la metrica non
            # e' calcolabile e non va registrata come zero.
            result = "non applicabile (nessuna domanda raggiungibile)"
        else:
            rate = entry["success"] / entry["reachable"]
            result = "%d/%d (%.0f%%)" % (entry["success"], entry["reachable"], 100 * rate)
        print("%-6s %-8d %-14d %s" % (condition, entry["runs"], entry["reachable"], result))
    print("-" * 72)
    print("Esecuzioni totali: %d" % len(rows))
    return summary


def print_traces(rows):
    traced = [row for row in rows if row["question_id"] in TRACE_QUESTION_IDS]
    if not traced:
        return
    print()
    print("Traccia delle domande cross-session")
    print("=" * 72)
    for question_id in TRACE_QUESTION_IDS:
        question_rows = [row for row in traced if row["question_id"] == question_id]
        if not question_rows:
            continue
        text = QUESTION_TEXTS.get(question_id, "")
        print()
        print("%s (%s)" % (question_id, question_rows[0]["question_category"]))
        print("  domanda: %s" % text)
        for row in question_rows:
            if row["retrieval_success"] is None:
                outcome = "non applicabile (domanda non raggiungibile in %s)" % row["condition"]
            elif row["retrieval_success"]:
                outcome = "riuscito (tutte le evidenze obbligatorie recuperate)"
            else:
                mancanti = [e for e in row["required_evidence_ids"] if e not in row["retrieved_message_ids"]]
                outcome = "fallito (evidenze mancanti: %s)" % ", ".join(mancanti)
            print("  - condizione:            %s" % row["condition"])
            print("    messaggi accessibili:  %s" % (", ".join(row["accessible_message_ids"]) or "(nessuno)"))
            print("    messaggi recuperati:   %s" % (", ".join(row["retrieved_message_ids"]) or "(nessuno)"))
            print("    evidenze richieste:    %s" % (", ".join(row["required_evidence_ids"]) or "(nessuna)"))
            print("    raggiungibile:         %s" % ("si" if row["reachable"] else "no"))
            print("    esito retrieval:       %s" % outcome)


# Testi delle domande, riempito da main() per la stampa della traccia.
QUESTION_TEXTS = {}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def load_scenarios(directory=SCENARIO_DIR):
    paths = sorted(Path(directory).glob("scenario_*.json"))
    scenarios = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            scenarios.append(json.load(handle))
    return scenarios


def write_jsonl(rows, path=RESULTS_PATH):
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

    for scenario in scenarios:
        for question in scenario["questions"]:
            QUESTION_TEXTS[question["question_id"]] = question["text"]

    rows = run(scenarios)
    path = write_jsonl(rows)

    print_summary(rows)
    print_traces(rows)
    print()
    print("Risultati scritti in %s (%d righe)." % (path.relative_to(REPO_ROOT), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
