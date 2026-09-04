#!/usr/bin/env python3
"""Memoria a grafo (architettura G) e recupero relazionale.

G non riparte dalle conversazioni: usa **gli stessi fatti candidati** di F e U e
**lo stesso stato aggiornato** prodotto da U. L'unica cosa che aggiunge e'
l'organizzazione in entita' e relazioni, piu' una procedura di recupero che
segue i collegamenti.

Che cosa vede il costruttore del grafo:
  - i fatti candidati dello scenario;
  - le voci di memoria di U con il loro stato (attivo, superato, ritirato).

Che cosa NON vede mai: domande di valutazione, oracle, `required_relations`,
`required_relation_chain`, relazioni attese.

Il grafo e' un file JSON con nodi e archi: liste e dizionari, nessun database.

Recupero relazionale, deterministico. G parte dalla stessa memoria di U e
aggiunge soltanto il passo relazionale, cosi' il confronto U/G isola quella
differenza:

  1. **nodi citati nella domanda**: i nodi il cui identificatore, alias o
     etichetta compare nel testo della domanda come sequenza contigua di parole;
  2. **nodi dalle voci di memoria**: i nodi citati dalle prime `max_seed_items`
     voci di U in ordine di punteggio, o che ne condividono un fatto sorgente;
  3. **percorsi minimi** fra tutte le coppie di nodi iniziali, cercati con una
     visita in ampiezza deterministica (vicini in ordine di identificatore
     dell'arco) e limitati a `max_hops` collegamenti;
  4. **priorita' nel budget** agli archi che compongono quei percorsi, poi alle
     voci di memoria iniziali, poi agli altri archi pertinenti (incidenti a un
     nodo toccato), poi alle restanti voci;
  5. **arresto** con la stessa regola di budget delle altre modalita'.

La politica di lettura di U vale anche per gli archi: in una domanda sullo stato
corrente sono attraversabili soltanto gli archi `attivo`; in una domanda storica
entrano anche `superato` e `ritirato`, con lo stato scritto nel contesto. La
scelta dipende solo dal testo della domanda.

Se un percorso non entra per intero nel budget non viene troncato ne' dato per
riuscito: resta registrato come incompleto.

Attenzione al significato di "completo": `topological_paths_complete_in_context`
dice soltanto che **tutti gli archi dei percorsi topologici trovati dal
retriever** sono entrati nel budget. Non dice che il contesto contenga tutte le
relazioni richieste dalla domanda, ne' che il contenuto recuperato sia corretto,
ne' che la risposta sara' completa. Un grafo puo' collegare due nodi con una
scorciatoia corretta ma insufficiente a spiegare il caso: la copertura delle
relazioni richieste si misura dopo, in fase di valutazione, contro l'oracle.

Nessun passaggio guarda oracle, `required_relations`, `required_relation_chain` o risposte
attese: la selezione dei nodi iniziali usa soltanto il testo della domanda e il
contenuto del grafo.

Uso:
    python3 scripts/rq2/build_graph.py --scenario scenario_04 --dry-run
    python3 scripts/rq2/build_graph.py --scenario scenario_04
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import extract_facts  # noqa: E402
import build_memory_updates as memory  # noqa: E402

sys.path.insert(0, str(rq2.SCRIPTS_DIR))
import run_generation as gen  # noqa: E402

GRAPH_DIR = rq2.RQ2_RESULTS_DIR / "graph"

DEFAULT_MAX_HOPS = 3
DEFAULT_MAX_SEED_ITEMS = 3
DEFAULT_MAX_SEED_NODES = 3

GRAPH_INSTRUCTIONS = (
    "Sei il componente che organizza la memoria di un caso come rete di entita' e relazioni.\n"
    "Ricevi i fatti gia' estratti e le voci di memoria con il loro stato. Devi produrre nodi e archi.\n"
    "\n"
    "Regole:\n"
    "1. Un nodo per ogni entita' concreta citata dai fatti: persone, messaggi, collegamenti, account,\n"
    "   eventi, destinazioni. Usa come identificatore quello gia' presente nei fatti quando esiste\n"
    "   (per esempio SMS-01, ACC-207); altrimenti scegline uno breve e stabile.\n"
    "2. Un arco per ogni relazione affermata dai fatti, con un predicato breve.\n"
    "3. Non inventare entita' o relazioni che i fatti non affermano.\n"
    "4. Lo stato di un arco e' `attivo` se la relazione vale ancora, `superato` se e' stata\n"
    "   sostituita da un'informazione piu' recente, `ritirato` se e' stata ritirata.\n"
    "5. Ogni nodo e ogni arco devono indicare i fatti da cui provengono, con i loro identificatori.\n"
    "\n"
    "Rispondi soltanto con un oggetto JSON, senza testo prima o dopo:\n"
    "{\"nodes\": [{\"node_id\": \"...\", \"type\": \"...\", \"label\": \"...\", \"aliases\": [],\n"
    "             \"source_fact_ids\": [\"...\"]}],\n"
    " \"edges\": [{\"subject\": \"...\", \"relation\": \"...\", \"object\": \"...\",\n"
    "             \"state\": \"attivo\", \"source_fact_ids\": [\"...\"]}]}\n"
)


# --------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------

def format_facts(facts):
    return "\n".join(
        "[%s] %s (da: %s)" % (fact["fact_id"], fact["text"], ", ".join(fact["source_message_ids"]))
        for fact in facts
    )


def format_entries(entries):
    return "\n".join(
        "[%s] (%s) %s — %s (da fatti: %s)"
        % (entry["entry_id"], entry["claim_key"], entry["value"], entry["status"],
           ", ".join(entry["source_fact_ids"]))
        for entry in entries
    )


def build_graph_prompt(facts, entries):
    return (
        "Istruzioni:\n"
        "%s\n"
        "\n"
        "Fatti del caso:\n"
        "%s\n"
        "\n"
        "Voci di memoria con il loro stato:\n"
        "%s"
    ) % (GRAPH_INSTRUCTIONS, format_facts(facts), format_entries(entries))


# --------------------------------------------------------------------------
# Costruzione del grafo
# --------------------------------------------------------------------------

def parse_graph(answer):
    """Legge l'oggetto JSON con nodi e archi. Restituisce (grafo, errore)."""
    import json
    if not answer:
        return None, "risposta vuota"
    text = answer.strip()
    match = extract_facts.FENCE_RE.search(text)
    if match:
        text = match.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None, "nessun oggetto JSON nella risposta: %s" % text[:200]
    try:
        parsed = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        return None, "JSON non valido (%s): %s" % (exc, text[:200])
    if not isinstance(parsed, dict) or "nodes" not in parsed or "edges" not in parsed:
        return None, "atteso un oggetto con 'nodes' e 'edges'"
    return parsed, None


