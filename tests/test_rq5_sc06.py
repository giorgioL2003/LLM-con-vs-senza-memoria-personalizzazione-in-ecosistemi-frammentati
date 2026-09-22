#!/usr/bin/env python3
"""Test offline di RQ5 / SC06.

Nessun test scarica modelli, apre connessioni o esegue generazioni reali: le
chiamate a Ollama sono sostituite da una funzione finta che risponde con
payload preparati.

I test verificano due cose in parallelo: che gli artefatti veri rispettino il
protocollo e che i controlli sappiano riconoscere una violazione costruita
apposta. Un validatore che accetta tutto non dimostra niente.
"""

from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq3"))

import rq5_common as common  # noqa: E402
import build_rq5_inputs as builder  # noqa: E402
import validate_rq5_inputs as validator  # noqa: E402
import run_rq5_ollama as runner  # noqa: E402
import evaluate_rq5 as evaluator  # noqa: E402
import summarize_rq5 as summarizer  # noqa: E402

CONFIG = common.load_config()
MODELS = [model["ollama_tag"] for model in CONFIG["models"]]

_BUILT = {}


def built():
    """Costruisce una volta sola richieste e oracle dalle sorgenti reali."""
    if not _BUILT:
        requests, oracle, _ = builder.build(CONFIG)
        _BUILT["requests"] = requests
        _BUILT["oracle"] = oracle
    return _BUILT["requests"], _BUILT["oracle"]


def fixture_episode():
    """Tre casi costruiti a mano, con un campo mancante nel caso C."""
    return {
        "Caso A": {
            "asset.assets[].variety": ["S - Web application"],
            "action.hacking.variety": ["Brute force"],
        },
        "Caso B": {
            "asset.assets[].variety": ["P - Human resources"],
            "action.social.vector": ["Email"],
        },
        "Caso C": {
            "action.malware.variety": ["Ransomware"],
            "action.social.variety": ["Phishing"],
        },
    }


# --------------------------------------------------------------------------
# Sorgenti
# --------------------------------------------------------------------------

class TestSources(unittest.TestCase):
    def test_declared_hashes_match(self):
        verified = common.verify_sources(CONFIG)
        self.assertEqual(len(verified), 4)
        for name, _path, expected, _rel in common.source_entries(CONFIG):
            self.assertEqual(verified[name]["sha256"], expected)

    def test_source_counts(self):
        self.assertEqual(len(common.load_queries(CONFIG)), 2124)
        self.assertEqual(len(common.load_oracle(CONFIG)), 2124)
        self.assertEqual(len(common.load_case_mapping(CONFIG)), 708)
        self.assertEqual(len(common.load_episodes(CONFIG)), 236)

    def test_altered_source_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for _name, path, _sha, rel in common.source_entries(CONFIG):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
            corrupted = root / CONFIG["source"]["queries_path"]
            corrupted.write_text(corrupted.read_text() + "\n")
            with self.assertRaises(ValueError):
                common.verify_sources(CONFIG, root)


# --------------------------------------------------------------------------
# Costruzione dei contesti
# --------------------------------------------------------------------------

class TestContextBuilder(unittest.TestCase):
    def test_distractor_uses_queried_field_when_present(self):
        cases = fixture_episode()
        self.assertEqual(
            common.distractor_field(cases["Caso B"], "asset.assets[].variety"),
            "asset.assets[].variety",
        )

    def test_distractor_falls_back_to_lexicographically_first_field(self):
        cases = fixture_episode()
        self.assertEqual(
            common.distractor_field(cases["Caso C"], "asset.assets[].variety"),
            "action.malware.variety",
        )

    def test_block_order_follows_sha256_rule(self):
        cases = fixture_episode()
        _text, blocks = common.build_context(
            CONFIG, "SC06-E001-A-Q1", "Caso A", "asset.assets[].variety",
            cases, "sufficient",
        )
        keys = [common.order_key(CONFIG, "SC06-E001-A-Q1", b["case_alias"]) for b in blocks]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual({b["case_alias"] for b in blocks}, {"Caso A", "Caso B", "Caso C"})

    def test_insufficient_differs_only_by_target_block(self):
        cases = fixture_episode()
        question_id = "SC06-E001-A-Q1"
        sufficient, blocks_s = common.build_context(
            CONFIG, question_id, "Caso A", "asset.assets[].variety", cases, "sufficient")
        insufficient, blocks_i = common.build_context(
            CONFIG, question_id, "Caso A", "asset.assets[].variety", cases, "insufficient")

        kept = [b for b in blocks_s if b["case_alias"] != "Caso A"]
        self.assertEqual([b["case_alias"] for b in kept],
                         [b["case_alias"] for b in blocks_i])
        self.assertEqual([b["field"] for b in kept], [b["field"] for b in blocks_i])
        self.assertEqual([b["values"] for b in kept], [b["values"] for b in blocks_i])
        removed = [b for b in sufficient.split(common.BLOCK_SEPARATOR)
                   if not b.startswith("Caso A.")]
        self.assertEqual(common.BLOCK_SEPARATOR.join(removed), insufficient)
        self.assertNotIn("Caso A.", insufficient)

    def test_block_format_matches_config(self):
        text = common.render_block(
            CONFIG, "Caso A", "asset.assets[].variety", ["S - Web application", "P - Human"])
        self.assertEqual(
            text, "Caso A.\n- Tipi di risorse coinvolte: S - Web application; P - Human")

    def test_question_parsing_is_independent_of_oracle(self):
        oracle = common.load_oracle(CONFIG)
        for row in oracle[:200]:
            alias, field = common.parse_question(row["question"], CONFIG)
            self.assertEqual(alias, row["case_alias"])
            self.assertEqual(field, row["field"])


