#!/usr/bin/env python3
"""Test dell'analisi causale dei fallimenti del pilot (step 3).

Verificano due cose: che le tracce siano estratte fedelmente dai file gia'
esistenti e che una causa dichiarata in modo incoerente con la traccia venga
intercettata. Le classificazioni approvate non vengono ricontrollate qui:
sono coperte da `tests/test_metrics.py`.

Esecuzione:
    python3 -m unittest discover -s tests -v
    python3 tests/test_error_analysis.py
"""

import copy
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_error_analysis as ea  # noqa: E402


def codes(errors):
    """Estrae i codici [E-...] dai messaggi di errore."""
    return {e.split("]")[0].lstrip("[") for e in errors if e.startswith("[")}


class PilotCasesTest(unittest.TestCase):
    """I due casi reali devono essere estratti e validati senza errori."""

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.digests, cls.errors = ea.build_analysis()
        cls.by_id = {row["case_id"]: row for row in cls.rows}

    def test_due_casi_validi(self):
        self.assertEqual(self.errors, [])
        self.assertEqual([r["case_id"] for r in self.rows], ["SC02-Q6/C1", "SC02-Q6/C2"])

    def test_caso_c1_perimetro_della_memoria(self):
        row = self.by_id["SC02-Q6/C1"]
        self.assertEqual(row["condition"], "C1")
        self.assertFalse(row["reachable"])
        self.assertIsNone(row["retrieval_success"])
        self.assertEqual(row["accessible_message_ids"], ["SC02-S4-U1"])
        self.assertEqual(row["unreachable_evidence_ids"], ["SC02-S2-U1"])
        self.assertEqual(row["not_retrieved_evidence_ids"], [])
        self.assertEqual(row["primary_cause"], "reachability")
        self.assertEqual(row["secondary_cause"], "answer")
        self.assertIn("non si e' astenuto", row["secondary_cause_description"])
        self.assertEqual(row["answer_class"], "incorrect")
        self.assertTrue(row["unsupported_claim"])
        self.assertFalse(row["benchmark_defect"])

    def test_caso_c2_retrieval(self):
        row = self.by_id["SC02-Q6/C2"]
        self.assertEqual(row["condition"], "C2")
        self.assertTrue(row["reachable"])
        self.assertFalse(row["retrieval_success"])
        self.assertEqual(row["unreachable_evidence_ids"], [])
        self.assertEqual(row["not_retrieved_evidence_ids"], ["SC02-S2-U1"])
        self.assertNotIn("SC02-S2-U1", row["retrieved_message_ids"])
        self.assertEqual(row["primary_cause"], "retrieval")
        self.assertIsNone(row["secondary_cause"])
        self.assertEqual(row["answer_class"], "partial")
        self.assertFalse(row["unsupported_claim"])
        self.assertFalse(row["benchmark_defect"])

    def test_full_history_solo_come_controllo_diagnostico(self):
        self.assertIsNone(self.by_id["SC02-Q6/C1"]["diagnostic_reference"])
        diagnostic = self.by_id["SC02-Q6/C2"]["diagnostic_reference"]
        self.assertEqual(diagnostic["mode"], "FULL_HISTORY")
        self.assertEqual(diagnostic["answer_class"], "complete")
        self.assertIn("SC02-S2-U1", diagnostic["context_message_ids"])
        for row in self.rows:
            self.assertIn(row["condition"], ea.CONDITIONS)

    def test_traccia_fedele_ai_file_di_origine(self):
        """La risposta registrata deve essere quella davvero generata."""
        generation = ea.load_jsonl(ea.GENERATION_PATH)
        for row in self.rows:
            source = ea.find(
                generation, "mode", row["scenario_id"], row["question_id"], row["condition"]
            )
            self.assertEqual(row["model_answer"], source["model_answer"])

    def test_calcolo_deterministico(self):
        again, digests, errors = ea.build_analysis()
        self.assertEqual(errors, [])
        self.assertEqual(again, self.rows)
        self.assertEqual(ea.render_markdown(again, digests), ea.render_markdown(self.rows, self.digests))

    def test_il_riepilogo_dichiara_stato_e_controllo_diagnostico(self):
        text = ea.render_markdown(self.rows, self.digests)
        self.assertIn("non conclusioni finali", text)
        self.assertIn("controllo diagnostico", text)


