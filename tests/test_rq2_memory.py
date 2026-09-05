#!/usr/bin/env python3
"""Test della memoria con aggiornamenti (architettura U).

Nessun test chiama il modello: al posto della chiamata viene riprodotta la
fixture dichiarata `tests/fixtures/rq2/*_update_answers_fixture.json`, che
contiene risposte finte e non uscite di Claude.
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
import run_retrieval_rq2 as retrieval_rq2  # noqa: E402
import fixture_replay  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "rq2"


def facts_fixture(scenario_id):
    return rq2.read_jsonl(FIXTURES / ("%s_facts_fixture.jsonl" % scenario_id))


def build(scenario_id):
    scenario = rq2.load_scenario(scenario_id)
    facts = facts_fixture(scenario_id)
    runner = fixture_replay.make_runner(FIXTURES / ("%s_update_answers_fixture.json" % scenario_id))
    operations, entries, log = memory.run(scenario, facts, rq2.load_config(), runner=runner)
    return facts, operations, entries, log


class TestStessiFattiCandidati(unittest.TestCase):
    """U non riestrae nulla: parte dagli stessi fatti candidati di F."""

    def test_ogni_operazione_cita_un_fatto_candidato(self):
        for scenario_id in ("scenario_03", "scenario_04"):
            facts, operations, _entries, _log = build(scenario_id)
            candidate_ids = {fact["fact_id"] for fact in facts}
            for operation in operations:
                self.assertTrue(set(operation["source_fact_ids"]) <= candidate_ids,
                                "%s: %s" % (scenario_id, operation["op_id"]))

    def test_F_e_U_leggono_lo_stesso_file_di_fatti(self):
        scenario = rq2.load_scenario("scenario_03")
        paths = {"facts": str(FIXTURES / "scenario_03_facts_fixture.jsonl")}
        f_context, f_sources, f_problem = retrieval_rq2.prepare(scenario, "F", paths)
        self.assertIsNone(f_problem)
        with self.subTest("U necessita anche dello stato"):
            # Il percorso e' indicato esplicitamente e non esiste: il controllo
            # deve dipendere dalla regola, non da quali prove reali sono gia'
            # state eseguite nel repository.
            senza_stato = dict(paths, state=str(FIXTURES / "stato_inesistente.json"))
            _u, _s, u_problem = retrieval_rq2.prepare(scenario, "U", senza_stato)
            self.assertIn("stato di U mancante", u_problem)
        facts_from_f = {item["item_id"] for item in f_context["items"]}
        self.assertEqual(facts_from_f, {fact["fact_id"] for fact in facts_fixture("scenario_03")})
        self.assertEqual(f_sources["facts"], rq2.relative(paths["facts"]))

    def test_ogni_fatto_candidato_riceve_una_operazione(self):
        for scenario_id in ("scenario_03", "scenario_04"):
            facts, operations, _entries, _log = build(scenario_id)
            trattati = set()
            for operation in operations:
                trattati.update(operation["source_fact_ids"])
            self.assertEqual(trattati, {fact["fact_id"] for fact in facts}, scenario_id)


class TestIsolamentoCostruttoreU(unittest.TestCase):
    def test_nessun_oracle_nei_prompt(self):
        for scenario_id in ("scenario_03", "scenario_04"):
            questions = rq2.load_questions(scenario_id)
            annotation = rq2.load_annotation_file(scenario_id)
            _facts, _ops, _entries, log = build(scenario_id)
            for entry in log["sessions"]:
                prompt = entry["prompt"]
                for question in questions:
                    self.assertNotIn(question["text"], prompt)
                    self.assertNotIn(question["expected_answer"], prompt)
                    for equivalent in question["accepted_equivalents"]:
                        self.assertNotIn(equivalent, prompt)
                # le operazioni attese dell'oracle non devono comparire
                for operation in annotation["expected_operations"]["operations"]:
                    self.assertNotIn(operation["op_id"], prompt)
                for word in ("expected_operation", "expected_state", "required_relations",
                             "Risposta attesa", "Astensione", "oracle"):
                    self.assertNotIn(word, prompt)

    def test_nessuna_sessione_futura_nei_prompt(self):
        for scenario_id in ("scenario_03", "scenario_04"):
            facts, _ops, _entries, log = build(scenario_id)
            for entry in log["sessions"]:
                order = entry["session_order"]
                futuri = [f for f in facts if f["session_order"] > order]
                for fact in futuri:
                    self.assertNotIn(fact["fact_id"], entry["prompt"],
                                     "%s vede %s" % (entry["session_id"], fact["fact_id"]))
                    self.assertNotIn(fact["text"], entry["prompt"])
                self.assertEqual(
                    entry["input_fact_ids"],
                    [f["fact_id"] for f in facts if f["session_order"] == order],
                )

    def test_lo_stato_precedente_entra_come_contesto(self):
        _facts, _ops, _entries, log = build("scenario_03")
        prima, seconda = log["sessions"][0], log["sessions"][1]
        self.assertIn(memory.NO_STATE, prima["prompt"])
        self.assertNotIn(memory.NO_STATE, seconda["prompt"])
        self.assertTrue(seconda["state_before"])


class TestOperazioni(unittest.TestCase):
    def setUp(self):
        self.facts, self.operations, self.entries, _log = build("scenario_03")
        self.by_id = {entry["entry_id"]: entry for entry in self.entries}

    def test_tutte_e_quattro_le_operazioni_sono_state_applicate(self):
        kinds = {operation["applied_operation"] for operation in self.operations}
        self.assertEqual(kinds, set(rq2.ALLOWED_OPERATIONS))
        self.assertTrue(all(operation["applied"] for operation in self.operations))

    def test_add_crea_un_fatto_attivo(self):
        operation = next(o for o in self.operations if o["proposed_operation"] == "ADD")
        entry = self.by_id[operation["resulting_entry_id"]]
        self.assertEqual(entry["status"], rq2.STATE_ACTIVE)
        self.assertIsNone(entry["superseded_by_op"])
        self.assertEqual(entry["created_by_op"], operation["op_id"])

    def test_update_supera_il_fatto_precedente_e_lo_collega_al_nuovo(self):
        updates = [o for o in self.operations if o["proposed_operation"] == "UPDATE"]
        self.assertTrue(updates)
        for operation in updates:
            superato = self.by_id[operation["supersedes_entry_id"]]
            nuovo = self.by_id[operation["resulting_entry_id"]]
            self.assertEqual(superato["status"], rq2.STATE_SUPERSEDED, operation["op_id"])
            self.assertEqual(superato["superseded_by_entry"], nuovo["entry_id"])
            self.assertEqual(superato["superseded_by_op"], operation["op_id"])
            self.assertEqual(nuovo["claim_key"], superato["claim_key"])
            self.assertGreater(nuovo["order"], superato["order"])

    def test_un_solo_fatto_attivo_per_claim(self):
        attivi = {}
        for entry in self.entries:
            if entry["status"] == rq2.STATE_ACTIVE:
                attivi[entry["claim_key"]] = attivi.get(entry["claim_key"], 0) + 1
        for claim_key, count in attivi.items():
            self.assertEqual(count, 1, claim_key)

    def test_delete_ritira_senza_sostituire(self):
        operation = next(o for o in self.operations if o["proposed_operation"] == "DELETE")
        ritirato = self.by_id[operation["supersedes_entry_id"]]
        self.assertEqual(ritirato["status"], rq2.STATE_RETRACTED)
        self.assertIsNone(ritirato["superseded_by_entry"])
        self.assertIsNone(operation["resulting_entry_id"])

    def test_noop_non_cambia_la_memoria(self):
        scenario = rq2.load_scenario("scenario_03")
        facts = facts_fixture("scenario_03")
        entries = []
        base = [{"fact_id": "SC03-F001", "session_id": "SC03-S1", "session_order": 1,
                 "source_message_ids": ["SC03-S1-U1"]}]
        add = {"op_id": "SC03-OP001", "proposed_operation": "ADD", "claim_key": "k", "value": "v",
               "target_entry_id": None}
        memory.apply_operation(add, base[0], entries, 1)
        prima = copy.deepcopy(entries)
        noop = {"op_id": "SC03-OP002", "proposed_operation": "NOOP", "claim_key": "k", "value": "conferma",
                "target_entry_id": None}
        memory.apply_operation(noop, base[0], entries, 2)
        self.assertEqual(entries, prima)
        self.assertIsNone(noop["resulting_entry_id"])
        self.assertEqual(noop["applied_operation"], "NOOP")
        self.assertTrue(scenario and facts)  # lo scenario e i fatti restano invariati

    def test_una_catena_di_update_conserva_tutte_le_versioni(self):
        classificazioni = [e for e in self.entries if e["claim_key"] == "classificazione"]
        self.assertEqual(len(classificazioni), 3)
        attivi = [e for e in classificazioni if e["status"] == rq2.STATE_ACTIVE]
        self.assertEqual(len(attivi), 1)
        catena = [e for e in classificazioni if e["status"] == rq2.STATE_SUPERSEDED]
        self.assertEqual(len(catena), 2)
        for entry in catena:
            self.assertIn(entry["superseded_by_entry"], self.by_id)

    def test_ogni_operazione_applicata_ha_lasciato_una_traccia_dello_stato(self):
        for operation in self.operations:
            self.assertIn("state_before_fingerprint", operation)
            self.assertIn("state_after_fingerprint", operation)
            if operation["applied_operation"] in ("ADD", "UPDATE", "DELETE"):
                self.assertNotEqual(operation["state_before_fingerprint"],
                                    operation["state_after_fingerprint"], operation["op_id"])
            elif operation["applied_operation"] == "NOOP":
                self.assertEqual(operation["state_before_fingerprint"],
                                 operation["state_after_fingerprint"], operation["op_id"])

    def test_ogni_operazione_registra_i_campi_richiesti(self):
        for operation in self.operations:
            for field in ("op_id", "proposed_operation", "applied_operation", "applied",
                          "rejection_reason", "target_entry_id", "claim_key", "value",
                          "source_fact_ids", "source_message_ids", "order", "reason",
                          "model_used", "config_id", "provenance_valid", "raw_proposal",
                          "state_before_fingerprint", "state_after_fingerprint"):
                self.assertIn(field, operation)
            self.assertTrue(operation["reason"], operation["op_id"])
            self.assertTrue(operation["provenance_valid"], operation["op_id"])

    def test_ordine_temporale_delle_operazioni(self):
        ordini = [operation["order"] for operation in self.operations]
        sessioni = [operation["session_order"] for operation in self.operations]
        self.assertEqual(ordini, sorted(ordini))
        self.assertEqual(sessioni, sorted(sessioni))


class TestRifiutoOperazioni(unittest.TestCase):
    """Una proposta non applicabile viene rifiutata in blocco: niente target
    sostitutivo, niente conversione in ADD, nessuna mutazione dello stato."""

    def setUp(self):
        self.fact = {"fact_id": "SC03-F001", "session_id": "SC03-S1", "session_order": 1,
                     "source_message_ids": ["SC03-S1-U1"]}

    def _stato_con_una_voce(self, claim_key="classificazione", status=rq2.STATE_ACTIVE):
        operation = {"op_id": "SC03-OP001", "proposed_operation": "ADD",
                     "claim_key": claim_key, "value": "ipotesi iniziale", "target_entry_id": None}
        entries = []
        memory.apply_operation(operation, self.fact, entries, 1)
        entries[0]["status"] = status
        return entries

    def _proponi(self, kind, entries, target, claim_key="classificazione"):
        operation = {"op_id": "SC03-OP002", "proposed_operation": kind, "claim_key": claim_key,
                     "value": "valore nuovo", "target_entry_id": target}
        prima = copy.deepcopy(entries)
        impronta = memory.state_fingerprint(entries)
        rifiuto = memory.apply_operation(operation, self.fact, entries, 2)
        return operation, rifiuto, prima, impronta

    def _assert_rifiutata_senza_mutazioni(self, operation, rifiuto, entries, prima, impronta):
        self.assertIsNotNone(rifiuto)
        self.assertFalse(operation["applied"])
        self.assertIsNone(operation["applied_operation"])
        self.assertEqual(operation["rejection_reason"], rifiuto)
        self.assertIsNone(operation["resulting_entry_id"])
        self.assertIsNone(operation["supersedes_entry_id"])
        self.assertEqual(entries, prima)
        self.assertEqual(memory.state_fingerprint(entries), impronta)
        self.assertEqual(operation["state_before_fingerprint"], operation["state_after_fingerprint"])

    def test_update_senza_target(self):
        entries = self._stato_con_una_voce()
        operation, rifiuto, prima, impronta = self._proponi("UPDATE", entries, None)
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertIn("senza target_entry_id", rifiuto)

    def test_delete_senza_target(self):
        entries = self._stato_con_una_voce()
        operation, rifiuto, prima, impronta = self._proponi("DELETE", entries, None)
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)

    def test_update_verso_un_fatto_inesistente(self):
        entries = self._stato_con_una_voce()
        operation, rifiuto, prima, impronta = self._proponi("UPDATE", entries, "SC03-M999")
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertIn("inesistente", rifiuto)

    def test_update_verso_un_fatto_gia_superato(self):
        entries = self._stato_con_una_voce(status=rq2.STATE_SUPERSEDED)
        operation, rifiuto, prima, impronta = self._proponi("UPDATE", entries, entries[0]["entry_id"])
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertIn("gia' superato", rifiuto)

    def test_delete_verso_un_fatto_gia_ritirato(self):
        entries = self._stato_con_una_voce(status=rq2.STATE_RETRACTED)
        operation, rifiuto, prima, impronta = self._proponi("DELETE", entries, entries[0]["entry_id"])
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertIn("gia' ritirato", rifiuto)

    def test_claim_key_incompatibile(self):
        entries = self._stato_con_una_voce()
        operation, rifiuto, prima, impronta = self._proponi(
            "UPDATE", entries, entries[0]["entry_id"], claim_key="tutt-altro")
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertIn("claim_key diverso", rifiuto)

    def test_nessun_target_sostitutivo_e_nessuna_conversione_in_add(self):
        """Il caso che prima veniva 'aggiustato': stesso claim_key attivo in
        memoria, ma target sbagliato. Ora non viene ripescato nulla."""
        entries = self._stato_con_una_voce()
        operation, rifiuto, prima, impronta = self._proponi("UPDATE", entries, "SC03-M999")
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertNotEqual(operation["applied_operation"], "ADD")
        self.assertEqual(len(entries), 1)

    def test_add_con_target(self):
        entries = self._stato_con_una_voce()
        operation, rifiuto, prima, impronta = self._proponi("ADD", entries, entries[0]["entry_id"])
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertIn("target_entry_id valorizzato", rifiuto)
        self.assertEqual(len(entries), 1)

    def test_noop_con_target(self):
        entries = self._stato_con_una_voce()
        operation, rifiuto, prima, impronta = self._proponi("NOOP", entries, entries[0]["entry_id"])
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertIn("target_entry_id valorizzato", rifiuto)

    def test_la_proposta_originale_resta_registrata_anche_quando_rifiutata(self):
        scenario = rq2.load_scenario("scenario_03")
        facts = facts_fixture("scenario_03")
        runner = fixture_replay.make_runner(FIXTURES / "scenario_03_update_answers_rejected_fixture.json")
        operations, _entries, _log = memory.run(scenario, facts, rq2.load_config(), runner=runner)
        for operation in operations:
            if operation["applied"]:
                continue
            self.assertIn("raw_proposal", operation)
            self.assertEqual(operation["raw_proposal"]["operation"], operation["proposed_operation"])
            self.assertEqual(operation["raw_proposal"].get("target_entry_id") or None,
                             operation["target_entry_id"])

    def test_la_fixture_artificiale_copre_tutti_i_tipi_di_rifiuto(self):
        import json
        document = json.loads(
            (FIXTURES / "scenario_03_update_answers_rejected_fixture.json").read_text("utf-8"))
        scenario = rq2.load_scenario("scenario_03")
        runner = fixture_replay.make_runner(FIXTURES / "scenario_03_update_answers_rejected_fixture.json")
        operations, _entries, log = memory.run(scenario, facts_fixture("scenario_03"),
                                               rq2.load_config(), runner=runner)
        rifiutate = [o for o in operations if not o["applied"]]
        self.assertEqual(len(rifiutate), document["expected_rejections"])
        self.assertEqual(log["rejected_count"], document["expected_rejections"])
        motivi = " | ".join(o["rejection_reason"] for o in rifiutate)
        self.assertIn("ADD con target_entry_id valorizzato", motivi)
        self.assertIn("NOOP con target_entry_id valorizzato", motivi)
        self.assertIn("inesistente", motivi)
        self.assertIn("claim_key diverso", motivi)
        self.assertEqual({o["proposed_operation"] for o in rifiutate}, {"ADD", "NOOP", "UPDATE"})

    def test_operazione_non_ammessa(self):
        entries = self._stato_con_una_voce()
        operation, rifiuto, prima, impronta = self._proponi("MERGE", entries, None)
        self._assert_rifiutata_senza_mutazioni(operation, rifiuto, entries, prima, impronta)
        self.assertIn("non ammessa", rifiuto)

    def test_le_operazioni_valide_restano_valide(self):
        for kind, target_needed in (("ADD", False), ("UPDATE", True), ("DELETE", True), ("NOOP", False)):
            entries = self._stato_con_una_voce()
            target = entries[0]["entry_id"] if target_needed else None
            operation = {"op_id": "SC03-OP002", "proposed_operation": kind,
                         "claim_key": "classificazione", "value": "v", "target_entry_id": target}
            rifiuto = memory.apply_operation(operation, self.fact, entries, 2)
            self.assertIsNone(rifiuto, kind)
            self.assertTrue(operation["applied"], kind)
            self.assertEqual(operation["applied_operation"], kind)

    def test_la_fixture_artificiale_produce_rifiuti_senza_mutazioni(self):
        scenario = rq2.load_scenario("scenario_03")
        facts = facts_fixture("scenario_03")
        runner = fixture_replay.make_runner(FIXTURES / "scenario_03_update_answers_rejected_fixture.json")
        operations, entries, log = memory.run(scenario, facts, rq2.load_config(), runner=runner)
        rifiutate = [o for o in operations if not o["applied"]]
        self.assertGreaterEqual(len(rifiutate), 2)
        for operation in rifiutate:
            self.assertIsNone(operation["applied_operation"])
            self.assertTrue(operation["rejection_reason"])
            self.assertEqual(operation["state_before_fingerprint"],
                             operation["state_after_fingerprint"], operation["op_id"])
        self.assertEqual(log["rejected_count"], len(rifiutate))
        # nessuna voce creata o superata da un'operazione rifiutata
        rifiutati = {o["op_id"] for o in rifiutate}
        for entry in entries:
            self.assertNotIn(entry["created_by_op"], rifiutati)
            self.assertNotIn(entry["superseded_by_op"], rifiutati)

    def test_la_fixture_artificiale_e_dichiarata_tale(self):
        import json
        document = json.loads(
            (FIXTURES / "scenario_03_update_answers_rejected_fixture.json").read_text("utf-8"))
        self.assertTrue(document["artificial"])
        self.assertIn("ARTIFICIALE", document["fixture_note"])

    def test_la_fixture_normale_non_contiene_rifiuti(self):
        for scenario_id in ("scenario_03", "scenario_04"):
            _facts, operations, _entries, _log = build(scenario_id)
            self.assertEqual([o for o in operations if not o["applied"]], [], scenario_id)


class TestPoliticaDiLettura(unittest.TestCase):
    def setUp(self):
        self.facts, self.operations, self.entries, _log = build("scenario_03")
        self.config = rq2.load_config()
        self.budget = rq2.budget_tokens(self.config)
        self.questions = {q["question_id"]: q for q in rq2.load_questions("scenario_03")}

    def _context(self, question_id):
        question = self.questions[question_id]
        scope = memory.question_scope(question["text"])
        items = memory.state_items(self.entries, scope)
        ranked = rq2.rank_items(question["text"], items)
        return scope, items, rq2.select_within_budget(ranked, self.budget)

    def test_la_regola_dipende_solo_dal_testo_della_domanda(self):
        self.assertEqual(memory.question_scope("Quale decisione è stata superata?"),
                         memory.SCOPE_HISTORY)
        self.assertEqual(memory.question_scope("Quali attività restano aperte?"),
                         memory.SCOPE_CURRENT)
        # nessun accesso all'oracle: la funzione prende solo una stringa
        self.assertEqual(memory.question_scope(self.questions["SC03-Q5"]["text"]),
                         memory.SCOPE_CURRENT)

    def test_domanda_corrente_non_vede_fatti_superati_o_ritirati(self):
        scope, items, selection = self._context("SC03-Q5")
        self.assertEqual(scope, memory.SCOPE_CURRENT)
        self.assertTrue(all(item["state"] == rq2.STATE_ACTIVE for item in items))
        for item in selection["selected"]:
            self.assertEqual(item["state"], rq2.STATE_ACTIVE, item["item_id"])

    def test_il_fatto_superato_esiste_ma_non_e_leggibile_nel_presente(self):
        """La verifica cloud passa da 'da eseguire' a 'completata'."""
        cloud = [e for e in self.entries if e["claim_key"] == "verifica-accessi-cloud"]
        self.assertEqual(len(cloud), 2)
        superato = next(e for e in cloud if e["status"] == rq2.STATE_SUPERSEDED)
        attivo = next(e for e in cloud if e["status"] == rq2.STATE_ACTIVE)
        _scope, items, _selection = self._context("SC03-Q5")
        leggibili = {item["item_id"] for item in items}
        self.assertNotIn(superato["entry_id"], leggibili)
        self.assertIn(attivo["entry_id"], leggibili)

    def test_domanda_storica_puo_recuperare_la_versione_precedente(self):
        scope, items, selection = self._context("SC03-Q2")
        self.assertEqual(scope, memory.SCOPE_HISTORY)
        leggibili = {item["item_id"] for item in items}
        superati = [e for e in self.entries if e["status"] == rq2.STATE_SUPERSEDED]
        self.assertTrue(superati)
        for entry in superati:
            self.assertIn(entry["entry_id"], leggibili)
        stati = {item["state"] for item in selection["selected"]}
        self.assertIn(rq2.STATE_SUPERSEDED, stati)

    def test_il_fatto_ritirato_resta_consultabile_come_storia(self):
        scope, items, _selection = self._context("SC03-Q3")
        self.assertEqual(scope, memory.SCOPE_HISTORY)
        ritirati = [e for e in self.entries if e["status"] == rq2.STATE_RETRACTED]
        self.assertTrue(ritirati)
        leggibili = {item["item_id"] for item in items}
        for entry in ritirati:
            self.assertIn(entry["entry_id"], leggibili)

    def test_lo_stato_e_scritto_nel_contesto(self):
        _scope, items, _selection = self._context("SC03-Q2")
        for item in items:
            self.assertIn("| %s |" % item["state"], item["render"], item["item_id"])


class TestArtefattiU(unittest.TestCase):
    def test_lo_stato_salvato_si_rilegge_uguale(self):
        import tempfile
        _facts, _ops, entries, _log = build("scenario_04")
        config = rq2.load_config()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            rq2.write_json(memory.state_document("scenario_04", entries, config, "fixture"), path)
            riletto = memory.load_state(path)
        self.assertEqual(len(riletto), len(entries))
        self.assertEqual({e["entry_id"] for e in riletto}, {e["entry_id"] for e in entries})

    def test_i_percorsi_predefiniti_stanno_sotto_results_rq2(self):
        for path in (memory.MEMORY_DIR, memory.operations_path("scenario_03"),
                     memory.state_path("scenario_03")):
            self.assertIn("results/rq2", str(path))


class TestRiferimentiEIdentificatori(unittest.TestCase):
    """I due spazi di identificatori non vanno confusi.

    `fact_id` nomina un fatto candidato, `target_entry_id` una voce di memoria.
    Una proposta che li scambia viene rifiutata, non rimappata.
    """

    def setUp(self):
        self.fact = {"fact_id": "SC03-F002", "session_id": "SC03-S1", "session_order": 1,
                     "source_message_ids": ["SC03-S1-U1"]}
        self.origine = {"fact_id": "SC03-F001", "session_id": "SC03-S1", "session_order": 1,
                        "source_message_ids": ["SC03-S1-U1"]}

    def _memoria_con_una_voce(self):
        operation = {"op_id": "SC03-OP001", "proposed_operation": "ADD",
                     "claim_key": "ipotesi", "value": "ipotesi iniziale", "target_entry_id": None}
        entries = []
        memory.apply_operation(operation, self.origine, entries, 1)
        return entries

    def test_update_che_indica_un_fact_id_e_rifiutato(self):
        """Il caso osservato su SC03: target_entry_id contiene `SC03-F001`."""
        entries = self._memoria_con_una_voce()
        self.assertEqual(entries[0]["entry_id"], "SC03-M001")
        self.assertEqual(entries[0]["source_fact_ids"], ["SC03-F001"])
        prima = copy.deepcopy(entries)
        impronta = memory.state_fingerprint(entries)
        operation = {"op_id": "SC03-OP002", "proposed_operation": "UPDATE", "claim_key": "ipotesi",
                     "value": "valore nuovo", "target_entry_id": "SC03-F001"}
        rifiuto = memory.apply_operation(operation, self.fact, entries, 2)
        self.assertIsNotNone(rifiuto)
        self.assertIn("inesistente", rifiuto)
        self.assertFalse(operation["applied"])
        self.assertIsNone(operation["applied_operation"])
        with self.subTest("nessuna rimappatura sull'omonima voce di memoria"):
            self.assertIsNone(operation["supersedes_entry_id"])
            self.assertEqual(entries[0]["status"], rq2.STATE_ACTIVE)
        with self.subTest("stato invariato"):
            self.assertEqual(entries, prima)
            self.assertEqual(memory.state_fingerprint(entries), impronta)

    def test_delete_che_indica_un_fact_id_e_rifiutato(self):
        entries = self._memoria_con_una_voce()
        impronta = memory.state_fingerprint(entries)
        operation = {"op_id": "SC03-OP002", "proposed_operation": "DELETE", "claim_key": "ipotesi",
                     "value": "ritirato", "target_entry_id": "SC03-F001"}
        rifiuto = memory.apply_operation(operation, self.fact, entries, 2)
        self.assertIn("inesistente", rifiuto)
        self.assertEqual(entries[0]["status"], rq2.STATE_ACTIVE)
        self.assertEqual(memory.state_fingerprint(entries), impronta)

    def test_le_istruzioni_distinguono_i_due_campi(self):
        testo = memory.UPDATE_INSTRUCTIONS
        self.assertIn("Fatti nuovi da valutare", testo)
        self.assertIn("Stato corrente della memoria", testo)
        self.assertIn("`fact_id`", testo)
        self.assertIn("`target_entry_id`", testo)
        self.assertIn("Non usare mai un identificatore di fatto nuovo come `target_entry_id`", testo)

    def test_nessun_identificatore_di_scenario_nelle_istruzioni(self):
        """Le istruzioni restano generiche: nessun caso di SC03 o SC04 dentro."""
        for testo in (memory.UPDATE_INSTRUCTIONS, memory.REPAIR_INSTRUCTIONS):
            self.assertNotRegex(testo, r"SC0\d")
            for parola in ("ransomware", "infostealer", "Kelpie", "RULE-01", "240"):
                self.assertNotIn(parola, testo)


class TestAggiornamentiSuccessiviNellaStessaSessione(unittest.TestCase):
    """Due aggiornamenti di fila sullo stesso oggetto, dentro una sola sessione."""

    def _fatto(self, numero):
        return {"fact_id": "SC03-F%03d" % numero, "session_id": "SC03-S1", "session_order": 1,
                "source_message_ids": ["SC03-S1-U1"]}

    def test_il_secondo_update_sulla_stessa_voce_e_rifiutato(self):
        entries = []
        memory.apply_operation({"op_id": "SC03-OP001", "proposed_operation": "ADD",
                                "claim_key": "ipotesi", "value": "prima", "target_entry_id": None},
                               self._fatto(1), entries, 1)
        primo = {"op_id": "SC03-OP002", "proposed_operation": "UPDATE", "claim_key": "ipotesi",
                 "value": "seconda", "target_entry_id": "SC03-M001"}
        self.assertIsNone(memory.apply_operation(primo, self._fatto(2), entries, 2))
        self.assertEqual(primo["resulting_entry_id"], "SC03-M002")

        secondo = {"op_id": "SC03-OP003", "proposed_operation": "UPDATE", "claim_key": "ipotesi",
                   "value": "terza", "target_entry_id": "SC03-M001"}
        impronta = memory.state_fingerprint(entries)
        rifiuto = memory.apply_operation(secondo, self._fatto(3), entries, 3)
        self.assertIn("gia' superato", rifiuto)
        self.assertEqual(memory.state_fingerprint(entries), impronta)

    def test_indicando_la_voce_nuova_il_secondo_update_passa(self):
        """La catena resta coerente se il target e' la voce prodotta dal primo."""
        entries = []
        memory.apply_operation({"op_id": "SC03-OP001", "proposed_operation": "ADD",
                                "claim_key": "ipotesi", "value": "prima", "target_entry_id": None},
                               self._fatto(1), entries, 1)
        memory.apply_operation({"op_id": "SC03-OP002", "proposed_operation": "UPDATE",
                                "claim_key": "ipotesi", "value": "seconda",
                                "target_entry_id": "SC03-M001"}, self._fatto(2), entries, 2)
        secondo = {"op_id": "SC03-OP003", "proposed_operation": "UPDATE", "claim_key": "ipotesi",
                   "value": "terza", "target_entry_id": "SC03-M002"}
        self.assertIsNone(memory.apply_operation(secondo, self._fatto(3), entries, 3))
        stati = {e["entry_id"]: e["status"] for e in entries}
        self.assertEqual(stati["SC03-M001"], rq2.STATE_SUPERSEDED)
        self.assertEqual(stati["SC03-M002"], rq2.STATE_SUPERSEDED)
        self.assertEqual(stati["SC03-M003"], rq2.STATE_ACTIVE)
        catena = {e["entry_id"]: e["superseded_by_entry"] for e in entries}
        self.assertEqual(catena["SC03-M001"], "SC03-M002")
        self.assertEqual(catena["SC03-M002"], "SC03-M003")


