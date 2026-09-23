#!/usr/bin/env python3
"""Controlli offline di RQ3 / SC07, prima di qualsiasi chiamata al modello.

Verifica hash, conteggi, unicita', split disgiunti, campi obbligatori, ordine
interlacciato, oracle, retrieval, assenza di oracle e provenienza nei prompt,
identita' degli input fra le due condizioni salvo il corpus accessibile, e che
nessun file versionato delle RQ precedenti risulti modificato.

Nessuna rete, nessun modello. Esce con codice 0 soltanto se tutti i controlli
passano. Con `--json` stampa l'esito completo in JSON.

Uso:
    python3 scripts/rq3/validate_rq3_sc07_inputs.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402
import select_rq3_sc07_advisories as selector  # noqa: E402
import run_rq3_sc07_retrieval as retrieval_step  # noqa: E402
import build_rq3_sc07_requests as request_builder  # noqa: E402

# Percorsi prodotti da SC07: le uniche modifiche ammesse nel repository.
SC07_PATH_MARKERS = ("rq3_sc07", "sc07_design_v1", "rq3/sc07", "github_advisory_database",
                     "RQ3_SC07", "test_rq3_sc07")


class Checks:
    def __init__(self):
        self.results = []

    def add(self, name, ok, detail=""):
        self.results.append({"check": name, "ok": bool(ok), "detail": detail})

    @property
    def ok(self):
        return all(r["ok"] for r in self.results)


def _dupes(values):
    return sorted(v for v, n in Counter(values).items() if n > 1)


def check_responses(config, split, repo_root=common.REPO_ROOT):
    """Coerenza del riuso nelle risposte salvate; `None` se non ce ne sono.

    Ogni cella riusata deve puntare a una chiamata reale conclusa con stesso
    prompt, stessa configurazione del modello e stessa risposta, come previsto
    dal piano; nessuna cella prevista come riuso deve avere una chiamata reale.
    """
    path = common.results_dir(config, split, repo_root) / "raw_responses.jsonl"
    if not path.exists():
        return None
    rows = common.read_jsonl(path)
    plan = {p["request_id"]: p for p in common.read_jsonl(common.call_plan_path(config, split, repo_root))}
    by_cell = {}
    for row in rows:
        by_cell[row["cell_id"]] = row
    ok_calls = {cid: r for cid, r in by_cell.items()
                if r.get("status") == "ok" and r.get("generation_kind") == "model_call"}
    problems = []
    for row in rows:
        entry = plan.get(row["request_id"])
        if entry is None:
            problems.append(f"{row['cell_id']}: richiesta non prevista")
            continue
        if row.get("generation_kind") != entry["generation_kind"]:
            problems.append(f"{row['cell_id']}: generation_kind {row.get('generation_kind')} "
                            f"invece di {entry['generation_kind']}")
        if row.get("model_config_sha256") != entry["model_config_sha256"] or row.get("prompt_sha256") != entry["prompt_sha256"]:
            problems.append(f"{row['cell_id']}: prompt o configurazione diversi dal piano")
        if row.get("generation_kind") == "reused_identical_prompt":
            if row.get("model_call") is not False:
                problems.append(f"{row['cell_id']}: riuso registrato come chiamata")
            source = ok_calls.get(row.get("reused_from_cell_id"))
            if source is None:
                problems.append(f"{row['cell_id']}: sorgente del riuso assente o non conclusa")
                continue
            if source["request_id"] != entry["reused_from_request_id"]:
                problems.append(f"{row['cell_id']}: sorgente diversa dal piano")
            same = (source["prompt_sha256"] == row["prompt_sha256"]
                    and source["model_config_sha256"] == row["model_config_sha256"]
                    and source["cli_input_sha256"] == row["cli_input_sha256"]
                    and source["response_text"] == row["response_text"]
                    and source["model_used"] == row["model_used"])
            if not same:
                problems.append(f"{row['cell_id']}: prompt, modello, parametri o risposta diversi dalla sorgente")
    planned_calls = sum(1 for p in plan.values() if p["generation_kind"] == "model_call")
    if len(ok_calls) > planned_calls:
        problems.append(f"chiamate reali concluse {len(ok_calls)} > previste {planned_calls}")
    return problems


def validate(config, repo_root=common.REPO_ROOT, config_path=common.CONFIG_PATH, check_git=True):
    c = Checks()
    design = common.design_dir(config, repo_root)
    sel_cfg = config["selection"]
    expected_counts = config["counts"]

    # 1. Sorgente ---------------------------------------------------------
    try:
        manifest = common.verify_snapshot(config, repo_root)
        c.add("source.snapshot_sha256", True, manifest["snapshot"]["sha256"])
    except Exception as error:  # noqa: BLE001
        c.add("source.snapshot_sha256", False, str(error))
        return c
    required = ["repository_url", "commit", "commit_date", "acquired_at", "subtree_git_tree"]
    missing = [k for k in required if not manifest.get(k)]
    missing += [f"license.{k}" for k in ("spdx", "sha256", "filename") if not manifest["license"].get(k)]
    c.add("source.manifest_complete", not missing, f"mancanti: {missing}" if missing else
          f"{manifest['repository_url']}@{manifest['commit'][:12]} ({manifest['commit_date']}), "
          f"licenza {manifest['license']['spdx']}")
    c.add("source.license_matches_config", manifest["license"]["spdx"] == config["source"]["license_spdx"],
          manifest["license"]["spdx"])

    # 2. Audit e selezione -------------------------------------------------
    candidates = common.read_jsonl(design / "candidates.jsonl")
    exclusions = common.read_jsonl(design / "exclusions.jsonl")
    selection = common.read_jsonl(design / "selection.jsonl")
    audit = common.read_json(design / "eligibility_audit.json")
    total = len(candidates) + len(exclusions)
    c.add("audit.covers_snapshot", total == manifest["snapshot"]["advisory_json_files"],
          f"{total} = {manifest['snapshot']['advisory_json_files']}")
    c.add("audit.criteria_known",
          set(r["criterion"] for r in exclusions) <= set(config["eligibility"]["criteria_order"]),
          "criteri di esclusione tutti dichiarati")
    c.add("audit.summary_consistent", audit["eligible"] == len(candidates) and audit["excluded"] == len(exclusions),
          f"{audit['eligible']} ammissibili, {audit['excluded']} esclusi")
    c.add("audit.no_candidate_excluded",
          not ({r["ghsa_id"] for r in candidates} & {r["ghsa_id"] for r in exclusions}), "")

    recomputed = common.select_episodes(candidates, config)
    c.add("selection.reproducible", recomputed == selection, "selezione ricalcolata identica")
    cand_ids = {r["ghsa_id"]: r for r in candidates}
    c.add("selection.all_eligible", all(r["ghsa_id"] in cand_ids for r in selection), "")
    c.add("selection.unique_ghsa", not _dupes([r["ghsa_id"] for r in selection]),
          f"{len({r['ghsa_id'] for r in selection})} GHSA distinti")
    for split in common.SPLITS:
        rows = [r for r in selection if r["split"] == split]
        episodes = {r["episode_id"] for r in rows}
        c.add(f"selection.{split}.counts",
              len(rows) == sel_cfg[split]["advisory_count"] and len(episodes) == sel_cfg[split]["episode_count"],
              f"{len(rows)} advisory, {len(episodes)} episodi")
    per_eco = Counter(
        (r["episode_id"], r["ecosystem"]) for r in selection if r["split"] == "evaluation")
    eco_episodes = Counter(eco for (_, eco) in per_eco)
    c.add("selection.evaluation.per_ecosystem",
          all(eco_episodes[e] == sel_cfg["evaluation"]["episodes_per_ecosystem"]
              for e in config["eligibility"]["ecosystems"]),
          dict(eco_episodes))
    ep_ok = True
    for ep_id in {r["episode_id"] for r in selection}:
        rows = [r for r in selection if r["episode_id"] == ep_id]
        if (len(rows) != 3 or len({r["ecosystem"] for r in rows}) != 1
                or len({r["package"].casefold() for r in rows}) != 3
                or sorted(r["activity"] for r in rows) != ["fix", "impact", "triage"]):
            ep_ok = False
    c.add("selection.episode_composition", ep_ok, "3 advisory, stesso ecosistema, pacchetti diversi, 3 attivita'")

    # 3. Conversazioni, domande, oracle -----------------------------------
    episodes = common.read_jsonl(design / "episodes.jsonl")
    questions = common.read_jsonl(design / "questions.jsonl")
    provenance = common.read_jsonl(design / "message_provenance.jsonl")
    oracle = {s: common.load_oracle(config, s, repo_root) for s in common.SPLITS}
    all_oracle = oracle["development"] + oracle["evaluation"]
    order = [tuple(x) for x in config["conversation"]["interleaving_order"]]

    c.add("episodes.count", len(episodes) == sum(expected_counts[s]["episodes"] for s in common.SPLITS),
          f"{len(episodes)} episodi")
    structure_ok, leaks = True, []
    for episode in episodes:
        messages = episode["messages"]
        if len(messages) != 6 or [(m["activity"], m["activity_turn"]) for m in messages] != order:
            structure_ok = False
        if [m["order"] for m in messages] != list(range(1, 7)) or any(m["role"] != "user" for m in messages):
            structure_ok = False
        for m in messages:
            found = common.prompt_leaks(m["content"])
            if found:
                leaks.append((m["message_id"], found))
        if set(episode) != {"episode_id", "split", "ecosystem", "messages"}:
            structure_ok = False
    c.add("episodes.interleaving_order", structure_ok,
          "6 messaggi utente: triage-1, impatto-1, correzione-1, triage-2, impatto-2, correzione-2")
    c.add("episodes.no_source_in_conversations", not leaks, str(leaks[:3]))
    message_ids = [m["message_id"] for e in episodes for m in e["messages"]]
    c.add("episodes.unique_message_ids", not _dupes(message_ids), f"{len(message_ids)} messaggi")

    by_ep_q = Counter(q["episode_id"] for q in questions)
    c.add("questions.six_per_episode", all(n == 6 for n in by_ep_q.values()) and len(by_ep_q) == len(episodes),
          f"{len(questions)} domande")
    c.add("questions.unique_ids", not _dupes([q["question_id"] for q in questions]), "")
    c.add("questions.no_oracle_fields", all(not (set(q) & common.ORACLE_KEYS) for q in questions), "")
    c.add("oracle.one_row_per_question",
          sorted(o["question_id"] for o in all_oracle) == sorted(q["question_id"] for q in questions), "")

    contents = {m["message_id"]: m for e in episodes for m in e["messages"]}
    episode_msgs = {e["episode_id"]: e["messages"] for e in episodes}
    unique_ok, evidence_ok, question_leak, prov_ok = True, True, [], True
    distractor_overlap = 0
    for row in all_oracle:
        value = row["expected_value"]
        target = [m for m in episode_msgs[row["episode_id"]] if m["activity"] == row["activity"]]
        containing = [m["message_id"] for m in target if value in m["content"]]
        if containing != [row["evidence_message_id"]]:
            unique_ok = False
        evidence = contents[row["evidence_message_id"]]
        if evidence["activity"] != row["activity"]:
            evidence_ok = False
        others = [m for m in episode_msgs[row["episode_id"]] if m["activity"] != row["activity"]]
        distractor_overlap += any(value in m["content"] for m in others)
        q_text = next(q["text"] for q in questions if q["question_id"] == row["question_id"])
        if value in q_text:
            question_leak.append(row["question_id"])
        p = row["provenance"]
        if not (p.get("ghsa_id") and p.get("source_path") and p.get("source_file_sha256") and p.get("osv_fields")):
            prov_ok = False
        if value != unicodedata.normalize("NFC", value).strip():
            unique_ok = False
    c.add("oracle.value_in_exactly_one_target_message", unique_ok, "")
    c.add("oracle.evidence_in_target_activity", evidence_ok, "")
    c.add("oracle.provenance_complete", prov_ok, "GHSA ID, file, SHA-256, campi OSV")
    c.add("questions.do_not_contain_expected_value", not question_leak, str(question_leak[:5]))
    c.add("diagnostic.expected_value_substring_of_distractor", True,
          f"{distractor_overlap} valori attesi compaiono anche in un messaggio di un'altra attivita' (informativo)")
    c.add("provenance.one_row_per_message",
          sorted(p["message_id"] for p in provenance) == sorted(message_ids), "")

    # 4. Split disgiunti ----------------------------------------------------
    split_sets = {}
    for split in common.SPLITS:
        split_sets[split] = {
            "episodes": {e["episode_id"] for e in episodes if e["split"] == split},
            "questions": {q["question_id"] for q in questions if q["split"] == split},
            "messages": {m["message_id"] for e in episodes if e["split"] == split for m in e["messages"]},
            "ghsa": {r["ghsa_id"] for r in selection if r["split"] == split},
        }
    disjoint = all(not (split_sets["development"][k] & split_sets["evaluation"][k]) for k in split_sets["development"])
    c.add("splits.disjoint", disjoint, "episodi, domande, messaggi e GHSA ID")

    # 5. Retrieval ------------------------------------------------------------
    top_k = config["retrieval"]["top_k"]
    for split in common.SPLITS:
        rows = common.read_jsonl(common.results_dir(config, split, repo_root) / "retrieval.jsonl")
        split_q = [q for q in questions if q["split"] == split]
        c.add(f"retrieval.{split}.rows", len(rows) == 2 * len(split_q), f"{len(rows)} righe")
        corpus_ok, topk_ok = True, True
        for row in rows:
            ep_msgs = episode_msgs[row["episode_id"]]
            target = [m["message_id"] for m in ep_msgs if m["activity"] == row["activity"]]
            if row["condition"] == "separated":
                corpus_ok &= row["accessible_message_ids"] == target
            else:
                corpus_ok &= row["accessible_message_ids"] == [m["message_id"] for m in ep_msgs]
                corpus_ok &= set(target) <= set(row["accessible_message_ids"])
            topk_ok &= row["top_k"] == top_k and len(row["retrieved_message_ids"]) == min(top_k, len(row["accessible_message_ids"]))
            topk_ok &= set(row["retrieved_message_ids"]) <= set(row["accessible_message_ids"])
            scores = [s["score"] for s in row["corpus_scores"]]
            topk_ok &= scores == sorted(scores, reverse=True)
        c.add(f"retrieval.{split}.corpus_per_condition", corpus_ok,
              "separata = 2 messaggi bersaglio; condivisa = gli stessi 2 + 4 distrattori")
        c.add(f"retrieval.{split}.top_k", topk_ok, f"top_k = {top_k}, punteggi decrescenti")
        common.forbid_oracle()
        try:
            recomputed = retrieval_step.rank_all(
                config, [e for e in episodes if e["split"] == split], split_q)
            c.add(f"retrieval.{split}.no_oracle_and_deterministic",
                  [{k: r[k] for k in x} for r, x in zip(rows, recomputed)] == recomputed,
                  "ranking ricalcolato con oracle vietato: identico")
        except common.OracleAccessError as error:
            c.add(f"retrieval.{split}.no_oracle_and_deterministic", False, str(error))
        finally:
            common.allow_oracle()

    # 6. Richieste ------------------------------------------------------------
    for split in common.SPLITS:
        requests = common.read_jsonl(common.requests_path(config, split, repo_root))
        rows = common.read_jsonl(common.results_dir(config, split, repo_root) / "retrieval.jsonl")
        expected_n = expected_counts[split]["requests"]
        c.add(f"requests.{split}.count", len(requests) == expected_n, f"{len(requests)} / {expected_n}")
        c.add(f"requests.{split}.unique_ids", not _dupes([r["request_id"] for r in requests]), "")
        c.add(f"requests.{split}.no_oracle_keys", all(not (set(r) & common.ORACLE_KEYS) for r in requests), "")
        rebuilt = request_builder.build_requests(
            config, [e for e in episodes if e["split"] == split],
            [q for q in questions if q["split"] == split], rows)
        c.add(f"requests.{split}.match_saved_retrieval", rebuilt == requests,
              "contesto = messaggi recuperati salvati, nello stesso ordine")
        leak_rows = [(r["request_id"], common.prompt_leaks(r["system"] + "\n" + r["user"]))
                     for r in requests if common.prompt_leaks(r["system"] + "\n" + r["user"])]
        c.add(f"requests.{split}.prompt_without_source", not leak_rows, str(leak_rows[:3]))
        split_oracle = {o["question_id"]: o for o in oracle[split]}
        injected = []
        for r in requests:
            value = split_oracle[r["question_id"]]["expected_value"]
            outside_context = r["system"] + r["question"]
            if value in outside_context:
                injected.append(r["request_id"])
            if r["user"] != config["prompt"]["user_template"].format(context=r["context"], question=r["question"]):
                injected.append(r["request_id"])
        c.add(f"requests.{split}.expected_value_only_via_retrieved_messages", not injected, str(injected[:3]))
        by_q = {}
        for r in requests:
            by_q.setdefault(r["question_id"], {})[r["condition"]] = r
        paired_ok, identical_ctx = True, 0
        invariant = ("config_id", "split", "question_id", "episode_id", "question_type", "activity",
                     "question", "system")
        for qid, pair in by_q.items():
            if set(pair) != set(common.CONDITIONS):
                paired_ok = False
                continue
            a, b = pair["separated"], pair["shared_interleaved"]
            paired_ok &= all(a[k] == b[k] for k in invariant)
            differing = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
            paired_ok &= differing <= {"request_id", "condition", "context_message_ids", "context", "user", "prompt_sha256"}
            identical_ctx += a["context"] == b["context"]
        c.add(f"requests.{split}.conditions_differ_only_in_context", paired_ok,
              f"{len(by_q)} coppie; contesto identico nelle due condizioni in {identical_ctx} coppie")

    # 6b. Piano delle chiamate e riuso dei prompt identici ----------------------
    mc = common.model_config_sha256(config)
    for split in common.SPLITS:
        requests = common.read_jsonl(common.requests_path(config, split, repo_root))
        saved = common.read_jsonl(common.call_plan_path(config, split, repo_root))
        try:
            plan = common.plan_calls(config, requests)
            c.add(f"calls.{split}.plan_reproducible", plan == saved, "piano ricalcolato dalle sole richieste")
        except ValueError as error:
            c.add(f"calls.{split}.plan_reproducible", False, str(error))
            continue
        calls = sum(1 for p in saved if p["generation_kind"] == "model_call")
        expected = expected_counts[split]
        c.add(f"calls.{split}.counts",
              len(saved) == expected["cells"] and calls == expected["model_calls"]
              and len(saved) - calls == expected["reused_cells"],
              f"{len(saved)} celle, {calls} chiamate reali, {len(saved) - calls} riusi "
              f"(attesi {expected['cells']}/{expected['model_calls']}/{expected['reused_cells']})")
        c.add(f"calls.{split}.unique_prompts_equal_model_calls",
              calls == len({r["prompt_sha256"] for r in requests}), "una chiamata per prompt distinto")
        by_id = {r["request_id"]: r for r in requests}
        plan_by_id = {p["request_id"]: p for p in saved}
        reuse_ok = True
        for p in saved:
            reuse_ok &= p["model_config_sha256"] == mc
            if p["generation_kind"] == "reused_identical_prompt":
                src = by_id[p["reused_from_request_id"]]
                own = by_id[p["request_id"]]
                reuse_ok &= plan_by_id[src["request_id"]]["generation_kind"] == "model_call"
                reuse_ok &= (src["system"], src["user"], src["prompt_sha256"]) == (
                    own["system"], own["user"], own["prompt_sha256"])
                reuse_ok &= src["question_id"] == own["question_id"]
                reuse_ok &= plan_by_id[src["request_id"]]["model_config_sha256"] == p["model_config_sha256"]
            else:
                reuse_ok &= p["reused_from_request_id"] is None
        c.add(f"calls.{split}.reuse_only_identical", reuse_ok,
              "riuso solo con system, user, prompt_sha256 e configurazione del modello identici")
        response_problems = check_responses(config, split, repo_root)
        if response_problems is None:
            c.add(f"responses.{split}.reuse_consistent", True, "nessuna risposta ancora salvata")
        else:
            c.add(f"responses.{split}.reuse_consistent", not response_problems, str(response_problems[:3]))

    # 7. Manifest di costruzione e configurazione -------------------------------
    build = common.read_json(design / "build_manifest.json")
    c.add("build.config_sha256", build["config_sha256"] == common.sha256_file(config_path), "")
    stale = [p for p, h in {**build["artifacts_sha256"], **build["retrieval_sha256"]}.items()
             if common.sha256_file(Path(repo_root) / p) != h]
    c.add("build.artifacts_sha256", not stale, f"diversi: {stale}" if stale else "tutti gli artefatti coincidono")
    model = config["model"]
    c.add("config.model_display_name", model["display_name"] == "Claude Sonnet 5 Chat", model["display_name"])
    command = common.cli_command(config)
    c.add("config.model_channel",
          model["model_id"] == "claude-sonnet-5" and model["access_channel"] == "Claude Code CLI"
          and model["fallback_model"] is None and "--fallback-model" not in command,
          f"{model['model_id']} via {model['access_channel']}, nessun fallback")
    c.add("config.cli_command",
          command[:2] == ["claude", "--print"] and command[command.index("--model") + 1] == "claude-sonnet-5"
          and command[command.index("--effort") + 1] == "medium" and command[command.index("--tools") + 1] == ""
          and "--no-session-persistence" in command,
          " ".join(repr(x) if x == "" else x for x in command))
    c.add("build.model_config_sha256", build.get("model_config_sha256") == mc, mc)
    c.add("config.one_generation_per_cell", config["generation"]["repetitions_per_cell"] == 1, "")
    c.add("config.bootstrap", config["evaluation"]["paired_comparison"]["bootstrap_repetitions"] == 10000, "")

    # 8. RQ precedenti non modificate -----------------------------------------
    if check_git:
        try:
            status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                                    cwd=repo_root, capture_output=True, text=True, check=True).stdout
            touched = [line[3:] for line in status.splitlines()
                       if not any(marker in line for marker in SC07_PATH_MARKERS)]
            c.add("repository.previous_rq_untouched", not touched,
                  f"file versionati modificati: {touched}" if touched else "nessun file versionato fuori da SC07 modificato")
        except (OSError, subprocess.CalledProcessError) as error:
            c.add("repository.previous_rq_untouched", False, f"git non disponibile: {error}")

    # Gate informativi (non bloccano la validazione offline, bloccano il runner)
    gates = {
        "model.model_id": model.get("model_id"),
        "model.access_channel": model.get("access_channel"),
        "model.registration_confirmed": model.get("registration_confirmed"),
        "generation.parameters_confirmed": config["generation"].get("parameters_confirmed"),
    }
    c.gates = gates
    return c


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    config = common.load_config()
    checks = validate(config)
    if args.json:
        print(json.dumps({"ok": checks.ok, "checks": checks.results,
                          "gates": getattr(checks, "gates", {})}, ensure_ascii=False, indent=2))
    else:
        for r in checks.results:
            print(f"[{'OK ' if r['ok'] else 'NO '}] {r['check']}" + (f" — {r['detail']}" if r["detail"] else ""))
        passed = sum(r["ok"] for r in checks.results)
        print(f"\n{passed}/{len(checks.results)} controlli superati.")
        gates = getattr(checks, "gates", {})
        if gates:
            print("\nGate prima delle chiamate reali (bloccano il runner, non la validazione):")
            for key, value in gates.items():
                print(f"  {key}: {value}")
    return 0 if checks.ok else 1


if __name__ == "__main__":
    sys.exit(main())