class CauseValidationTest(unittest.TestCase):
    """Una causa non sostenuta dalla traccia deve essere intercettata."""

    @classmethod
    def setUpClass(cls):
        rows, _digests, _errors = ea.build_analysis()
        cls.by_id = {row["case_id"]: row for row in rows}

    def corrupted(self, case_id, **changes):
        row = copy.deepcopy(self.by_id[case_id])
        row.update(changes)
        return row

    def test_reachability_dichiarata_con_evidenza_raggiungibile(self):
        row = self.corrupted("SC02-Q6/C2", primary_cause="reachability", secondary_cause=None)
        self.assertIn("E-CAUSE-EVIDENCE", codes(ea.validate_case(row)))

    def test_retrieval_dichiarato_con_evidenza_irraggiungibile(self):
        row = self.corrupted("SC02-Q6/C1", primary_cause="retrieval", secondary_cause=None)
        self.assertIn("E-CAUSE-EVIDENCE", codes(ea.validate_case(row)))

    def test_answer_dichiarato_con_evidenza_non_recuperata(self):
        row = self.corrupted("SC02-Q6/C2", primary_cause="answer", secondary_cause=None)
        self.assertIn("E-CAUSE-EVIDENCE", codes(ea.validate_case(row)))

    def test_causa_sconosciuta(self):
        row = self.corrupted("SC02-Q6/C1", primary_cause="modello_stanco")
        self.assertIn("E-CAUSE", codes(ea.validate_case(row)))

    def test_causa_secondaria_uguale_alla_principale(self):
        row = self.corrupted("SC02-Q6/C1", secondary_cause="reachability")
        self.assertIn("E-CAUSE", codes(ea.validate_case(row)))

    def test_benchmark_defect_senza_causa_benchmark(self):
        row = self.corrupted("SC02-Q6/C1", benchmark_defect=True)
        self.assertIn("E-BENCHMARK", codes(ea.validate_case(row)))

    def test_causa_benchmark_senza_benchmark_defect(self):
        row = self.corrupted("SC02-Q6/C1", primary_cause="benchmark", secondary_cause=None)
        self.assertIn("E-BENCHMARK", codes(ea.validate_case(row)))

    def test_full_history_non_puo_essere_una_condizione(self):
        row = self.corrupted("SC02-Q6/C2", condition="FULL_HISTORY")
        self.assertIn("E-CONDITION", codes(ea.validate_case(row)))

    def test_controllo_diagnostico_solo_per_fallimenti_di_retrieval(self):
        row = copy.deepcopy(self.by_id["SC02-Q6/C1"])
        row["diagnostic_reference"] = copy.deepcopy(
            self.by_id["SC02-Q6/C2"]["diagnostic_reference"]
        )
        self.assertIn("E-DIAGNOSTIC", codes(ea.validate_case(row)))

    def test_messaggio_recuperato_fuori_dal_perimetro(self):
        row = self.corrupted(
            "SC02-Q6/C1", retrieved_message_ids=["SC02-S4-U1", "SC02-S2-U1"]
        )
        self.assertIn("E-TRACE", codes(ea.validate_case(row)))

    def test_caso_senza_fallimento(self):
        row = self.corrupted("SC02-Q6/C2", answer_class="complete")
        self.assertIn("E-CASE", codes(ea.validate_case(row)))

    def test_analisi_che_contraddice_la_classificazione_approvata(self):
        row = self.corrupted("SC02-Q6/C1", unsupported_claim=False)
        evaluation = ea.load_jsonl(ea.EVALUATION_PATH)
        self.assertIn("E-EVAL-MATCH", codes(ea.validate_against_evaluation([row], evaluation)))

    def test_caso_duplicato(self):
        row = self.by_id["SC02-Q6/C1"]
        evaluation = ea.load_jsonl(ea.EVALUATION_PATH)
        self.assertIn("E-DUP", codes(ea.validate_all([row, copy.deepcopy(row)], evaluation)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
