#!/usr/bin/env python3
"""Retrieval dell'esperimento principale RQ2 per T, F, U e G.

Esegue soltanto il *recupero*: non costruisce prompt, non chiama nessun modello
e non genera risposte.

Che cosa cambia da una modalita' all'altra:

  - **T**: l'unita' recuperabile e' il messaggio originale;
  - **F**: e' il fatto estratto, con la sua provenienza;
  - **U**: e' la voce di memoria con il suo stato temporale; quali voci siano
    leggibili dipende dalla politica dichiarata in
    `scripts/rq2/build_memory_updates.py` (stato corrente oppure storia, decisa
    dal solo testo della domanda);
  - **G**: parte dalla stessa memoria di U e aggiunge l'espansione relazionale
    sul grafo.

Il metodo di ranking resta quello del pilot (TF-IDF / coseno) per T, F e U, cosi'
le differenze osservate riguardano la memoria e non il retriever. G aggiunge il
passo relazionale, che e' proprio la differenza architetturale in esame.

Il taglio non e' un top-k fisso ma un **budget in token applicato al blocco di
contesto realmente formattato**: testo, identificatori, provenienza, stato
temporale e relazioni. Vengono registrati token del contenuto, token
dell'overhead strutturale, totale, elemento che ha causato l'arresto ed eventuale
superamento dovuto al primo elemento.

FULL_HISTORY non compare qui: non usa retrieval e sta fuori dal budget.

Uso:
    python3 scripts/rq2/run_retrieval_rq2.py --scenario scenario_02
    python3 scripts/rq2/run_retrieval_rq2.py --scenario scenario_03 \
        --facts results/rq2/facts/scenario_03_facts.jsonl \
        --state results/rq2/memory/scenario_03_state.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import extract_facts  # noqa: E402
import build_memory_updates as memory  # noqa: E402
import build_graph as graph_memory  # noqa: E402

DEFAULT_OUT = rq2.RQ2_RESULTS_DIR / "retrieval_rq2.jsonl"
RETRIEVAL_MODES = ("T", "F", "U", "G")


# --------------------------------------------------------------------------
# Elementi di memoria
# --------------------------------------------------------------------------

def fact_items(facts):
    """F: un elemento per fatto estratto, con la sua provenienza."""
    items = []
    for fact in facts:
        items.append(
            rq2.make_item(
                item_id=fact["fact_id"],
                text=fact["text"],
                render=rq2.render_fact(fact["fact_id"], fact["source_message_ids"], fact["text"]),
                session_order=fact["session_order"],
                item_order=fact["order"],
                source_message_ids=fact["source_message_ids"],
                source_fact_ids=[fact["fact_id"]],
                unit="fatto",
                extra={"kind": fact.get("kind"), "negated": fact.get("negated")},
            )
        )
    items.sort(key=lambda item: (item["session_order"], item["item_order"]))
    return items


# --------------------------------------------------------------------------
# Una prova
# --------------------------------------------------------------------------

def _selected_records(selection):
    return [
        {
            "item_id": item["item_id"],
            "rank": item["rank"],
            "score": item["score"],
            "tokens": item["tokens"],
            "content_tokens": item["content_tokens"],
            "overhead_tokens": item["overhead_tokens"],
            "render": item["render"],
            "unit": item["unit"],
            "state": item.get("state"),
            "source_message_ids": item["source_message_ids"],
            "source_fact_ids": item.get("source_fact_ids", []),
        }
        for item in selection["selected"]
    ]


def evaluate(scenario_id, question, mode, budget, sources, memory_context, label="esecuzione"):
    """Una combinazione scenario x domanda x modalita'."""
    extra = {}

    if mode == "G":
        trace = graph_memory.retrieve(
            question["text"], memory_context["graph"], memory_context["entries"], budget)
        ranked, selection = trace["ranked"], trace["selection"]
        memory_items = len(memory_context["graph"]["nodes"]) + len(memory_context["graph"]["edges"])
        memory_unit = "nodi e archi"
        extra = {
            "reading_scope": trace["scope"],
            "graph_seed_item_ids": trace["seed_item_ids"],
            "graph_question_node_ids": trace["question_node_ids"],
            "graph_question_node_matches": trace["question_node_matches"],
            "graph_entry_node_ids": trace["entry_node_ids"],
            "graph_entry_node_matches": trace["entry_node_matches"],
            "graph_seed_node_ids": trace["anchor_node_ids"],
            "graph_pairs_searched": trace["pairs_searched"],
            "graph_topological_paths_found": trace["topological_paths_found"],
            "graph_topological_paths_discarded": trace["topological_paths_discarded"],
            "graph_topological_paths_complete_in_context": trace["topological_paths_complete_in_context"],
            "graph_readable_edge_ids": trace["readable_edge_ids"],
            "graph_hidden_edge_ids": trace["hidden_edge_ids"],
            "graph_selected_edge_ids": trace["selected_edge_ids"],
            "graph_unselected_edges": trace["unselected_edges"],
            "graph_path": trace["path"],
            "graph_max_hops": trace["max_hops"],
            "graph_max_seed_items": trace["max_seed_items"],
            "graph_max_seed_nodes": trace["max_seed_nodes"],
        }
    else:
        if mode == "U":
            scope = memory.question_scope(question["text"])
            items = memory.state_items(memory_context["entries"], scope)
            memory_items = len(memory_context["entries"])
            memory_unit = "fatto con stato"
            extra = {"reading_scope": scope, "readable_items": len(items)}
        else:
            items = memory_context["items"]
            memory_items = len(items)
            memory_unit = items[0]["unit"] if items else None
        ranked = rq2.rank_items(question["text"], items)
        selection = rq2.select_within_budget(ranked, budget)

    selected = selection["selected"]
    provenance = []
    for item in selected:
        for message_id in item["source_message_ids"]:
            if message_id not in provenance:
                provenance.append(message_id)

    required_evidence = list(question["required_evidence_ids"])
    facts_trace = []
    for fact in question["required_facts"]:
        wanted = list(fact["source_message_ids"])
        matching = [
            item["item_id"] for item in selected
            if all(source in item["source_message_ids"] for source in wanted)
        ]
        facts_trace.append(
            {
                "fact_key": fact["fact_key"],
                "text": fact["text"],
                "source_message_ids": wanted,
                "items_with_matching_provenance": matching,
                "provenance_match": bool(matching),
                "content_match": None,
            }
        )

    row = {
        "scenario_id": scenario_id,
        "question_id": question["question_id"],
        "question_category": question["category"],
        "mode": mode,
        "label": label,
        "facts_source": sources.get("facts"),
        "state_source": sources.get("state"),
        "graph_source": sources.get("graph"),
        "memory_unit": memory_unit,
        "memory_items": memory_items,
        "budget_tokens": budget,
        "context_tokens": selection["context_tokens"],
        "context_content_tokens": selection["content_tokens"],
        "context_overhead_tokens": selection["overhead_tokens"],
        "context_items": len(selected),
        "selected_item_ids": [item["item_id"] for item in selected],
        "selected": _selected_records(selection),
        "ranking": [
            {"item_id": item["item_id"], "rank": item["rank"], "score": item["score"],
             "tokens": item["tokens"], "unit": item["unit"]}
            for item in ranked
        ],
        "stopped_by": selection["stopped_by"],
        "budget_exceeded_by_first_item": selection["budget_exceeded_by_first_item"],
        "context_provenance_message_ids": provenance,
        "required_evidence_ids": required_evidence,
        "evidence_in_context_by_provenance": [m for m in required_evidence if m in provenance],
        "evidence_provenance_complete": (
            None if not question["fact_present_in_corpus"]
            else all(m in provenance for m in required_evidence)
        ),
        "required_facts_trace": facts_trace,
        "fact_present_in_corpus": question["fact_present_in_corpus"],
        "expected_behavior": question["expected_behavior"],
        "provenance_warning": (
            "La corrispondenza di provenienza non dimostra che il fatto sia stato "
            "conservato correttamente: content_match va annotato a mano."
        ),
    }
    row.update(extra)
    return row


