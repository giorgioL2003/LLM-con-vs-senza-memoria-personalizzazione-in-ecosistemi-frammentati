#!/usr/bin/env python3
"""Test del dataset e della configurazione di RQ2.

Verificano due cose: che i dati veri passino la validazione e che il validatore
sappia riconoscere corruzioni intenzionali. Un validatore che accetta tutto non
dimostra niente.
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq2"))

import rq2_common as rq2  # noqa: E402
import validate_rq2 as validator  # noqa: E402


def _context(scenario_id):
    scenario = rq2.load_scenario(scenario_id)
    messages_by_id = {}
    for session in scenario["sessions"]:
        for message in session["messages"]:
            messages_by_id[message["message_id"]] = session["session_id"]
    user_ids = {entry["message_id"] for entry in rq2.user_messages(scenario)}
    session_order = {s["session_id"]: s["order"] for s in scenario["sessions"]}
    return scenario, messages_by_id, user_ids, session_order


def _codes(errors):
    return {error.split("]")[0].strip("[") for error in errors}


class TestDatiVeri(unittest.TestCase):
    def test_validazione_completa_senza_errori(self):
        self.assertEqual(validator.validate_all(), [])

    def test_quattro_sessioni_e_sette_domande_per_scenario(self):
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            self.assertEqual(len(scenario["sessions"]), 4, scenario_id)
            self.assertEqual(len(rq2.load_questions(scenario_id)), 7, scenario_id)

    def test_identificatori_unici_fra_scenari(self):
        message_ids, question_ids = [], []
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            for session in scenario["sessions"]:
                message_ids += [m["message_id"] for m in session["messages"]]
            question_ids += [q["question_id"] for q in rq2.load_questions(scenario_id)]
        self.assertEqual(len(message_ids), len(set(message_ids)))
        self.assertEqual(len(question_ids), len(set(question_ids)))

    def test_overlay_non_altera_le_evidenze_del_pilot(self):
        for scenario_id in ("scenario_01", "scenario_02"):
            pilot = json.loads((REPO_ROOT / "data" / "scenarios" / ("%s.json" % scenario_id)).read_text("utf-8"))
            declared = {q["question_id"]: q["required_evidence_ids"] for q in pilot["questions"]}
            for question in rq2.load_questions(scenario_id):
                self.assertEqual(
                    question["required_evidence_ids"],
                    declared[question["question_id"]],
                    question["question_id"],
                )

    def test_annotazioni_dichiarate_come_bozza(self):
        for scenario_id in rq2.SCENARIO_IDS:
            annotation = rq2.load_annotation_file(scenario_id)
            self.assertFalse(annotation["frozen"], scenario_id)
            self.assertTrue(annotation["review_required"], scenario_id)

    def test_sc03_contiene_tutte_le_operazioni(self):
        operations = rq2.load_annotation_file("scenario_03")["expected_operations"]["operations"]
        kinds = {operation["expected_operation"] for operation in operations}
        self.assertEqual(kinds, set(rq2.ALLOWED_OPERATIONS))

    def test_sc04_relazioni_hanno_sempre_una_evidenza(self):
        graph = rq2.load_annotation_file("scenario_04")["graph_annotation"]
        for relation in graph["relations"]:
            self.assertTrue(relation["source_message_ids"], relation["relation_id"])

    def test_ogni_scenario_ha_una_astensione(self):
        for scenario_id in rq2.SCENARIO_IDS:
            absent = [q for q in rq2.load_questions(scenario_id) if not q["fact_present_in_corpus"]]
            self.assertEqual(len(absent), 1, scenario_id)
            self.assertEqual(absent[0]["expected_behavior"], rq2.BEHAVIOR_ABSTAIN)

    def test_ultima_sessione_non_riassume_tutta_la_storia(self):
        """Almeno tre domande per scenario richiedono evidenze fuori dall'ultima sessione."""
        for scenario_id in rq2.SCENARIO_IDS:
            scenario = rq2.load_scenario(scenario_id)
            order = {s["session_id"]: s["order"] for s in scenario["sessions"]}
            session_of = {}
            for session in scenario["sessions"]:
                for message in session["messages"]:
                    session_of[message["message_id"]] = session["session_id"]
            last = max(order.values())
            outside = 0
            for question in rq2.load_questions(scenario_id):
                orders = {order[session_of[m]] for m in question["required_evidence_ids"]}
                if orders and min(orders) < last:
                    outside += 1
            self.assertGreaterEqual(outside, 3, scenario_id)


