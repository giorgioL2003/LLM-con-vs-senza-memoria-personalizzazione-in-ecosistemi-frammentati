#!/usr/bin/env python3
"""Test della pipeline RQ2: estrazione, budget, retrieval, prompt, tracce.

Nessun test chiama il modello. Dove serve un'uscita dell'estrattore si usa la
fixture dichiarata in `tests/fixtures/rq2/`, mai un risultato sperimentale.
"""

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq2"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import rq2_common as rq2  # noqa: E402
import extract_facts  # noqa: E402
import run_retrieval_rq2 as retrieval_rq2  # noqa: E402
import build_generation_inputs_rq2 as inputs_rq2  # noqa: E402
import build_annotation_template_rq2 as template_rq2  # noqa: E402
import build_memory_updates as memory  # noqa: E402
import build_graph as graph_memory  # noqa: E402
import fixture_replay  # noqa: E402
import run_generation as gen  # noqa: E402

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "rq2"
FIXTURE = FIXTURE_DIR / "scenario_02_facts_fixture.jsonl"


def _fixture_paths(tmp_dir):
    """Percorsi delle fixture gia' preparate da `_matrice_da_fixture`."""
    tmp_dir = Path(tmp_dir)
    paths = {}
    for scenario_id in ("scenario_02", "scenario_03", "scenario_04"):
        paths[scenario_id] = {"facts": str(FIXTURE_DIR / ("%s_facts_fixture.jsonl" % scenario_id))}
    for scenario_id in ("scenario_03", "scenario_04"):
        paths[scenario_id]["state"] = str(tmp_dir / ("%s_state.json" % scenario_id))
    paths["scenario_04"]["graph"] = str(tmp_dir / "scenario_04_graph.json")
    return paths


def _matrice_da_fixture(tmp_dir):
    """Intera matrice RQ2 costruita offline dalle fixture dichiarate.

    Ripete i passi della verifica offline dentro una cartella temporanea: fatti
    candidati gia' scritti, risposte finte per U e per G, nessuna chiamata al
    modello.
    """
    config = rq2.load_config()
    tmp_dir = Path(tmp_dir)
    paths = {}
    for scenario_id in ("scenario_02", "scenario_03", "scenario_04"):
        paths[scenario_id] = {"facts": str(FIXTURE_DIR / ("%s_facts_fixture.jsonl" % scenario_id))}

    for scenario_id in ("scenario_03", "scenario_04"):
        scenario = rq2.load_scenario(scenario_id)
        facts = rq2.read_jsonl(paths[scenario_id]["facts"])
        runner = fixture_replay.make_runner(FIXTURE_DIR / ("%s_update_answers_fixture.json" % scenario_id))
        _ops, entries, _log = memory.run(scenario, facts, config, runner=runner)
        state_file = tmp_dir / ("%s_state.json" % scenario_id)
        rq2.write_json(memory.state_document(scenario_id, entries, config, "fixture"), state_file)
        paths[scenario_id]["state"] = str(state_file)
        if scenario_id == "scenario_04":
            graph, _glog = graph_memory.run(
                scenario, facts, entries, config,
                runner=fixture_replay.make_runner(FIXTURE_DIR / "scenario_04_graph_answer_fixture.json"))
            graph_file = tmp_dir / "scenario_04_graph.json"
            rq2.write_json(graph_memory.graph_document(scenario_id, graph, config, "fixture"), graph_file)
            paths[scenario_id]["graph"] = str(graph_file)

    retrieval, skipped = retrieval_rq2.run(list(rq2.SCENARIO_IDS), config, paths, "fixture")
    inputs, _ = inputs_rq2.build(list(rq2.SCENARIO_IDS), config, retrieval)
    return config, retrieval, inputs, skipped
MARCATORE_RISPOSTA = "RISPOSTA-FINTA-DEL-TEST-9271"


def _fuga(testo, prompt, sorgenti):
    """Vero se `testo` compare nel prompt senza venire da una sorgente ammessa.

    Una risposta attesa puo' coincidere con una frase del messaggio sorgente:
    quello non e' un oracle che filtra nel prompt, e' il messaggio stesso. La
    fuga c'e' solo se il testo compare senza essere contenuto in nessuna delle
    sorgenti ammesse per quel prompt.
    """
    if testo not in prompt:
        return False
    return not any(testo in sorgente for sorgente in sorgenti)


def _retrieval_rows(scenario_id="scenario_02", modes=("T", "F")):
    config = rq2.load_config()
    rows, _ = retrieval_rq2.run([scenario_id], config, {scenario_id: {"facts": str(FIXTURE)}},
                                label="fixture", modes=list(modes))
    return rows


# --------------------------------------------------------------------------
# 1. L'estrattore non deve vedere oracle, domande o sessioni future
# --------------------------------------------------------------------------

