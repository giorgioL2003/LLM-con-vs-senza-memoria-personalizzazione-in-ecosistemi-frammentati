#!/usr/bin/env python3
"""Retrieval Turn-level RAG di RQ4 / SC05, nelle due condizioni.

Fase 1 — ranking (oracle vietato). Per ogni domanda e condizione:
  - corpus accessibile: `separated` = messaggi utente di S6-S9;
    `shared` = messaggi utente di S1-S9;
  - ranking TF-IDF e selezione entro 200 token con le funzioni di RQ2
    (`rank_items`, `select_within_budget`), messaggi con punteggio nullo
    esclusi, nessun troncamento;
  - si salvano corpus, ranking completo, punteggi, token, messaggi
    selezionati e motivo dell'arresto in `retrieval.jsonl`, che non contiene
    nulla dell'oracle.

Fase 2 — copertura (dopo il ranking). Si legge l'oracle e si scrive, in un
file separato `retrieval_coverage.jsonl`, per ogni fatto obbligatorio se
l'evidenza e' raggiungibile nel corpus e se e' nel contesto recuperato, con
l'attesa derivata (`answered`/`insufficient`). La copertura e' per
provenienza: non prova che il contenuto sia utilizzabile.

Uso:
    python3 scripts/rq4/run_rq4_retrieval.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq4_common as common  # noqa: E402



def rank_all(config, messages, questions):
    """Fase 1: nessun dato dell'oracle."""
    items = common.message_items(config, messages)
    rows = []
    for question in sorted(questions, key=lambda q: q["question_id"]):
        for condition in config["conditions"]["order"]:
            corpus = common.accessible_items(config, items, condition)
            ranked, selection = common.retrieve(config, question["text"], corpus)
            rows.append({
                "question_id": question["question_id"],
                "condition": condition,
                "query": question["text"],
                "accessible_sessions": list(config["conditions"][condition]["accessible_sessions"]),
                "accessible_message_ids": [item["item_id"] for item in corpus],
                "ranking": [
                    {"message_id": e["item_id"], "session_order": e["session_order"], "rank": e["rank"],
                     "score": e["score"], "tokens": e["tokens"], "content_tokens": e["content_tokens"],
                     "overhead_tokens": e["overhead_tokens"]}
                    for e in ranked
                ],
                "selected_message_ids": [e["item_id"] for e in selection["selected"]],
                "selected_renders": [e["render"] for e in selection["selected"]],
                "context_tokens": selection["context_tokens"],
                "context_content_tokens": selection["content_tokens"],
                "context_overhead_tokens": selection["overhead_tokens"],
                "budget_tokens": selection["budget_tokens"],
                "stopped_by": selection["stopped_by"],
                "budget_exceeded_by_first_item": selection["budget_exceeded_by_first_item"],
            })
    return rows


def coverage(config, rows, oracle_rows):
    """Fase 2: raggiungibilita' e copertura per fatto, dopo il ranking."""
    oracle = {o["question_id"]: o for o in oracle_rows}
    result = []
    for row in rows:
        o = oracle[row["question_id"]]
        corpus, context = set(row["accessible_message_ids"]), set(row["selected_message_ids"])
        facts = []
        for fact in o["required_facts"]:
            sources = fact["source_message_ids"]
            facts.append({
                "fact_key": fact["fact_key"],
                "source_message_ids": sources,
                "phases": fact["phases"],
                "in_corpus": all(s in corpus for s in sources),
                "in_context": all(s in context for s in sources),
            })
        reachable = sum(f["in_corpus"] for f in facts)
        retrieved = sum(f["in_context"] for f in facts)
        result.append({
            "question_id": row["question_id"],
            "condition": row["condition"],
            "group": o["group"],
            "required_evidence_ids": o["required_evidence_ids"],
            "facts": facts,
            "facts_total": len(facts),
            "facts_in_corpus": reachable,
            "facts_in_context": retrieved,
            "evidence_in_corpus": {f["fact_key"]: f["in_corpus"] for f in facts},
            "evidence_in_context": {f["fact_key"]: f["in_context"] for f in facts},
            "expected_status_given_corpus": "answered" if facts and reachable == len(facts) else "insufficient",
            "expected_status_given_context": "answered" if facts and retrieved == len(facts) else "insufficient",
            "retrieval_loss": reachable - retrieved,
            "note": "copertura per provenienza: il giudizio sul contenuto resta alla revisione",
        })
    return result


def run(config, out_root=common.REPO_ROOT):
    design = common.design_dir(config, out_root)
    messages = common.read_jsonl(design / "messages.jsonl")
    questions = common.read_jsonl(design / "questions.jsonl")
    common.forbid_oracle()
    try:
        rows = rank_all(config, messages, questions)
    finally:
        common.allow_oracle()
    cov = coverage(config, rows, common.load_oracle(config, out_root))
    common.dump_jsonl(design / "retrieval.jsonl", rows)
    common.dump_jsonl(design / "retrieval_coverage.jsonl", cov)
    return rows, cov


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    rows, cov = run(common.load_config())
    for c in cov:
        row = next(r for r in rows if (r["question_id"], r["condition"]) == (c["question_id"], c["condition"]))
        print(f"{c['question_id']} {c['condition']:<9} [{c['group']}] contesto {row['context_tokens']:>3} token "
              f"{row['selected_message_ids']}  fatti nel corpus {c['facts_in_corpus']}/{c['facts_total']}, "
              f"nel contesto {c['facts_in_context']}/{c['facts_total']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