# --------------------------------------------------------------------------
# Richieste costruite
# --------------------------------------------------------------------------

class TestBuiltInputs(unittest.TestCase):
    def test_counts_per_split(self):
        requests, _ = built()
        development = [row for row in requests if row["split"] == "development"]
        evaluation = [row for row in requests if row["split"] == "evaluation"]
        self.assertEqual(len(development), 216)
        self.assertEqual(len(evaluation), 4032)
        self.assertEqual(len(development) * len(MODELS), 432)
        self.assertEqual(len(evaluation) * len(MODELS), 8064)

    def test_episode_ranges_are_disjoint(self):
        requests, _ = built()
        development = {common.episode_number(row["episode_id"]) for row in requests
                       if row["split"] == "development"}
        evaluation = {common.episode_number(row["episode_id"]) for row in requests
                      if row["split"] == "evaluation"}
        self.assertEqual(development, set(range(1, 13)))
        self.assertEqual(evaluation, set(range(13, 237)))
        self.assertFalse(development & evaluation)

    def test_cells_are_unique(self):
        requests, _ = built()
        cells = [common.cell_id(row["split"], tag, row["condition"], row["question_id"])
                 for row in requests for tag in MODELS]
        self.assertEqual(len(cells), len(set(cells)))
        self.assertEqual(len(cells), 8496)

    def test_same_prompt_for_both_models(self):
        requests, _ = built()
        for row in requests[:400]:
            payloads = [common.chat_payload(CONFIG, tag, row["messages"][0]["content"],
                                            row["messages"][1]["content"]) for tag in MODELS]
            self.assertEqual(payloads[0]["messages"], payloads[1]["messages"])
            digests = {common.prompt_sha256(p["messages"][0]["content"],
                                            p["messages"][1]["content"]) for p in payloads}
            self.assertEqual(digests, {row["prompt_sha256"]})

    def test_requests_carry_no_oracle_field(self):
        requests, _ = built()
        forbidden = CONFIG["context_builder"]["forbidden_prompt_inputs"]
        for row in requests:
            for key in forbidden:
                self.assertNotIn(key, row)

    def test_prompts_carry_no_identifier_or_source(self):
        requests, _ = built()
        cases = {(row["episode_id"], row["case_alias"]): row
                 for row in common.load_case_mapping(CONFIG)}
        for row in requests:
            text = row["messages"][0]["content"] + row["messages"][1]["content"]
            self.assertNotIn("http", text)
            self.assertNotIn("data/json", text)
            for alias in ("Caso A", "Caso B", "Caso C"):
                meta = cases.get((row["episode_id"], alias))
                if meta:
                    self.assertNotIn(meta["incident_id"], text)
                    self.assertNotIn(meta["source_path"], text)
                    self.assertNotIn(meta["reference"].strip(), text)

    def test_insufficient_prompts_have_no_target_block(self):
        requests, oracle = built()
        by_request = {row["request_id"]: row for row in oracle}
        for row in requests:
            if row["condition"] != "insufficient":
                continue
            alias = by_request[row["request_id"]]["case_alias"]
            self.assertNotIn(alias, row["context_block_order"])
            context = row["messages"][1]["content"].split("\n\nQUESTION")[0]
            self.assertNotIn(f"\n{alias}.", context)

    def test_oracle_expectations_per_condition(self):
        _requests, oracle = built()
        design = {row["question_id"]: row for row in common.load_oracle(CONFIG)}
        for row in oracle:
            if row["condition"] == "sufficient":
                self.assertEqual(row["expected_values"],
                                 design[row["question_id"]]["expected_values"])
            else:
                self.assertEqual(row["expected_values"], [])


# --------------------------------------------------------------------------
# Validatore
# --------------------------------------------------------------------------

class TestValidator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        requests, oracle = built()
        for split in common.SPLITS:
            common.dump_jsonl(self.dir / f"{split}_requests.jsonl",
                              [row for row in requests if row["split"] == split])
            common.dump_jsonl(self.dir / f"{split}_oracle.jsonl",
                              [row for row in oracle if row["split"] == split])

    def tearDown(self):
        self.tmp.cleanup()

    def _validate(self):
        report = validator.Report(verbose=False)
        ok = validator.validate(CONFIG, self.dir, report)
        return ok, report

    def test_real_inputs_pass(self):
        ok, report = self._validate()
        self.assertTrue(ok, [check for check in report.failed])
        self.assertGreaterEqual(len(report.checks), 25)

    def _corrupt(self, split, mutate):
        path = self.dir / f"{split}_requests.jsonl"
        rows = common.read_jsonl(path)
        mutate(rows)
        common.dump_jsonl(path, rows)

    def test_detects_changed_prompt(self):
        self._corrupt("development",
                      lambda rows: rows[0]["messages"][1].__setitem__(
                          "content", rows[0]["messages"][1]["content"] + " extra"))
        ok, report = self._validate()
        self.assertFalse(ok)
        self.assertIn("prompt ricostruiti indipendentemente",
                      [check["check"] for check in report.failed])

    def test_detects_missing_request(self):
        self._corrupt("development", lambda rows: rows.pop())
        ok, report = self._validate()
        self.assertFalse(ok)
        failed = [check["check"] for check in report.failed]
        self.assertTrue(any("richieste indipendenti dal modello" in name for name in failed))

    def test_detects_leaked_identifier(self):
        cases = {(row["episode_id"], row["case_alias"]): row
                 for row in common.load_case_mapping(CONFIG)}

        def mutate(rows):
            row = rows[0]
            incident = cases[(row["episode_id"], "Caso A")]["incident_id"]
            row["messages"][1]["content"] += f"\n(incidente {incident})"

        self._corrupt("development", mutate)
        ok, report = self._validate()
        self.assertFalse(ok)
        self.assertIn("nessun identificativo VERIS o riferimento nei prompt",
                      [check["check"] for check in report.failed])

    def test_detects_reordered_blocks(self):
        def mutate(rows):
            row = next(r for r in rows if len(r["context_block_order"]) == 3)
            context, question = row["messages"][1]["content"].split("\n\nQUESTION\n")
            blocks = context[len("CONTEXT\n"):].split(common.BLOCK_SEPARATOR)
            blocks[0], blocks[1] = blocks[1], blocks[0]
            row["messages"][1]["content"] = (
                "CONTEXT\n" + common.BLOCK_SEPARATOR.join(blocks) + "\n\nQUESTION\n" + question)

        self._corrupt("development", mutate)
        ok, report = self._validate()
        self.assertFalse(ok)

    def test_detects_duplicated_request(self):
        self._corrupt("development", lambda rows: rows.append(copy.deepcopy(rows[0])))
        ok, report = self._validate()
        self.assertFalse(ok)
        self.assertIn("request_id univoci", [check["check"] for check in report.failed])


