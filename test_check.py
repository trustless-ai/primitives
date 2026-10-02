"""Offline registry-boundary regressions; no GitHub, RPC or secret-file access."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest import mock

# check.py's unrelated contract setup may read a local key at import time.
with tempfile.TemporaryDirectory() as home, \
        mock.patch.dict(os.environ, {"ALCHEMY_KEY": ""}), \
        mock.patch.object(Path, "home", return_value=Path(home)):
    import check


HERE = Path(__file__).resolve().parent


def recipe(name="deils-leg2-reveal-v0"):
    return {"name": name, "status": "SHIPPED", "proof": {
        "type": "recompute-recipe", "ref": "trustless-ai/recompute-kit/conformance/" + name}}


class RecipeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.process = mock.patch.object(check.subprocess, "run").start()
        self.addCleanup(mock.patch.stopall)
        self.process.return_value = subprocess.CompletedProcess([], 0, "[]", "")

    def listing(self, items):
        self.process.return_value = subprocess.CompletedProcess([], 0, json.dumps(items), "")

    def test_package_and_suite_is_runner_declared_not_pass(self):
        self.listing([{"name": "suite.json", "type": "file"}, {"name": "vectors.json", "type": "file"}])
        state, detail = check.check(recipe("captured-admission-v0"))
        self.assertEqual(state, "RUNNER_DECLARED")
        self.assertIn("conformance not checked", detail)
        self.process.assert_called_once_with(
            ["gh", "api", "repos/trustless-ai/recompute-kit/contents/conformance/captured-admission-v0"],
            capture_output=True, text=True, timeout=25)

    def test_package_without_suite_is_package_present_not_pass(self):
        self.listing([{"name": "vectors.json", "type": "file"}, {"name": "README.md", "type": "file"}])
        state, detail = check.check(recipe())
        self.assertEqual(state, "PACKAGE_PRESENT")
        self.assertIn("no suite.json / no runner declaration", detail)
        self.assertIn("conformance not checked", detail)

    def test_package_404_remains_stale(self):
        self.process.return_value = subprocess.CompletedProcess([], 1, "", "gh: Not Found (HTTP 404)")
        self.assertEqual(check.check(recipe())[0], "STALE")

    def test_transport_http_failure_cannot_check(self):
        for error in ["gh: Forbidden (HTTP 403)", "gh: timeout", "gh: Bad Gateway (HTTP 502)",
                      "proxy error on request 404 (HTTP 500)"]:
            with self.subTest(error=error):
                self.process.return_value = subprocess.CompletedProcess([], 1, "[]", error)
                self.assertEqual(check.check(recipe())[0], "CANNOT_CHECK")

    def test_failed_process_cannot_promote_plausible_manifest_json(self):
        self.process.return_value = subprocess.CompletedProcess(
            [], 1, '[{"name":"suite.json","type":"file"}]', "connection reset")
        self.assertEqual(check.check(recipe())[0], "CANNOT_CHECK")

    def test_launch_failure_and_timeout_cannot_check(self):
        for error in [FileNotFoundError("gh unavailable"), subprocess.TimeoutExpired("gh", 25)]:
            with self.subTest(error=type(error).__name__):
                self.process.side_effect = error
                self.assertEqual(check.check(recipe())[0], "CANNOT_CHECK")

    def test_empty_or_non_json_output_cannot_check(self):
        for output in ["", "<html>gateway outage</html>", "{broken"]:
            with self.subTest(output=output):
                self.process.return_value = subprocess.CompletedProcess([], 0, output, "")
                self.assertEqual(check.check(recipe())[0], "CANNOT_CHECK")

    def test_wrong_listing_shapes_cannot_check(self):
        for items in [None, {}, {"type": "file"}, [None], [{}],
                      [{"name": "suite.json", "type": []}],
                      [{"name": 123, "type": "file"}], [{"name": "", "type": "file"}],
                      [{"name": "suite.json", "type": "unknown"}]]:
            with self.subTest(items=items):
                self.listing(items)
                self.assertEqual(check.check(recipe())[0], "CANNOT_CHECK")

    def test_duplicate_entry_names_cannot_check(self):
        self.listing([{"name": "suite.json", "type": "file"}] * 2)
        self.assertEqual(check.check(recipe())[0], "CANNOT_CHECK")

    def test_non_file_manifest_cannot_declare_runner(self):
        for kind in ["dir", "symlink", "submodule"]:
            with self.subTest(kind=kind):
                self.listing([{"name": "suite.json", "type": kind}])
                self.assertEqual(check.check(recipe())[0], "CANNOT_CHECK")

    def test_empty_directory_is_only_presence_not_correctness(self):
        self.assertEqual(check.check(recipe())[0], "PACKAGE_PRESENT")

    def test_uncovered_is_not_a_dependency_or_a_pass_fallback(self):
        # Any second lookup, including unavailable/malformed uncovered.json, is forbidden.
        def only_package(args, **kwargs):
            self.assertEqual(args, ["gh", "api", "repos/trustless-ai/recompute-kit/contents/conformance/deils-leg2-reveal-v0"])
            return subprocess.CompletedProcess([], 0, '[{"name":"README.md","type":"file"}]', "")
        self.process.side_effect = only_package
        self.assertEqual(check.check(recipe())[0], "PACKAGE_PRESENT")
        self.assertEqual(self.process.call_count, 1)

    def test_all_real_registry_recipes_use_the_same_presence_boundary(self):
        entries = [e for e in check.REG["primitives"] if e.get("proof", {}).get("type") == "recompute-recipe"]
        self.assertEqual(len(entries), 26)
        for entry in entries:
            with self.subTest(recipe=entry["name"]):
                self.listing([{"name": "suite.json", "type": "file"}])
                self.assertEqual(check.check(entry)[0], "RUNNER_DECLARED")
                self.listing([{"name": "vectors.json", "type": "file"}])
                self.assertEqual(check.check(entry)[0], "PACKAGE_PRESENT")


class RegistryExitTests(unittest.TestCase):
    def run_states(self, states):
        entries = [{"name": "entry-" + str(i)} for i in range(len(states))]
        with mock.patch.object(check, "REG", {"primitives": entries}), \
                mock.patch.object(check, "check", side_effect=[(s, "observed") for s in states]), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            rc = check.main()
        return rc, output.getvalue()

    def test_presence_observations_keep_registry_exit_zero_without_suite_pass(self):
        rc, out = self.run_states(["RUNNER_DECLARED", "PACKAGE_PRESENT"])
        self.assertEqual(rc, 0)
        self.assertIn("RUNNER_DECLARED:1", out)
        self.assertIn("PACKAGE_PRESENT:1", out)
        self.assertNotIn("PASS:", out)
        self.assertIn("not conformance PASS", out)

    def test_missing_package_fails_drift_gate(self):
        self.assertEqual(self.run_states(["PACKAGE_PRESENT", "STALE"])[0], 1)

    def test_lookup_failure_fails_closed(self):
        self.assertEqual(self.run_states(["RUNNER_DECLARED", "CANNOT_CHECK"])[0], 2)

    def test_drift_still_outranks_unknown(self):
        self.assertEqual(self.run_states(["STALE", "CANNOT_CHECK"])[0], 1)

    def test_other_proof_types_keep_existing_contracts(self):
        with mock.patch.object(check, "gh_exists", return_value=(True, "200")):
            self.assertEqual(check.check({"proof": {"type": "repo", "ref": "github.com/trustless-ai/example"}})[0], "PASS")
        with mock.patch.object(check, "eth_getcode", return_value=("UNRESOLVED", "disagree")):
            self.assertEqual(check.check({"proof": {"type": "contract", "address": "0x123", "chain": "mainnet"}})[0], "UNRESOLVED")
        self.assertEqual(check.check({"proof": {"type": "erc", "ref": "example"}})[0], "INDEX")
        self.assertEqual(check.check({"proof": {"type": "typo"}})[0], "CANNOT_CHECK")
        self.assertEqual(check.check({"proof": {"type": "typo"}, "optional": True})[0], "SKIP")


class RegistryInstructionsTests(unittest.TestCase):
    def test_recipe_instructions_are_conditional_and_status_is_preserved(self):
        entries = [e for e in check.REG["primitives"] if e.get("proof", {}).get("type") == "recompute-recipe"]
        for entry in entries:
            with self.subTest(recipe=entry["name"]):
                self.assertEqual(entry["status"], "SHIPPED")
                self.assertEqual(entry["verified_at"], "2026-09-03")
                self.assertIn("If suite.json exists", entry["verify"])
                self.assertIn("otherwise no central-runner verification is declared", entry["verify"])
                self.assertIn("not a conformance PASS", entry["verify"])

    def test_generator_cannot_reintroduce_old_recipe_claim(self):
        # The historical generator has a fixed output directory; intercept writes,
        # never write there or overwrite tracked fixtures during a test.
        rendered = {}
        def capture(path, data, *args, **kwargs):
            rendered[path.name] = data
            return len(data)
        with mock.patch.object(Path, "write_text", capture), contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(HERE / "gen.py"), run_name="generator_test")
        generated = json.loads(rendered["primitives.json"])
        recipes = lambda doc: [e for e in doc["primitives"] if e["proof"]["type"] == "recompute-recipe"]
        self.assertEqual(recipes(generated), recipes(check.REG))
        self.assertNotIn("run the suite to check any of them", rendered["README.md"])
        for text in [rendered["README.md"], (HERE / "README.md").read_text(encoding="utf-8")]:
            self.assertIn("**SHIPPED** (code + vectors, verifiable)", text)
            self.assertIn("RUNNER_DECLARED", text)
            self.assertIn("PACKAGE_PRESENT", text)
            self.assertIn("not a conformance verdict", text)
            self.assertIn("uncovered.json` is not a checker dependency", text)


if __name__ == "__main__":
    unittest.main()
