"""Test offline di RQ3 / SC07.

Nessuna rete e nessun modello: le fixture sono advisory OSV sintetici scritti
in una directory temporanea, un repository git locale per l'acquisizione e un
trasporto finto per il runner.

Esecuzione:
    python3 -m unittest tests.test_rq3_sc07
"""

from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq3"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import rq3_sc07_common as common  # noqa: E402
import acquire_rq3_sc07_source as acquire  # noqa: E402
import select_rq3_sc07_advisories as selector  # noqa: E402
import build_rq3_sc07_episodes as episodes_builder  # noqa: E402
import run_rq3_sc07_retrieval as retrieval_step  # noqa: E402
import build_rq3_sc07_requests as request_builder  # noqa: E402
import validate_rq3_sc07_inputs as validator  # noqa: E402
import run_rq3_sc07_claude as runner  # noqa: E402
import evaluate_rq3_sc07 as evaluator  # noqa: E402
import summarize_rq3_sc07 as summarizer  # noqa: E402
import run_retrieval_pilot as pilot  # noqa: E402

REAL_CONFIG = common.load_config()
COMMIT = "0" * 40
GHSA_ALPHABET = "23456789cfghjmpqrvwx"
ECOSYSTEM_COUNTS = {"npm": 16, "PyPI": 16, "Maven": 16, "Go": 13, "RubyGems": 13}


def ghsa(index):
    chars = []
    for _ in range(12):
        chars.append(GHSA_ALPHABET[index % 20])
        index //= 20
    s = "".join(chars)
    return f"GHSA-{s[0:4]}-{s[4:8]}-{s[8:12]}"


def advisory(ghsa_id, ecosystem, package, severity="HIGH", introduced="0", fixed="1.2.3", **overrides):
    record = {
        "schema_version": "1.4.0",
        "id": ghsa_id,
        "modified": "2026-01-01T00:00:00Z",
        "published": "2026-01-01T00:00:00Z",
        "aliases": ["CVE-2026-12345"],
        "summary": "Path traversal in " + package,
        "details": "details",
        "severity": [],
        "affected": [{
            "package": {"ecosystem": ecosystem, "name": package},
            "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": introduced}, {"fixed": fixed}]}],
        }],
        "references": [{"type": "WEB", "url": "https://example.org"}],
        "database_specific": {"cwe_ids": ["CWE-22"], "severity": severity, "github_reviewed": True},
    }
    record.update(overrides)
    return record


def fixture_advisories():
    """(percorso nel repository, advisory) ammissibili e non ammissibili."""
    records = []
    index = 1
    for ecosystem, count in ECOSYSTEM_COUNTS.items():
        for n in range(count):
            package = f"{ecosystem.lower()}-pkg{n:02d}" if ecosystem != "Maven" else f"org.example:lib{n:02d}"
            introduced = "0" if n % 2 == 0 else f"{n}.0.0"
            record = advisory(ghsa(index), ecosystem, package, severity=["LOW", "MODERATE", "HIGH", "CRITICAL"][n % 4],
                              introduced=introduced, fixed=f"{n}.{n}.{n + 1}")
            records.append(record)
            index += 1
    # Un pacchetto ripetuto per verificare pacchetti diversi dentro l'episodio.
    records.append(advisory(ghsa(index), "npm", "npm-pkg00", fixed="9.9.9"))
    index += 1
    bad = [
        advisory(ghsa(index), "npm", "withdrawn-pkg", withdrawn="2026-01-02T00:00:00Z"),
        advisory(ghsa(index + 1), "npm", "evil-pkg", summary="Malicious Package in evil-pkg"),
        advisory(ghsa(index + 2), "npm", "nuget-pkg"),
        advisory(ghsa(index + 3), "NuGet", "nuget-pkg"),
        advisory(ghsa(index + 4), "npm", "nosev-pkg"),
        advisory(ghsa(index + 5), "npm", "lastaff-pkg"),
        advisory(ghsa(index + 6), "npm", " spaced-pkg"),
        advisory(ghsa(index + 7), "npm", "st"),
    ]
    bad[2]["affected"].append({"package": {"ecosystem": "npm", "name": "other"},
                               "ranges": bad[2]["affected"][0]["ranges"]})
    bad[4]["database_specific"]["severity"] = None
    bad[5]["affected"][0]["ranges"][0]["events"] = [{"introduced": "0"}, {"last_affected": "1.0.0"}]
    records.extend(bad)
    return [(f"advisories/github-reviewed/2026/01/{r['id']}/{r['id']}.json", r) for r in records]


def make_fixture_repo(root):
    """Snapshot, licenza, manifest e configurazione dentro `root`."""
    root = Path(root)
    config = copy.deepcopy(REAL_CONFIG)
    config["source"]["commit"] = COMMIT
    config["source"]["snapshot_filename"] = f"{COMMIT}.tar.gz"
    entries = [(p, json.dumps(r, indent=2).encode("utf-8")) for p, r in fixture_advisories()]
    entries.append(("LICENSE.md", b"Attribution 4.0 International\n"))
    snapshot = common.snapshot_path(config, root)
    sha = common.build_deterministic_tar_gz(entries, f"advisory-database-{COMMIT}", snapshot)
    config["source"]["snapshot_sha256"] = sha
    license_path = common.source_dir(config, root) / "LICENSE.md"
    license_path.write_bytes(b"Attribution 4.0 International\n")
    manifest = {
        "repository_url": config["source"]["repository_url"],
        "commit": COMMIT,
        "commit_date": "2026-01-01T00:00:00Z",
        "acquired_at": "2026-01-01T00:00:00Z",
        "subtree_git_tree": "f" * 40,
        "snapshot": {"sha256": sha, "advisory_json_files": len(entries) - 1},
        "license": {"spdx": "CC-BY-4.0", "filename": "LICENSE.md",
                    "sha256": common.sha256_file(license_path)},
    }
    common.dump_json(common.manifest_path(config, root), manifest)
    config_path = root / "config.json"
    common.dump_json(config_path, config)
    return config, config_path


def build_all(root):
    """Pipeline completa sulla fixture.

    I conteggi attesi di chiamate reali e riusi dipendono dai dati: per la
    fixture si ricavano dal piano e si scrivono nella sua configurazione, poi
    si ricostruisce il manifest con la configurazione definitiva.
    """
    config, config_path = make_fixture_repo(root)
    selector.run(config, root)
    episodes_builder.run(config, root)
    retrieval_step.run(config, root)
    manifest = request_builder.run(config, root, config_path)
    for split in common.SPLITS:
        counts = manifest["counts"][split]
        config["counts"][split].update(cells=counts["cells"], model_calls=counts["model_calls"],
                                       reused_cells=counts["reused_cells"])
    common.dump_json(config_path, config)
    request_builder.run(config, root, config_path)
    return config, config_path


class FixtureCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="rq3_sc07_test_")
        cls.root = Path(cls.tmp)
        cls.config, cls.config_path = build_all(cls.root)
        cls.design = common.design_dir(cls.config, cls.root)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def read(self, name):
        return common.read_jsonl(self.design / name)


# --------------------------------------------------------------------------
# Sorgente
# --------------------------------------------------------------------------

class SourceTests(unittest.TestCase):
    def test_deterministic_snapshot_hash(self):
        entries = [("b.json", b"{}"), ("a.json", b"[]")]
        with tempfile.TemporaryDirectory() as tmp:
            h1 = common.build_deterministic_tar_gz(entries, "root", Path(tmp) / "one.tar.gz")
            h2 = common.build_deterministic_tar_gz(list(reversed(entries)), "root", Path(tmp) / "two.tar.gz")
            h3 = common.build_deterministic_tar_gz([("a.json", b"[1]")], "root", Path(tmp) / "three.tar.gz")
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h3)

    def test_verify_snapshot_rejects_mismatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, _ = make_fixture_repo(tmp)
            common.verify_snapshot(config, tmp)
            wrong_commit = copy.deepcopy(config)
            wrong_commit["source"]["commit"] = "1" * 40
            with self.assertRaises(ValueError):
                common.verify_snapshot(wrong_commit, tmp)
            no_hash = copy.deepcopy(config)
            no_hash["source"]["snapshot_sha256"] = None
            with self.assertRaises(ValueError):
                common.verify_snapshot(no_hash, tmp)
            with common.snapshot_path(config, tmp).open("ab") as handle:
                handle.write(b"tamper")
            with self.assertRaises(ValueError):
                common.verify_snapshot(config, tmp)
            with self.assertRaises(ValueError):
                selector.run(config, tmp)

    def test_selection_refuses_missing_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, _ = make_fixture_repo(tmp)
            common.snapshot_path(config, tmp).unlink()
            with self.assertRaises(FileNotFoundError):
                selector.run(config, tmp)

    def test_acquisition_from_local_git_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            upstream = Path(tmp) / "upstream"
            for rel, record in fixture_advisories()[:3]:
                path = upstream / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(record), encoding="utf-8")
            (upstream / "advisories" / "unreviewed").mkdir(parents=True)
            (upstream / "advisories" / "unreviewed" / "x.json").write_text("{}")
            (upstream / "LICENSE.md").write_text("Attribution 4.0 International\n")
            env = ["-c", "user.name=t", "-c", "user.email=t@example.org"]
            for args in (["init", "-q"], ["add", "."], [*env, "commit", "-q", "-m", "sync"],
                         ["config", "uploadpack.allowAnySHA1InWant", "true"],
                         ["config", "uploadpack.allowFilter", "true"]):
                subprocess.run(["git", *args], cwd=upstream, check=True, capture_output=True)
            commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=upstream, check=True,
                                    capture_output=True, text=True).stdout.strip()
            config = copy.deepcopy(REAL_CONFIG)
            config["source"].update(repository_url=upstream.as_uri(), commit=commit,
                                    snapshot_filename=f"{commit}.tar.gz", snapshot_sha256=None)
            root = Path(tmp) / "repo"
            manifest = acquire.acquire(config, root)
            self.assertEqual(manifest["commit"], commit)
            self.assertEqual(manifest["snapshot"]["advisory_json_files"], 3)
            self.assertTrue(manifest["acquired_at"] and manifest["commit_date"] and manifest["subtree_git_tree"])
            self.assertEqual(manifest["license"]["spdx"], "CC-BY-4.0")
            config["source"]["snapshot_sha256"] = manifest["snapshot"]["sha256"]
            common.verify_snapshot(config, root)
            names = [p for p, _ in common.iter_snapshot_advisories(common.snapshot_path(config, root),
                                                                   "advisories/github-reviewed")]
            self.assertEqual(len(names), 3)
            # Una seconda acquisizione dello stesso commit produce lo stesso hash.
            again = acquire.acquire(config, root)
            self.assertEqual(again["snapshot"]["sha256"], manifest["snapshot"]["sha256"])

    def test_write_config_hash_only_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            path.write_text('{"source": {"snapshot_sha256": null}}')
            self.assertTrue(acquire.write_config_hash("abc", path))
            self.assertFalse(acquire.write_config_hash("abc", path))
            with self.assertRaises(ValueError):
                acquire.write_config_hash("def", path)


# --------------------------------------------------------------------------
# Ammissibilita'
# --------------------------------------------------------------------------

