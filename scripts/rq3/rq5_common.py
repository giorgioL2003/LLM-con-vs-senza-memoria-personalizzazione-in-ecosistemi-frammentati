#!/usr/bin/env python3
"""Funzioni condivise di RQ5 / SC06.

Questo modulo tiene in un posto solo le regole che tutti gli script di RQ5
devono applicare allo stesso modo:

  - leggere `data/rq3/config/rq5_sc06_v1.json`, che e' l'unica fonte
    autoritativa di split, prompt, costruzione dei contesti, modelli,
    parametri e metriche;
  - verificare gli SHA-256 delle quattro sorgenti dichiarate;
  - costruire i blocchi di contesto e il loro ordine con la regola esatta
    della configurazione;
  - identificare in modo univoco richieste (indipendenti dal modello) e celle
    (una per modello);
  - normalizzare e validare l'output del modello senza correggerlo.

Regole della configurazione applicate qui:

  - `block_format`     -> `{case_alias}.\\n- {field_label}: {valori}`
  - `distractor_rule`  -> per ogni altro caso si usa il campo della domanda se
                          presente, altrimenti il primo campo disponibile in
                          ordine lessicografico;
  - `ordering_rule`    -> i blocchi inclusi sono ordinati per
                          SHA-256(builder_seed + ':' + question_id + ':' +
                          case_alias).

Dettaglio non fissato dalla configurazione e quindi dichiarato qui, non
scelto altrove: i blocchi vengono uniti da una riga vuota (`\\n\\n`), come nel
rendering degli episodi in `data/rq3/sc06_design_v1/ESEMPIO.md`. Il valore e'
scritto in `build_manifest.json` sotto `block_separator`.

Il modulo non chiama mai Ollama e non contiene metriche: le sole funzioni che
toccano l'oracle sono `load_oracle` e `load_case_mapping`, che il runner delle
generazioni non deve invocare.

Solo libreria standard.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "data" / "rq3" / "config" / "rq5_sc06_v1.json"

DATA_DIR = REPO_ROOT / "data" / "rq3"
RESULTS_ROOT = REPO_ROOT / "results" / "rq5" / "sc06"

# Ogni versione della configurazione ha le proprie directory: gli artefatti di
# una versione non vengono mai sovrascritti da un'altra. La v1.0 e' nata prima
# di questa regola e conserva i nomi originali.
LEGACY_ARTIFACT_SLUG = {"rq5-sc06-v1.0": "v1"}

INPUTS_DIR = DATA_DIR / "sc06_rq5_v1"
RESULTS_DIR = RESULTS_ROOT / "v1"

SPLITS = ("development", "evaluation")
CONDITIONS = ("sufficient", "insufficient")

# Separatore fra blocchi di contesto: non fissato dalla configurazione.
BLOCK_SEPARATOR = "\n\n"

# Le domande sono generate da `prepare_sc06_design.py` con questa forma fissa.
# Serve a ricostruire caso bersaglio e campo senza leggere l'oracle.
QUESTION_PATTERN = re.compile(
    r"^Per (?P<alias>Caso [A-Z]), quali valori erano stati riportati "
    r"nel campo «(?P<label>.+?)»\?"
)


# --------------------------------------------------------------------------
# Configurazione e sorgenti
# --------------------------------------------------------------------------

def load_config(path=CONFIG_PATH):
    """Legge la configurazione autoritativa."""
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def version_slug(config):
    """`rq5-sc06-v1.1` -> `v1_1`; la v1.0 conserva il nome storico `v1`."""
    config_id = config["config_id"]
    if config_id in LEGACY_ARTIFACT_SLUG:
        return LEGACY_ARTIFACT_SLUG[config_id]
    match = re.search(r"-(v[0-9][0-9.]*)$", config_id)
    if not match:
        raise ValueError(f"config_id senza versione riconoscibile: {config_id}")
    return match.group(1).replace(".", "_")


def inputs_dir(config, repo_root=REPO_ROOT):
    """Directory degli input della versione indicata dalla configurazione."""
    return repo_root / "data" / "rq3" / f"sc06_rq5_{version_slug(config)}"


def results_dir(config, repo_root=REPO_ROOT):
    """Directory dei risultati della versione indicata dalla configurazione."""
    return repo_root / "results" / "rq5" / "sc06" / version_slug(config)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_entries(config):
    """Le quattro sorgenti dichiarate: (nome, percorso assoluto, sha atteso)."""
    source = config["source"]
    names = ("episodes", "queries", "oracle", "case_mapping")
    entries = []
    for name in names:
        rel = source[f"{name}_path"]
        entries.append((name, REPO_ROOT / rel, source[f"{name}_sha256"], rel))
    return entries


def verify_sources(config, repo_root=REPO_ROOT):
    """Verifica gli SHA-256 delle sorgenti. Solleva se uno non corrisponde."""
    verified = {}
    for name, path, expected, rel in source_entries(config):
        path = repo_root / rel
        if not path.exists():
            raise FileNotFoundError(f"sorgente mancante: {rel}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(
                f"SHA-256 diverso per {rel}: atteso {expected}, trovato {actual}"
            )
        verified[name] = {"path": rel, "sha256": actual}
    return verified


# --------------------------------------------------------------------------
# Lettura e scrittura JSONL
# --------------------------------------------------------------------------

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
    """Scrittura completa di un file JSONL (chiavi ordinate, ASCII)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def dump_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class JsonlAppender:
    """Append incrementale, resistente a interruzioni.

    Ogni riga viene scritta, svuotata dal buffer e sincronizzata su disco: se
    il processo viene interrotto, le celle gia' concluse restano leggibili e
    `--resume` puo' ripartire da li'.
    """

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
        import os

        self._handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
        self._handle.flush()
        os.fsync(self._handle.fileno())


