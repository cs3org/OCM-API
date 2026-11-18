"""Check two spaces after clear sentence-ending periods in draft prose."""

import argparse
from itertools import groupby
from pathlib import Path
import re
import subprocess


ABBREVIATIONS = {"e.g.", "i.e.", "etc.", "cf.", "vs.", "Dr.", "Mr.", "Ms.",
                 "Mrs.", "Prof.", "Fig.", "Eq.", "Sec.", "St."}
BOUNDARY = re.compile(r'''\.[\"')\]]*( +)(?=[\"'(\[]*[A-Z])''')
FENCE = re.compile(r"^[ \t>]*(`{3,}|~{3,})")


def mask(match):
    """Hide literals without shifting diagnostic positions."""
    return re.sub(r"[^\n]", "x", match[0])


def spacing_findings(text):
    findings = []
    # Kramdown's multipart header ends at "--- abstract".
    header = text.startswith("---\n")
    fence = None
    list_indent = 0
    prose = []
    for number, raw in enumerate(text.splitlines(), 1):
        # Excluded blocks also bound multiline inline-code spans.
        prose.append(None)
        if header:
            if number > 1 and (raw == "---" or raw.startswith("--- ")):
                header = False
            continue
        delimiter = FENCE.match(raw)
        if delimiter:
            run = delimiter[1]
            if fence is None:
                fence = run
            elif (run[0] == fence[0] and len(run) >= len(fence)
                  and not raw[delimiter.end():].strip()):
                fence = None
            continue
        if fence or not raw.strip() or raw.startswith(("---", "\t")):
            continue
        marker = re.match(r"^\s*(?:[*+-]|\d+[.)])\s+", raw)
        indent = len(raw) - len(raw.lstrip())
        if marker:
            list_indent = marker.end()
        elif raw.strip() and indent < list_indent:
            list_indent = 0
        if indent >= list_indent + 4:
            continue
        if re.match(r"^\s*(?:#{1,6} |\{:|\[[^\]]+\]:|<)", raw):
            continue
        prose[-1] = (number, re.sub(r"^(\s*\d+\.\s+)", mask, raw))
    for is_prose, entries in groupby(prose, key=lambda entry: entry is not None):
        if not is_prose:
            continue
        block = list(entries)
        protected = re.sub(r"(`+).*?\1", mask,
                           "\n".join(line for _, line in block), flags=re.S)
        protected = re.sub(r"<?https?://[^\s<>]+>?", mask, protected)
        for (number, _), line in zip(block, protected.split("\n")):
            for match in BOUNDARY.finditer(line):
                word = re.search(r"[\w.-]+$", line[:match.start()])
                if word and word[0] + "." in ABBREVIATIONS:
                    continue
                if len(match[1]) != 2:
                    findings.append((number, match.start(1) + 1))
    return findings


def added_lines(base, path):
    diff = subprocess.check_output(
        ["git", "diff", "--no-ext-diff", "--no-color", "--unified=0",
         base, "--", str(path)],
        text=True)
    result = set()
    for start, count in re.findall(r"^@@ -[^ ]+ \+(\d+)(?:,(\d+))? @@", diff, re.M):
        result.update(range(int(start), int(start) + int(count or 1)))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="check only lines changed from this Git revision")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    failed = False
    for path in args.paths or sorted(Path.cwd().glob("IETF-*.md")):
        changed = added_lines(args.base, path) if args.base else None
        for line, column in spacing_findings(path.read_text(encoding="utf-8")):
            if changed is None or line in changed:
                print(f"{path}:{line}:{column}: use two spaces between sentences")
                failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