# --------------------------------------------------------------------------
# Parser dell'output
# --------------------------------------------------------------------------

class TestOutputParser(unittest.TestCase):
    def parse(self, content):
        return common.parse_model_output(content, CONFIG)

    def test_valid_output(self):
        values, error = self.parse('{"values": ["Brute force"]}')
        self.assertEqual(values, ["Brute force"])
        self.assertIsNone(error)

    def test_duplicates_and_order_do_not_matter(self):
        first, _ = self.parse('{"values": ["A", "B", "A"]}')
        second, _ = self.parse('{"values": ["B", "A"]}')
        self.assertEqual(common.normalize_values(first, CONFIG),
                         common.normalize_values(second, CONFIG))

    def test_empty_list_is_valid(self):
        values, error = self.parse('{"values": []}')
        self.assertEqual(values, [])
        self.assertIsNone(error)

    def test_broken_json(self):
        self.assertEqual(self.parse('{"values": ['), (None, "not_json"))
        self.assertEqual(self.parse("Non lo so."), (None, "not_json"))

    def test_extra_keys_are_rejected(self):
        values, error = self.parse('{"values": ["A"], "reason": "perche"}')
        self.assertIsNone(values)
        self.assertTrue(error.startswith("extra_keys:"))

    def test_missing_key_and_wrong_types(self):
        self.assertEqual(self.parse('{"risposte": []}'), (None, "missing_values_key"))
        self.assertEqual(self.parse('{"values": "A"}'), (None, "values_not_list"))
        self.assertEqual(self.parse('{"values": [1, 2]}'),
                         (None, "values_not_list_of_strings"))
        self.assertEqual(self.parse('["A"]'), (None, "not_json_object"))
        self.assertEqual(self.parse(""), (None, "empty_content"))

    def test_normalization_keeps_case_and_strips_outer_spaces(self):
        self.assertEqual(common.normalize_values(["  Brute force  "], CONFIG),
                         {"Brute force"})
        self.assertNotEqual(common.normalize_values(["brute force"], CONFIG),
                            {"Brute force"})

    def test_unicode_nfc_normalization(self):
        decomposed = "Café"
        composed = "Café"
        self.assertEqual(common.normalize_values([decomposed], CONFIG),
                         common.normalize_values([composed], CONFIG))


# --------------------------------------------------------------------------
# Valutazione
# --------------------------------------------------------------------------

def _request(condition="sufficient", question_id="SC06-E100-A-Q1"):
    return {
        "request_id": common.request_id("evaluation", condition, question_id),
        "split": "evaluation",
        "condition": condition,
        "question_id": question_id,
        "episode_id": "SC06-E100",
        "prompt_sha256": "hash",
        "messages": [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}],
    }


def _oracle(condition="sufficient", expected=("Brute force", "SQLi"),
            detectable=("Phishing",)):
    return {
        "request_id": common.request_id("evaluation", condition, "SC06-E100-A-Q1"),
        "condition": condition,
        "family": "variety",
        "field": "action.hacking.variety",
        "case_alias": "Caso A",
        "expected_values": list(expected) if condition == "sufficient" else [],
        "detectable_cross_case_intrusion_values": list(detectable),
    }


def _response(content, status="ok", prompt_sha256="hash"):
    return {
        "cell_id": "x", "status": status, "content": content,
        "prompt_sha256": prompt_sha256, "ollama_metrics": {},
        "error": None, "attempts": 1,
    }


