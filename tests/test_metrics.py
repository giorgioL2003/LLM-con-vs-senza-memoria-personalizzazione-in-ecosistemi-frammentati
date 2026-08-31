#!/usr/bin/env python3
"""Test del calcolo delle metriche aggregate del pilot (step 2).

Verificano due cose: che la validazione intercetti annotazioni incoerenti e
che le formule della sezione 10 di `EXPERIMENT.md` producano i numeri attesi,
compreso il caso in cui una metrica non e' calcolabile e deve valere `null`.

Esecuzione:
    python3 -m unittest discover -s tests -v
    python3 tests/test_metrics.py
"""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import summarize_evaluation as m  # noqa: E402


def codes(errors):
    """Estrae i codici [E-...] dai messaggi di errore."""
    return {e.split("]")[0].lstrip("[") for e in errors if e.startswith("[")}


def annotation(
    question_id="Q1",
    mode="C2",
    reachable=True,
    retrieval_success=True,
    answer_class="complete",
    obsolete_used=False,
    unsupported_claim=False,
    scenario_id="scenario_01",
    expected_behavior=None,
):
    """Annotazione minima e coerente; i test la corrompono un campo alla volta."""
    if expected_behavior is None:
        expected_behavior = "complete_answer" if reachable else "abstention"
    return {
        "scenario_id": scenario_id,
        "question_id": question_id,
        "mode": mode,
        "reachable": reachable,
        "retrieval_success": retrieval_success,
        "expected_behavior": expected_behavior,
        "answer_class": answer_class,
        "obsolete_used": obsolete_used,
        "unsupported_claim": unsupported_claim,
    }


class RatioTest(unittest.TestCase):
    """Con denominatore zero la metrica e' null, non zero."""

    def test_denominatore_zero_produce_null(self):
        self.assertEqual(m.ratio(0, 0), {"numerator": 0, "denominator": 0, "value": None})

    def test_valore_normale(self):
        self.assertEqual(m.ratio(11, 12)["value"], round(11 / 12, m.ROUNDING))

    def test_metrica_a_zero_resta_zero(self):
        """Zero su un denominatore valido non deve diventare null."""
        self.assertEqual(m.ratio(0, 14)["value"], 0.0)


