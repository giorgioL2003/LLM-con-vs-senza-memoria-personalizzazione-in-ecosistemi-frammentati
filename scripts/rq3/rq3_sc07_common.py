#!/usr/bin/env python3
"""Regole condivise di RQ3 / SC07.

Tutti gli script di SC07 leggono `data/rq3/config/rq3_sc07_v1.json`, unica
fonte autoritativa di sorgente, criteri di ammissibilita', selezione,
template, domande, retriever, prompt, parametri e metriche. Questo modulo
applica quelle regole allo stesso modo in ogni fase:

  - hash e lettura/scrittura JSON/JSONL;
  - lettura dello snapshot della sorgente (tar.gz) dopo averne verificato lo
    SHA-256 rispetto a configurazione e manifest;
  - ammissibilita' di un advisory OSV, con il primo criterio non soddisfatto;
  - chiave di ordinamento deterministica e composizione degli episodi;
  - rendering di messaggi, domande e contesti;
  - retrieval Turn-level RAG: importa `retrieve` da
    `scripts/run_retrieval_pilot.py` senza copiarne o cambiarne la semantica;
  - prompt e parser dell'output `{"value": string|null}`;
  - comando Claude Code CLI (importato da `scripts/run_generation.py`),
    configurazione del modello e piano delle chiamate con riuso dei prompt
    identici.

Le funzioni che leggono l'oracle sono soltanto `load_oracle`; il runner delle
generazioni e la parte di ranking del retrieval non la invocano. Quando un
processo imposta `forbid_oracle()`, ogni tentativo di leggerla solleva
un'eccezione.

Solo libreria standard (Python >= 3.9).
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "data" / "rq3" / "config" / "rq3_sc07_v1.json"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import run_retrieval_pilot as pilot_retrieval  # noqa: E402  (semantica del pilot)
import run_generation as pilot_generation  # noqa: E402  (meccanismo di chiamata del pilot)

SPLITS = ("development", "evaluation")
CONDITIONS = ("separated", "shared_interleaved")

GHSA_RE = re.compile(r"GHSA(-[23456789cfghjmpqrvwx]{4}){3}", re.IGNORECASE)
CVE_RE = re.compile(r"CVE-\d{4}-\d{3,}", re.IGNORECASE)
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f  ]")

# Stringhe che non devono mai comparire in un prompt: rimandano alla fonte.
FORBIDDEN_PROMPT_SUBSTRINGS = (
    "http://",
    "https://",
    "github.com/advisories",
    "advisory-database",
    "github-reviewed",
    "nvd.nist.gov",
    "osv.dev",
)

# Chiavi dell'oracle o della provenienza che non devono stare in una richiesta.
ORACLE_KEYS = frozenset({
    "expected_value",
    "evidence_message_id",
    "ghsa_id",
    "aliases",
    "source_path",
    "source_file_sha256",
    "osv_fields",
    "provenance",
    "retrieval_success",
})


# --------------------------------------------------------------------------
# Configurazione, percorsi, hash
# --------------------------------------------------------------------------

def load_config(path=CONFIG_PATH):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def design_dir(config, repo_root=REPO_ROOT):
    return Path(repo_root) / config["artifacts"]["design_dir"]


def results_dir(config, split, repo_root=REPO_ROOT):
    return Path(repo_root) / config["artifacts"]["results_dir"] / split


def source_dir(config, repo_root=REPO_ROOT):
    return Path(repo_root) / config["source"]["source_dir"]


def snapshot_path(config, repo_root=REPO_ROOT):
    return source_dir(config, repo_root) / config["source"]["snapshot_filename"]


def manifest_path(config, repo_root=REPO_ROOT):
    return Path(repo_root) / config["source"]["manifest_path"]


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_text(text):
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path, repo_root=REPO_ROOT):
    try:
        return str(Path(path).resolve().relative_to(Path(repo_root).resolve()))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------
# JSON e JSONL
# --------------------------------------------------------------------------

def read_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_jsonl(path):
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
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
    """Append riga per riga con flush e fsync: resiste alle interruzioni."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = None

    def __enter__(self):
        self._handle = self.path.open("a", encoding="utf-8")
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        return False

    def write(self, row):
        self._handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())


