#!/usr/bin/env python3
"""Test della memoria a grafo (architettura G) e del recupero relazionale.

Nessun test chiama il modello: al posto della chiamata viene riprodotta la
fixture dichiarata `tests/fixtures/rq2/scenario_04_graph_answer_fixture.json`,
che contiene una risposta finta e non un'uscita di Claude.
"""

import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq2"))

import rq2_common as rq2  # noqa: E402
import build_memory_updates as memory  # noqa: E402
import build_graph as graph_memory  # noqa: E402
import fixture_replay  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "rq2"
SCENARIO = "scenario_04"


def build_all():
    config = rq2.load_config()
    scenario = rq2.load_scenario(SCENARIO)
    facts = rq2.read_jsonl(FIXTURES / ("%s_facts_fixture.jsonl" % SCENARIO))
    operations, entries, _log = memory.run(
        scenario, facts, config,
        runner=fixture_replay.make_runner(FIXTURES / ("%s_update_answers_fixture.json" % SCENARIO)))
    graph, graph_log = graph_memory.run(
        scenario, facts, entries, config,
        runner=fixture_replay.make_runner(FIXTURES / ("%s_graph_answer_fixture.json" % SCENARIO)))
    return config, scenario, facts, operations, entries, graph, graph_log


class TestCostruzioneGrafo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.config, cls.scenario, cls.facts, cls.operations,
         cls.entries, cls.graph, cls.log) = build_all()

    def test_G_riceve_gli_stessi_fatti_e_lo_stesso_stato_di_U(self):
        self.assertEqual(self.log["input_fact_ids"], [f["fact_id"] for f in self.facts])
        self.assertEqual(self.log["input_entry_ids"], [e["entry_id"] for e in self.entries])
        # e nient'altro: nel prompt compaiono solo fatti e voci di memoria
        for entry in self.entries:
            self.assertIn(entry["entry_id"], self.log["prompt"])

    def test_lo_stato_nel_prompt_e_quello_prodotto_da_U(self):
        superati = [e for e in self.entries if e["status"] != rq2.STATE_ACTIVE]
        self.assertTrue(superati)
        for entry in superati:
            self.assertIn("%s — %s" % (entry["value"], entry["status"]), self.log["prompt"])

    def test_nessun_oracle_nel_prompt_del_costruttore(self):
        annotation = rq2.load_annotation_file(SCENARIO)
        prompt = self.log["prompt"]
        for question in rq2.load_questions(SCENARIO):
            self.assertNotIn(question["text"], prompt)
            self.assertNotIn(question["expected_answer"], prompt)
            for relation_id in question["required_relations"]:
                self.assertNotIn(relation_id, prompt)
        for relation in annotation["graph_annotation"]["relations"]:
            self.assertNotIn(relation["relation_id"], prompt)
        for word in ("required_relations", "required_relation_chain", "graph_annotation",
                     "Risposta attesa", "oracle"):
            self.assertNotIn(word, prompt)

    def test_ogni_nodo_conserva_provenienza_valida(self):
        allowed = {m["message_id"] for m in rq2.user_messages(self.scenario)}
        fact_ids = {f["fact_id"] for f in self.facts}
        self.assertTrue(self.graph["nodes"])
        for node in self.graph["nodes"]:
            self.assertTrue(node["provenance_valid"], node["node_id"])
            self.assertTrue(set(node["source_fact_ids"]) <= fact_ids, node["node_id"])
            self.assertTrue(set(node["source_message_ids"]) <= allowed, node["node_id"])

    def test_ogni_arco_conserva_provenienza_e_stato(self):
        allowed = {m["message_id"] for m in rq2.user_messages(self.scenario)}
        node_ids = {node["node_id"] for node in self.graph["nodes"]}
        self.assertTrue(self.graph["edges"])
        for edge in self.graph["edges"]:
            self.assertTrue(edge["provenance_valid"], edge["edge_id"])
            self.assertIn(edge["subject"], node_ids)
            self.assertIn(edge["object"], node_ids)
            self.assertIn(edge["state"], rq2.ALLOWED_STATES, edge["edge_id"])
            self.assertTrue(edge["state_valid"], edge["edge_id"])
            self.assertTrue(set(edge["source_message_ids"]) <= allowed, edge["edge_id"])
            self.assertTrue(edge["source_message_ids"], edge["edge_id"])

    def test_lo_stato_temporale_degli_archi_e_usato(self):
        stati = {edge["state"] for edge in self.graph["edges"]}
        self.assertIn(rq2.STATE_ACTIVE, stati)
        self.assertTrue(stati - {rq2.STATE_ACTIVE}, "nessun arco non attivo: lo stato non e' esercitato")

    def test_provenienza_inventata_viene_segnalata_non_corretta(self):
        parsed = {
            "nodes": [{"node_id": "X", "type": "cosa", "label": "x", "aliases": [],
                       "source_fact_ids": ["SC04-F999"]}],
            "edges": [{"subject": "X", "relation": "tocca", "object": "Y", "state": "attivo",
                       "source_fact_ids": []}],
        }
        graph = graph_memory.normalize_graph(parsed, SCENARIO, self.facts,
                                             {"SC04-S1-U1"})
        self.assertFalse(graph["nodes"][0]["provenance_valid"])
        self.assertIn("fatto inesistente", graph["nodes"][0]["provenance_problem"])
        self.assertFalse(graph["edges"][0]["provenance_valid"])
        self.assertIn("object non e' un nodo dichiarato", graph["edges"][0]["provenance_problem"])


