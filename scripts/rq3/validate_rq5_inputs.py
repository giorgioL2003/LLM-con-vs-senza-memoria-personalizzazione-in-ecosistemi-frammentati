#!/usr/bin/env python3
"""Validatore offline degli input di RQ5 / SC06.

Controlla quello che deve essere vero *prima* di qualsiasi chiamata ai modelli:

  - gli SHA-256 e i conteggi delle quattro sorgenti;
  - gli split disgiunti: E001-E012 solo nello sviluppo, E013-E236 solo nella
    valutazione;
  - 216 richieste indipendenti dal modello nello sviluppo e 4.032 nella
    valutazione, cioe' 432 e 8.064 celle dopo l'espansione sui due modelli;
  - l'unicita' di richieste e celle;
  - l'assenza nei prompt di risposte attese, identificativi VERIS, fonti e
    valori usati per riconoscere le confusioni;
  - lo stesso prompt, e lo stesso hash, per i due modelli sulla stessa domanda
    e condizione;
  - la differenza fra le due condizioni limitata al blocco del caso bersaglio,
    con distrattori e ordine relativo invariati.

I blocchi e il loro ordine vengono **ricostruiti qui**, da `queries.jsonl`,
`case_mapping.jsonl` e dalle regole della configurazione, senza riusare le
funzioni di costruzione di `rq5_common`: se il costruttore e il validatore
concordano, due implementazioni indipendenti danno lo stesso testo.

Lo script non chiama Ollama. Esce con codice 1 se un controllo fallisce.

Uso:
    python3 scripts/rq3/validate_rq5_inputs.py
    python3 scripts/rq3/validate_rq5_inputs.py --inputs-dir data/rq3/sc06_rq5_v1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq5_common as common  # noqa: E402

FORBIDDEN_IN_TEXT = ("http://", "https://", "data/json", "VCDB")


class Report:
    """Raccolta di esiti: ogni controllo stampa una riga e puo' fallire."""

    def __init__(self, verbose=True):
        self.checks = []
        self.verbose = verbose

    def add(self, name, ok, detail=""):
        self.checks.append({"check": name, "ok": bool(ok), "detail": detail})
        if self.verbose:
            print(f"[{'OK  ' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
        return ok

    @property
    def failed(self):
        return [check for check in self.checks if not check["ok"]]


# --------------------------------------------------------------------------
# Ricostruzione indipendente
# --------------------------------------------------------------------------

def _rebuild_context(config, question_id, question, episode_cases):
    """Ricostruisce i due contesti applicando di nuovo le regole della config.

    Implementazione separata da `rq5_common.build_context`: legge di nuovo
    `block_format`, `distractor_rule` e `ordering_rule` dalla configurazione.
    """
    builder = config["context_builder"]
    labels = builder["field_labels"]
    inverse = {label: field for field, label in labels.items()}

    match = re.match(
        r"^Per (Caso [A-Z]), quali valori erano stati riportati nel campo "
        r"«(.+?)»\?",
        question,
    )
    if not match:
        raise ValueError(f"{question_id}: domanda non riconosciuta")
    target_alias, label = match.group(1), match.group(2)
    field = inverse[label]

    def key(alias):
        raw = f"{builder['builder_seed']}:{question_id}:{alias}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def block_text(alias, field_path, values):
        return builder["block_format"].format(
            case_alias=alias,
            field_label=labels[field_path],
            semicolon_separated_values="; ".join(values),
        )

    distractors = []
    for alias in sorted(episode_cases):
        if alias == target_alias:
            continue
        fields = episode_cases[alias]
        chosen = field if field in fields else sorted(fields)[0]
        distractors.append((alias, chosen, list(fields[chosen])))

    target = (target_alias, field, list(episode_cases[target_alias].get(field, [])))

    contexts, orders = {}, {}
    for condition in ("sufficient", "insufficient"):
        chosen = list(distractors)
        if condition == "sufficient":
            chosen.append(target)
        chosen.sort(key=lambda item: key(item[0]))
        contexts[condition] = common.BLOCK_SEPARATOR.join(
            block_text(*item) for item in chosen
        )
        orders[condition] = [item[0] for item in chosen]
    return target_alias, field, contexts, orders


# --------------------------------------------------------------------------
# Controlli
# --------------------------------------------------------------------------

def check_sources(config, report, repo_root):
    try:
        common.verify_sources(config, repo_root)
        report.add("SHA-256 delle quattro sorgenti", True)
    except Exception as error:  # noqa: BLE001 - l'errore va mostrato, non nascosto
        report.add("SHA-256 delle quattro sorgenti", False, str(error))
        return None

    queries = common.load_queries(config, repo_root)
    oracle = common.load_oracle(config, repo_root)
    cases = common.load_case_mapping(config, repo_root)
    episodes = common.load_episodes(config, repo_root)

    split_cfg = config["split"]
    expected_questions = (
        split_cfg["development"]["question_count_per_condition"]
        + split_cfg["evaluation"]["question_count_per_condition"]
    )
    expected_cases = (
        split_cfg["development"]["case_count"] + split_cfg["evaluation"]["case_count"]
    )
    expected_episodes = (
        split_cfg["development"]["episode_count"] + split_cfg["evaluation"]["episode_count"]
    )
    report.add(
        "conteggi delle sorgenti",
        len(queries) == len(oracle) == expected_questions
        and len(cases) == expected_cases
        and len(episodes) == expected_episodes,
        f"queries={len(queries)} oracle={len(oracle)} casi={len(cases)} "
        f"episodi={len(episodes)}",
    )
    return {"queries": queries, "oracle": oracle, "cases": cases, "episodes": episodes}


def check_split(config, sources, requests, report):
    bounds = common.split_bounds(config)
    episodes_by_split = defaultdict(set)
    for row in requests:
        episodes_by_split[row["split"]].add(common.episode_number(row["episode_id"]))

    ok = True
    for split, (low, high) in bounds.items():
        numbers = episodes_by_split[split]
        expected = set(range(low, high + 1))
        ok &= report.add(
            f"episodi dello split {split}",
            numbers == expected,
            f"attesi E{low:03d}-E{high:03d} ({len(expected)}), trovati {len(numbers)}",
        )
    overlap = episodes_by_split["development"] & episodes_by_split["evaluation"]
    ok &= report.add("split disgiunti", not overlap, f"sovrapposizione: {sorted(overlap)}")
    return ok


def check_counts(config, requests, report):
    models = [model["ollama_tag"] for model in config["models"]]
    per_split = Counter(row["split"] for row in requests)
    per_split_condition = Counter((row["split"], row["condition"]) for row in requests)

    ok = True
    for split in common.SPLITS:
        questions = config["split"][split]["question_count_per_condition"]
        expected_requests = questions * len(common.CONDITIONS)
        expected_cells = expected_requests * len(models)
        ok &= report.add(
            f"richieste indipendenti dal modello — {split}",
            per_split[split] == expected_requests,
            f"attese {expected_requests}, trovate {per_split[split]}",
        )
        ok &= report.add(
            f"celle dopo l'espansione sui {len(models)} modelli — {split}",
            per_split[split] * len(models) == expected_cells,
            f"attese {expected_cells}, trovate {per_split[split] * len(models)}",
        )
        for condition in common.CONDITIONS:
            ok &= report.add(
                f"richieste {condition} — {split}",
                per_split_condition[(split, condition)] == questions,
                f"attese {questions}, trovate {per_split_condition[(split, condition)]}",
            )

    declared = config["call_counts"]
    ok &= report.add(
        "conteggi dichiarati in call_counts",
        per_split["development"] * len(models) == declared["development_maximum"]
        and per_split["evaluation"] * len(models) == declared["evaluation"],
        f"development_maximum={declared['development_maximum']}, "
        f"evaluation={declared['evaluation']}",
    )
    return ok


def check_uniqueness(config, requests, report):
    models = [model["ollama_tag"] for model in config["models"]]
    ids = [row["request_id"] for row in requests]
    keys = [(row["split"], row["condition"], row["question_id"]) for row in requests]
    ok = report.add(
        "request_id univoci", len(set(ids)) == len(ids),
        f"{len(ids) - len(set(ids))} duplicati",
    )
    ok &= report.add(
        "una richiesta per split/condizione/domanda",
        len(set(keys)) == len(keys),
        f"{len(keys) - len(set(keys))} duplicati",
    )
    cells = [
        common.cell_id(row["split"], tag, row["condition"], row["question_id"])
        for row in requests for tag in models
    ]
    ok &= report.add(
        "cell_id univoci", len(set(cells)) == len(cells),
        f"{len(cells)} celle totali",
    )
    return ok


def check_model_independence(config, requests, report):
    """Lo stesso prompt, e lo stesso hash, per entrambi i modelli."""
    models = [model["ollama_tag"] for model in config["models"]]
    leaked = [
        row["request_id"] for row in requests
        if any(tag in json.dumps(row, ensure_ascii=False) for tag in models)
        or "model" in row
    ]
    ok = report.add(
        "richieste prive di riferimenti al modello", not leaked,
        f"{len(leaked)} richieste con un tag di modello",
    )

    mismatched = []
    for row in requests:
        payloads = [
            common.chat_payload(
                config, tag, row["messages"][0]["content"], row["messages"][1]["content"]
            )
            for tag in models
        ]
        digests = {
            common.prompt_sha256(
                payload["messages"][0]["content"], payload["messages"][1]["content"]
            )
            for payload in payloads
        }
        if len(digests) != 1 or digests.pop() != row["prompt_sha256"]:
            mismatched.append(row["request_id"])
        if len({json.dumps(p["messages"], sort_keys=True) for p in payloads}) != 1:
            mismatched.append(row["request_id"])
    ok &= report.add(
        "stesso prompt e stesso hash per i due modelli", not mismatched,
        f"{len(mismatched)} richieste diverse fra modelli",
    )
    return ok


def check_reconstruction(config, sources, requests, report):
    """Ricostruisce blocchi, ordine e prompt e li confronta con i file."""
    cases = common.cases_by_episode(sources["cases"])
    queries = {row["question_id"]: row for row in sources["queries"]}
    by_question = defaultdict(dict)
    for row in requests:
        by_question[row["question_id"]][row["condition"]] = row

    prompt_diff, order_diff, hash_diff, condition_diff = [], [], [], []
    for question_id, rows in by_question.items():
        query = queries[question_id]
        target_alias, _field, contexts, orders = _rebuild_context(
            config, question_id, query["question"], cases[query["episode_id"]]
        )
        for condition, row in rows.items():
            system = config["prompt"]["system"]
            user = config["prompt"]["user_template"].format(
                context=contexts[condition], question=query["question"]
            )
            if row["messages"][0]["content"] != system or row["messages"][1]["content"] != user:
                prompt_diff.append(row["request_id"])
            if row["context_block_order"] != orders[condition]:
                order_diff.append(row["request_id"])
            if row["prompt_sha256"] != common.prompt_sha256(system, user):
                hash_diff.append(row["request_id"])

        # La sola differenza ammessa fra le due condizioni e' il blocco bersaglio.
        sufficient = orders["sufficient"]
        insufficient = orders["insufficient"]
        if [a for a in sufficient if a != target_alias] != insufficient:
            condition_diff.append(question_id)
        if target_alias in insufficient:
            condition_diff.append(question_id)
        sufficient_blocks = contexts["sufficient"].split(common.BLOCK_SEPARATOR)
        insufficient_blocks = contexts["insufficient"].split(common.BLOCK_SEPARATOR)
        kept = [b for b in sufficient_blocks if not b.startswith(target_alias + ".")]
        if kept != insufficient_blocks:
            condition_diff.append(question_id)

    ok = report.add(
        "prompt ricostruiti indipendentemente", not prompt_diff,
        f"{len(prompt_diff)} differenze",
    )
    ok &= report.add(
        "ordine dei blocchi ricostruito", not order_diff, f"{len(order_diff)} differenze"
    )
    ok &= report.add(
        "hash del prompt coerente", not hash_diff, f"{len(hash_diff)} differenze"
    )
    ok &= report.add(
        "stessi distrattori e stesso ordine relativo nelle due condizioni",
        not condition_diff,
        f"{len(set(condition_diff))} domande con differenze oltre il blocco bersaglio",
    )
    return ok


def check_prompt_leakage(config, sources, requests, oracle_rows, report):
    forbidden_keys = config["context_builder"]["forbidden_prompt_inputs"]
    by_case = {(row["episode_id"], row["case_alias"]): row for row in sources["cases"]}
    oracle_by_request = {row["request_id"]: row for row in oracle_rows}

    key_leaks, text_leaks, answer_leaks, id_leaks = [], [], [], []
    for row in requests:
        blob = json.dumps(row, ensure_ascii=False)
        serialized = json.loads(blob)
        for key in forbidden_keys:
            if key in serialized or f'"{key}"' in blob:
                key_leaks.append(row["request_id"])
        text = row["messages"][0]["content"] + "\n" + row["messages"][1]["content"]
        for needle in FORBIDDEN_IN_TEXT:
            if needle in text:
                text_leaks.append(row["request_id"])
        episode_id = row["episode_id"]
        for alias in ("Caso A", "Caso B", "Caso C"):
            meta = by_case.get((episode_id, alias))
            if not meta:
                continue
            for key in ("incident_id", "source_path", "reference"):
                value = (meta.get(key) or "").strip()
                if value and value in text:
                    id_leaks.append(row["request_id"])

        oracle = oracle_by_request.get(row["request_id"])
        if oracle and row["condition"] == "insufficient":
            # Nella condizione insufficiente non deve esserci alcun blocco del
            # caso bersaglio: il controllo e' sulla struttura, non sui valori,
            # perche' un distrattore puo' legittimamente riportare lo stesso
            # valore per il proprio caso.
            if oracle["case_alias"] in row["context_block_order"]:
                answer_leaks.append(row["request_id"])
            if f"\n{oracle['case_alias']}." in "\n" + text.split("QUESTION")[0]:
                answer_leaks.append(row["request_id"])

    ok = report.add(
        "nessun campo vietato nei record di richiesta", not key_leaks,
        f"campi vietati: {forbidden_keys}; {len(set(key_leaks))} richieste",
    )
    ok &= report.add(
        "nessun URL o percorso di sorgente nei prompt", not text_leaks,
        f"{len(set(text_leaks))} richieste",
    )
    ok &= report.add(
        "nessun identificativo VERIS o riferimento nei prompt", not id_leaks,
        f"{len(set(id_leaks))} richieste",
    )
    ok &= report.add(
        "nessun blocco del caso bersaglio nella condizione insufficiente",
        not answer_leaks, f"{len(set(answer_leaks))} richieste",
    )
    return ok


def check_oracle(config, sources, requests, oracle_rows, report):
    oracle_by_request = {row["request_id"]: row for row in oracle_rows}
    request_ids = {row["request_id"] for row in requests}
    ok = report.add(
        "una riga di oracle per ogni richiesta",
        set(oracle_by_request) == request_ids,
        f"oracle={len(oracle_by_request)} richieste={len(request_ids)}",
    )

    design = {row["question_id"]: row for row in sources["oracle"]}
    wrong = []
    for row in oracle_rows:
        expected = design[row["question_id"]]["expected_values"]
        if row["condition"] == "sufficient" and row["expected_values"] != expected:
            wrong.append(row["request_id"])
        if row["condition"] == "insufficient" and row["expected_values"] != []:
            wrong.append(row["request_id"])
    ok &= report.add(
        "risposte attese: valori nel sufficiente, lista vuota nell'insufficiente",
        not wrong, f"{len(wrong)} righe",
    )

    evaluation = [row for row in oracle_rows if row["split"] == "evaluation"]
    per_family = Counter(
        row["family"] for row in evaluation if row["condition"] == "sufficient"
    )
    ok &= report.add(
        "famiglie di domanda nella valutazione",
        dict(per_family) == config["split"]["evaluation"]["question_family_counts"],
        f"{dict(sorted(per_family.items()))}",
    )
    detectable = sum(
        1 for row in evaluation
        if row["condition"] == "sufficient" and row["detectable_cross_case_intrusion_values"]
    )
    ok &= report.add(
        "domande con confusione fra casi rilevabile",
        detectable == config["split"]["evaluation"]["questions_with_detectable_cross_case_values"],
        f"attese {config['split']['evaluation']['questions_with_detectable_cross_case_values']}, "
        f"trovate {detectable}",
    )
    return ok


def validate(config, inputs_dir, report, repo_root=common.REPO_ROOT):
    sources = check_sources(config, report, repo_root)
    if sources is None:
        return False

    inputs_dir = Path(inputs_dir)
    requests, oracle_rows = [], []
    for split in common.SPLITS:
        requests += common.read_jsonl(inputs_dir / f"{split}_requests.jsonl")
        oracle_rows += common.read_jsonl(inputs_dir / f"{split}_oracle.jsonl")

    ok = check_split(config, sources, requests, report)
    ok &= check_counts(config, requests, report)
    ok &= check_uniqueness(config, requests, report)
    ok &= check_model_independence(config, requests, report)
    ok &= check_reconstruction(config, sources, requests, report)
    ok &= check_prompt_leakage(config, sources, requests, oracle_rows, report)
    ok &= check_oracle(config, sources, requests, oracle_rows, report)
    return ok and not report.failed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=str(common.CONFIG_PATH))
    parser.add_argument("--inputs-dir", default=None,
                        help="predefinita: la directory della versione in configurazione")
    parser.add_argument("--repo-root", default=str(common.REPO_ROOT))
    parser.add_argument("--json-out", default=None, help="salva l'esito dei controlli")
    args = parser.parse_args(argv)

    config = common.load_config(args.config)
    repo_root = Path(args.repo_root)
    inputs = Path(args.inputs_dir) if args.inputs_dir else common.inputs_dir(config, repo_root)
    report = Report()
    print(f"configurazione {config['config_id']} — input {inputs}\n")
    ok = validate(config, inputs, report, repo_root)
    if args.json_out:
        common.dump_json(args.json_out, {"ok": ok, "checks": report.checks})
    print()
    print(
        f"{len(report.checks) - len(report.failed)}/{len(report.checks)} controlli superati."
        if ok else f"{len(report.failed)} controlli falliti."
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
