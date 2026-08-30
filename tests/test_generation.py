#!/usr/bin/env python3
"""Test essenziali della fase di generazione.

Verificano soltanto quattro cose: come viene costruito il comando, che il
modello richiesto sia quello dichiarato, che ogni chiamata sia indipendente e
che le risposte vengano salvate e riprese correttamente. Nessun test chiama il
modello davvero: al posto di `subprocess.run` viene usato un finto runner.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_generation as gen  # noqa: E402


class FakeCompleted:
    def __init__(self, stdout, returncode=0, stderr=""):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def fake_stream(answer="risposta", model="claude-sonnet-5"):
    """Output stream-json come quello vero: init, messaggio assistant, risultato."""
    events = [
        {"type": "system", "subtype": "init", "model": model, "tools": []},
        {"type": "assistant", "message": {"model": model,
                                          "content": [{"type": "text", "text": answer}]}},
        {"type": "result", "is_error": False, "result": answer},
    ]
    return "\n".join(json.dumps(event) for event in events)


def fake_runner(answer="risposta", model="claude-sonnet-5", calls=None):
    """Finto `subprocess.run`: registra le chiamate e risponde in stream-json."""

    def runner(command, input=None, cwd=None, capture_output=None, text=None, timeout=None):
        if calls is not None:
            calls.append({"command": command, "input": input, "cwd": cwd})
        return FakeCompleted(fake_stream(answer, model))

    return runner


def _input_row(question_id="SC01-Q1", mode="C0", prompt="Domanda:\ntest"):
    return {
        "scenario_id": "scenario_01",
        "question_id": question_id,
        "mode": mode,
        "prompt": prompt,
    }


class TestComando(unittest.TestCase):
    def test_modalita_non_interattiva_senza_strumenti(self):
        command = gen.build_command()
        self.assertEqual(command[0], "claude")
        self.assertIn("--print", command)
        # tutti gli strumenti disattivati: il valore di --tools e' la stringa vuota
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertIn("--strict-mcp-config", command)
        self.assertIn("--no-session-persistence", command)
        self.assertEqual(command[command.index("--output-format") + 1], "stream-json")

    def test_modello_ed_effort_esatti(self):
        command = gen.build_command()
        self.assertEqual(command[command.index("--model") + 1], "claude-sonnet-5")
        self.assertEqual(command[command.index("--effort") + 1], "medium")

    def test_nessun_fallback_e_nessuna_ripresa(self):
        command = gen.build_command()
        for option in ("--fallback-model", "--resume", "--continue", "-c", "-r"):
            self.assertNotIn(option, command)

    def test_modello_usato_letto_dal_messaggio_che_risponde(self):
        answer, model, error = gen.parse_stream(fake_stream("Lisbona", "claude-sonnet-5"))
        self.assertEqual((answer, model, error), ("Lisbona", "claude-sonnet-5", None))

    def test_un_altro_modello_verrebbe_riconosciuto(self):
        # se rispondesse un modello diverso da quello richiesto, sarebbe visibile
        _answer, model, _error = gen.parse_stream(fake_stream("Lisbona", "claude-haiku-4-5-20251001"))
        self.assertEqual(model, "claude-haiku-4-5-20251001")


class TestIndipendenza(unittest.TestCase):
    def test_una_chiamata_per_input_con_il_solo_prompt(self):
        calls = []
        rows = [
            _input_row("SC01-Q1", "C0", "prompt uno"),
            _input_row("SC01-Q1", "C1", "prompt due"),
        ]
        gen.run(rows, cwd="/tmp/neutra", runner=fake_runner(calls=calls))

        self.assertEqual(len(calls), 2)
        # nessuna conversazione fra le due chiamate: stesso comando, prompt diversi
        self.assertEqual(calls[0]["command"], calls[1]["command"])
        self.assertEqual([call["input"] for call in calls], ["prompt uno", "prompt due"])
        # nessun contenuto della prima chiamata entra nella seconda
        self.assertNotIn("prompt uno", calls[1]["input"])
        # directory neutra, non quella del progetto
        self.assertEqual(calls[1]["cwd"], "/tmp/neutra")

    def test_errore_di_una_chiamata_non_ferma_le_altre(self):
        def runner(command, input=None, cwd=None, **kwargs):
            if "due" in input:
                raise subprocess.TimeoutExpired(command, 1)
            return FakeCompleted(fake_stream("ok"))

        results = gen.run(
            [_input_row("SC01-Q1", "C0", "uno"), _input_row("SC01-Q1", "C1", "due"),
             _input_row("SC01-Q1", "C2", "tre")],
            cwd="/tmp/neutra",
            runner=runner,
        )
        self.assertEqual([bool(result["error"]) for result in results], [False, True, False])


class TestSalvataggio(unittest.TestCase):
    def test_riga_salvata_con_tutti_i_campi(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "smoke.jsonl"
            gen.run(
                [_input_row("SC01-Q1", "C2", "prompt")],
                cwd=directory,
                runner=fake_runner(answer="due obiettivi"),
                on_result=lambda result: gen.append_result(out, result),
            )
            saved = json.loads(out.read_text(encoding="utf-8").strip())

        self.assertEqual(saved["scenario_id"], "scenario_01")
        self.assertEqual(saved["question_id"], "SC01-Q1")
        self.assertEqual(saved["mode"], "C2")
        self.assertEqual(saved["model_requested"], "claude-sonnet-5")
        self.assertEqual(saved["model_used"], "claude-sonnet-5")
        self.assertEqual(saved["effort"], "medium")
        self.assertEqual(saved["model_answer"], "due obiettivi")
        self.assertIsNone(saved["error"])

    def test_ripresa_salta_solo_le_prove_completate(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "smoke.jsonl"
            gen.append_result(out, {"scenario_id": "scenario_01", "question_id": "SC01-Q1",
                                    "mode": "C0", "error": None})
            gen.append_result(out, {"scenario_id": "scenario_01", "question_id": "SC01-Q1",
                                    "mode": "C1", "error": "timeout"})
            done = gen.load_done(out)

        self.assertIn(("scenario_01", "SC01-Q1", "C0"), done)
        self.assertNotIn(("scenario_01", "SC01-Q1", "C1"), done)


class TestSelezione(unittest.TestCase):
    def test_una_domanda_nelle_quattro_modalita(self):
        rows = gen.load_inputs()
        selected = gen.select(rows, question_id="SC01-Q1")
        self.assertEqual([row["mode"] for row in selected], ["C0", "C1", "C2", "FULL_HISTORY"])


if __name__ == "__main__":
    unittest.main()
