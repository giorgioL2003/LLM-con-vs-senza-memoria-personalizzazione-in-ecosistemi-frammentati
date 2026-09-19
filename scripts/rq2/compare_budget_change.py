#!/usr/bin/env python3
"""Confronto fra due preparazioni di RQ2: prima e dopo il cambio di budget.

Legge due insiemi di file di retrieval — quelli delle prove gia' eseguite e
quelli della nuova preparazione — e dice, per scenario e per architettura:

  - quanti token di contesto c'erano prima e quanti ce ne sono ora;
  - quali elementi sono entrati in piu' (l'informazione aggiunta) e da quali
    messaggi provengono;
  - quanti contesti sono effettivamente cambiati;
  - dove togliere il tetto cambia il *comportamento* del retrieval e non solo
    la quantita' di testo: T che arriva a contenere quasi tutta la cronologia,
    la soglia di pertinenza che diventa l'unico criterio di esclusione, i casi
    in cui il tetto non escludeva nulla.

Non chiama nessun modello, non tocca i giudizi e non riscrive nessun artefatto:
legge e basta. Le prove vecchie e quelle nuove restano file distinti.

Il confronto e' valido solo a parita' di memoria: lo script controlla che le
sorgenti (fatti, stato, grafo) di ogni coppia coincidano, e lo segnala quando
non e' cosi'.

Uso:
    python3 scripts/rq2/compare_budget_change.py
    python3 scripts/rq2/compare_budget_change.py --csv riepilogo.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402

NEW_DIR = rq2.RQ2_RESULTS_DIR / "budget_per_scenario_v1"

# Da dove vengono i contesti delle prove attuali, cella per cella. Sono gli
# stessi file dichiarati in RACCOLTA_RISULTATI/INVENTARIO.md §5: versioni
# corrette per SC03-U e SC04-U/G, estensione T per SC04 e SC05.
BEFORE = {
    ("scenario_02", "T"): "results/rq2/retrieval_sc02.jsonl",
    ("scenario_02", "F"): "results/rq2/retrieval_sc02.jsonl",
    ("scenario_03", "F"): "results/rq2/retrieval_sc03.jsonl",
    ("scenario_03", "U"): "results/rq2/retrieval_repair_v3/retrieval_sc03_u.jsonl",
    ("scenario_04", "T"): "results/rq2/t_ext_v1/retrieval_t_sc04.jsonl",
    ("scenario_04", "U"): "results/rq2/sc04_repair_v3/retrieval_sc04_ug.jsonl",
    ("scenario_04", "G"): "results/rq2/sc04_repair_v3/retrieval_sc04_ug.jsonl",
    ("scenario_05", "T"): "results/rq2/t_ext_v1/retrieval_t_sc05.jsonl",
    ("scenario_05", "U"): "results/rq2/sc05_dev_v1/retrieval_sc05_u_ger.jsonl",
    ("scenario_05", "GER"): "results/rq2/sc05_dev_v1/retrieval_sc05_u_ger.jsonl",
}

AFTER = {
    "scenario_02": NEW_DIR / "retrieval_sc02.jsonl",
    "scenario_03": NEW_DIR / "retrieval_sc03.jsonl",
    "scenario_04": NEW_DIR / "retrieval_sc04.jsonl",
    "scenario_05": NEW_DIR / "retrieval_sc05.jsonl",
}

ORDER = ["scenario_02", "scenario_03", "scenario_04", "scenario_05"]
MODE_ORDER = ["T", "F", "U", "G", "GER"]


def _index(path):
    rows = {}
    for row in rq2.read_jsonl(path):
        rows[(row["scenario_id"], row["question_id"], row["mode"])] = row
    return rows


def load_sides():
    before, after = {}, {}
    for path in sorted(set(BEFORE.values())):
        full = rq2.REPO_ROOT / path
        for key, row in _index(full).items():
            if (key[0], key[2]) in BEFORE and BEFORE[(key[0], key[2])] == path:
                before[key] = row
    for scenario_id, path in AFTER.items():
        if not Path(path).exists():
            continue
        after.update(_index(path))
    return before, after


def history_size(scenario_id):
    """Quanti messaggi utente ha lo scenario e quanti token misura la cronologia."""
    scenario = rq2.load_scenario(scenario_id)
    items = rq2.message_items(scenario)
    return len(items), sum(item["tokens"] for item in items)


def history_ids(scenario_id):
    return [item["item_id"] for item in rq2.message_items(rq2.load_scenario(scenario_id))]


def compare(before, after):
    """Una riga di confronto per ogni cella scenario x architettura."""
    cells = []
    keys = sorted({(k[0], k[2]) for k in after} & {(k[0], k[2]) for k in before},
                  key=lambda k: (ORDER.index(k[0]) if k[0] in ORDER else 99,
                                 MODE_ORDER.index(k[1]) if k[1] in MODE_ORDER else 99))

    for scenario_id, mode in keys:
        questions = sorted(q for (s, q, m) in after if s == scenario_id and m == mode)
        history_items, history_tokens = history_size(scenario_id)
        cronologia = set(history_ids(scenario_id)) if mode == "T" else None
        per_question, mismatched_sources = [], []

        for question_id in questions:
            key = (scenario_id, question_id, mode)
            old, new = before.get(key), after.get(key)
            if old is None:
                continue
            for field in ("facts_source", "state_source", "graph_source"):
                if old.get(field) != new.get(field):
                    mismatched_sources.append("%s: %s %s -> %s"
                                              % (question_id, field, old.get(field), new.get(field)))
            old_ids = list(old["selected_item_ids"])
            new_ids = list(new["selected_item_ids"])
            added = [i for i in new_ids if i not in old_ids]
            removed = [i for i in old_ids if i not in new_ids]
            old_prov = set(old["context_provenance_message_ids"])
            new_prov = set(new["context_provenance_message_ids"])
            # Quanti elementi restano fuori per pertinenza e non per spazio:
            # senza tetto e' l'unico criterio di esclusione rimasto.
            excluded_by_threshold = sum(1 for item in new["ranking"] if item["score"] <= 0)
            per_question.append({
                "question_id": question_id,
                "ranked_items": len(new["ranking"]),
                "excluded_by_threshold": excluded_by_threshold,
                "tokens_before": old["context_tokens"],
                "tokens_after": new["context_tokens"],
                "items_before": old["context_items"],
                "items_after": new["context_items"],
                "added_item_ids": added,
                "removed_item_ids": removed,
                "added_message_ids": sorted(new_prov - old_prov),
                "changed": old_ids != new_ids,
                "budget_before": old["budget_tokens"],
                "budget_after": new["budget_tokens"],
                "stopped_before": (old["stopped_by"] or {}).get("reason"),
                "stopped_after": (new["stopped_by"] or {}).get("reason"),
                "evidence_before": old["evidence_provenance_complete"],
                "evidence_after": new["evidence_provenance_complete"],
                # Solo per T: il contesto contiene ormai ogni messaggio utente?
                # Stesso contenuto di FULL_HISTORY, ordine del ranking.
                "covers_whole_history": (cronologia is not None
                                         and set(new_ids) == cronologia),
            })

        if not per_question:
            continue
        n = len(per_question)
        changed = [q for q in per_question if q["changed"]]
        applicable = [q for q in per_question if q["evidence_before"] is not None]
        cells.append({
            "scenario_id": scenario_id,
            "mode": mode,
            "questions": n,
            "budget_before": per_question[0]["budget_before"],
            "budget_after": per_question[0]["budget_after"],
            "tokens_before": sum(q["tokens_before"] for q in per_question) / n,
            "tokens_after": sum(q["tokens_after"] for q in per_question) / n,
            "tokens_after_max": max(q["tokens_after"] for q in per_question),
            "items_before": sum(q["items_before"] for q in per_question) / n,
            "items_after": sum(q["items_after"] for q in per_question) / n,
            "added_items_total": sum(len(q["added_item_ids"]) for q in per_question),
            "removed_items_total": sum(len(q["removed_item_ids"]) for q in per_question),
            "added_messages_total": sum(len(q["added_message_ids"]) for q in per_question),
            "changed_contexts": len(changed),
            "unchanged_question_ids": [q["question_id"] for q in per_question if not q["changed"]],
            "excluded_by_threshold": sum(q["excluded_by_threshold"] for q in per_question) / n,
            "covers_whole_history": sum(1 for q in per_question if q["covers_whole_history"]),
            "evidence_before": sum(1 for q in applicable if q["evidence_before"]),
            "evidence_after": sum(1 for q in applicable if q["evidence_after"]),
            "evidence_applicable": len(applicable),
            "history_items": history_items,
            "history_tokens": history_tokens,
            "stopped_after": sorted({q["stopped_after"] for q in per_question}, key=str),
            "mismatched_sources": mismatched_sources,
            "per_question": per_question,
        })
    return cells


# --------------------------------------------------------------------------
# Segnalazioni: dove il cambiamento non e' solo quantitativo
# --------------------------------------------------------------------------

def warnings(cells):
    notes = []
    for cell in cells:
        where = "%s / %s" % (cell["scenario_id"], cell["mode"])

        if cell["mismatched_sources"]:
            notes.append("%s: le sorgenti di memoria non coincidono con la prova precedente — %s"
                         % (where, "; ".join(cell["mismatched_sources"][:3])))

        if cell["budget_after"] is None and cell["unchanged_question_ids"] and cell["changed_contexts"]:
            notes.append("%s: %s non cambia nemmeno senza tetto — li' il budget non escludeva nulla, "
                         "si fermava gia' la soglia di pertinenza"
                         % (where, ", ".join(cell["unchanged_question_ids"])))

        if cell["budget_after"] is None and cell["changed_contexts"] == 0:
            notes.append("%s: togliere il tetto non cambia nulla — il budget non escludeva niente, "
                         "a fermare il retrieval era gia' la soglia di pertinenza" % where)

        # T senza tetto tende a FULL_HISTORY: quanto ci si avvicina?
        if cell["mode"] == "T" and cell["budget_after"] is None:
            quota = cell["items_after"] / cell["history_items"]
            if cell["covers_whole_history"]:
                notes.append("%s: in %d prove su %d il ranking di T arriva a includere tutti i %d messaggi "
                             "utente. Il retrieval viene eseguito comunque — ranking, soglia e ordine sono "
                             "quelli di sempre — ma in quelle prove non esclude nulla: il contenuto "
                             "coincide con quello di FULL_HISTORY e cambia l'ordine, che qui e' quello del "
                             "ranking e non quello cronologico. Il confronto con il controllo diagnostico "
                             "resta definito e misura l'effetto dell'ordine, non quello della selezione."
                             % (where, cell["covers_whole_history"], cell["questions"],
                                cell["history_items"]))
            elif quota >= 0.8:
                notes.append("%s: T ora recupera in media %.1f messaggi su %d (%.0f%% della cronologia): "
                             "il confronto con FULL_HISTORY perde gran parte del suo significato"
                             % (where, cell["items_after"], cell["history_items"], 100 * quota))

        if cell["budget_after"] is None and cell["excluded_by_threshold"] == 0:
            notes.append("%s: senza tetto non resta nessun criterio di esclusione basato sul ranking — "
                         "la soglia di pertinenza non scarta nulla, quindi entra tutto cio' che le "
                         "regole della modalita' producono" % where)

        if cell["budget_after"] is None:
            crescita = (cell["tokens_after"] / cell["tokens_before"]) if cell["tokens_before"] else 0
            if crescita >= 2.0:
                notes.append("%s: il contesto medio passa da %.0f a %.0f token (x%.1f): l'overhead "
                             "strutturale non esclude piu' elementi e smette di essere la variabile "
                             "misurata dai confronti a parita' di budget"
                             % (where, cell["tokens_before"], cell["tokens_after"], crescita))
            if cell["removed_items_total"]:
                notes.append("%s: %d elementi presenti prima non compaiono piu': senza tetto il "
                             "prefisso del ranking puo' solo allungarsi, quindi va spiegato"
                             % (where, cell["removed_items_total"]))
            if cell["evidence_applicable"] and cell["evidence_after"] == cell["evidence_before"]:
                notes.append("%s: la copertura per PROVENIENZA resta %d/%d, cioe' era gia' completa e non "
                             "puo' salire. Questo NON dice che non entri nuova evidenza: la provenienza "
                             "conta i messaggi sorgente citati, non i fatti presenti nel testo. Un "
                             "messaggio puo' essere gia' rappresentato da un fatto parziale mentre quello "
                             "decisivo resta fuori. Per sapere se l'informazione e' entrata davvero serve "
                             "la verifica sul contenuto, che sta nelle valutazioni."
                             % (where, cell["evidence_after"], cell["evidence_applicable"]))

        if cell["budget_after"] is not None and cell["changed_contexts"]:
            notes.append("%s: il tetto e' rimasto ma il contesto cambia in %d prove: da verificare"
                         % (where, cell["changed_contexts"]))
    return notes


def print_report(cells):
    print("Confronto prima/dopo il cambio di budget — nessun modello e' stato chiamato")
    print("=" * 100)
    print("%-12s %-4s %-12s %-13s %-11s %-13s %-9s %s" % (
        "scenario", "mod.", "budget do.", "token pr./do.",
        "elem. pr/do", "aggiunti", "cambiati", "esclusi per pertinenza"))
    print("-" * 100)
    for cell in cells:
        print("%-12s %-4s %-12s %-13s %-11s %-13s %-9s %.1f" % (
            cell["scenario_id"], cell["mode"],
            rq2.budget_label(cell["budget_after"]),
            "%.0f -> %.0f" % (cell["tokens_before"], cell["tokens_after"]),
            "%.1f -> %.1f" % (cell["items_before"], cell["items_after"]),
            "%d el./%d msg" % (cell["added_items_total"], cell["added_messages_total"]),
            "%d/%d" % (cell["changed_contexts"], cell["questions"]),
            cell["excluded_by_threshold"]))
    print("-" * 100)
    print("Copertura dell'evidenza per provenienza (non misura il contenuto):")
    for cell in cells:
        if not cell["evidence_applicable"]:
            continue
        print("  %-12s %-4s %d/%d -> %d/%d" % (
            cell["scenario_id"], cell["mode"],
            cell["evidence_before"], cell["evidence_applicable"],
            cell["evidence_after"], cell["evidence_applicable"]))
    notes = warnings(cells)
    print("-" * 100)
    if notes:
        print("Segnalazioni:")
        for note in notes:
            print("  - %s" % note)
    else:
        print("Nessuna segnalazione.")


def write_csv(cells, path):
    columns = ["scenario_id", "mode", "questions", "budget_before", "budget_after",
               "tokens_before", "tokens_after", "items_before", "items_after",
               "added_items_total", "added_messages_total", "removed_items_total",
               "changed_contexts", "excluded_by_threshold", "covers_whole_history", "evidence_before", "evidence_after", "evidence_applicable",
               "history_items", "history_tokens"]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(",".join(columns) + "\n")
        for cell in cells:
            values = []
            for column in columns:
                value = cell[column]
                if value is None:
                    values.append("nessun tetto" if column.startswith("budget") else "")
                elif isinstance(value, float):
                    values.append("%.1f" % value)
                else:
                    values.append(str(value))
            handle.write(",".join(values) + "\n")
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Confronta le prove attuali con la nuova preparazione.")
    parser.add_argument("--csv", default=None, help="scrive il riepilogo per cella in formato CSV")
    parser.add_argument("--json", default=None, help="scrive il confronto completo, domanda per domanda")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    before, after = load_sides()
    if not after:
        print("Nessun retrieval nuovo da confrontare: eseguire prima la preparazione.", file=sys.stderr)
        return 1
    cells = compare(before, after)
    print_report(cells)
    if args.csv:
        print("Riepilogo scritto in %s." % rq2.relative(write_csv(cells, args.csv)))
    if args.json:
        rq2.write_json({"cells": cells, "warnings": warnings(cells)}, args.json)
        print("Confronto completo scritto in %s." % rq2.relative(Path(args.json)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