# --------------------------------------------------------------------------
# Snapshot della sorgente
# --------------------------------------------------------------------------

def verify_snapshot(config, repo_root=REPO_ROOT):
    """Verifica che snapshot, manifest e configurazione coincidano.

    Ritorna il manifest. Solleva se manca qualcosa o se un hash differisce:
    in quel caso nessun record puo' essere selezionato.
    """
    source = config["source"]
    path = snapshot_path(config, repo_root)
    mpath = manifest_path(config, repo_root)
    if not path.exists():
        raise FileNotFoundError(f"snapshot mancante: {rel(path, repo_root)}")
    if not mpath.exists():
        raise FileNotFoundError(f"manifest mancante: {rel(mpath, repo_root)}")
    manifest = read_json(mpath)
    actual = sha256_file(path)
    expected_config = source.get("snapshot_sha256")
    if not expected_config:
        raise ValueError("snapshot_sha256 non registrato nella configurazione")
    if actual != expected_config:
        raise ValueError(f"SHA-256 snapshot diverso dalla configurazione: {actual} != {expected_config}")
    if manifest.get("snapshot", {}).get("sha256") != actual:
        raise ValueError("SHA-256 snapshot diverso dal manifest")
    if manifest.get("commit") != source["commit"]:
        raise ValueError("commit del manifest diverso da quello della configurazione")
    if manifest.get("repository_url") != source["repository_url"]:
        raise ValueError("repository del manifest diverso da quello della configurazione")
    license_path = source_dir(config, repo_root) / manifest["license"]["filename"]
    if sha256_file(license_path) != manifest["license"]["sha256"]:
        raise ValueError("SHA-256 della licenza diverso dal manifest")
    return manifest


def iter_snapshot_advisories(path, subtree):
    """Itera `(percorso nel repository, bytes)` dei JSON sotto `subtree`.

    Il primo componente del percorso nell'archivio e' la radice
    `advisory-database-<commit>/` e viene rimosso. L'ordine e' quello,
    ordinato, in cui lo snapshot e' stato costruito.
    """
    prefix = subtree.rstrip("/") + "/"
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            if not member.isfile():
                continue
            repo_path = member.name.split("/", 1)[-1]
            if repo_path.startswith(prefix) and repo_path.endswith(".json"):
                yield repo_path, archive.extractfile(member).read()


def build_deterministic_tar_gz(entries, root_name, out_path):
    """Scrive un tar.gz riproducibile.

    `entries` e' una lista di `(percorso relativo, bytes)`. Membri ordinati,
    mtime/uid/gid a zero, permessi 0644, gzip senza timestamp: gli stessi file
    producono sempre lo stesso SHA-256.
    """
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for rel_path, data in sorted(entries, key=lambda item: item[0]):
            info = tarfile.TarInfo(name=f"{root_name}/{rel_path}")
            info.size = len(data)
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as gz:
            gz.write(buffer.getvalue())
    return sha256_file(out_path)


# --------------------------------------------------------------------------
# Ammissibilita'
# --------------------------------------------------------------------------

def render_range(config, introduced, fixed):
    rules = config["conversation"]["range_rendering"]
    if introduced == "0":
        return rules["introduced_zero"].format(fixed=fixed)
    return rules["otherwise"].format(introduced=introduced, fixed=fixed)


def _usable_value(value):
    return (
        isinstance(value, str)
        and value != ""
        and value == value.strip()
        and value == unicodedata.normalize("NFC", value)
        and not CONTROL_RE.search(value)
    )


def is_malware(advisory, config):
    rules = config["eligibility"]
    cwes = (advisory.get("database_specific") or {}).get("cwe_ids") or []
    if rules["malware_cwe"] in cwes:
        return True
    summary = advisory.get("summary") or ""
    return re.search(rules["malware_summary_pattern"], summary, re.IGNORECASE) is not None