class EligibilityTests(unittest.TestCase):
    path = "advisories/github-reviewed/2026/01/x/x.json"

    def criterion(self, record, path=None):
        return common.check_eligibility(record, path or self.path, REAL_CONFIG)[0]

    def test_eligible(self):
        self.assertIsNone(self.criterion(advisory(ghsa(1), "npm", "left-pad")))

    def test_every_criterion(self):
        cases = {}
        rec = advisory(ghsa(1), "npm", "p")
        cases["not_github_reviewed"] = (rec, "advisories/unreviewed/x.json")
        rec = advisory(ghsa(1), "npm", "left-pad"); rec["database_specific"]["github_reviewed"] = False
        cases["not_github_reviewed/flag"] = (rec, None)
        cases["withdrawn"] = (advisory(ghsa(1), "npm", "left-pad", withdrawn="2026-01-01T00:00:00Z"), None)
        rec = advisory(ghsa(1), "npm", "left-pad"); rec["database_specific"]["cwe_ids"] = ["CWE-506"]
        cases["malware"] = (rec, None)
        cases["malware/summary"] = (advisory(ghsa(1), "npm", "x", summary="left-pad contains malware"), None)
        rec = advisory(ghsa(1), "npm", "left-pad")
        rec["affected"].append({"package": {"ecosystem": "npm", "name": "right-pad"}, "ranges": []})
        cases["not_exactly_one_package"] = (rec, None)
        cases["not_exactly_one_package/none"] = (advisory(ghsa(1), "npm", "x", affected=[]), None)
        cases["ecosystem_not_in_scope"] = (advisory(ghsa(1), "crates.io", "left-pad"), None)
        cases["severity_missing_or_not_categorical"] = (advisory(ghsa(1), "npm", "left-pad", severity=""), None)
        rec = advisory(ghsa(1), "npm", "left-pad"); rec["affected"].append(copy.deepcopy(rec["affected"][0]))
        cases["range_not_interpretable/two_entries"] = (rec, None)
        rec = advisory(ghsa(1), "npm", "left-pad")
        rec["affected"][0]["ranges"].append(copy.deepcopy(rec["affected"][0]["ranges"][0]))
        cases["range_not_interpretable/two_ranges"] = (rec, None)
        rec = advisory(ghsa(1), "npm", "left-pad"); rec["affected"][0]["ranges"][0]["type"] = "GIT"
        cases["range_not_interpretable/git"] = (rec, None)
        rec = advisory(ghsa(1), "npm", "left-pad")
        rec["affected"][0]["ranges"][0]["events"] = [{"introduced": "0"}]
        cases["range_not_interpretable/no_fixed"] = (rec, None)
        rec = advisory(ghsa(1), "npm", "left-pad")
        rec["affected"][0]["ranges"][0]["events"] = [{"introduced": "0"}, {"last_affected": "1.0"}]
        cases["range_not_interpretable/last_affected"] = (rec, None)
        rec = advisory(ghsa(1), "npm", "left-pad")
        rec["affected"][0]["ranges"][0]["events"] = [{"introduced": "0"}, {"fixed": "1"}, {"fixed": "2"}]
        cases["range_not_interpretable/two_fixed"] = (rec, None)
        cases["range_not_interpretable/equal"] = (advisory(ghsa(1), "npm", "left-pad", introduced="1.0", fixed="1.0"), None)
        cases["message_value_not_usable/space"] = (advisory(ghsa(1), "npm", "left-pad", fixed=" 1.0"), None)
        cases["message_value_not_usable/empty"] = (advisory(ghsa(1), "npm", "left-pad", fixed=""), None)
        cases["message_value_not_usable/newline"] = (advisory(ghsa(1), "npm", "left\npad"), None)
        cases["message_value_not_usable/type"] = (advisory(ghsa(1), "npm", "left-pad", fixed=3), None)
        cases["expected_value_not_unique_in_target_messages"] = (advisory(ghsa(1), "npm", "st"), None)
        for label, (record, path) in cases.items():
            with self.subTest(label):
                self.assertEqual(self.criterion(record, path), label.split("/")[0])

    def test_first_failing_criterion_wins(self):
        rec = advisory(ghsa(1), "crates.io", "x", withdrawn="2026-01-01T00:00:00Z")
        self.assertEqual(self.criterion(rec), "withdrawn")

    def test_range_rendering(self):
        self.assertEqual(common.render_range(REAL_CONFIG, "0", "1.2.3"), "< 1.2.3")
        self.assertEqual(common.render_range(REAL_CONFIG, "1.0.0", "1.2.3"), ">= 1.0.0, < 1.2.3")

    def test_audit_records_first_criterion_for_each_exclusion(self):
        entries = [(p, json.dumps(r).encode()) for p, r in fixture_advisories()]
        candidates, exclusions = selector.audit(REAL_CONFIG, entries)
        reasons = {row["criterion"] for row in exclusions}
        self.assertEqual(reasons, {"withdrawn", "malware", "not_exactly_one_package", "ecosystem_not_in_scope",
                                   "severity_missing_or_not_categorical", "range_not_interpretable",
                                   "message_value_not_usable", "expected_value_not_unique_in_target_messages"})
        self.assertEqual(len(candidates) + len(exclusions), len(entries))


# --------------------------------------------------------------------------
# Selezione
# --------------------------------------------------------------------------

class SelectionTests(FixtureCase):
    def test_counts_and_uniqueness(self):
        selection = self.read("selection.jsonl")
        dev = [r for r in selection if r["split"] == "development"]
        ev = [r for r in selection if r["split"] == "evaluation"]
        self.assertEqual((len(dev), len({r["episode_id"] for r in dev})), (9, 3))
        self.assertEqual((len(ev), len({r["episode_id"] for r in ev})), (60, 20))
        self.assertEqual(len({r["ghsa_id"] for r in selection}), 69)
        per_eco = {}
        for r in ev:
            per_eco.setdefault(r["ecosystem"], set()).add(r["episode_id"])
        self.assertEqual({e: len(s) for e, s in per_eco.items()},
                         {e: 4 for e in REAL_CONFIG["eligibility"]["ecosystems"]})

    def test_packages_distinct_within_episode(self):
        selection = self.read("selection.jsonl")
        for ep in {r["episode_id"] for r in selection}:
            rows = [r for r in selection if r["episode_id"] == ep]
            self.assertEqual(len({r["package"].casefold() for r in rows}), 3)
            self.assertEqual(len({r["ecosystem"] for r in rows}), 1)
            self.assertEqual([r["activity"] for r in sorted(rows, key=lambda r: r["position"])],
                             ["triage", "impact", "fix"])

    def test_reproducible_and_order_independent(self):
        candidates = self.read("candidates.jsonl")
        first = common.select_episodes(candidates, self.config)
        second = common.select_episodes(list(reversed(candidates)), self.config)
        self.assertEqual(first, second)
        self.assertEqual(first, self.read("selection.jsonl"))

    def test_seed_changes_ranking(self):
        other = copy.deepcopy(self.config)
        other["selection"]["seed"] = "1"
        candidates = [dict(r, rank_key=common.rank_key("1", r["ecosystem"], r["ghsa_id"]))
                      for r in self.read("candidates.jsonl")]
        self.assertNotEqual(
            [r["ghsa_id"] for r in common.select_episodes(candidates, other)],
            [r["ghsa_id"] for r in self.read("selection.jsonl")])

    def test_rank_key(self):
        self.assertEqual(common.rank_key("20260923", "npm", "GHSA-aaaa-bbbb-cccc"),
                         common.sha256_text("20260923:npm:GHSA-aaaa-bbbb-cccc"))

    def test_insufficient_stratum_stops(self):
        candidates = self.read("candidates.jsonl")
        ruby = [r for r in candidates if r["ecosystem"] == "RubyGems"]
        reduced = [r for r in candidates if r["ecosystem"] != "RubyGems"] + ruby[:11]
        with self.assertRaises(common.InsufficientStratum):
            common.select_episodes(reduced, self.config)


# --------------------------------------------------------------------------
# Conversazioni, domande, oracle
# --------------------------------------------------------------------------

