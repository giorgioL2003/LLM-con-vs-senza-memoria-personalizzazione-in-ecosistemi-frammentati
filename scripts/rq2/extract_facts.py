#!/usr/bin/env python3
"""Estrattore dei fatti candidati (architettura F, Fact-based RAG).

Legge le conversazioni di uno scenario **una sessione alla volta e in ordine
cronologico** e produce fatti brevi con identificatore, testo, messaggi
sorgente e ordine temporale.

Che cosa vede l'estrattore:
  - i messaggi dell'utente della sessione corrente, con i loro identificatori;
  - l'elenco dei fatti gia' estratti dalle sessioni precedenti, come contesto.

Che cosa NON vede mai:
  - le domande di valutazione;
  - l'oracle, le risposte attese, i fatti obbligatori;
  - le sessioni successive a quella in lavorazione;
  - i messaggi dell'assistente, che non introducono fatti autorevoli e non sono
    indicizzati nemmeno in T.

F conserva i fatti: non applica UPDATE ne' DELETE. Un'informazione superata
resta in memoria accanto a quella nuova, ed e' proprio questa la differenza che
il confronto F/U su SC03 deve misurare. I fatti salvati qui sono i *fatti
candidati* che U riutilizzera' nel blocco successivo.

Gli errori dell'estrattore non vengono corretti a mano: vengono registrati
(`provenance_valid`, `parse_error`) e valutati.

Uso:
    # nessuna chiamata al modello: costruisce e salva soltanto i prompt
    python3 scripts/rq2/extract_facts.py --scenario scenario_02 --dry-run

    # estrazione reale con Claude Sonnet 5 (una chiamata per sessione)
    python3 scripts/rq2/extract_facts.py --scenario scenario_02

Le chiamate riusano il meccanismo gia' adottato dal progetto
(`scripts/run_generation.py`): un processo `claude` isolato per chiamata.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402

sys.path.insert(0, str(rq2.SCRIPTS_DIR))
import run_generation as gen  # noqa: E402  (riuso del meccanismo di chiamata)

FACTS_DIR = rq2.RQ2_RESULTS_DIR / "facts"

ALLOWED_KINDS = rq2.ALLOWED_FACT_KINDS

# Prompt di estrazione: ruolo di sola scrittura della memoria. E' distinto dal
# prompt di risposta alle domande e viene salvato insieme all'output.
EXTRACTION_INSTRUCTIONS = (
    "Sei il componente di memoria di un sistema che segue un caso distribuito su piu' conversazioni.\n"
    "Il tuo unico compito e' estrarre fatti brevi dai messaggi che ti vengono mostrati.\n"
    "\n"
    "Regole:\n"
    "1. Estrai soltanto informazioni contenute nei messaggi nuovi. Non aggiungere conoscenze esterne\n"
    "   e non trarre conclusioni che non siano scritte.\n"
    "2. Un fatto per informazione: frasi brevi e autonome, comprensibili senza rileggere il messaggio.\n"
    "3. Conserva le negazioni: se il messaggio dice che qualcosa non e' avvenuto, non e' stato osservato\n"
    "   o non e' stato determinato, il fatto deve dirlo esplicitamente.\n"
    "4. Distingui le ipotesi dalle conferme: usa il campo \"kind\" con uno di questi valori:\n"
    "   osservazione, ipotesi, conferma, decisione, stato, ritiro.\n"
    "5. Non unire in un solo fatto informazioni provenienti da messaggi diversi.\n"
    "6. Non modificare, non aggiornare e non cancellare i fatti gia' estratti: aggiungi soltanto i fatti\n"
    "   ricavati dai messaggi nuovi, anche quando contraddicono un fatto precedente.\n"
    "7. Per ogni fatto indica i messaggi da cui proviene, usando esattamente gli identificatori mostrati\n"
    "   fra parentesi quadre.\n"
    "\n"
    "Rispondi soltanto con un array JSON, senza testo prima o dopo. Ogni elemento ha questa forma:\n"
    "{\"text\": \"...\", \"source_message_ids\": [\"...\"], \"kind\": \"...\", \"negated\": true}\n"
)

NO_PREVIOUS_FACTS = "(nessun fatto estratto in precedenza: questa e' la prima sessione)"


# --------------------------------------------------------------------------
# Costruzione dei prompt
# --------------------------------------------------------------------------

def format_previous_facts(facts):
    if not facts:
        return NO_PREVIOUS_FACTS
    return "\n".join(
        "[%s] %s (da: %s)" % (fact["fact_id"], fact["text"], ", ".join(fact["source_message_ids"]))
        for fact in facts
    )


def format_messages(messages):
    return "\n".join("[%s] %s" % (m["message_id"], m["content"]) for m in messages)


def build_session_prompt(session_messages, previous_facts):
    return (
        "Istruzioni:\n"
        "%s\n"
        "\n"
        "Fatti gia' estratti nelle conversazioni precedenti (solo per contesto, non vanno ripetuti):\n"
        "%s\n"
        "\n"
        "Messaggi nuovi da elaborare:\n"
        "%s"
    ) % (EXTRACTION_INSTRUCTIONS, format_previous_facts(previous_facts), format_messages(session_messages))


def build_prompts(scenario):
    """Un prompt per sessione, in ordine cronologico.

    Il prompt della sessione k contiene i messaggi della sola sessione k e i
    fatti gia' estratti dalle sessioni 1..k-1. Nessuna sessione futura.
    """
    prompts = []
    messages_by_session = {}
    for entry in rq2.user_messages(scenario):
        messages_by_session.setdefault(entry["session_id"], []).append(entry)

    for session in rq2.sessions_in_order(scenario):
        session_id = session["session_id"]
        messages = messages_by_session.get(session_id, [])
        if not messages:
            continue
        prompts.append(
            {
                "scenario_id": scenario["scenario_id"],
                "session_id": session_id,
                "session_order": session["order"],
                "message_ids": [m["message_id"] for m in messages],
                "messages": messages,
            }
        )
    return prompts


# --------------------------------------------------------------------------
# Lettura della risposta del modello
# --------------------------------------------------------------------------

FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def parse_facts(answer):
    """Legge l'array JSON prodotto dal modello. Restituisce (fatti, errore)."""
    if not answer:
        return [], "risposta vuota"
    text = answer.strip()
    match = FENCE_RE.search(text)
    if match:
        text = match.group(1).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1 or end < start:
        return [], "nessun array JSON nella risposta: %s" % text[:200]
    try:
        parsed = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        return [], "JSON non valido (%s): %s" % (exc, text[:200])
    if not isinstance(parsed, list):
        return [], "atteso un array JSON"
    return parsed, None


