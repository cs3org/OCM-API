"""Report new idnits errors while retaining exact inherited exceptions."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re


def new_errors(report, text, baseline):
    remaining = Counter((item["code"], item["text"]) for item in baseline)
    lines = text.split("\n")
    errors = []
    for nit in report["nits"]:
        if nit["severity"] != "ValidationError":
            continue
        locations = nit.get("line", [])
        if not locations:
            errors.append(f'{nit["code"]}: {nit["desc"]}')
        for location in locations:
            number = location["line"]
            value = lines[number - 1] if 0 < number <= len(lines) else None
            key = (nit["code"], value)
            if remaining[key]:
                remaining[key] -= 1
            else:
                errors.append(f'{nit["code"]} at line {number}: {nit["desc"]}')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("text", type=Path)
    parser.add_argument("baseline", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    baseline = json.loads(args.baseline.read_text())
    name = re.sub(r"-\d+$", "", args.text.stem)
    errors = new_errors(report, args.text.read_text(), baseline["drafts"].get(name, []))
    for error in errors:
        print(f"{args.text}: {error}")
    print(f'{args.text.name}: {report["nitsBySeverity"]}; {len(errors)} new errors')
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
