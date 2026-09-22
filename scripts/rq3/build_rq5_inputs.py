#!/usr/bin/env python3
"""Costruzione offline delle richieste e degli oracle di RQ5 / SC06.

Lo script fa quattro cose, in quest'ordine:

  1. verifica gli SHA-256 delle quattro sorgenti dichiarate nella
     configurazione `data/rq3/config/rq5_sc06_v1.json`;
  2. costruisce i due contesti (`sufficient`, `insufficient`) di ogni domanda
     con la regola esatta della configurazione;
  3. scrive *separati* richieste e oracle, divisi per split;
  4. scrive un manifest con conteggi, hash e scelte di formato.

Le richieste sono indipendenti dal modello: la stessa richiesta viene inviata
a entrambi i tag Ollama, quindi il prompt e il suo hash sono identici per i due
modelli nella stessa domanda e condizione. L'espansione sui modelli avviene nel
runner, non qui.

Le richieste non contengono risposte attese, identificativi VERIS, fonti o
valori usati per riconoscere le confusioni fra casi: i campi vietati sono
elencati in `context_builder.forbidden_prompt_inputs` e il controllo e'
eseguito su ogni prompt prima di scrivere.

Lo script non chiama Ollama e non tocca RQ1 o RQ2.

Uso:
    python3 scripts/rq3/build_rq5_inputs.py
    python3 scripts/rq3/build_rq5_inputs.py --out-dir data/rq3/sc06_rq5_v1
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq5_common as common  # noqa: E402


def _forbidden_strings(case_rows):
    """Stringhe che non possono comparire in un prompt: ID, percorsi, fonti."""
    forbidden = set()
    for row in case_rows:
        for key in ("incident_id", "source_path", "reference"):
            value = row.get(key)
            if value:
                forbidden.add(str(value).strip())
    return forbidden


def _check_prompt(question_id, condition, system, user, forbidden):
    """Nessun identificativo, percorso o fonte nel testo inviato al modello."""
    text = system + "\n" + user
    for needle in forbidden:
        if needle and needle in text:
            raise ValueError(
                f"{question_id}/{condition}: il prompt contiene una stringa vietata "
                f"({needle[:60]!r})"
            )
    for needle in ("http://", "https://", "data/json", "VCDB", "incident_id"):
        if needle in text:
            raise ValueError(
                f"{question_id}/{condition}: il prompt contiene {needle!r}"
            )


def build(config, repo_root=common.REPO_ROOT):
    """Ritorna `(richieste, oracle, statistiche)` per tutti gli split."""
    queries = common.load_queries(config, repo_root)
    oracle_rows = common.load_oracle(config, repo_root)
    case_rows = common.load_case_mapping(config, repo_root)
    episodes = common.load_episodes(config, repo_root)

    oracle_by_question = {row["question_id"]: row for row in oracle_rows}
    if len(oracle_by_question) != len(oracle_rows):
        raise ValueError("oracle_questions.jsonl contiene question_id duplicati")
    cases = common.cases_by_episode(case_rows)
    case_meta = {(row["episode_id"], row["case_alias"]): row for row in case_rows}
    episode_ids = {row["episode_id"] for row in episodes}

    requests, oracle_out = [], []
    stats = Counter()

    for query in queries:
        question_id = query["question_id"]
        episode_id = query["episode_id"]
        question = query["question"]
        if episode_id not in episode_ids:
            raise ValueError(f"{question_id}: episodio sconosciuto {episode_id}")
        split = common.split_of(episode_id, config)

        # Caso bersaglio e campo ricavati dalla domanda, non dall'oracle.
        target_alias, field = common.parse_question(question, config)

        oracle = oracle_by_question.get(question_id)
        if oracle is None:
            raise ValueError(f"{question_id}: manca la riga di oracle")
        if oracle["case_alias"] != target_alias or oracle["field"] != field:
            raise ValueError(
                f"{question_id}: domanda e oracle non concordano su caso o campo"
            )
        if oracle["question"] != question:
            raise ValueError(f"{question_id}: testo della domanda diverso nell'oracle")

        episode_cases = cases.get(episode_id)
        if not episode_cases or len(episode_cases) != 3:
            raise ValueError(f"{episode_id}: attesi tre casi in case_mapping.jsonl")
        target_values = episode_cases[target_alias].get(field, [])
        if list(target_values) != list(oracle["expected_values"]):
            raise ValueError(
                f"{question_id}: i valori del caso bersaglio non coincidono con l'oracle"
            )

        forbidden = _forbidden_strings(
            [case_meta[(episode_id, alias)] for alias in episode_cases]
        )

        for condition in common.CONDITIONS:
            context, blocks = common.build_context(
                config, question_id, target_alias, field, episode_cases, condition
            )
            system, user = common.build_prompt(config, context, question)
            _check_prompt(question_id, condition, system, user, forbidden)
            identifier = common.request_id(split, condition, question_id)
            digest = common.prompt_sha256(system, user)

            requests.append({
                "request_id": identifier,
                "split": split,
                "episode_id": episode_id,
                "question_id": question_id,
                "condition": condition,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "prompt_sha256": digest,
                "context_block_order": [b["case_alias"] for b in blocks],
                "context_block_fields": {b["case_alias"]: b["field"] for b in blocks},
            })

            expected = list(oracle["expected_values"]) if condition == "sufficient" else []
            meta = case_meta[(episode_id, target_alias)]
            oracle_out.append({
                "request_id": identifier,
                "split": split,
                "episode_id": episode_id,
                "question_id": question_id,
                "condition": condition,
                "case_alias": target_alias,
                "family": oracle["family"],
                "field": field,
                "expected_values": expected,
                "expected_values_sufficient": list(oracle["expected_values"]),
                "detectable_cross_case_intrusion_values":
                    list(oracle["detectable_cross_case_intrusion_values"]),
                "other_cases_values_same_field": oracle["other_cases_values_same_field"],
                "evidence_message_id": oracle["evidence_message_id"],
                "incident_id": meta["incident_id"],
                "source_path": meta["source_path"],
                "reference": meta.get("reference"),
                "context_blocks": blocks,
                "context_values": sorted({v for b in blocks for v in b["values"]}),
                "prompt_sha256": digest,
            })
            stats[f"{split}:{condition}"] += 1
        stats[f"{split}:questions"] += 1

    requests.sort(key=lambda row: (row["question_id"], row["condition"] != "sufficient"))
    oracle_out.sort(key=lambda row: (row["question_id"], row["condition"] != "sufficient"))
    return requests, oracle_out, stats


def _counts(config, requests):
    models = [model["ollama_tag"] for model in config["models"]]
    per_split = Counter(row["split"] for row in requests)
    return {
        split: {
            "model_independent_requests": per_split[split],
            "cells_after_model_expansion": per_split[split] * len(models),
            "questions": per_split[split] // len(common.CONDITIONS),
        }
        for split in common.SPLITS
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=str(common.CONFIG_PATH))
    parser.add_argument("--out-dir", default=None,
                        help="predefinita: la directory della versione in configurazione")
    parser.add_argument(
        "--repo-root", default=str(common.REPO_ROOT),
        help="radice da cui risolvere i percorsi delle sorgenti (per i test)",
    )
    args = parser.parse_args(argv)

    config = common.load_config(args.config)
    repo_root = Path(args.repo_root)
    out_dir = Path(args.out_dir) if args.out_dir else common.inputs_dir(config, repo_root)
    verified = common.verify_sources(config, repo_root)
    print("SHA-256 delle sorgenti verificati:")
    for name, info in sorted(verified.items()):
        print(f"  {name:13s} {info['sha256'][:16]}...  {info['path']}")

    requests, oracle_rows, _ = build(config, repo_root)
    for split in common.SPLITS:
        common.dump_jsonl(
            out_dir / f"{split}_requests.jsonl",
            [row for row in requests if row["split"] == split],
        )
        common.dump_jsonl(
            out_dir / f"{split}_oracle.jsonl",
            [row for row in oracle_rows if row["split"] == split],
        )

    counts = _counts(config, requests)
    manifest = {
        "config_id": config["config_id"],
        "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "inputs_built_no_model_calls",
        "model_calls_made": 0,
        "sources_verified": verified,
        "builder_seed": config["context_builder"]["builder_seed"],
        "block_separator": common.BLOCK_SEPARATOR,
        "block_separator_note": (
            "Il separatore fra blocchi non e' fissato dalla configurazione: "
            "si usa una riga vuota, come nel rendering degli episodi."
        ),
        "ordering_rule": config["context_builder"]["ordering_rule"],
        "distractor_rule": config["context_builder"]["distractor_rule"],
        "prompt_sha256_definition": "sha256('SYSTEM\\n' + system + '\\n\\nUSER\\n' + user)",
        "request_id_definition": "split|condition|question_id",
        "cell_id_definition": "split|ollama_tag|condition|question_id",
        "models": [model["ollama_tag"] for model in config["models"]],
        "counts": counts,
        "config_call_counts": config["call_counts"],
        "files": {
            f"{split}_{kind}": f"{split}_{kind}.jsonl"
            for split in common.SPLITS
            for kind in ("requests", "oracle")
        },
        "forbidden_prompt_inputs": config["context_builder"]["forbidden_prompt_inputs"],
    }
    common.dump_json(out_dir / "build_manifest.json", manifest)

    print()
    for split in common.SPLITS:
        info = counts[split]
        print(
            f"{split:12s} domande={info['questions']:5d} "
            f"richieste={info['model_independent_requests']:5d} "
            f"celle={info['cells_after_model_expansion']:5d}"
        )
    print(f"\nScritti in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
