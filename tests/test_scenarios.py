#!/usr/bin/env python3
"""Test del validatore degli scenari.

Verifica sia i due scenari reali del pilot (che devono risultare validi) sia
alcune corruzioni intenzionali dei dati, che devono essere intercettate.

Esecuzione:
    python3 -m unittest discover -s tests -v
    python3 tests/test_scenarios.py
"""

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_scenarios as v  # noqa: E402


def codes(errors):
    """Estrae i codici [E-...] dai messaggi di errore."""
    return {e.split("]")[0].lstrip("[") for e in errors if e.startswith("[")}


class ScenarioFilesTest(unittest.TestCase):
    """I file reali del pilot devono superare la validazione."""

    @classmethod
    def setUpClass(cls):
        cls.paths = v.default_paths()
        cls.scenarios = [v.load_scenario(p) for p in cls.paths]

    def test_due_scenari_presenti(self):
        self.assertEqual([p.name for p in self.paths], ["scenario_01.json", "scenario_02.json"])

    def test_collezione_valida(self):
        errors = v.validate_collection(self.scenarios, sources=[p.name for p in self.paths])
        self.assertEqual(errors, [], "\n".join(errors))

    def test_struttura_minima(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["scenario_id"]):
                self.assertEqual(len(scenario["sessions"]), 4)
                self.assertEqual(len(scenario["questions"]), 7)
                for session in scenario["sessions"]:
                    self.assertTrue(session["messages"])

    def test_copertura_per_scenario(self):
        by_id = {s["scenario_id"]: v.coverage_of(s) for s in self.scenarios}
        self.assertEqual(by_id["scenario_01"], {"C0": 0, "C1": 2, "C2": 6})
        self.assertEqual(by_id["scenario_02"], {"C0": 0, "C1": 3, "C2": 6})

    def test_copertura_totale(self):
        totals = {c: 0 for c in v.CONDITIONS}
        for scenario in self.scenarios:
            for condition, value in v.coverage_of(scenario).items():
                totals[condition] += value
        self.assertEqual(totals, {"C0": 0, "C1": 5, "C2": 12})
        self.assertEqual(sum(len(s["questions"]) for s in self.scenarios), 14)

    def test_categorie_ammesse_e_uniche(self):
        for scenario in self.scenarios:
            categories = [q["category"] for q in scenario["questions"]]
            with self.subTest(scenario=scenario["scenario_id"]):
                self.assertEqual(sorted(categories), sorted(v.ALLOWED_CATEGORIES))

    def test_informazione_assente_non_raggiungibile(self):
        for scenario in self.scenarios:
            for question in scenario["questions"]:
                if question["category"] == v.ABSENT_CATEGORY:
                    with self.subTest(question=question["question_id"]):
                        self.assertFalse(question["fact_present_in_corpus"])
                        self.assertEqual(question["required_evidence_ids"], [])
                        self.assertEqual(
                            question["reachability"], {"C0": False, "C1": False, "C2": False}
                        )

    def test_evidenze_esistono_e_appartengono_alle_sessioni(self):
        for scenario in self.scenarios:
            index = {
                m["message_id"]: s["session_id"]
                for s in scenario["sessions"]
                for m in s["messages"]
            }
            session_ids = [s["session_id"] for s in scenario["sessions"]]
            for question in scenario["questions"]:
                for evidence_id in question["required_evidence_ids"]:
                    with self.subTest(question=question["question_id"], evidence=evidence_id):
                        self.assertIn(evidence_id, index)
                        self.assertIn(index[evidence_id], session_ids)

    def test_perimetri_delle_condizioni(self):
        for scenario in self.scenarios:
            session_ids = [s["session_id"] for s in scenario["sessions"]]
            conditions = scenario["conditions"]
            with self.subTest(scenario=scenario["scenario_id"]):
                self.assertEqual(conditions["C0"]["accessible_sessions"], [])
                self.assertEqual(conditions["C1"]["accessible_sessions"], session_ids[-1:])
                self.assertEqual(conditions["C2"]["accessible_sessions"], session_ids)