def extract_facts(advisory, config):
    """Fatti destinati ai messaggi. Assume che i criteri 1-7 siano passati."""
    affected = advisory["affected"][0]
    events = affected["ranges"][0]["events"]
    introduced = events[0]["introduced"]
    fixed = events[1]["fixed"]
    return {
        "package": affected["package"]["name"],
        "ecosystem": affected["package"]["ecosystem"],
        "severity": advisory["database_specific"]["severity"],
        "introduced": introduced,
        "fixed_version": fixed,
        "vulnerable_range": render_range(config, introduced, fixed),
    }


def render_activity_messages(config, activity, facts):
    """I due messaggi di un'attivita': {turno: testo}."""
    templates = config["conversation"]["message_templates"][activity]
    return {
        int(turn): spec["text"].format(**facts)
        for turn, spec in templates.items()
    }


def expected_values_for_activity(config, activity, facts):
    """{fatto: (valore atteso, turno dell'evidenza)} per un'attivita'."""
    result = {}
    for item in config["questions"]["items"]:
        if item["activity"] == activity:
            result[item["fact"]] = (facts[item["fact"]], item["evidence_turn"])
    return result


def unique_value_problems(config, facts):
    """Violazioni della regola 'valore atteso in un solo messaggio bersaglio'.

    Controlla tutte e tre le attivita' possibili, perche' l'attivita' viene
    assegnata soltanto dopo l'ordinamento.
    """
    problems = []
    for activity in config["conversation"]["message_templates"]:
        messages = render_activity_messages(config, activity, facts)
        for fact, (value, turn) in expected_values_for_activity(config, activity, facts).items():
            containing = sorted(t for t, text in messages.items() if value in text)
            if containing != [turn]:
                problems.append(f"{activity}.{fact}: '{value}' nei turni {containing}, atteso [{turn}]")
    return problems


def check_eligibility(advisory, repo_path, config):
    """Ritorna `(None, None)` se ammissibile, altrimenti `(criterio, dettaglio)`.

    I criteri sono verificati nell'ordine di `eligibility.criteria_order`;
    si registra il primo non soddisfatto.
    """
    rules = config["eligibility"]
    subtree = config["source"]["subtree"].rstrip("/") + "/"
    database = advisory.get("database_specific") or {}

    if not repo_path.startswith(subtree) or database.get("github_reviewed") is not True:
        return "not_github_reviewed", f"github_reviewed={database.get('github_reviewed')!r}"
    if advisory.get("withdrawn"):
        return "withdrawn", f"withdrawn={advisory.get('withdrawn')}"
    if is_malware(advisory, config):
        return "malware", (advisory.get("summary") or "")[:120]

    affected = advisory.get("affected") or []
    packages = {
        ((entry.get("package") or {}).get("ecosystem"), (entry.get("package") or {}).get("name"))
        for entry in affected
    }
    if len(packages) != 1:
        return "not_exactly_one_package", f"{len(packages)} pacchetti distinti"

    ecosystem = next(iter(packages))[0]
    if ecosystem not in rules["ecosystems"]:
        return "ecosystem_not_in_scope", str(ecosystem)

    severity = database.get("severity")
    if not isinstance(severity, str) or severity not in rules["severity_values"]:
        return "severity_missing_or_not_categorical", repr(severity)

    if len(affected) != 1:
        return "range_not_interpretable", f"{len(affected)} voci affected per lo stesso pacchetto"
    ranges = affected[0].get("ranges") or []
    if len(ranges) != 1:
        return "range_not_interpretable", f"{len(ranges)} intervalli"
    if ranges[0].get("type") not in rules["range_types"]:
        return "range_not_interpretable", f"tipo {ranges[0].get('type')!r}"
    events = ranges[0].get("events") or []
    shape = [sorted(event) for event in events if isinstance(event, dict)]
    if shape != [["introduced"], ["fixed"]]:
        return "range_not_interpretable", f"eventi {shape}"
    introduced, fixed = events[0]["introduced"], events[1]["fixed"]
    if introduced == fixed:
        return "range_not_interpretable", "introduced == fixed"

    name = affected[0]["package"].get("name")
    for label, value in (("package", name), ("severity", severity),
                         ("introduced", introduced), ("fixed", fixed)):
        if not _usable_value(value):
            return "message_value_not_usable", f"{label}={value!r}"

    facts = extract_facts(advisory, config)
    problems = unique_value_problems(config, facts)
    if problems:
        return "expected_value_not_unique_in_target_messages", "; ".join(problems)
    return None, None


