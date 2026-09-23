#!/usr/bin/env python3
"""Generazioni di RQ3 / SC07 con Claude Sonnet 5 Chat tramite Claude Code CLI.

Meccanismo di chiamata: lo stesso di `scripts/run_generation.py`, da cui sono
importati `build_command` e `parse_stream`:
  - `claude --print` non interattivo, prompt su stdin;
  - `--model claude-sonnet-5`, `--effort medium`, nessun `--fallback-model`;
  - `--tools ""`, `--strict-mcp-config`, `--setting-sources ""`;
  - `--no-session-persistence`: nessuna conversazione da riprendere;
  - directory di lavoro temporanea, vuota, verificata prima di ogni chiamata;
  - `--output-format stream-json`: si salva il modello realmente usato.
Non servono l'SDK `anthropic` ne' una API key: serve un `claude` autenticato.

Lo script legge soltanto configurazione, richieste e piano delle chiamate
dello split scelto. **Non legge mai l'oracle**: per tutta l'esecuzione
`common.forbid_oracle()` e' attivo.

Riuso dei prompt identici (`generation.reuse_identical_prompts`): quando due
celle hanno lo stesso `prompt_sha256` e la stessa configurazione del modello
(`model_config_sha256`), la prima nell'ordine delle richieste riceve una
chiamata reale; le altre ricevono la stessa risposta con
`generation_kind="reused_identical_prompt"` e `reused_from_cell_id`. Il riuso
non e' una nuova chiamata al modello. Prima di riusare, il runner controlla che
system e user siano identici carattere per carattere.

Un output errato o non conforme e' una cella conclusa: non viene rigenerato.
Gli errori di trasporto restano nel file e vengono ritentati solo con
`--resume`. `--limit N` limita le chiamate reali, non le celle.

Blocchi prima di una chiamata reale:
  1. modello `claude-sonnet-5`, canale `Claude Code CLI`, nessun fallback,
     registrazione e parametri confermati nella configurazione;
  2. richieste, piano delle chiamate e configurazione del modello uguali a
     `build_manifest.json`;
  3. solo per `evaluation`: sviluppo completo (36 celle), file
     `results/rq3/sc07/v1/evaluation_gate.json` riferito alle risposte dello
     sviluppo e alla configurazione attuali, flag `--confirm-evaluation`.

`--dry-run` non esegue `claude`, non apre connessioni e non scrive file.

Uso:
    python3 scripts/rq3/run_rq3_sc07_claude.py --split development --dry-run
    python3 scripts/rq3/run_rq3_sc07_claude.py --split development
    python3 scripts/rq3/run_rq3_sc07_claude.py --split development --resume
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq3_sc07_common as common  # noqa: E402

CLI_CHANNEL = "Claude Code CLI"


class GateError(RuntimeError):
    pass


def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# --------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------

def model_gate_problems(config):
    model, generation = config["model"], config["generation"]
    params = generation["parameters"]
    problems = []
    if not model.get("model_id"):
        problems.append("model.model_id non registrato")
    if model.get("access_channel") != CLI_CHANNEL:
        problems.append(f"model.access_channel deve essere '{CLI_CHANNEL}'")
    if model.get("registration_confirmed") is not True:
        problems.append("model.registration_confirmed non e' true")
    if generation.get("parameters_confirmed") is not True:
        problems.append("generation.parameters_confirmed non e' true")
    if model.get("fallback_model") is not None or params.get("fallback_model") is not None:
        problems.append("nessun modello di fallback ammesso")
    if params.get("model") != model.get("model_id"):
        problems.append("generation.parameters.model diverso da model.model_id")
    if "--fallback-model" in common.cli_command(config):
        problems.append("il comando contiene --fallback-model")
    return problems


def evaluation_gate_path(config, repo_root=common.REPO_ROOT):
    return Path(repo_root) / config["artifacts"]["results_dir"] / "evaluation_gate.json"


def last_rows_by_cell(path):
    """Ultima riga per cella: vale l'ultimo tentativo."""
    if not Path(path).exists():
        return {}
    rows = {}
    for row in common.read_jsonl(path):
        rows[row["cell_id"]] = row
    return rows