class TestEvaluation(unittest.TestCase):
    def evaluate(self, condition, content, expected=("Brute force", "SQLi"),
                 detectable=("Phishing",), status="ok", response=True):
        return evaluator.evaluate_cell(
            CONFIG, _request(condition), _oracle(condition, expected, detectable),
            "gemma3:4b", _response(content, status) if response else None,
        )

    def test_exact_match(self):
        row = self.evaluate("sufficient", '{"values": ["SQLi", "Brute force"]}')
        self.assertTrue(row["exact_match"])
        self.assertEqual(row["false_negatives"], 0)
        self.assertEqual(row["false_positives"], 0)
        self.assertFalse(row["has_unsupported_value"])

    def test_omission(self):
        row = self.evaluate("sufficient", '{"values": ["Brute force"]}')
        self.assertFalse(row["exact_match"])
        self.assertEqual(row["missing_values"], ["SQLi"])
        self.assertEqual(row["false_negatives"], 1)
        self.assertEqual(row["true_positives"], 1)

    def test_addition(self):
        row = self.evaluate("sufficient", '{"values": ["Brute force", "SQLi", "Backdoor"]}')
        self.assertFalse(row["exact_match"])
        self.assertEqual(row["extra_values"], ["Backdoor"])
        self.assertEqual(row["false_positives"], 1)
        self.assertTrue(row["has_unsupported_value"])

    def test_correct_abstention(self):
        row = self.evaluate("insufficient", '{"values": []}')
        self.assertTrue(row["correct_abstention"])
        self.assertIsNone(row["exact_match"])
        self.assertFalse(row["has_unsupported_value"])

    def test_failed_abstention_is_unsupported(self):
        row = self.evaluate("insufficient", '{"values": ["Brute force"]}')
        self.assertFalse(row["correct_abstention"])
        self.assertTrue(row["has_unsupported_value"])

    def test_cross_case_intrusion_detected(self):
        row = self.evaluate("sufficient", '{"values": ["Brute force", "SQLi", "Phishing"]}')
        self.assertTrue(row["cross_case_detectable"])
        self.assertTrue(row["cross_case_intrusion"])
        self.assertEqual(row["cross_case_values_returned"], ["Phishing"])

    def test_cross_case_not_reported_when_not_detectable(self):
        row = self.evaluate("sufficient", '{"values": ["Backdoor"]}', detectable=())
        self.assertFalse(row["cross_case_detectable"])
        self.assertIsNone(row["cross_case_intrusion"])

    def test_format_error_is_kept_not_repaired(self):
        row = self.evaluate("sufficient", 'Ecco la risposta: {"values": ["SQLi"]}')
        self.assertTrue(row["format_error"])
        self.assertFalse(row["format_ok"])
        self.assertFalse(row["exact_match"])
        self.assertIsNone(row["predicted_normalized"])
        self.assertEqual(row["raw_content"], 'Ecco la risposta: {"values": ["SQLi"]}')

    def test_missing_cell_is_reported(self):
        row = self.evaluate("sufficient", None, response=False)
        self.assertEqual(row["response_status"], "missing")
        self.assertFalse(row["format_ok"])
        self.assertFalse(row["format_error"])

    def test_transport_error_is_reported(self):
        row = self.evaluate("sufficient", None, status="error")
        self.assertEqual(row["response_status"], "error")
        self.assertFalse(row["exact_match"])

    def test_stale_prompt_is_reported(self):
        row = evaluator.evaluate_cell(
            CONFIG, _request(), _oracle(), "gemma3:4b",
            _response('{"values": []}', prompt_sha256="altro"))
        self.assertEqual(row["response_status"], "stale_prompt")

    def test_one_row_per_expected_cell(self):
        requests = [_request("sufficient"), _request("insufficient")]
        oracle = [_oracle("sufficient"), _oracle("insufficient")]
        rows = evaluator.evaluate(CONFIG, requests, oracle, [], MODELS)
        self.assertEqual(len(rows), len(requests) * len(MODELS))
        self.assertEqual({row["response_status"] for row in rows}, {"missing"})

    def test_last_attempt_wins_and_attempts_are_counted(self):
        request = _request("sufficient")
        cell = common.cell_id("evaluation", "gemma3:4b", "sufficient", request["question_id"])
        responses = [
            {**_response(None, "error"), "cell_id": cell},
            {**_response('{"values": ["Brute force", "SQLi"]}'), "cell_id": cell},
        ]
        rows = evaluator.evaluate(CONFIG, [request], [_oracle()], responses, ["gemma3:4b"])
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["exact_match"])
        self.assertEqual(rows[0]["attempts"], 2)


# --------------------------------------------------------------------------
# Runner con Ollama simulato
# --------------------------------------------------------------------------

class FakeOllama:
    """Server Ollama simulato: nessuna rete, nessun modello scaricato."""

    def __init__(self, answer='{"values": []}', fail_first_cells=0, digests=None):
        self.answer = answer
        self.fail_first_cells = fail_first_cells
        self.calls = []
        self.chat_calls = 0
        self.cell_calls = 0
        self.digests = digests or {
            model["ollama_tag"]: model["ollama_digest"] for model in CONFIG["models"]
        }

    def __call__(self, url, payload=None, timeout=None, method=None):
        self.calls.append((url, payload))
        if url.endswith("/api/version"):
            return {"version": CONFIG["runtime"]["verified_version"]}
        if url.endswith("/api/tags"):
            return {"models": [
                {"model": tag, "digest": digest, "size": 1,
                 "details": {"quantization_level": "Q4_K_M"}}
                for tag, digest in self.digests.items()
            ]}
        if url.endswith("/api/ps"):
            return {"models": [{"model": payload["model"] if payload else "gemma3:4b",
                                "size": 1, "size_vram": 1}]} if False else {
                "models": [{"model": tag, "size": 10, "size_vram": 10}
                           for tag in self.digests]}
        if url.endswith("/api/chat"):
            if not payload.get("messages"):
                return {"status": "unloaded"}
            self.chat_calls += 1
            warmup = payload["messages"][-1]["content"] == runner.WARMUP_PROMPT
            if not warmup:
                self.cell_calls += 1
                if self.cell_calls <= self.fail_first_cells:
                    raise OSError("connessione rifiutata (simulata)")
            answer = self.answer(payload) if callable(self.answer) else self.answer
            return {
                "model": payload["model"],
                "message": {"role": "assistant", "content": answer},
                "done": True, "done_reason": "stop",
                "total_duration": 1_000_000_000, "load_duration": 1,
                "prompt_eval_count": 100, "prompt_eval_cached_count": 0,
                "prompt_eval_duration": 1_000_000,
                "eval_count": 10, "eval_duration": 100_000_000,
            }
        raise AssertionError(f"endpoint non previsto: {url}")


