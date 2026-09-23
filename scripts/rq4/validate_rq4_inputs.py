#!/usr/bin/env python3
"""Controlli offline di RQ4 / SC05 (gate del protocollo prima delle chiamate).

  1. hash immutati di scenario, annotazioni, retriever e configurazione modelli;
  2. 28 celle attese, tutte uniche;
  3. perimetri separato (S6-S9) e condiviso (S1-S9) ricostruiti correttamente;
  4. oracle assente da retrieval e richieste; ranking ricalcolato con oracle vietato;
  5. prompt identici fra modelli nella stessa condizione e domanda;
  6. piano di riuso ricalcolabile da soli prompt e configurazione, conteggi congelati;
  7. digest locali verificati (legge `preflight/model_verification.json`,
     prodotto da `run_rq4_ollama.py --verify-models`; nessuna rete qui);
  8. manifest e artefatti coerenti;
  9. nessun file versionato di RQ1, RQ2, RQ3 o RQ5 modificato.

Con `--phase generation` controlla anche le risposte salvate di smoke e
valutazione: una riga conclusa per cella, modello, digest, prompt e payload
congelati, tipo di generazione del piano, warmup eseguiti.

Con `--phase design` (predefinito) verifica anche che non esista nessun
`raw_responses.jsonl` di RQ4. Esce con 0 soltanto se tutto passa.

Uso:
    python3 scripts/rq4/validate_rq4_inputs.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq4_common as common  # noqa: E402
import build_rq4_design as design_builder  # noqa: E402
import run_rq4_retrieval as retrieval_step  # noqa: E402
import build_rq4_requests as request_builder  # noqa: E402
import run_rq4_ollama as runner  # noqa: E402

RQ4_PATH_MARKERS = ("data/rq4/", "scripts/rq4/", "results/rq4/", "tests/test_rq4")


class Checks:
    def __init__(self):
        self.results = []

    def add(self, name, ok, detail=""):
        self.results.append({"check": name, "ok": bool(ok), "detail": detail})

    @property
    def ok(self):
        return all(r["ok"] for r in self.results)


def check_responses(config, stage, cells, plan, out_root=common.REPO_ROOT):
    """Risposte salvate: una riga conclusa per cella, coerente con richiesta e modello."""
    out_dir = common.stage_dir(config, stage, out_root)
    path = out_dir / "raw_responses.jsonl"
    if not path.exists():
        return [f"{common.rel(path, out_root)} assente"]
    last = runner.last_rows_by_cell(path)
    by_cell = {cell["cell_id"]: cell for cell in cells}
    kinds = {p["cell_id"]: p for p in plan} if plan else {}
    digests = {m["ollama_tag"]: m["ollama_digest"] for m in config["models"]}
    problems = []
    for cid, cell in by_cell.items():
        row = last.get(cid)
        if row is None or row.get("status") != "ok":
            problems.append(f"{cid}: risposta mancante o in errore")
            continue
        if row["model_tag"] != cell["model_tag"] or row["prompt_sha256"] != cell["prompt_sha256"]:
            problems.append(f"{cid}: modello o prompt diversi dalla richiesta")
        if row.get("ollama_digest") != digests[cell["model_tag"]]:
            problems.append(f"{cid}: digest diverso da quello dichiarato")
        if kinds and row.get("generation_kind") != kinds[cid]["generation_kind"]:
            problems.append(f"{cid}: generation_kind diverso dal piano")
        if row.get("generation_kind") == "model_call":
            expected = common.chat_payload(config, cell["model_tag"], cell["system"], cell["user"])
            if row.get("request") != expected:
                problems.append(f"{cid}: payload diverso da quello congelato")
            if row.get("response_model") != cell["model_tag"]:
                problems.append(f"{cid}: modello di risposta {row.get('response_model')}")
    extra = sorted(set(last) - set(by_cell))
    if extra:
        problems.append(f"celle non previste: {extra[:3]}")
    warm = out_dir / "warmup_responses.jsonl"
    if warm.exists():
        per_model = {}
        for row in common.read_jsonl(warm):
            per_model[row["model_tag"]] = per_model.get(row["model_tag"], 0) + 1
        needed = config["runtime"]["warmup_requests_per_model"]
        for tag in {cell["model_tag"] for cell in cells}:
            if per_model.get(tag, 0) < needed:
                problems.append(f"{tag}: warmup {per_model.get(tag, 0)} < {needed}")
    else:
        problems.append("warmup_responses.jsonl assente")
    return problems


def validate(config, out_root=common.REPO_ROOT, config_path=common.CONFIG_PATH, phase="design", check_git=True):
    c = Checks()
    design = common.design_dir(config, out_root)
    counts = config["counts"]

    # 1. Sorgenti -----------------------------------------------------------
    try:
        verified = common.verify_sources(config)
        c.add("sources.sha256", True, ", ".join(f"{k} {v['sha256'][:12]}" for k, v in verified.items()))
    except (OSError, ValueError) as error:
        c.add("sources.sha256", False, str(error))
        return c
    problems = common.models_reference_problems(config)
    c.add("sources.models_match_rq5_config", not problems, "; ".join(problems) or "tag, digest, quantizzazione e runtime")
    rq2_regex = common.read_json(common.REPO_ROOT / config["sources"]["retriever"]["token_counting_config"]["path"])[
        "context_budget"]["token_counting"]["regex"]
    c.add("sources.token_rule_matches_rq2", rq2_regex == config["retrieval"]["token_counting_regex"], rq2_regex)

    # Disegno ricostruito e confrontato con i file salvati
    messages = common.read_jsonl(design / "messages.jsonl")
    questions = common.read_jsonl(design / "questions.jsonl")
    oracle = common.read_jsonl(design / "oracle.jsonl")
    scenario = common.load_scenario(config)
    annotations = common.load_annotations(config)
    c.add("design.messages_reproducible", design_builder.project_messages(config, scenario) == messages,
          f"{len(messages)} messaggi utente")
    c.add("design.oracle_reproducible", design_builder.build_oracle(config, annotations, messages) == oracle, "")
    c.add("design.counts",
          len(messages) == counts["user_messages"] and len({m["session_id"] for m in messages}) == counts["sessions"]
          and len(questions) == counts["questions"],
          f"{len(messages)} messaggi, {len({m['session_id'] for m in messages})} sessioni, {len(questions)} domande")
    c.add("design.user_only", all(m["role"] == "user" for m in messages) and all("-U" in m["message_id"] for m in messages), "")
    handoff_ok = all((m["phase"] == "A") == (m["session_order"] <= config["scenario"]["handoff"]["after_session_order"])
                     for m in messages)
    c.add("design.handoff_5_6", handoff_ok, "fase A = S1-S5, fase B = S6-S9")

    groups_ok, detail = True, []
    for o in oracle:
        orders = [o_ for f in o["required_facts"] for o_ in f["source_session_orders"]]
        if o["group"] == "handoff_dependent":
            ok = any(x <= 5 for x in orders)
        elif o["group"] == "post_handoff_control":
            ok = bool(orders) and all(x >= 6 for x in orders)
        else:
            ok = not orders and o["fact_present_in_corpus"] is False
        groups_ok &= ok
        detail.append(f"{o['question_id']}={o['group']}")
    c.add("design.question_groups_consistent_with_evidence", groups_ok, ", ".join(detail))

    # 3. Perimetri ------------------------------------------------------------
    retrieval = common.read_jsonl(design / "retrieval.jsonl")
    ids_by_session = {}
    for m in messages:
        ids_by_session.setdefault(m["session_order"], []).append(m["message_id"])
    perimeter_ok = True
    for row in retrieval:
        sessions = config["conditions"][row["condition"]]["accessible_sessions"]
        expected = [mid for s in sorted(sessions) for mid in ids_by_session[s]]
        perimeter_ok &= row["accessible_message_ids"] == expected
        perimeter_ok &= set(row["selected_message_ids"]) <= set(row["accessible_message_ids"])
    c.add("retrieval.perimeters", perimeter_ok and len(retrieval) == counts["retrieval_rows"],
          f"{len(retrieval)} righe; separata S6-S9 ({sum(len(ids_by_session[s]) for s in range(6, 10))} messaggi), "
          f"condivisa S1-S9 ({len(messages)})")
    budget_ok = all(r["context_tokens"] <= config["retrieval"]["budget_tokens"] or r["budget_exceeded_by_first_item"]
                    for r in retrieval)
    zero_ok = all(s["score"] > 0 for r in retrieval for s in r["ranking"] if s["message_id"] in r["selected_message_ids"])
    c.add("retrieval.budget_and_zero_scores", budget_ok and zero_ok,
          f"budget {config['retrieval']['budget_tokens']} token; nessun messaggio con punteggio nullo selezionato")

    # 4. Oracle assente -------------------------------------------------------
    common.forbid_oracle()
    try:
        recomputed = retrieval_step.rank_all(config, messages, questions)
        c.add("retrieval.deterministic_without_oracle", recomputed == retrieval, "ranking ricalcolato con oracle vietato")
    except common.OracleAccessError as error:
        c.add("retrieval.deterministic_without_oracle", False, str(error))
    finally:
        common.allow_oracle()
    cells = common.read_jsonl(design / "requests.jsonl")
    leaked_keys = sorted({k for row in retrieval + cells + questions for k in row if k in common.ORACLE_KEYS})
    c.add("oracle.absent_from_retrieval_requests_questions", not leaked_keys, str(leaked_keys))
    texts = []
    for o in oracle:
        texts += [o["expected_answer"]] + o["mandatory_facts"] + [f["text"] for f in o["required_facts"]]
    # Il contesto contiene legittimamente i messaggi recuperati: si controllano
    # le parti del prompt che non vengono dal retrieval (istruzioni e domanda).
    in_prompt = sorted({t[:40] for t in texts for cell in cells if t and t in cell["system"] + cell["question"]})
    c.add("oracle.texts_absent_from_instructions_and_question", not in_prompt, str(in_prompt[:3]))
    template_ok = all(cell["user"] == config["prompt"]["user_template"].format(
        context=cell["context"], question=cell["question"]) for cell in cells)
    c.add("prompts.user_equals_template", template_ok, "user = Contesto (righe recuperate) + Domanda")
    c.add("oracle.no_assistant_messages_in_prompts",
          not any("-A" in mid for cell in cells for mid in cell["context_message_ids"]), "")
    rebuilt = request_builder.build_cells(config, questions, retrieval)
    c.add("requests.match_saved_retrieval", rebuilt == cells, "contesto = righe selezionate dal retrieval")

    # 2. Celle --------------------------------------------------------------
    ids = [cell["cell_id"] for cell in cells]
    combos = Counter((cell["model_tag"], cell["condition"], cell["question_id"]) for cell in cells)
    c.add("cells.count_unique", len(ids) == counts["cells"] == len(set(ids)) and all(v == 1 for v in combos.values())
          and len(combos) == counts["models"] * counts["conditions"] * counts["questions"],
          f"{len(ids)} celle = {counts['models']} modelli x {counts['conditions']} condizioni x {counts['questions']} domande")

    # 5. Prompt identici fra modelli -----------------------------------------
    by_key = {}
    for cell in cells:
        by_key.setdefault((cell["condition"], cell["question_id"]), set()).add((cell["system"], cell["user"]))
    c.add("prompts.identical_across_models", all(len(v) == 1 for v in by_key.values()),
          f"{len(by_key)} coppie domanda/condizione")
    mc_ok = all(cell["model_config_sha256"] == common.model_config_sha256(config, cell["model_tag"]) for cell in cells)
    c.add("prompts.model_config_per_model", mc_ok, "")

    # 6. Piano di riuso ----------------------------------------------------------
    plan = common.read_jsonl(design / "generation_plan.jsonl")
    c.add("plan.reproducible_from_requests", plan == common.plan_generation(config, cells), "")
    calls = [p for p in plan if p["generation_kind"] == "model_call"]
    per_model = {tag: sum(p["model_tag"] == tag for p in calls) for tag in config["runtime"]["model_order"]}
    c.add("plan.frozen_counts",
          len(plan) == counts["cells"] and len(calls) == counts["model_calls"]
          and len(plan) - len(calls) == counts["reused_cells"] and per_model == counts["model_calls_per_model"],
          f"{len(calls)} chiamate reali {per_model}, {len(plan) - len(calls)} riusi")
    by_cell = {cell["cell_id"]: cell for cell in cells}
    reuse_ok = all(
        p["reused_from_cell_id"] is None or (
            by_cell[p["reused_from_cell_id"]]["model_tag"] == p["model_tag"]
            and by_cell[p["reused_from_cell_id"]]["prompt_sha256"] == p["prompt_sha256"]
            and by_cell[p["reused_from_cell_id"]]["model_config_sha256"] == p["model_config_sha256"])
        for p in plan)
    c.add("plan.reuse_only_same_model_identical_input", reuse_ok, "")

    # 7. Digest locali --------------------------------------------------------
    vpath = runner.verification_path(config, out_root)
    if vpath.exists():
        record = common.read_json(vpath)
        digests_ok = record.get("ok") and all(
            record["models"][m["ollama_tag"]].get("model_digest") == m["ollama_digest"] for m in config["models"])
        c.add("models.local_digests_verified", digests_ok,
              f"verificati il {record.get('checked_at')} (Ollama "
              f"{next(iter(record['models'].values())).get('ollama_version')}), generazioni {record.get('generations')}")
    else:
        c.add("models.local_digests_verified", False, "eseguire run_rq4_ollama.py --verify-models")

    # 8. Manifest --------------------------------------------------------------
    build = common.read_json(design / "build_manifest.json")
    c.add("build.config_sha256", build["config_sha256"] == common.sha256_file(config_path), "")
    stale = [p for p, h in build["artifacts_sha256"].items() if common.sha256_file(Path(out_root) / p) != h]
    c.add("build.artifacts_sha256", not stale, f"diversi: {stale}" if stale else "tutti coincidono")
    c.add("build.counts_equal_config", all(build["counts"][k] == counts[k] for k in
                                           ("cells", "model_calls", "reused_cells", "model_calls_per_model")), "")

    # Fase di generazione: coerenza delle risposte salvate --------------------
    if phase == "generation":
        for stage, expected_cells in (("smoke", common.read_jsonl(design / "smoke_requests.jsonl")),
                                      ("evaluation", cells)):
            problems = check_responses(config, stage, expected_cells, plan if stage == "evaluation" else None, out_root)
            c.add(f"responses.{stage}", not problems, "; ".join(problems[:4]) if problems else
                  f"{len(expected_cells)} celle concluse, digest, parametri e prompt coerenti")

    # Fase 1: nessuna risposta -------------------------------------------------
    if phase == "design":
        responses = sorted(common.rel(p, out_root) for p in common.results_dir(config, out_root).rglob("raw_responses.jsonl"))
        c.add("phase1.no_raw_responses", not responses, str(responses) if responses else "nessun raw_responses.jsonl")

    # 9. Altre RQ ---------------------------------------------------------------
    if check_git:
        try:
            status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=common.REPO_ROOT,
                                    capture_output=True, text=True, check=True).stdout
            touched = [line[3:] for line in status.splitlines() if not any(m in line for m in RQ4_PATH_MARKERS)]
            c.add("repository.other_rq_untouched", not touched, str(touched) if touched else "nessun file versionato modificato")
        except (OSError, subprocess.CalledProcessError) as error:
            c.add("repository.other_rq_untouched", False, str(error))
    return c


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phase", choices=("design", "generation"), default="design")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    checks = validate(common.load_config(), phase=args.phase)
    if args.json:
        print(json.dumps({"ok": checks.ok, "checks": checks.results}, ensure_ascii=False, indent=2))
    else:
        for r in checks.results:
            print(f"[{'OK ' if r['ok'] else 'NO '}] {r['check']}" + (f" — {r['detail']}" if r["detail"] else ""))
        print(f"\n{sum(r['ok'] for r in checks.results)}/{len(checks.results)} controlli superati.")
    return 0 if checks.ok else 1


if __name__ == "__main__":
    sys.exit(main())