def evaluation_gate_problems(config, confirm_flag, repo_root=common.REPO_ROOT, config_path=common.CONFIG_PATH):
    problems = []
    if not confirm_flag:
        problems.append("manca --confirm-evaluation")
    dev_requests = common.read_jsonl(common.requests_path(config, "development", repo_root))
    dev_responses = common.results_dir(config, "development", repo_root) / "raw_responses.jsonl"
    model_id = config["model"].get("model_id")
    last = last_rows_by_cell(dev_responses)
    done = sum(
        1 for r in dev_requests
        if last.get(common.cell_id("development", model_id, r["condition"], r["question_id"]), {}).get("status") == "ok"
    )
    if done != len(dev_requests):
        problems.append(f"sviluppo incompleto: {done}/{len(dev_requests)} celle concluse")
    gate_path = evaluation_gate_path(config, repo_root)
    if not gate_path.exists():
        problems.append(f"file di gate assente: {common.rel(gate_path, repo_root)}")
        return problems
    gate = common.read_json(gate_path)
    for key in ("approved_by", "approved_at", "development_raw_responses_sha256", "config_sha256"):
        if not gate.get(key):
            problems.append(f"evaluation_gate.{key} mancante")
    if dev_responses.exists() and gate.get("development_raw_responses_sha256") != common.sha256_file(dev_responses):
        problems.append("evaluation_gate non riferito all'attuale file di risposte dello sviluppo")
    if gate.get("config_sha256") != common.sha256_file(config_path):
        problems.append("evaluation_gate non riferito all'attuale configurazione")
    return problems


def check_inputs_against_manifest(config, split, requests, repo_root=common.REPO_ROOT):
    """Richieste, piano e configurazione del modello coincidono con la costruzione."""
    build = common.read_json(common.design_dir(config, repo_root) / "build_manifest.json")
    for path in (common.requests_path(config, split, repo_root), common.call_plan_path(config, split, repo_root)):
        if build["artifacts_sha256"].get(common.rel(path, repo_root)) != common.sha256_file(path):
            raise GateError(f"{common.rel(path, repo_root)} diverso dal build_manifest")
    if build.get("model_config_sha256") != common.model_config_sha256(config):
        raise GateError("configurazione del modello diversa da quella del build_manifest")
    plan = common.read_jsonl(common.call_plan_path(config, split, repo_root))
    if plan != common.plan_calls(config, requests):
        raise GateError("piano delle chiamate non ricalcolabile dalle richieste")
    return common.sha256_file(common.requests_path(config, split, repo_root)), plan


# --------------------------------------------------------------------------
# Trasporto Claude Code CLI
# --------------------------------------------------------------------------

