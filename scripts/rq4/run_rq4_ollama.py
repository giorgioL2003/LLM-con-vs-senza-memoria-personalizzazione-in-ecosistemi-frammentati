#!/usr/bin/env python3
"""Runner Ollama di RQ4 / SC05 (modelli B: Gemma 3 4B IT, Llama 3.2 3B Instruct).

Riusa, importandole dal runner RQ5 senza modificarlo, le misure di sicurezza
e tracciabilita': `http_json`, `preflight` (versione di Ollama, tag e digest
locale), `process_snapshot` e `unload`. Il payload e' `rq5_common.chat_payload`.

Modalita':
  --verify-models   solo metadati (`/api/version`, `/api/tags`): verifica tag,
                    digest e quantizzazione dei due modelli, nessuna
                    generazione; scrive `results/rq4/sc05/v1/preflight/
                    model_verification.json`
  --dry-run         nessuna connessione e nessun file: conteggi, piano, gate
                    ed esempi separato/condiviso per Q2, Q4 e Q7
  --stage smoke     una richiesta per modello sulla fixture non SC05
                    (richiede --confirm-smoke)
  --stage evaluation  le 28 celle (richiede --confirm-evaluation e
                    `results/rq4/sc05/v1/evaluation_gate.json`)

Durante l'esecuzione reale: un modello alla volta (`--model`), tre warmup
esclusi dai risultati, temperatura 0, seed 42, num_ctx 4096, num_predict 128,
`--limit` sulle chiamate reali, `--resume`, arresto dopo errori consecutivi.
Le celle con prompt identico dello stesso modello ricevono la stessa risposta
come `reused_identical_prompt` (per i dati congelati: nessuna).

L'oracle non viene mai letto: `forbid_oracle()` e' attivo per tutta
l'esecuzione. Gli output non conformi non vengono corretti ne' rigenerati.

Uso:
    python3 scripts/rq4/run_rq4_ollama.py --verify-models
    python3 scripts/rq4/run_rq4_ollama.py --stage evaluation --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq4_common as common  # noqa: E402
import run_rq5_ollama as rq5_runner  # noqa: E402  (sola lettura)

DRY_RUN_QUESTIONS = ("SC05-Q2", "SC05-Q4", "SC05-Q7")


class GateError(RuntimeError):
    pass


def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def verification_path(config, out_root=common.REPO_ROOT):
    return common.results_dir(config, out_root) / "preflight" / "model_verification.json"


def evaluation_gate_path(config, out_root=common.REPO_ROOT):
    return common.results_dir(config, out_root) / "evaluation_gate.json"


# --------------------------------------------------------------------------
# Verifica dei modelli (solo metadati)
# --------------------------------------------------------------------------

def verify_models(config, transport=rq5_runner.http_json, out_root=common.REPO_ROOT, write=True):
    record = {"checked_at": _now(), "config_id": config["config_id"], "models": {}, "ok": True,
              "generations": 0, "endpoints": ["/api/version", "/api/tags"]}
    for model in config["models"]:
        tag = model["ollama_tag"]
        try:
            checks = rq5_runner.preflight(config, tag, transport=transport)
            ok = (checks["model_digest"] == model["ollama_digest"]
                  and checks.get("quantization") == model["quantization"])
            record["models"][tag] = {**checks, "declared_digest": model["ollama_digest"],
                                     "declared_quantization": model["quantization"], "ok": ok}
        except Exception as error:  # noqa: BLE001 - la verifica fallita va registrata
            record["models"][tag] = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        record["ok"] = record["ok"] and record["models"][tag]["ok"]
    if write:
        common.dump_json(verification_path(config, out_root), record)
    return record


# --------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------

def gate_problems(config, stage, args, out_root=common.REPO_ROOT, config_path=common.CONFIG_PATH):
    problems = []
    if stage == "smoke" and not args.confirm_smoke:
        problems.append("manca --confirm-smoke (smoke test non autorizzato)")
    if stage == "evaluation":
        if not args.confirm_evaluation:
            problems.append("manca --confirm-evaluation (valutazione non autorizzata)")
        gate_path = evaluation_gate_path(config, out_root)
        if not gate_path.exists():
            problems.append(f"file di gate assente: {common.rel(gate_path, out_root)}")
        else:
            gate = common.read_json(gate_path)
            for key in ("approved_by", "approved_at", "config_sha256", "build_manifest_sha256"):
                if not gate.get(key):
                    problems.append(f"evaluation_gate.{key} mancante")
            if gate.get("config_sha256") != common.sha256_file(config_path):
                problems.append("evaluation_gate non riferito all'attuale configurazione")
            manifest = common.design_dir(config, out_root) / "build_manifest.json"
            if gate.get("build_manifest_sha256") != common.sha256_file(manifest):
                problems.append("evaluation_gate non riferito all'attuale build_manifest")
    verification = verification_path(config, out_root)
    if not verification.exists() or not common.read_json(verification).get("ok"):
        problems.append("verifica di tag e digest assente o non superata (--verify-models)")
    if args.model and args.model not in config["runtime"]["model_order"]:
        problems.append(f"modello non previsto: {args.model}")
    return problems


def check_inputs(config, stage, out_root=common.REPO_ROOT):
    """Richieste e piano coincidono con il manifest e sono ricalcolabili."""
    design = common.design_dir(config, out_root)
    build = common.read_json(design / "build_manifest.json")
    names = ("requests.jsonl", "generation_plan.jsonl") if stage == "evaluation" else ("smoke_requests.jsonl",)
    for name in names:
        path = design / name
        if build["artifacts_sha256"].get(common.rel(path, out_root)) != common.sha256_file(path):
            raise GateError(f"{name} diverso dal build_manifest")
    for tag in config["runtime"]["model_order"]:
        if build["model_config_sha256"][tag] != common.model_config_sha256(config, tag):
            raise GateError(f"configurazione di {tag} diversa dal build_manifest")
    if stage == "smoke":
        cells = common.read_jsonl(design / "smoke_requests.jsonl")
        return cells, [{"cell_id": c["cell_id"], "model_tag": c["model_tag"], "generation_kind": "model_call",
                        "reused_from_cell_id": None} for c in cells]
    cells = common.read_jsonl(design / "requests.jsonl")
    plan = common.read_jsonl(design / "generation_plan.jsonl")
    if plan != common.plan_generation(config, cells):
        raise GateError("piano delle generazioni non ricalcolabile dalle richieste")
    return cells, plan


# --------------------------------------------------------------------------
# Celle
# --------------------------------------------------------------------------

def last_rows_by_cell(path):
    if not Path(path).exists():
        return {}
    rows = {}
    for row in common.read_jsonl(path):
        rows[row["cell_id"]] = row
    return rows


def run_model_call(config, cell, transport, run_id, digest, timeout):
    payload = common.chat_payload(config, cell["model_tag"], cell["system"], cell["user"])
    record = {
        "cell_id": cell["cell_id"], "request_id": cell["request_id"], "config_id": config["config_id"],
        "run_id": run_id, "stage": cell["stage"], "model_tag": cell["model_tag"], "ollama_digest": digest,
        "condition": cell.get("condition"), "question_id": cell.get("question_id"),
        "prompt_sha256": cell["prompt_sha256"], "model_config_sha256": cell["model_config_sha256"],
        "generation_kind": "model_call", "model_call": True, "reused_from_cell_id": None,
        "request": payload, "started_at": _now(),
    }
    started = time.monotonic()
    try:
        response = transport(config["runtime"]["endpoint"], payload, timeout=timeout)
    except Exception as error:  # noqa: BLE001 - l'errore va conservato
        record.update({"status": "error", "content": None, "response": None,
                       "error": {"type": type(error).__name__, "message": str(error)}, "ollama_metrics": {}})
    else:
        record.update({
            "status": "ok", "content": (response.get("message") or {}).get("content"),
            "response": response, "error": None, "response_model": response.get("model"),
            "done_reason": response.get("done_reason"),
            "ollama_metrics": {f: response.get(f) for f in config["performance"]["log_ollama_fields"]},
        })
    record["finished_at"] = _now()
    record["wall_seconds"] = round(time.monotonic() - started, 6)
    return record


def reuse_row(cell, source_cell, source_row, run_id):
    if cell["model_tag"] != source_cell["model_tag"]:
        raise ValueError("riuso fra modelli diversi non ammesso")
    if (cell["system"], cell["user"], cell["prompt_sha256"], cell["model_config_sha256"]) != (
            source_cell["system"], source_cell["user"], source_cell["prompt_sha256"], source_cell["model_config_sha256"]):
        raise ValueError(f"riuso rifiutato: input diverso per {cell['cell_id']}")
    if source_row.get("status") != "ok" or source_row.get("generation_kind") != "model_call":
        raise ValueError("riuso ammesso solo da una chiamata reale conclusa")
    return {
        "cell_id": cell["cell_id"], "request_id": cell["request_id"], "run_id": run_id, "stage": cell["stage"],
        "model_tag": cell["model_tag"], "ollama_digest": source_row.get("ollama_digest"),
        "condition": cell["condition"], "question_id": cell["question_id"],
        "prompt_sha256": cell["prompt_sha256"], "model_config_sha256": cell["model_config_sha256"],
        "generation_kind": "reused_identical_prompt", "model_call": False,
        "reused_from_cell_id": source_row["cell_id"], "created_at": _now(), "status": "ok",
        "content": source_row["content"], "response_model": source_row.get("response_model"), "error": None,
    }


def warmup(config, model_tag, transport, timeout, out_path):
    with common.JsonlAppender(out_path) as out:
        for index in range(config["runtime"]["warmup_requests_per_model"]):
            payload = common.chat_payload(config, model_tag, config["prompt"]["system"],
                                          config["runtime"]["warmup_prompt"])
            record = {"warmup": True, "model_tag": model_tag, "index": index + 1, "started_at": _now(),
                      "request": payload}
            try:
                response = transport(config["runtime"]["endpoint"], payload, timeout=timeout)
                record.update({"status": "ok", "content": (response.get("message") or {}).get("content")})
            except Exception as error:  # noqa: BLE001
                record.update({"status": "error", "error": f"{type(error).__name__}: {error}"})
            record["finished_at"] = _now()
            out.write(record)


# --------------------------------------------------------------------------
# Dry-run
# --------------------------------------------------------------------------

def dry_run_report(config, stage, cells, plan, problems, out_root):
    print(f"DRY-RUN — nessuna connessione a Ollama, nessun file scritto. Stage: {stage}")
    calls = [p for p in plan if p["generation_kind"] == "model_call"]
    print(f"Celle: {len(cells)}  chiamate reali previste: {len(calls)}  riusi: {len(plan) - len(calls)}")
    for tag in config["runtime"]["model_order"]:
        model = common.model_entry(config, tag)
        own = [p for p in plan if p["model_tag"] == tag]
        print(f"  {tag:<12} digest {model['ollama_digest'][:12]}…  {model['quantization']}  "
              f"celle {len(own)}, chiamate {sum(p['generation_kind'] == 'model_call' for p in own)}")
    options = config["runtime"]["options"]
    print(f"Runtime: Ollama {config['runtime']['verified_version']}, options {options}, "
          f"warmup {config['runtime']['warmup_requests_per_model']} per modello (esclusi)")
    verification = verification_path(config, out_root)
    if verification.exists():
        record = common.read_json(verification)
        print(f"Verifica modelli: {'OK' if record['ok'] else 'FALLITA'} ({record['checked_at']})")
    print("Gate: " + ("; ".join(problems) if problems else "nessun blocco"))
    if stage != "evaluation":
        for cell in cells:
            print("-" * 78 + f"\n{cell['cell_id']}\n{cell['user']}")
        return
    leaks = sorted({k for c in cells for k in common.ORACLE_KEYS if k in c})
    by_prompt = {}
    for c in cells:
        by_prompt.setdefault((c["condition"], c["question_id"]), set()).add(c["prompt_sha256"])
    same = all(len(v) == 1 for v in by_prompt.values())
    print(f"Chiavi di oracle nelle richieste: {leaks or 'nessuna'}; "
          f"prompt identico fra Gemma e Llama per domanda/condizione: {'sì' if same else 'NO'}")
    print("\nSYSTEM (identico per tutte le celle):\n" + config["prompt"]["system"])
    first_model = config["runtime"]["model_order"][0]
    for qid in DRY_RUN_QUESTIONS:
        for condition in config["conditions"]["order"]:
            cell = next(c for c in cells if c["model_tag"] == first_model
                        and c["question_id"] == qid and c["condition"] == condition)
            kinds = {p["model_tag"]: p["generation_kind"] for p in plan
                     if p["question_id"] == qid and p["condition"] == condition}
            print("\n" + "=" * 78)
            print(f"{qid} — {condition}  (contesto: {', '.join(cell['context_message_ids'])})")
            print(f"prompt_sha256 {cell['prompt_sha256'][:16]}…  generazione: {kinds}")
            print("-" * 78)
            print(cell["user"])


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv=None, transport=None, out_root=common.REPO_ROOT, config_path=common.CONFIG_PATH):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=("smoke", "evaluation"))
    parser.add_argument("--model", help="tag del modello da eseguire (uno alla volta)")
    parser.add_argument("--verify-models", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="numero massimo di chiamate reali")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--confirm-smoke", action="store_true")
    parser.add_argument("--confirm-evaluation", action="store_true")
    parser.add_argument("--max-consecutive-errors", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args(argv)
    common.forbid_oracle()
    try:
        return _run(args, transport, out_root, config_path)
    finally:
        common.allow_oracle()


def _run(args, transport, out_root, config_path):
    config = common.load_config(config_path)
    http = transport or rq5_runner.http_json
    if args.verify_models:
        record = verify_models(config, http, out_root)
        for tag, entry in record["models"].items():
            print(f"{tag}: {'OK' if entry['ok'] else 'NO'} "
                  f"{entry.get('model_digest') or entry.get('error')} {entry.get('quantization', '')} "
                  f"(Ollama {entry.get('ollama_version', '?')})")
        print("Nessuna generazione eseguita.")
        return 0 if record["ok"] else 2
    if not args.stage:
        print("Indica --stage oppure --verify-models.", file=sys.stderr)
        return 2
    stage = args.stage
    cells, plan = check_inputs(config, stage, out_root)
    problems = gate_problems(config, stage, args, out_root, config_path)
    if args.dry_run:
        dry_run_report(config, stage, cells, plan, problems, out_root)
        return 0
    if not args.model:
        problems.append("indica --model: un modello alla volta")
    if problems:
        for problem in problems:
            print(f"BLOCCATO: {problem}", file=sys.stderr)
        return 2

    out_dir = common.stage_dir(config, stage, out_root)
    responses_path = out_dir / "raw_responses.jsonl"
    tag = args.model
    last = last_rows_by_cell(responses_path)
    # Il file e' condiviso dai due modelli: il blocco riguarda solo le righe del
    # modello richiesto, cosi' Llama puo' partire dopo Gemma senza --resume.
    if any(row.get("model_tag") == tag for row in last.values()) and not args.resume:
        print(f"BLOCCATO: {common.rel(responses_path, out_root)} contiene gia' risposte di {tag}; usa --resume.",
              file=sys.stderr)
        return 2

    checks = rq5_runner.preflight(config, tag, transport=http)
    by_id = {c["cell_id"]: c for c in cells}
    own_plan = [p for p in plan if p["model_tag"] == tag]
    done = {cid for cid, row in last.items() if row.get("status") == "ok"}
    allowed = [p["cell_id"] for p in own_plan if p["generation_kind"] == "model_call" and p["cell_id"] not in done]
    if args.limit is not None:
        allowed = allowed[: args.limit]
    allowed = set(allowed)

    run_id = uuid.uuid4().hex
    started = _now()
    warmup(config, tag, http, args.timeout, out_dir / "warmup_responses.jsonl")
    snapshot = rq5_runner.process_snapshot(config, tag, transport=http)
    counts = {"model_calls_attempted": 0, "model_calls_ok": 0, "model_call_errors": 0, "reused_cells_written": 0}
    consecutive, stopped = 0, False
    with common.JsonlAppender(responses_path) as out:
        for entry in own_plan:
            cid = entry["cell_id"]
            if cid in done:
                continue
            if entry["generation_kind"] == "model_call":
                if cid not in allowed:
                    continue
                row = run_model_call(config, by_id[cid], http, run_id, checks["model_digest"], args.timeout)
                out.write(row)
                last[cid] = row
                counts["model_calls_attempted"] += 1
                if row["status"] == "ok":
                    counts["model_calls_ok"] += 1
                    done.add(cid)
                    consecutive = 0
                else:
                    counts["model_call_errors"] += 1
                    consecutive += 1
                print(f"{cid}: {row['status']} {(row['content'] or '')[:70]!r}")
                if consecutive >= args.max_consecutive_errors:
                    stopped = True
                    print(f"Arresto dopo {consecutive} errori consecutivi.", file=sys.stderr)
                    break
            else:
                source = last.get(entry["reused_from_cell_id"])
                if not source or source.get("status") != "ok":
                    continue
                row = reuse_row(by_id[cid], by_id[entry["reused_from_cell_id"]], source, run_id)
                out.write(row)
                last[cid] = row
                done.add(cid)
                counts["reused_cells_written"] += 1
    unloaded = rq5_runner.unload(config, tag, http, args.timeout)

    manifest_path = out_dir / "run_manifest.json"
    runs = common.read_json(manifest_path)["runs"] if manifest_path.exists() else []
    runs.append({
        "run_id": run_id, "config_id": config["config_id"], "config_sha256": common.sha256_file(config_path),
        "stage": stage, "model_tag": tag, "preflight": checks, "process_snapshot": snapshot, "unload": unloaded,
        "model_config_sha256": common.model_config_sha256(config, tag), "started_at": started,
        "finished_at": _now(), "options": {"limit": args.limit, "resume": args.resume},
        "counts": counts, "stopped_early": stopped,
        "planned": {"cells": len(own_plan), "model_calls": sum(p["generation_kind"] == "model_call" for p in own_plan)},
    })
    common.dump_json(manifest_path, {"runs": runs})
    print(f"{tag}: chiamate {counts['model_calls_ok']} ok, {counts['model_call_errors']} errori, "
          f"riusi {counts['reused_cells_written']}.")
    return 1 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