class TestRecuperoRelazionale(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.config, cls.scenario, cls.facts, cls.operations,
         cls.entries, cls.graph, cls.log) = build_all()
        cls.budget = rq2.budget_tokens(cls.config)
        cls.questions = {q["question_id"]: q for q in rq2.load_questions(SCENARIO)}

    def _retrieve(self, question_id, **kwargs):
        return graph_memory.retrieve(self.questions[question_id]["text"], self.graph,
                                     self.entries, self.budget, **kwargs)

    def test_G_parte_dalle_stesse_voci_di_memoria_di_U(self):
        trace = self._retrieve("SC04-Q3")
        entry_ids = {e["entry_id"] for e in self.entries}
        for item in trace["selection"]["selected"]:
            if item["unit"] != "arco":
                self.assertIn(item["item_id"], entry_ids)

    def test_il_percorso_e_tracciabile_fino_ai_nodi_iniziali(self):
        trace = self._retrieve("SC04-Q3")
        self.assertTrue(trace["topological_paths_found"])
        per_id = {edge["edge_id"]: edge for edge in self.graph["edges"]}
        for path in trace["topological_paths_found"]:
            source, target = path["pair"]
            self.assertIn(source, trace["anchor_node_ids"])
            self.assertIn(target, trace["anchor_node_ids"])
            # gli archi del percorso formano una catena da source a target
            corrente = source
            for edge_id in path["edge_ids"]:
                edge = per_id[edge_id]
                self.assertIn(corrente, (edge["subject"], edge["object"]), edge_id)
                corrente = edge["object"] if edge["subject"] == corrente else edge["subject"]
            self.assertEqual(corrente, target)
            self.assertEqual(len(path["edge_ids"]), path["hops"])

    def test_ogni_arco_recuperato_porta_la_sua_provenienza(self):
        trace = self._retrieve("SC04-Q3")
        allowed = {m["message_id"] for m in rq2.user_messages(self.scenario)}
        for passo in trace["path"]:
            self.assertTrue(passo["source_message_ids"], passo["edge_id"])
            self.assertTrue(set(passo["source_message_ids"]) <= allowed)

    def test_limite_dei_collegamenti_applicato(self):
        stretta = self._retrieve("SC04-Q3", max_hops=1)
        larga = self._retrieve("SC04-Q3", max_hops=3)
        self.assertTrue(all(p["hops"] <= 1 for p in stretta["topological_paths_found"]))
        self.assertGreater(len(larga["topological_paths_found"]), len(stretta["topological_paths_found"]))
        self.assertTrue(stretta["topological_paths_discarded"])
        for scarto in stretta["topological_paths_discarded"]:
            self.assertIn("entro 1 collegamenti", scarto["reason"])

    def test_i_percorsi_topologici_entrano_interi_nel_budget(self):
        """Attenzione al significato: dice solo che gli archi *trovati dal
        retriever* ci sono tutti, non che il contesto contenga la catena
        richiesta dalla domanda."""
        trace = self._retrieve("SC04-Q3")
        self.assertTrue(trace["topological_paths_complete_in_context"])
        selezionati = set(trace["selected_edge_ids"])
        for path in trace["topological_paths_found"]:
            self.assertTrue(set(path["edge_ids"]) <= selezionati, path["path_id"])
            self.assertEqual(path["missing_edge_ids"], [])
        self.assertLessEqual(trace["selection"]["context_tokens"], self.budget)

    def test_il_percorso_topologico_non_e_la_catena_dell_oracle(self):
        """La catena annotata puo' ripassare da un'entita' gia' incontrata e non
        coincide con lo shortest path fra due nodi."""
        annotation = rq2.load_annotation_file(SCENARIO)
        question = next(q for q in annotation["questions"] if q["question_id"] == "SC04-Q3")
        catena = question["required_relation_chain"]
        relazioni = {r["relation_id"]: r for r in annotation["graph_annotation"]["relations"]}
        entita = []
        for relation_id in catena:
            relazione = relazioni[relation_id]
            entita += [relazione["subject"], relazione["object"]]
        self.assertGreater(len(entita), len(set(entita)),
                           "la catena non ripassa da nessuna entita': non serve a distinguere")
        trace = self._retrieve("SC04-Q3")
        topologici = set()
        for path in trace["topological_paths_found"]:
            topologici.update(path["edge_ids"])
        mancanti = [r for r in catena if r not in trace["selected_edge_ids"]]
        self.assertTrue(mancanti,
                        "con questa fixture la catena dell'oracle non e' tutta nel contesto")
        self.assertNotEqual(topologici, set(catena))

    def test_un_percorso_incompleto_viene_dichiarato_tale(self):
        """Con un budget minuscolo il percorso non entra: il codice non deve
        troncare ne' dichiarare successo."""
        trace = graph_memory.retrieve(self.questions["SC04-Q3"]["text"], self.graph,
                                      self.entries, 40)
        self.assertTrue(trace["topological_paths_found"])
        self.assertFalse(trace["topological_paths_complete_in_context"])
        incompleti = [p for p in trace["topological_paths_found"] if not p["in_context"]]
        self.assertTrue(incompleti)
        self.assertTrue(all(p["missing_edge_ids"] for p in incompleti))

    def test_i_nodi_iniziali_vengono_dalla_domanda_e_dalle_voci(self):
        trace = self._retrieve("SC04-Q3")
        self.assertTrue(trace["question_node_ids"])
        self.assertEqual(trace["anchor_node_ids"],
                         trace["question_node_ids"] + trace["entry_node_ids"])
        for match in trace["question_node_matches"]:
            self.assertIn(match["matched_name"].lower(),
                          self.questions["SC04-Q3"]["text"].lower())

    def test_gli_archi_esclusi_hanno_una_ragione(self):
        trace = self._retrieve("SC04-Q3")
        esclusi = {e["edge_id"]: e["reason"] for e in trace["unselected_edges"]}
        selezionati = set(trace["selected_edge_ids"])
        for edge in self.graph["edges"]:
            if edge["edge_id"] in selezionati:
                self.assertNotIn(edge["edge_id"], esclusi)
            else:
                self.assertIn(edge["edge_id"], esclusi, edge["edge_id"])
                self.assertTrue(esclusi[edge["edge_id"]])

    def test_recupero_deterministico(self):
        primo = self._retrieve("SC04-Q3")
        secondo = self._retrieve("SC04-Q3")
        self.assertEqual(primo["selection"]["selected"] and
                         [i["item_id"] for i in primo["selection"]["selected"]],
                         [i["item_id"] for i in secondo["selection"]["selected"]])
        self.assertEqual(primo["anchor_node_ids"], secondo["anchor_node_ids"])
        self.assertEqual([p["edge_ids"] for p in primo["topological_paths_found"]],
                         [p["edge_ids"] for p in secondo["topological_paths_found"]])

    def test_una_domanda_relazionale_recupera_archi(self):
        trace = self._retrieve("SC04-Q3")
        self.assertTrue(trace["anchor_node_ids"])
        self.assertTrue([i for i in trace["selection"]["selected"] if i["unit"] == "arco"])

    def test_ogni_domanda_riceve_un_contesto(self):
        """Senza entita' nominate G non trova nodi iniziali, ma resta la memoria di U."""
        for question_id in self.questions:
            trace = self._retrieve(question_id)
            self.assertTrue(trace["selection"]["selected"], question_id)

    def test_G_usa_la_stessa_politica_di_lettura_di_U(self):
        corrente = self._retrieve("SC04-Q4")
        storica = self._retrieve("SC04-Q2")
        self.assertEqual(corrente["scope"], memory.SCOPE_CURRENT)
        self.assertEqual(storica["scope"], memory.SCOPE_HISTORY)
        for item in corrente["selection"]["selected"]:
            if item["unit"] != "arco":
                self.assertEqual(item["state"], rq2.STATE_ACTIVE, item["item_id"])

    def test_grafo_senza_archi_degrada_alla_memoria_di_U(self):
        vuoto = {"nodes": self.graph["nodes"], "edges": []}
        trace = graph_memory.retrieve(self.questions["SC04-Q3"]["text"], vuoto,
                                      self.entries, self.budget)
        self.assertEqual(trace["path"], [])
        self.assertEqual(trace["topological_paths_found"], [])
        self.assertTrue(trace["selection"]["selected"])

    def test_nessuna_regola_scritta_per_una_domanda_particolare(self):
        """La procedura non guarda l'oracle: nessun identificatore
        dell'annotazione compare fra i parametri o nella traccia."""
        annotation = rq2.load_annotation_file(SCENARIO)
        attesi = {r["relation_id"] for r in annotation["graph_annotation"]["relations"]}
        for question_id in self.questions:
            trace = self._retrieve(question_id)
            serializzata = json.dumps(
                {k: v for k, v in trace.items() if k not in ("ranked", "selection")},
                ensure_ascii=False, default=str)
            for relation_id in attesi:
                self.assertNotIn(relation_id, serializzata, question_id)
            for question in self.questions.values():
                self.assertNotIn(question["expected_answer"], serializzata)


