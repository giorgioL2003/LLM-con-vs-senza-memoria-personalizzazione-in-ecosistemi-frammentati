#!/usr/bin/env python3
"""Costruzione del disegno di RQ4 / SC05.

Verifica gli SHA-256 delle sorgenti congelate, poi legge in sola lettura
scenario e annotazioni SC05 e scrive in `data/rq4/sc05_handoff_v1/`:

  source_manifest.json   sorgenti, hash, sessioni, passaggio 5/6, regole copiate
  messages.jsonl         i 16 messaggi utente con identificatori originali, fase
                         (A = S1-S5, B = S6-S9) e token secondo la regola di RQ2
  questions.jsonl        le 7 domande (testo e gruppo), senza oracle
  oracle.jsonl           fatti obbligatori, provenienza e attesa per condizione,
                         copiati dall'annotazione senza alterarla

I messaggi dell'assistente non vengono proiettati. Nessuna chiamata ai modelli.

Uso:
    python3 scripts/rq4/build_rq4_design.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq4_common as common  # noqa: E402


def project_messages(config, scenario):
    """Soli messaggi utente, in ordine cronologico, con fase e token."""
    role = config["scenario"]["indexed_role"]
    rows = []
    for session in sorted(scenario["sessions"], key=lambda s: s["order"]):
        for message in sorted(session["messages"], key=lambda m: m["order"]):
            if message["role"] != role:
                continue
            render = common.rq2_common.render_message(message["message_id"], message["content"])
            rows.append({
                "message_id": message["message_id"],
                "session_id": session["session_id"],
                "session_order": session["order"],
                "message_order": message["order"],
                "phase": common.phase_of(config, session["order"]),
                "role": role,
                "content": message["content"],
                "content_tokens": common.rq2_common.count_tokens(message["content"]),
                "render": render,
                "render_tokens": common.rq2_common.count_tokens(render),
            })
    return rows


def build_oracle(config, annotations, messages):
    session_of = {m["message_id"]: m["session_order"] for m in messages}
    rows = []
    for entry in annotations["questions"]:
        qid = entry["question_id"]
        facts = []
        for fact in entry.get("required_facts", []):
            orders = sorted({session_of[mid] for mid in fact["source_message_ids"]})
            facts.append({
                "fact_key": fact["fact_key"],
                "kind": fact["kind"],
                "text": fact["text"],
                "negated": fact.get("negated", False),
                "source_message_ids": list(fact["source_message_ids"]),
                "source_session_orders": orders,
                "phases": sorted({common.phase_of(config, o) for o in orders}),
            })
        per_condition = {}
        for condition in config["conditions"]["order"]:
            sessions = set(config["conditions"][condition]["accessible_sessions"])
            in_corpus = {f["fact_key"]: all(o in sessions for o in f["source_session_orders"]) for f in facts}
            complete = bool(facts) and all(in_corpus.values())
            per_condition[condition] = {
                "evidence_in_corpus": in_corpus,
                "expected_status_given_corpus": "answered" if complete else "insufficient",
            }
        rows.append({
            "question_id": qid,
            "group": common.group_of(config, qid),
            "category": entry["category"],
            "text": entry["text"],
            "expected_answer": entry["expected_answer"],
            "expected_behavior": entry["expected_behavior"],
            "fact_present_in_corpus": entry["fact_present_in_corpus"],
            "mandatory_facts": list(entry["mandatory_facts"]),
            "required_facts": facts,
            "required_evidence_ids": common.rq2_common._derive_evidence_ids(entry.get("required_facts", [])),
            "obsolete_information": list(entry.get("obsolete_information", [])),
            "accepted_equivalents": list(entry.get("accepted_equivalents", [])),
            "required_state_meaning": list(entry.get("required_state_meaning", [])),
            "review_note": entry.get("review_note"),
            "per_condition": per_condition,
            "provenance": {
                "annotation_id": annotations.get("annotation_id"),
                "annotation_path": config["sources"]["annotations"]["path"],
                "annotation_sha256": config["sources"]["annotations"]["sha256"],
                "annotation_status": annotations.get("status"),
            },
        })
    return rows


def run(config, out_root=common.REPO_ROOT):
    verified = common.verify_sources(config)
    problems = common.models_reference_problems(config)
    if problems:
        raise ValueError("; ".join(problems))
    scenario = common.load_scenario(config)
    annotations = common.load_annotations(config)
    session_ids = [s["session_id"] for s in sorted(scenario["sessions"], key=lambda s: s["order"])]
    if session_ids != config["scenario"]["session_ids"]:
        raise ValueError(f"sessioni diverse da quelle dichiarate: {session_ids}")

    messages = project_messages(config, scenario)
    questions = [{"question_id": q["question_id"], "text": q["text"], "group": common.group_of(config, q["question_id"])}
                 for q in annotations["questions"]]
    oracle = build_oracle(config, annotations, messages)

    out = common.design_dir(config, out_root)
    common.dump_jsonl(out / "messages.jsonl", messages)
    common.dump_jsonl(out / "questions.jsonl", questions)
    common.dump_jsonl(out / "oracle.jsonl", oracle)
    common.dump_json(out / "source_manifest.json", {
        "config_id": config["config_id"],
        "sources": verified,
        "read_only": True,
        "scenario_id": scenario["scenario_id"],
        "case_id": config["scenario"]["case_id"],
        "session_ids": session_ids,
        "handoff": config["scenario"]["handoff"],
        "user_messages": len(messages),
        "user_message_ids_by_phase": {
            phase: [m["message_id"] for m in messages if m["phase"] == phase] for phase in ("A", "B")
        },
        "assistant_messages_indexed": 0,
        "annotation": {
            "annotation_id": annotations.get("annotation_id"),
            "status": annotations.get("status"),
            "abstention_rule": annotations.get("abstention_rule"),
            "provenance_warning": annotations.get("provenance_warning"),
        },
        "evaluation_rules": config["evaluation"],
        "models": config["models"],
        "runtime": config["runtime"],
    })
    return messages, questions, oracle


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    messages, questions, oracle = run(common.load_config())
    print(f"Messaggi utente: {len(messages)} (fase A {sum(m['phase'] == 'A' for m in messages)}, "
          f"fase B {sum(m['phase'] == 'B' for m in messages)})")
    for group in common.GROUPS:
        print(f"  {group}: {[q['question_id'] for q in questions if q['group'] == group]}")
    print(f"Righe di oracle: {len(oracle)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
