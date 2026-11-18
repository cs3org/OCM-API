"""Check two spaces after clear sentence-ending periods in draft prose."""

import argparse
from bisect import bisect_right
from collections import Counter
from difflib import SequenceMatcher
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


def line_offsets(lines):
    offsets = []
    position = 0
    for line in lines:
        offsets.append(position)
        position += len(line) + 1
    return offsets


def classify_findings(base, result):
    old_lines, new_lines = base.splitlines(), result.splitlines()
    previous = set(spacing_findings(base))
    remaining = previous.copy()
    current = set(spacing_findings(result))
    inherited = set()
    exposed = set()
    for tag, a, b, c, d in SequenceMatcher(
            None, old_lines, new_lines, autojunk=False).get_opcodes():
        if tag == "equal":
            for line, column in current:
                old = (line - c + a, column)
                if c < line <= d and old in remaining:
                    inherited.add((line, column))
                    remaining.remove(old)
                elif c < line <= d and old not in previous:
                    exposed.add((line, column))
        elif tag == "replace" and any(a < line <= b for line, _ in remaining):
            old_offsets = line_offsets(old_lines[a:b])
            new_offsets = line_offsets(new_lines[c:d])
            matches = SequenceMatcher(None, "\n".join(old_lines[a:b]),
                                      "\n".join(new_lines[c:d])).get_matching_blocks()
            for line, column in sorted(current):
                if not c < line <= d:
                    continue
                raw = new_lines[line - 1]
                left = re.search(r"\S+$", raw[:column - 1])
                right = re.match(r" +\S+", raw[column - 1:])
                start = new_offsets[line - c - 1] + left.start()
                end = new_offsets[line - c - 1] + column - 1 + right.end()
                # The whole boundary must survive, not just its bad spaces.
                for match in matches:
                    if match.b <= start and end <= match.b + match.size:
                        gap = new_offsets[line - c - 1] + column - 1
                        old_gap = gap - match.b + match.a
                        index = bisect_right(old_offsets, old_gap) - 1
                        old = (a + index + 1, old_gap - old_offsets[index] + 1)
                        if old in remaining:
                            inherited.add((line, column))
                            remaining.remove(old)
                        elif old not in previous:
                            exposed.add((line, column))
                        break
    # A moved line may retain one old occurrence; extra copies cannot.
    moved = Counter((old_lines[line - 1], col) for line, col in remaining)
    # Newly exposed prose cannot borrow a removed finding elsewhere.
    for point in sorted(current - inherited - exposed):
        line, col = point
        key = (new_lines[line - 1], col)
        if moved[key]:
            inherited.add(point)
            moved[key] -= 1
    return sorted(current - inherited), sorted(inherited)


def git_text(*args):
    return subprocess.check_output(
        ["git", *args], text=True, encoding="utf-8", stderr=subprocess.PIPE)


def base_source(tree, path, root):
    relative = path.resolve().relative_to(root).as_posix()
    if not git_text("ls-tree", tree, "--", relative):
        return ""
    return git_text("show", f"{tree}:{relative}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--base", help="compare findings with this Git revision")
    mode.add_argument("--audit", action="store_true", help="report without content gating")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    if args.base is not None and not args.base.strip():
        parser.error("--base must not be empty")
    paths = args.paths or sorted(Path.cwd().glob("IETF-*.md"))
    counts = Counter()
    errors = 0
    changed_files = 0
    tree = None
    if not paths:
        print("Sentence spacing: FAILED (no draft sources found).")
        return 1
    if args.base:
        try:
            tree = git_text("rev-parse", "--verify", "--end-of-options",
                            f"{args.base}^{{tree}}").strip()
            root = Path(git_text("rev-parse", "--show-toplevel").strip()).resolve()
            print(f"Sentence spacing baseline: {args.base} (tree {tree})")
        except subprocess.CalledProcessError as error:
            tree = None
            print(f"Baseline check failed: {error.stderr.strip()}")
            errors += 1
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
            if args.base and tree:
                original = base_source(tree, path, root)
                changed_files += original != text
                introduced, inherited = classify_findings(original, text)
                groups = [("introduced", introduced), ("inherited", inherited)]
            else:
                label = "unclassified" if args.base else "audit" if args.audit else "error"
                groups = [(label, spacing_findings(text))]
            for label, findings in groups:
                counts[label] += len(findings)
                for line, column in findings:
                    print(f"{path}:{line}:{column}: [{label}] "
                          "use two spaces between sentences")
        except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as error:
            detail = (error.stderr.strip()
                      if isinstance(error, subprocess.CalledProcessError) else error)
            print(f"{path}: check failed: {detail}")
            errors += 1
    failed = errors or counts["introduced"] or counts["error"]
    status = "FAILED" if failed else "AUDIT" if args.audit else "OK"
    if args.base:
        details = f'{counts["introduced"]} introduced, {counts["inherited"]} inherited'
        if errors:
            details += f'; comparison incomplete; {counts["unclassified"]} unclassified'
        else:
            details += f'; {len(paths)} file' + ('s' if len(paths) != 1 else '')
            details += f', {changed_files} changed'
    else:
        total = sum(counts.values())
        details = f'{total} finding' + ('s' if total != 1 else '')
        details += f' in {len(paths)} file' + ('s' if len(paths) != 1 else '')
        details += '; full sources'
    if errors:
        details += f'; {errors} check error' + ('s' if errors != 1 else '')
    print(f"Sentence spacing: {status} ({details}).")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
