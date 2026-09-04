#!/usr/bin/env python3
"""Modello di annotazione per la valutazione di RQ2.

Produce una riga per ogni prova (scenario x domanda x modalita') con:

  - quello che si puo' calcolare automaticamente: che cosa c'era in memoria, che
    cosa e' entrato nel contesto, quanti token, con quale provenienza;
  - quello che deve essere annotato a mano: `null` nei campi di giudizio.

Serve a distinguere i tre casi che la roadmap chiede di non confondere:

  1. **fatto perso o alterato nell'estrazione** — il messaggio sorgente esiste ed
     e' stato letto, ma il fatto in memoria non conserva il contenuto richiesto.
     Si riconosce da `fact_in_memory_by_provenance = true` con
     `fact_preserved_in_memory = false`;
  2. **fatto conservato ma non recuperato** — il fatto e' in memoria con il
     contenuto giusto, ma non entra nel contesto entro il budget. Si riconosce
     da `fact_preserved_in_memory = true` con `fact_in_context = false`;
  3. **risposta errata nonostante l'evidenza disponibile** — il fatto e' nel
     contesto ed e' corretto, ma la risposta e' sbagliata. Si riconosce da
     `fact_content_correct_in_context = true` con `answer_class` diversa da
     `completa`.

Per le domande che dichiarano relazioni obbligatorie viene prodotta anche una
traccia per relazione: quali elementi selezionati ne condividono la provenienza,
se la relazione risulta coperta *per provenienza*, e i due giudizi semantici da
compilare a mano.

La corrispondenza di provenienza e' un indizio, non una prova: il collegamento a
un `message_id` non dimostra che il fatto o la relazione ne conservino il
contenuto. Per questo `fact_preserved_in_memory`,
`fact_content_correct_in_context`, `relation_content_correct` e
`relation_retrieved` nascono `null` e devono essere compilati leggendo il testo.

`evidence_complete` non diventa mai `true` da solo: vale `false` quando manca
gia' per provenienza almeno un fatto o una relazione obbligatoria (una prova
negativa e' sufficiente), e resta `null` quando la provenienza c'e' ma la
correttezza del contenuto non e' ancora stata verificata a mano.

Le annotazioni vengono lette **soltanto qui**, in fase di valutazione: non
entrano nella costruzione dei fatti, nella gestione di U, nella costruzione del
grafo, nella selezione dei nodi, nella ricerca dei percorsi, nel ranking o nel
prompt di risposta.

Uso:
    python3 scripts/rq2/build_annotation_template_rq2.py \
        --retrieval results/rq2/retrieval_rq2.jsonl \
        --inputs results/rq2/generation_inputs_rq2.jsonl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import build_memory_updates as memory  # noqa: E402
import build_graph as graph_memory  # noqa: E402

DEFAULT_RETRIEVAL = rq2.RQ2_RESULTS_DIR / "retrieval_rq2.jsonl"
DEFAULT_INPUTS = rq2.RQ2_RESULTS_DIR / "generation_inputs_rq2.jsonl"
DEFAULT_OUT = rq2.RQ2_RESULTS_DIR / "annotation_template_rq2.jsonl"

ANSWER_CLASSES = ("completa", "parziale", "errata", "astensione corretta")
ERROR_ORIGINS = ("raggiungibilita", "estrazione", "gestione", "grafo", "retrieval",
                 "risposta", "benchmark", "nessuno")
FACT_MEMORY_MODES = ("F", "U", "G")


def memory_provenance(mode, scenario_id, sources):
    """message_id coperti dalla memoria completa della modalita'.

    Si guarda la provenienza dichiarata da *tutta* la memoria, non solo dagli
    elementi finiti nel contesto: e' quello che distingue "il fatto non e' mai
    arrivato in memoria" da "il fatto c'era ma non e' stato recuperato".

      - T e FULL_HISTORY: i messaggi originali;
      - F: i fatti estratti;
      - U: le voci di memoria, attive e in archivio;
      - G: i nodi e gli archi del grafo.
    """
    covered = set()
    if mode == "F" and sources.get("facts"):
        for fact in rq2.read_jsonl(rq2.REPO_ROOT / sources["facts"]):
            covered.update(fact["source_message_ids"])
        return covered
    if mode == "U" and sources.get("state"):
        for entry in memory.load_state(rq2.REPO_ROOT / sources["state"]):
            covered.update(entry["source_message_ids"])
        return covered
    if mode == "G" and sources.get("graph"):
        graph = graph_memory.load_graph(rq2.REPO_ROOT / sources["graph"])
        for element in graph["nodes"] + graph["edges"]:
            covered.update(element["source_message_ids"])
        return covered
    scenario = rq2.load_scenario(scenario_id)
    return {entry["message_id"] for entry in rq2.user_messages(scenario)}


def relation_trace(question, annotation, selected_items):
    """Traccia per ogni relazione obbligatoria, dopo che il retrieval e' finito.

    `relation_present_by_provenance` dice soltanto che nel contesto c'e' almeno
    un elemento che dichiara di venire da tutti i messaggi sorgente della
    relazione. Non dimostra che la relazione sia stata rappresentata
    correttamente: per quello ci sono i due campi da annotare a mano.
    """
    relations = {}
    graph_block = (annotation or {}).get("graph_annotation") or {}
    for relation in graph_block.get("relations", []):
        relations[relation["relation_id"]] = relation

    rows = []
    for relation_id in question["required_relations"]:
        relation = relations.get(relation_id)
        if relation is None:
            rows.append({"relation_id": relation_id, "problem": "relazione non dichiarata"})
            continue
        sources = list(relation["source_message_ids"])
        sharing = [
            item for item in selected_items
            if sources and all(source in item["source_message_ids"] for source in sources)
        ]
        rows.append({
            "relation_id": relation_id,
            "triple": "%s -%s-> %s" % (relation["subject"], relation["predicate"], relation["object"]),
            "text": relation["predicate"],
            "source_message_ids": sources,
            "selected_items_with_shared_provenance": [item["item_id"] for item in sharing],
            "selected_edges_with_shared_provenance": [
                item["item_id"] for item in sharing if item.get("unit") == "arco"
            ],
            "relation_present_by_provenance": bool(sharing),
            # da annotare a mano leggendo il contesto
            "relation_content_correct": None,
            "relation_retrieved": None,
            "annotator_note": None,
        })
    return rows


def build(input_rows, retrieval_rows):
    retrieval = {(r["scenario_id"], r["question_id"], r["mode"]): r for r in retrieval_rows}
    questions = {}
    annotations = {}
    memory_cache = {}
    rows = []

    for row in input_rows:
        scenario_id = row["scenario_id"]
        if scenario_id not in questions:
            questions[scenario_id] = {q["question_id"]: q for q in rq2.load_questions(scenario_id)}
            annotations[scenario_id] = rq2.load_annotation_file(scenario_id)
        question = questions[scenario_id][row["question_id"]]
        mode = row["mode"]
        source = retrieval.get((scenario_id, row["question_id"], mode))
        sources = {
            "facts": source["facts_source"] if source else None,
            "state": source.get("state_source") if source else None,
            "graph": source.get("graph_source") if source else None,
        }

        cache_key = (scenario_id, mode, sources["facts"], sources["state"], sources["graph"])
        if cache_key not in memory_cache:
            memory_cache[cache_key] = memory_provenance(mode, scenario_id, sources)
        in_memory = memory_cache[cache_key]

        context_provenance = set(row["context_provenance_message_ids"])
        fact_rows = []
        for fact in question["required_facts"]:
            sources = list(fact["source_message_ids"])
            fact_rows.append(
                {
                    "fact_key": fact["fact_key"],
                    "text": fact["text"],
                    "kind": fact["kind"],
                    "negated": fact["negated"],
                    "source_message_ids": sources,
                    # automatico: la provenienza dice soltanto che i messaggi
                    # giusti sono stati letti e sono citati.
                    "fact_in_memory_by_provenance": all(s in in_memory for s in sources),
                    "fact_in_context_by_provenance": all(s in context_provenance for s in sources),
                    # da annotare a mano leggendo il testo.
                    "fact_preserved_in_memory": None,
                    "fact_content_correct_in_context": None,
                    "annotator_note": None,
                }
            )

        selected_items = source["selected"] if source else [
            {"item_id": item_id, "source_message_ids": [item_id], "unit": "messaggio"}
            for item_id in row["context_item_ids"]
        ]
        relations = relation_trace(question, annotations[scenario_id], selected_items)
        missing_relations = [r["relation_id"] for r in relations
                             if not r.get("relation_present_by_provenance")]
        missing_facts = [f["fact_key"] for f in fact_rows if not f["fact_in_context_by_provenance"]]
        # Prova negativa sufficiente: se manca gia' la provenienza, l'evidenza non
        # e' completa. Il contrario non vale: la provenienza non basta a dichiararla
        # completa, quindi in quel caso il campo resta da compilare.
        evidence_complete = False if (missing_relations or missing_facts) else None

        rows.append(
            {
                "scenario_id": scenario_id,
                "question_id": row["question_id"],
                "question_category": question["category"],
                "mode": mode,
                "label": row.get("retrieval_label") or "senza retrieval",
                "memory_unit": source["memory_unit"] if source else "messaggio",
                "memory_items": source["memory_items"] if source else len(in_memory),
                "reading_scope": row.get("reading_scope"),
                "graph_seed_node_ids": (source or {}).get("graph_seed_node_ids", []),
                "graph_path": (source or {}).get("graph_path", []),
                "context_item_ids": list(row["context_item_ids"]),
                "context_items": len(row["context_item_ids"]),
                "context_tokens": row["context_tokens"],
                "context_content_tokens": row["context_content_tokens"],
                "context_overhead_tokens": row["context_overhead_tokens"],
                "budget_applies": row["budget_applies"],
                "budget_tokens": row["budget_tokens"],
                "fact_present_in_corpus": question["fact_present_in_corpus"],
                "expected_behavior": question["expected_behavior"],
                "obsolete_information": list(question["obsolete_information"]),
                "accepted_equivalents": list(question["accepted_equivalents"]),
                "required_relation_ids": list(question["required_relations"]),
                "required_relation_chain": list(question["required_relation_chain"]),
                "required_state_keys": list(question["required_state_keys"]),
                "required_facts": fact_rows,
                "required_relations": relations,
                "relations_present_by_provenance": [
                    r["relation_id"] for r in relations if r.get("relation_present_by_provenance")
                ],
                "relations_missing_by_provenance": missing_relations,
                "relation_chain_covered_by_provenance": (
                    None if not question["required_relation_chain"]
                    else all(rid not in missing_relations for rid in question["required_relation_chain"])
                ),
                "facts_missing_by_provenance": missing_facts,
                "evidence_complete": evidence_complete,
                "evidence_complete_rule": (
                    "false quando manca gia' per provenienza un fatto o una relazione obbligatoria; "
                    "null quando la provenienza c'e' ma la correttezza del contenuto non e' stata "
                    "ancora verificata a mano. Non diventa mai true automaticamente."
                ),
                # Giudizio sulla risposta: tutto da compilare a mano.
                "answer_class": None,
                "obsolete_used": None,
                "unsupported_claim": None,
                "wrong_abstention": None,
                "error_origin": None,
                "annotator_note": None,
                "allowed_answer_class": list(ANSWER_CLASSES),
                "allowed_error_origin": list(ERROR_ORIGINS),
                "diagnosis_order": [
                    "raggiungibilita: l'evidenza non e' nelle sorgenti ammesse",
                    "estrazione: evidenza presente nei messaggi ma persa o alterata in memoria",
                    "gestione: evidenza estratta ma persa dalle operazioni di aggiornamento (solo U e G)",
                    "grafo: evidenza in memoria ma non rappresentata da nodi e archi (solo G)",
                    "retrieval: evidenza conservata in memoria ma non entrata nel contesto",
                    "risposta: evidenza nel contesto ma risposta non corretta",
                    "benchmark: domanda o annotazione difettosa",
                ],
                "warning": (
                    "I campi *_by_provenance sono automatici e basati sugli identificatori: "
                    "non dimostrano che il contenuto del fatto sia stato conservato."
                ),
            }
        )
    return rows


def print_summary(rows):
    print("%-13s %-13s %-7s %-11s %-11s %s"
          % ("scenario", "modalita'", "righe", "fatti", "relazioni", "campi manuali"))
    keys = []
    for row in rows:
        key = (row["scenario_id"], row["mode"])
        if key not in keys:
            keys.append(key)
    for scenario_id, mode in keys:
        subset = [r for r in rows if r["scenario_id"] == scenario_id and r["mode"] == mode]
        facts = sum(len(r["required_facts"]) for r in subset)
        relations = sum(len(r["required_relations"]) for r in subset)
        manual = facts * 2 + relations * 2 + len(subset) * 5
        print("%-13s %-13s %-7d %-11d %-11d %d"
              % (scenario_id, mode, len(subset), facts, relations, manual))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Costruisce il modello di annotazione della valutazione RQ2.")
    parser.add_argument("--retrieval", default=str(DEFAULT_RETRIEVAL))
    parser.add_argument("--inputs", default=str(DEFAULT_INPUTS))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    for path in (args.retrieval, args.inputs):
        if not Path(path).exists():
            print("File mancante: %s" % rq2.relative(path), file=sys.stderr)
            return 1

    rows = build(rq2.read_jsonl(args.inputs), rq2.read_jsonl(args.retrieval))
    path = rq2.write_jsonl(rows, args.out)

    print("Modello di annotazione RQ2 (tutti i giudizi sono null: vanno compilati a mano)")
    print("-" * 78)
    print_summary(rows)
    print("-" * 78)
    print("Scritto in %s (%d righe)." % (rq2.relative(path), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