class TestIsolamentoEstrattore(unittest.TestCase):
    def test_nessuna_domanda_o_oracle_nei_prompt(self):
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            questions = rq2.load_questions(scenario_id)
            prompts = extract_facts.build_prompts(scenario)
            facts_so_far = []
            for entry in prompts:
                prompt = extract_facts.build_session_prompt(entry["messages"], facts_so_far)
                sorgenti = [m["content"] for m in entry["messages"]]
                for question in questions:
                    self.assertNotIn(question["text"], prompt, question["question_id"])
                    self.assertFalse(_fuga(question["expected_answer"], prompt, sorgenti),
                                     question["question_id"])
                    for obsolete in question["obsolete_information"]:
                        self.assertFalse(_fuga(obsolete, prompt, sorgenti), question["question_id"])
                    for equivalent in question["accepted_equivalents"]:
                        self.assertFalse(_fuga(equivalent, prompt, sorgenti), question["question_id"])
                for word in ("Risposta attesa", "Fatti obbligatori", "oracle",
                             "expected_answer", "raggiungibil", "Astensione",
                             "Domanda:", "annotazione"):
                    self.assertNotIn(word, prompt)

    def test_il_prompt_e_solo_istruzioni_fatti_precedenti_e_messaggi(self):
        """Controllo strutturale: nel prompt non c'e' nient'altro.

        Un fatto obbligatorio dell'oracle puo' comparire nel prompt perche' e'
        citato dal messaggio sorgente, che e' esattamente cio' che l'estrattore
        deve leggere. Per questo la verifica non cerca sottostringhe ma
        ricostruisce il prompt e lo confronta pezzo per pezzo."""
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            for entry in extract_facts.build_prompts(scenario):
                prompt = extract_facts.build_session_prompt(entry["messages"], [])
                atteso = (
                    "Istruzioni:\n%s\n\nFatti gia' estratti nelle conversazioni precedenti "
                    "(solo per contesto, non vanno ripetuti):\n%s\n\nMessaggi nuovi da elaborare:\n%s"
                    % (
                        extract_facts.EXTRACTION_INSTRUCTIONS,
                        extract_facts.NO_PREVIOUS_FACTS,
                        "\n".join("[%s] %s" % (m["message_id"], m["content"]) for m in entry["messages"]),
                    )
                )
                self.assertEqual(prompt, atteso, entry["session_id"])

    def test_nessuna_sessione_futura_nel_prompt(self):
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            prompts = extract_facts.build_prompts(scenario)
            for position, entry in enumerate(prompts):
                prompt = extract_facts.build_session_prompt(entry["messages"], [])
                for future in prompts[position + 1:]:
                    for message_id in future["message_ids"]:
                        self.assertNotIn(message_id, prompt, "%s vede %s" % (entry["session_id"], message_id))
                    for message in future["messages"]:
                        self.assertNotIn(message["content"], prompt)

    def test_nessun_messaggio_dell_assistente_nel_prompt(self):
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            assistant = [
                message for session in scenario["sessions"] for message in session["messages"]
                if message["role"] == "assistant"
            ]
            for entry in extract_facts.build_prompts(scenario):
                prompt = extract_facts.build_session_prompt(entry["messages"], [])
                for message in assistant:
                    self.assertNotIn(message["message_id"], prompt)

    def test_ordine_cronologico_delle_sessioni(self):
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            orders = [entry["session_order"] for entry in extract_facts.build_prompts(scenario)]
            self.assertEqual(orders, sorted(orders))
            self.assertEqual(orders, list(range(1, len(orders) + 1)))

    def test_i_fatti_precedenti_entrano_come_contesto(self):
        scenario = rq2.load_scenario("scenario_02")
        prompts = extract_facts.build_prompts(scenario)
        previous = [{"fact_id": "SC02-F001", "text": "un fatto precedente",
                     "source_message_ids": ["SC02-S1-U1"]}]
        prompt = extract_facts.build_session_prompt(prompts[1]["messages"], previous)
        self.assertIn("SC02-F001", prompt)
        self.assertIn("un fatto precedente", prompt)
        self.assertNotIn(extract_facts.NO_PREVIOUS_FACTS, prompt)


# --------------------------------------------------------------------------
# 2. Provenienza e lettura dell'uscita del modello
# --------------------------------------------------------------------------

class TestNormalizzazioneFatti(unittest.TestCase):
    def setUp(self):
        self.session = {"session_id": "SC02-S1", "session_order": 1}

    def test_provenienza_valida(self):
        facts, counter = extract_facts.normalize(
            [{"text": "un fatto", "source_message_ids": ["SC02-S1-U1"], "kind": "stato", "negated": False}],
            "scenario_02", self.session, {"SC02-S1-U1"}, 0)
        self.assertEqual(counter, 1)
        self.assertEqual(facts[0]["fact_id"], "SC02-F001")
        self.assertTrue(facts[0]["provenance_valid"])
        self.assertEqual(facts[0]["order"], 1)

    def test_provenienza_non_ammessa_viene_segnalata_non_corretta(self):
        facts, _ = extract_facts.normalize(
            [{"text": "x", "source_message_ids": ["SC02-S4-U1"], "kind": "stato"}],
            "scenario_02", self.session, {"SC02-S1-U1"}, 0)
        self.assertFalse(facts[0]["provenance_valid"])
        self.assertIn("SC02-S4-U1", facts[0]["provenance_problem"])
        # il fatto resta salvato: gli errori si registrano, non si correggono
        self.assertEqual(facts[0]["source_message_ids"], ["SC02-S4-U1"])

    def test_fatto_senza_provenienza(self):
        facts, _ = extract_facts.normalize(
            [{"text": "x", "kind": "stato"}], "scenario_02", self.session, {"SC02-S1-U1"}, 0)
        self.assertFalse(facts[0]["provenance_valid"])

    def test_kind_non_ammesso_viene_segnalato(self):
        facts, _ = extract_facts.normalize(
            [{"text": "x", "source_message_ids": ["SC02-S1-U1"], "kind": "inventato"}],
            "scenario_02", self.session, {"SC02-S1-U1"}, 0)
        self.assertFalse(facts[0]["kind_valid"])

    def test_ordine_temporale_continua_fra_le_sessioni(self):
        facts_a, counter = extract_facts.normalize(
            [{"text": "a", "source_message_ids": ["SC02-S1-U1"], "kind": "stato"}],
            "scenario_02", self.session, {"SC02-S1-U1"}, 0)
        session_2 = {"session_id": "SC02-S2", "session_order": 2}
        facts_b, counter = extract_facts.normalize(
            [{"text": "b", "source_message_ids": ["SC02-S2-U1"], "kind": "stato"}],
            "scenario_02", session_2, {"SC02-S2-U1"}, counter)
        self.assertEqual([f["order"] for f in facts_a + facts_b], [1, 2])
        self.assertEqual(facts_b[0]["fact_id"], "SC02-F002")

    def test_lettura_json_con_recinto_di_codice(self):
        answer = "Ecco i fatti:\n```json\n[{\"text\": \"a\", \"source_message_ids\": [\"M1\"]}]\n```"
        parsed, error = extract_facts.parse_facts(answer)
        self.assertIsNone(error)
        self.assertEqual(len(parsed), 1)

    def test_risposta_non_json_produce_un_errore_registrato(self):
        parsed, error = extract_facts.parse_facts("non ho capito la richiesta")
        self.assertEqual(parsed, [])
        self.assertIsNotNone(error)

    def test_estrazione_dry_run_non_chiama_il_modello(self):
        scenario = rq2.load_scenario("scenario_02")
        facts, log = extract_facts.run(scenario, rq2.load_config(), dry_run=True)
        self.assertEqual(facts, [])
        self.assertEqual(len(log["sessions"]), 4)
        for entry in log["sessions"]:
            self.assertFalse(entry["executed"])
            self.assertIsNone(entry["model_answer"])

    def test_estrazione_con_runner_finto(self):
        """Il runner finto sostituisce la chiamata: nessun processo claude parte."""
        scenario = rq2.load_scenario("scenario_02")
        calls = []

        def fake(prompt):
            calls.append(prompt)
            return ('[{"text": "fatto finto", "source_message_ids": ["%s"], "kind": "stato", "negated": false}]'
                    % ("SC02-S%d-U1" % len(calls)), "claude-sonnet-5", None)

        facts, log = extract_facts.run(scenario, rq2.load_config(), runner=fake)
        self.assertEqual(len(calls), 4)
        self.assertEqual(len(facts), 4)
        self.assertEqual([f["fact_id"] for f in facts],
                         ["SC02-F001", "SC02-F002", "SC02-F003", "SC02-F004"])
        self.assertTrue(all(f["provenance_valid"] for f in facts))
        # dalla seconda sessione in poi il prompt contiene i fatti gia' estratti
        self.assertIn("SC02-F001", calls[1])


