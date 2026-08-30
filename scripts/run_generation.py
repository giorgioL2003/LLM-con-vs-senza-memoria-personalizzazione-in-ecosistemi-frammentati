#!/usr/bin/env python3
"""Generazione delle risposte del modello per gli input gia' preparati.

Lo script legge `results/generation_inputs.jsonl` e, per ogni input, esegue una
chiamata indipendente a Claude Code in modalita' non interattiva. Non modifica
gli scenari, l'oracle, il retrieval o gli input: legge soltanto il campo
`prompt` gia' costruito e salva la risposta in un file separato.

Ogni chiamata e' isolata:
  - un processo `claude` per input, senza `--resume` e senza `--continue`,
    quindi la conversazione non prosegue da una domanda alla successiva;
  - `--no-session-persistence`, quindi non resta nulla su disco da riprendere;
  - `--tools ""`, quindi il modello non puo' leggere file ne' cercare altro;
  - directory di lavoro neutra e vuota, quindi il modello non riceve
    informazioni dal progetto;
  - `--model claude-sonnet-5` e `--effort medium`, senza `--fallback-model`:
    se il modello richiesto non e' disponibile la chiamata fallisce e l'errore
    viene registrato, non sostituito da un altro modello.

Uso:
    python3 scripts/run_generation.py --out results/generation_pilot.jsonl
    python3 scripts/run_generation.py --question-id SC02-Q6 --out results/smoke_test.jsonl

L'esecuzione e' riprendibile: gli input gia' completati nel file di output
vengono saltati e non vengono richiamati. Le prove finite in errore vengono
invece rieseguite e la nuova riga viene aggiunta in fondo al file: se per la
stessa terna scenario/domanda/modalita' esistono piu' righe, vale l'ultima.

Serve un `claude` autenticato nel terminale da cui si lancia lo script: se
manca il login la chiamata fallisce con "Not logged in" e l'errore viene
salvato al posto della risposta.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUTS_PATH = REPO_ROOT / "results" / "generation_inputs.jsonl"
DEFAULT_OUTPUT = REPO_ROOT / "results" / "generation_pilot.jsonl"

MODEL = "claude-sonnet-5"
EFFORT = "medium"
TIMEOUT_SECONDS = 300

# Chiave che identifica una prova: uno scenario, una domanda, una modalita'.
KEY_FIELDS = ("scenario_id", "question_id", "mode")


def build_command(model=MODEL, effort=EFFORT):
    """Comando di una singola chiamata. Il prompt arriva da stdin."""
    return [
        "claude",
        "--print",                    # non interattivo
        "--model", model,             # modello esatto, nessun alias
        "--effort", effort,
        "--tools", "",                # nessuno strumento disponibile
        "--strict-mcp-config",        # nessun server MCP
        "--setting-sources", "",      # nessuna impostazione utente o di progetto
        "--no-session-persistence",   # nessuna conversazione da riprendere
        "--output-format", "stream-json",  # ogni messaggio dichiara il proprio modello
        "--verbose",                  # richiesto da stream-json
    ]


def key_of(row):
    return tuple(row[field] for field in KEY_FIELDS)


def load_inputs(path=INPUTS_PATH):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_done(path):
    """Chiavi gia' completate senza errore, da non richiamare."""
    path = Path(path)
    if not path.exists():
        return set()
    done = set()
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("error") is None:
                done.add(key_of(row))
    return done


def parse_stream(stdout):
    """Legge l'output stream-json: (risposta, modello che l'ha prodotta, errore).

    Il modello viene preso dai messaggi `assistant`, cioe' da chi ha scritto la
    risposta. Non si usa `modelUsage`, che somma anche le chiamate ausiliarie
    interne di Claude Code (un modello piu' piccolo per compiti di servizio,
    non per la risposta).
    """
    answer = None
    error = None
    models = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            model = (event.get("message") or {}).get("model")
            if model and model not in models:
                models.append(model)
        elif event.get("type") == "result":
            if event.get("is_error"):
                error = "errore riportato da claude: %s" % str(event.get("result"))[:500]
            else:
                answer = event.get("result")
    if error is None and answer is None:
        error = "nessun risultato nell'output: %s" % stdout.strip()[:500]
    return answer, (", ".join(models) or None), error


def call_claude(prompt, cwd, model=MODEL, effort=EFFORT, runner=subprocess.run):
    """Una chiamata indipendente. Restituisce (risposta, modello_usato, errore)."""
    command = build_command(model, effort)
    try:
        completed = runner(
            command,
            input=prompt,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, None, "timeout dopo %d secondi" % TIMEOUT_SECONDS
    except OSError as exc:
        return None, None, "impossibile eseguire claude: %s" % exc

    if completed.returncode != 0:
        return None, None, "claude uscito con codice %d: %s" % (
            completed.returncode,
            (completed.stderr or completed.stdout or "").strip()[:500],
        )

    return parse_stream(completed.stdout)


def run(rows, cwd, model=MODEL, effort=EFFORT, runner=subprocess.run, on_result=None):
    """Una chiamata per input, nell'ordine dato. Nessuno stato fra le chiamate."""
    results = []
    for row in rows:
        answer, used, error = call_claude(row["prompt"], cwd, model, effort, runner)
        result = {
            "scenario_id": row["scenario_id"],
            "question_id": row["question_id"],
            "mode": row["mode"],
            "model_requested": model,
            "model_used": used,
            "effort": effort,
            "model_answer": answer,
            "error": error,
        }
        results.append(result)
        if on_result is not None:
            on_result(result)
    return results


def append_result(path, result):
    """Scrittura incrementale: se l'esecuzione si interrompe, il gia' fatto resta."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")


def select(rows, question_id=None, modes=None, limit=None):
    selected = rows
    if question_id:
        selected = [row for row in selected if row["question_id"] == question_id]
    if modes:
        selected = [row for row in selected if row["mode"] in modes]
    if limit is not None:
        selected = selected[:limit]
    return selected


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Genera le risposte del modello.")
    parser.add_argument("--inputs", default=str(INPUTS_PATH))
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--question-id", default=None, help="esegue una sola domanda")
    parser.add_argument("--modes", nargs="*", default=None, help="modalita' da eseguire")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--effort", default=EFFORT)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    rows = select(load_inputs(args.inputs), args.question_id, args.modes, args.limit)
    if not rows:
        print("Nessun input selezionato.", file=sys.stderr)
        return 1

    done = load_done(args.out)
    todo = [row for row in rows if key_of(row) not in done]

    print("Input selezionati: %d (gia' completati: %d, da eseguire: %d)"
          % (len(rows), len(rows) - len(todo), len(todo)))
    if not todo:
        print("Niente da fare.")
        return 0

    # Directory neutra e vuota: il modello non vede il progetto.
    cwd = tempfile.mkdtemp(prefix="generazione_")
    print("Modello: %s | effort: %s | directory: %s" % (args.model, args.effort, cwd))
    print("Comando: %s" % " ".join(repr(part) if part == "" else part for part in build_command(args.model, args.effort)))
    print("-" * 72)

    def report(result):
        append_result(args.out, result)
        stato = "errore: %s" % result["error"] if result["error"] else "ok (%s)" % result["model_used"]
        print("%-12s %-8s %-13s %s" % (result["scenario_id"], result["question_id"], result["mode"], stato))

    results = run(todo, cwd, args.model, args.effort, on_result=report)

    failed = [result for result in results if result["error"]]
    print("-" * 72)
    print("Completate: %d | fallite: %d" % (len(results) - len(failed), len(failed)))
    print("Risposte scritte in %s" % args.out)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
