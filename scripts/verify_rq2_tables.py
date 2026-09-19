#!/usr/bin/env python3
"""Ricalcola e verifica la sintesi numerica RQ2, senza scrivere file.

Confronta annotazioni, riepilogo_*.json e sintesi_rq2.csv. Non rivaluta
risposte, non approva giudizi, non chiama modelli e non verifica la
trascrizione Markdown. Richiede soltanto la libreria standard.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "RACCOLTA_RISULTATI"
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


def verify(root=ROOT):
    with (root / "sintesi_rq2.csv").open(encoding="utf-8", newline="") as handle:
        saved_rows = list(csv.DictReader(handle))
    saved = {(r["scenario"], r["modalita"]): r for r in saved_rows}
    expected = {(s, m) for s, modes in SCENARIOS.items() for m in modes}
    require(len(saved_rows) == len(saved) and set(saved) == expected,
            "CSV: combinazioni scenario/modalita mancanti, duplicate o inattese")
    output = []
    total = 0
    for scenario, modes in SCENARIOS.items():
        folder = root / scenario
        rows = [json.loads(line) for line in
                (folder / f"valutazioni_{scenario.lower()}.jsonl").read_text(
                    encoding="utf-8").splitlines() if line.strip()]
        summary = json.loads((folder / f"riepilogo_{scenario.lower()}.json").read_text(
            encoding="utf-8"))
        require(set(r["mode"] for r in rows) == set(modes),
                f"{scenario}: modalita inattese o mancanti")
        require(set(summary["riepilogo_per_modalita"]) == set(modes),
                f"{scenario}: modalita del riepilogo diverse dalle annotazioni")
        for row in rows:
            tag = f"{scenario}/{row['question_id']}/{row['mode']}"
            require(row["scenario_id"] == f"scenario_{scenario[2:]}", tag + ": scenario errato")
            require(row["analysis_revision"] == summary["revisione"], tag + ": revisione incoerente")
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
                "revisione_scheda": summary["revisione"],
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
            for column, value in values.items():
                require(saved[scenario, mode][column] == value,
                        tag + f": CSV {column}: {saved[scenario, mode][column]!r} != {value!r}")
            output.append((scenario, mode, values))
            total += n
    for diagnostic in (False, True):
        print("\n" + ("FULL_HISTORY — controllo diagnostico fuori budget" if diagnostic
                         else "Modalita a budget (200 token)"))
        print("Scenario Modalita       C&S    Classi C/P/E/A  Retrieval  Answer  Obs.  Non sup.")
        for scenario, mode, values in output:
            if (mode == "FULL_HISTORY") != diagnostic:
                continue
            classes = "/".join(values[c] for c in (
                "classe_completa", "classe_parziale", "classe_errata", "astensione_corretta"))
            retrieval = values["retrieval_success"].replace("non applicabile", "n/a")
            print(f"{scenario:8} {mode:14} {values['complete_e_supportate']:6} {classes:15} "
                  f"{retrieval:10} {values['answer_success']:7} "
                  f"{values['informazione_obsoleta']:5} {values['affermazioni_non_supportate']}")
    print(f"\nOK: {total} annotazioni, {len(output)} righe di sintesi; conteggi e metriche coincidono con JSON e CSV.")
    print("C&S = complete e supportate; classi = complete/parziali/errate/astensioni corrette.")
    print("Il controllo non approva i giudizi e non verifica la trascrizione Markdown.")
    print("Nessun file scritto, nessuna chiamata al modello.")


if __name__ == "__main__":
    try:
        verify()
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        sys.exit(1)