def normalize_graph(parsed, scenario_id, facts, allowed_messages):
    """Nodi e archi con provenienza risalita ai messaggi tramite i fatti.

    La provenienza non viene corretta: un nodo o un arco che cita un fatto
    inesistente viene salvato con `provenance_valid: false`.
    """
    prefix = "SC%s" % scenario_id.split("_")[-1]
    facts_by_id = {fact["fact_id"]: fact for fact in facts}

    def provenance(source_fact_ids):
        messages, problems = [], []
        for fact_id in source_fact_ids:
            fact = facts_by_id.get(fact_id)
            if fact is None:
                problems.append("fatto inesistente: %s" % fact_id)
                continue
            for message_id in fact["source_message_ids"]:
                if message_id not in allowed_messages:
                    problems.append("messaggio non ammesso: %s" % message_id)
                elif message_id not in messages:
                    messages.append(message_id)
        if not source_fact_ids:
            problems.append("nessun fatto sorgente")
        return messages, problems

    nodes = []
    for raw in parsed.get("nodes", []):
        if not isinstance(raw, dict):
            continue
        source_fact_ids = [str(f) for f in (raw.get("source_fact_ids") or [])]
        messages, problems = provenance(source_fact_ids)
        nodes.append(
            {
                "node_id": str(raw.get("node_id", "")).strip(),
                "type": str(raw.get("type", "")).strip(),
                "label": str(raw.get("label", "")).strip(),
                "aliases": [str(a) for a in (raw.get("aliases") or [])],
                "source_fact_ids": source_fact_ids,
                "source_message_ids": messages,
                "provenance_valid": not problems,
                "provenance_problem": "; ".join(problems) or None,
            }
        )

    node_ids = {node["node_id"] for node in nodes}
    edges = []
    for index, raw in enumerate(parsed.get("edges", []), start=1):
        if not isinstance(raw, dict):
            continue
        source_fact_ids = [str(f) for f in (raw.get("source_fact_ids") or [])]
        messages, problems = provenance(source_fact_ids)
        subject = str(raw.get("subject", "")).strip()
        obj = str(raw.get("object", "")).strip()
        for role, value in (("subject", subject), ("object", obj)):
            if value not in node_ids:
                problems.append("%s non e' un nodo dichiarato: %s" % (role, value))
        state = str(raw.get("state", rq2.STATE_ACTIVE)).strip().lower()
        edges.append(
            {
                "edge_id": "%s-E%03d" % (prefix, index),
                "subject": subject,
                "relation": str(raw.get("relation", "")).strip(),
                "object": obj,
                "state": state if state in rq2.ALLOWED_STATES else state,
                "state_valid": state in rq2.ALLOWED_STATES,
                "source_fact_ids": source_fact_ids,
                "source_message_ids": messages,
                "provenance_valid": not problems,
                "provenance_problem": "; ".join(problems) or None,
                "order": index,
            }
        )
    return {"nodes": nodes, "edges": edges}