# --------------------------------------------------------------------------
# 3. Conteggio dei token e regola di selezione
# --------------------------------------------------------------------------

class TestBudget(unittest.TestCase):
    def _items(self, sizes):
        items = []
        for index, size in enumerate(sizes, start=1):
            items.append({"item_id": "I%d" % index, "tokens": size, "score": 1.0 / index,
                          "session_order": 1, "item_order": index})
        return items

    def test_conteggio_deterministico(self):
        text = "Il token scade dopo 15 minuti."
        self.assertEqual(rq2.count_tokens(text), rq2.count_tokens(text))
        self.assertEqual(rq2.count_tokens(""), 0)
        self.assertEqual(rq2.count_tokens("uno due tre"), 3)
        self.assertEqual(rq2.count_tokens("uno, due."), 4)

    def test_selezione_entro_il_budget(self):
        result = rq2.select_within_budget(self._items([80, 80, 80]), 200)
        self.assertEqual([i["item_id"] for i in result["selected"]], ["I1", "I2"])
        self.assertEqual(result["context_tokens"], 160)
        self.assertLessEqual(result["context_tokens"], 200)
        self.assertEqual(result["stopped_by"]["item_id"], "I3")

    def test_arresto_al_primo_elemento_che_non_entra(self):
        """La selezione e' un prefisso del ranking: un elemento piccolo dopo uno
        troppo grande non viene ripescato."""
        result = rq2.select_within_budget(self._items([100, 150, 10]), 200)
        self.assertEqual([i["item_id"] for i in result["selected"]], ["I1"])
        self.assertNotIn("I3", [i["item_id"] for i in result["selected"]])

    def test_garanzia_minima_se_il_primo_supera_il_budget(self):
        result = rq2.select_within_budget(self._items([500, 10]), 200)
        self.assertEqual([i["item_id"] for i in result["selected"]], ["I1"])
        self.assertTrue(result["budget_exceeded_by_first_item"])

    def test_punteggio_nullo_escluso(self):
        items = self._items([10, 10])
        items[1]["score"] = 0.0
        result = rq2.select_within_budget(items, 200)
        self.assertEqual([i["item_id"] for i in result["selected"]], ["I1"])
        self.assertEqual(result["stopped_by"]["reason"], "punteggio nullo")

    def test_parita_risolta_dall_ordine_dello_scenario(self):
        items = [
            {"item_id": "B", "text": "token scaduto", "tokens": 2, "session_order": 2, "item_order": 1},
            {"item_id": "A", "text": "token scaduto", "tokens": 2, "session_order": 1, "item_order": 1},
        ]
        ranked = rq2.rank_items("token scaduto", items)
        self.assertEqual([item["item_id"] for item in ranked], ["A", "B"])
        self.assertEqual(ranked[0]["score"], ranked[1]["score"])

    def test_stesso_budget_per_T_e_F(self):
        rows = _retrieval_rows()
        budgets = {row["budget_tokens"] for row in rows}
        self.assertEqual(budgets, {rq2.budget_tokens()})


# --------------------------------------------------------------------------
# 3-bis. Il budget riguarda il contesto realmente formattato
# --------------------------------------------------------------------------