class TestPoliticaTemporaleDegliArchi(unittest.TestCase):
    """La regola corrente/storia di U vale anche per gli archi di G."""

    @classmethod
    def setUpClass(cls):
        (cls.config, cls.scenario, cls.facts, cls.operations,
         cls.entries, cls.graph, cls.log) = build_all()
        cls.budget = rq2.budget_tokens(cls.config)
        cls.superato = next(e for e in cls.graph["edges"] if e["state"] != rq2.STATE_ACTIVE)

    def test_filtro_diretto_sugli_archi(self):
        corrente = graph_memory.readable_edges(self.graph["edges"], memory.SCOPE_CURRENT)
        storica = graph_memory.readable_edges(self.graph["edges"], memory.SCOPE_HISTORY)
        self.assertTrue(all(e["state"] == rq2.STATE_ACTIVE for e in corrente))
        self.assertEqual(len(storica), len(self.graph["edges"]))
        self.assertNotIn(self.superato, corrente)
        self.assertIn(self.superato, storica)

    def test_un_arco_superato_non_e_valido_in_una_domanda_corrente(self):
        domanda = "Quale regola di inoltro risulta attiva sull'account aziendale?"
        self.assertEqual(memory.question_scope(domanda), memory.SCOPE_CURRENT)
        trace = graph_memory.retrieve(domanda, self.graph, self.entries, self.budget)
        self.assertNotIn(self.superato["edge_id"], trace["readable_edge_ids"])
        self.assertNotIn(self.superato["edge_id"], trace["selected_edge_ids"])
        motivo = next(e["reason"] for e in trace["unselected_edges"]
                      if e["edge_id"] == self.superato["edge_id"])
        self.assertIn("non leggibile", motivo)

    def test_lo_stesso_arco_compare_con_stato_esplicito_in_una_domanda_storica(self):
        domanda = "Quale regola di inoltro sull'account aziendale e' stata modificata rispetto a prima?"
        self.assertEqual(memory.question_scope(domanda), memory.SCOPE_HISTORY)
        trace = graph_memory.retrieve(domanda, self.graph, self.entries, self.budget)
        self.assertIn(self.superato["edge_id"], trace["readable_edge_ids"])
        item = next((i for i in trace["ranked"] if i["item_id"] == self.superato["edge_id"]), None)
        self.assertIsNotNone(item, "l'arco superato non e' nemmeno stato considerato")
        self.assertIn("| %s |" % self.superato["state"], item["render"])

    def test_un_arco_superato_non_e_attraversabile_nel_presente(self):
        """Il filtro agisce prima della ricerca dei percorsi: un arco non
        leggibile non puo' nemmeno fare da ponte."""
        archi = graph_memory.readable_edges(self.graph["edges"], memory.SCOPE_CURRENT)
        links = graph_memory.adjacency(archi)
        raggiungibili = graph_memory.shortest_path(
            links, self.superato["subject"], self.superato["object"], 1)
        self.assertIsNone(raggiungibili)
        links_storici = graph_memory.adjacency(
            graph_memory.readable_edges(self.graph["edges"], memory.SCOPE_HISTORY))
        self.assertIsNotNone(graph_memory.shortest_path(
            links_storici, self.superato["subject"], self.superato["object"], 1))

    def test_U_e_G_applicano_la_stessa_politica(self):
        for domanda in ("Quali azioni risultano completate sull'account?",
                        "Quale valutazione iniziale e' stata superata?"):
            scope = memory.question_scope(domanda)
            trace = graph_memory.retrieve(domanda, self.graph, self.entries, self.budget)
            self.assertEqual(trace["scope"], scope)
            voci = memory.state_items(self.entries, scope)
            ammessi = {rq2.STATE_ACTIVE} if scope == memory.SCOPE_CURRENT else set(rq2.ALLOWED_STATES)
            self.assertTrue(all(v["state"] in ammessi for v in voci))
            for edge_id in trace["readable_edge_ids"]:
                edge = next(e for e in self.graph["edges"] if e["edge_id"] == edge_id)
                self.assertIn(edge["state"], ammessi)