class TestRunner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.inputs = self.dir / "inputs"
        self.out = self.dir / "results"
        requests, oracle = built()
        development = [row for row in requests if row["split"] == "development"][:6]
        common.dump_jsonl(self.inputs / "development_requests.jsonl", development)
        common.dump_jsonl(
            self.inputs / "development_oracle.jsonl",
            [row for row in oracle
             if row["request_id"] in {r["request_id"] for r in development}],
        )
        self.requests = development

    def tearDown(self):
        self.tmp.cleanup()

    def run_runner(self, extra=(), transport=None):
        transport = transport or FakeOllama()
        code = runner.main(
            ["--split", "development", "--inputs-dir", str(self.inputs),
             "--out-dir", str(self.out), *extra],
            transport=transport,
        )
        return code, transport

    def responses(self):
        path = self.out / "development" / "raw_responses.jsonl"
        return common.read_jsonl(path) if path.exists() else []

    def test_dry_run_makes_no_call_and_writes_nothing(self):
        code, transport = self.run_runner(["--dry-run", "--model", "gemma3:4b"])
        self.assertEqual(code, 0)
        self.assertEqual(transport.calls, [])
        self.assertFalse((self.out / "development").exists())

    def test_dry_run_requests_have_no_expected_answers(self):
        forbidden = CONFIG["context_builder"]["forbidden_prompt_inputs"]
        selected = runner.dry_run_report(CONFIG, MODELS, self.requests, None)
        for row in selected:
            blob = json.dumps(row, ensure_ascii=False)
            for key in forbidden:
                self.assertNotIn(f'"{key}"', blob)

    def test_run_writes_one_record_per_cell(self):
        code, transport = self.run_runner(["--model", "gemma3:4b"])
        self.assertEqual(code, 0)
        rows = self.responses()
        self.assertEqual(len(rows), len(self.requests))
        self.assertEqual({row["model_tag"] for row in rows}, {"gemma3:4b"})
        self.assertEqual(len({row["cell_id"] for row in rows}), len(self.requests))
        self.assertEqual(
            transport.chat_calls,
            len(self.requests) + CONFIG["runtime"]["warmup_requests_per_model"],
        )

    def test_warmup_is_kept_out_of_results(self):
        self.run_runner(["--model", "gemma3:4b"])
        warmup = common.read_jsonl(self.out / "development" / "warmup_responses.jsonl")
        self.assertEqual(len(warmup), CONFIG["runtime"]["warmup_requests_per_model"])
        self.assertTrue(all(row["warmup"] for row in warmup))
        self.assertTrue(all(not row["warmup"] for row in self.responses()))

    def test_request_order_is_question_then_condition(self):
        self.run_runner(["--model", "gemma3:4b"])
        rows = self.responses()
        order = [(row["question_id"], row["condition"]) for row in rows]
        self.assertEqual(
            order, sorted(order, key=lambda item: (item[0], item[1] != "sufficient")))

    def test_both_models_get_the_same_prompt(self):
        self.run_runner()
        rows = self.responses()
        by_cell = {}
        for row in rows:
            by_cell.setdefault((row["question_id"], row["condition"]), set()).add(
                row["prompt_sha256"])
        self.assertTrue(all(len(hashes) == 1 for hashes in by_cell.values()))
        self.assertEqual(len(rows), len(self.requests) * len(MODELS))

    def test_errors_are_preserved_and_resume_retries_only_them(self):
        code, _ = self.run_runner(["--model", "gemma3:4b"],
                                  transport=FakeOllama(fail_first_cells=2))
        self.assertEqual(code, 1)
        first = self.responses()
        errors = [row for row in first if row["status"] == "error"]
        self.assertEqual(len(errors), 2)
        self.assertTrue(all(row["error"]["type"] == "OSError" for row in errors))

        code, transport = self.run_runner(["--model", "gemma3:4b", "--resume"])
        self.assertEqual(code, 0)
        rows = self.responses()
        # Le righe di errore restano nel file; solo quelle celle sono state rifatte.
        self.assertEqual(len(rows), len(first) + 2)
        self.assertEqual(len(errors), sum(1 for row in rows if row["status"] == "error"))
        last, _ = evaluator.last_response_per_cell(rows)
        self.assertEqual(len(last), len(self.requests))
        self.assertTrue(all(row["status"] == "ok" for row in last.values()))
        self.assertEqual(
            transport.chat_calls, 2 + CONFIG["runtime"]["warmup_requests_per_model"])

    def test_resume_does_not_duplicate_completed_cells(self):
        self.run_runner(["--model", "gemma3:4b"])
        before = len(self.responses())
        _code, transport = self.run_runner(["--model", "gemma3:4b", "--resume"])
        self.assertEqual(len(self.responses()), before)
        self.assertEqual(transport.chat_calls,
                         CONFIG["runtime"]["warmup_requests_per_model"])

    def test_non_conforming_output_is_not_repaired(self):
        transport = FakeOllama(answer="non e' JSON")
        self.run_runner(["--model", "gemma3:4b"], transport=transport)
        rows = self.responses()
        self.assertEqual(len(rows), len(self.requests))
        self.assertTrue(all(row["content"] == "non e' JSON" for row in rows))
        _code, second = self.run_runner(["--model", "gemma3:4b", "--resume"],
                                        transport=FakeOllama())
        self.assertEqual(second.chat_calls, CONFIG["runtime"]["warmup_requests_per_model"])

    def test_limit_restricts_the_number_of_cells(self):
        _code, transport = self.run_runner(["--model", "gemma3:4b", "--limit", "2"])
        self.assertEqual(len(self.responses()), 2)

    def test_wrong_digest_stops_the_run(self):
        transport = FakeOllama(digests={"gemma3:4b": "0" * 64, "llama3.2:3b": "1" * 64})
        with self.assertRaises(RuntimeError):
            self.run_runner(["--model", "gemma3:4b"], transport=transport)
        self.assertEqual(self.responses(), [])

    def test_missing_model_stops_the_run(self):
        transport = FakeOllama(digests={"llama3.2:3b": CONFIG["models"][1]["ollama_digest"]})
        with self.assertRaises(RuntimeError) as error:
            self.run_runner(["--model", "gemma3:4b"], transport=transport)
        self.assertIn("non e' installato", str(error.exception))

    def test_wrong_ollama_version_stops_the_run(self):
        class OldOllama(FakeOllama):
            def __call__(self, url, payload=None, timeout=None, method=None):
                if url.endswith("/api/version"):
                    return {"version": "0.1.0"}
                return super().__call__(url, payload, timeout, method)

        with self.assertRaises(RuntimeError):
            self.run_runner(["--model", "gemma3:4b"], transport=OldOllama())

    def test_payload_uses_schema_and_options_from_config(self):
        _code, transport = self.run_runner(["--model", "gemma3:4b", "--limit", "1"])
        chats = [payload for url, payload in transport.calls
                 if url.endswith("/api/chat") and payload.get("messages")]
        self.assertTrue(chats)
        payload = chats[-1]
        self.assertEqual(payload["options"], CONFIG["runtime"]["options"])
        self.assertEqual(payload["format"], CONFIG["prompt"]["response_schema"])
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["keep_alive"], CONFIG["runtime"]["keep_alive"])

    def test_runner_never_reads_oracle_or_case_mapping(self):
        opened = []
        real_open, real_read = Path.open, Path.read_text

        def spy_open(self, *args, **kwargs):
            opened.append(str(self))
            return real_open(self, *args, **kwargs)

        def spy_read(self, *args, **kwargs):
            opened.append(str(self))
            return real_read(self, *args, **kwargs)

        with mock.patch.object(Path, "open", spy_open), \
                mock.patch.object(Path, "read_text", spy_read):
            self.run_runner(["--model", "gemma3:4b", "--limit", "2"])

        self.assertTrue(opened)
        for path in opened:
            self.assertNotIn("oracle", path)
            self.assertNotIn("case_mapping", path)

    def test_runner_source_does_not_load_oracle(self):
        source = Path(runner.__file__).read_text(encoding="utf-8")
        for forbidden in ("load_oracle", "load_case_mapping", "_oracle.jsonl",
                          "expected_values"):
            self.assertNotIn(forbidden, source.split('"""', 2)[2])

    def test_manifest_records_the_run(self):
        self.run_runner(["--model", "gemma3:4b"])
        manifest = json.loads(
            (self.out / "development" / "run_manifest.json").read_text(encoding="utf-8"))
        run = manifest["runs"][-1]
        self.assertEqual(run["model_tag"], "gemma3:4b")
        self.assertEqual(run["completed_ok"], len(self.requests))
        self.assertEqual(run["errors"], 0)
        self.assertFalse(run["warmup_in_results"])
        self.assertIn("size_vram", run["process_snapshot"])


