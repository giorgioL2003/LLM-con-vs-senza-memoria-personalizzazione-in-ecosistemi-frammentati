#!/usr/bin/env python3
"""Regole condivise di RQ4 / SC05 (passaggio fra modelli).

Tutti gli script di RQ4 leggono `data/rq4/config/rq4_sc05_v1.json`, unica
fonte autoritativa. Questo modulo applica le stesse regole in ogni fase:

  - verifica degli SHA-256 delle sorgenti congelate (scenario e annotazioni
    SC05, configurazione RQ5 dei modelli, moduli e configurazione del
    retriever), lette sempre in sola lettura dal repository;
  - proiezione dei soli messaggi utente, con gli identificatori originali;
  - Turn-level RAG: `message_items`, `rank_items` e `select_within_budget`
    sono importati da `scripts/rq2/rq2_common.py` (che a sua volta usa il
    TF-IDF di `scripts/run_retrieval_pilot.py`), senza copiarli;
  - prompt, hash del prompt, configurazione del modello e piano di riuso;
  - payload Ollama: `chat_payload` importato da `scripts/rq3/rq5_common.py`;
  - parser rigoroso dell'output `{"status", "answer"}`.

Le sorgenti si leggono sempre da `REPO_ROOT`; gli artefatti si scrivono sotto
`out_root` (di norma lo stesso `REPO_ROOT`, una directory temporanea nei test).

L'oracle si legge soltanto con `load_oracle`; ranking, richieste e runner non
la invocano, e con `forbid_oracle()` ogni lettura solleva un'eccezione.

Solo libreria standard.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "data" / "rq4" / "config" / "rq4_sc05_v1.json"

for _path in (REPO_ROOT / "scripts", REPO_ROOT / "scripts" / "rq2", REPO_ROOT / "scripts" / "rq3"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import rq2_common  # noqa: E402  (ranking TF-IDF e budget di RQ2, sola lettura)
import rq5_common  # noqa: E402  (payload Ollama di RQ5, sola lettura)

GROUPS = ("handoff_dependent", "post_handoff_control", "absent_information")
STATUSES = ("answered", "insufficient")

# Chiavi dell'oracle che non devono mai comparire in retrieval, richieste o runner.
ORACLE_KEYS = frozenset({
    "expected_answer", "mandatory_facts", "required_facts", "required_evidence_ids",
    "obsolete_information", "accepted_equivalents", "expected_behavior", "category",
    "required_state_meaning", "review_note", "expected_status_given_corpus",
    "expected_status_given_context", "evidence_in_corpus", "evidence_in_context",
})


# --------------------------------------------------------------------------
# Configurazione, percorsi, hash, file
# --------------------------------------------------------------------------

def load_config(path=CONFIG_PATH):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def design_dir(config, out_root=REPO_ROOT):
    return Path(out_root) / config["artifacts"]["design_dir"]


def results_dir(config, out_root=REPO_ROOT):
    return Path(out_root) / config["artifacts"]["results_dir"]


def stage_dir(config, stage, out_root=REPO_ROOT):
    return results_dir(config, out_root) / stage


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_text(text):
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def rel(path, root=REPO_ROOT):
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except ValueError:
        return str(path)


def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{number} non e' JSON valido: {error}")
    return rows


def dump_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


class JsonlAppender:
    """Append con flush e fsync: le righe gia' scritte sopravvivono a un'interruzione."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = None

    def __enter__(self):
        self._handle = self.path.open("a", encoding="utf-8")
        return self

    def __exit__(self, *exc):
        self._handle.close()
        return False

    def write(self, row):
        self._handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())


# --------------------------------------------------------------------------
# Sorgenti congelate
# --------------------------------------------------------------------------

def source_entries(config):
    """(nome, percorso relativo, sha atteso) di tutte le sorgenti in sola lettura."""
    sources = config["sources"]
    entries = [
        ("scenario", sources["scenario"]["path"], sources["scenario"]["sha256"]),
        ("annotations", sources["annotations"]["path"], sources["annotations"]["sha256"]),
        ("models_reference", sources["models_reference"]["path"], sources["models_reference"]["sha256"]),
    ]
    for name, spec in sources["retriever"].items():
        entries.append((f"retriever.{name}", spec["path"], spec["sha256"]))
    return entries