# --------------------------------------------------------------------------
# Split
# --------------------------------------------------------------------------

def episode_number(episode_id):
    """`SC06-E007` -> 7."""
    match = re.search(r"E(\d+)$", episode_id)
    if not match:
        raise ValueError(f"episode_id non riconosciuto: {episode_id}")
    return int(match.group(1))


def split_bounds(config):
    """Estremi degli episodi dei due split, letti dalla configurazione."""
    bounds = {}
    for split in SPLITS:
        spec = config["split"][split]["episodes"]
        numbers = [int(part) for part in re.findall(r"E(\d+)", spec)]
        if len(numbers) != 2:
            raise ValueError(f"intervallo di episodi non riconosciuto: {spec}")
        bounds[split] = (min(numbers), max(numbers))
    return bounds


def split_of(episode_id, config):
    number = episode_number(episode_id)
    for split, (low, high) in split_bounds(config).items():
        if low <= number <= high:
            return split
    raise ValueError(f"episodio fuori da entrambi gli split: {episode_id}")


# --------------------------------------------------------------------------
# Identificatori
# --------------------------------------------------------------------------

def request_id(split, condition, question_id):
    """Identificatore della richiesta, indipendente dal modello."""
    return f"{split}|{condition}|{question_id}"


def cell_id(split, model_tag, condition, question_id):
    """Identificatore della cella: split, tag del modello, condizione, domanda."""
    return f"{split}|{model_tag}|{condition}|{question_id}"


def prompt_sha256(system, user):
    """Hash del prompt effettivo: stesso valore per i due modelli."""
    return sha256_text("SYSTEM\n" + system + "\n\nUSER\n" + user)


# --------------------------------------------------------------------------
# Costruzione dei contesti
# --------------------------------------------------------------------------

def parse_question(question, config):
    """Ricava (case_alias, field_path) dal testo della domanda.

    Serve per costruire e per controllare il contesto senza leggere l'oracle:
    l'etichetta del campo e' gia' nella domanda e la mappa etichetta->campo
    della configurazione e' biunivoca.
    """
    match = QUESTION_PATTERN.match(question)
    if not match:
        raise ValueError(f"domanda non riconosciuta: {question[:80]}")
    labels = config["context_builder"]["field_labels"]
    inverse = {label: field for field, label in labels.items()}
    if len(inverse) != len(labels):
        raise ValueError("le etichette dei campi non sono univoche")
    label = match.group("label")
    if label not in inverse:
        raise ValueError(f"etichetta di campo sconosciuta: {label}")
    return match.group("alias"), inverse[label]


def render_block(config, case_alias, field, values):
    """Un blocco di contesto secondo `block_format`."""
    labels = config["context_builder"]["field_labels"]
    return config["context_builder"]["block_format"].format(
        case_alias=case_alias,
        field_label=labels[field],
        semicolon_separated_values="; ".join(values),
    )


def distractor_field(fields_of_case, queried_field):
    """Campo del distrattore secondo `distractor_rule`."""
    if queried_field in fields_of_case:
        return queried_field
    available = sorted(fields_of_case)
    if not available:
        raise ValueError("caso senza campi disponibili: distrattore impossibile")
    return available[0]


def order_key(config, question_id, case_alias):
    """Chiave d'ordinamento dei blocchi secondo `ordering_rule`."""
    seed = config["context_builder"]["builder_seed"]
    return sha256_text(f"{seed}:{question_id}:{case_alias}")