class TestBudgetSulContestoFormattato(unittest.TestCase):
    """Il costo di un elemento non e' il suo testo: e' la riga che finisce nel
    prompt, identificatori e provenienza compresi."""

    def test_un_elemento_costa_contenuto_piu_overhead(self):
        item = rq2.make_item(
            item_id="SC02-F001", text="il token scade dopo 15 minuti",
            render=rq2.render_fact("SC02-F001", ["SC02-S2-U1"], "il token scade dopo 15 minuti"),
            session_order=1, item_order=1, source_message_ids=["SC02-S2-U1"], unit="fatto")
        self.assertEqual(item["content_tokens"], rq2.count_tokens(item["text"]))
        self.assertEqual(item["tokens"], rq2.count_tokens(item["render"]))
        self.assertEqual(item["tokens"], item["content_tokens"] + item["overhead_tokens"])
        self.assertGreater(item["overhead_tokens"], 0)

    def test_il_blocco_di_contesto_vale_la_somma_delle_righe(self):
        scenario = rq2.load_scenario("scenario_02")
        items = rq2.message_items(scenario)
        blocco = rq2.context_block(items)
        self.assertEqual(rq2.count_tokens(blocco), sum(item["tokens"] for item in items))

    def test_l_overhead_dipende_dalla_rappresentazione(self):
        """Un fatto costa piu' struttura di un messaggio, una voce di U piu' di
        un fatto: e' proprio cio' che il budget deve mettere in conto."""
        testo = "il token scade dopo 15 minuti"
        messaggio = rq2.count_tokens(rq2.render_message("SC02-S2-U1", testo))
        fatto = rq2.count_tokens(rq2.render_fact("SC02-F001", ["SC02-S2-U1"], testo))
        voce = rq2.count_tokens(rq2.render_state_entry("SC02-M001", "attivo", ["SC02-S2-U1"], testo))
        self.assertLess(messaggio, fatto)
        self.assertLess(fatto, voce)

    def test_il_budget_conta_anche_la_struttura(self):
        """Con lo stesso testo, un elemento con piu' struttura riempie prima."""
        testo = "parola " * 40
        senza = [rq2.make_item("A%d" % i, testo, testo, 1, i, [], unit="x") for i in range(1, 6)]
        con = [
            rq2.make_item("A%d" % i, testo, rq2.render_fact("SC02-F%03d" % i, ["SC02-S1-U1"], testo),
                          1, i, ["SC02-S1-U1"], unit="x")
            for i in range(1, 6)
        ]
        for group in (senza, con):
            for position, item in enumerate(group, start=1):
                item["score"] = 1.0 / position
        self.assertGreater(len(rq2.select_within_budget(senza, 200)["selected"]),
                           len(rq2.select_within_budget(con, 200)["selected"]))

    def test_il_contesto_inviato_coincide_con_quello_contato(self):
        config = rq2.load_config()
        retrieval = _retrieval_rows()
        rows, _ = inputs_rq2.build(["scenario_02"], config, retrieval)
        by_key = {(r["question_id"], r["mode"]): r for r in retrieval}
        for row in rows:
            source = by_key.get((row["question_id"], row["mode"]))
            if source is None:
                continue
            blocco = "\n".join(item["render"] for item in source["selected"])
            self.assertIn(blocco, row["prompt"], "%s %s" % (row["question_id"], row["mode"]))
            self.assertEqual(rq2.count_tokens(blocco), row["context_tokens"])
            self.assertLessEqual(row["context_tokens"], row["budget_tokens"])


# --------------------------------------------------------------------------
# 4. Retrieval: provenienza, budget, tracce
# --------------------------------------------------------------------------

class TestRetrievalRQ2(unittest.TestCase):
    def setUp(self):
        self.rows = _retrieval_rows()
        scenario = rq2.load_scenario("scenario_02")
        self.message_ids = {entry["message_id"] for entry in rq2.user_messages(scenario)}

    def test_contesto_sempre_entro_il_budget(self):
        for row in self.rows:
            if row["budget_exceeded_by_first_item"]:
                continue
            self.assertLessEqual(row["context_tokens"], row["budget_tokens"], row["question_id"])

    def test_provenienza_valida_di_ogni_elemento_selezionato(self):
        for row in self.rows:
            for item in row["selected"]:
                self.assertTrue(item["source_message_ids"], item["item_id"])
                for message_id in item["source_message_ids"]:
                    self.assertIn(message_id, self.message_ids, item["item_id"])

    def test_F_recupera_piu_elementi_di_T_a_parita_di_budget(self):
        """Due messaggi non equivalgono a due fatti: il budget e' in token."""
        t = [r for r in self.rows if r["mode"] == "T"]
        f = [r for r in self.rows if r["mode"] == "F"]
        self.assertGreater(sum(r["context_items"] for r in f), sum(r["context_items"] for r in t))

    def test_content_match_resta_da_annotare(self):
        for row in self.rows:
            for trace in row["required_facts_trace"]:
                self.assertIsNone(trace["content_match"], row["question_id"])

    def test_provenienza_non_dimostra_il_contenuto(self):
        """Caso costruito apposta nella fixture: SC02-F009 perde i 15 minuti.

        La provenienza risulta corretta, quindi nessun controllo automatico puo'
        accorgersi della perdita: il campo del contenuto deve restare da annotare.
        """
        row = next(r for r in self.rows if r["mode"] == "F" and r["question_id"] == "SC02-Q2")
        trace = next(t for t in row["required_facts_trace"] if t["fact_key"] == "token-scadenza-15-minuti")
        self.assertTrue(trace["provenance_match"])
        self.assertIsNone(trace["content_match"])
        fatti = {f["fact_id"]: f["text"] for f in rq2.read_jsonl(FIXTURE)}
        testo = " ".join(fatti[i] for i in row["selected_item_ids"])
        self.assertNotIn("15 minuti", testo)

    def test_full_history_non_compare_nel_retrieval(self):
        self.assertNotIn(rq2.FULL_HISTORY, {row["mode"] for row in self.rows})

    def test_ranking_deterministico(self):
        self.assertEqual(
            [r["selected_item_ids"] for r in self.rows],
            [r["selected_item_ids"] for r in _retrieval_rows()],
        )

    def test_domanda_di_astensione_non_ha_evidenze_richieste(self):
        for row in self.rows:
            if not row["fact_present_in_corpus"]:
                self.assertEqual(row["required_evidence_ids"], [])
                self.assertIsNone(row["evidence_provenance_complete"])


# --------------------------------------------------------------------------
# 5. Input di generazione: riuso del retrieval salvato e prompt comune
# --------------------------------------------------------------------------