def verify_sources(config, source_root=REPO_ROOT):
    verified = {}
    for name, path, expected in source_entries(config):
        full = Path(source_root) / path
        if not full.exists():
            raise FileNotFoundError(f"sorgente mancante: {path}")
        actual = sha256_file(full)
        if actual != expected:
            raise ValueError(f"SHA-256 diverso per {path}: atteso {expected}, trovato {actual}")
        verified[name] = {"path": path, "sha256": actual}
    return verified


def models_reference_problems(config, source_root=REPO_ROOT):
    """Modelli e runtime devono coincidere con la configurazione RQ5 congelata."""
    reference = read_json(Path(source_root) / config["sources"]["models_reference"]["path"])
    problems = []
    keys = ("display_name", "ollama_tag", "ollama_digest", "quantization", "parameters")
    ours = [{k: m[k] for k in keys} for m in config["models"]]
    theirs = [{k: m[k] for k in keys} for m in reference["models"]]
    if ours != theirs:
        problems.append("models diversi dalla configurazione RQ5")
    for key in ("engine", "verified_version", "endpoint", "stream", "keep_alive",
                "one_model_loaded_at_a_time", "model_order", "warmup_requests_per_model", "options"):
        if config["runtime"][key] != reference["runtime"][key]:
            problems.append(f"runtime.{key} diverso dalla configurazione RQ5")
    return problems


def load_scenario(config, source_root=REPO_ROOT):
    with (Path(source_root) / config["sources"]["scenario"]["path"]).open(encoding="utf-8") as handle:
        raw = json.load(handle)
    return {"scenario_id": raw["scenario_id"], "sessions": raw["sessions"]}


def load_annotations(config, source_root=REPO_ROOT):
    with (Path(source_root) / config["sources"]["annotations"]["path"]).open(encoding="utf-8") as handle:
        return json.load(handle)


def phase_of(config, session_order):
    handoff = config["scenario"]["handoff"]
    if session_order in handoff["phase_a_sessions"]:
        return "A"
    if session_order in handoff["phase_b_sessions"]:
        return "B"
    raise ValueError(f"sessione fuori dalle due fasi: {session_order}")


def group_of(config, question_id):
    for group in GROUPS:
        if question_id in config["question_groups"][group]["question_ids"]:
            return group
    raise ValueError(f"domanda senza gruppo: {question_id}")


# --------------------------------------------------------------------------
# Turn-level RAG (nessuna lettura dell'oracle)
# --------------------------------------------------------------------------

def message_items(config, messages):
    """Elementi di RQ2/T dai messaggi utente proiettati, nello stesso ordine."""
    scenario = {"sessions": []}
    by_session = {}
    for message in messages:
        by_session.setdefault((message["session_order"], message["session_id"]), []).append({
            "message_id": message["message_id"], "role": "user",
            "order": message["message_order"], "content": message["content"],
        })
    for (order, session_id), items in sorted(by_session.items()):
        scenario["sessions"].append({"session_id": session_id, "order": order, "messages": items})
    return rq2_common.message_items(scenario)


def accessible_items(config, items, condition):
    sessions = set(config["conditions"][condition]["accessible_sessions"])
    return [item for item in items if item["session_order"] in sessions]


def retrieve(config, question_text, corpus_items):
    """Ranking e selezione entro il budget con le funzioni di RQ2."""
    retrieval = config["retrieval"]
    ranked = rq2_common.rank_items(question_text, corpus_items)
    selection = rq2_common.select_within_budget(
        ranked, retrieval["budget_tokens"], retrieval["min_score_exclusive"])
    return ranked, selection


# --------------------------------------------------------------------------
# Prompt, configurazione del modello, piano di riuso
# --------------------------------------------------------------------------

def render_context(config, renders):
    if not renders:
        return config["prompt"]["empty_context"]
    return config["prompt"]["context_line_separator"].join(renders)


def build_prompt(config, context, question_text):
    prompt = config["prompt"]
    return prompt["system"], prompt["user_template"].format(context=context, question=question_text)


def prompt_sha256(system, user):
    return sha256_text("SYSTEM\n" + system + "\n\nUSER\n" + user)


def model_entry(config, model_tag):
    for model in config["models"]:
        if model["ollama_tag"] == model_tag:
            return model
    raise KeyError(f"modello non previsto: {model_tag}")