class EpisodeTests(FixtureCase):
    def test_structure_and_interleaving(self):
        episodes = self.read("episodes.jsonl")
        self.assertEqual(len(episodes), 23)
        for episode in episodes:
            self.assertEqual([(m["activity"], m["activity_turn"]) for m in episode["messages"]],
                             [("triage", 1), ("impact", 1), ("fix", 1), ("triage", 2), ("impact", 2), ("fix", 2)])
            self.assertTrue(all(m["role"] == "user" for m in episode["messages"]))
            self.assertEqual({m["activity"] for m in episode["messages"]}, {"triage", "impact", "fix"})

    def test_six_questions_per_episode_without_answers(self):
        questions = self.read("questions.jsonl")
        self.assertEqual(len(questions), 138)
        for q in questions:
            self.assertFalse(set(q) & common.ORACLE_KEYS)

    def test_expected_value_in_exactly_one_target_message(self):
        episodes = {e["episode_id"]: e for e in self.read("episodes.jsonl")}
        for split in common.SPLITS:
            for row in common.load_oracle(self.config, split, self.root):
                target = [m for m in episodes[row["episode_id"]]["messages"] if m["activity"] == row["activity"]]
                containing = [m["message_id"] for m in target if row["expected_value"] in m["content"]]
                self.assertEqual(containing, [row["evidence_message_id"]])

    def test_oracle_provenance_and_separation(self):
        oracle = common.load_oracle(self.config, "evaluation", self.root)
        self.assertEqual(len(oracle), 120)
        for row in oracle:
            self.assertTrue(row["provenance"]["ghsa_id"].startswith("GHSA-"))
            self.assertTrue(row["provenance"]["osv_fields"])
        text = (self.design / "episodes.jsonl").read_text() + (self.design / "questions.jsonl").read_text()
        self.assertIsNone(common.GHSA_RE.search(text))
        self.assertNotIn("CVE-", text)

    def test_splits_disjoint(self):
        selection = self.read("selection.jsonl")
        dev = {r["ghsa_id"] for r in selection if r["split"] == "development"}
        ev = {r["ghsa_id"] for r in selection if r["split"] == "evaluation"}
        self.assertFalse(dev & ev)
        questions = self.read("questions.jsonl")
        self.assertFalse({q["episode_id"] for q in questions if q["split"] == "development"}
                         & {q["episode_id"] for q in questions if q["split"] == "evaluation"})


# --------------------------------------------------------------------------
# Retrieval
# --------------------------------------------------------------------------

class RetrievalTests(FixtureCase):
    def rows(self, split="evaluation"):
        return common.read_jsonl(common.results_dir(self.config, split, self.root) / "retrieval.jsonl")

    def test_corpus_per_condition(self):
        episodes = {e["episode_id"]: e for e in self.read("episodes.jsonl")}
        for row in self.rows():
            messages = episodes[row["episode_id"]]["messages"]
            target = [m["message_id"] for m in messages if m["activity"] == row["activity"]]
            if row["condition"] == "separated":
                self.assertEqual(row["accessible_message_ids"], target)
            else:
                self.assertEqual(len(row["accessible_message_ids"]), 6)
                self.assertTrue(set(target) <= set(row["accessible_message_ids"]))
                distractors = set(row["accessible_message_ids"]) - set(target)
                self.assertEqual(len(distractors), 4)
            self.assertEqual(len(row["retrieved_message_ids"]), 2)
            self.assertEqual(row["top_k"], 2)

    def test_uses_pilot_retriever(self):
        corpus = [{"message_id": f"m{i}", "session_order": 1, "message_order": i, "content": text}
                  for i, text in enumerate(["alpha beta", "beta gamma", "gamma delta"], 1)]
        full, top = common.rank_corpus("beta", corpus, 2)
        self.assertEqual([d["message_id"] for d in top],
                         [d["message_id"] for d in pilot.retrieve("beta", corpus, top_k=2)])
        self.assertEqual(len(full), 3)

    def test_deterministic_tie_break_by_message_order(self):
        corpus = [{"message_id": f"m{i}", "session_order": 1, "message_order": i, "content": "same text"}
                  for i in (3, 1, 2)]
        _, top = common.rank_corpus("unrelated", corpus, 2)
        self.assertEqual([d["message_id"] for d in top], ["m1", "m2"])

    def test_ranking_never_reads_oracle(self):
        episodes = [e for e in self.read("episodes.jsonl") if e["split"] == "development"]
        questions = [q for q in self.read("questions.jsonl") if q["split"] == "development"]
        common.forbid_oracle()
        try:
            with self.assertRaises(common.OracleAccessError):
                common.load_oracle(self.config, "development", self.root)
            rows = retrieval_step.rank_all(self.config, episodes, questions)
        finally:
            common.allow_oracle()
        self.assertEqual(len(rows), 36)
        self.assertFalse(any("evidence_message_id" in r for r in rows))


# --------------------------------------------------------------------------
# Richieste e validatore
# --------------------------------------------------------------------------

