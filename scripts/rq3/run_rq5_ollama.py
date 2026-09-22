#!/usr/bin/env python3
"""Esecuzione delle generazioni di RQ5 / SC06 con Ollama.

Lo script legge soltanto due cose: la configurazione autoritativa e il file di
richieste dello split scelto. **Non apre mai l'oracle o `case_mapping.jsonl`**:
durante la generazione le risposte attese non devono essere disponibili
nemmeno in memoria.

Per ogni cella (split, tag del modello, condizione, `question_id`) esegue una
chiamata a `/api/chat` con prompt, schema e opzioni della configurazione e
salva richiesta, risposta grezza, eventuale errore, orari e tutti i metadati
restituiti da Ollama. Gli output non conformi vengono conservati come sono:
non esiste una seconda chiamata per correggerli.

I modelli vengono eseguiti uno alla volta, nell'ordine dichiarato in
`runtime.model_order`; prima di ogni blocco si eseguono le richieste di
riscaldamento previste, registrate in un file separato ed escluse dai
risultati. Le richieste seguono `runtime.request_order`: `question_id`
crescente, prima `sufficient` poi `insufficient`.

Prima di partire lo script verifica che il tag esista in locale e che il
digest coincida con quello della configurazione. Con `--dry-run` non viene
aperta nessuna connessione: vengono soltanto mostrate le richieste, che non
contengono risposte attese.

Uso:
    # anteprima, nessuna chiamata
    python3 scripts/rq3/run_rq5_ollama.py --split development --dry-run

    # esecuzione dello split di sviluppo, un modello alla volta
    python3 scripts/rq3/run_rq5_ollama.py --split development --model gemma3:4b
    python3 scripts/rq3/run_rq5_ollama.py --split development --model llama3.2:3b

    # ripresa dopo un'interruzione
    python3 scripts/rq3/run_rq5_ollama.py --split development --model gemma3:4b --resume
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq5_common as common  # noqa: E402

WARMUP_PROMPT = "Rispondi soltanto con {\"values\": []}."


def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def http_json(url, payload=None, timeout=600, method=None):
    """Una chiamata HTTP JSON. Nei test viene sostituita da una funzione finta."""
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _base_url(config):
    endpoint = urlparse(config["runtime"]["endpoint"])
    return f"{endpoint.scheme}://{endpoint.netloc}"


# --------------------------------------------------------------------------
# Controlli prima di partire
# --------------------------------------------------------------------------

def preflight(config, model_tag, transport=http_json, allow_version_mismatch=False):
    """Verifica versione di Ollama, presenza del tag e digest locale."""
    base = _base_url(config)
    checks = {}

    version = transport(f"{base}/api/version").get("version")
    checks["ollama_version"] = version
    expected_version = config["runtime"]["verified_version"]
    if version != expected_version and not allow_version_mismatch:
        raise RuntimeError(
            f"Ollama {version} diverso dalla versione verificata {expected_version}: "
            "usa --allow-version-mismatch solo dichiarandolo nei risultati."
        )

    declared = {model["ollama_tag"]: model for model in config["models"]}
    if model_tag not in declared:
        raise RuntimeError(f"tag non previsto dalla configurazione: {model_tag}")

    tags = transport(f"{base}/api/tags").get("models", [])
    local = {entry.get("model") or entry.get("name"): entry for entry in tags}
    if model_tag not in local:
        raise RuntimeError(
            f"{model_tag} non e' installato localmente: nessun modello viene scaricato."
        )
    digest = local[model_tag].get("digest")
    if digest != declared[model_tag]["ollama_digest"]:
        raise RuntimeError(
            f"{model_tag}: digest locale {digest} diverso da "
            f"{declared[model_tag]['ollama_digest']}"
        )
    checks["model_digest"] = digest
    checks["model_size_bytes"] = local[model_tag].get("size")
    checks["quantization"] = (local[model_tag].get("details") or {}).get("quantization_level")
    return checks


def process_snapshot(config, model_tag, transport=http_json):
    """`size` e `size_vram` da /api/ps: allocazione dichiarata, non picco di RAM."""
    base = _base_url(config)
    try:
        loaded = transport(f"{base}/api/ps").get("models", [])
    except Exception as error:  # noqa: BLE001
        return {"error": f"{type(error).__name__}: {error}"}
    for entry in loaded:
        if (entry.get("model") or entry.get("name")) == model_tag:
            return {
                "model": model_tag,
                "size": entry.get("size"),
                "size_vram": entry.get("size_vram"),
                "context_length": entry.get("context_length"),
                "note": config["performance"]["limitation"],
            }
    return {"model": model_tag, "note": "modello non presente in /api/ps"}


# --------------------------------------------------------------------------
# Esecuzione
# --------------------------------------------------------------------------

def load_requests(path, split):
    rows = common.read_jsonl(path)
    wrong = [row for row in rows if row["split"] != split]
    if wrong:
        raise ValueError(f"{path} contiene {len(wrong)} richieste di un altro split")
    rows.sort(key=lambda row: (row["question_id"], row["condition"] != "sufficient"))
    return rows


def completed_cells(path):
    """Celle gia' concluse e valide: `status == ok` con contenuto presente.

    Vale l'ultima riga scritta per ogni cella. Le righe di errore restano nel
    file ma non contano come concluse, quindi `--resume` le riprova senza
    cancellarle.
    """
    path = Path(path)
    if not path.exists():
        return {}
    last = {}
    for row in common.read_jsonl(path):
        last[row["cell_id"]] = row
    return {
        cell: row for cell, row in last.items()
        if row.get("status") == "ok" and row.get("content") is not None
    }


def _metrics(response, config):
    return {
        field: response.get(field)
        for field in config["performance"]["log_ollama_fields"]
    }


def run_cell(config, model_tag, request, transport, timeout):
    """Una chiamata. Ritorna il record da salvare, anche in caso di errore."""
    payload = common.chat_payload(
        config, model_tag,
        request["messages"][0]["content"], request["messages"][1]["content"],
    )
    record = {
        "cell_id": common.cell_id(
            request["split"], model_tag, request["condition"], request["question_id"]
        ),
        "request_id": request["request_id"],
        "split": request["split"],
        "model_tag": model_tag,
        "condition": request["condition"],
        "question_id": request["question_id"],
        "episode_id": request["episode_id"],
        "prompt_sha256": request["prompt_sha256"],
        "request": payload,
        "started_at": _now(),
        "warmup": False,
    }
    started = time.monotonic()
    try:
        response = transport(config["runtime"]["endpoint"], payload, timeout=timeout)
    except Exception as error:  # noqa: BLE001 - l'errore va conservato, non corretto
        record.update({
            "status": "error",
            "content": None,
            "response": None,
            "error": {"type": type(error).__name__, "message": str(error)},
            "ollama_metrics": {},
        })
    else:
        record.update({
            "status": "ok",
            "content": (response.get("message") or {}).get("content"),
            "response": response,
            "error": None,
            "ollama_metrics": _metrics(response, config),
            "done_reason": response.get("done_reason"),
        })
    record["finished_at"] = _now()
    record["wall_seconds"] = round(time.monotonic() - started, 6)
    return record


def warmup(config, model_tag, transport, timeout, out_path):
    """Richieste di riscaldamento: escluse dai risultati, comunque registrate."""
    count = config["runtime"]["warmup_requests_per_model"]
    records = []
    with common.JsonlAppender(out_path) as appender:
        for index in range(count):
            payload = common.chat_payload(
                config, model_tag, config["prompt"]["system"], WARMUP_PROMPT
            )
            record = {
                "warmup": True,
                "model_tag": model_tag,
                "index": index + 1,
                "started_at": _now(),
                "request": payload,
            }
            try:
                response = transport(config["runtime"]["endpoint"], payload, timeout=timeout)
            except Exception as error:  # noqa: BLE001
                record.update({"status": "error",
                               "error": {"type": type(error).__name__, "message": str(error)}})
            else:
                record.update({"status": "ok", "response": response,
                               "content": (response.get("message") or {}).get("content")})
            record["finished_at"] = _now()
            appender.write(record)
            records.append(record)
    return records


def unload(config, model_tag, transport, timeout):
    """Scarica il modello: uno solo resta caricato alla volta."""
    payload = {"model": model_tag, "messages": [], "keep_alive": 0}
    try:
        transport(config["runtime"]["endpoint"], payload, timeout=timeout)
        return {"model": model_tag, "unloaded": True}
    except Exception as error:  # noqa: BLE001
        return {"model": model_tag, "unloaded": False,
                "error": f"{type(error).__name__}: {error}"}


def append_manifest(path, entry):
    path = Path(path)
    manifest = {"runs": []}
    if path.exists():
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.setdefault("runs", [])
    manifest["runs"].append(entry)
    manifest["config_id"] = entry["config_id"]
    manifest["split"] = entry["split"]
    common.dump_json(path, manifest)


def dry_run_report(config, model_tags, requests, limit):
    """Mostra le richieste senza aprire connessioni."""
    forbidden = config["context_builder"]["forbidden_prompt_inputs"]
    selected = requests[:limit] if limit else requests
    print(f"DRY RUN — nessuna chiamata a Ollama, nessun file scritto.")
    print(f"modelli:   {', '.join(model_tags)}")
    print(f"richieste: {len(selected)} (indipendenti dal modello)")
    print(f"celle:     {len(selected) * len(model_tags)}")
    present = sorted(
        key for key in forbidden
        for row in selected
        if key in json.dumps(row, ensure_ascii=False)
    )
    print(f"campi vietati presenti nelle richieste: {present or 'nessuno'}")
    print("risposte attese incluse nelle richieste: no")
    if selected:
        example = common.chat_payload(
            config, model_tags[0],
            selected[0]["messages"][0]["content"], selected[0]["messages"][1]["content"],
        )
        print(f"\nEsempio di richiesta — {selected[0]['request_id']}")
        print(json.dumps(example, ensure_ascii=False, indent=2))
    return selected


def main(argv=None, transport=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", required=True, choices=common.SPLITS)
    parser.add_argument("--model", action="append", default=None,
                        help="tag Ollama; ripetibile. Senza opzione: tutti, uno alla volta.")
    parser.add_argument("--limit", type=int, default=None,
                        help="esegue solo le prime N richieste dello split")
    parser.add_argument("--resume", action="store_true",
                        help="salta le celle gia' concluse e valide")
    parser.add_argument("--dry-run", action="store_true",
                        help="mostra le richieste senza chiamare Ollama")
    parser.add_argument("--config", default=str(common.CONFIG_PATH))
    parser.add_argument("--inputs-dir", default=None,
                        help="predefinita: la directory della versione in configurazione")
    parser.add_argument("--out-dir", default=None,
                        help="predefinita: la directory della versione in configurazione")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--allow-version-mismatch", action="store_true")
    parser.add_argument("--no-unload", action="store_true",
                        help="non scarica il modello alla fine del blocco")
    args = parser.parse_args(argv)

    config = common.load_config(args.config)
    transport = transport or http_json

    order = config["runtime"]["model_order"]
    model_tags = args.model or list(order)
    unknown = [tag for tag in model_tags if tag not in order]
    if unknown:
        parser.error(f"tag non dichiarati nella configurazione: {unknown}")
    model_tags.sort(key=order.index)

    inputs = Path(args.inputs_dir) if args.inputs_dir else common.inputs_dir(config)
    requests_path = inputs / f"{args.split}_requests.jsonl"
    requests = load_requests(requests_path, args.split)
    if args.limit:
        requests = requests[: args.limit]

    if args.dry_run:
        dry_run_report(config, model_tags, requests, None)
        return 0

    out_dir = (Path(args.out_dir) if args.out_dir else common.results_dir(config)) / args.split
    responses_path = out_dir / "raw_responses.jsonl"
    warmup_path = out_dir / "warmup_responses.jsonl"
    manifest_path = out_dir / "run_manifest.json"

    done = completed_cells(responses_path) if args.resume else {}
    exit_code = 0

    for model_tag in model_tags:
        checks = preflight(config, model_tag, transport, args.allow_version_mismatch)
        print(f"{model_tag}: Ollama {checks['ollama_version']}, digest verificato.")

        warmup_records = warmup(config, model_tag, transport, args.timeout, warmup_path)
        snapshot = process_snapshot(config, model_tag, transport)

        planned = [
            row for row in requests
            if common.cell_id(args.split, model_tag, row["condition"], row["question_id"])
            not in done
        ]
        skipped = len(requests) - len(planned)
        counts = {"ok": 0, "error": 0}
        started_at = _now()
        with common.JsonlAppender(responses_path) as appender:
            for index, row in enumerate(planned, 1):
                record = run_cell(config, model_tag, row, transport, args.timeout)
                appender.write(record)
                counts[record["status"]] += 1
                if index % 25 == 0 or index == len(planned):
                    print(f"  {model_tag} {index}/{len(planned)} "
                          f"(ok={counts['ok']} errori={counts['error']})")
        unloaded = None if args.no_unload else unload(
            config, model_tag, transport, args.timeout
        )

        append_manifest(manifest_path, {
            "config_id": config["config_id"],
            "split": args.split,
            "model_tag": model_tag,
            "started_at": started_at,
            "finished_at": _now(),
            "preflight": checks,
            "requests_file": str(requests_path.relative_to(common.REPO_ROOT))
            if str(requests_path).startswith(str(common.REPO_ROOT)) else str(requests_path),
            "requests_sha256": common.sha256_file(requests_path),
            "options": config["runtime"]["options"],
            "keep_alive": config["runtime"]["keep_alive"],
            "response_schema": config["prompt"]["response_schema"],
            "request_order": config["runtime"]["request_order"],
            "warmup_requests": len(warmup_records),
            "warmup_in_results": config["runtime"]["warmup_in_results"],
            "resume": args.resume,
            "limit": args.limit,
            "planned_cells": len(planned),
            "skipped_completed_cells": skipped,
            "completed_ok": counts["ok"],
            "errors": counts["error"],
            "process_snapshot": snapshot,
            "unload": unloaded,
        })
        print(f"{model_tag}: ok={counts['ok']} errori={counts['error']} "
              f"saltate={skipped}")
        if counts["error"]:
            exit_code = 1

    print(f"\nRisposte in {responses_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