class TestGrafoSintetico(unittest.TestCase):
    """Grafo finto e minimo: serve a controllare la procedura in astratto,
    senza dipendere dalla forma di SC04."""

    def setUp(self):
        # Ogni nodo ha un fatto sorgente diverso: cosi' l'ancoraggio dipende dai
        # nomi e non da una provenienza condivisa da tutti.
        counter = {"n": 0}

        def node(node_id, label, aliases=()):
            counter["n"] += 1
            return {"node_id": node_id, "type": "cosa", "label": label, "aliases": list(aliases),
                    "source_fact_ids": ["X-F%03d" % counter["n"]], "source_message_ids": ["X-S1-U1"],
                    "provenance_valid": True, "provenance_problem": None}

        def edge(order, subject, relation, obj, state=rq2.STATE_ACTIVE):
            return {"edge_id": "X-E%03d" % order, "subject": subject, "relation": relation,
                    "object": obj, "state": state, "state_valid": True,
                    "source_fact_ids": ["X-F001"], "source_message_ids": ["X-S1-U1"],
                    "provenance_valid": True, "provenance_problem": None, "order": order}

        # catena A - B - C - D, piu' un ramo laterale E e un arco superato A-F
        self.graph = {
            "nodes": [node("alfa", "primo nodo"), node("beta", "secondo nodo"),
                      node("gamma", "terzo nodo"), node("delta", "quarto nodo"),
                      node("epsilon", "nodo laterale"), node("zeta", "nodo superato")],
            "edges": [edge(1, "alfa", "tocca", "beta"), edge(2, "beta", "tocca", "gamma"),
                      edge(3, "gamma", "tocca", "delta"), edge(4, "beta", "tocca", "epsilon"),
                      edge(5, "alfa", "toccava", "zeta", rq2.STATE_SUPERSEDED)],
        }
        self.entries = [{
            "entry_id": "X-M001", "claim_key": "k", "value": "il caso riguarda un collegamento",
            "status": rq2.STATE_ACTIVE, "source_fact_ids": ["X-F001"],
            "source_message_ids": ["X-S1-U1"], "session_id": "X-S1", "session_order": 1,
            "order": 1, "created_by_op": "X-OP001", "superseded_by_op": None,
            "superseded_by_entry": None,
        }]

    def test_percorso_minimo_fra_due_nodi_nominati(self):
        trace = graph_memory.retrieve("Come sono collegati alfa e delta?", self.graph,
                                      self.entries, 400, max_hops=3)
        self.assertEqual(trace["question_node_ids"], ["alfa", "delta"])
        percorso = next(p for p in trace["topological_paths_found"] if p["pair"] == ["alfa", "delta"])
        self.assertEqual(percorso["edge_ids"], ["X-E001", "X-E002", "X-E003"])
        self.assertTrue(percorso["in_context"])

    def test_il_ramo_laterale_non_entra_nel_percorso(self):
        trace = graph_memory.retrieve("Come sono collegati alfa e delta?", self.graph,
                                      self.entries, 400, max_hops=3)
        percorso = next(p for p in trace["topological_paths_found"] if p["pair"] == ["alfa", "delta"])
        self.assertNotIn("X-E004", percorso["edge_ids"])

    def test_limite_dei_collegamenti_scarta_il_percorso_troppo_lungo(self):
        trace = graph_memory.retrieve("Come sono collegati alfa e delta?", self.graph,
                                      self.entries, 400, max_hops=2)
        self.assertEqual(trace["topological_paths_found"], [])
        self.assertTrue(trace["topological_paths_discarded"])
        self.assertIn("entro 2 collegamenti", trace["topological_paths_discarded"][0]["reason"])

    def test_arco_superato_escluso_nel_presente_e_incluso_nella_storia(self):
        corrente = graph_memory.retrieve("Come sono collegati alfa e zeta?", self.graph,
                                         self.entries, 400, max_hops=3)
        self.assertNotIn("X-E005", corrente["readable_edge_ids"])
        self.assertEqual(corrente["topological_paths_found"], [])
        storica = graph_memory.retrieve(
            "Come erano collegati alfa e zeta prima che fosse superato?", self.graph,
            self.entries, 400, max_hops=3)
        self.assertEqual(storica["scope"], memory.SCOPE_HISTORY)
        self.assertIn("X-E005", storica["readable_edge_ids"])
        self.assertTrue(any("X-E005" in p["edge_ids"] for p in storica["topological_paths_found"]))

    def test_percorso_incompleto_dichiarato_con_budget_stretto(self):
        trace = graph_memory.retrieve("Come sono collegati alfa e delta?", self.graph,
                                      self.entries, 45, max_hops=3)
        self.assertTrue(trace["topological_paths_found"])
        self.assertFalse(trace["topological_paths_complete_in_context"])
        percorso = trace["topological_paths_found"][0]
        self.assertTrue(percorso["missing_edge_ids"])