class RequestTests(FixtureCase):
    def test_counts(self):
        self.assertEqual(len(common.read_jsonl(common.requests_path(self.config, "development", self.root))), 36)
        self.assertEqual(len(common.read_jsonl(common.requests_path(self.config, "evaluation", self.root))), 240)

    def test_prompt_has_no_source_or_oracle(self):
        oracle = {o["question_id"]: o for o in common.load_oracle(self.config, "evaluation", self.root)}
        for r in common.read_jsonl(common.requests_path(self.config, "evaluation", self.root)):
            self.assertEqual(common.prompt_leaks(r["system"] + r["user"]), [])
            self.assertFalse(set(r) & common.ORACLE_KEYS)
            self.assertNotIn(oracle[r["question_id"]]["expected_value"], r["system"] + r["question"])

    def test_leak_detector(self):
        self.assertIn("ghsa_id", common.prompt_leaks("see GHSA-x5mm-wm4g-j5xv"))
        self.assertIn("cve_id", common.prompt_leaks("CVE-2026-1234"))
        self.assertIn("https://", common.prompt_leaks("https://example.org"))
        self.assertEqual(common.prompt_leaks("github.com/rclone/rclone < 1.2"), [])

    def test_conditions_share_model_prompt_and_parameters(self):
        requests = common.read_jsonl(common.requests_path(self.config, "evaluation", self.root))
        by_q = {}
        for r in requests:
            by_q.setdefault(r["question_id"], {})[r["condition"]] = r
        for pair in by_q.values():
            a, b = pair["separated"], pair["shared_interleaved"]
            self.assertEqual((a["system"], a["question"]), (b["system"], b["question"]))
            ia, ib = common.cli_input(self.config, a), common.cli_input(self.config, b)
            self.assertEqual(ia.split("\n\nQUESTION\n")[1], ib.split("\n\nQUESTION\n")[1])
            self.assertEqual(ia == ib, a["context"] == b["context"])
        plan = common.read_jsonl(common.call_plan_path(self.config, "evaluation", self.root))
        self.assertEqual({p["model_config_sha256"] for p in plan}, {common.model_config_sha256(self.config)})

    def test_call_plan_reuses_only_identical_prompts(self):
        for split in common.SPLITS:
            requests = common.read_jsonl(common.requests_path(self.config, split, self.root))
            plan = common.read_jsonl(common.call_plan_path(self.config, split, self.root))
            by_id = {r["request_id"]: r for r in requests}
            calls = [p for p in plan if p["generation_kind"] == "model_call"]
            self.assertEqual(len(plan), len(requests))
            self.assertEqual(len(calls), len({r["prompt_sha256"] for r in requests}))
            for p in plan:
                if p["generation_kind"] == "reused_identical_prompt":
                    src, own = by_id[p["reused_from_request_id"]], by_id[p["request_id"]]
                    self.assertEqual((src["system"], src["user"]), (own["system"], own["user"]))
                    self.assertEqual((src["condition"], own["condition"]), ("separated", "shared_interleaved"))
            self.assertEqual(common.plan_calls(self.config, requests), plan)

    def test_plan_rejects_hash_collision_with_different_text(self):
        requests = common.read_jsonl(common.requests_path(self.config, "development", self.root))
        pair = [r for r in requests if r["question_id"] == requests[0]["question_id"]]
        forged = [dict(pair[0]), dict(pair[1], user=pair[1]["user"] + " ", prompt_sha256=pair[0]["prompt_sha256"])]
        with self.assertRaises(ValueError):
            common.plan_calls(self.config, forged)
        disabled = copy.deepcopy(self.config)
        disabled["generation"]["reuse_identical_prompts"]["enabled"] = False
        plan = common.plan_calls(disabled, requests)
        self.assertTrue(all(p["generation_kind"] == "model_call" for p in plan))

    def test_validator_passes_on_fixture(self):
        checks = validator.validate(self.config, self.root, self.config_path, check_git=False)
        failed = [r for r in checks.results if not r["ok"]]
        self.assertEqual(failed, [])

    def test_validator_detects_injected_leak(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(self.root, tmp, dirs_exist_ok=True)
            path = common.requests_path(self.config, "development", tmp)
            rows = common.read_jsonl(path)
            rows[0]["user"] += "\nGHSA-x5mm-wm4g-j5xv"
            rows[1]["expected_value"] = "x"
            common.dump_jsonl(path, rows)
            checks = validator.validate(self.config, tmp, Path(tmp) / "config.json", check_git=False)
            failed = {r["check"] for r in checks.results if not r["ok"]}
            self.assertIn("requests.development.prompt_without_source", failed)
            self.assertIn("requests.development.no_oracle_keys", failed)
            self.assertIn("build.artifacts_sha256", failed)


# --------------------------------------------------------------------------
# Parser e metriche
# --------------------------------------------------------------------------

class ParserTests(unittest.TestCase):
    def test_parser(self):
        self.assertEqual(common.parse_model_output('{"value": "lodash"}'), (True, "lodash", None))
        self.assertEqual(common.parse_model_output(' {"value": null} \n'), (True, None, None))
        self.assertEqual(common.parse_model_output('{"value": "a"'), (False, None, "not_json"))
        self.assertEqual(common.parse_model_output('{"value": "a", "why": "x"}'), (False, None, "extra_keys:why"))
        self.assertEqual(common.parse_model_output('{"answer": "a"}'), (False, None, "missing_value_key"))
        self.assertEqual(common.parse_model_output('{"value": 3}'), (False, None, "value_type:int"))
        self.assertEqual(common.parse_model_output('["a"]'), (False, None, "not_json_object"))
        self.assertEqual(common.parse_model_output('```json\n{"value": "a"}\n```')[2], "not_json")
        self.assertEqual(common.parse_model_output(""), (False, None, "empty_text"))
        self.assertEqual(common.parse_model_output(None), (False, None, "no_text"))

    def test_normalization(self):
        self.assertEqual(common.normalize_value("  café ", REAL_CONFIG), "café")
        self.assertNotEqual(common.normalize_value("Lodash", REAL_CONFIG), "lodash")


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.request = {"request_id": "r", "split": "evaluation", "condition": "shared_interleaved",
                        "question_id": "Q1", "episode_id": "E", "question_type": "triage.package",
                        "activity": "triage",
                        "context": "[1] il pacchetto coinvolto è left-pad\n[2] il pacchetto coinvolto è right-pad"}
        self.retrieval = {"evidence_message_id": "M1", "retrieved_message_ids": ["M1", "M2"],
                          "evidence_reachable": True, "retrieval_success": True,
                          "contamination_count": 1, "contamination_rate": 0.5}
        self.oracle = {"expected_value": "left-pad", "ecosystem": "npm"}
        self.facts = {("triage", "package"): "left-pad", ("impact", "package"): "right-pad",
                      ("fix", "package"): "up-pad", ("triage", "severity"): "HIGH"}

    def cell(self, text, status="ok", retrieval=None):
        response = None if status is None else {"cell_id": "c", "status": status, "response_text": text}
        return evaluator.evaluate_cell(REAL_CONFIG, self.request, retrieval or self.retrieval,
                                       self.oracle, self.facts, response)

    def test_exact_match_and_support(self):
        row = self.cell('{"value": " left-pad "}')
        self.assertTrue(row["exact_match"])
        self.assertTrue(row["supported"])
        self.assertIsNone(row["error_category"])
        self.assertFalse(self.cell('{"value": "Left-pad"}')["exact_match"])

    def test_cross_activity_confusion(self):
        row = self.cell('{"value": "right-pad"}')
        self.assertFalse(row["exact_match"])
        self.assertTrue(row["supported"])
        self.assertTrue(row["cross_activity_confusion"])
        self.assertEqual(row["confused_with"], ["impact.package"])
        self.assertEqual(row["error_category"], "generation")
        unsupported = self.cell('{"value": "invented"}')
        self.assertFalse(unsupported["supported"])
        self.assertFalse(unsupported["cross_activity_confusion"])

    def test_null_format_missing_and_retrieval_errors(self):
        null = self.cell('{"value": null}')
        self.assertTrue(null["null_despite_evidence"])
        self.assertEqual(null["error_category"], "generation")
        self.assertEqual(self.cell("not json")["error_category"], "format")
        self.assertEqual(self.cell(None, status="error")["error_category"], "missing_response")
        self.assertEqual(self.cell(None, status=None)["error_category"], "missing_response")
        failed = dict(self.retrieval, retrieval_success=False)
        self.assertEqual(self.cell('{"value": "right-pad"}', retrieval=failed)["error_category"], "retrieval")
        unreachable = dict(failed, evidence_reachable=False)
        self.assertEqual(self.cell('{"value": null}', retrieval=unreachable)["error_category"], "evidence_unreachable")

    def test_contamination_summary(self):
        rows = [{"contamination_count": 1, "retrieved_messages": 2}, {"contamination_count": 0, "retrieved_messages": 2}]
        self.assertEqual(summarizer.contamination(rows)["rate"], 0.25)


# --------------------------------------------------------------------------
# Runner, valutazione, riepilogo
# --------------------------------------------------------------------------

class FakeTransport:
    """Sostituisce `claude`: risponde `{"value": null}`; errori a richiesta."""

    command = ["claude", "--print", "(test)"]

    def __init__(self, fail_on=(), probe_oracle=None, model_used="claude-sonnet-5"):
        self.fail_on = set(fail_on)
        self.calls = []
        self.probe_oracle = probe_oracle
        self.oracle_blocked = []
        self.model_used = model_used

    def __call__(self, text):
        self.calls.append(text)
        if self.probe_oracle:
            try:
                common.load_oracle(*self.probe_oracle)
                self.oracle_blocked.append(False)
            except common.OracleAccessError:
                self.oracle_blocked.append(True)
        if any(marker in text for marker in self.fail_on):
            return {"error": "claude uscito con codice 1: boom", "answer": None, "model_used": None,
                    "stdout": "", "stderr": "boom", "returncode": 1}
        return {"error": None, "answer": '{"value": null}', "model_used": self.model_used,
                "stdout": '{"type": "result", "is_error": false, "result": "{\\"value\\": null}"}',
                "stderr": "", "returncode": 0}


class Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def stream(model, result, is_error=False):
    events = [
        {"type": "system", "subtype": "init", "model": model},
        {"type": "assistant", "message": {"model": model, "content": [{"type": "text", "text": result}]}},
        {"type": "result", "is_error": is_error, "result": result, "usage": {"input_tokens": 10}},
    ]
    return "\n".join(json.dumps(e) for e in events) + "\n"


class CliTransportTests(unittest.TestCase):
    def test_same_mechanism_as_run_generation(self):
        command = common.cli_command(REAL_CONFIG)
        self.assertEqual(command, common.pilot_generation.build_command("claude-sonnet-5", "medium"))
        self.assertNotIn("--fallback-model", command)
        for flag in ("--print", "--no-session-persistence", "--strict-mcp-config"):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(REAL_CONFIG["model"]["access_channel"], "Claude Code CLI")
        self.assertEqual(runner.model_gate_problems(REAL_CONFIG), [])

    def test_transport_stdin_empty_cwd_and_model_used(self):
        seen = {}

        def fake_run(command, **kwargs):
            seen.update(command=command, **kwargs)
            return Completed(stdout=stream("claude-sonnet-5", '{"value": "left-pad"}'))

        with tempfile.TemporaryDirectory() as cwd:
            call = runner.make_cli_transport(REAL_CONFIG, cwd, runner=fake_run)
            outcome = call("PROMPT")
            self.assertEqual(seen["command"], common.cli_command(REAL_CONFIG))
            self.assertEqual(seen["input"], "PROMPT")
            self.assertEqual(seen["cwd"], cwd)
            self.assertEqual(seen["timeout"], 300)
            self.assertEqual(outcome["answer"], '{"value": "left-pad"}')
            self.assertEqual(outcome["model_used"], "claude-sonnet-5")
            self.assertIsNone(outcome["error"])
            (Path(cwd) / "stray.txt").write_text("x")
            seen.clear()
            self.assertIn("non vuota", call("PROMPT")["error"])
            self.assertEqual(seen, {})

    def test_transport_errors(self):
        with tempfile.TemporaryDirectory() as cwd:
            failed = runner.make_cli_transport(REAL_CONFIG, cwd, runner=lambda c, **k: Completed(1, "", "Not logged in"))
            self.assertIn("Not logged in", failed("x")["error"])
            reported = runner.make_cli_transport(
                REAL_CONFIG, cwd, runner=lambda c, **k: Completed(stdout=stream("claude-sonnet-5", "boom", True)))
            self.assertIn("errore riportato", reported("x")["error"])

            def timeout(command, **kwargs):
                raise subprocess.TimeoutExpired(command, 300)

            self.assertIn("timeout", runner.make_cli_transport(REAL_CONFIG, cwd, runner=timeout)("x")["error"])

    def test_config_without_cli_or_with_fallback_is_blocked(self):
        config = copy.deepcopy(REAL_CONFIG)
        config["model"]["access_channel"] = "Anthropic API"
        config["model"]["fallback_model"] = "claude-sonnet-4-6"
        problems = runner.model_gate_problems(config)
        self.assertTrue(any("access_channel" in p for p in problems))
        self.assertTrue(any("fallback" in p for p in problems))


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="rq3_sc07_runner_")
        self.root = Path(self.tmp)
        self.config, self.config_path = build_all(self.root)
        self.responses = common.results_dir(self.config, "development", self.root) / "raw_responses.jsonl"
        self.plan = common.read_jsonl(common.call_plan_path(self.config, "development", self.root))
        self.requests = {r["request_id"]: r for r in
                         common.read_jsonl(common.requests_path(self.config, "development", self.root))}
        self.n_calls = sum(1 for p in self.plan if p["generation_kind"] == "model_call")

    def tearDown(self):
        common.allow_oracle()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, args, transport):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return runner.main(args, transport=transport, repo_root=self.root, config_path=self.config_path)

    def test_fixture_has_reuse(self):
        self.assertLess(self.n_calls, len(self.plan))

    def test_dry_run_writes_nothing_and_calls_nothing(self):
        transport = FakeTransport()
        self.assertEqual(self.run_main(["--split", "development", "--dry-run"], transport), 0)
        self.assertEqual(transport.calls, [])
        self.assertFalse(self.responses.exists())

    def test_model_gate_blocks_real_calls(self):
        unconfirmed = copy.deepcopy(self.config)
        unconfirmed["model"]["registration_confirmed"] = False
        common.dump_json(self.config_path, unconfirmed)
        transport = FakeTransport()
        self.assertEqual(self.run_main(["--split", "development"], transport), 2)
        self.assertEqual(transport.calls, [])

    def test_changed_model_configuration_is_refused(self):
        changed = copy.deepcopy(self.config)
        changed["generation"]["parameters"]["effort"] = "high"
        common.dump_json(self.config_path, changed)
        with self.assertRaises(runner.GateError):
            self.run_main(["--split", "development"], FakeTransport())

    def test_runner_never_reads_oracle(self):
        for split in common.SPLITS:
            common.oracle_path(self.config, split, self.root).unlink()
        transport = FakeTransport(probe_oracle=(self.config, "development", self.root))
        self.assertEqual(self.run_main(["--split", "development", "--limit", "2"], transport), 0)
        self.assertEqual(transport.oracle_blocked, [True, True])
        self.assertEqual(sum(1 for r in common.read_jsonl(self.responses) if r["model_call"]), 2)

    def test_one_call_per_identical_prompt_and_reuse_fields(self):
        transport = FakeTransport()
        self.assertEqual(self.run_main(["--split", "development"], transport), 0)
        self.assertEqual(len(transport.calls), self.n_calls)
        self.assertEqual(len(set(transport.calls)), self.n_calls)
        rows = common.read_jsonl(self.responses)
        self.assertEqual(len(rows), len(self.plan))
        by_cell = {r["cell_id"]: r for r in rows}
        reused = [r for r in rows if r["generation_kind"] == "reused_identical_prompt"]
        self.assertEqual(len(reused), len(self.plan) - self.n_calls)
        for r in reused:
            source = by_cell[r["reused_from_cell_id"]]
            self.assertFalse(r["model_call"])
            self.assertEqual(source["generation_kind"], "model_call")
            self.assertEqual((r["prompt_sha256"], r["model_config_sha256"], r["cli_input_sha256"]),
                             (source["prompt_sha256"], source["model_config_sha256"], source["cli_input_sha256"]))
            self.assertEqual((r["response_text"], r["model_used"]), (source["response_text"], source["model_used"]))
            self.assertEqual(r["condition"], "shared_interleaved")
        self.assertEqual(validator.check_responses(self.config, "development", self.root), [])
        run = common.read_json(self.responses.parent / "run_manifest.json")["runs"][-1]
        self.assertEqual(run["counts"]["model_calls_ok"], self.n_calls)
        self.assertEqual(run["counts"]["reused_cells_written"], len(reused))
        self.assertEqual(run["models_used"], ["claude-sonnet-5"])
        evaluations = evaluator.evaluate(self.config, "development", self.root)
        self.assertEqual(len(evaluations), len(self.plan))
        self.assertEqual(sum(1 for e in evaluations if e["generation_kind"] == "reused_identical_prompt"),
                         len(reused))
        summary = summarizer.summarize(self.config, evaluations, "development")
        self.assertEqual(summary["generation"]["model_calls"], self.n_calls)

    def test_reuse_rejected_for_different_prompt(self):
        entries = [p for p in self.plan if p["generation_kind"] == "model_call"]
        a, b = self.requests[entries[0]["request_id"]], self.requests[entries[1]["request_id"]]
        source_row = runner.run_model_call(self.config, a, entries[0], FakeTransport(), "r")
        with self.assertRaises(ValueError):
            runner.reuse_row(self.config, b, entries[1], a, source_row, "r")
        reused = next(p for p in self.plan if p["generation_kind"] == "reused_identical_prompt")
        src_entry = next(p for p in self.plan if p["request_id"] == reused["reused_from_request_id"])
        source_row = runner.run_model_call(self.config, self.requests[src_entry["request_id"]], src_entry,
                                           FakeTransport(), "r")
        other = dict(source_row, model_config_sha256="different")
        with self.assertRaises(ValueError):
            runner.reuse_row(self.config, self.requests[reused["request_id"]], reused,
                             self.requests[src_entry["request_id"]], other, "r")

    def test_validator_detects_inconsistent_reuse(self):
        self.run_main(["--split", "development"], FakeTransport())
        rows = common.read_jsonl(self.responses)
        index = next(i for i, r in enumerate(rows) if r["generation_kind"] == "reused_identical_prompt")
        rows[index]["response_text"] = '{"value": "altro"}'
        call_index = next(i for i, r in enumerate(rows)
                          if r["generation_kind"] == "model_call" and r["condition"] == "separated"
                          and r["cell_id"] != rows[index]["reused_from_cell_id"])
        rows[call_index]["generation_kind"] = "reused_identical_prompt"
        common.dump_jsonl(self.responses, rows)
        problems = validator.check_responses(self.config, "development", self.root)
        self.assertTrue(any("diversi dalla sorgente" in p for p in problems))
        self.assertTrue(any("generation_kind" in p for p in problems))

    def test_model_used_is_recorded_even_if_different(self):
        self.run_main(["--split", "development", "--limit", "1"], FakeTransport(model_used="claude-other"))
        row = common.read_jsonl(self.responses)[0]
        self.assertEqual(row["model_used"], "claude-other")
        self.assertFalse(row["model_used_matches_requested"])

    def test_resume_without_duplicates_keeps_errors(self):
        first = self.requests[self.plan[0]["request_id"]]
        marker = first["question"]
        failed_calls = {p["request_id"] for p in self.plan if p["generation_kind"] == "model_call"
                        and marker in common.cli_input(self.config, self.requests[p["request_id"]])}
        blocked_reuse = [p for p in self.plan if p["reused_from_request_id"] in failed_calls]
        self.assertTrue(failed_calls and blocked_reuse)
        failing = FakeTransport(fail_on=[marker])
        self.assertEqual(self.run_main(["--split", "development", "--max-consecutive-errors", "99"], failing), 0)
        self.assertEqual(len(failing.calls), self.n_calls)
        rows = common.read_jsonl(self.responses)
        self.assertEqual(len(rows), len(self.plan) - len(blocked_reuse))
        self.assertEqual(sum(1 for r in rows if r["status"] == "error"), len(failed_calls))
        # Senza --resume il runner rifiuta di ripartire.
        self.assertEqual(self.run_main(["--split", "development"], FakeTransport()), 2)
        healthy = FakeTransport()
        self.assertEqual(self.run_main(["--split", "development", "--resume"], healthy), 0)
        self.assertEqual(len(healthy.calls), len(failed_calls))
        rows = common.read_jsonl(self.responses)
        self.assertEqual(len(rows), len(self.plan) + len(failed_calls))
        self.assertEqual(sum(1 for r in rows if r["status"] == "error"), len(failed_calls))
        last = runner.last_rows_by_cell(self.responses)
        self.assertEqual(len(last), len(self.plan))
        self.assertTrue(all(r["status"] == "ok" for r in last.values()))
        again = FakeTransport()
        self.assertEqual(self.run_main(["--split", "development", "--resume"], again), 0)
        self.assertEqual(again.calls, [])
        self.assertEqual(len(common.read_jsonl(self.responses)), len(self.plan) + len(failed_calls))
        self.assertEqual(len(common.read_json(self.responses.parent / "run_manifest.json")["runs"]), 3)
        self.assertEqual(validator.check_responses(self.config, "development", self.root), [])

    def test_interruption_between_call_and_reuse(self):
        self.run_main(["--split", "development"], FakeTransport())
        rows = common.read_jsonl(self.responses)
        common.dump_jsonl(self.responses, [r for r in rows if r["generation_kind"] == "model_call"])
        transport = FakeTransport()
        self.assertEqual(self.run_main(["--split", "development", "--resume"], transport), 0)
        self.assertEqual(transport.calls, [])
        self.assertEqual(len(runner.last_rows_by_cell(self.responses)), len(self.plan))

    def test_limit_counts_real_calls(self):
        transport = FakeTransport()
        self.run_main(["--split", "development", "--limit", "3"], transport)
        self.assertEqual(len(transport.calls), 3)
        rows = common.read_jsonl(self.responses)
        self.assertEqual(sum(1 for r in rows if r["model_call"]), 3)

    def test_evaluation_gate(self):
        transport = FakeTransport()
        self.assertEqual(self.run_main(["--split", "evaluation", "--confirm-evaluation"], transport), 2)
        self.run_main(["--split", "development"], FakeTransport())
        self.assertEqual(self.run_main(["--split", "evaluation", "--confirm-evaluation"], transport), 2)
        gate = runner.evaluation_gate_path(self.config, self.root)
        common.dump_json(gate, {"approved_by": "x", "approved_at": "2026-01-01",
                                "development_raw_responses_sha256": common.sha256_file(self.responses),
                                "config_sha256": common.sha256_file(self.config_path)})
        self.assertEqual(self.run_main(["--split", "evaluation"], transport), 2)
        self.assertEqual(transport.calls, [])
        self.assertEqual(self.run_main(["--split", "evaluation", "--confirm-evaluation", "--limit", "1"], transport), 0)
        self.assertEqual(len(transport.calls), 1)

    def test_evaluation_keeps_rows_for_missing_cells(self):
        self.run_main(["--split", "development", "--limit", "5"], FakeTransport())
        present = len(runner.last_rows_by_cell(self.responses))
        rows = evaluator.evaluate(self.config, "development", self.root)
        self.assertEqual(len(rows), 36)
        missing = 36 - present
        self.assertEqual(sum(1 for r in rows if r["response_status"] == "missing"), missing)
        self.assertEqual(sum(1 for r in rows if r["error_category"] == "missing_response"), missing)
        summary = summarizer.run(self.config, "development", self.root, all_outputs=True)
        self.assertEqual(summary["by_condition"]["separated"]["exact_match"]["denominator"], 18)
        for name in ("summary.json", "summary.csv", "SINTESI.md"):
            self.assertTrue((self.responses.parent / name).exists())