class ValidationTest(unittest.TestCase):
    def test_annotazioni_coerenti_non_producono_errori(self):
        rows = [
            annotation(question_id="Q1", mode="C0", reachable=False, retrieval_success=None,
                       answer_class="correct_abstention"),
            annotation(question_id="Q1", mode="C2"),
        ]
        self.assertEqual(m.validate_rows(rows), [])

    def test_campo_mancante(self):
        row = annotation()
        del row["answer_class"]
        self.assertIn("E-FIELD", codes(m.validate_rows([row])))

    def test_campo_di_tipo_sbagliato(self):
        self.assertIn("E-FIELD", codes(m.validate_rows([annotation(reachable="si")])))

    def test_retrieval_success_non_booleano(self):
        self.assertIn("E-FIELD", codes(m.validate_rows([annotation(retrieval_success="ok")])))

    def test_annotazione_duplicata(self):
        rows = [annotation(), annotation()]
        self.assertIn("E-DUP", codes(m.validate_rows(rows)))

    def test_classe_di_risposta_sconosciuta(self):
        self.assertIn("E-VALUE", codes(m.validate_rows([annotation(answer_class="quasi")])))

    def test_modalita_sconosciuta(self):
        self.assertIn("E-VALUE", codes(m.validate_rows([annotation(mode="C3")])))

    def test_retrieval_success_deve_essere_null_se_non_raggiungibile(self):
        row = annotation(reachable=False, retrieval_success=True,
                         answer_class="correct_abstention")
        self.assertIn("E-RETRIEVAL-NULL", codes(m.validate_rows([row])))

    def test_full_history_non_ha_esito_di_retrieval(self):
        row = annotation(mode="FULL_HISTORY", retrieval_success=True)
        self.assertIn("E-DIAGNOSTIC", codes(m.validate_rows([row])))

    def test_astensione_corretta_solo_se_evidenza_non_raggiungibile(self):
        row = annotation(reachable=True, retrieval_success=True,
                         answer_class="correct_abstention")
        self.assertIn("E-ABSTENTION", codes(m.validate_rows([row])))

    def test_expected_behavior_incoerente_con_reachable(self):
        row = annotation(reachable=True, expected_behavior="abstention")
        self.assertIn("E-EXPECTED", codes(m.validate_rows([row])))

    def test_totale_annotazioni_sbagliato(self):
        self.assertIn("E-COUNT", codes(m.validate_totals([annotation()])))

    def test_annotazione_che_contraddice_il_retrieval(self):
        rows = [annotation(question_id="Q1", mode="C2", retrieval_success=True)]
        retrieval = [{
            "scenario_id": "scenario_01", "question_id": "Q1", "condition": "C2",
            "reachable": True, "retrieval_success": False,
        }]
        self.assertIn("E-RETRIEVAL-MATCH", codes(m.validate_against_retrieval(rows, retrieval)))

    def test_annotazione_senza_riga_di_retrieval(self):
        errors = m.validate_against_retrieval([annotation(mode="C1")], [])
        self.assertIn("E-RETRIEVAL-MISSING", codes(errors))

    def test_full_history_non_richiede_riga_di_retrieval(self):
        self.assertEqual(m.validate_against_retrieval([annotation(mode="FULL_HISTORY",
                                                                 retrieval_success=None)], []), [])

    def test_annotazione_che_contraddice_gli_input_di_generazione(self):
        rows = [annotation(question_id="Q1", mode="C2", reachable=True)]
        inputs = [{
            "scenario_id": "scenario_01", "question_id": "Q1", "mode": "C2",
            "reachable": False, "retrieval_success": True,
        }]
        self.assertIn("E-INPUT-MATCH", codes(m.validate_against_inputs(rows, inputs)))

    def test_prova_eseguita_ma_non_annotata(self):
        inputs = [
            {"scenario_id": "scenario_01", "question_id": "Q1", "mode": "C2",
             "reachable": True, "retrieval_success": True},
            {"scenario_id": "scenario_01", "question_id": "Q2", "mode": "C2",
             "reachable": True, "retrieval_success": True},
        ]
        errors = m.validate_against_inputs([annotation(question_id="Q1")], inputs)
        self.assertIn("E-INPUT-MISSING", codes(errors))


class FormulaTest(unittest.TestCase):
    """Metriche calcolate a mano su un piccolo insieme di annotazioni."""

    def setUp(self):
        # 5 prove: 3 raggiungibili (2 recuperate, di cui 1 completa e 1 parziale;
        # 1 raggiungibile ma non recuperata) e 2 non raggiungibili (1 astensione
        # corretta, 1 errata con informazione obsoleta e fatto non supportato).
        self.rows = [
            annotation(question_id="Q1", retrieval_success=True, answer_class="complete"),
            annotation(question_id="Q2", retrieval_success=True, answer_class="partial"),
            annotation(question_id="Q3", retrieval_success=False, answer_class="incorrect"),
            annotation(question_id="Q4", reachable=False, retrieval_success=None,
                       answer_class="correct_abstention"),
            annotation(question_id="Q5", reachable=False, retrieval_success=None,
                       answer_class="incorrect", obsolete_used=True, unsupported_claim=True),
        ]
        self.assertEqual(m.validate_rows(self.rows), [])
        self.metrics = m.metrics_for(self.rows)

    def test_conteggi_di_base(self):
        self.assertEqual(self.metrics["total_trials"], 5)
        self.assertEqual(self.metrics["reachable_questions"], 3)
        self.assertEqual(self.metrics["unreachable_questions"], 2)
        self.assertEqual(
            self.metrics["answer_class_counts"],
            {"complete": 1, "partial": 1, "incorrect": 2, "correct_abstention": 1},
        )

    def test_reachability_rate(self):
        self.assertEqual(self.metrics["reachability_rate"], m.ratio(3, 5))

    def test_retrieval_success_condizionato_alla_raggiungibilita(self):
        self.assertEqual(self.metrics["retrieval_success_rate"], m.ratio(2, 3))

    def test_complete_answer_rate_esclude_le_parziali(self):
        self.assertEqual(self.metrics["complete_answer_rate"], m.ratio(1, 5))

    def test_answer_success_condizionato_al_recupero(self):
        self.assertEqual(self.metrics["answer_success_rate"], m.ratio(1, 2))

    def test_correct_abstention_sulle_sole_non_raggiungibili(self):
        self.assertEqual(self.metrics["correct_abstention_rate"], m.ratio(1, 2))

    def test_indicatori_di_errore_sul_totale(self):
        self.assertEqual(self.metrics["obsolete_information_use_rate"], m.ratio(1, 5))
        self.assertEqual(self.metrics["unsupported_claim_rate"], m.ratio(1, 5))

    def test_nessuna_domanda_raggiungibile_produce_null(self):
        rows = [
            annotation(question_id="Q1", mode="C0", reachable=False, retrieval_success=None,
                       answer_class="correct_abstention"),
        ]
        metrics = m.metrics_for(rows)
        self.assertIsNone(metrics["retrieval_success_rate"]["value"])
        self.assertIsNone(metrics["answer_success_rate"]["value"])
        self.assertEqual(metrics["complete_answer_rate"]["value"], 0.0)
        self.assertEqual(metrics["correct_abstention_rate"]["value"], 1.0)

    def test_full_history_senza_metriche_di_retrieval(self):
        metrics = m.metrics_for(self.rows, with_retrieval_metrics=False)
        self.assertNotIn("retrieval_success_rate", metrics)
        self.assertNotIn("answer_success_rate", metrics)
        self.assertIn("complete_answer_rate", metrics)


