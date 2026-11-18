"""Exercise draft aggregation with real Git snapshots and small converter stubs."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


STUB = r'''
import json
import os
from pathlib import Path
import sys

tool, args = Path(sys.argv[0]).name, sys.argv[1:]
with open(os.environ["CALL_LOG"], "a") as stream:
    stream.write(json.dumps({"tool": tool, "args": args}) + "\n")
if tool == os.environ.get("FAIL_TOOL") and os.environ.get("FAIL_DRAFT", "") in str(args):
    print("deliberate converter failure", file=sys.stderr)
    sys.exit(3)
if tool == "kramdown-rfc":
    print(Path(args[0]).read_text(), end="")
elif tool == "xml2rfc":
    xml = Path(args[0])
    for suffix in [".txt", ".html"]:
        xml.with_suffix(suffix).write_text(xml.read_text())
else:
    if os.environ.get("IDNITS_CRASH"):
        sys.exit(7)
    if os.environ.get("IDNITS_BAD_JSON"):
        print("{")
        sys.exit(0)
    lines = Path(args[-1]).read_text().split("\n")
    positions = [{"line": i + 1, "pos": 1} for i, line in enumerate(lines) if "BAD" in line]
    nits = [{"severity": "ValidationError", "code": "STUB_ERROR",
             "desc": "fixture error", "line": positions}] if positions else []
    print(json.dumps({"nits": nits}))
    sys.exit(2 if nits else 0)
'''


class DraftBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "artifacts"
        self.script = Path(__file__).resolve().parents[1] / "tools/check_draft_build.py"
        self.env = dict(os.environ, CALL_LOG=str(self.root / "calls.jsonl"))
        subprocess.run(["git", "init", "--quiet", str(self.root)],
                       check=True, capture_output=True, env=self.env)
        binary = self.root / "bin"
        binary.mkdir()
        for name in ["kramdown-rfc", "xml2rfc", "idnits"]:
            path = binary / name
            path.write_text(f"#!{sys.executable}\n" + STUB)
            path.chmod(0o755)
        self.env["PATH"] = str(binary) + os.pathsep + self.env["PATH"]
        self.sources = {f"IETF-{name}.md": f"docname: draft-{name}-00\nBody\n"
                        for name in ["a", "b", "c"]}
        for name, text in self.sources.items():
            (self.root / name).write_text(text)

    def base_tree(self, sources):
        entries = []
        for name, text in sorted(sources.items()):
            blob = subprocess.check_output(
                ["git", "hash-object", "-w", "--stdin"], input=text,
                text=True, cwd=self.root, env=self.env).strip()
            entries.append(f"100644 blob {blob}\t{name}\n")
        return subprocess.check_output(["git", "mktree"], input="".join(entries),
                                       text=True, cwd=self.root, env=self.env).strip()

    def run_check(self, *args, output=None):
        return subprocess.run(
            [sys.executable, str(self.script), "--output", str(output or self.output), *args],
            cwd=self.root, env=self.env, capture_output=True, text=True)

    def test_existing_errors_do_not_block_but_extra_occurrences_do(self):
        sources = {**self.sources, "IETF-a.md": self.sources["IETF-a.md"] + "BAD\n"}
        base = self.base_tree(sources)
        (self.root / "IETF-a.md").write_text(sources["IETF-a.md"])
        result = self.run_check("--base", base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 inherited error", result.stdout)
        (self.root / "IETF-a.md").write_text(sources["IETF-a.md"] + "BAD\n")
        result = self.run_check("--base", base, output=self.root / "extra")
        self.assertEqual(result.returncode, 1)
        self.assertIn("1 introduced finding", result.stdout)
        self.assertIn("3 result drafts, 1 failed", result.stdout)

    def test_first_converter_failure_does_not_stop_other_drafts(self):
        base = self.base_tree(self.sources)
        self.env.update(FAIL_TOOL="kramdown-rfc", FAIL_DRAFT="IETF-a.md")
        result = self.run_check("--base", base)
        self.assertEqual(result.returncode, 1)
        self.assertIn("deliberate converter failure", result.stderr)
        self.assertIn("check incomplete", result.stdout)
        calls = [json.loads(line) for line in (self.root / "calls.jsonl").read_text().splitlines()]
        for name in ["draft-b-00.txt", "draft-c-00.txt"]:
            self.assertTrue(any(call["tool"] == "idnits" and name in call["args"][-1]
                                for call in calls))
        self.assertFalse(any(call["tool"] == "xml2rfc" and "draft-a" in call["args"][0]
                             for call in calls))

    def test_revisions_have_separate_outputs_and_sources_stay_exact(self):
        base = self.base_tree(self.sources)
        source = self.root / "IETF-a.md"
        value = self.sources[source.name].replace("-00", "-01")
        source.write_text(value)
        result = self.run_check("--base", base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.output / "base/IETF-a/draft-a-00.txt").is_file())
        self.assertTrue((self.output / "IETF-a/draft-a-01.txt").is_file())
        self.assertEqual(source.read_text(), value)
        for suffix in ["xml", "html", "txt", "nits.json"]:
            self.assertTrue(list(self.output.rglob(f"*.{suffix}")))

    def test_added_and_removed_drafts(self):
        base = self.base_tree(self.sources)
        (self.root / "IETF-c.md").unlink()
        (self.root / "IETF-d.md").write_text("docname: draft-d-00\nBAD\n")
        result = self.run_check("--base", base)
        self.assertEqual(result.returncode, 1)
        self.assertIn("IETF-c.md: removed from result", result.stdout)
        self.assertIn("[introduced error]", result.stdout)
        record = json.loads((self.output / "comparison.json").read_text())
        added = next(item for item in record["drafts"] if item["source"] == "IETF-d.md")
        self.assertEqual(added["base_status"], "absent")

    def test_audit_is_nonblocking_and_invalid_baseline_is_not(self):
        (self.root / "IETF-a.md").write_text(self.sources["IETF-a.md"] + "BAD\n")
        result = self.run_check("--audit")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[audit error]", result.stdout)
        result = self.run_check("--base", "missing-revision", output=self.root / "invalid")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Baseline extraction failed", result.stdout)
        self.assertNotIn("[introduced", result.stdout)
        self.assertIn("check incomplete", result.stdout)
        result = self.run_check("--base", "", output=self.root / "empty-base")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--base must not be empty", result.stderr)

    def test_bad_reports_and_tool_exits_are_check_failures(self):
        base = self.base_tree(self.sources)
        for flag in ["IDNITS_CRASH", "IDNITS_BAD_JSON"]:
            with self.subTest(flag=flag):
                self.env[flag] = "1"
                result = self.run_check("--base", base, output=self.root / flag)
                self.env.pop(flag)
                self.assertEqual(result.returncode, 1)
                self.assertIn("3 result drafts, 3 failed", result.stdout)

    def test_no_sources_and_stale_outputs_are_not_clean(self):
        base = self.base_tree(self.sources)
        result = self.run_check("--base", base)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.run_check("--base", base)
        self.assertEqual(result.returncode, 1)
        self.assertIn("output directory is not empty", result.stdout)
        for name in self.sources:
            (self.root / name).unlink()
        result = self.run_check("--audit", output=self.root / "empty")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no result draft sources", result.stdout)


if __name__ == "__main__":
    unittest.main()