class TestCorruzioniDelleDomande(unittest.TestCase):
    def setUp(self):
        self.scenario_id = "scenario_03"
        (_, self.messages, self.user_ids, self.order) = _context(self.scenario_id)
        self.questions = rq2.load_questions(self.scenario_id)

    def _run(self, questions):
        errors = []
        validator.validate_questions(self.scenario_id, questions, self.messages, self.user_ids,
                                     self.order, errors)
        return errors

    def test_dati_veri_ok(self):
        self.assertEqual(self._run(self.questions), [])

    def test_fatto_con_messaggio_inesistente(self):
        questions = copy.deepcopy(self.questions)
        questions[0]["required_facts"][0]["source_message_ids"] = ["SC03-S9-U9"]
        self.assertIn("E-PROVENANCE", _codes(self._run(questions)))

    def test_fatto_che_cita_un_messaggio_dell_assistente(self):
        questions = copy.deepcopy(self.questions)
        questions[0]["required_facts"][0]["source_message_ids"] = ["SC03-S1-A1"]
        self.assertIn("E-PROVENANCE", _codes(self._run(questions)))

    def test_fatto_senza_provenienza(self):
        questions = copy.deepcopy(self.questions)
        questions[0]["required_facts"][0]["source_message_ids"] = []
        self.assertIn("E-PROVENANCE", _codes(self._run(questions)))

    def test_informazione_assente_con_evidenze(self):
        questions = copy.deepcopy(self.questions)
        absent = next(q for q in questions if not q["fact_present_in_corpus"])
        absent["required_facts"] = [
            {"fact_key": "x", "text": "y", "source_message_ids": ["SC03-S1-U1"],
             "kind": "osservazione", "negated": False}
        ]
        self.assertIn("E-ABSENT", _codes(self._run(questions)))

    def test_cross_session_con_una_sola_sessione(self):
        questions = copy.deepcopy(self.questions)
        cross = next(q for q in questions if q["category"] == "cross_session_link")
        for fact in cross["required_facts"]:
            fact["source_message_ids"] = ["SC03-S1-U1"]
        cross["required_evidence_ids"] = ["SC03-S1-U1"]
        self.assertIn("E-CROSS", _codes(self._run(questions)))

    def test_categoria_non_ammessa(self):
        questions = copy.deepcopy(self.questions)
        questions[0]["category"] = "categoria_inventata"
        self.assertIn("E-CATEGORY", _codes(self._run(questions)))

    def test_evidenze_tutte_nell_ultima_sessione(self):
        questions = copy.deepcopy(self.questions)
        for question in questions:
            for fact in question["required_facts"]:
                fact["source_message_ids"] = ["SC03-S4-U2"]
            question["required_evidence_ids"] = ["SC03-S4-U2"]
        self.assertIn("E-LASTSESSION", _codes(self._run(questions)))


class TestCorruzioniDelleOperazioni(unittest.TestCase):
    def setUp(self):
        self.scenario_id = "scenario_03"
        (_, self.messages, _, self.order) = _context(self.scenario_id)
        self.annotation = rq2.load_annotation_file(self.scenario_id)

    def _run_ops(self, annotation):
        errors = []
        validator.validate_operations(self.scenario_id, annotation, self.messages, self.order,
                                      errors, require_full_policy=True)
        return errors

    def _run_state(self, annotation):
        errors = []
        validator.validate_state(self.scenario_id, annotation, errors)
        return errors

    def test_dati_veri_ok(self):
        self.assertEqual(self._run_ops(self.annotation), [])
        self.assertEqual(self._run_state(self.annotation), [])

    def test_update_senza_fatto_superato(self):
        annotation = copy.deepcopy(self.annotation)
        update = next(o for o in annotation["expected_operations"]["operations"]
                      if o["expected_operation"] == "UPDATE")
        update["supersedes"] = None
        self.assertIn("E-OPS", _codes(self._run_ops(annotation)))

    def test_delete_che_supera_un_claim_diverso(self):
        annotation = copy.deepcopy(self.annotation)
        delete = next(o for o in annotation["expected_operations"]["operations"]
                      if o["expected_operation"] == "DELETE")
        delete["supersedes"] = "SC03-OP01"
        self.assertIn("E-OPS", _codes(self._run_ops(annotation)))

    def test_operazioni_fuori_ordine_cronologico(self):
        annotation = copy.deepcopy(self.annotation)
        annotation["expected_operations"]["operations"].reverse()
        self.assertIn("E-OPS-ORDER", _codes(self._run_ops(annotation)))

    def test_provenienza_di_una_sessione_sbagliata(self):
        annotation = copy.deepcopy(self.annotation)
        annotation["expected_operations"]["operations"][0]["source_message_ids"] = ["SC03-S4-U2"]
        self.assertIn("E-PROVENANCE", _codes(self._run_ops(annotation)))

    def test_stato_incompleto(self):
        annotation = copy.deepcopy(self.annotation)
        annotation["expected_state"]["entries"] = annotation["expected_state"]["entries"][:2]
        self.assertIn("E-STATE", _codes(self._run_state(annotation)))

    def test_fatto_attivo_dichiarato_superato(self):
        annotation = copy.deepcopy(self.annotation)
        entry = next(e for e in annotation["expected_state"]["entries"] if e["status"] == "attivo")
        entry["superseded_by"] = "SC03-OP12"
        self.assertIn("E-STATE", _codes(self._run_state(annotation)))