class BootstrapTests(unittest.TestCase):
    def rows(self):
        rows = []
        for e in range(6):
            for q in range(6):
                for condition in common.CONDITIONS:
                    correct = (e + q + (condition == "shared_interleaved")) % 3 != 0
                    rows.append({"episode_id": f"E{e}", "question_id": f"E{e}-Q{q}", "condition": condition,
                                 "exact_match": correct, "retrieval_success": True})
        return rows

    def test_reproducible_and_by_episode(self):
        rows = self.rows()
        draws = summarizer.bootstrap_draws(6, 500, 20260923)
        self.assertEqual(draws, summarizer.bootstrap_draws(6, 500, 20260923))
        self.assertTrue(all(len(d) == 6 for d in draws))
        a = summarizer.paired_bootstrap(rows, "exact_match", draws)
        b = summarizer.paired_bootstrap(rows, "exact_match", summarizer.bootstrap_draws(6, 500, 20260923))
        self.assertEqual(a, b)
        self.assertEqual(a["episodes"], 6)
        self.assertLessEqual(a["ci95_low_pp"], a["effect_pp"])
        self.assertGreaterEqual(a["ci95_high_pp"], a["effect_pp"])
        c = summarizer.paired_bootstrap(rows, "exact_match", summarizer.bootstrap_draws(6, 500, 1))
        self.assertEqual(a["effect_pp"], c["effect_pp"])

    def test_paired_table(self):
        rows = [{"question_id": "q", "condition": "separated", "exact_match": True},
                {"question_id": "q", "condition": "shared_interleaved", "exact_match": False}]
        self.assertEqual(summarizer.paired_table(rows)["only_separated"], 1)