# --------------------------------------------------------------------------
# Selezione deterministica
# --------------------------------------------------------------------------

def rank_key(seed, ecosystem, ghsa_id):
    return sha256_text(f"{seed}:{ecosystem}:{ghsa_id}")


def episode_id(config, number):
    return config["selection"]["episode_id_format"].format(number=number)


def episode_plan(config):
    """Lista ordinata di `(split, episode_id, ecosistema)` da riempire."""
    selection = config["selection"]
    plan = []
    dev = selection["development"]
    for offset, ecosystem in enumerate(dev["ecosystems"]):
        plan.append(("development", episode_id(config, dev["first_episode_number"] + offset), ecosystem))
    if len(dev["ecosystems"]) != dev["episode_count"]:
        raise ValueError("development.ecosystems non coincide con episode_count")
    evaluation = selection["evaluation"]
    number = evaluation["first_episode_number"]
    for ecosystem in config["eligibility"]["ecosystems"]:
        for _ in range(evaluation["episodes_per_ecosystem"]):
            plan.append(("evaluation", episode_id(config, number), ecosystem))
            number += 1
    if sum(1 for split, _, _ in plan if split == "evaluation") != evaluation["episode_count"]:
        raise ValueError("episodes_per_ecosystem x ecosistemi diverso da episode_count")
    return plan


class InsufficientStratum(RuntimeError):
    """Uno strato non contiene abbastanza candidati: la preparazione si ferma."""


def select_episodes(candidates, config):
    """Assegna i candidati agli episodi secondo la configurazione.

    `candidates` sono righe con almeno `ghsa_id`, `ecosystem`, `package`,
    `rank_key`. Ritorna le righe di selezione nell'ordine di estrazione.
    """
    activities = [activity["key"] for activity in config["conversation"]["activities"]]
    pools = {}
    for row in sorted(candidates, key=lambda r: (r["ecosystem"], r["rank_key"], r["ghsa_id"])):
        pools.setdefault(row["ecosystem"], []).append(row)
    used = set()
    selection = []
    for split, ep_id, ecosystem in episode_plan(config):
        pool = pools.get(ecosystem, [])
        chosen_packages = set()
        for position, activity in enumerate(activities, 1):
            pick = None
            for row in pool:
                if row["ghsa_id"] in used:
                    continue
                if row["package"].casefold() in chosen_packages:
                    continue
                pick = row
                break
            if pick is None:
                raise InsufficientStratum(
                    f"strato {ecosystem}: candidati insufficienti per {ep_id} ({split}), "
                    f"posizione {position}"
                )
            used.add(pick["ghsa_id"])
            chosen_packages.add(pick["package"].casefold())
            selection.append({
                "split": split,
                "episode_id": ep_id,
                "ecosystem": ecosystem,
                "activity": activity,
                "position": position,
                "ghsa_id": pick["ghsa_id"],
                "package": pick["package"],
                "rank_key": pick["rank_key"],
                "rank_in_ecosystem": pool.index(pick) + 1,
                "source_path": pick["source_path"],
                "source_file_sha256": pick["source_file_sha256"],
            })
    return selection


# --------------------------------------------------------------------------
# Episodi, domande, oracle
# --------------------------------------------------------------------------

def message_id(config, ep_id, order):
    return config["conversation"]["message_id_format"].format(episode_id=ep_id, order=order)


def question_id(config, ep_id, number):
    return config["questions"]["question_id_format"].format(episode_id=ep_id, number=number)