class TestCorruzioniDelGrafo(unittest.TestCase):
    def setUp(self):
        self.scenario_id = "scenario_04"
        (_, self.messages, _, _) = _context(self.scenario_id)
        self.annotation = rq2.load_annotation_file(self.scenario_id)
        self.questions = rq2.load_questions(self.scenario_id)

    def _run(self, annotation, questions=None):
        errors = []
        validator.validate_graph(self.scenario_id, annotation, questions or self.questions,
                                 self.messages, errors)
        return errors

    def test_dati_veri_ok(self):
        self.assertEqual(self._run(self.annotation), [])

    def test_relazione_verso_entita_inesistente(self):
        annotation = copy.deepcopy(self.annotation)
        annotation["graph_annotation"]["relations"][0]["object"] = "ENTITA-FANTASMA"
        self.assertIn("E-GRAPH", _codes(self._run(annotation)))

    def test_percorso_interrotto(self):
        questions = copy.deepcopy(self.questions)
        question = next(q for q in questions if q["required_relation_chain"])
        question["required_relation_chain"] = [question["required_relation_chain"][0], question["required_relation_chain"][-1]]
        self.assertIn("E-GRAPH", _codes(self._run(self.annotation, questions)))

    def test_relazione_richiesta_inesistente(self):
        questions = copy.deepcopy(self.questions)
        questions[1]["required_relations"] = ["SC04-R99"]
        self.assertIn("E-GRAPH", _codes(self._run(self.annotation, questions)))


class TestConfigurazione(unittest.TestCase):
    def setUp(self):
        self.config = rq2.load_config()

    def _run(self, config):
        errors = []
        validator.validate_config(config, errors)
        return errors

    def test_configurazione_vera_ok(self):
        self.assertEqual(self._run(self.config), [])

    def test_matrice_uguale_alla_roadmap(self):
        for scenario_id, modes in validator.ROADMAP_MATRIX.items():
            self.assertEqual(rq2.planned_modes(scenario_id, self.config), modes)

    def test_modalita_eseguibili_sono_un_sottoinsieme_delle_previste(self):
        for scenario_id in rq2.SCENARIO_IDS:
            planned = set(rq2.planned_modes(scenario_id, self.config))
            self.assertTrue(set(rq2.runnable_modes(scenario_id, self.config)) <= planned, scenario_id)

    def test_matrice_alterata_viene_segnalata(self):
        config = copy.deepcopy(self.config)
        config["matrix"]["scenario_01"]["planned"] = ["T", "F", "FULL_HISTORY"]
        self.assertIn("E-MATRIX", _codes(self._run(config)))

    def test_modalita_non_implementata_dichiarata_eseguibile(self):
        config = copy.deepcopy(self.config)
        config["modes"]["G"]["implemented"] = False
        self.assertIn("E-MATRIX", _codes(self._run(config)))

    def test_tutte_le_modalita_previste_sono_eseguibili(self):
        """La matrice e' completa: ogni cella prevista e' anche eseguibile."""
        for scenario_id in rq2.SCENARIO_IDS:
            self.assertEqual(rq2.runnable_modes(scenario_id, self.config),
                             rq2.planned_modes(scenario_id, self.config), scenario_id)

    def test_full_history_dentro_al_budget_viene_segnalato(self):
        config = copy.deepcopy(self.config)
        config["context_budget"]["applies_to"].append(rq2.FULL_HISTORY)
        self.assertIn("E-BUDGET", _codes(self._run(config)))

    def test_budget_mancante_o_nullo(self):
        config = copy.deepcopy(self.config)
        config["context_budget"]["max_tokens"] = 0
        self.assertIn("E-BUDGET", _codes(self._run(config)))

    def test_77_generazioni_previste_dalla_matrice(self):
        total = sum(7 * len(modes) for modes in validator.ROADMAP_MATRIX.values())
        self.assertEqual(total, 77)


class TestSeparazioneDeiFile(unittest.TestCase):
    def test_scenario_rq2_non_contiene_oracle(self):
        for scenario_id in ("scenario_03", "scenario_04"):
            raw = json.loads(rq2.SCENARIO_SOURCES[scenario_id][1].read_text("utf-8"))
            for key in validator.FORBIDDEN_SCENARIO_KEYS:
                self.assertNotIn(key, raw, "%s / %s" % (scenario_id, key))

    def test_oracle_nel_file_delle_conversazioni_viene_segnalato(self):
        original = rq2.SCENARIO_SOURCES["scenario_03"]
        raw = json.loads(original[1].read_text("utf-8"))
        raw["questions"] = [{"question_id": "SC03-QX"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario_03.json"
            path.write_text(json.dumps(raw, ensure_ascii=False), "utf-8")
            rq2.SCENARIO_SOURCES["scenario_03"] = ("rq2", path)
            try:
                errors = []
                validator.validate_scenario_file("scenario_03", errors)
            finally:
                rq2.SCENARIO_SOURCES["scenario_03"] = original
        self.assertIn("E-LEAK", _codes(errors))

    def test_rq2_scrive_solo_sotto_results_rq2(self):
        self.assertTrue(str(rq2.RQ2_RESULTS_DIR).endswith("results/rq2"))
        for path in (rq2.RQ2_SCENARIO_DIR, rq2.RQ2_ANNOTATION_DIR, rq2.RQ2_CONFIG_PATH):
            self.assertIn("rq2", str(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