class TestInputDiGenerazione(unittest.TestCase):
    def setUp(self):
        self.config = rq2.load_config()
        self.retrieval = _retrieval_rows()
        self.rows, _ = inputs_rq2.build(["scenario_02"], self.config, self.retrieval)

    def test_una_riga_per_domanda_e_modalita(self):
        modes = rq2.runnable_modes("scenario_02", self.config)
        self.assertEqual(len(self.rows), 7 * len(modes))
        self.assertEqual({r["mode"] for r in self.rows}, set(modes))

    def test_controlli_superati(self):
        errors = inputs_rq2.check(self.rows, ["scenario_02"], self.config, self.retrieval)
        self.assertEqual(errors, [])

    def test_contesto_uguale_al_retrieval_salvato(self):
        by_key = {(r["question_id"], r["mode"]): r for r in self.rows}
        for source in self.retrieval:
            row = by_key[(source["question_id"], source["mode"])]
            self.assertEqual(row["context_item_ids"], source["selected_item_ids"])
            self.assertEqual(row["context_tokens"], source["context_tokens"])

    def test_il_retrieval_non_viene_rieseguito(self):
        """Se cambio la selezione salvata, l'input deve seguire quella salvata."""
        retrieval = copy.deepcopy(self.retrieval)
        target = next(r for r in retrieval if r["mode"] == "T" and r["question_id"] == "SC02-Q1")
        target["selected_item_ids"] = ["SC02-S3-U1"]
        target["selected"] = [{"item_id": "SC02-S3-U1", "rank": 1, "score": 0.5, "tokens": 87,
                               "content_tokens": 80, "overhead_tokens": 7, "unit": "messaggio",
                               "state": None, "render": "[SC02-S3-U1] testo sostituito a mano",
                               "source_message_ids": ["SC02-S3-U1"], "source_fact_ids": []}]
        target["context_provenance_message_ids"] = ["SC02-S3-U1"]
        target["context_tokens"] = 87
        target["context_content_tokens"] = 80
        target["context_overhead_tokens"] = 7
        rows, _ = inputs_rq2.build(["scenario_02"], self.config, retrieval)
        row = next(r for r in rows if r["mode"] == "T" and r["question_id"] == "SC02-Q1")
        self.assertEqual(row["context_item_ids"], ["SC02-S3-U1"])
        self.assertIn("testo sostituito a mano", row["prompt"])

    def test_full_history_completo_cronologico_e_fuori_budget(self):
        scenario = rq2.load_scenario("scenario_02")
        history = [entry["message_id"] for entry in rq2.user_messages(scenario)]
        for row in self.rows:
            if row["mode"] != rq2.FULL_HISTORY:
                continue
            self.assertEqual(row["context_item_ids"], history)
            self.assertFalse(row["budget_applies"])
            self.assertFalse(row["retrieval_used"])
            self.assertGreater(row["context_tokens"], rq2.budget_tokens(self.config))

    def test_prompt_comune_identico_al_pilot(self):
        for row in self.rows:
            self.assertIn(inputs_rq2.INSTRUCTIONS, row["prompt"])
            self.assertEqual(row["prompt"].count("Domanda:"), 1)
            self.assertIsNone(row["model_answer"])

    def test_nessuna_annotazione_nel_prompt(self):
        questions = {q["question_id"]: q for q in rq2.load_questions("scenario_02")}
        scenario = rq2.load_scenario("scenario_02")
        sorgenti = [m["content"] for m in rq2.message_index(scenario).values()]
        sorgenti += [f["text"] for f in rq2.read_jsonl(FIXTURE)]
        for row in self.rows:
            question = questions[row["question_id"]]
            self.assertFalse(_fuga(question["expected_answer"], row["prompt"], sorgenti))
            for equivalent in question["accepted_equivalents"]:
                self.assertFalse(_fuga(equivalent, row["prompt"], sorgenti))
            for obsolete in question["obsolete_information"]:
                self.assertFalse(_fuga(obsolete, row["prompt"], sorgenti))
            for other in questions.values():
                if other["question_id"] != row["question_id"]:
                    self.assertNotIn(other["text"], row["prompt"])

    def test_il_prompt_e_solo_istruzioni_contesto_e_domanda(self):
        """Controllo strutturale: il prompt e' esattamente la composizione
        prevista, quindi non puo' contenere altro oltre al contesto scelto."""
        questions = {q["question_id"]: q for q in rq2.load_questions("scenario_02")}
        by_key = {(r["question_id"], r["mode"]): r for r in self.retrieval}
        scenario = rq2.load_scenario("scenario_02")
        history = [item["render"] for item in rq2.message_items(scenario)]
        for row in self.rows:
            source = by_key.get((row["question_id"], row["mode"]))
            renders = history if source is None else [i["render"] for i in source["selected"]]
            atteso = inputs_rq2.build_prompt(inputs_rq2.format_context(renders),
                                             questions[row["question_id"]]["text"])
            self.assertEqual(row["prompt"], atteso, "%s %s" % (row["question_id"], row["mode"]))

    def test_i_fatti_portano_la_loro_provenienza_nel_contesto(self):
        row = next(r for r in self.rows if r["mode"] == "F")
        for item_id in row["context_item_ids"]:
            self.assertIn("[%s | da: " % item_id, row["prompt"])

    def test_controllo_segnala_un_contesto_manomesso(self):
        rows = copy.deepcopy(self.rows)
        target = next(r for r in rows if r["mode"] == "T")
        target["context_item_ids"] = ["SC02-S1-U1", "SC02-S2-U1", "SC02-S3-U1", "SC02-S4-U1"]
        errors = inputs_rq2.check(rows, ["scenario_02"], self.config, self.retrieval)
        self.assertTrue(any("contesto diverso dal retrieval salvato" in e for e in errors))


# --------------------------------------------------------------------------
# 6. Riuso del runner del pilot e indipendenza delle prove
# --------------------------------------------------------------------------