# --------------------------------------------------------------------------
# Preparazione della memoria
# --------------------------------------------------------------------------

def prepare(scenario, mode, paths):
    """Memoria della modalita'. Restituisce (contesto, sorgenti, motivo_salto)."""
    scenario_id = scenario["scenario_id"]

    if mode == "T":
        return {"items": rq2.message_items(scenario)}, {}, None

    facts_file = Path(paths.get("facts") or extract_facts.facts_path(scenario_id))
    if not facts_file.exists():
        return None, {}, "fatti candidati mancanti: %s" % rq2.relative(facts_file)
    facts = rq2.read_jsonl(facts_file)
    sources = {"facts": rq2.relative(facts_file)}

    if mode == "F":
        return {"items": fact_items(facts)}, sources, None

    state_file = Path(paths.get("state") or memory.state_path(scenario_id))
    if not state_file.exists():
        return None, sources, "stato di U mancante: %s" % rq2.relative(state_file)
    entries = memory.load_state(state_file)
    sources["state"] = rq2.relative(state_file)

    if mode == "U":
        return {"entries": entries}, sources, None

    graph_file = Path(paths.get("graph") or graph_memory.graph_path(scenario_id))
    if not graph_file.exists():
        return None, sources, "grafo mancante: %s" % rq2.relative(graph_file)
    sources["graph"] = rq2.relative(graph_file)
    return {"entries": entries, "graph": graph_memory.load_graph(graph_file)}, sources, None


