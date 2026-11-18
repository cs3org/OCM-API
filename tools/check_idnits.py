"""Report introduced and inherited idnits findings from two rendered drafts."""

import argparse
from collections import Counter
import json
from pathlib import Path


def occurrences(report, text):
    if not isinstance(report, dict) or not isinstance(report.get("nits"), list):
        raise ValueError("invalid idnits report: expected a nits array")
    # idnits counts newlines, not form feeds in paginated text.
    lines = text.split("\n")
    result = []
    for nit in report["nits"]:
        if (not isinstance(nit, dict)
                or nit.get("severity") not in {
                    "ValidationError", "ValidationWarning", "ValidationComment"}
                or not all(isinstance(nit.get(key), str) for key in ["code", "desc"])
                or not isinstance(nit.get("line", []), list)):
            raise ValueError("invalid idnits finding")
        locations = nit.get("line", [])
        if not locations:
            result.append((("global", nit["code"], nit["desc"]), nit, None))
        for location in locations:
            if (not isinstance(location, dict)
                    or type(location.get("line")) is not int
                    or not 1 <= location["line"] <= len(lines)
                    or type(location.get("pos", 1)) is not int
                    or location.get("pos", 1) < 1):
                raise ValueError("invalid idnits location")
            key = ("line", nit["code"], lines[location["line"] - 1])
            result.append((key, nit, location))
    return result


def classify_findings(report, text, base_report, base_text):
    # Consume each exact base occurrence once, even when line numbers move.
    remaining = Counter(key for key, nit, _ in occurrences(base_report, base_text)
                        if nit["severity"] == "ValidationError")
    introduced, inherited, advisory = [], [], []
    for finding in occurrences(report, text):
        key, nit, _ = finding
        if nit["severity"] != "ValidationError":
            advisory.append(finding)
        elif remaining[key]:
            inherited.append(finding)
            remaining[key] -= 1
        else:
            introduced.append(finding)
    return introduced, inherited, advisory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("text", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--base-report", type=Path)
    mode.add_argument("--audit", action="store_true")
    parser.add_argument("--base-text", type=Path)
    args = parser.parse_args()
    if bool(args.base_report) != bool(args.base_text):
        parser.error("--base-report and --base-text must be supplied together")
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        text = args.text.read_text(encoding="utf-8")
        base = (json.loads(args.base_report.read_text(encoding="utf-8"))
                if args.base_report else {"nits": []})
        base_text = (args.base_text.read_text(encoding="utf-8")
                     if args.base_text else "")
        introduced, inherited, advisory = classify_findings(report, text, base, base_text)
        new_label = "audit" if args.audit else "introduced" if args.base_report else "full"
        for label, findings in [(new_label, introduced), ("inherited", inherited),
                                ("advisory", advisory)]:
            for _, nit, location in findings:
                where = args.text.name
                if location:
                    where += f':{location["line"]}:{location.get("pos", 1)}'
                severity = nit["severity"].removeprefix("Validation").lower()
                print(f'{where}: [{label} {severity}] {nit["code"]}: {nit["desc"]}')
        failed = bool(introduced) and not args.audit
        status = "FAILED" if failed else "AUDIT" if args.audit else "OK"
        findings = 'finding' if len(introduced) == 1 else 'findings'
        errors = 'error' if len(inherited) == 1 else 'errors'
        print(f'idnits: {status} ({len(introduced)} {new_label} {findings}, '
              f'{len(inherited)} inherited {errors}, {len(advisory)} advisories; '
              f'{args.text.name}; occurrence counts).')
        return int(failed)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"{args.report.name}: idnits comparison failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