# --------------------------------------------------------------------------
# Riepilogo e bootstrap
# --------------------------------------------------------------------------

def _evaluation_rows(episodes=20, per_episode=4):
    """Righe di valutazione sintetiche.

    Il primo modello risponde sempre bene; il secondo sbaglia un numero di
    celle che cambia da episodio a episodio, cosi' il bootstrap per episodio ha
    qualcosa da ricampionare.
    """
    rows = []
    for episode in range(episodes):
        wrong = episode % (per_episode + 1)
        for index in range(per_episode):
            for model, correct in (("gemma3:4b", True), ("llama3.2:3b", index >= wrong)):
                rows.append({
                    "cell_id": f"c{episode}-{index}-{model}",
                    "model_tag": model, "condition": "sufficient",
                    "question_id": f"Q{episode}-{index}",
                    "episode_id": f"SC06-E{episode:03d}", "family": "variety",
                    "response_status": "ok", "format_ok": True, "format_error": False,
                    "exact_match": correct, "correct_abstention": None,
                    "true_positives": 1 if correct else 0,
                    "false_positives": 0 if correct else 1, "false_negatives": 0,
                    "has_unsupported_value": not correct,
                    "cross_case_detectable": True,
                    "cross_case_intrusion": not correct,
                    "n_expected": 1, "ollama_metrics": {"total_duration": 1_000_000_000,
                                                        "eval_count": 10,
                                                        "eval_duration": 100_000_000},
                })
    return rows