class TestArtefattiG(unittest.TestCase):
    def test_il_grafo_salvato_si_rilegge_uguale(self):
        import tempfile
        config, _scenario, facts, _ops, _entries, graph, _log = build_all()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "graph.json"
            rq2.write_json(graph_memory.graph_document(SCENARIO, graph, config, "fixture"), path)
            riletto = graph_memory.load_graph(path)
        self.assertEqual(riletto, {"nodes": graph["nodes"], "edges": graph["edges"]})
        self.assertTrue(facts)

    def test_i_percorsi_predefiniti_stanno_sotto_results_rq2(self):
        for path in (graph_memory.GRAPH_DIR, graph_memory.graph_path(SCENARIO)):
            self.assertIn("results/rq2", str(path))

    def test_le_risposte_finte_devono_dichiararsi_fixture(self):
        """Il replay rifiuta un file che non si dichiara fixture: cosi' non si
        possono far passare per finte delle risposte vere, o viceversa."""
        import json, tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "non_dichiarato.json"
            path.write_text(json.dumps({"answers": ["[]"]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                fixture_replay.load_answers(path)
        runner = fixture_replay.make_runner(FIXTURES / "scenario_04_graph_answer_fixture.json")
        self.assertEqual(len(runner.answers), 1)
        runner("prompt")
        answer, model, error = runner("prompt di troppo")
        self.assertIsNone(answer)
        self.assertIn("fixture esaurita", error)
        self.assertIsNone(model)


if __name__ == "__main__":
    unittest.main(verbosity=2)
