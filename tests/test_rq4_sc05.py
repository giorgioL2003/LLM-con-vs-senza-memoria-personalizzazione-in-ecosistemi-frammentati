"""Test offline di RQ4 / SC05.

Nessuna rete e nessun modello: le sorgenti SC05 del repository sono lette in
sola lettura, gli artefatti vengono scritti in una directory temporanea e
Ollama e' sostituito da un trasporto finto.

Esecuzione:
    python3 -m unittest tests.test_rq4_sc05
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq4"))

import rq4_common as common  # noqa: E402
import build_rq4_design as design_builder  # noqa: E402
import run_rq4_retrieval as retrieval_step  # noqa: E402
import build_rq4_requests as request_builder  # noqa: E402
import validate_rq4_inputs as validator  # noqa: E402
import run_rq4_ollama as runner  # noqa: E402
import evaluate_rq4 as evaluator  # noqa: E402
import summarize_rq4 as summarizer  # noqa: E402

CONFIG = common.load_config()
HANDOFF_DEPENDENT = ["SC05-Q1", "SC05-Q2", "SC05-Q4", "SC05-Q6"]
CONTROLS = ["SC05-Q3", "SC05-Q5"]
ABSENT = ["SC05-Q7"]


def build_all(out_root, config=CONFIG, config_path=common.CONFIG_PATH):
    design_builder.run(config, out_root)
    retrieval_step.run(config, out_root)
    return request_builder.run(config, out_root, config_path)


class FakeOllama:
    """Risponde a /api/version, /api/tags, /api/ps e /api/chat senza rete."""

    def __init__(self, digests=None, version="0.34.2", fail_chat=0, content='{"status": "insufficient", "answer": ""}'):
        self.digests = digests or {m["ollama_tag"]: m["ollama_digest"] for m in CONFIG["models"]}
        self.version = version
        self.fail_chat = fail_chat
        self.content = content
        self.chat_payloads = []
        self.urls = []
        self.probe = None
        self.oracle_blocked = []

    def __call__(self, url, payload=None, timeout=600, method=None):
        self.urls.append(url)
        if url.endswith("/api/version"):
            return {"version": self.version}
        if url.endswith("/api/tags"):
            return {"models": [{"model": tag, "name": tag, "digest": digest, "size": 1,
                                "details": {"quantization_level": "Q4_K_M"}} for tag, digest in self.digests.items()]}
        if url.endswith("/api/ps"):
            return {"models": []}
        if payload is not None and not payload.get("messages"):
            return {}
        self.chat_payloads.append(payload)
        if self.probe:
            try:
                common.load_oracle(*self.probe)
                self.oracle_blocked.append(False)
            except common.OracleAccessError:
                self.oracle_blocked.append(True)
        if self.fail_chat:
            self.fail_chat -= 1
            raise ConnectionError("boom")
        return {"model": payload["model"], "message": {"role": "assistant", "content": self.content},
                "done_reason": "stop", "total_duration": 1, "eval_count": 3}


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="rq4_test_")
        cls.root = Path(cls.tmp)
        cls.manifest = build_all(cls.root)
        cls.design = common.design_dir(CONFIG, cls.root)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def read(self, name):
        return common.read_jsonl(self.design / name)


# --------------------------------------------------------------------------
# Sorgenti e disegno
# --------------------------------------------------------------------------

class SourceTests(unittest.TestCase):
    def test_hashes_match_protocol(self):
        verified = common.verify_sources(CONFIG)
        self.assertEqual(verified["scenario"]["sha256"], "be57e57c4c133dda015d6c955cef59058f514e896dde9a94e50e0b85e87bc0fa")
        self.assertEqual(verified["annotations"]["sha256"], "454be8c6c7a7bc17bce349a356aa872075bf8dc27ca600d2ff0ba7d51f67e3a8")
        self.assertEqual(verified["models_reference"]["sha256"], "01662ccb0980ae24552b91942663cffe97b390ded23f74ccdd9d3946d4debc14")

    def test_wrong_hash_stops_the_build(self):
        broken = copy.deepcopy(CONFIG)
        broken["sources"]["scenario"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                design_builder.run(broken, tmp)
            self.assertFalse(any(Path(tmp).rglob("*.jsonl")))

    def test_models_equal_rq5_reference(self):
        self.assertEqual(common.models_reference_problems(CONFIG), [])
        changed = copy.deepcopy(CONFIG)
        changed["runtime"]["options"]["temperature"] = 0.7
        self.assertTrue(common.models_reference_problems(changed))

    def test_sources_read_only(self):
        before = {path: common.sha256_file(REPO_ROOT / path) for _, path, _ in common.source_entries(CONFIG)}
        with tempfile.TemporaryDirectory() as tmp:
            build_all(Path(tmp))
            written = {p.relative_to(tmp).parts[0] for p in Path(tmp).rglob("*") if p.is_file()}
        after = {path: common.sha256_file(REPO_ROOT / path) for _, path, _ in common.source_entries(CONFIG)}
        self.assertEqual(before, after)
        self.assertEqual(written, {"data"})


class DesignTests(Built):
    def test_sixteen_user_messages_nine_sessions(self):
        messages = self.read("messages.jsonl")
        self.assertEqual(len(messages), 16)
        self.assertEqual(len({m["session_id"] for m in messages}), 9)
        self.assertTrue(all(m["role"] == "user" and "-U" in m["message_id"] for m in messages))

    def test_handoff_between_s5_and_s6(self):
        messages = self.read("messages.jsonl")
        self.assertEqual({m["session_order"] for m in messages if m["phase"] == "A"}, {1, 2, 3, 4, 5})
        self.assertEqual({m["session_order"] for m in messages if m["phase"] == "B"}, {6, 7, 8, 9})
        self.assertEqual(CONFIG["scenario"]["handoff"]["after_session_order"], 5)

    def test_question_groups(self):
        questions = {q["question_id"]: q["group"] for q in self.read("questions.jsonl")}
        self.assertEqual(len(questions), 7)
        self.assertEqual(sorted(q for q, g in questions.items() if g == "handoff_dependent"), HANDOFF_DEPENDENT)
        self.assertEqual(sorted(q for q, g in questions.items() if g == "post_handoff_control"), CONTROLS)
        self.assertEqual(sorted(q for q, g in questions.items() if g == "absent_information"), ABSENT)

    def test_oracle_copies_annotation(self):
        annotation = {q["question_id"]: q for q in common.load_annotations(CONFIG)["questions"]}
        for row in self.read("oracle.jsonl"):
            source = annotation[row["question_id"]]
            self.assertEqual(row["expected_answer"], source["expected_answer"])
            self.assertEqual([f["fact_key"] for f in row["required_facts"]],
                             [f["fact_key"] for f in source["required_facts"]])
        oracle = {o["question_id"]: o for o in self.read("oracle.jsonl")}
        self.assertEqual(oracle["SC05-Q4"]["per_condition"]["separated"]["evidence_in_corpus"],
                         {"revisione-regole-aperta": True, "vincolo-rapporto": False})
        for qid in ("SC05-Q1", "SC05-Q2", "SC05-Q6"):
            self.assertEqual(oracle[qid]["per_condition"]["separated"]["expected_status_given_corpus"], "insufficient")
            self.assertEqual(oracle[qid]["per_condition"]["shared"]["expected_status_given_corpus"], "answered")
        self.assertEqual(oracle["SC05-Q7"]["per_condition"]["shared"]["expected_status_given_corpus"], "insufficient")


# --------------------------------------------------------------------------
# Retrieval
# --------------------------------------------------------------------------

class RetrievalTests(Built):
    def test_perimeters(self):
        messages = self.read("messages.jsonl")
        late = [m["message_id"] for m in messages if m["session_order"] >= 6]
        every = [m["message_id"] for m in messages]
        for row in self.read("retrieval.jsonl"):
            expected = late if row["condition"] == "separated" else every
            self.assertEqual(row["accessible_message_ids"], expected)

    def test_ranking_and_budget_deterministic(self):
        messages, questions = self.read("messages.jsonl"), self.read("questions.jsonl")
        first = retrieval_step.rank_all(CONFIG, messages, questions)
        self.assertEqual(first, retrieval_step.rank_all(CONFIG, list(reversed(messages)), questions))
        self.assertEqual(first, self.read("retrieval.jsonl"))
        for row in first:
            self.assertTrue(row["context_tokens"] <= 200 or row["budget_exceeded_by_first_item"])
            scores = {s["message_id"]: s["score"] for s in row["ranking"]}
            self.assertTrue(all(scores[m] > 0 for m in row["selected_message_ids"]))
            ranked_ids = [s["message_id"] for s in row["ranking"]]
            self.assertEqual(row["selected_message_ids"], ranked_ids[:len(row["selected_message_ids"])])

    def test_uses_rq2_functions(self):
        messages = self.read("messages.jsonl")
        items = common.message_items(CONFIG, messages)
        ranked = common.rq2_common.rank_items("server esposto", items)
        selection = common.rq2_common.select_within_budget(ranked, 200, 0.0)
        _, ours = common.retrieve(CONFIG, "server esposto", items)
        self.assertEqual([e["item_id"] for e in ours["selected"]], [e["item_id"] for e in selection["selected"]])
        self.assertEqual(items[0]["render"], "[SC05-S1-U1] " + messages[0]["content"])

    def test_ranking_never_reads_oracle(self):
        common.forbid_oracle()
        try:
            with self.assertRaises(common.OracleAccessError):
                common.load_oracle(CONFIG, self.root)
            rows = retrieval_step.rank_all(CONFIG, self.read("messages.jsonl"), self.read("questions.jsonl"))
        finally:
            common.allow_oracle()
        self.assertEqual(len(rows), 14)
        self.assertFalse({k for r in rows for k in r} & common.ORACLE_KEYS)

    def test_coverage_is_separate_and_consistent(self):
        coverage = {(c["question_id"], c["condition"]): c for c in self.read("retrieval_coverage.jsonl")}
        for qid in ("SC05-Q1", "SC05-Q2", "SC05-Q6"):
            self.assertEqual(coverage[(qid, "separated")]["facts_in_corpus"], 0)
        self.assertEqual(coverage[("SC05-Q7", "shared")]["facts_total"], 0)
        for c in coverage.values():
            self.assertLessEqual(c["facts_in_context"], c["facts_in_corpus"])


# --------------------------------------------------------------------------
# Richieste e piano
# --------------------------------------------------------------------------

class RequestTests(Built):
    def test_twenty_eight_unique_cells(self):
        cells = self.read("requests.jsonl")
        self.assertEqual(len(cells), 28)
        self.assertEqual(len({c["cell_id"] for c in cells}), 28)
        self.assertEqual(len({(c["model_tag"], c["condition"], c["question_id"]) for c in cells}), 28)

    def test_prompt_identical_across_models(self):
        by_key = {}
        for c in self.read("requests.jsonl"):
            by_key.setdefault((c["condition"], c["question_id"]), set()).add((c["system"], c["user"], c["prompt_sha256"]))
        self.assertEqual(len(by_key), 14)
        self.assertTrue(all(len(v) == 1 for v in by_key.values()))

    def test_requests_without_oracle(self):
        oracle = self.read("oracle.jsonl")
        for c in self.read("requests.jsonl"):
            self.assertFalse(set(c) & common.ORACLE_KEYS)
            for o in oracle:
                self.assertNotIn(o["expected_answer"], c["system"] + c["user"])
            self.assertTrue(all("-U" in m for m in c["context_message_ids"]))

    def test_plan_and_frozen_counts(self):
        plan = self.read("generation_plan.jsonl")
        calls = [p for p in plan if p["generation_kind"] == "model_call"]
        self.assertEqual((len(plan), len(calls)), (28, CONFIG["counts"]["model_calls"]))
        self.assertEqual(self.manifest["counts"]["model_calls_per_model"], CONFIG["counts"]["model_calls_per_model"])

    def test_reuse_only_within_same_model_and_identical_input(self):
        base = {"system": "S", "user": "U", "prompt_sha256": "p", "condition": "separated", "question_id": "Q"}
        cells = [
            dict(base, cell_id="a1", model_tag="gemma3:4b", model_config_sha256="g"),
            dict(base, cell_id="a2", model_tag="gemma3:4b", model_config_sha256="g", condition="shared"),
            dict(base, cell_id="b1", model_tag="llama3.2:3b", model_config_sha256="l"),
            dict(base, cell_id="b2", model_tag="llama3.2:3b", model_config_sha256="l2", condition="shared"),
        ]
        plan = {p["cell_id"]: p for p in common.plan_generation(CONFIG, cells)}
        self.assertEqual(plan["a2"]["generation_kind"], "reused_identical_prompt")
        self.assertEqual(plan["a2"]["reused_from_cell_id"], "a1")
        self.assertEqual(plan["b1"]["generation_kind"], "model_call")
        self.assertEqual(plan["b2"]["generation_kind"], "model_call")
        forged = [cells[0], dict(cells[1], user="diverso")]
        with self.assertRaises(ValueError):
            common.plan_generation(CONFIG, forged)

    def test_payload_uses_frozen_runtime(self):
        cell = self.read("requests.jsonl")[0]
        payload = common.chat_payload(CONFIG, cell["model_tag"], cell["system"], cell["user"])
        self.assertEqual(payload["options"], {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": 128})
        self.assertEqual(payload["format"], CONFIG["prompt"]["response_schema"])
        self.assertFalse(payload["stream"])

    def test_validator_passes_on_fixture(self):
        runner.verify_models(CONFIG, FakeOllama(), self.root)
        checks = validator.validate(CONFIG, self.root, check_git=False)
        self.assertEqual([r for r in checks.results if not r["ok"]], [])

    def test_validator_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(self.root, tmp, dirs_exist_ok=True)
            path = common.design_dir(CONFIG, tmp) / "requests.jsonl"
            rows = common.read_jsonl(path)
            rows[0]["expected_answer"] = "x"
            rows[1]["user"] += " altro"
            common.dump_jsonl(path, rows)
            failed = {r["check"] for r in validator.validate(CONFIG, tmp, check_git=False).results if not r["ok"]}
            self.assertIn("oracle.absent_from_retrieval_requests_questions", failed)
            self.assertIn("prompts.identical_across_models", failed)
            self.assertIn("build.artifacts_sha256", failed)


# --------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------

class ParserTests(unittest.TestCase):
    def test_parser(self):
        parse = lambda t: common.parse_output(t, CONFIG)  # noqa: E731
        self.assertEqual(parse('{"status": "answered", "answer": "SRV-14"}'),
                         (True, {"status": "answered", "answer": "SRV-14"}, None))
        self.assertTrue(parse(' {"status": "insufficient", "answer": ""}\n')[0])
        self.assertEqual(parse('{"status": "maybe", "answer": "x"}')[2], "status_not_allowed:'maybe'")
        self.assertEqual(parse('{"status": "answered", "answer": "x", "why": 1}')[2], "extra_keys:why")
        self.assertEqual(parse('Ecco: {"status": "answered", "answer": "x"}')[2], "not_json")
        self.assertEqual(parse('{"status": "answered", "answer": "x"} grazie')[2], "not_json")
        self.assertEqual(parse('{"status": "answered"}')[2], "missing_keys:answer")
        self.assertEqual(parse('{"status": "answered", "answer": 3}')[2], "answer_type:int")
        self.assertEqual(parse(None)[2], "no_text")


# --------------------------------------------------------------------------
# Runner, valutazione, riepilogo
# --------------------------------------------------------------------------

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rq4_runner_")
        self.root = Path(self.tmp)
        build_all(self.root)
        self.responses = common.stage_dir(CONFIG, "evaluation", self.root) / "raw_responses.jsonl"

    def tearDown(self):
        common.allow_oracle()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, args, transport):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            code = runner.main(args, transport=transport, out_root=self.root)
        return code, out.getvalue()

    def authorize(self):
        runner.verify_models(CONFIG, FakeOllama(), self.root)
        common.dump_json(runner.evaluation_gate_path(CONFIG, self.root), {
            "approved_by": "test", "approved_at": "2026-09-23",
            "config_sha256": common.sha256_file(common.CONFIG_PATH),
            "build_manifest_sha256": common.sha256_file(common.design_dir(CONFIG, self.root) / "build_manifest.json"),
        })

    def test_dry_run_offline(self):
        fake = FakeOllama()
        code, out = self.run_main(["--stage", "evaluation", "--dry-run"], fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.urls, [])
        self.assertFalse(any(common.results_dir(CONFIG, self.root).rglob("*")))
        for marker in ("SC05-Q2 — separated", "SC05-Q2 — shared", "SC05-Q4 — separated",
                       "SC05-Q4 — shared", "SC05-Q7 — separated", "SC05-Q7 — shared", "Celle: 28"):
            self.assertIn(marker, out)

    def test_verify_models_metadata_only(self):
        fake = FakeOllama()
        code, _ = self.run_main(["--verify-models"], fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.chat_payloads, [])
        self.assertTrue(all(u.endswith(("/api/version", "/api/tags")) for u in fake.urls))
        bad = FakeOllama(digests={"gemma3:4b": "x" * 64, "llama3.2:3b": CONFIG["models"][1]["ollama_digest"]})
        code, _ = self.run_main(["--verify-models"], bad)
        self.assertEqual(code, 2)
        self.assertFalse(common.read_json(runner.verification_path(CONFIG, self.root))["ok"])

    def test_gates_block_without_authorization(self):
        fake = FakeOllama()
        runner.verify_models(CONFIG, fake, self.root)
        self.assertEqual(self.run_main(["--stage", "evaluation", "--model", "gemma3:4b"], fake)[0], 2)
        self.assertEqual(self.run_main(["--stage", "smoke", "--model", "gemma3:4b"], fake)[0], 2)
        self.assertEqual(fake.chat_payloads, [])
        self.assertFalse(self.responses.exists())

    def test_evaluation_run_resume_and_no_oracle(self):
        self.authorize()
        fake = FakeOllama(fail_chat=0)
        fake.probe = (CONFIG, self.root)
        code, _ = self.run_main(["--stage", "evaluation", "--model", "gemma3:4b", "--confirm-evaluation",
                                 "--limit", "5"], fake)
        self.assertEqual(code, 0)
        warmups = [p for p in fake.chat_payloads if "status" in p["messages"][1]["content"] and "Contesto" not in p["messages"][1]["content"]]
        self.assertEqual(len(warmups), 3)
        self.assertEqual(len(fake.chat_payloads), 3 + 5)
        self.assertTrue(all(fake.oracle_blocked))
        rows = common.read_jsonl(self.responses)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r["model_tag"] == "gemma3:4b" and r["generation_kind"] == "model_call" for r in rows))
        self.assertEqual(self.run_main(["--stage", "evaluation", "--model", "gemma3:4b", "--confirm-evaluation"], fake)[0], 2)
        fake2 = FakeOllama()
        code, _ = self.run_main(["--stage", "evaluation", "--model", "gemma3:4b", "--confirm-evaluation", "--resume"], fake2)
        self.assertEqual(code, 0)
        self.assertEqual(len(fake2.chat_payloads), 3 + 9)
        self.assertEqual(len(runner.last_rows_by_cell(self.responses)), 14)

    def test_second_model_starts_without_resume_and_generation_validates(self):
        self.authorize()
        for tag in ("gemma3:4b", "llama3.2:3b"):
            code, _ = self.run_main(["--stage", "evaluation", "--model", tag, "--confirm-evaluation"], FakeOllama())
            self.assertEqual(code, 0)
        self.assertEqual(self.run_main(["--stage", "evaluation", "--model", "gemma3:4b", "--confirm-evaluation"],
                                       FakeOllama())[0], 2)
        for tag in ("gemma3:4b", "llama3.2:3b"):
            code, _ = self.run_main(["--stage", "smoke", "--model", tag, "--confirm-smoke"], FakeOllama())
            self.assertEqual(code, 0)
        self.assertEqual(len(runner.last_rows_by_cell(self.responses)), 28)
        checks = validator.validate(CONFIG, self.root, phase="generation", check_git=False)
        self.assertEqual([r for r in checks.results if not r["ok"]], [])
        rows = common.read_jsonl(self.responses)
        rows[0]["ollama_digest"] = "x"
        common.dump_jsonl(self.responses, rows)
        failed = {r["check"] for r in validator.validate(CONFIG, self.root, phase="generation", check_git=False).results
                  if not r["ok"]}
        self.assertIn("responses.evaluation", failed)

    def test_consecutive_errors_stop_and_are_kept(self):
        self.authorize()
        fake = FakeOllama(fail_chat=99)
        code, _ = self.run_main(["--stage", "evaluation", "--model", "llama3.2:3b", "--confirm-evaluation"], fake)
        self.assertEqual(code, 1)
        rows = common.read_jsonl(self.responses)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["status"] == "error" for r in rows))

    def test_missing_responses_are_kept_and_judgments_pending(self):
        self.authorize()
        self.run_main(["--stage", "evaluation", "--model", "gemma3:4b", "--confirm-evaluation", "--limit", "2"],
                      FakeOllama(content='{"status": "answered", "answer": "SRV-99"}'))
        rows = evaluator.evaluate(CONFIG, self.root)
        self.assertEqual(len(rows), 28)
        self.assertEqual(sum(r["response_status"] == "missing" for r in rows), 26)
        answered = [r for r in rows if r["response_status"] == "ok"]
        self.assertTrue(all(r["format_ok"] for r in answered))
        self.assertTrue(all(r["flags"]["unsupported_identifier_candidates"] == ["SRV-99"] for r in answered))
        self.assertTrue(all(r["judgments"]["final_class"] is None
                            and r["judgments"]["review_status"] == "proposto/in attesa di revisione" for r in rows))
        template = common.read_jsonl(common.stage_dir(CONFIG, "evaluation", self.root) / "annotation_template.jsonl")
        self.assertEqual(len(template), 28)
        summary = summarizer.run(CONFIG, self.root)
        block = summary["by_model"]["gemma3:4b"]["separated"]["handoff_dependent"]
        self.assertEqual(block["cells"], 4)
        self.assertEqual(block["human_review"]["pending"], 4)
        for name in ("summary.json", "summary.csv", "SINTESI.md"):
            self.assertTrue((common.stage_dir(CONFIG, "evaluation", self.root) / name).exists())


# --------------------------------------------------------------------------
# Artefatti reali
# --------------------------------------------------------------------------

@unittest.skipUnless((REPO_ROOT / "data/rq4/sc05_handoff_v1/build_manifest.json").exists(), "artefatti non costruiti")
class RealArtifactTests(unittest.TestCase):
    def test_real_inputs_validate(self):
        generated = any((REPO_ROOT / "results" / "rq4").rglob("raw_responses.jsonl"))
        checks = validator.validate(CONFIG, phase="generation" if generated else "design")
        self.assertEqual([r for r in checks.results if not r["ok"]], [])

    def test_saved_responses_consistent_if_present(self):
        # In fase 1 non esistono risposte; dopo la generazione devono essere coerenti.
        design = common.design_dir(CONFIG)
        for stage, name in (("smoke", "smoke_requests.jsonl"), ("evaluation", "requests.jsonl")):
            if (common.stage_dir(CONFIG, stage) / "raw_responses.jsonl").exists():
                plan = common.read_jsonl(design / "generation_plan.jsonl") if stage == "evaluation" else None
                problems = validator.check_responses(CONFIG, stage, common.read_jsonl(design / name), plan)
                self.assertEqual([p for p in problems if "mancante" not in p], [])


if __name__ == "__main__":
    unittest.main()