def model_configuration(config, model_tag):
    """Tutto cio' che, oltre al prompt, determina una generazione di quel modello."""
    model = model_entry(config, model_tag)
    runtime = config["runtime"]
    return {
        "ollama_tag": model_tag,
        "ollama_digest": model["ollama_digest"],
        "quantization": model["quantization"],
        "engine": runtime["engine"],
        "verified_version": runtime["verified_version"],
        "endpoint": runtime["endpoint"],
        "stream": runtime["stream"],
        "keep_alive": runtime["keep_alive"],
        "options": runtime["options"],
        "format": config["prompt"]["response_schema"],
    }


def model_config_sha256(config, model_tag):
    return sha256_text(json.dumps(model_configuration(config, model_tag), sort_keys=True, ensure_ascii=False))


def chat_payload(config, model_tag, system, user):
    """Corpo di `/api/chat`: stessa funzione del runner RQ5."""
    return rq5_common.chat_payload(config, model_tag, system, user)


def request_id(condition, question_id):
    return f"{condition}|{question_id}"


def cell_id(stage, model_tag, condition, question_id):
    return f"{stage}|{model_tag}|{condition}|{question_id}"


def plan_generation(config, cells):
    """Piano delle generazioni dalle sole celle (prompt e configurazione).

    Nell'ordine delle celle, la prima di ogni gruppo `(model_tag, prompt_sha256,
    model_config_sha256)` e' una chiamata reale; le altre riusano la sua
    risposta. Il modello fa parte della chiave: nessun riuso fra Gemma e Llama.
    """
    first = {}
    plan = []
    for cell in cells:
        key = (cell["model_tag"], cell["prompt_sha256"], cell["model_config_sha256"])
        base = {"cell_id": cell["cell_id"], "model_tag": cell["model_tag"], "condition": cell["condition"],
                "question_id": cell["question_id"], "prompt_sha256": cell["prompt_sha256"],
                "model_config_sha256": cell["model_config_sha256"]}
        source = first.get(key) if config["reuse"]["enabled"] else None
        if source is None:
            first[key] = cell
            plan.append({**base, "generation_kind": "model_call", "reused_from_cell_id": None})
            continue
        if (source["system"], source["user"]) != (cell["system"], cell["user"]):
            raise ValueError(f"stesso hash ma prompt diverso: {cell['cell_id']}")
        plan.append({**base, "generation_kind": "reused_identical_prompt", "reused_from_cell_id": source["cell_id"]})
    return plan


# --------------------------------------------------------------------------
# Oracle (mai letto da ranking, richieste o runner)
# --------------------------------------------------------------------------

_ORACLE_FORBIDDEN = False


class OracleAccessError(RuntimeError):
    pass


def forbid_oracle():
    global _ORACLE_FORBIDDEN
    _ORACLE_FORBIDDEN = True


def allow_oracle():
    global _ORACLE_FORBIDDEN
    _ORACLE_FORBIDDEN = False


def load_oracle(config, out_root=REPO_ROOT):
    if _ORACLE_FORBIDDEN:
        raise OracleAccessError("lettura dell'oracle vietata in questa fase")
    return read_jsonl(design_dir(config, out_root) / "oracle.jsonl")


# --------------------------------------------------------------------------
# Parser dell'output
# --------------------------------------------------------------------------

def parse_output(text, config):
    """Parser rigoroso: `(ok, {"status", "answer"} | None, errore)`. Nessuna correzione."""
    if text is None:
        return False, None, "no_text"
    if not isinstance(text, str):
        return False, None, "text_not_string"
    stripped = text.strip()
    if not stripped:
        return False, None, "empty_text"
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return False, None, "not_json"
    if not isinstance(parsed, dict):
        return False, None, "not_json_object"
    expected = set(config["prompt"]["response_schema"]["required"])
    missing = sorted(expected - set(parsed))
    if missing:
        return False, None, "missing_keys:" + ",".join(missing)
    extra = sorted(set(parsed) - expected)
    if extra:
        return False, None, "extra_keys:" + ",".join(extra)
    allowed = config["prompt"]["response_schema"]["properties"]["status"]["enum"]
    if parsed["status"] not in allowed:
        return False, None, f"status_not_allowed:{parsed['status']!r}"
    if not isinstance(parsed["answer"], str):
        return False, None, f"answer_type:{type(parsed['answer']).__name__}"
    return True, {"status": parsed["status"], "answer": parsed["answer"]}, None


def salient_tokens(text, config):
    return re.findall(config["evaluation"]["salient_token_regex"], text or "")