def run(scenario, facts, entries, config, dry_run=False, runner=None, model=None, effort=None):
    model = model or config["models"]["extraction"]["model"]
    effort = effort or config["models"]["extraction"]["effort"]
    prompt = build_graph_prompt(facts, entries)
    allowed_messages = {entry["message_id"] for entry in rq2.user_messages(scenario)}

    log = {
        "scenario_id": scenario["scenario_id"],
        "source_file": scenario["source_file"],
        "config_id": config["config_id"],
        "model": model,
        "effort": effort,
        "dry_run": dry_run,
        "graph_instructions": GRAPH_INSTRUCTIONS,
        "input_fact_ids": [fact["fact_id"] for fact in facts],
        "input_entry_ids": [entry["entry_id"] for entry in entries],
        "prompt": prompt,
    }

    if dry_run:
        log.update({"executed": False, "model_answer": None, "model_used": None,
                    "error": None, "parse_error": None})
        return {"nodes": [], "edges": []}, log

    cwd = tempfile.mkdtemp(prefix="grafo_")
    call = runner or (lambda p: gen.call_claude(p, cwd, model, effort))
    answer, used, error = call(prompt)
    log.update({"executed": True, "model_answer": answer, "model_used": used, "error": error})
    if error:
        log["parse_error"] = None
        return {"nodes": [], "edges": []}, log

    parsed, parse_error = parse_graph(answer)
    log["parse_error"] = parse_error
    if parsed is None:
        return {"nodes": [], "edges": []}, log

    graph = normalize_graph(parsed, scenario["scenario_id"], facts, allowed_messages)
    log["node_count"] = len(graph["nodes"])
    log["edge_count"] = len(graph["edges"])
    return graph, log


# --------------------------------------------------------------------------
# Recupero relazionale
# --------------------------------------------------------------------------

def readable_edges(edges, scope):
    """Archi leggibili in quell'ambito temporale.

    Stessa politica applicata da U alle voci di memoria: nel presente valgono
    solo le relazioni ancora attive; nelle domande storiche entrano anche quelle
    superate e ritirate, con lo stato scritto nel contesto.
    """
    if scope == memory.SCOPE_HISTORY:
        allowed = set(rq2.ALLOWED_STATES)
    else:
        allowed = {rq2.STATE_ACTIVE}
    return [edge for edge in edges if edge["state"] in allowed]


def _contains(sequence, sub):
    """Vero se `sub` compare come sottosequenza contigua di `sequence`."""
    if not sub or len(sub) > len(sequence):
        return False
    for start in range(len(sequence) - len(sub) + 1):
        if sequence[start:start + len(sub)] == sub:
            return True
    return False


def mentioned_nodes(question_text, graph):
    """Nodi nominati direttamente nella domanda.

    Si confrontano le parole, non le stringhe grezze: identificatore, alias ed
    etichetta di ogni nodo vengono cercati come sequenza contigua di parole nel
    testo della domanda. Non si guarda nient'altro che la domanda e il grafo.
    """
    question_tokens = rq2.pilot_rag.tokenize(question_text)
    found = []
    for node in graph["nodes"]:
        names = [node["node_id"]] + list(node["aliases"]) + [node["label"]]
        for name in names:
            if not name:
                continue
            if _contains(question_tokens, rq2.pilot_rag.tokenize(name)):
                found.append({"node_id": node["node_id"], "matched_name": name})
                break
    return found