def normalize(raw_facts, scenario_id, session, allowed_message_ids, counter):
    """Trasforma l'uscita del modello in fatti con identificatore e ordine.

    La provenienza viene controllata ma non corretta: un fatto che cita un
    messaggio non ammesso viene salvato con `provenance_valid: false`.
    """
    prefix = "SC%s" % scenario_id.split("_")[-1]
    facts = []
    for raw in raw_facts:
        if not isinstance(raw, dict):
            continue
        counter += 1
        sources = raw.get("source_message_ids") or []
        if isinstance(sources, str):
            sources = [sources]
        sources = [str(s).strip() for s in sources]
        unknown = [s for s in sources if s not in allowed_message_ids]
        kind = str(raw.get("kind", "")).strip().lower()
        text = str(raw.get("text", "")).strip()
        facts.append(
            {
                "fact_id": "%s-F%03d" % (prefix, counter),
                "scenario_id": scenario_id,
                "session_id": session["session_id"],
                "session_order": session["session_order"],
                "order": counter,
                "text": text,
                "source_message_ids": sources,
                "kind": kind if kind in ALLOWED_KINDS else kind,
                "kind_valid": kind in ALLOWED_KINDS,
                "negated": bool(raw.get("negated", False)),
                "provenance_valid": bool(sources) and not unknown,
                "provenance_problem": (
                    None if (sources and not unknown)
                    else ("nessun messaggio sorgente" if not sources
                          else "messaggi non ammessi: %s" % ", ".join(unknown))
                ),
                "tokens": rq2.count_tokens(text),
            }
        )
    return facts, counter


# --------------------------------------------------------------------------
# Esecuzione
# --------------------------------------------------------------------------

