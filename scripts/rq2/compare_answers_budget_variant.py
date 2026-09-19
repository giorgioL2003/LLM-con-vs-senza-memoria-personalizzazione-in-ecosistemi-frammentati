#!/usr/bin/env python3
"""Confronto prima/dopo sulle risposte, dentro ogni scenario e per architettura.

«Prima» = la prova con `rq2-dev-0.1` e il tetto di 200 token, con i giudizi
gia' presenti in `RACCOLTA_RISULTATI/`. «Dopo» = la prova
`budget-per-scenario-v1` senza tetto, con i giudizi proposti qui.

Mostra, per ogni cella scenario x architettura:

  - i token del contesto, prima e dopo;
  - le classi delle risposte: complete e supportate, parziali, errate,
    astensioni corrette;
  - quali domande sono migliorate, peggiorate o rimaste equivalenti;
  - la differenza fra **provenienza** dei messaggi sorgente e **presenza
    effettiva dei fatti** nel testo del contesto.

Le due prove hanno una sola generazione ciascuna: le differenze sono
**osservate**, non spiegate. Il modello puo' rispondere in modo diverso anche
a parita' di contesto, quindi nessuna variazione viene attribuita al budget
senza che il contesto sia davvero cambiato — e nemmeno allora con certezza.

Uso:
    python3 scripts/rq2/compare_answers_budget_variant.py
    python3 scripts/rq2/compare_answers_budget_variant.py --json confronto.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402

NEW_DIR = rq2.RQ2_RESULTS_DIR / "budget_per_scenario_v1"
COLLECTION = rq2.REPO_ROOT / "RACCOLTA_RISULTATI"

BEFORE_FILES = {
    "scenario_02": COLLECTION / "SC02" / "valutazioni_sc02.jsonl",
    "scenario_03": COLLECTION / "SC03" / "valutazioni_sc03.jsonl",
    "scenario_04": COLLECTION / "SC04" / "valutazioni_sc04.jsonl",
}

GENERATED = {
    "scenario_02": ("T", "F"),
    "scenario_03": ("F", "U"),
    "scenario_04": ("T", "U", "G"),
}

# Ordine di merito delle classi: serve solo a dire «migliorata» o «peggiorata».
# Non e' un punteggio e non va sommato.
RANK = {"errata": 0, "parziale": 1, "completa": 2, "astensione corretta": 2}


def _key(row):
    return (row["scenario_id"], row["question_id"], row["mode"])


def load_before():
    rows = {}
    for scenario_id, path in BEFORE_FILES.items():
        for row in rq2.read_jsonl(path):
            if row["scenario_id"] == scenario_id and row["mode"] in GENERATED[scenario_id]:
                rows[_key(row)] = row
    return rows


def load_after():
    return {_key(row): row for row in rq2.read_jsonl(NEW_DIR / "valutazioni_budget_per_scenario.jsonl")}


def _coverage(row, field):
    """'3/4' -> (3, 4).

    Le domande ad astensione non hanno fatti richiesti: la raccolta esistente
    ci scrive `null`, le righe nuove `0/0`. Sono la stessa cosa.
    """
    value = row[field]
    if value is None:
        return 0, 0
    got, total = value.split("/")
    return int(got), int(total)


def _merit(row):
    """Merito di una risposta: la classe, ma «completa» vale solo se supportata."""
    if row["answer_class"] == "completa" and not row["counts_as_complete_and_supported"]:
        return 1.5      # fra parziale e completa: completa ma non supportata
    return RANK[row["answer_class"]]


def compare(before, after):
    cells = []
    for scenario_id, modes in GENERATED.items():
        for mode in modes:
            questions = sorted({k[1] for k in after if k[0] == scenario_id and k[2] == mode})
            per_question = []
            for question_id in questions:
                key = (scenario_id, question_id, mode)
                old, new = before.get(key), after.get(key)
                if old is None:
                    continue
                old_ctx, new_ctx = _coverage(old, "rq2_fact_coverage_in_context"), \
                    _coverage(new, "rq2_fact_coverage_in_context")
                delta = _merit(new) - _merit(old)
                per_question.append({
                    "question_id": question_id,
                    "category": new["question_category"],
                    "class_before": old["answer_class"],
                    "class_after": new["answer_class"],
                    "supported_before": old["counts_as_complete_and_supported"],
                    "supported_after": new["counts_as_complete_and_supported"],
                    "tokens_before": old["context_tokens"],
                    "tokens_after": new["context_tokens"],
                    "items_before": old["context_items"],
                    "items_after": new["context_items"],
                    "context_changed": old["context_item_ids"] != new["context_item_ids"],
                    "provenance_before": old["evidence_provenance_complete_auto"],
                    "provenance_after": new["evidence_provenance_complete_auto"],
                    "facts_in_context_before": "%d/%d" % old_ctx,
                    "facts_in_context_after": "%d/%d" % new_ctx,
                    "facts_gained": new_ctx[0] - old_ctx[0],
                    "obsolete_before": old["obsolete_used"],
                    "obsolete_after": new["obsolete_used"],
                    "unsupported_before": old["unsupported_claim"],
                    "unsupported_after": new["unsupported_claim"],
                    "esito": ("migliorata" if delta > 0 else
                              "peggiorata" if delta < 0 else "equivalente"),
                })

            if not per_question:
                continue
            n = len(per_question)

            def count(field, value):
                return sum(1 for q in per_question if q[field] == value)

            cells.append({
                "scenario_id": scenario_id,
                "mode": mode,
                "questions": n,
                "tokens_before": round(sum(q["tokens_before"] for q in per_question) / n, 1),
                "tokens_after": round(sum(q["tokens_after"] for q in per_question) / n, 1),
                "complete_supported_before": sum(1 for q in per_question if q["supported_before"]),
                "complete_supported_after": sum(1 for q in per_question if q["supported_after"]),
                "parziali_before": count("class_before", "parziale"),
                "parziali_after": count("class_after", "parziale"),
                "errate_before": count("class_before", "errata"),
                "errate_after": count("class_after", "errata"),
                "astensioni_before": count("class_before", "astensione corretta"),
                "astensioni_after": count("class_after", "astensione corretta"),
                "migliorate": count("esito", "migliorata"),
                "peggiorate": count("esito", "peggiorata"),
                "equivalenti": count("esito", "equivalente"),
                "contesti_cambiati": sum(1 for q in per_question if q["context_changed"]),
                "fatti_guadagnati": sum(q["facts_gained"] for q in per_question),
                "provenienza_completa_before": sum(1 for q in per_question if q["provenance_before"]),
                "provenienza_completa_after": sum(1 for q in per_question if q["provenance_after"]),
                "obsolete_before": sum(1 for q in per_question if q["obsolete_before"]),
                "obsolete_after": sum(1 for q in per_question if q["obsolete_after"]),
                "unsupported_before": sum(1 for q in per_question if q["unsupported_before"]),
                "unsupported_after": sum(1 for q in per_question if q["unsupported_after"]),
                "per_question": per_question,
            })
    return cells


def notes(cells):
    """Osservazioni da leggere con prudenza: una sola generazione per condizione."""
    righe = []
    for cell in cells:
        where = "%s / %s" % (cell["scenario_id"], cell["mode"])

        cambiate_senza_contesto = [q for q in cell["per_question"]
                                   if q["esito"] != "equivalente" and not q["context_changed"]]
        if cambiate_senza_contesto:
            righe.append("%s: %s cambia giudizio con un contesto IDENTICO a prima. Non e' un effetto "
                         "del budget: e' variabilita' fra due generazioni."
                         % (where, ", ".join(q["question_id"] for q in cambiate_senza_contesto)))

        piu_contesto_stesso_esito = [q for q in cell["per_question"]
                                     if q["context_changed"] and q["esito"] == "equivalente"]
        if piu_contesto_stesso_esito:
            righe.append("%s: %s ricevono piu' contesto e restano allo stesso giudizio."
                         % (where, ", ".join(q["question_id"] for q in piu_contesto_stesso_esito)))

        fatti_senza_miglioramento = [q for q in cell["per_question"]
                                     if q["facts_gained"] > 0 and q["esito"] != "migliorata"]
        if fatti_senza_miglioramento:
            righe.append("%s: %s guadagnano fatti richiesti nel contesto senza che la risposta migliori."
                         % (where, ", ".join(q["question_id"] for q in fatti_senza_miglioramento)))

        prov_ok_fatti_no = [q for q in cell["per_question"]
                            if q["provenance_after"] and
                            q["facts_in_context_after"].split("/")[0] != q["facts_in_context_after"].split("/")[1]]
        if prov_ok_fatti_no:
            righe.append("%s: in %s la provenienza dei messaggi e' completa ma i fatti richiesti NON sono "
                         "tutti nel testo del contesto (%s). La provenienza non basta a dire che "
                         "l'informazione c'e'."
                         % (where, ", ".join(q["question_id"] for q in prov_ok_fatti_no),
                            ", ".join("%s %s" % (q["question_id"], q["facts_in_context_after"])
                                      for q in prov_ok_fatti_no)))

        obsolete_rimaste = [q for q in cell["per_question"] if q["obsolete_after"]]
        if obsolete_rimaste:
            righe.append("%s: %s usa ancora informazione obsoleta anche senza tetto: il problema non era "
                         "lo spazio." % (where, ", ".join(q["question_id"] for q in obsolete_rimaste)))

        if cell["peggiorate"]:
            peggio = [q["question_id"] for q in cell["per_question"] if q["esito"] == "peggiorata"]
            righe.append("%s: %s peggiora. Piu' contesto non e' automaticamente meglio."
                         % (where, ", ".join(peggio)))
    return righe


def print_report(cells):
    print("Confronto prima/dopo sulle RISPOSTE — una sola generazione per condizione")
    print("=" * 104)
    print("%-12s %-4s %-15s %-13s %-9s %-9s %-11s %s" % (
        "scenario", "mod.", "token pr./do.", "compl.+supp.", "parziali", "errate", "astensioni",
        "migl./peggio/uguali"))
    print("-" * 104)
    for cell in cells:
        print("%-12s %-4s %-15s %-13s %-9s %-9s %-11s %d/%d/%d" % (
            cell["scenario_id"], cell["mode"],
            "%.0f -> %.0f" % (cell["tokens_before"], cell["tokens_after"]),
            "%d -> %d" % (cell["complete_supported_before"], cell["complete_supported_after"]),
            "%d -> %d" % (cell["parziali_before"], cell["parziali_after"]),
            "%d -> %d" % (cell["errate_before"], cell["errate_after"]),
            "%d -> %d" % (cell["astensioni_before"], cell["astensioni_after"]),
            cell["migliorate"], cell["peggiorate"], cell["equivalenti"]))
    print("-" * 104)
    print("Presenza dei FATTI richiesti nel testo del contesto, non solo dei messaggi sorgente:")
    print("%-12s %-4s %-24s %s" % ("scenario", "mod.", "provenienza completa", "fatti richiesti guadagnati"))
    for cell in cells:
        print("  %-10s %-4s %-24s %+d"
              % (cell["scenario_id"], cell["mode"],
                 "%d/%d -> %d/%d" % (cell["provenienza_completa_before"], cell["questions"],
                                     cell["provenienza_completa_after"], cell["questions"]),
                 cell["fatti_guadagnati"]))
    print("-" * 104)
    print("Informazione obsoleta e affermazioni non supportate:")
    for cell in cells:
        print("  %-10s %-4s obsoleta %d -> %d | non supportate %d -> %d"
              % (cell["scenario_id"], cell["mode"],
                 cell["obsolete_before"], cell["obsolete_after"],
                 cell["unsupported_before"], cell["unsupported_after"]))
    print("-" * 104)
    print("Domanda per domanda:")
    for cell in cells:
        print("  %s / %s" % (cell["scenario_id"], cell["mode"]))
        for q in cell["per_question"]:
            print("    %-9s %-18s %-11s %-24s ctx %s %s"
                  % (q["question_id"], q["category"], q["esito"],
                     "%s -> %s" % (q["class_before"], q["class_after"]),
                     "%d -> %d tok" % (q["tokens_before"], q["tokens_after"]),
                     "(identico)" if not q["context_changed"] else ""))
    print("-" * 104)
    print("Osservazioni:")
    for riga in notes(cells):
        print("  - %s" % riga)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Confronto prima/dopo sulle risposte.")
    parser.add_argument("--json", default=None)
    args = parser.parse_args(argv)

    before, after = load_before(), load_after()
    if not after:
        print("Mancano le valutazioni nuove.", file=sys.stderr)
        return 1
    cells = compare(before, after)
    print_report(cells)
    if args.json:
        rq2.write_json({"cells": cells, "osservazioni": notes(cells)}, args.json)
        print("Confronto scritto in %s." % rq2.relative(Path(args.json)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