class TestPassataDiRiparazione(unittest.TestCase):
    """Le proposte rifiutate tornano al modello con lo stato aggiornato.

    Le risposte usate qui sono finte e scritte nel test: nessuna chiamata al
    modello, nessuna correzione automatica delle uscite.
    """

    def _scenario_e_fatti(self):
        scenario = rq2.load_scenario("scenario_03")
        facts = [f for f in facts_fixture("scenario_03") if f["session_order"] == 1][:2]
        return scenario, facts

    def _runner(self, risposte):
        coda = list(risposte)
        registro = []

        def runner(prompt):
            registro.append(prompt)
            if not coda:
                return None, None, "nessuna risposta prevista"
            return coda.pop(0), "finto (nessuna chiamata al modello)", None

        runner.prompts = registro
        return runner

    def test_la_riproposta_vede_lo_stato_aggiornato_e_viene_applicata(self):
        scenario, facts = self._scenario_e_fatti()
        primo, secondo = facts[0]["fact_id"], facts[1]["fact_id"]
        prima_passata = json.dumps([
            {"fact_id": primo, "operation": "ADD", "claim_key": "oggetto",
             "value": "prima versione", "target_entry_id": None, "reason": "nuovo"},
            {"fact_id": secondo, "operation": "UPDATE", "claim_key": "oggetto",
             "value": "seconda versione", "target_entry_id": primo, "reason": "supera il precedente"},
        ])
        riparazione = json.dumps([
            {"fact_id": secondo, "operation": "UPDATE", "claim_key": "oggetto",
             "value": "seconda versione", "target_entry_id": "SC03-M001",
             "reason": "supera la voce di memoria"},
        ])
        runner = self._runner([prima_passata, riparazione])
        operations, entries, log = memory.run(scenario, facts, rq2.load_config(),
                                              runner=runner, repair_attempts=1)

        with self.subTest("la prima proposta resta rifiutata"):
            rifiutata = operations[1]
            self.assertFalse(rifiutata["applied"])
            self.assertIn("inesistente", rifiutata["rejection_reason"])
            self.assertEqual(rifiutata["attempt"], 1)
            self.assertEqual(rifiutata["target_entry_id"], primo)
        with self.subTest("la riproposta e' un'operazione nuova e tracciata"):
            riproposta = operations[2]
            self.assertEqual(riproposta["attempt"], 2)
            self.assertEqual(riproposta["retry_of"], operations[1]["op_id"])
            self.assertEqual(operations[1]["retried_by"], riproposta["op_id"])
            self.assertTrue(riproposta["applied"])
            self.assertEqual(riproposta["applied_operation"], "UPDATE")
        with self.subTest("lo stato e' coerente"):
            stati = {e["entry_id"]: e["status"] for e in entries}
            self.assertEqual(stati["SC03-M001"], rq2.STATE_SUPERSEDED)
            self.assertEqual(stati["SC03-M003"], rq2.STATE_ACTIVE)
        with self.subTest("il prompt di riparazione mostra lo stato, non l'oracle"):
            secondo_prompt = runner.prompts[1]
            self.assertIn("SC03-M001", secondo_prompt)
            self.assertIn("Proposte non applicate", secondo_prompt)
            self.assertNotIn("expected_answer", secondo_prompt)
        with self.subTest("chiamate contate"):
            self.assertEqual(log["repair_round_count"], 1)
            self.assertEqual(log["model_calls"], 2)

    def test_una_riproposta_ancora_invalida_resta_rifiutata(self):
        scenario, facts = self._scenario_e_fatti()
        primo, secondo = facts[0]["fact_id"], facts[1]["fact_id"]
        prima_passata = json.dumps([
            {"fact_id": primo, "operation": "ADD", "claim_key": "oggetto",
             "value": "prima versione", "target_entry_id": None, "reason": "nuovo"},
            {"fact_id": secondo, "operation": "UPDATE", "claim_key": "oggetto",
             "value": "seconda", "target_entry_id": primo, "reason": "supera"},
        ])
        riparazione = json.dumps([
            {"fact_id": secondo, "operation": "UPDATE", "claim_key": "oggetto",
             "value": "seconda", "target_entry_id": "SC03-M999", "reason": "ancora sbagliato"},
        ])
        runner = self._runner([prima_passata, riparazione])
        operations, entries, _log = memory.run(scenario, facts, rq2.load_config(),
                                               runner=runner, repair_attempts=1)
        riproposta = operations[2]
        self.assertFalse(riproposta["applied"])
        self.assertIn("inesistente", riproposta["rejection_reason"])
        with self.subTest("nessuna conversione in ADD"):
            self.assertIsNone(riproposta["applied_operation"])
            self.assertEqual(len(entries), 1)
        with self.subTest("una sola riparazione, non un ciclo"):
            self.assertEqual(len([o for o in operations if o["attempt"] > 1]), 1)

    def test_senza_rifiuti_non_si_spende_una_chiamata_in_piu(self):
        scenario, facts = self._scenario_e_fatti()
        risposta = json.dumps([
            {"fact_id": f["fact_id"], "operation": "ADD", "claim_key": "oggetto-%d" % i,
             "value": "valore", "target_entry_id": None, "reason": "nuovo"}
            for i, f in enumerate(facts)
        ])
        runner = self._runner([risposta])
        operations, _entries, log = memory.run(scenario, facts, rq2.load_config(),
                                               runner=runner, repair_attempts=1)
        self.assertTrue(all(o["applied"] for o in operations))
        self.assertEqual(log["repair_round_count"], 0)
        self.assertEqual(log["model_calls"], 1)
        self.assertEqual(len(runner.prompts), 1)

    def test_la_riparazione_chiede_un_array_anche_per_un_solo_fatto(self):
        """Con un fatto solo il modello aveva risposto con un oggetto singolo,
        che il parser scarta: l'istruzione ora lo dice esplicitamente."""
        self.assertIn("array JSON anche quando il fatto da rivalutare e' uno solo",
                      memory.REPAIR_INSTRUCTIONS)

    def test_una_riposta_non_in_array_non_produce_operazioni_e_non_muta_lo_stato(self):
        scenario, facts = self._scenario_e_fatti()
        primo, secondo = facts[0]["fact_id"], facts[1]["fact_id"]
        prima_passata = json.dumps([
            {"fact_id": primo, "operation": "ADD", "claim_key": "oggetto",
             "value": "prima", "target_entry_id": None, "reason": "nuovo"},
            {"fact_id": secondo, "operation": "UPDATE", "claim_key": "oggetto",
             "value": "seconda", "target_entry_id": None, "reason": "supera"},
        ])
        oggetto_singolo = json.dumps(
            {"fact_id": secondo, "operation": "UPDATE", "claim_key": "oggetto",
             "value": "seconda", "target_entry_id": "SC03-M001", "reason": "supera"})
        runner = self._runner([prima_passata, oggetto_singolo])
        operations, entries, log = memory.run(scenario, facts, rq2.load_config(),
                                              runner=runner, repair_attempts=1)
        self.assertEqual(len(operations), 2)
        self.assertFalse(operations[1]["applied"])
        self.assertEqual(len(entries), 1)
        self.assertIsNotNone(log["sessions"][0]["repair_rounds"][0]["parse_error"])

    def test_la_riparazione_e_attiva_per_impostazione_predefinita_da_riga_di_comando(self):
        self.assertEqual(memory.DEFAULT_REPAIR_ATTEMPTS, 1)
        self.assertEqual(memory.parse_args([]).repair_attempts, 1)

    def test_senza_riparazione_il_comportamento_e_quello_della_prima_prova(self):
        scenario, facts = self._scenario_e_fatti()
        primo, secondo = facts[0]["fact_id"], facts[1]["fact_id"]
        risposta = json.dumps([
            {"fact_id": primo, "operation": "ADD", "claim_key": "oggetto",
             "value": "prima", "target_entry_id": None, "reason": "nuovo"},
            {"fact_id": secondo, "operation": "UPDATE", "claim_key": "oggetto",
             "value": "seconda", "target_entry_id": primo, "reason": "supera"},
        ])
        runner = self._runner([risposta])
        operations, _entries, log = memory.run(scenario, facts, rq2.load_config(),
                                               runner=runner, repair_attempts=0)
        self.assertEqual(len(operations), 2)
        self.assertFalse(operations[1]["applied"])
        self.assertEqual(log["model_calls"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
