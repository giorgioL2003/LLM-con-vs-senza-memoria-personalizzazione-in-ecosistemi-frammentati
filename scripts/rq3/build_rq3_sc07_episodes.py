#!/usr/bin/env python3
"""Costruzione di conversazioni, domande e oracle di RQ3 / SC07.

Legge `selection.jsonl`, verifica di nuovo lo snapshot e rilegge dall'archivio
il JSON originale di ogni advisory selezionato (controllando che il suo
SHA-256 coincida con quello registrato in selezione). Da quei campi OSV, e da
nient'altro, costruisce:

  episodes.jsonl                conversazioni: 6 messaggi utente interlacciati
                                per episodio, senza GHSA ID, URL o fonte
  questions.jsonl               6 domande per episodio, senza risposte
  development_oracle.jsonl      valore atteso, messaggio di evidenza e
  evaluation_oracle.jsonl       provenienza campo-per-campo, per domanda
  message_provenance.jsonl      per ogni messaggio: advisory, file, campi OSV

Conversazioni e domande non contengono nulla dell'oracle; l'oracle e la
provenienza stanno in file separati.

Uso:
    python3 scripts/rq3/build_rq3_sc07_episodes.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402


def osv_value(advisory, field_path):
    """Valore di un percorso come `affected[0].ranges[0].events[1].fixed`."""
    value = advisory
    for part in field_path.split("."):
        name, _, index = part.partition("[")
        value = value[name]
        if index:
            value = value[int(index.rstrip("]"))]
    return value


def load_selected_advisories(config, selection, repo_root=common.REPO_ROOT):
    manifest = common.verify_snapshot(config, repo_root)
    wanted = {row["source_path"]: row for row in selection}
    found = {}
    for repo_path, data in common.iter_snapshot_advisories(
            common.snapshot_path(config, repo_root), config["source"]["subtree"]):
        row = wanted.get(repo_path)
        if row is None:
            continue
        if common.sha256_bytes(data) != row["source_file_sha256"]:
            raise ValueError(f"SHA-256 diverso per {repo_path}")
        advisory = json.loads(data.decode("utf-8"))
        if advisory["id"] != row["ghsa_id"]:
            raise ValueError(f"GHSA ID diverso per {repo_path}")
        criterion, detail = common.check_eligibility(advisory, repo_path, config)
        if criterion:
            raise ValueError(f"{row['ghsa_id']} selezionato ma non ammissibile: {criterion} {detail}")
        found[row["ghsa_id"]] = advisory
    missing = {row["ghsa_id"] for row in selection} - set(found)
    if missing:
        raise ValueError(f"advisory selezionati assenti dallo snapshot: {sorted(missing)}")
    return manifest, found


def build(config, selection, advisories, manifest):
    by_episode = {}
    for row in selection:
        by_episode.setdefault(row["episode_id"], []).append(row)

    episodes, questions, provenance = [], [], []
    oracle = {split: [] for split in common.SPLITS}
    templates = config["conversation"]["message_templates"]

    for ep_id in sorted(by_episode):
        rows = sorted(by_episode[ep_id], key=lambda r: r["position"])
        split, ecosystem = rows[0]["split"], rows[0]["ecosystem"]
        by_activity = {row["activity"]: row for row in rows}
        facts = {a: common.extract_facts(advisories[r["ghsa_id"]], config) for a, r in by_activity.items()}
        episode = common.build_episode(config, split, ep_id, ecosystem, facts)
        episodes.append(episode)
        messages = {(m["activity"], m["activity_turn"]): m for m in episode["messages"]}

        for message in episode["messages"]:
            row = by_activity[message["activity"]]
            spec = templates[message["activity"]][str(message["activity_turn"])]
            advisory = advisories[row["ghsa_id"]]
            provenance.append({
                "message_id": message["message_id"],
                "episode_id": ep_id,
                "split": split,
                "activity": message["activity"],
                "activity_turn": message["activity_turn"],
                "fact": spec["fact"],
                "ghsa_id": row["ghsa_id"],
                "source_commit": manifest["commit"],
                "source_path": row["source_path"],
                "source_file_sha256": row["source_file_sha256"],
                "osv_fields": {field: osv_value(advisory, field) for field in spec["osv_fields"]},
            })

        episode_questions = common.build_questions(config, split, ep_id)
        questions.extend(episode_questions)
        items = {item["number"]: item for item in config["questions"]["items"]}
        for question in episode_questions:
            item = items[question["number"]]
            row = by_activity[item["activity"]]
            advisory = advisories[row["ghsa_id"]]
            evidence = messages[(item["activity"], item["evidence_turn"])]
            expected = facts[item["activity"]][item["fact"]]
            spec = templates[item["activity"]][str(item["evidence_turn"])]
            oracle[split].append({
                "question_id": question["question_id"],
                "episode_id": ep_id,
                "split": split,
                "ecosystem": ecosystem,
                "question_type": item["question_type"],
                "activity": item["activity"],
                "fact": item["fact"],
                "expected_value": expected,
                "evidence_message_id": evidence["message_id"],
                "provenance": {
                    "ghsa_id": row["ghsa_id"],
                    "aliases": list(advisory.get("aliases") or []),
                    "source_commit": manifest["commit"],
                    "source_path": row["source_path"],
                    "source_file_sha256": row["source_file_sha256"],
                    "osv_fields": {field: osv_value(advisory, field) for field in spec["osv_fields"]},
                    "rendering": (
                        config["conversation"]["range_rendering"]
                        if item["fact"] == "vulnerable_range" else "verbatim"
                    ),
                },
            })
    return episodes, questions, oracle, provenance


def run(config, repo_root=common.REPO_ROOT):
    out = common.design_dir(config, repo_root)
    selection = common.read_jsonl(out / "selection.jsonl")
    manifest, advisories = load_selected_advisories(config, selection, repo_root)
    episodes, questions, oracle, provenance = build(config, selection, advisories, manifest)
    common.dump_jsonl(out / "episodes.jsonl", episodes)
    common.dump_jsonl(out / "questions.jsonl", questions)
    common.dump_jsonl(out / "message_provenance.jsonl", provenance)
    for split in common.SPLITS:
        common.dump_jsonl(common.oracle_path(config, split, repo_root), oracle[split])
    return episodes, questions, oracle


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    config = common.load_config()
    episodes, questions, oracle = run(config)
    print(f"Episodi: {len(episodes)}  domande: {len(questions)}")
    for split in common.SPLITS:
        n_ep = sum(1 for e in episodes if e["split"] == split)
        print(f"  {split}: {n_ep} episodi, {len(oracle[split])} righe di oracle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
