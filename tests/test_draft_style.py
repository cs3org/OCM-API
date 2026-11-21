"""Checks for prose boundaries and exact inherited draft nits."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import check_draft_style as style
from tools import check_idnits as nits
from tools.check_draft_style import spacing_findings


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
        self.assertFalse(spacing_findings('3.1. First item\n3.2. Another item\n'))
        self.assertEqual(spacing_findings('3.1. First item. Next sentence.\n'),
                         [(1, 17)])
        self.assertTrue(spacing_findings('* Item\n    A sentence. Next one.\n'))
        self.assertFalse(spacing_findings('* Item\n      Code. Another token.\n'))

    def test_reference_author_initials(self):
        for authors in ['Bradner, S.', 'Dusseault, L. M.',
                        'Barnes, R., Bhargavan, K., Lipp, B. and Wood, C. A.',
                        'Hedberg, R., Ed., Jones, M.B., Solberg, A.A.,\n'
                        'Bradley, J., De Marco, G., and V. Dzhuvinov,']:
            with self.subTest(authors=authors):
                entry = f'[REF] {authors} "[A title](https://example.org)".\n'
                self.assertFalse(spacing_findings(entry))
                self.assertEqual(spacing_findings(entry + 'Bad prose. Next sentence.\n'),
                                 [(entry.count('\n') + 1, 11)])
        self.assertTrue(spacing_findings(
            '[REF] Bradner, S. "[A title](https://example.org)", 1997. Next sentence.\n'))
        self.assertTrue(spacing_findings(
            '[REF] Bradner, S. "[A sentence. Next sentence](https://example.org)".\n'))

    def test_initials_in_name_lists(self):
        self.assertFalse(spacing_findings(
            'Tilo Steiger, C.D. Tiwari, Alejandro Unger and Tom Wezepoel.\n'))
        self.assertTrue(spacing_findings('Choose option A. Next sentence.\n'))
        self.assertTrue(spacing_findings('We visited the U.S. Next sentence.\n'))
        self.assertTrue(spacing_findings(
            'Tilo Steiger, C.D. Tiwari, Alejandro Unger. Next sentence.\n'))

    def test_trailing_citations(self):
        self.assertFalse(spacing_findings('A statement. [RFC6838]\n'))
        self.assertEqual(spacing_findings('A statement. [RFC6838]\nBad prose. Next one.\n'),
                         [(2, 11)])
        self.assertTrue(spacing_findings('A statement. [RFC6838] Next sentence.\n'))
        self.assertTrue(spacing_findings('A statement. [Important note]\n'))

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
            self.assertIn(f"{source.name}:1:14: [inherited]", result.stdout)
            self.assertIn(f"{source.name}:2:14: [introduced]", result.stdout)
            self.assertIn("1 introduced, 1 inherited", result.stdout)
            self.assertEqual(result.stderr, "")
            self.assertEqual(source.read_bytes(), value)

    def test_finding_inheritance(self):
        bad = "Old sentence. Next sentence.\n"
        cases = [
            (bad, bad, 0, 1),
            (bad, "\n" + bad, 0, 1),
            (bad, bad.replace("Old", "New"), 0, 1),
            (bad, bad.replace("Next", "Another"), 1, 0),
            (bad, bad.replace(". Next", ".  Next"), 0, 0),
            (bad, bad * 2, 1, 1),
            ("Header\n" + bad + "Footer\n", bad + "Header\nFooter\n", 0, 1),
            ("~~~ text\n" + bad + "~~~\n", bad, 1, 0),
            (bad + "Left one\nLeft two\n~~~\n" + bad + "~~~\nRight one\nRight two\n",
             "Left one\nLeft two\n" + bad + "Right one\nRight two\n", 1, 0),
            ('[REF] Bradner, S. "[A title]"\n',
             'Bradner, S. "[A title]"\n', 1, 0),
            ('A statement. [RFC6838]\n',
             'A statement. [RFC6838] Next sentence.\n', 1, 0),
            ("", bad, 1, 0),
        ]
        for base, result, new_count, old_count in cases:
            with self.subTest(base=base, result=result):
                introduced, inherited = style.classify_findings(base, result)
                self.assertEqual(len(introduced), new_count)
                self.assertEqual(len(inherited), old_count)

    def test_audit_reports_all_inputs(self):
        script = Path(__file__).resolve().parents[1] / "tools/check_draft_style.py"
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ["first.md", "second.md"]]
            for path in paths:
                path.write_text("A sentence. Next sentence.\n")
            result = subprocess.run(
                [sys.executable, str(script), "--audit", *map(str, paths)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for path in paths:
                self.assertIn(f"{path}:1:12: [audit]", result.stdout)
            self.assertIn("2 findings in 2 files", result.stdout)

    def test_audit_with_base_classifies_without_failing(self):
        script = Path(__file__).resolve().parents[1] / "tools/check_draft_style.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "IETF-example.md"
            original = "Old sentence. Next sentence.\n"
            subprocess.run(["git", "init", "--quiet", directory],
                           check=True, capture_output=True)
            blob = subprocess.check_output(
                ["git", "hash-object", "-w", "--stdin"],
                input=original.encode(), cwd=root).decode().strip()
            base = subprocess.check_output(
                ["git", "mktree"], input=f"100644 blob {blob}\t{source.name}\n",
                text=True, cwd=root).strip()
            source.write_text(original + "New sentence. Next sentence.\n")
            result = subprocess.run(
                [sys.executable, str(script), "--base", base, "--audit", source.name],
                cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"{source.name}:1:14: [inherited]", result.stdout)
            self.assertIn(f"{source.name}:2:14: [introduced]", result.stdout)
            self.assertIn("AUDIT (1 introduced, 1 inherited", result.stdout)
            result = subprocess.run(
                [sys.executable, str(script), "--base", "missing-revision",
                 "--audit", source.name], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Baseline check failed", result.stdout)

    def test_source_errors_do_not_hide_other_findings(self):
        script = Path(__file__).resolve().parents[1] / "tools/check_draft_style.py"
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / "exists.md"
            good.write_text("A sentence. Next sentence.\n")
            result = subprocess.run(
                [sys.executable, str(script), "--audit",
                 str(Path(directory) / "missing.md"), str(good)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("missing.md", result.stdout)
            self.assertIn(f"{good}:1:12: [audit]", result.stdout)
            self.assertIn("1 check error", result.stdout)
            result = subprocess.run(
                [sys.executable, str(script), "--base", "", str(good)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--base must not be empty", result.stderr)

    def test_exact_nit_baseline(self):
        nit = {"severity": "ValidationError", "code": "LINE_TOO_LONG",
               "desc": "overlong", "line": [{"line": 1}]}
        report = {"nits": [nit]}
        for text, result, expected in [
                ('original line', report, (0, 1)),
                ('different line', report, (1, 0)),
                ('original line', {"nits": [nit, nit]}, (1, 1))]:
            with self.subTest(text=text, result=result):
                new, old, advisory = nits.classify_findings(
                    result, text, report, 'original line')
                self.assertEqual((len(new), len(old)), expected)
                self.assertEqual(advisory, [])

    def test_nit_lines_follow_newlines_across_page_breaks(self):
        report = {"nits": [{"severity": "ValidationError", "code": "LINE_TOO_LONG",
                            "desc": "overlong", "line": [{"line": 3}]}]}
        base = 'page one\n\f\noriginal line'
        for result, expected in [(base, (0, 1)),
                                 ('page one\n\f\ndifferent line', (1, 0))]:
            new, old, _ = nits.classify_findings(report, result, report, base)
            self.assertEqual((len(new), len(old)), expected)

    def test_unexpected_nit(self):
        report = {"nits": [{"severity": "ValidationError", "code": "OTHER",
                            "desc": "another error"}]}
        empty = {"nits": []}
        new, old, _ = nits.classify_findings(report, '', empty, '')
        self.assertEqual((len(new), len(old)), (1, 0))
        new, old, _ = nits.classify_findings(report, '', report, '')
        self.assertEqual((len(new), len(old)), (0, 1))
        self.assertEqual(nits.classify_findings(empty, '', empty, ''), ([], [], []))

    def test_grouped_nits_and_invalid_reports(self):
        nit = {"severity": "ValidationError", "code": "LINE_TOO_LONG",
               "desc": "two lines", "line": [{"line": 1}, {"line": 2}]}
        base = {"nits": [{**nit, "desc": "one line", "line": [{"line": 1}]}]}
        new, old, _ = nits.classify_findings(
            {"nits": [nit]}, 'same\nsame', base, 'same')
        self.assertEqual((len(new), len(old)), (1, 1))
        warning = {"severity": "ValidationWarning", "code": "REFERENCE",
                   "desc": "review this reference"}
        self.assertEqual(len(nits.classify_findings(
            {"nits": [warning]}, '', {"nits": []}, '')[2]), 1)
        for report in [{}, {"nits": "bad"},
                       {"nits": [{**nit, "line": [{"line": 99}]}]}]:
            with self.subTest(report=report), self.assertRaises(ValueError):
                nits.classify_findings(report, 'one line', {"nits": []}, '')


if __name__ == "__main__":
    unittest.main()
