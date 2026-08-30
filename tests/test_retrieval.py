#!/usr/bin/env python3
"""Test essenziali del retrieval Turn-level RAG.

Verificano soltanto le regole del retriever e il perimetro delle condizioni.
La struttura dei dati e la raggiungibilita' dichiarata sono gia' coperte da
`tests/test_scenarios.py` e non vengono ricontrollate qui.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_retrieval_pilot as rag  # noqa: E402


def _message(message_id, session_id, session_order, content, role="user"):
    return {
        "message_id": message_id,
        "session_id": session_id,
        "order": 1,
        "role": role,
        "content": content,
    }


def _scenario():
    """Scenario minimo: una sessione per messaggio, come nel pilot."""
    sessions = [
        {
            "session_id": "T-S%d" % order,
            "order": order,
            "title": "sessione %d" % order,
            "messages": [
                _message("T-S%d-U1" % order, "T-S%d" % order, order, content),
                _message("T-S%d-A1" % order, "T-S%d" % order, order, "va bene", role="assistant"),
            ],
        }
        for order, content in enumerate(
            [
                "il token di reset scade dopo 15 minuti",
                "la pipeline CI espone un vecchio token",
                "resta da provare il collegamento dall app mobile",
                "argomento del tutto diverso: sostituzione dei portatili",
            ],
            start=1,
        )
    ]
    return {
        "scenario_id": "scenario_test",
        "conditions": {
            "C0": {"accessible_sessions": []},
            "C1": {"accessible_sessions": ["T-S4"]},
            "C2": {"accessible_sessions": ["T-S1", "T-S2", "T-S3", "T-S4"]},
        },
        "sessions": sessions,
        "questions": [],
    }


class TokenizeTest(unittest.TestCase):
    def test_minuscolo_e_caratteri_conservati(self):
        tokens = rag.tokenize("Il token `svc-reporting` e reset_audit alle 09:10!")
        self.assertEqual(
            tokens,
            ["il", "token", "svc-reporting", "e", "reset_audit", "alle", "09", "10"],
        )


class CorpusTest(unittest.TestCase):
    def test_perimetri_delle_condizioni(self):
        scenario = _scenario()
        ids = lambda condition: [  # noqa: E731
            d["message_id"]
            for d in rag.build_corpus(
                scenario, scenario["conditions"][condition]["accessible_sessions"]
            )
        ]
        self.assertEqual(ids("C0"), [])
        self.assertEqual(ids("C1"), ["T-S4-U1"])
        self.assertEqual(ids("C2"), ["T-S1-U1", "T-S2-U1", "T-S3-U1", "T-S4-U1"])

    def test_messaggi_dell_assistente_non_indicizzati(self):
        scenario = _scenario()
        corpus = rag.build_corpus(scenario, ["T-S1", "T-S2", "T-S3", "T-S4"])
        self.assertFalse([d for d in corpus if d["message_id"].endswith("-A1")])


class RetrieveTest(unittest.TestCase):
    def setUp(self):
        self.corpus = rag.build_corpus(_scenario(), ["T-S1", "T-S2", "T-S3", "T-S4"])

    def test_top_k_e_pertinenza(self):
        retrieved = rag.retrieve("quando scade il token di reset?", self.corpus)
        self.assertEqual(len(retrieved), rag.TOP_K)
        self.assertEqual(retrieved[0]["message_id"], "T-S1-U1")

    def test_corpus_piu_piccolo_di_k(self):
        self.assertEqual(rag.retrieve("qualsiasi domanda", []), [])
        uno = rag.retrieve("qualsiasi domanda", self.corpus[:1])
        self.assertEqual([d["message_id"] for d in uno], ["T-S1-U1"])

    def test_parita_di_punteggio_ordine_deterministico(self):
        # Query senza termini in comune: tutti i punteggi valgono 0 e deve
        # rimanere l'ordine di sessione e di messaggio.
        retrieved = rag.retrieve("zzzz qqqq", self.corpus)
        self.assertEqual(
            [d["message_id"] for d in retrieved], ["T-S1-U1", "T-S2-U1"]
        )
        self.assertEqual([d["score"] for d in retrieved], [0.0, 0.0])


class EvaluateTest(unittest.TestCase):
    def _question(self, reachability, evidence):
        return {
            "question_id": "T-Q1",
            "category": "cross_session_link",
            "text": "quando scade il token di reset?",
            "required_evidence_ids": evidence,
            "reachability": reachability,
        }

    def test_successo_null_quando_non_raggiungibile(self):
        question = self._question({"C0": False, "C1": False, "C2": False}, [])
        for condition in rag.CONDITIONS:
            row = rag.evaluate(_scenario(), question, condition)
            self.assertIsNone(row["retrieval_success"], condition)

    def test_successo_vero_solo_se_tutte_le_evidenze_sono_recuperate(self):
        scenario = _scenario()
        ok = self._question({"C0": False, "C1": False, "C2": True}, ["T-S1-U1"])
        row = rag.evaluate(scenario, ok, "C2")
        self.assertTrue(row["retrieval_success"])

        # T-S4-U1 e' fuori tema: raggiungibile ma non recuperato.
        parziale = self._question({"C0": False, "C1": False, "C2": True}, ["T-S1-U1", "T-S4-U1"])
        row = rag.evaluate(scenario, parziale, "C2")
        self.assertFalse(row["retrieval_success"])
        self.assertNotIn("T-S4-U1", row["retrieved_message_ids"])

    def test_c0_non_recupera_nulla(self):
        question = self._question({"C0": False, "C1": True, "C2": True}, ["T-S4-U1"])
        row = rag.evaluate(_scenario(), question, "C0")
        self.assertEqual(row["accessible_message_ids"], [])
        self.assertEqual(row["retrieved_message_ids"], [])


if __name__ == "__main__":
    unittest.main()