def build_episode(config, split, ep_id, ecosystem, facts_by_activity):
    """Conversazione interlacciata: soli messaggi utente, nessuna provenienza."""
    messages = []
    rendered = {
        activity: render_activity_messages(config, activity, facts)
        for activity, facts in facts_by_activity.items()
    }
    for order, (activity, turn) in enumerate(config["conversation"]["interleaving_order"], 1):
        messages.append({
            "message_id": message_id(config, ep_id, order),
            "order": order,
            "role": "user",
            "activity": activity,
            "activity_turn": turn,
            "content": rendered[activity][turn],
        })
    return {
        "episode_id": ep_id,
        "split": split,
        "ecosystem": ecosystem,
        "messages": messages,
    }


def build_questions(config, split, ep_id):
    return [
        {
            "question_id": question_id(config, ep_id, item["number"]),
            "episode_id": ep_id,
            "split": split,
            "number": item["number"],
            "question_type": item["question_type"],
            "activity": item["activity"],
            "text": item["text"],
        }
        for item in config["questions"]["items"]
    ]


# --------------------------------------------------------------------------
# Retrieval Turn-level RAG
# --------------------------------------------------------------------------

def accessible_corpus(episode, activity, condition):
    """Messaggi utente accessibili al retriever, in ordine di conversazione.

    Usa soltanto la conversazione e l'attivita' della domanda: nessun dato
    dell'oracle. I campi `session_order`/`message_order` sono quelli richiesti
    dal retriever del pilot (una sola sessione per episodio).
    """
    if condition not in CONDITIONS:
        raise ValueError(f"condizione sconosciuta: {condition}")
    corpus = []
    for message in episode["messages"]:
        if message["role"] != pilot_retrieval.INDEXED_ROLE:
            continue
        if condition == "separated" and message["activity"] != activity:
            continue
        corpus.append({
            "message_id": message["message_id"],
            "session_order": 1,
            "message_order": message["order"],
            "content": message["content"],
        })
    corpus.sort(key=lambda document: (document["session_order"], document["message_order"]))
    return corpus


def rank_corpus(query, corpus, top_k):
    """Ranking completo e primi `top_k` con la funzione del pilot.

    Il ranking completo serve solo a salvare i punteggi di tutto il corpus:
    si verifica che i suoi primi `top_k` coincidano con la chiamata a
    `top_k` del pilot.
    """
    full = pilot_retrieval.retrieve(query, corpus, top_k=len(corpus))
    top = pilot_retrieval.retrieve(query, corpus, top_k=top_k)
    if [d["message_id"] for d in full[:top_k]] != [d["message_id"] for d in top]:
        raise AssertionError("ranking completo e top-k del pilot non coincidono")
    return full, top


# --------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------

def render_context(config, retrieved_contents):
    prompt = config["prompt"]
    return prompt["context_line_separator"].join(
        prompt["context_line_format"].format(rank=rank, content=content)
        for rank, content in enumerate(retrieved_contents, 1)
    )


def build_prompt(config, context, question_text):
    prompt = config["prompt"]
    return prompt["system"], prompt["user_template"].format(context=context, question=question_text)


def prompt_sha256(system, user):
    return sha256_text("SYSTEM\n" + system + "\n\nUSER\n" + user)


def cli_input(config, request):
    """Testo inviato su stdin a `claude --print`: system e user del prompt."""
    return config["generation"]["cli_input_template"].format(system=request["system"], user=request["user"])


def cli_command(config):
    """Comando esatto: `build_command` di `scripts/run_generation.py`."""
    params = config["generation"]["parameters"]
    return pilot_generation.build_command(params["model"], params["effort"])


def model_configuration(config):
    """Tutto cio' che, oltre al prompt, determina una generazione."""
    params = config["generation"]["parameters"]
    if params["model"] != config["model"]["model_id"]:
        raise ValueError("generation.parameters.model diverso da model.model_id")
    return {
        "model_id": config["model"]["model_id"],
        "access_channel": config["model"]["access_channel"],
        "fallback_model": config["model"]["fallback_model"],
        "parameters": params,
        "command": cli_command(config),
        "cli_input_template": config["generation"]["cli_input_template"],
    }


def model_config_sha256(config):
    return sha256_text(json.dumps(model_configuration(config), sort_keys=True, ensure_ascii=False))


