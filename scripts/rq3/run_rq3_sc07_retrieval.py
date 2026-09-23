#!/usr/bin/env python3
"""Retrieval Turn-level RAG di RQ3 / SC07, sulle due condizioni.

Fase 1 — ranking (oracle vietato). Per ogni domanda e condizione:
  - corpus accessibile: `separated` = i 2 messaggi utente dell'attivita' della
    domanda; `shared_interleaved` = tutti i 6 messaggi interlacciati;
  - query = testo della domanda;
  - ranking con `retrieve` di `scripts/run_retrieval_pilot.py` (TF-IDF,
    coseno, stessa tokenizzazione, spareggio per ordine dei messaggi);
  - `top_k` dalla configurazione (2).
Durante questa fase `common.forbid_oracle()` e' attivo: qualsiasi lettura
dell'oracle solleva un'eccezione.

Fase 2 — annotazione. Solo dopo il ranking si legge l'oracle per registrare
evidenza obbligatoria, raggiungibilita', successo del retrieval e
contaminazione. Queste annotazioni non cambiano i messaggi recuperati.

Scrive `results/rq3/sc07/v1/<split>/retrieval.jsonl` e `retrieval_summary.json`.

Uso:
    python3 scripts/rq3/run_rq3_sc07_retrieval.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402


def rank_all(config, episodes, questions):
    """Fase 1: ranking senza oracle. Ritorna le righe di retrieval non annotate."""
    top_k = config["retrieval"]["top_k"]
    by_episode = {episode["episode_id"]: episode for episode in episodes}
    activity_of = {
        m["message_id"]: m["activity"] for e in episodes for m in e["messages"]
    }
    rows = []
    for question in sorted(questions, key=lambda q: q["question_id"]):
        episode = by_episode[question["episode_id"]]
        for condition in config["conditions"]["order"]:
            corpus = common.accessible_corpus(episode, question["activity"], condition)
            full, top = common.rank_corpus(question["text"], corpus, top_k)
            rows.append({
                "split": question["split"],
                "condition": condition,
                "question_id": question["question_id"],
                "episode_id": question["episode_id"],
                "question_type": question["question_type"],
                "activity": question["activity"],
                "query": question["text"],
                "top_k": top_k,
                "accessible_message_ids": [d["message_id"] for d in corpus],
                "corpus_scores": [
                    {"rank": rank, "message_id": d["message_id"], "score": d["score"],
                     "activity": activity_of[d["message_id"]]}
                    for rank, d in enumerate(full, 1)
                ],
                "retrieved_message_ids": [d["message_id"] for d in top],
                "retrieved_scores": [d["score"] for d in top],
                "retrieved_activities": [activity_of[d["message_id"]] for d in top],
            })
    return rows


def annotate(rows, oracle_rows):
    """Fase 2: evidenza, raggiungibilita', successo, contaminazione."""
    oracle = {row["question_id"]: row for row in oracle_rows}
    annotated = []
    for row in rows:
        evidence = oracle[row["question_id"]]["evidence_message_id"]
        retrieved = row["retrieved_message_ids"]
        other = sum(1 for a in row["retrieved_activities"] if a != row["activity"])
        annotated.append({
            **row,
            "evidence_message_id": evidence,
            "evidence_reachable": evidence in row["accessible_message_ids"],
            "retrieval_success": evidence in retrieved,
            "evidence_rank": next(
                (s["rank"] for s in row["corpus_scores"] if s["message_id"] == evidence), None),
            "contamination_count": other,
            "contamination_rate": other / len(retrieved) if retrieved else None,
        })
    return annotated


def summarize(rows, config):
    summary = {}
    for condition in config["conditions"]["order"]:
        subset = [r for r in rows if r["condition"] == condition]
        retrieved = sum(len(r["retrieved_message_ids"]) for r in subset)
        summary[condition] = {
            "questions": len(subset),
            "evidence_reachable": sum(r["evidence_reachable"] for r in subset),
            "retrieval_success": sum(r["retrieval_success"] for r in subset),
            "retrieved_messages": retrieved,
            "retrieved_from_other_activities": sum(r["contamination_count"] for r in subset),
            "by_question_type": {
                qt: {
                    "questions": sum(1 for r in subset if r["question_type"] == qt),
                    "retrieval_success": sum(r["retrieval_success"] for r in subset if r["question_type"] == qt),
                    "retrieved_from_other_activities": sum(
                        r["contamination_count"] for r in subset if r["question_type"] == qt),
                }
                for qt in sorted({r["question_type"] for r in subset})
            },
        }
    return summary


def run(config, repo_root=common.REPO_ROOT):
    design = common.design_dir(config, repo_root)
    episodes = common.read_jsonl(design / "episodes.jsonl")
    questions = common.read_jsonl(design / "questions.jsonl")
    outputs = {}
    for split in common.SPLITS:
        split_questions = [q for q in questions if q["split"] == split]
        split_episodes = [e for e in episodes if e["split"] == split]
        common.forbid_oracle()
        try:
            ranked = rank_all(config, split_episodes, split_questions)
        finally:
            common.allow_oracle()
        rows = annotate(ranked, common.load_oracle(config, split, repo_root))
        out = common.results_dir(config, split, repo_root)
        common.dump_jsonl(out / "retrieval.jsonl", rows)
        summary = summarize(rows, config)
        common.dump_json(out / "retrieval_summary.json", {
            "config_id": config["config_id"], "split": split, "top_k": config["retrieval"]["top_k"],
            "by_condition": summary,
        })
        outputs[split] = (rows, summary)
    return outputs


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    config = common.load_config()
    for split, (rows, summary) in run(config).items():
        print(f"{split}: {len(rows)} righe di retrieval")
        for condition, s in summary.items():
            print(f"  {condition:<20} evidenza raggiungibile {s['evidence_reachable']}/{s['questions']}"
                  f"  recuperata {s['retrieval_success']}/{s['questions']}"
                  f"  messaggi di altre attivita' {s['retrieved_from_other_activities']}/{s['retrieved_messages']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
