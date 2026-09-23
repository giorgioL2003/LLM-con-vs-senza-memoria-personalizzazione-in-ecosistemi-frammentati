#!/usr/bin/env python3
"""Audit di ammissibilita' e selezione deterministica di RQ3 / SC07.

1. Verifica snapshot, licenza, manifest e configurazione: se un hash non
   coincide si ferma prima di leggere qualsiasi record.
2. Applica a ogni advisory di `advisories/github-reviewed` i criteri di
   `eligibility.criteria_order`, nell'ordine; per ogni esclusione registra il
   primo criterio non soddisfatto.
3. Ordina i candidati per SHA-256(seed:ecosistema:GHSA ID) e compone gli
   episodi secondo `selection` (prima sviluppo, poi valutazione; pacchetti
   diversi dentro l'episodio; nessun advisory riusato). Se uno strato non basta
   si ferma: i criteri non vengono allentati.

Scrive in `data/rq3/sc07_design_v1/`:
  eligibility_audit.json   conteggi per criterio, cumulativi e per ecosistema
  candidates.jsonl         advisory ammissibili con i campi usati
  exclusions.jsonl         advisory esclusi con criterio e dettaglio
  selection.jsonl          69 advisory assegnati a split, episodio e attivita'

Uso:
    python3 scripts/rq3/select_rq3_sc07_advisories.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402


def audit(config, advisories):
    """`advisories`: iterabile di `(repo_path, bytes)`. Ritorna candidati ed esclusioni."""
    seed = config["selection"]["seed"]
    candidates, exclusions = [], []
    for repo_path, data in advisories:
        advisory = json.loads(data.decode("utf-8"))
        ghsa_id = advisory.get("id")
        criterion, detail = common.check_eligibility(advisory, repo_path, config)
        base = {
            "ghsa_id": ghsa_id,
            "source_path": repo_path,
            "source_file_sha256": common.sha256_bytes(data),
        }
        if criterion:
            exclusions.append({**base, "criterion": criterion, "detail": detail})
            continue
        facts = common.extract_facts(advisory, config)
        candidates.append({
            **base,
            "ecosystem": facts["ecosystem"],
            "package": facts["package"],
            "severity": facts["severity"],
            "introduced": facts["introduced"],
            "fixed_version": facts["fixed_version"],
            "vulnerable_range": facts["vulnerable_range"],
            "aliases": list(advisory.get("aliases") or []),
            "modified": advisory.get("modified"),
            "published": advisory.get("published"),
            "rank_key": common.rank_key(seed, facts["ecosystem"], ghsa_id),
        })
    ids = [row["ghsa_id"] for row in candidates + exclusions]
    if len(ids) != len(set(ids)):
        raise ValueError("GHSA ID duplicati nello snapshot")
    candidates.sort(key=lambda r: (r["ecosystem"], r["rank_key"], r["ghsa_id"]))
    exclusions.sort(key=lambda r: r["source_path"])
    return candidates, exclusions


def audit_summary(config, manifest, candidates, exclusions, selection):
    order = config["eligibility"]["criteria_order"]
    by_criterion = Counter(row["criterion"] for row in exclusions)
    total = len(candidates) + len(exclusions)
    remaining = total
    cumulative = [{"step": "advisory JSON in advisories/github-reviewed", "remaining": total}]
    for criterion in order:
        remaining -= by_criterion.get(criterion, 0)
        cumulative.append({"step": criterion, "excluded": by_criterion.get(criterion, 0), "remaining": remaining})
    per_ecosystem = Counter(row["ecosystem"] for row in candidates)
    unique_packages = {
        eco: len({r["package"].casefold() for r in candidates if r["ecosystem"] == eco})
        for eco in config["eligibility"]["ecosystems"]
    }
    selected = Counter((row["split"], row["ecosystem"]) for row in selection)
    return {
        "config_id": config["config_id"],
        "source_commit": manifest["commit"],
        "snapshot_sha256": manifest["snapshot"]["sha256"],
        "advisories_examined": total,
        "eligible": len(candidates),
        "excluded": len(exclusions),
        "excluded_by_criterion": {c: by_criterion.get(c, 0) for c in order},
        "cumulative": cumulative,
        "eligible_by_ecosystem": {e: per_ecosystem.get(e, 0) for e in config["eligibility"]["ecosystems"]},
        "eligible_unique_packages_by_ecosystem": unique_packages,
        "selected_by_split_and_ecosystem": {
            f"{split}/{eco}": n for (split, eco), n in sorted(selected.items())
        },
        "selected_total": len(selection),
        "seed": config["selection"]["seed"],
        "rank_key": config["selection"]["rank_key"],
        "note": "Esclusioni attribuite al primo criterio non soddisfatto, nell'ordine di criteria_order.",
    }


def run(config, repo_root=common.REPO_ROOT):
    manifest = common.verify_snapshot(config, repo_root)
    advisories = common.iter_snapshot_advisories(common.snapshot_path(config, repo_root), config["source"]["subtree"])
    candidates, exclusions = audit(config, advisories)
    selection = common.select_episodes(candidates, config)
    out = common.design_dir(config, repo_root)
    common.dump_jsonl(out / "candidates.jsonl", candidates)
    common.dump_jsonl(out / "exclusions.jsonl", exclusions)
    common.dump_jsonl(out / "selection.jsonl", selection)
    summary = audit_summary(config, manifest, candidates, exclusions, selection)
    common.dump_json(out / "eligibility_audit.json", summary)
    return summary, selection


def main(argv=None):
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    config = common.load_config()
    try:
        summary, selection = run(config)
    except common.InsufficientStratum as error:
        print(f"ARRESTO: {error}. I criteri non vengono allentati.", file=sys.stderr)
        return 3
    print(f"Advisory esaminati: {summary['advisories_examined']}")
    for step in summary["cumulative"][1:]:
        print(f"  - {step['step']:<48} esclusi {step['excluded']:>6}  restano {step['remaining']:>6}")
    print("Ammissibili per ecosistema:", summary["eligible_by_ecosystem"])
    print(f"Selezionati: {len(selection)}")
    for key, value in summary["selected_by_split_and_ecosystem"].items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
