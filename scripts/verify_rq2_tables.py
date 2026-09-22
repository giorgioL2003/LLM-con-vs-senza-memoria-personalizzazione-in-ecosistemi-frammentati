#!/usr/bin/env python3
"""Ricalcola e verifica la sintesi numerica RQ2, senza scrivere file.

Di default mostra la variante senza tetto su SC02-SC04, riusando SC05 e
FULL_HISTORY dalla raccolta storica. --storico mostra la prova a 200 token.
Confronta annotazioni e riepiloghi JSON; per i dati storici anche il CSV. Non rivaluta
risposte, non approva giudizi, non chiama modelli e non verifica la
trascrizione Markdown. Richiede soltanto la libreria standard.
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "RACCOLTA_RISULTATI"
VARIANT = ROOT.parent / "results" / "rq2" / "budget_per_scenario_v1"
SCENARIOS = {
    "SC02": ("T", "F", "FULL_HISTORY"),
    "SC03": ("F", "U", "FULL_HISTORY"),
    "SC04": ("U", "G", "T", "FULL_HISTORY"),
    "SC05": ("U", "GER", "T", "FULL_HISTORY"),
}
CLASSES = ("completa", "parziale", "errata", "astensione corretta")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fraction(num, den):
    return f"{num}/{den}" if den else "non applicabile"


def verify(root=ROOT, variant_dir=VARIANT):
    with (root / "sintesi_rq2.csv").open(encoding="utf-8", newline="") as handle:
        saved_rows = list(csv.DictReader(handle))
    saved = {(r["scenario"], r["modalita"]): r for r in saved_rows}
    expected = {(s, m) for s, modes in SCENARIOS.items() for m in modes}
    require(len(saved_rows) == len(saved) and set(saved) == expected,
            "CSV: combinazioni scenario/modalita mancanti, duplicate o inattese")
    variant_rows = []
    variant_summary = None
    if variant_dir is not None:
        variant_rows = [json.loads(line) for line in
                        (variant_dir / "valutazioni_budget_per_scenario.jsonl").read_text(
                            encoding="utf-8").splitlines() if line.strip()]
        variant_summary = json.loads(
            (variant_dir / "riepilogo_budget_per_scenario.json").read_text(encoding="utf-8"))
        expected_variant = {(f"scenario_{s[2:]}", f"{s}-Q{i}", m)
                            for s, modes in SCENARIOS.items() if s != "SC05"
                            for m in modes if m != "FULL_HISTORY" for i in range(1, 8)}
        keys = [(r["scenario_id"], r["question_id"], r["mode"]) for r in variant_rows]
        require(len(keys) == len(set(keys)) and set(keys) == expected_variant,
                "Variante: domande mancanti, duplicate o inattese")
        require(set(variant_summary["riepilogo_per_scenario"]) ==
                {"scenario_02", "scenario_03", "scenario_04"},
                "Variante: scenari del riepilogo inattesi o mancanti")
        for row in variant_rows:
            require(row["budget_tokens"] is None and row["budget_applies"] is False,
                    "Variante: atteso contesto senza tetto")
            require(row["config_id"] == "rq2-dev-0.2-budget-per-scenario",
                    "Variante: configurazione inattesa")
            # La variante salva il flag evidence_retrieved_content_verified
            # sempre a True. Il suo riepilogo usa invece la copertura dei fatti:
            # ricaviamo da quella l'evidenza completa, senza modificare i file.
            got, needed = map(int, row["rq2_fact_coverage_in_context"].split("/"))
            details = row["rq2_fact_detail"]
            require(set(details) == set(row["oracle_rq2_required_fact_keys"]),
                    "Variante: dettaglio dei fatti incompleto")
            require(all(type(f["in_context"]) is bool for f in details.values()),
                    "Variante: presenza dei fatti non valutata")
            require(needed == len(details) and
                    got == sum(f["in_context"] for f in details.values()),
                    "Variante: copertura del contesto incoerente con il dettaglio dei fatti")
            require(needed > 0 if row["reachable"] else needed == 0,
                    "Variante: fatti richiesti incoerenti con raggiungibilita")
            row["evidence_retrieved_content_verified"] = (
                got == needed if row["reachable"] else None)
    output = []
    total = 0
    for scenario, modes in SCENARIOS.items():
        folder = root / scenario
        rows = [json.loads(line) for line in
                (folder / f"valutazioni_{scenario.lower()}.jsonl").read_text(
                    encoding="utf-8").splitlines() if line.strip()]
        summary = json.loads((folder / f"riepilogo_{scenario.lower()}.json").read_text(
            encoding="utf-8"))
        new_modes = set()
        revisions = {mode: summary["revisione"] for mode in modes}
        if variant_summary is not None and scenario != "SC05":
            new_modes = set(modes) - {"FULL_HISTORY"}
            scenario_id = f"scenario_{scenario[2:]}"
            new_summary = variant_summary["riepilogo_per_scenario"][scenario_id]
            require(set(new_summary) == new_modes,
                    f"{scenario}: modalita della variante inattese o mancanti")
            rows = [r for r in rows if r["mode"] == "FULL_HISTORY"] + [
                r for r in variant_rows if r["scenario_id"] == scenario_id]
            summary["riepilogo_per_modalita"].update(new_summary)
            revisions.update({mode: variant_summary["revisione"] for mode in new_modes})
        require(set(r["mode"] for r in rows) == set(modes),
                f"{scenario}: modalita inattese o mancanti")
        require(set(summary["riepilogo_per_modalita"]) == set(modes),
                f"{scenario}: modalita del riepilogo diverse dalle annotazioni")
        for row in rows:
            tag = f"{scenario}/{row['question_id']}/{row['mode']}"
            require(row["scenario_id"] == f"scenario_{scenario[2:]}", tag + ": scenario errato")
            require(row["analysis_revision"] == revisions[row["mode"]], tag + ": revisione incoerente")
            require(row["answer_class"] in CLASSES and row["answer_class_suspended"] is False,
                    tag + ": classe mancante o giudizio sospeso")
            for field in ("reachable", "counts_as_complete_and_supported",
                          "supported_by_original_conversation", "obsolete_used",
                          "unsupported_claim", "wrong_abstention"):
                require(type(row[field]) is bool, tag + f": {field} non valutato")
            require(row["counts_as_complete_and_supported"] == (
                row["answer_class"] == "completa" and row["supported_by_original_conversation"]),
                tag + ": completezza/supporto incoerenti")
            evidence = row["evidence_retrieved_content_verified"]
            require(type(evidence) is bool if row["reachable"] else evidence is None,
                    tag + ": evidenza non valutata o incoerente con raggiungibilita")
        for mode in modes:
            group = [r for r in rows if r["mode"] == mode]
            tag = f"{scenario}/{mode}"
            require(len(group) == 7 and {r["question_id"] for r in group} == {
                f"{scenario}-Q{i}" for i in range(1, 8)}, tag + ": domande mancanti o duplicate")
            n = len(group)
            classes = Counter(r["answer_class"] for r in group)
            reachable = [r for r in group if r["reachable"]]
            evidence = [r for r in group if r["evidence_retrieved_content_verified"] is True]
            unavailable = [r for r in group if not r["reachable"]]
            complete = sum(r["counts_as_complete_and_supported"] for r in group)
            metrics = {
                "CompleteAnswerRate": (complete, n),
                "ReachabilityRate": (len(reachable), n),
                "AnswerSuccess_condizionato_al_recupero": (
                    sum(r["counts_as_complete_and_supported"] for r in evidence), len(evidence)),
                "CorrectAbstentionRate": (
                    sum(r["answer_class"] == "astensione corretta" for r in unavailable), len(unavailable)),
                "ObsoleteUseRate": (sum(r["obsolete_used"] for r in group), n),
                "UnsupportedClaimRate": (sum(r["unsupported_claim"] for r in group), n),
                "WrongAbstentionRate": (sum(r["wrong_abstention"] for r in group), n),
                "RetrievalSuccess_condizionato_alla_raggiungibilita": (
                    (None, None) if mode == "FULL_HISTORY" else (
                        sum(r["evidence_retrieved_content_verified"] is True for r in reachable),
                        len(reachable))),
            }
            stored = summary["riepilogo_per_modalita"][mode]
            require(stored["N_c"] == n, tag + ": N_c diverso")
            require(stored["classi"] == {**{c: classes[c] for c in CLASSES}, "sospese": 0},
                    tag + ": classi diverse")
            for name, (num, den) in metrics.items():
                item = stored[name]
                require((item["numeratore"], item["denominatore"]) == (num, den),
                        tag + f": {name}, frazione diversa")
                value = round(num / den, 4) if den else None
                percent = round(100 * num / den, 1) if den else None
                require(item["valore"] == value, tag + f": {name}, valore diverso")
                if "percentuale" in item:
                    require(item["percentuale"] == percent, tag + f": {name}, percentuale diversa")
            values = {
                "n_risposte": str(n), "complete_e_supportate_pct": str(round(100 * complete / n, 1)),
                "classe_completa": str(classes["completa"]),
                "classe_parziale": str(classes["parziale"]), "classe_errata": str(classes["errata"]),
                "astensione_corretta": str(classes["astensione corretta"]),
                "contesto_token_medio": str(round(sum(r["context_tokens"] for r in group) / n, 1)),
                "revisione_scheda": revisions[mode],
            }
            for column, name in {
                "complete_e_supportate": "CompleteAnswerRate", "reachability": "ReachabilityRate",
                "answer_success": "AnswerSuccess_condizionato_al_recupero",
                "astensione_corretta_su_non_raggiungibili": "CorrectAbstentionRate",
                "informazione_obsoleta": "ObsoleteUseRate",
                "affermazioni_non_supportate": "UnsupportedClaimRate",
                "astensioni_errate": "WrongAbstentionRate",
                "retrieval_success": "RetrievalSuccess_condizionato_alla_raggiungibilita",
            }.items():
                values[column] = fraction(*metrics[name])
            num, den = metrics["RetrievalSuccess_condizionato_alla_raggiungibilita"]
            values["retrieval_success_pct"] = str(round(100 * num / den, 1)) if den else ""
            if mode in new_modes:
                require(stored["token_contesto_medi"] == float(values["contesto_token_medio"]),
                        tag + ": token medi diversi dal riepilogo")
            else:
                for column, value in values.items():
                    require(saved[scenario, mode][column] == value,
                            tag + f": CSV {column}: {saved[scenario, mode][column]!r} != {value!r}")
            output.append((scenario, mode, values))
            total += n
    if variant_dir is None:
        groups = [("Prova storica — modalita a budget (200 token)",
                   lambda s, m: m != "FULL_HISTORY")]
    else:
        print("RQ2 — budget per scenario (valutazioni nuove PROPOSTE)")
        groups = [
            ("SC02-SC04 — senza tetto di token",
             lambda s, m: s != "SC05" and m != "FULL_HISTORY"),
            ("SC05 — budget 200 token",
             lambda s, m: s == "SC05" and m != "FULL_HISTORY"),
        ]
    groups.append(("FULL_HISTORY — controllo diagnostico fuori budget per SC05",
                   lambda s, m: m == "FULL_HISTORY"))
    for title, include in groups:
        print("\n" + title)
        print("Scenario Modalita       C&S    Classi C/P/E/A  Retrieval  Answer  Obs.  Non sup.")
        for scenario, mode, values in output:
            if not include(scenario, mode):
                continue
            classes = "/".join(values[c] for c in (
                "classe_completa", "classe_parziale", "classe_errata", "astensione_corretta"))
            retrieval = values["retrieval_success"].replace("non applicabile", "n/a")
            print(f"{scenario:8} {mode:14} {values['complete_e_supportate']:6} {classes:15} "
                  f"{retrieval:10} {values['answer_success']:7} "
                  f"{values['informazione_obsoleta']:5} {values['affermazioni_non_supportate']}")
    print(f"\nOK: {total} annotazioni, {len(output)} righe di sintesi; conteggi e metriche verificati.")
    if variant_dir is not None:
        print("49 risposte nuove + 49 storiche riutilizzate; riepiloghi JSON verificati, CSV per le righe storiche.")
        print("Il CSV storico resta riferito alla prova a 200 token. Per mostrarla: --storico.")
    else:
        print("Conteggi e metriche coincidono con i riepiloghi JSON e il CSV storico.")
    print("C&S = complete e supportate; classi = complete/parziali/errate/astensioni corrette.")
    print("Il controllo non approva i giudizi e non verifica la trascrizione Markdown.")
    print("Nessun file scritto, nessuna chiamata al modello.")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storico", action="store_true",
                        help="mostra la raccolta originale a 200 token per tutti gli scenari")
    args = parser.parse_args()
    try:
        verify(variant_dir=None if args.storico else VARIANT)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        sys.exit(1)