def seed_nodes(graph, seed_items, max_seed_nodes):
    """Nodi ricavati dalle voci di memoria piu' pertinenti.

    Un nodo entra quando il suo identificatore o un suo alias compare nel testo
    di una voce, oppure quando condivide con quella voce un fatto sorgente.
    L'ordine segue il punteggio della voce che lo ha ancorato.
    """
    seeds = []
    for item in seed_items:
        lowered = item["text"].lower()
        facts = set(item["source_fact_ids"])
        for node in graph["nodes"]:
            node_id = node["node_id"]
            if any(seed["node_id"] == node_id for seed in seeds):
                continue
            names = [node_id] + list(node["aliases"])
            named = any(name and name.lower() in lowered for name in names)
            shared = bool(facts & set(node["source_fact_ids"]))
            if named or shared:
                seeds.append({"node_id": node_id, "from_entry": item["item_id"]})
    return seeds[:max_seed_nodes]


def adjacency(edges):
    """Vicini di ogni nodo, in ordine di identificatore dell'arco."""
    links = {}
    for edge in sorted(edges, key=lambda e: e["edge_id"]):
        links.setdefault(edge["subject"], []).append((edge, edge["object"]))
        links.setdefault(edge["object"], []).append((edge, edge["subject"]))
    return links


def shortest_path(links, source, target, max_hops):
    """Percorso minimo fra due nodi, al massimo `max_hops` collegamenti.

    Visita in ampiezza deterministica: i vicini vengono esaminati in ordine di
    identificatore dell'arco, quindi a parita' di lunghezza il percorso scelto e'
    sempre lo stesso.
    """
    if source == target or source not in links:
        return None
    frontier = [(source, [])]
    visited = {source}
    for _hop in range(max_hops):
        next_frontier = []
        for node_id, path in frontier:
            for edge, other in links.get(node_id, []):
                if other in visited:
                    continue
                extended = path + [edge]
                if other == target:
                    return extended
                visited.add(other)
                next_frontier.append((other, extended))
        frontier = next_frontier
        if not frontier:
            break
    return None


def _edge_item(edge, score, role, hop=None, reached_from=None, path_ids=None):
    text = "%s %s %s" % (edge["subject"], edge["relation"], edge["object"])
    return rq2.make_item(
        item_id=edge["edge_id"],
        text=text,
        render=rq2.render_edge(edge["edge_id"], edge["subject"], edge["relation"],
                               edge["object"], edge["state"], edge["source_message_ids"]),
        session_order=0,
        item_order=edge["order"],
        source_message_ids=edge["source_message_ids"],
        source_fact_ids=edge["source_fact_ids"],
        unit="arco",
        state=edge["state"],
        extra={"score": score, "role": role, "hop": hop, "reached_from": reached_from,
               "in_paths": list(path_ids or []),
               "subject": edge["subject"], "relation": edge["relation"], "object": edge["object"]},
    )


