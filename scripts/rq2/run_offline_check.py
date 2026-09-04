#!/usr/bin/env python3
"""Prova dell'intera matrice RQ2 **senza chiamare nessun modello**.

Esegue in fila: validazione, prompt di estrazione in dry run, costruzione di U,
costruzione di G, retrieval per tutte le modalita' previste, input di
generazione, modello di annotazione, confronto F/U su SC03 e confronto U/G su
SC04.

Al posto delle chiamate a Claude vengono riprodotte **fixture dichiarate** sotto
`tests/fixtures/rq2/`: fatti candidati gia' scritti e risposte finte dei
costruttori di U e di G. I file prodotti finiscono in
`results/rq2/offline_check/`, sono etichettati `fixture` e **non sono risultati
sperimentali**: servono a controllare che la pipeline funzioni, che il budget
venga applicato al contesto realmente formattato, che la provenienza sia valida
e che le tracce distinguano i tipi di errore.

Lo script controlla anche, con un confronto di impronte, che nessun file del
pilot di RQ1 sia stato toccato.

Uso:
    python3 scripts/rq2/run_offline_check.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import validate_rq2  # noqa: E402
import extract_facts  # noqa: E402
import build_memory_updates as memory  # noqa: E402
import build_graph as graph_memory  # noqa: E402
import run_retrieval_rq2 as retrieval_rq2  # noqa: E402
import build_generation_inputs_rq2 as inputs_rq2  # noqa: E402
import build_annotation_template_rq2 as template_rq2  # noqa: E402
import fixture_replay  # noqa: E402

OUT_DIR = rq2.RQ2_RESULTS_DIR / "offline_check"
FIXTURE_DIR = rq2.REPO_ROOT / "tests" / "fixtures" / "rq2"
LABEL = "fixture"

FACT_FIXTURES = {
    "scenario_02": FIXTURE_DIR / "scenario_02_facts_fixture.jsonl",
    "scenario_03": FIXTURE_DIR / "scenario_03_facts_fixture.jsonl",
    "scenario_04": FIXTURE_DIR / "scenario_04_facts_fixture.jsonl",
}
UPDATE_FIXTURES = {
    "scenario_03": FIXTURE_DIR / "scenario_03_update_answers_fixture.json",
    "scenario_04": FIXTURE_DIR / "scenario_04_update_answers_fixture.json",
}
# Fixture artificiale, tenuta separata: contiene proposte volutamente sbagliate
# e serve solo a mostrare il rifiuto. Non rappresenta il comportamento atteso.
REJECTED_FIXTURE = FIXTURE_DIR / "scenario_03_update_answers_rejected_fixture.json"
GRAPH_FIXTURES = {
    "scenario_04": FIXTURE_DIR / "scenario_04_graph_answer_fixture.json",
}

MEMORY_SCENARIOS = ("scenario_03", "scenario_04")
GRAPH_SCENARIOS = ("scenario_04",)

FU_QUESTION = "SC03-Q5"   # confronto F/U: la domanda con un fatto superato in agguato
UG_QUESTION = "SC04-Q3"   # confronto U/G: la domanda relazionale


def pilot_fingerprint():
    """Impronte dei file del pilot che RQ2 non deve mai riscrivere."""
    paths = sorted(
        list((rq2.REPO_ROOT / "data" / "scenarios").glob("*.json"))
        + [p for p in (rq2.REPO_ROOT / "results").glob("*.jsonl")]
        + [p for p in (rq2.REPO_ROOT / "results").glob("*.json")]
        + list((rq2.REPO_ROOT / "pilot").glob("*.md"))
    )
    return {rq2.relative(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def step(number, title):
    print()
    print("=" * 78)
    print("Passo %d — %s" % (number, title))
    print("=" * 78)


def show_context(rows, question_id, modes):
    for mode in modes:
        row = next((r for r in rows if r["question_id"] == question_id and r["mode"] == mode), None)
        if row is None:
            print("\n--- %s: nessun input costruito ---" % mode)
            continue
        scope = " | lettura: %s" % row["reading_scope"] if row.get("reading_scope") else ""
        print()
        print("--- %s | %d elementi | %d token (%d contenuto + %d struttura)%s ---"
              % (mode, len(row["context_item_ids"]), row["context_tokens"],
                 row["context_content_tokens"], row["context_overhead_tokens"], scope))
        contesto = row["prompt"].split("Contesto:\n", 1)[1].split("\n\nDomanda:")[0]
        print(contesto)


def main():
    print("=" * 78)
    print("VERIFICA OFFLINE DELLA MATRICE RQ2 — nessuna chiamata al modello")
    print("Fatti, operazioni di U e grafo di G vengono da FIXTURE dichiarate.")
    print("I file prodotti in results/rq2/offline_check/ NON sono risultati sperimentali.")
    print("=" * 78)

    before = pilot_fingerprint()
    config = rq2.load_config()
    budget = rq2.budget_tokens(config)

    step(1, "Validazione di dataset, annotazioni e configurazione")
    if validate_rq2.main() != 0:
        return 1

    step(2, "Prompt di estrazione dei fatti (dry run, SC02 SC03 SC04)")
    for scenario_id in FACT_FIXTURES:
        if extract_facts.main(["--scenario", scenario_id, "--dry-run",
                               "--out-dir", str(OUT_DIR / "facts")]) != 0:
            return 1
        print()

    step(3, "Costruzione di U dai fatti candidati (fixture)")
    paths_by_scenario = {}
    for scenario_id in FACT_FIXTURES:
        paths_by_scenario[scenario_id] = {"facts": str(FACT_FIXTURES[scenario_id])}

    for scenario_id in MEMORY_SCENARIOS:
        scenario = rq2.load_scenario(scenario_id)
        facts = rq2.read_jsonl(FACT_FIXTURES[scenario_id])
        runner = fixture_replay.make_runner(UPDATE_FIXTURES[scenario_id])
        operations, entries, log = memory.run(scenario, facts, config, runner=runner)
        log.update({"label": LABEL, "facts_source": rq2.relative(FACT_FIXTURES[scenario_id]),
                    "fixture_answers": rq2.relative(UPDATE_FIXTURES[scenario_id])})
        rq2.write_json(log, memory.log_path(scenario_id, OUT_DIR / "memory"))
        rq2.write_jsonl(operations, memory.operations_path(scenario_id, OUT_DIR / "memory"))
        state_file = memory.state_path(scenario_id, OUT_DIR / "memory")
        rq2.write_json(memory.state_document(scenario_id, entries, config, LABEL), state_file)
        paths_by_scenario[scenario_id]["state"] = str(state_file)

        counts = {}
        for operation in operations:
            counts[operation["proposed_operation"]] = counts.get(operation["proposed_operation"], 0) + 1
        status = {}
        for entry in entries:
            status[entry["status"]] = status.get(entry["status"], 0) + 1
        rejected = [o for o in operations if not o["applied"]]
        print("%-13s fatti=%-3d proposte: %-38s stato: %-38s rifiutate: %d"
              % (scenario_id, len(facts),
                 ", ".join("%s=%d" % item for item in sorted(counts.items())),
                 ", ".join("%s=%d" % item for item in sorted(status.items())), len(rejected)))

    esempio = next(o for o in operations if o["applied"] and o["proposed_operation"] == "UPDATE")
    print()
    print("Esempio di operazione applicata (%s):" % esempio["op_id"])
    print("  proposta:  %s su '%s' -> %r" % (esempio["proposed_operation"], esempio["claim_key"],
                                             esempio["value"][:60]))
    print("  target:    %s | nuova voce: %s" % (esempio["target_entry_id"], esempio["resulting_entry_id"]))
    print("  applicata: %s | motivazione del sistema: %s" % (esempio["applied"], esempio["reason"][:70]))
    print("  impronta stato: %s -> %s (cambiata: %s)"
          % (esempio["state_before_fingerprint"], esempio["state_after_fingerprint"],
             esempio["state_before_fingerprint"] != esempio["state_after_fingerprint"]))

    step(4, "Rifiuto di operazioni non applicabili (fixture artificiale, separata)")
    print("Fixture: %s" % rq2.relative(REJECTED_FIXTURE))
    print("Contiene proposte volutamente sbagliate: serve a mostrare il rifiuto,")
    print("non rappresenta il comportamento atteso del modello.")
    scenario = rq2.load_scenario("scenario_03")
    facts = rq2.read_jsonl(FACT_FIXTURES["scenario_03"])
    bad_ops, bad_entries, bad_log = memory.run(
        scenario, facts, config, runner=fixture_replay.make_runner(REJECTED_FIXTURE))
    bad_log.update({"label": "fixture artificiale",
                    "fixture_answers": rq2.relative(REJECTED_FIXTURE),
                    "facts_source": rq2.relative(FACT_FIXTURES["scenario_03"])})
    rq2.write_json(bad_log, memory.log_path("scenario_03", OUT_DIR / "memory_rejected"))
    rq2.write_jsonl(bad_ops, memory.operations_path("scenario_03", OUT_DIR / "memory_rejected"))
    rq2.write_json(memory.state_document("scenario_03", bad_entries, config, "fixture artificiale"),
                   memory.state_path("scenario_03", OUT_DIR / "memory_rejected"))
    rifiutate = [o for o in bad_ops if not o["applied"]]
    print()
    print("Proposte: %d | applicate: %d | rifiutate: %d"
          % (len(bad_ops), len(bad_ops) - len(rifiutate), len(rifiutate)))
    for operation in rifiutate:
        print("  %s  %s -> applied_operation=%s"
              % (operation["op_id"], operation["proposed_operation"], operation["applied_operation"]))
        print("     motivo:   %s" % operation["rejection_reason"])
        print("     impronta: %s -> %s | attivi %d -> %d | mutazione: %s"
              % (operation["state_before_fingerprint"], operation["state_after_fingerprint"],
                 operation["state_before_active"], operation["state_after_active"],
                 "SI" if operation["state_before_fingerprint"] != operation["state_after_fingerprint"]
                 else "nessuna"))
    if any(o["state_before_fingerprint"] != o["state_after_fingerprint"] for o in rifiutate):
        print("Un rifiuto ha modificato lo stato: e' un errore.", file=sys.stderr)
        return 1
    print()
    print("Le operazioni rifiutate restano negli artefatti (%s) e vanno contate"
          % rq2.relative(memory.operations_path("scenario_03", OUT_DIR / "memory_rejected")))
    print("come errori di gestione della memoria, non come guasti dello script.")

    step(5, "Costruzione di G dallo stesso stato aggiornato di U (fixture)")
    for scenario_id in GRAPH_SCENARIOS:
        scenario = rq2.load_scenario(scenario_id)
        facts = rq2.read_jsonl(FACT_FIXTURES[scenario_id])
        entries = memory.load_state(paths_by_scenario[scenario_id]["state"])
        runner = fixture_replay.make_runner(GRAPH_FIXTURES[scenario_id])
        graph, log = graph_memory.run(scenario, facts, entries, config, runner=runner)
        log.update({"label": LABEL, "facts_source": rq2.relative(FACT_FIXTURES[scenario_id]),
                    "state_source": rq2.relative(paths_by_scenario[scenario_id]["state"]),
                    "fixture_answers": rq2.relative(GRAPH_FIXTURES[scenario_id])})
        rq2.write_json(log, graph_memory.log_path(scenario_id, OUT_DIR / "graph"))
        graph_file = graph_memory.graph_path(scenario_id, OUT_DIR / "graph")
        rq2.write_json(
            graph_memory.graph_document(scenario_id, graph, config, LABEL,
                                        rq2.relative(FACT_FIXTURES[scenario_id]),
                                        rq2.relative(paths_by_scenario[scenario_id]["state"])),
            graph_file)
        paths_by_scenario[scenario_id]["graph"] = str(graph_file)
        invalid = [x for x in graph["nodes"] + graph["edges"] if not x["provenance_valid"]]
        print("%-13s nodi=%-3d archi=%-3d provenienza non valida: %d"
              % (scenario_id, len(graph["nodes"]), len(graph["edges"]), len(invalid)))

    step(6, "Retrieval di T, F, U e G entro il budget effettivo (%d token)" % budget)
    rows, skipped = retrieval_rq2.run(list(rq2.SCENARIO_IDS), config, paths_by_scenario, LABEL)
    retrieval_rq2.print_summary(rows)
    for scenario_id, mode, reason in skipped:
        print("saltato: %s / %s — %s" % (scenario_id, mode, reason))
    retrieval_file = OUT_DIR / "retrieval_rq2.jsonl"
    rq2.write_jsonl(rows, retrieval_file)
    print("\nRetrieval scritto in %s (%d righe)." % (rq2.relative(retrieval_file), len(rows)))

    step(7, "Input di generazione per l'intera matrice")
    if inputs_rq2.main(["--retrieval", str(retrieval_file),
                        "--out", str(OUT_DIR / "generation_inputs_rq2.jsonl")]) != 0:
        return 1
    inputs = rq2.read_jsonl(OUT_DIR / "generation_inputs_rq2.jsonl")
    expected = sum(7 * len(rq2.planned_modes(s, config)) for s in rq2.SCENARIO_IDS)
    print("Celle costruite: %d su %d previste dalla matrice." % (len(inputs), expected))
    if len(inputs) != expected:
        print("La matrice non e' completa.", file=sys.stderr)
        return 1

    step(8, "Modello di annotazione della valutazione")
    if template_rq2.main(["--retrieval", str(retrieval_file),
                          "--inputs", str(OUT_DIR / "generation_inputs_rq2.jsonl"),
                          "--out", str(OUT_DIR / "annotation_template_rq2.jsonl")]) != 0:
        return 1
    template = rq2.read_jsonl(OUT_DIR / "annotation_template_rq2.jsonl")

    step(9, "Confronto F / U su %s" % FU_QUESTION)
    question = next(q for q in rq2.load_questions("scenario_03") if q["question_id"] == FU_QUESTION)
    print("domanda: %s" % question["text"])
    print("da non usare come valido: %s" % "; ".join(question["obsolete_information"]))
    show_context(inputs, FU_QUESTION, ("F", "U", rq2.FULL_HISTORY))

    step(10, "Confronto U / G su %s" % UG_QUESTION)
    question = next(q for q in rq2.load_questions("scenario_04") if q["question_id"] == UG_QUESTION)
    print("domanda: %s" % question["text"])
    graph_row = next(r for r in rows if r["question_id"] == UG_QUESTION and r["mode"] == "G")
    print()
    print("nodi citati nella domanda:  %s" % (", ".join(
        "%s (per '%s')" % (m["node_id"], m["matched_name"]) for m in graph_row["graph_question_node_matches"]
    ) or "(nessuno)"))
    print("nodi dalle voci di memoria: %s" % (", ".join(
        "%s (da %s)" % (m["node_id"], m["from_entry"]) for m in graph_row["graph_entry_node_matches"]
    ) or "(nessuno)"))
    print("coppie esaminate: %d | limite: %d collegamenti"
          % (len(graph_row["graph_pairs_searched"]), graph_row["graph_max_hops"]))
    print()
    print("percorsi topologici trovati (fra i nodi iniziali, non la catena della domanda):")
    for path in graph_row["graph_topological_paths_found"]:
        print("  %s  %s -> %s  (%d collegamenti: %s)  nel contesto: %s%s"
              % (path["path_id"], path["pair"][0], path["pair"][1], path["hops"],
                 ", ".join(path["edge_ids"]), "si" if path["in_context"] else "NO",
                 "" if path["in_context"] else " — mancano %s" % ", ".join(path["missing_edge_ids"])))
    for scarto in graph_row["graph_topological_paths_discarded"]:
        print("  scartato  %s -> %s: %s" % (scarto["pair"][0], scarto["pair"][1], scarto["reason"]))
    print()
    if graph_row["graph_topological_paths_complete_in_context"]:
        print("Tutti i percorsi TOPOLOGICI trovati entrano interi nel budget: %d token su %d."
              % (graph_row["context_tokens"], graph_row["budget_tokens"]))
        print("Vuol dire solo questo: gli archi che il retriever ha trovato ci sono tutti.")
        print("NON vuol dire che il contesto contenga tutte le relazioni richieste dalla")
        print("domanda, ne' che il contenuto sia corretto, ne' che la risposta sara' completa.")
    else:
        print("ATTENZIONE: almeno un percorso topologico NON entra interamente nel budget "
              "(%d token su %d)." % (graph_row["context_tokens"], graph_row["budget_tokens"]))
        print("Il percorso resta registrato come incompleto: non viene troncato ne' dato per riuscito.")
    print()
    print("archi effettivamente selezionati: %s"
          % (", ".join(graph_row["graph_selected_edge_ids"]) or "(nessuno)"))
    print("archi non selezionati e perche':")
    for escluso in graph_row["graph_unselected_edges"]:
        print("  %-12s %s" % (escluso["edge_id"], escluso["reason"]))
    show_context(inputs, UG_QUESTION, ("U", "G"))

    print()
    print("-" * 78)
    print("Copertura delle relazioni richieste dall'annotazione (fase di valutazione)")
    print("-" * 78)
    print("Il percorso topologico dice solo che gli archi trovati dal retriever sono")
    print("entrati nel budget. Se le relazioni richieste dalla domanda siano davvero")
    print("nel contesto si misura qui, dopo il retrieval, contro l'oracle.")
    for mode in ("U", "G", rq2.FULL_HISTORY):
        riga = next((r for r in template
                     if r["question_id"] == UG_QUESTION and r["mode"] == mode), None)
        if riga is None:
            continue
        print()
        print("--- %s ---" % mode)
        print("catena esplicativa richiesta: %s" % " -> ".join(riga["required_relation_chain"]))
        for relazione in riga["required_relations"]:
            print("  %-10s %-48s provenienza=%-5s archi=%-14s contenuto=%s"
                  % (relazione["relation_id"], relazione["triple"][:48],
                     relazione["relation_present_by_provenance"],
                     ",".join(relazione["selected_edges_with_shared_provenance"]) or "-",
                     relazione["relation_content_correct"]))
        print("  coperte solo per provenienza: %s"
              % (", ".join(riga["relations_present_by_provenance"]) or "(nessuna)"))
        print("  mancanti:                     %s"
              % (", ".join(riga["relations_missing_by_provenance"]) or "(nessuna)"))
        print("  catena coperta per provenienza: %s" % riga["relation_chain_covered_by_provenance"])
        print("  giudizi semantici ancora da compilare: relation_content_correct e "
              "relation_retrieved = null per tutte")
        print("  evidence_complete: %s" % riga["evidence_complete"])
    print()
    print("Nota diagnostica sulla fixture: con il grafo di fixture, G non porta nel")
    print("contesto le relazioni su URL-01, quindi SC04-Q3 NON possiede tutta l'evidenza")
    print("richiesta. E' un esito di retrieval da osservare, non un guasto della pipeline:")
    print("il retriever non viene adattato per farlo passare.")
    print("La copertura per provenienza e' inoltre grossolana: un arco puo' condividere il")
    print("messaggio sorgente di una relazione senza rappresentarla. Per questo")
    print("relation_content_correct resta null e va annotato a mano.")

    step(11, "Politica corrente/storia applicata anche agli archi")
    print("La stessa regola che filtra le voci di U filtra gli archi di G.")
    print("%-11s %-9s %-9s %s" % ("domanda", "lettura", "archi", "archi non leggibili"))
    for question_id in ("SC04-Q3", "SC04-Q4", "SC04-Q2"):
        riga = next(r for r in rows if r["question_id"] == question_id and r["mode"] == "G")
        nascosti = [e["edge_id"] for e in riga["graph_unselected_edges"]
                    if e["reason"].startswith("stato ")]
        print("%-11s %-9s %-9d %s"
              % (question_id, riga["reading_scope"], len(riga["graph_readable_edge_ids"]),
                 ", ".join(nascosti) or "(nessuno)"))
    superati = [e for e in graph["edges"] if e["state"] != rq2.STATE_ACTIVE]
    for edge in superati:
        corrente = next(r for r in rows if r["question_id"] == "SC04-Q3" and r["mode"] == "G")
        storica = next(r for r in rows if r["question_id"] == "SC04-Q2" and r["mode"] == "G")
        print()
        print("arco %s (%s -%s-> %s), stato %s:"
              % (edge["edge_id"], edge["subject"], edge["relation"], edge["object"], edge["state"]))
        print("  domanda corrente (SC04-Q3): leggibile = %s"
              % (edge["edge_id"] in corrente["graph_readable_edge_ids"]))
        print("  domanda storica  (SC04-Q2): leggibile = %s"
              % (edge["edge_id"] in storica["graph_readable_edge_ids"]))

    step(12, "Il pilot di RQ1 non e' stato toccato")
    after = pilot_fingerprint()
    changed = sorted(k for k in before if before[k] != after.get(k))
    missing = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    if changed or missing or added:
        for name in changed:
            print("MODIFICATO: %s" % name)
        for name in missing:
            print("SCOMPARSO: %s" % name)
        for name in added:
            print("AGGIUNTO: %s" % name)
        print("\nLa verifica ha toccato file del pilot: e' un errore.")
        return 1
    print("%d file del pilot confrontati per impronta: tutti invariati." % len(before))

    print()
    print("=" * 78)
    print("Verifica offline completata. Output in %s" % rq2.relative(OUT_DIR))
    print("Ricorda: dati da fixture, non risultati sperimentali; annotazioni non approvate;")
    print("protocollo non congelato; nessuna generazione finale eseguita.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