def build_context(config, question_id, target_alias, field, episode_cases, condition):
    """Costruisce il contesto di una domanda in una delle due condizioni.

    `episode_cases` e' una mappa `case_alias -> {field_path: [valori]}` dei tre
    casi dell'episodio (da `case_mapping.jsonl`: fatti, non oracle).

    Ritorna `(testo, blocchi)` dove ogni blocco riporta alias, campo, valori e
    ruolo (`target` o `distractor`).
    """
    if condition not in CONDITIONS:
        raise ValueError(f"condizione sconosciuta: {condition}")
    if target_alias not in episode_cases:
        raise ValueError(f"caso bersaglio assente dall'episodio: {target_alias}")

    blocks = []
    if condition == "sufficient":
        target_values = episode_cases[target_alias].get(field)
        if not target_values:
            raise ValueError(
                f"{question_id}: il caso bersaglio non ha valori per {field}"
            )
        blocks.append({
            "case_alias": target_alias,
            "field": field,
            "values": list(target_values),
            "role": "target",
        })
    # I distrattori sono identici nelle due condizioni.
    for alias in sorted(episode_cases):
        if alias == target_alias:
            continue
        chosen = distractor_field(episode_cases[alias], field)
        blocks.append({
            "case_alias": alias,
            "field": chosen,
            "values": list(episode_cases[alias][chosen]),
            "role": "distractor",
        })

    blocks.sort(key=lambda block: order_key(config, question_id, block["case_alias"]))
    text = BLOCK_SEPARATOR.join(
        render_block(config, b["case_alias"], b["field"], b["values"]) for b in blocks
    )
    return text, blocks


def build_prompt(config, context, question):
    """System e user secondo `prompt.system` e `prompt.user_template`."""
    system = config["prompt"]["system"]
    user = config["prompt"]["user_template"].format(context=context, question=question)
    return system, user


def chat_payload(config, model_tag, system, user):
    """Corpo della richiesta a `/api/chat`, con schema e opzioni dichiarati."""
    runtime = config["runtime"]
    return {
        "model": model_tag,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": runtime["stream"],
        "keep_alive": runtime["keep_alive"],
        "format": config["prompt"]["response_schema"],
        "options": dict(runtime["options"]),
    }


# --------------------------------------------------------------------------
# Sorgenti di dati (l'oracle non va letto dal runner delle generazioni)
# --------------------------------------------------------------------------

def load_queries(config, repo_root=REPO_ROOT):
    return read_jsonl(repo_root / config["source"]["queries_path"])


def load_case_mapping(config, repo_root=REPO_ROOT):
    return read_jsonl(repo_root / config["source"]["case_mapping_path"])


def load_oracle(config, repo_root=REPO_ROOT):
    return read_jsonl(repo_root / config["source"]["oracle_path"])


def load_episodes(config, repo_root=REPO_ROOT):
    return read_jsonl(repo_root / config["source"]["episodes_path"])


def cases_by_episode(case_mapping_rows):
    """`episode_id -> {case_alias: {field: [valori]}}`, solo fatti dei casi."""
    grouped = {}
    for row in case_mapping_rows:
        grouped.setdefault(row["episode_id"], {})[row["case_alias"]] = {
            field: list(values) for field, values in row["answerable_fields"].items()
        }
    return grouped


# --------------------------------------------------------------------------
# Normalizzazione e validazione dell'output
# --------------------------------------------------------------------------

def normalize_value(value, config):
    """NFC e rimozione dei soli spazi esterni, secondo `evaluation.normalization`."""
    rules = config["evaluation"]["normalization"]
    text = value
    if rules.get("unicode_normalization"):
        text = unicodedata.normalize(rules["unicode_normalization"], text)
    if rules.get("strip_outer_whitespace", True):
        text = text.strip()
    if not rules.get("case_sensitive", True):
        text = text.casefold()
    return text


def normalize_values(values, config):
    """Insieme normalizzato: ordine e duplicati non contano."""
    return {normalize_value(value, config) for value in values}


def parse_model_output(content, config):
    """Valida l'output grezzo contro lo schema dichiarato.

    Ritorna `(values, errore)`: `values` e' la lista originale se l'output e'
    conforme, altrimenti `None` e `errore` dice perche'. Non corregge nulla e
    non riprova: un output non conforme resta un errore osservato.
    """
    rules = config["evaluation"]["normalization"]
    if content is None:
        return None, "no_content"
    if not isinstance(content, str):
        return None, "content_not_string"
    text = content.strip()
    if not text:
        return None, "empty_content"
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None, "not_json"
    if not isinstance(parsed, dict):
        return None, "not_json_object"
    if "values" not in parsed:
        return None, "missing_values_key"
    if rules.get("json_object_must_have_only_values_key", True) and set(parsed) != {"values"}:
        extra = ",".join(sorted(set(parsed) - {"values"}))
        return None, f"extra_keys:{extra}"
    values = parsed["values"]
    if not isinstance(values, list):
        return None, "values_not_list"
    if rules.get("values_must_be_list_of_strings", True):
        if any(not isinstance(item, str) for item in values):
            return None, "values_not_list_of_strings"
    return values, None