def retrieve(question_text, graph, entries, budget, max_hops=DEFAULT_MAX_HOPS,
             max_seed_items=DEFAULT_MAX_SEED_ITEMS, max_seed_nodes=DEFAULT_MAX_SEED_NODES):
    """Recupero relazionale entro il budget effettivo."""
    scope = memory.question_scope(question_text)
    usable_edges = readable_edges(graph["edges"], scope)
    hidden_edges = [e for e in graph["edges"] if e not in usable_edges]

    ranked = rq2.rank_items(question_text, memory.state_items(entries, scope))
    positive = [item for item in ranked if item["score"] > 0]
    seed_items = positive[:max_seed_items]

    from_question = mentioned_nodes(question_text, graph)
    from_entries = [seed for seed in seed_nodes(graph, seed_items, max_seed_nodes)
                    if seed["node_id"] not in {n["node_id"] for n in from_question}]
    anchors = [n["node_id"] for n in from_question] + [n["node_id"] for n in from_entries]

    # --- percorsi minimi fra i nodi iniziali -----------------------------
    links = adjacency(usable_edges)
    pairs, paths, discarded = [], [], []
    path_edges, path_of_edge = [], {}
    for index, source in enumerate(anchors):
        for target in anchors[index + 1:]:
            pairs.append([source, target])
            found = shortest_path(links, source, target, max_hops)
            if found is None:
                discarded.append({
                    "pair": [source, target],
                    "reason": "nessun percorso entro %d collegamenti" % max_hops,
                })
                continue
            path_id = "P%02d" % (len(paths) + 1)
            paths.append({
                "path_id": path_id,
                "pair": [source, target],
                "hops": len(found),
                "edge_ids": [edge["edge_id"] for edge in found],
                "in_context": None,
            })
            for edge in found:
                path_of_edge.setdefault(edge["edge_id"], []).append(path_id)
                if edge["edge_id"] not in {e["edge_id"] for e in path_edges}:
                    path_edges.append(edge)

    # --- altri archi pertinenti ------------------------------------------
    touched = set(anchors)
    for edge in path_edges:
        touched.update((edge["subject"], edge["object"]))
    path_ids = {edge["edge_id"] for edge in path_edges}
    other_edges = sorted(
        (edge for edge in usable_edges
         if edge["edge_id"] not in path_ids
         and (edge["subject"] in touched or edge["object"] in touched)),
        key=lambda e: e["edge_id"],
    )
    off_topic = [edge for edge in usable_edges
                 if edge["edge_id"] not in path_ids
                 and edge not in other_edges]

    # --- ordine dichiarato del contesto ----------------------------------
    ordered = []
    for position, edge in enumerate(path_edges, start=1):
        ordered.append(_edge_item(edge, round(1.0 + 1.0 / position, 6), "percorso",
                                  path_ids=path_of_edge[edge["edge_id"]]))
    ordered.extend(seed_items)
    for position, edge in enumerate(other_edges, start=1):
        ordered.append(_edge_item(edge, round(0.5 / position, 6), "arco pertinente"))
    ordered.extend(positive[max_seed_items:])
    for position, item in enumerate(ordered, start=1):
        item["rank"] = position

    selection = rq2.select_within_budget(ordered, budget)
    selected_ids = {item["item_id"] for item in selection["selected"]}

    for path in paths:
        path["in_context"] = all(edge_id in selected_ids for edge_id in path["edge_ids"])
        path["missing_edge_ids"] = [e for e in path["edge_ids"] if e not in selected_ids]

    unselected = []
    for edge in path_edges + other_edges:
        if edge["edge_id"] not in selected_ids:
            unselected.append({"edge_id": edge["edge_id"], "reason": "non entrato nel budget"})
    for edge in off_topic:
        unselected.append({"edge_id": edge["edge_id"],
                           "reason": "non incidente a un nodo iniziale o a un percorso"})
    for edge in hidden_edges:
        unselected.append({"edge_id": edge["edge_id"],
                           "reason": "stato %s non leggibile con la domanda %s" % (edge["state"], scope)})

    return {
        "scope": scope,
        "question_node_ids": [n["node_id"] for n in from_question],
        "question_node_matches": from_question,
        "entry_node_ids": [n["node_id"] for n in from_entries],
        "entry_node_matches": from_entries,
        "anchor_node_ids": anchors,
        "seed_item_ids": [item["item_id"] for item in seed_items],
        "seed_item_scores": {item["item_id"]: item["score"] for item in seed_items},
        "pairs_searched": pairs,
        "topological_paths_found": paths,
        "topological_paths_discarded": discarded,
        "topological_paths_complete_in_context": bool(paths) and all(p["in_context"] for p in paths),
        "readable_edge_ids": [edge["edge_id"] for edge in usable_edges],
        "hidden_edge_ids": [edge["edge_id"] for edge in hidden_edges],
        "selected_edge_ids": [item["item_id"] for item in selection["selected"] if item["unit"] == "arco"],
        "unselected_edges": unselected,
        "max_hops": max_hops,
        "max_seed_items": max_seed_items,
        "max_seed_nodes": max_seed_nodes,
        "ranked": ordered,
        "selection": selection,
        "path": [
            {"edge_id": item["item_id"], "role": item["role"], "in_paths": item["in_paths"],
             "subject": item["subject"], "relation": item["relation"], "object": item["object"],
             "state": item["state"], "source_message_ids": item["source_message_ids"]}
            for item in selection["selected"] if item["unit"] == "arco"
        ],
    }