class TestSummary(unittest.TestCase):
    def test_performance_is_separated_by_model(self):
        rows = _evaluation_rows(episodes=2, per_episode=2)
        for row in rows:
            if row["model_tag"] == "gemma3:4b":
                row["ollama_metrics"] = {
                    "total_duration": 1_000_000_000,
                    "eval_count": 10,
                    "eval_duration": 100_000_000,
                }
            else:
                row["ollama_metrics"] = {
                    "total_duration": 2_000_000_000,
                    "eval_count": 10,
                    "eval_duration": 200_000_000,
                }

        entries = {row["model_tag"]: row for row in summarizer.performance(rows, MODELS)}
        expected_per_model = len(rows) // len(MODELS)
        self.assertEqual(entries["gemma3:4b"]["responses_with_timing"], expected_per_model)
        self.assertEqual(entries["llama3.2:3b"]["responses_with_timing"], expected_per_model)
        self.assertEqual(entries["gemma3:4b"]["median_total_seconds"], 1.0)
        self.assertEqual(entries["llama3.2:3b"]["median_total_seconds"], 2.0)
        self.assertEqual(entries["gemma3:4b"]["median_tokens_per_second"], 100.0)
        self.assertEqual(entries["llama3.2:3b"]["median_tokens_per_second"], 50.0)

    def test_rates_use_expected_cells_as_denominator(self):
        rows = _evaluation_rows()
        table = summarizer.rate_table(rows, MODELS)
        exact = {row["model_tag"]: row for row in table
                 if row["metric"] == "exact_match" and row["family"] == summarizer.ALL_FAMILIES}
        expected = {
            model: sum(1 for row in rows
                       if row["model_tag"] == model and row["exact_match"])
            for model in MODELS
        }
        self.assertEqual(exact["gemma3:4b"]["rate"], 1.0)
        self.assertEqual(exact["llama3.2:3b"]["numerator"], expected["llama3.2:3b"])
        self.assertEqual(exact["llama3.2:3b"]["denominator"], len(rows) // len(MODELS))
        self.assertLess(exact["llama3.2:3b"]["rate"], 1.0)

    def test_bootstrap_is_reproducible(self):
        rows = _evaluation_rows()
        first = summarizer.paired_bootstrap(rows, "exact_match", *MODELS, 500, 20260922)
        second = summarizer.paired_bootstrap(rows, "exact_match", *MODELS, 500, 20260922)
        self.assertEqual(first, second)
        other = summarizer.paired_bootstrap(rows, "exact_match", *MODELS, 500, 1)
        self.assertNotEqual(first["ci95_low_pp"], other["ci95_low_pp"])
        self.assertEqual(first["effect_pp"], other["effect_pp"])

    def test_bootstrap_resamples_episodes(self):
        rows = _evaluation_rows()
        result = summarizer.paired_bootstrap(rows, "exact_match", *MODELS, 500, 20260922)
        self.assertEqual(result["episodes_resampled"], 20)
        self.assertEqual(result["unit"], "episodio")
        self.assertFalse(result["p_values"])
        wrong = sum(1 for row in rows
                    if row["model_tag"] == "llama3.2:3b" and not row["exact_match"])
        self.assertAlmostEqual(result["effect_pp"], wrong / (len(rows) / 2) * 100, places=6)
        self.assertLess(result["ci95_low_pp"], result["effect_pp"])
        self.assertGreater(result["ci95_high_pp"], result["effect_pp"])

    def test_cross_case_denominator_is_the_detectable_subset(self):
        rows = _evaluation_rows()
        for row in rows[:10]:
            row["cross_case_detectable"] = False
            row["cross_case_intrusion"] = None
        table = summarizer.rate_table(rows, MODELS)
        entries = [row for row in table if row["metric"] == "cross_case_intrusion"
                   and row["family"] == summarizer.ALL_FAMILIES]
        self.assertEqual(sum(row["denominator"] for row in entries), len(rows) - 10)

    def test_summary_files_are_written(self):
        rows = _evaluation_rows()
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp)
            common.dump_jsonl(results / "evaluation" / "evaluations.jsonl", rows)
            code = summarizer.main(
                ["--split", "evaluation", "--results-dir", str(results), "--no-bootstrap"])
            self.assertEqual(code, 0)
            for name in ("summary.json", "summary.csv", "SINTESI.md"):
                self.assertTrue((results / "evaluation" / name).exists())
            summary = json.loads(
                (results / "evaluation" / "summary.json").read_text(encoding="utf-8"))
            self.assertFalse(summary["judge_model_used"])
            self.assertIn("Do not combine", summary["forbidden_aggregation"])

    def test_summary_does_not_change_evaluations(self):
        rows = _evaluation_rows()
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp)
            path = results / "evaluation" / "evaluations.jsonl"
            common.dump_jsonl(path, rows)
            before = path.read_bytes()
            summarizer.main(["--split", "evaluation", "--results-dir", str(results),
                             "--no-bootstrap"])
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# --------------------------------------------------------------------------
# Versione 1.1: chiarimento sulle etichette composte
# --------------------------------------------------------------------------

CONFIG_V11_PATH = REPO_ROOT / "data" / "rq3" / "config" / "rq5_sc06_v1_1.json"
CONFIG_V11 = common.load_config(CONFIG_V11_PATH)

# Frasi che la v1.1 aggiunge alle istruzioni. Il test non le riscrive: le
# cerca nel prompt e verifica che, tolte, resti esattamente il prompt v1.0.
RULE_MARKERS = (
    "punto e virgola separa etichette distinte",
    "singolo elemento dell'array",
    "conservati integralmente",
    "Non dividere, abbreviare o rimuovere parti di un'etichetta.",
)


def _dataset_values():
    return {value
            for row in common.load_case_mapping(CONFIG)
            for values in row["answerable_fields"].values()
            for value in values}