def run(scenario_ids, config, paths_by_scenario=None, label="esecuzione", modes=None):
    budget = rq2.budget_tokens(config)
    paths_by_scenario = paths_by_scenario or {}
    rows, skipped = [], []

    for scenario_id in scenario_ids:
        scenario = rq2.load_scenario(scenario_id)
        questions = rq2.load_questions(scenario_id)
        runnable = modes if modes is not None else rq2.runnable_modes(scenario_id, config)
        paths = paths_by_scenario.get(scenario_id, {})

        for mode in RETRIEVAL_MODES:
            if mode not in runnable:
                continue
            context, sources, problem = prepare(scenario, mode, paths)
            if problem:
                skipped.append((scenario_id, mode, problem))
                continue
            for question in questions:
                rows.append(evaluate(scenario_id, question, mode, budget, sources, context, label))
    return rows, skipped


# --------------------------------------------------------------------------
# Riepilogo
# --------------------------------------------------------------------------

def print_summary(rows):
    print("%-13s %-5s %-7s %-9s %-9s %-9s %s"
          % ("scenario", "mod.", "prove", "elementi", "contenuto", "overhead", "provenienza completa"))
    keys = []
    for row in rows:
        key = (row["scenario_id"], row["mode"])
        if key not in keys:
            keys.append(key)
    for scenario_id, mode in keys:
        subset = [r for r in rows if r["scenario_id"] == scenario_id and r["mode"] == mode]
        applicable = [r for r in subset if r["evidence_provenance_complete"] is not None]
        complete = [r for r in applicable if r["evidence_provenance_complete"]]
        coverage = ("%d/%d" % (len(complete), len(applicable))) if applicable else "non applicabile"
        print("%-13s %-5s %-7d %-9.1f %-9.1f %-9.1f %s" % (
            scenario_id, mode, len(subset),
            sum(r["context_items"] for r in subset) / len(subset),
            sum(r["context_content_tokens"] for r in subset) / len(subset),
            sum(r["context_overhead_tokens"] for r in subset) / len(subset),
            coverage,
        ))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Retrieval RQ2 per T, F, U e G, entro il budget effettivo.")
    parser.add_argument("--scenario", action="append", default=None)
    parser.add_argument("--facts", default=None, help="fatti candidati per F, U e G")
    parser.add_argument("--state", default=None, help="stato di U per U e G")
    parser.add_argument("--graph", default=None, help="grafo per G")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--label", default="esecuzione")
    parser.add_argument("--modes", nargs="*", default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = rq2.load_config()
    scenario_ids = args.scenario or list(rq2.SCENARIO_IDS)

    paths_by_scenario = {}
    if args.facts or args.state or args.graph:
        if len(scenario_ids) != 1:
            print("--facts, --state e --graph richiedono un solo --scenario", file=sys.stderr)
            return 1
        paths_by_scenario[scenario_ids[0]] = {
            "facts": args.facts, "state": args.state, "graph": args.graph}

    rows, skipped = run(scenario_ids, config, paths_by_scenario, args.label, args.modes)

    print("Retrieval RQ2 — budget %d token sul contesto formattato, metodo %s"
          % (rq2.budget_tokens(config), config["retrieval"]["method"]))
    if args.label != "esecuzione":
        print("ATTENZIONE: etichetta '%s'. Non sono risultati sperimentali." % args.label)
    print("-" * 78)
    if rows:
        print_summary(rows)
    else:
        print("Nessuna prova eseguita.")
    print("-" * 78)
    for scenario_id, mode, reason in skipped:
        print("saltato: %s / %s — %s" % (scenario_id, mode, reason))
    if not rows:
        return 1

    path = rq2.write_jsonl(rows, args.out)
    print("Risultati scritti in %s (%d righe)." % (rq2.relative(path), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