def plan_calls(config, requests):
    """Piano delle generazioni: chiamate reali e celle riusate.

    Usa soltanto le richieste (mai l'oracle). Nell'ordine delle richieste, la
    prima cella di ogni gruppo `(prompt_sha256, model_config_sha256)` e' una
    chiamata reale; le altre riusano la sua risposta. Il riuso richiede che
    system e user siano identici carattere per carattere, non solo l'hash.
    """
    reuse = config["generation"]["reuse_identical_prompts"]
    mc = model_config_sha256(config)
    primary = {}
    plan = []
    for request in requests:
        if prompt_sha256(request["system"], request["user"]) != request["prompt_sha256"]:
            raise ValueError(f"prompt_sha256 non coerente: {request['request_id']}")
        key = (request["prompt_sha256"], mc)
        entry = {
            "request_id": request["request_id"],
            "split": request["split"],
            "condition": request["condition"],
            "question_id": request["question_id"],
            "prompt_sha256": request["prompt_sha256"],
            "model_config_sha256": mc,
        }
        first = primary.get(key) if reuse["enabled"] else None
        if first is None:
            primary[key] = request
            plan.append({**entry, "generation_kind": "model_call", "reused_from_request_id": None})
            continue
        if first["system"] != request["system"] or first["user"] != request["user"]:
            raise ValueError(f"stesso hash ma prompt diverso: {request['request_id']}")
        plan.append({**entry, "generation_kind": "reused_identical_prompt",
                     "reused_from_request_id": first["request_id"]})
    return plan


def call_plan_path(config, split, repo_root=REPO_ROOT):
    return design_dir(config, repo_root) / f"{split}_call_plan.jsonl"


def request_id(split, condition, qid):
    return f"{split}|{condition}|{qid}"


def cell_id(split, model_id, condition, qid):
    return f"{split}|{model_id}|{condition}|{qid}"


def prompt_leaks(text):
    """Indicatori di fonte o provenienza presenti in un testo di prompt."""
    found = []
    if GHSA_RE.search(text):
        found.append("ghsa_id")
    if CVE_RE.search(text):
        found.append("cve_id")
    lowered = text.lower()
    for token in FORBIDDEN_PROMPT_SUBSTRINGS:
        if token in lowered:
            found.append(token)
    return found


# --------------------------------------------------------------------------
# Oracle (mai letto dal runner ne' dal ranking del retrieval)
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


def oracle_path(config, split, repo_root=REPO_ROOT):
    return design_dir(config, repo_root) / f"{split}_oracle.jsonl"


def requests_path(config, split, repo_root=REPO_ROOT):
    return design_dir(config, repo_root) / f"{split}_requests.jsonl"


def load_oracle(config, split, repo_root=REPO_ROOT):
    if _ORACLE_FORBIDDEN:
        raise OracleAccessError("lettura dell'oracle vietata in questa fase")
    return read_jsonl(oracle_path(config, split, repo_root))


# --------------------------------------------------------------------------
# Normalizzazione e parser dell'output
# --------------------------------------------------------------------------

def normalize_value(value, config):
    rules = config["evaluation"]["normalization"]
    text = value
    if rules.get("unicode_normalization"):
        text = unicodedata.normalize(rules["unicode_normalization"], text)
    if rules.get("strip_outer_whitespace", True):
        text = text.strip()
    if not rules.get("case_sensitive", True):
        text = text.casefold()
    return text


_MISSING = object()


def parse_model_output(text):
    """Parser rigoroso di `{"value": string|null}`.

    Ritorna `(ok, value, errore)`. Nessuna correzione: blocchi di codice,
    testo extra, chiavi aggiuntive o tipi diversi sono errori di formato.
    """
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
    value = parsed.get("value", _MISSING)
    if value is _MISSING:
        return False, None, "missing_value_key"
    if set(parsed) != {"value"}:
        extra = ",".join(sorted(set(parsed) - {"value"}))
        return False, None, f"extra_keys:{extra}"
    if value is not None and not isinstance(value, str):
        return False, None, f"value_type:{type(value).__name__}"
    return True, value, None