class CorruptedDataTest(unittest.TestCase):
    """Errori introdotti di proposito devono essere segnalati."""

    def setUp(self):
        self.scenario = copy.deepcopy(v.load_scenario(v.DEFAULT_SCENARIO_DIR / "scenario_01.json"))

    def validate(self):
        return v.validate_scenario(self.scenario, source="scenario_01.json")

    def question(self, question_id):
        return next(q for q in self.scenario["questions"] if q["question_id"] == question_id)

    def test_baseline_valido(self):
        self.assertEqual(self.validate(), [])

    def test_message_id_duplicato(self):
        self.scenario["sessions"][1]["messages"][0]["message_id"] = "SC01-S1-U1"
        self.assertIn("E-DUP", codes(self.validate()))

    def test_question_id_duplicato(self):
        self.scenario["questions"][1]["question_id"] = self.scenario["questions"][0]["question_id"]
        self.assertIn("E-DUP", codes(self.validate()))

    def test_scenario_id_duplicato_nella_collezione(self):
        gemello = copy.deepcopy(self.scenario)
        errors = v.validate_collection([self.scenario, gemello], sources=["a.json", "b.json"])
        self.assertIn("E-DUP", codes(errors))

    def test_evidenza_inesistente(self):
        self.question("SC01-Q1")["required_evidence_ids"] = ["SC01-S9-U9"]
        self.assertIn("E-EVIDENCE-MISSING", codes(self.validate()))

    def test_messaggio_con_sessione_dichiarata_errata(self):
        self.scenario["sessions"][0]["messages"][0]["session_id"] = "SC01-S3"
        self.assertIn("E-EVIDENCE-SESSION", codes(self.validate()))

    def test_reachability_incoerente(self):
        # Q1 dipende dalla Sessione 1: non puo' essere raggiungibile in C1.
        self.question("SC01-Q1")["reachability"]["C1"] = True
        self.assertIn("E-REACH", codes(self.validate()))

    def test_c0_non_puo_essere_raggiungibile(self):
        self.question("SC01-Q5")["reachability"]["C0"] = True
        self.assertIn("E-REACH", codes(self.validate()))

    def test_perimetro_c1_alterato(self):
        self.scenario["conditions"]["C1"]["accessible_sessions"] = ["SC01-S3", "SC01-S4"]
        self.assertIn("E-PERIMETER", codes(self.validate()))

    def test_informazione_assente_con_evidenza(self):
        assente = self.question("SC01-Q7")
        assente["required_evidence_ids"] = ["SC01-S1-U1"]
        errors = self.validate()
        self.assertIn("E-ABSENT", codes(errors))

    def test_informazione_assente_dichiarata_raggiungibile(self):
        self.question("SC01-Q7")["reachability"]["C2"] = True
        self.assertIn("E-REACH", codes(self.validate()))

    def test_categoria_non_ammessa(self):
        self.question("SC01-Q1")["category"] = "obiettivo_principale"
        self.assertIn("E-CATEGORY", codes(self.validate()))

    def test_campo_obbligatorio_mancante(self):
        del self.question("SC01-Q3")["mandatory_facts"]
        self.assertIn("E-FIELD", codes(self.validate()))

    def test_ordine_sessioni_incoerente(self):
        self.scenario["sessions"][2]["order"] = 4
        self.assertIn("E-ORDER", codes(self.validate()))

    def test_ordine_messaggi_incoerente(self):
        self.scenario["sessions"][0]["messages"][1]["order"] = 5
        self.assertIn("E-ORDER", codes(self.validate()))

    def test_numero_di_sessioni_errato(self):
        self.scenario["sessions"].pop()
        self.assertIn("E-COUNT", codes(self.validate()))

    def test_numero_di_domande_errato(self):
        self.scenario["questions"].pop()
        self.assertIn("E-COUNT", codes(self.validate()))

    def test_copertura_attesa_non_rispettata(self):
        # Spostare l'evidenza di Q6 nella sola Sessione 4 la renderebbe locale:
        # cambia la copertura di C1 rispetto a quella registrata nel pilot.
        self.question("SC01-Q6")["required_evidence_ids"] = ["SC01-S4-U1"]
        self.question("SC01-Q6")["reachability"]["C1"] = True
        self.question("SC01-Q6")["expected_behavior_by_condition"]["C1"] = "Risposta completa"
        self.assertIn("E-COVERAGE", codes(self.validate()))

    def test_comportamento_atteso_incoerente(self):
        self.question("SC01-Q5")["expected_behavior_by_condition"]["C1"] = "Astensione"
        self.assertIn("E-BEHAVIOR", codes(self.validate()))

    def test_file_sorgente_inesistente(self):
        self.scenario["source_files"] = ["pilot/file_che_non_esiste.md"]
        self.assertIn("E-SOURCE-FILE", codes(self.validate()))

    def test_json_valido_su_disco(self):
        for path in v.default_paths():
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"))


class CommandLineTest(unittest.TestCase):
    """Il validatore deve essere eseguibile da riga di comando."""

    def test_exit_code_zero_sugli_scenari_reali(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "validate_scenarios.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Validazione superata", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