# --------------------------------------------------------------------------
# Artefatti reali (se presenti)
# --------------------------------------------------------------------------

@unittest.skipUnless((REPO_ROOT / "data/rq3/sc07_design_v1/build_manifest.json").exists(), "artefatti non costruiti")
class RealArtifactTests(unittest.TestCase):
    def test_real_inputs_validate(self):
        checks = validator.validate(REAL_CONFIG, check_git=False)
        failed = [r for r in checks.results if not r["ok"]]
        self.assertEqual(failed, [])

    def test_real_counts(self):
        expected = {"development": (36, 23), "evaluation": (240, 139)}
        for split, (cells, calls) in expected.items():
            self.assertEqual(len(common.read_jsonl(common.requests_path(REAL_CONFIG, split))), cells)
            plan = common.read_jsonl(common.call_plan_path(REAL_CONFIG, split))
            self.assertEqual(len(plan), cells)
            self.assertEqual(sum(1 for p in plan if p["generation_kind"] == "model_call"), calls)
            self.assertEqual(REAL_CONFIG["counts"][split]["model_calls"], calls)

    def test_saved_responses_consistent_and_evaluation_gated(self):
        for split in common.SPLITS:
            self.assertIn(validator.check_responses(REAL_CONFIG, split), (None, []))
        if (common.results_dir(REAL_CONFIG, "evaluation") / "raw_responses.jsonl").exists():
            gate = common.read_json(runner.evaluation_gate_path(REAL_CONFIG))
            self.assertEqual(gate["approved_by"], "student")
            self.assertEqual(gate["config_sha256"], common.sha256_file(common.CONFIG_PATH))
            self.assertEqual(gate["development_raw_responses_sha256"],
                             common.sha256_file(common.results_dir(REAL_CONFIG, "development") / "raw_responses.jsonl"))


if __name__ == "__main__":
    unittest.main()