class TestVersionV11(unittest.TestCase):
    """La v1.1 chiarisce una regola di formato e non tocca nient'altro."""

    def test_config_id_and_version_block(self):
        self.assertEqual(CONFIG_V11["config_id"], "rq5-sc06-v1.1")
        self.assertEqual(CONFIG_V11["version"]["derived_from"], CONFIG["config_id"])

    def test_rule_is_present_in_the_prompt(self):
        system = CONFIG_V11["prompt"]["system"]
        for marker in RULE_MARKERS:
            self.assertIn(marker, system)
        self.assertNotIn(RULE_MARKERS[0], CONFIG["prompt"]["system"])

    def test_removing_the_rule_gives_back_the_v1_0_prompt(self):
        system = CONFIG_V11["prompt"]["system"]
        start = system.index("Nel CONTEXT il punto e virgola")
        end = system.index(RULE_MARKERS[-1]) + len(RULE_MARKERS[-1])
        stripped = (system[:start] + system[end:]).replace("  ", " ").strip()
        self.assertEqual(stripped, CONFIG["prompt"]["system"])

    def test_instructions_contain_no_dataset_value_or_example(self):
        system = CONFIG_V11["prompt"]["system"]
        for value in _dataset_values():
            pattern = r"(?<!\w)" + re.escape(value) + r"(?!\w)"
            self.assertIsNone(re.search(pattern, system),
                              f"il valore {value!r} compare nelle istruzioni")
        for row in common.load_case_mapping(CONFIG):
            self.assertNotIn(row["incident_id"], system)
        for word in ("esempio", "example", "ad esempio", "e.g."):
            self.assertNotIn(word, system.lower())

    def test_only_prompt_system_and_version_differ(self):
        allowed = {"config_id", "prompt", "version"}
        differing = {key for key in set(CONFIG) | set(CONFIG_V11)
                     if CONFIG.get(key) != CONFIG_V11.get(key)}
        self.assertEqual(differing, allowed)
        self.assertEqual(set(CONFIG_V11) - set(CONFIG), {"version"})
        prompt_diff = {key for key in set(CONFIG["prompt"]) | set(CONFIG_V11["prompt"])
                       if CONFIG["prompt"].get(key) != CONFIG_V11["prompt"].get(key)}
        self.assertEqual(prompt_diff, {"system"})

    def test_dataset_split_models_runtime_and_metrics_are_identical(self):
        for block in ("source", "split", "conditions", "context_builder", "models",
                      "runtime", "evaluation", "performance", "call_counts",
                      "execution_gates", "scope"):
            self.assertEqual(CONFIG[block], CONFIG_V11[block], block)

    def test_versions_use_separate_directories(self):
        self.assertEqual(common.version_slug(CONFIG), "v1")
        self.assertEqual(common.version_slug(CONFIG_V11), "v1_1")
        self.assertNotEqual(common.inputs_dir(CONFIG), common.inputs_dir(CONFIG_V11))
        self.assertNotEqual(common.results_dir(CONFIG), common.results_dir(CONFIG_V11))
        self.assertTrue(str(common.inputs_dir(CONFIG_V11)).endswith("sc06_rq5_v1_1"))
        self.assertTrue(str(common.results_dir(CONFIG_V11)).endswith("v1_1"))

    def test_built_requests_differ_only_by_instruction_and_hash(self):
        for split in common.SPLITS:
            v1 = {row["request_id"]: row for row in common.read_jsonl(
                common.inputs_dir(CONFIG) / f"{split}_requests.jsonl")}
            v11 = {row["request_id"]: row for row in common.read_jsonl(
                common.inputs_dir(CONFIG_V11) / f"{split}_requests.jsonl")}
            self.assertEqual(set(v1), set(v11))
            for key, first in v1.items():
                second = v11[key]
                # contesto, domanda, distrattori e ordine: identici
                self.assertEqual(first["messages"][1], second["messages"][1])
                self.assertEqual(first["context_block_order"], second["context_block_order"])
                self.assertEqual(first["context_block_fields"], second["context_block_fields"])
                self.assertEqual(first["episode_id"], second["episode_id"])
                self.assertEqual(first["condition"], second["condition"])
                # istruzione e hash: gli unici campi diversi
                self.assertNotEqual(first["messages"][0], second["messages"][0])
                self.assertNotEqual(first["prompt_sha256"], second["prompt_sha256"])
                self.assertEqual(
                    {k for k in first if first[k] != second[k]},
                    {"messages", "prompt_sha256"},
                )

    def test_oracle_is_unchanged_apart_from_the_prompt_hash(self):
        for split in common.SPLITS:
            v1 = {row["request_id"]: row for row in common.read_jsonl(
                common.inputs_dir(CONFIG) / f"{split}_oracle.jsonl")}
            v11 = {row["request_id"]: row for row in common.read_jsonl(
                common.inputs_dir(CONFIG_V11) / f"{split}_oracle.jsonl")}
            self.assertEqual(set(v1), set(v11))
            for key, first in v1.items():
                self.assertEqual(
                    {k for k in first if first[k] != v11[key][k]}, {"prompt_sha256"})

    def test_v1_0_artifacts_do_not_contain_the_new_rule(self):
        for split in common.SPLITS:
            for row in common.read_jsonl(
                    common.inputs_dir(CONFIG) / f"{split}_requests.jsonl"):
                self.assertNotIn(RULE_MARKERS[0], row["messages"][0]["content"])

    def test_both_models_still_share_the_v1_1_prompt(self):
        rows = common.read_jsonl(
            common.inputs_dir(CONFIG_V11) / "development_requests.jsonl")
        self.assertEqual(len(rows), 216)
        for row in rows:
            payloads = [common.chat_payload(CONFIG_V11, tag,
                                            row["messages"][0]["content"],
                                            row["messages"][1]["content"])
                        for tag in MODELS]
            self.assertEqual(payloads[0]["messages"], payloads[1]["messages"])
            self.assertEqual(
                common.prompt_sha256(row["messages"][0]["content"],
                                     row["messages"][1]["content"]),
                row["prompt_sha256"])

    def test_v1_1_inputs_pass_the_validator(self):
        report = validator.Report(verbose=False)
        ok = validator.validate(CONFIG_V11, common.inputs_dir(CONFIG_V11), report)
        self.assertTrue(ok, [check for check in report.failed])