def _result_event(stdout):
    for line in reversed((stdout or "").splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            return event
    return None


def _failure(error):
    return {"error": error, "answer": None, "model_used": None, "stdout": None, "stderr": None, "returncode": None}


def make_cli_transport(config, cwd, runner=subprocess.run):
    """Una chiamata `claude --print` isolata per ogni input.

    Ritorna una funzione `call(cli_input) -> dict`. `runner` e' sostituibile
    nei test; in esecuzione reale e' `subprocess.run`.
    """
    command = common.cli_command(config)
    timeout = config["generation"]["parameters"]["timeout_seconds"]

    def call(text):
        if any(Path(cwd).iterdir()):
            return _failure(f"directory di lavoro non vuota: {cwd}")
        try:
            completed = runner(command, input=text, cwd=str(cwd), capture_output=True,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return _failure(f"timeout dopo {timeout} secondi")
        except OSError as exc:
            return _failure(f"impossibile eseguire claude: {exc}")
        result = {"stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode}
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()[:500]
            return {**result, "error": f"claude uscito con codice {completed.returncode}: {detail}",
                    "answer": None, "model_used": None}
        answer, used, error = common.pilot_generation.parse_stream(completed.stdout)
        return {**result, "answer": answer, "model_used": used, "error": error}

    call.command = command
    call.cwd = str(cwd)
    return call


def cli_version(runner=subprocess.run):
    try:
        completed = runner(["claude", "--version"], capture_output=True, text=True, timeout=30)
        return completed.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


# --------------------------------------------------------------------------
# Celle
# --------------------------------------------------------------------------

def _base_row(config, request, plan_entry, run_id):
    model = config["model"]
    return {
        "cell_id": common.cell_id(request["split"], model["model_id"], request["condition"], request["question_id"]),
        "request_id": request["request_id"],
        "config_id": config["config_id"],
        "run_id": run_id,
        "split": request["split"],
        "condition": request["condition"],
        "question_id": request["question_id"],
        "episode_id": request["episode_id"],
        "model_display_name": model["display_name"],
        "model_requested": model["model_id"],
        "access_channel": model["access_channel"],
        "effort": config["generation"]["parameters"]["effort"],
        "model_config_sha256": plan_entry["model_config_sha256"],
        "prompt_sha256": request["prompt_sha256"],
        "cli_input_sha256": common.sha256_text(common.cli_input(config, request)),
    }


def run_model_call(config, request, plan_entry, transport, run_id):
    started, t0 = _now(), time.monotonic()
    outcome = transport(common.cli_input(config, request))
    latency = time.monotonic() - t0
    error = outcome.get("error")
    answer = None if error else outcome.get("answer")
    model_used = outcome.get("model_used")
    return {
        **_base_row(config, request, plan_entry, run_id),
        "generation_kind": "model_call",
        "model_call": True,
        "reused_from_cell_id": None,
        "cli_command": getattr(transport, "command", None),
        "started_at": started,
        "finished_at": _now(),
        "latency_seconds": round(latency, 3),
        "status": "error" if error else "ok",
        "error": error,
        "response_text": answer,
        "response_sha256": None if answer is None else common.sha256_text(answer),
        "model_used": model_used,
        "model_used_matches_requested": (model_used == config["model"]["model_id"]) if model_used else None,
        "returncode": outcome.get("returncode"),
        "raw_stdout": outcome.get("stdout"),
        "raw_stderr": outcome.get("stderr"),
        "result_event": _result_event(outcome.get("stdout")),
    }


def reuse_row(config, request, plan_entry, source_request, source_row, run_id):
    """Cella con prompt identico: stessa risposta, nessuna nuova chiamata."""
    if (request["system"] != source_request["system"] or request["user"] != source_request["user"]
            or request["prompt_sha256"] != source_request["prompt_sha256"]):
        raise ValueError(f"riuso rifiutato: prompt diverso per {request['request_id']}")
    if source_row.get("model_config_sha256") != plan_entry["model_config_sha256"]:
        raise ValueError(f"riuso rifiutato: configurazione del modello diversa per {request['request_id']}")
    if source_row.get("status") != "ok" or source_row.get("generation_kind") != "model_call":
        raise ValueError("riuso ammesso solo da una chiamata reale conclusa")
    return {
        **_base_row(config, request, plan_entry, run_id),
        "generation_kind": "reused_identical_prompt",
        "model_call": False,
        "reused_from_cell_id": source_row["cell_id"],
        "created_at": _now(),
        "status": "ok",
        "error": None,
        "response_text": source_row["response_text"],
        "response_sha256": source_row["response_sha256"],
        "model_used": source_row["model_used"],
        "model_used_matches_requested": source_row["model_used_matches_requested"],
    }


# --------------------------------------------------------------------------
# Dry-run
# --------------------------------------------------------------------------

def dry_run_report(config, split, requests, plan, pending_calls, pending_reuse, gate_problems):
    by_id = {r["request_id"]: r for r in requests}
    model_calls = sum(1 for p in plan if p["generation_kind"] == "model_call")
    print(f"DRY-RUN — nessuna chiamata a claude, nessun file scritto. Split: {split}")
    print(f"Celle: {len(plan)}  chiamate reali previste: {model_calls}  "
          f"celle con prompt identico riusato: {len(plan) - model_calls}")
    print(f"Da eseguire ora: {len(pending_calls)} chiamate reali, {len(pending_reuse)} riusi")
    print(f"Modello: {config['model']['display_name']} = {config['model']['model_id']} "
          f"via {config['model']['access_channel']}, effort {config['generation']['parameters']['effort']}, "
          f"fallback {config['model']['fallback_model']}")
    print("Comando: " + " ".join(repr(p) if p == "" else p for p in common.cli_command(config)))
    print("Directory di lavoro: nuova directory temporanea vuota; prompt su stdin")
    print(f"`claude` nel PATH: {shutil.which('claude') or 'NO'}")
    print(f"model_config_sha256: {common.model_config_sha256(config)}")
    print("Gate: " + ("; ".join(gate_problems) if gate_problems else "nessun blocco"))

    reused = next((p for p in plan if p["generation_kind"] == "reused_identical_prompt"), None)
    differing = next((p for p in plan if p["generation_kind"] == "model_call"
                      and p["condition"] == "shared_interleaved"), None)
    for title, entry in (("Coppia con prompt identico", reused), ("Coppia con contesti diversi", differing)):
        if entry is None:
            continue
        print("\n" + "=" * 78 + f"\n{title}: {entry['question_id']}")
        pair = [x for x in plan if x["question_id"] == entry["question_id"]]
        for p in pair:
            r = by_id[p["request_id"]]
            note = f"riusa {p['reused_from_request_id']}" if p["reused_from_request_id"] else "chiamata reale"
            leaks = common.prompt_leaks(common.cli_input(config, r))
            oracle_keys = sorted(set(r) & common.ORACLE_KEYS)
            print(f"- {p['request_id']}: {p['generation_kind']} ({note}); "
                  f"prompt_sha256 {p['prompt_sha256'][:16]}...; "
                  f"indicatori di fonte: {leaks or 'nessuno'}; chiavi di oracle: {oracle_keys or 'nessuna'}")
        shown = [pair[0]] if entry is reused else pair
        for p in shown:
            print("-" * 78 + f"\nstdin di {p['request_id']}:\n" + common.cli_input(config, by_id[p["request_id"]]))


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv=None, transport=None, repo_root=common.REPO_ROOT, config_path=common.CONFIG_PATH):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", required=True, choices=common.SPLITS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="numero massimo di chiamate reali")
    parser.add_argument("--resume", action="store_true", help="salta le celle gia' concluse con status ok")
    parser.add_argument("--confirm-evaluation", action="store_true")
    parser.add_argument("--max-consecutive-errors", type=int, default=3)
    args = parser.parse_args(argv)

    # Per tutta l'esecuzione ogni lettura dell'oracle solleva un'eccezione.
    common.forbid_oracle()
    try:
        return _run(args, transport, repo_root, config_path)
    finally:
        common.allow_oracle()


def _run(args, transport, repo_root, config_path):
    config = common.load_config(config_path)
    split = args.split
    requests = common.read_jsonl(common.requests_path(config, split, repo_root))
    requests_sha, plan = check_inputs_against_manifest(config, split, requests, repo_root)
    by_id = {r["request_id"]: r for r in requests}
    out_dir = common.results_dir(config, split, repo_root)
    responses_path = out_dir / "raw_responses.jsonl"
    model_id = config["model"]["model_id"]
    cell_of = {p["request_id"]: common.cell_id(split, model_id, p["condition"], p["question_id"]) for p in plan}

    gate_problems = model_gate_problems(config)
    if split == "evaluation":
        gate_problems += evaluation_gate_problems(config, args.confirm_evaluation, repo_root, config_path)

    last = last_rows_by_cell(responses_path)
    done = {cid for cid, row in last.items() if row.get("status") == "ok"}
    pending_calls = [p for p in plan
                     if p["generation_kind"] == "model_call" and cell_of[p["request_id"]] not in done]
    if args.limit is not None:
        pending_calls = pending_calls[: args.limit]
    pending_reuse = [p for p in plan
                     if p["generation_kind"] != "model_call" and cell_of[p["request_id"]] not in done]

    if args.dry_run:
        dry_run_report(config, split, requests, plan, pending_calls, pending_reuse, gate_problems)
        return 0
    if gate_problems:
        for problem in gate_problems:
            print(f"BLOCCATO: {problem}", file=sys.stderr)
        return 2
    if last and not args.resume:
        print(f"BLOCCATO: {common.rel(responses_path, repo_root)} contiene gia' risposte; usa --resume.",
              file=sys.stderr)
        return 2

    workdir = None
    version = "transport di test"
    if transport is None:
        if not shutil.which("claude"):
            print("BLOCCATO: comando `claude` non trovato nel PATH.", file=sys.stderr)
            return 2
        version = cli_version()
        # Directory neutra e vuota: il modello non vede il progetto.
        workdir = tempfile.mkdtemp(prefix="rq3_sc07_generazione_")
        transport = make_cli_transport(config, workdir)

    allowed_calls = {p["request_id"] for p in pending_calls}
    run_id = uuid.uuid4().hex
    started = _now()
    counts = {"model_calls_attempted": 0, "model_calls_ok": 0, "model_call_errors": 0,
              "reused_cells_written": 0}
    consecutive_errors, stopped_early = 0, False
    with common.JsonlAppender(responses_path) as out:
        for entry in plan:
            request = by_id[entry["request_id"]]
            cid = cell_of[entry["request_id"]]
            if cid in done:
                continue
            if entry["generation_kind"] == "model_call":
                if entry["request_id"] not in allowed_calls:
                    continue
                row = run_model_call(config, request, entry, transport, run_id)
                out.write(row)
                last[cid] = row
                counts["model_calls_attempted"] += 1
                if row["status"] == "ok":
                    counts["model_calls_ok"] += 1
                    done.add(cid)
                    consecutive_errors = 0
                else:
                    counts["model_call_errors"] += 1
                    consecutive_errors += 1
                print(f"{cid}: chiamata {row['status']} {row['latency_seconds']}s "
                      f"[{row['model_used']}] {(row['response_text'] or row['error'] or '')[:60]!r}")
                if consecutive_errors >= args.max_consecutive_errors:
                    stopped_early = True
                    print(f"Arresto dopo {consecutive_errors} errori consecutivi.", file=sys.stderr)
                    break
            else:
                source_cid = cell_of[entry["reused_from_request_id"]]
                source_row = last.get(source_cid)
                if not source_row or source_row.get("status") != "ok":
                    continue
                row = reuse_row(config, request, entry, by_id[entry["reused_from_request_id"]],
                                source_row, run_id)
                out.write(row)
                last[cid] = row
                done.add(cid)
                counts["reused_cells_written"] += 1
                print(f"{cid}: riuso di {source_cid}")

    leftover = []
    if workdir:
        leftover = os.listdir(workdir)
        shutil.rmtree(workdir, ignore_errors=True)
    final = last_rows_by_cell(responses_path)
    ok_rows = [r for r in final.values() if r.get("status") == "ok"]
    manifest_path = out_dir / "run_manifest.json"
    runs = common.read_json(manifest_path)["runs"] if manifest_path.exists() else []
    runs.append({
        "run_id": run_id,
        "config_id": config["config_id"],
        "config_sha256": common.sha256_file(config_path),
        "split": split,
        "requests_sha256": requests_sha,
        "model_display_name": config["model"]["display_name"],
        "model_requested": model_id,
        "access_channel": config["model"]["access_channel"],
        "model_config_sha256": common.model_config_sha256(config),
        "cli_command": common.cli_command(config),
        "cli_version": version,
        "working_directory": workdir,
        "working_directory_files_after_run": leftover,
        "python": platform.python_version(),
        "started_at": started,
        "finished_at": _now(),
        "options": {"limit": args.limit, "resume": args.resume},
        "counts": counts,
        "stopped_early": stopped_early,
        "planned": {"cells": len(plan),
                    "model_calls": sum(1 for p in plan if p["generation_kind"] == "model_call")},
        "cells_ok_after_run": len(ok_rows),
        "model_calls_ok_after_run": sum(1 for r in ok_rows if r.get("generation_kind") == "model_call"),
        "models_used": sorted({r.get("model_used") or "?" for r in ok_rows}),
    })
    common.dump_json(manifest_path, {"runs": runs})
    print(f"Chiamate reali: {counts['model_calls_ok']} ok, {counts['model_call_errors']} errori; "
          f"riusi scritti: {counts['reused_cells_written']}. Celle ok: {len(ok_rows)}/{len(plan)}.")
    if split == "development" and len(ok_rows) == len(plan):
        print("Sviluppo completo: fermarsi e rivedere prima di qualsiasi valutazione.")
    return 1 if stopped_early else 0


if __name__ == "__main__":
    sys.exit(main())
