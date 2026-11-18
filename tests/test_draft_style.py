"""Checks for prose boundaries and exact inherited draft nits."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.check_draft_style import spacing_findings
from tools.check_idnits import new_errors


class DraftStyleTests(unittest.TestCase):
    def test_sentence_spacing(self):
        for gap, expected in ((" ", True), ("  ", False), ("   ", True)):
            with self.subTest(gap=gap):
                self.assertEqual(bool(spacing_findings(f"A sentence.{gap}Next sentence.")),
                                 expected)
        self.assertFalse(spacing_findings("A sentence.\nNext sentence."))

    def test_multipart_header(self):
        draft = ("---\ntitle: A title. Another phrase\n--- abstract\n"
                 "A sentence. Next one.\n--- middle\n"
                 "More prose.  Correct spacing.\n")
        self.assertEqual(spacing_findings(draft), [(4, 12)])

    def test_code_and_attributes(self):
        for prefix, fence in (("", "~~~"), ("", "````"),
                              ("    ", "~~~"), ("> ", "~~~")):
            draft = (f'{prefix}{fence} json\n{prefix}{{"userId": "alice. Bob"}}\n'
                     f'{prefix}{fence}\n'
                     '{: #example title="A value. Another value"}\n'
                     'An opaque `alice. Bob` value.  Valid prose.\n')
            with self.subTest(prefix=prefix, fence=fence):
                self.assertFalse(spacing_findings(draft))
                self.assertTrue(spacing_findings(draft + "Outside prose. Next sentence."))
        self.assertFalse(spacing_findings('    Code. Another token.\n'))
        self.assertFalse(spacing_findings('An opaque `first.\nNext part` value.\n'))

    def test_backticks_in_examples_leave_prose_visible(self):
        for fence in ("~~~", "```"):
            draft = (f'{fence} json\n{{"id": "first`literal"}}\n{fence}\n'
                     'Bad prose. Next sentence.\n'
                     f'{fence} json\n{{"id": "second`literal"}}\n{fence}\n')
            with self.subTest(fence=fence):
                self.assertEqual(spacing_findings(draft), [(4, 11)])

    def test_lists(self):
        self.assertFalse(spacing_findings('1. First item\n2. Another item\n'))
        self.assertTrue(spacing_findings('* Item\n    A sentence. Next one.\n'))
        self.assertFalse(spacing_findings('* Item\n      Code. Another token.\n'))

    def test_abbreviations_and_identifiers(self):
        self.assertFalse(spacing_findings('See e.g. Figure 2 or Dr. Smith.\n'))
        self.assertFalse(spacing_findings('Version 1.4.0 at https://example.org/a.b\n'))
        self.assertFalse(spacing_findings('[RFC2119]: https://example.org/a.b\n'))

    def test_quoted_sentence(self):
        self.assertTrue(spacing_findings('The response is "Denied." Another attempt fails.'))
        self.assertFalse(spacing_findings('The response is "Denied."  Another attempt fails.'))

    def test_cli_preserves_source(self):
        value = (b'~~~ json\n{"userId": "alice  smith@a.example.org"}\n'
                 b'~~~\nA sentence. Next one.')
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "IETF-example.md"
            source.write_bytes(value)
            command = [sys.executable, str(Path(__file__).resolve().parents[1] /
                       "tools/check_draft_style.py"), str(source)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("use two spaces between sentences", result.stdout)
            self.assertEqual(result.stderr, "")
            self.assertEqual(source.read_bytes(), value)

    def test_changed_lines_with_git_color(self):
        script = Path(__file__).resolve().parents[1] / "tools/check_draft_style.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "IETF-example.md"
            original = b"Old sentence. Next sentence.\n"
            value = original + b"New sentence. Next sentence.\n"
            env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="color.ui",
                       GIT_CONFIG_VALUE_0="always")
            subprocess.run(["git", "init", "--quiet", directory],
                           check=True, capture_output=True, env=env)
            blob = subprocess.check_output(
                ["git", "hash-object", "-w", "--stdin"],
                input=original, cwd=root, env=env).decode().strip()
            base = subprocess.check_output(
                ["git", "mktree"], input=f"100644 blob {blob}\t{source.name}\n",
                text=True, cwd=root, env=env).strip()
            source.write_bytes(value)
            subprocess.run(["git", "add", "--", source.name],
                           cwd=root, env=env, check=True, capture_output=True)
            result = subprocess.run(
                [sys.executable, str(script), "--base", base, source.name],
                cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout,
                             f"{source.name}:2:14: use two spaces between sentences\n")
            self.assertEqual(result.stderr, "")
            self.assertEqual(source.read_bytes(), value)

    def test_exact_nit_baseline(self):
        nit = {"severity": "ValidationError", "code": "LINE_TOO_LONG",
               "desc": "overlong", "line": [{"line": 1}]}
        report = {"nits": [nit]}
        baseline = [{"code": "LINE_TOO_LONG", "text": "original line"}]
        self.assertFalse(new_errors(report, 'original line', baseline))
        self.assertTrue(new_errors(report, 'different line', baseline))
        self.assertTrue(new_errors({"nits": [nit, nit]}, 'original line', baseline))

    def test_nit_lines_follow_newlines_across_page_breaks(self):
        report = {"nits": [{"severity": "ValidationError", "code": "LINE_TOO_LONG",
                            "desc": "overlong", "line": [{"line": 3}]}]}
        baseline = [{"code": "LINE_TOO_LONG", "text": "original line"}]
        self.assertFalse(new_errors(report, 'page one\n\f\noriginal line', baseline))
        self.assertTrue(new_errors(report, 'page one\n\f\ndifferent line', baseline))

    def test_unexpected_nit(self):
        report = {"nits": [{"severity": "ValidationError", "code": "OTHER",
                            "desc": "another error"}]}
        self.assertTrue(new_errors(report, '', []))
        self.assertFalse(new_errors({"nits": []}, '', []))


if __name__ == "__main__":
    unittest.main()