class TestRiusoDelRunner(unittest.TestCase):
    def setUp(self):
        self.config = rq2.load_config()
        self.rows, _ = inputs_rq2.build(["scenario_02"], self.config, _retrieval_rows())

    def test_il_runner_del_pilot_legge_gli_input_rq2(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inputs.jsonl"
            rq2.write_jsonl(self.rows, path)
            loaded = gen.load_inputs(path)
            self.assertEqual(len(loaded), len(self.rows))
            selected = gen.select(loaded, question_id="SC02-Q2")
            self.assertEqual(len(selected), len(rq2.runnable_modes("scenario_02", self.config)))

    def test_una_chiamata_indipendente_per_prova(self):
        calls = []

        def runner(command, input=None, cwd=None, capture_output=None, text=None, timeout=None):
            calls.append(input)

            class Completed:
                stdout = "\n".join([
                    json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-5"}}),
                    json.dumps({"type": "result", "is_error": False, "result": MARCATORE_RISPOSTA}),
                ])
                stderr = ""
                returncode = 0

            return Completed()

        results = gen.run(self.rows[:3], cwd=".", runner=runner)
        self.assertEqual(len(results), 3)
        self.assertEqual(len(calls), 3)
        # nessuna risposta precedente entra nella chiamata successiva
        for prompt in calls:
            self.assertNotIn(MARCATORE_RISPOSTA, prompt)
        self.assertTrue(all(r["model_answer"] == MARCATORE_RISPOSTA for r in results))
        # ogni prompt e' esattamente quello dell'input corrispondente
        self.assertEqual(calls, [row["prompt"] for row in self.rows[:3]])

    def test_le_prove_gia_completate_non_vengono_richiamate(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.jsonl"
            gen.append_result(out, {"scenario_id": "scenario_02", "question_id": "SC02-Q1",
                                    "mode": "T", "error": None})
            done = gen.load_done(out)
            self.assertIn(("scenario_02", "SC02-Q1", "T"), done)


# --------------------------------------------------------------------------
# 7. Modello di annotazione: i tre casi da distinguere
# --------------------------------------------------------------------------

class TestModelloDiAnnotazione(unittest.TestCase):
    def setUp(self):
        self.retrieval = _retrieval_rows()
        self.inputs, _ = inputs_rq2.build(["scenario_02"], rq2.load_config(), self.retrieval)
        self.rows = template_rq2.build(self.inputs, self.retrieval)

    def test_una_riga_per_prova(self):
        self.assertEqual(len(self.rows), len(self.inputs))

    def test_tutti_i_giudizi_nascono_vuoti(self):
        for row in self.rows:
            for field in ("answer_class", "obsolete_used", "unsupported_claim",
                          "wrong_abstention", "error_origin"):
                self.assertIsNone(row[field], field)
            for fact in row["required_facts"]:
                self.assertIsNone(fact["fact_preserved_in_memory"])
                self.assertIsNone(fact["fact_content_correct_in_context"])

    def test_i_tre_casi_hanno_campi_distinti(self):
        row = next(r for r in self.rows if r["mode"] == "F" and r["question_id"] == "SC02-Q2")
        fact = next(f for f in row["required_facts"] if f["fact_key"] == "token-scadenza-15-minuti")
        # 1. estrazione: il messaggio e' stato letto (memoria) ...
        self.assertTrue(fact["fact_in_memory_by_provenance"])
        # ... ma se il contenuto e' andato perso lo dice solo l'annotazione manuale
        self.assertIsNone(fact["fact_preserved_in_memory"])
        # 2. retrieval: presenza nel contesto, automatica
        self.assertIn("fact_in_context_by_provenance", fact)
        # 3. risposta: classe della risposta, manuale
        self.assertIn("risposta", " ".join(row["diagnosis_order"]))

    def test_fatto_non_recuperato_si_distingue_da_fatto_assente_in_memoria(self):
        row = next(r for r in self.rows if r["mode"] == "T" and r["question_id"] == "SC02-Q6")
        fact = next(f for f in row["required_facts"] if f["fact_key"] == "token-scadenza-15-minuti")
        self.assertTrue(fact["fact_in_memory_by_provenance"])
        self.assertFalse(fact["fact_in_context_by_provenance"])

    def test_classi_e_origini_ammesse_sono_dichiarate(self):
        for row in self.rows:
            self.assertIn("completa", row["allowed_answer_class"])
            self.assertIn("estrazione", row["allowed_error_origin"])
            self.assertIn("retrieval", row["allowed_error_origin"])
            self.assertIn("risposta", row["allowed_error_origin"])


# --------------------------------------------------------------------------
# 7-bis. La matrice completa: stesso limite per T, F, U e G
# --------------------------------------------------------------------------

class TestMatriceCompleta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.config, cls.retrieval, cls.inputs, cls.skipped = _matrice_da_fixture(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_la_matrice_e_completa(self):
        self.assertEqual(self.skipped, [])
        atteso = sum(7 * len(rq2.planned_modes(s, self.config)) for s in rq2.SCENARIO_IDS)
        self.assertEqual(len(self.inputs), atteso)
        self.assertEqual(atteso, 77)
        for scenario_id in rq2.SCENARIO_IDS:
            modi = {r["mode"] for r in self.inputs if r["scenario_id"] == scenario_id}
            self.assertEqual(modi, set(rq2.planned_modes(scenario_id, self.config)), scenario_id)

    def test_T_F_U_e_G_rispettano_lo_stesso_limite(self):
        budget = rq2.budget_tokens(self.config)
        visti = set()
        for row in self.inputs:
            if row["mode"] == rq2.FULL_HISTORY:
                continue
            visti.add(row["mode"])
            self.assertTrue(row["budget_applies"], row["mode"])
            self.assertEqual(row["budget_tokens"], budget)
            self.assertLessEqual(row["context_tokens"], budget,
                                 "%s %s %s" % (row["scenario_id"], row["question_id"], row["mode"]))
        self.assertEqual(visti, {"T", "F", "U", "G"})

    def test_full_history_resta_completo_e_fuori_budget(self):
        budget = rq2.budget_tokens(self.config)
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            attesi = [m["message_id"] for m in rq2.user_messages(scenario)]
            righe = [r for r in self.inputs
                     if r["scenario_id"] == scenario_id and r["mode"] == rq2.FULL_HISTORY]
            self.assertEqual(len(righe), 7, scenario_id)
            for row in righe:
                self.assertEqual(row["context_item_ids"], attesi)
                self.assertFalse(row["budget_applies"])
                self.assertFalse(row["retrieval_used"])
                self.assertGreater(row["context_tokens"], budget, scenario_id)

    def test_F_e_U_su_SC03_partono_dagli_stessi_fatti_candidati(self):
        f = [r for r in self.retrieval if r["scenario_id"] == "scenario_03" and r["mode"] == "F"]
        u = [r for r in self.retrieval if r["scenario_id"] == "scenario_03" and r["mode"] == "U"]
        self.assertTrue(f and u)
        self.assertEqual({r["facts_source"] for r in f}, {r["facts_source"] for r in u})

    def test_U_e_G_su_SC04_partono_dagli_stessi_fatti_e_dallo_stesso_stato(self):
        u = [r for r in self.retrieval if r["scenario_id"] == "scenario_04" and r["mode"] == "U"]
        g = [r for r in self.retrieval if r["scenario_id"] == "scenario_04" and r["mode"] == "G"]
        self.assertTrue(u and g)
        self.assertEqual({r["facts_source"] for r in u}, {r["facts_source"] for r in g})
        self.assertEqual({r["state_source"] for r in u}, {r["state_source"] for r in g})
        self.assertTrue(all(r["graph_source"] for r in g))

    def test_G_aggiunge_soltanto_il_livello_relazionale(self):
        """A parita' di domanda, il contesto di G contiene voci di U piu' archi."""
        u = {r["question_id"]: r for r in self.retrieval
             if r["scenario_id"] == "scenario_04" and r["mode"] == "U"}
        g = {r["question_id"]: r for r in self.retrieval
             if r["scenario_id"] == "scenario_04" and r["mode"] == "G"}
        con_archi = 0
        for question_id, riga in g.items():
            unita = {item["unit"] for item in riga["selected"]}
            self.assertTrue(unita <= {"fatto con stato", "arco"}, question_id)
            if "arco" in unita:
                con_archi += 1
            self.assertEqual(riga["reading_scope"], u[question_id]["reading_scope"])
        self.assertGreater(con_archi, 0)

    def test_le_righe_di_G_registrano_nodi_percorsi_e_scarti(self):
        righe = [r for r in self.retrieval if r["mode"] == "G"]
        self.assertTrue(righe)
        for row in righe:
            for field in ("graph_question_node_ids", "graph_entry_node_ids", "graph_seed_node_ids",
                          "graph_pairs_searched", "graph_topological_paths_found", "graph_topological_paths_discarded",
                          "graph_topological_paths_complete_in_context", "graph_readable_edge_ids",
                          "graph_hidden_edge_ids", "graph_selected_edge_ids",
                          "graph_unselected_edges", "graph_max_hops"):
                self.assertIn(field, row, row["question_id"])
            selezionati = set(row["graph_selected_edge_ids"])
            esclusi = {e["edge_id"] for e in row["graph_unselected_edges"]}
            self.assertEqual(selezionati & esclusi, set(), row["question_id"])

    def test_nessuna_operazione_rifiutata_con_le_fixture_normali(self):
        """Le fixture che rappresentano il comportamento atteso non devono
        produrre rifiuti: se ne producono, e' cambiata la politica."""
        for scenario_id in ("scenario_03", "scenario_04"):
            scenario = rq2.load_scenario(scenario_id)
            facts = rq2.read_jsonl(FIXTURE_DIR / ("%s_facts_fixture.jsonl" % scenario_id))
            runner = fixture_replay.make_runner(
                FIXTURE_DIR / ("%s_update_answers_fixture.json" % scenario_id))
            operations, _entries, log = memory.run(scenario, facts, self.config, runner=runner)
            self.assertEqual(log["rejected_count"], 0, scenario_id)
            self.assertTrue(all(o["applied"] for o in operations), scenario_id)

    def test_ogni_riga_registra_contenuto_overhead_e_arresto(self):
        for row in self.retrieval:
            self.assertEqual(row["context_tokens"],
                             row["context_content_tokens"] + row["context_overhead_tokens"])
            self.assertIn("stopped_by", row)
            self.assertIn("budget_exceeded_by_first_item", row)
            for item in row["selected"]:
                self.assertIn("render", item)
                self.assertEqual(item["tokens"], rq2.count_tokens(item["render"]))

    def test_provenienza_valida_in_tutte_le_modalita(self):
        ammessi = {}
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            ammessi[scenario_id] = {m["message_id"] for m in rq2.user_messages(scenario)}
        for row in self.retrieval:
            for item in row["selected"]:
                self.assertTrue(item["source_message_ids"], item["item_id"])
                for message_id in item["source_message_ids"]:
                    self.assertIn(message_id, ammessi[row["scenario_id"]], item["item_id"])

    def test_l_oracle_non_influenza_la_selezione(self):
        """Prova diretta: con l'oracle sostituito da valori finti, il retrieval
        sceglie esattamente gli stessi elementi.

        L'unica cosa che il retrieval legge della domanda e' il suo testo. Fatti
        obbligatori, relazioni richieste, catena, risposta attesa e informazioni
        obsolete finiscono solo nelle tracce diagnostiche, dopo la selezione.
        """
        budget = rq2.budget_tokens(self.config)
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            paths = _fixture_paths(self._tmp.name).get(scenario_id, {})
            for mode in ("T", "F", "U", "G"):
                if mode not in rq2.planned_modes(scenario_id, self.config):
                    continue
                context, sources, problem = retrieval_rq2.prepare(scenario, mode, paths)
                self.assertIsNone(problem, "%s %s" % (scenario_id, mode))
                for question in rq2.load_questions(scenario_id):
                    cieca = copy.deepcopy(question)
                    cieca.update({
                        "expected_answer": "RISPOSTA FINTA",
                        "mandatory_facts": ["fatto finto"],
                        "required_facts": [{
                            "fact_key": "finto", "text": "finto",
                            "source_message_ids": ["MSG-INESISTENTE"],
                            "kind": "stato", "negated": False}],
                        "required_evidence_ids": ["MSG-INESISTENTE"],
                        "required_relations": ["REL-INESISTENTE"],
                        "required_relation_chain": ["REL-INESISTENTE"],
                        "obsolete_information": ["niente"],
                        "accepted_equivalents": ["niente"],
                        "fact_present_in_corpus": not question["fact_present_in_corpus"],
                    })
                    vera = retrieval_rq2.evaluate(scenario_id, question, mode, budget,
                                                  sources, context, "fixture")
                    finta = retrieval_rq2.evaluate(scenario_id, cieca, mode, budget,
                                                   sources, context, "fixture")
                    dove = "%s %s %s" % (scenario_id, question["question_id"], mode)
                    self.assertEqual(vera["selected_item_ids"], finta["selected_item_ids"], dove)
                    self.assertEqual(vera["context_tokens"], finta["context_tokens"], dove)
                    if mode == "G":
                        self.assertEqual(vera["graph_seed_node_ids"], finta["graph_seed_node_ids"], dove)
                        self.assertEqual(
                            [p["edge_ids"] for p in vera["graph_topological_paths_found"]],
                            [p["edge_ids"] for p in finta["graph_topological_paths_found"]], dove)

    def test_la_traccia_delle_relazioni_e_solo_post_retrieval(self):
        """Le relazioni obbligatorie compaiono nel modello di annotazione, non
        nelle righe di retrieval."""
        for row in self.retrieval:
            self.assertNotIn("required_relations", row)
            self.assertNotIn("required_relation_chain", row)
        righe = template_rq2.build(self.inputs, self.retrieval)
        con_relazioni = [r for r in righe if r["required_relation_ids"]]
        self.assertTrue(con_relazioni)
        for riga in con_relazioni:
            self.assertEqual(len(riga["required_relations"]), len(riga["required_relation_ids"]))
            for relazione in riga["required_relations"]:
                self.assertIn("relation_present_by_provenance", relazione)
                self.assertIsNone(relazione["relation_content_correct"])
                self.assertIsNone(relazione["relation_retrieved"])

    def test_evidence_complete_non_diventa_mai_true_da_solo(self):
        for riga in template_rq2.build(self.inputs, self.retrieval):
            self.assertIn(riga["evidence_complete"], (False, None), riga["question_id"])
            if riga["relations_missing_by_provenance"] or riga["facts_missing_by_provenance"]:
                self.assertFalse(riga["evidence_complete"], riga["question_id"])

    def test_percorso_topologico_completo_non_implica_evidenza_completa(self):
        """Il caso di SC04-Q3 con le fixture: il retriever chiude i suoi percorsi
        topologici, ma due relazioni richieste restano fuori dal contesto."""
        riga_g = next(r for r in self.retrieval
                      if r["question_id"] == "SC04-Q3" and r["mode"] == "G")
        self.assertTrue(riga_g["graph_topological_paths_complete_in_context"])
        annotazione = next(r for r in template_rq2.build(self.inputs, self.retrieval)
                           if r["question_id"] == "SC04-Q3" and r["mode"] == "G")
        self.assertTrue(annotazione["relations_missing_by_provenance"])
        self.assertFalse(annotazione["relation_chain_covered_by_provenance"])
        self.assertFalse(annotazione["evidence_complete"])

    def test_le_annotazioni_coprono_tutta_la_matrice(self):
        righe = template_rq2.build(self.inputs, self.retrieval)
        self.assertEqual(len(righe), len(self.inputs))
        for riga in righe:
            self.assertIsNone(riga["answer_class"])
            self.assertIsNone(riga["error_origin"])
            self.assertIn("gestione", riga["allowed_error_origin"])
            self.assertIn("grafo", riga["allowed_error_origin"])

    def test_la_memoria_di_U_e_di_G_e_valutata_sulla_propria_provenienza(self):
        righe = {(r["scenario_id"], r["question_id"], r["mode"]): r
                 for r in template_rq2.build(self.inputs, self.retrieval)}
        u = righe[("scenario_04", "SC04-Q3", "U")]
        g = righe[("scenario_04", "SC04-Q3", "G")]
        self.assertTrue(u["required_facts"])
        for riga in (u, g):
            for fatto in riga["required_facts"]:
                self.assertIn("fact_in_memory_by_provenance", fatto)
                self.assertIsNone(fatto["fact_preserved_in_memory"])


# --------------------------------------------------------------------------
# 8. Separazione dal pilot
# --------------------------------------------------------------------------

class TestSeparazioneDalPilot(unittest.TestCase):
    def _fingerprint(self):
        paths = sorted(
            list((REPO_ROOT / "data" / "scenarios").glob("*.json"))
            + list((REPO_ROOT / "results").glob("*.jsonl"))
            + list((REPO_ROOT / "results").glob("*.json"))
        )
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

    def test_la_pipeline_rq2_non_tocca_i_file_del_pilot(self):
        """Anche costruendo U e G per l'intera matrice, il pilot resta invariato."""
        before = self._fingerprint()
        with tempfile.TemporaryDirectory() as tmp:
            _config, retrieval, rows, _skipped = _matrice_da_fixture(tmp)
            rq2.write_jsonl(retrieval, Path(tmp) / "retrieval.jsonl")
            rq2.write_jsonl(rows, Path(tmp) / "inputs.jsonl")
            rq2.write_jsonl(template_rq2.build(rows, retrieval), Path(tmp) / "template.jsonl")
        self.assertEqual(before, self._fingerprint())

    def test_i_percorsi_predefiniti_stanno_sotto_results_rq2(self):
        for path in (retrieval_rq2.DEFAULT_OUT, inputs_rq2.DEFAULT_OUT,
                     template_rq2.DEFAULT_OUT, extract_facts.FACTS_DIR,
                     memory.MEMORY_DIR, graph_memory.GRAPH_DIR):
            self.assertIn("results/rq2", str(path))

    def test_il_pilot_resta_valido(self):
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import validate_scenarios  # noqa: E402
        self.assertEqual(validate_scenarios.main(["--quiet"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