def run(scenario, config, dry_run=False, runner=None, model=None, effort=None):
    """Estrazione sessione per sessione. Restituisce (fatti, registro)."""
    model = model or config["models"]["extraction"]["model"]
    effort = effort or config["models"]["extraction"]["effort"]

    prompts = build_prompts(scenario)
    facts = []
    log_entries = []
    counter = 0
    cwd = tempfile.mkdtemp(prefix="estrazione_") if not dry_run else None

    for prompt_entry in prompts:
        prompt = build_session_prompt(prompt_entry["messages"], facts)
        allowed = set(prompt_entry["message_ids"])
        entry = {
            "scenario_id": scenario["scenario_id"],
            "session_id": prompt_entry["session_id"],
            "session_order": prompt_entry["session_order"],
            "input_message_ids": list(prompt_entry["message_ids"]),
            "facts_in_context": [fact["fact_id"] for fact in facts],
            "prompt": prompt,
            "model_requested": model,
            "effort": effort,
        }

        if dry_run:
            entry.update({"executed": False, "model_answer": None, "model_used": None,
                          "error": None, "parse_error": None, "facts_extracted": []})
            log_entries.append(entry)
            continue

        call = runner or (lambda p: gen.call_claude(p, cwd, model, effort))
        answer, used, error = call(prompt)
        entry.update({"executed": True, "model_answer": answer, "model_used": used, "error": error})

        if error:
            entry.update({"parse_error": None, "facts_extracted": []})
            log_entries.append(entry)
            continue

        raw_facts, parse_error = parse_facts(answer)
        new_facts, counter = normalize(raw_facts, scenario["scenario_id"], prompt_entry, allowed, counter)
        facts.extend(new_facts)
        entry.update({"parse_error": parse_error, "facts_extracted": [f["fact_id"] for f in new_facts]})
        log_entries.append(entry)

    log = {
        "scenario_id": scenario["scenario_id"],
        "source_file": scenario["source_file"],
        "config_id": config["config_id"],
        "model": model,
        "effort": effort,
        "dry_run": dry_run,
        "extraction_instructions": EXTRACTION_INSTRUCTIONS,
        "sessions": log_entries,
        "fact_count": len(facts),
    }
    return facts, log


def facts_path(scenario_id, out_dir=FACTS_DIR):
    return Path(out_dir) / ("%s_facts.jsonl" % scenario_id)


def log_path(scenario_id, out_dir=FACTS_DIR, dry_run=False):
    suffix = "_extraction_prompts.json" if dry_run else "_extraction_log.json"
    return Path(out_dir) / ("%s%s" % (scenario_id, suffix))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Estrae i fatti candidati di uno scenario (architettura F).")
    parser.add_argument("--scenario", default="scenario_02", choices=list(rq2.SCENARIO_IDS))
    parser.add_argument("--dry-run", action="store_true",
                        help="costruisce e salva i prompt senza chiamare il modello")
    parser.add_argument("--out-dir", default=str(FACTS_DIR))
    parser.add_argument("--model", default=None)
    parser.add_argument("--effort", default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = rq2.load_config()
    scenario = rq2.load_scenario(args.scenario)

    facts, log = run(scenario, config, dry_run=args.dry_run, model=args.model, effort=args.effort)

    out_dir = Path(args.out_dir)
    written_log = rq2.write_json(log, log_path(args.scenario, out_dir, args.dry_run))

    print("Estrazione dei fatti — %s (%s)" % (args.scenario, scenario["title"]))
    print("modello: %s | effort: %s | %s"
          % (log["model"], log["effort"], "DRY RUN, nessuna chiamata" if args.dry_run else "chiamate reali"))
    print("-" * 78)
    for entry in log["sessions"]:
        stato = "prompt costruito" if args.dry_run else (
            "errore: %s" % entry["error"] if entry["error"]
            else ("parse: %s" % entry["parse_error"] if entry["parse_error"]
                  else "%d fatti" % len(entry["facts_extracted"]))
        )
        print("%-12s messaggi=%-28s %s"
              % (entry["session_id"], ", ".join(entry["input_message_ids"]), stato))
    print("-" * 78)
    print("Prompt e configurazione salvati in %s" % rq2.relative(written_log))

    if args.dry_run:
        print("Nessun fatto prodotto: per estrarre davvero, rieseguire senza --dry-run.")
        return 0

    written_facts = rq2.write_jsonl(facts, facts_path(args.scenario, out_dir))
    invalid = [f for f in facts if not f["provenance_valid"]]
    print("Fatti salvati in %s (%d righe)" % (rq2.relative(written_facts), len(facts)))
    if invalid:
        print("Attenzione: %d fatti con provenienza non valida, registrati e non corretti a mano." % len(invalid))
    failed = [e for e in log["sessions"] if e["error"] or e["parse_error"]]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