class PilotFilesTest(unittest.TestCase):
    """Il pilot reale deve validare e produrre le metriche attese."""

    @classmethod
    def setUpClass(cls):
        cls.summary, cls.errors = m.build_summary(
            m.EVALUATION_PATH, m.RETRIEVAL_PATH, m.GENERATION_INPUTS_PATH
        )

    def test_le_56_annotazioni_sono_valide(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(self.summary["totals"]["annotations"], 56)

    def test_metriche_delle_condizioni_principali(self):
        conditions = self.summary["conditions"]
        self.assertEqual(sorted(conditions), ["C0", "C1", "C2"])
        self.assertEqual(conditions["C0"]["reachability_rate"], m.ratio(0, 14))
        self.assertEqual(conditions["C1"]["reachability_rate"], m.ratio(5, 14))
        self.assertEqual(conditions["C2"]["reachability_rate"], m.ratio(12, 14))
        self.assertIsNone(conditions["C0"]["retrieval_success_rate"]["value"])
        self.assertIsNone(conditions["C0"]["answer_success_rate"]["value"])
        self.assertEqual(conditions["C1"]["retrieval_success_rate"], m.ratio(5, 5))
        self.assertEqual(conditions["C2"]["retrieval_success_rate"], m.ratio(11, 12))
        self.assertEqual(conditions["C2"]["complete_answer_rate"], m.ratio(11, 14))

    def test_full_history_resta_diagnostico(self):
        diagnostic = self.summary["diagnostic"]["FULL_HISTORY"]
        self.assertNotIn("retrieval_success_rate", diagnostic)
        self.assertNotIn("answer_success_rate", diagnostic)
        self.assertNotIn("FULL_HISTORY", self.summary["conditions"])

    def test_calcolo_deterministico(self):
        again, errors = m.build_summary(
            m.EVALUATION_PATH, m.RETRIEVAL_PATH, m.GENERATION_INPUTS_PATH
        )
        self.assertEqual(errors, [])
        self.assertEqual(
            json.dumps(again, sort_keys=True), json.dumps(self.summary, sort_keys=True)
        )
        self.assertEqual(m.render_markdown(again), m.render_markdown(self.summary))

    def test_il_riepilogo_dichiara_che_sono_risultati_del_pilot(self):
        text = m.render_markdown(self.summary)
        self.assertIn("non conclusioni finali", text)
        self.assertIn("FULL_HISTORY", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