# --------------------------------------------------------------------------
# Percorsi e I/O
# --------------------------------------------------------------------------

def graph_path(scenario_id, out_dir=GRAPH_DIR):
    return Path(out_dir) / ("%s_graph.json" % scenario_id)


def log_path(scenario_id, out_dir=GRAPH_DIR, dry_run=False):
    suffix = "_graph_prompt.json" if dry_run else "_graph_log.json"
    return Path(out_dir) / ("%s%s" % (scenario_id, suffix))


def graph_document(scenario_id, graph, config, label="esecuzione", facts_source=None, state_source=None):
    return {
        "scenario_id": scenario_id,
        "config_id": config["config_id"],
        "label": label,
        "facts_source": facts_source,
        "state_source": state_source,
        "retrieval": {"max_hops": DEFAULT_MAX_HOPS, "max_seed_items": DEFAULT_MAX_SEED_ITEMS,
                      "max_seed_nodes": DEFAULT_MAX_SEED_NODES},
        "nodes": graph["nodes"],
        "edges": graph["edges"],
    }


def load_graph(path):
    import json
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    return {"nodes": document["nodes"], "edges": document["edges"]}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Costruisce la memoria a grafo (G).")
    parser.add_argument("--scenario", default="scenario_04", choices=list(rq2.SCENARIO_IDS))
    parser.add_argument("--facts", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out-dir", default=str(GRAPH_DIR))
    parser.add_argument("--label", default="esecuzione")
    parser.add_argument("--model", default=None)
    parser.add_argument("--effort", default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = rq2.load_config()
    scenario = rq2.load_scenario(args.scenario)

    facts_file = Path(args.facts) if args.facts else extract_facts.facts_path(args.scenario)
    state_file = Path(args.state) if args.state else memory.state_path(args.scenario)
    for path, hint in ((facts_file, "scripts/rq2/extract_facts.py"),
                       (state_file, "scripts/rq2/build_memory_updates.py")):
        if not path.exists():
            print("File mancante: %s. Eseguire prima %s." % (rq2.relative(path), hint), file=sys.stderr)
            return 1

    facts = rq2.read_jsonl(facts_file)
    entries = memory.load_state(state_file)

    graph, log = run(scenario, facts, entries, config, dry_run=args.dry_run,
                     model=args.model, effort=args.effort)
    log["facts_source"] = rq2.relative(facts_file)
    log["state_source"] = rq2.relative(state_file)
    log["label"] = args.label
    written_log = rq2.write_json(log, log_path(args.scenario, Path(args.out_dir), args.dry_run))

    print("Memoria a grafo — %s" % args.scenario)
    print("fatti candidati: %s" % rq2.relative(facts_file))
    print("stato di U:      %s" % rq2.relative(state_file))
    print("modello: %s | effort: %s | %s"
          % (log["model"], log["effort"], "DRY RUN, nessuna chiamata" if args.dry_run else "chiamate reali"))
    if args.label != "esecuzione":
        print("ATTENZIONE: etichetta '%s'. Non sono risultati sperimentali." % args.label)
    print("-" * 78)
    print("Prompt e configurazione salvati in %s" % rq2.relative(written_log))
    if args.dry_run:
        print("Nessun grafo prodotto: per costruirlo davvero, rieseguire senza --dry-run.")
        return 0
    if log.get("error") or log.get("parse_error"):
        print("Costruzione fallita: %s" % (log.get("error") or log.get("parse_error")), file=sys.stderr)
        return 1

    path = rq2.write_json(
        graph_document(args.scenario, graph, config, args.label,
                       rq2.relative(facts_file), rq2.relative(state_file)),
        graph_path(args.scenario, Path(args.out_dir)))
    invalid = [x for x in graph["nodes"] + graph["edges"] if not x["provenance_valid"]]
    print("Grafo: %d nodi, %d archi" % (len(graph["nodes"]), len(graph["edges"])))
    if invalid:
        print("Attenzione: %d fra nodi e archi con provenienza non valida, registrati e non corretti." % len(invalid))
    print("Grafo salvato in %s" % rq2.relative(path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
