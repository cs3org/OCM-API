"""Build base/result drafts and report content regressions without stopping early."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile


def render(source, output, idnits, label):
    stage = "docname"
    try:
        names = re.findall(r"^docname: *(.*)$", source.read_text(encoding="utf-8"), re.M)
        if len(names) != 1 or not re.fullmatch(r"draft-[a-z0-9-]+-[0-9]{2,}", names[0]):
            raise ValueError("expected one valid docname")
        if output.exists() and any(output.iterdir()):
            raise ValueError("draft output directory is not empty")
        output.mkdir(parents=True, exist_ok=True)
        xml = output / (names[0] + ".xml")
        text = xml.with_suffix(".txt")
        report = output / (names[0] + ".nits.json")
        stage = "kramdown-rfc"
        print(f"{source.name} ({label}): {stage}", flush=True)
        with xml.open("w", encoding="utf-8") as stream:
            subprocess.run(["kramdown-rfc", source.name], cwd=source.parent,
                           stdout=stream, check=True)
        stage = "xml2rfc"
        print(f"{source.name} ({label}): {stage}", flush=True)
        subprocess.run(["xml2rfc", str(xml), "--text", "--html", "--path", str(output)],
                       cwd=source.parent, check=True)
        if not text.is_file() or not xml.with_suffix(".html").is_file():
            raise ValueError("converter did not produce text and HTML")
        stage = "idnits"
        print(f"{source.name} ({label}): {stage}", flush=True)
        with report.open("w", encoding="utf-8") as stream:
            result = subprocess.run([idnits, "--mode", "normal", "--output", "json",
                                     "--fail-on", "errors", str(text)], stdout=stream)
        # Exit 2 contains findings; their base comparison decides failure.
        if result.returncode not in (0, 2):
            raise ValueError(f"unexpected idnits exit {result.returncode}")
        return report, text
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"{source.name} ({label}): {stage} failed: {error}", flush=True)
        return None


def extract_base(revision, directory):
    tree = subprocess.check_output(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{revision}^{{tree}}"],
        text=True).strip()
    archive = directory.parent / "base.tar"
    with archive.open("wb") as stream:
        subprocess.run(["git", "archive", tree], stdout=stream, check=True)
    directory.mkdir()
    with tarfile.open(archive) as stream:
        stream.extractall(directory, filter="data")
    return tree


def check_drafts(root, output, base, audit, idnits, temporary):
    output.mkdir(parents=True, exist_ok=True)
    if audit:
        print("Advisory mode: content findings do not fail; build and "
              "tool errors still do.", flush=True)
    record = {"mode": "comparison" if base else "audit" if audit else "full",
              "advisory": audit, "base": base,
              "checkout": os.environ.get("GITHUB_SHA"),
              "pr_head": os.environ.get("PR_HEAD_SHA"), "drafts": []}
    baseline = None
    baseline_error = False
    if base:
        try:
            baseline = temporary / "base-inputs"
            record["base_tree"] = extract_base(base, baseline)
            print(f"Draft baseline: {base} (tree {record['base_tree']})", flush=True)
        except (OSError, ValueError, tarfile.TarError, subprocess.CalledProcessError) as error:
            print(f"Baseline extraction failed: {error}", flush=True)
            baseline = None
            baseline_error = True
    head_names = {p.name for p in root.glob("IETF-*.md") if p.is_file()}
    base_names = {p.name for p in baseline.glob("IETF-*.md") if p.is_file()} if baseline else set()
    failed = 0
    adapter = Path(__file__).resolve().with_name("check_idnits.py")
    for name in sorted(head_names | base_names):
        if name not in head_names:
            print(f"{name}: removed from result", flush=True)
            record["drafts"].append({"source": name, "status": "removed"})
            continue
        old = None
        entry = {"source": name, "status": "incomplete"}
        if name in base_names:
            old = render(baseline / name, output / "base" / Path(name).stem,
                         idnits, "base")
        elif base and not baseline_error:
            # Absence was verified in a valid base, not inferred from a failed check.
            absent = output / "base" / Path(name).stem
            absent.mkdir(parents=True, exist_ok=True)
            report, text = absent / "absent.json", absent / "absent.txt"
            report.write_text('{"nits": [], "absent": true}\n', encoding="utf-8")
            text.write_text("", encoding="utf-8")
            old = report, text
            entry["base_status"] = "absent"
        current = render(root / name, output / Path(name).stem, idnits, "result")
        if current and (not base or old):
            args = [sys.executable, str(adapter), *map(str, current)]
            if base:
                args += ["--base-report", str(old[0]), "--base-text", str(old[1])]
            if audit:
                args += ["--audit"]
            result = subprocess.run(args)
            entry["status"] = "passed" if result.returncode == 0 else "failed"
            entry["result_report"] = str(current[0].relative_to(output))
            if old:
                entry["base_report"] = str(old[0].relative_to(output))
        else:
            print(f"{name}: check incomplete; no content-regression result", flush=True)
        failed += entry["status"] != "passed"
        record["drafts"].append(entry)
    if not head_names:
        print("Draft builds: no result draft sources found", flush=True)
    record["failed_drafts"] = failed
    record["baseline_error"] = baseline_error
    (output / "comparison.json").write_text(json.dumps(record, indent=2) + "\n",
                                            encoding="utf-8")
    status = "FAILED" if failed or baseline_error or not head_names else "OK"
    advisory = ", advisory" if audit else ""
    print(f"Draft builds: {status} ({len(head_names)} result drafts, {failed} failed; "
          f"{record['mode']}{advisory}).", flush=True)
    return int(status == "FAILED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base")
    parser.add_argument("--audit", action="store_true",
                        help="report content findings without failing; "
                             "operational errors still fail")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--idnits", default="idnits")
    args = parser.parse_args()
    if args.base is not None and not args.base.strip():
        parser.error("--base must not be empty")
    try:
        with tempfile.TemporaryDirectory() as directory:
            return check_drafts(Path.cwd(), args.output.resolve(), args.base,
                                args.audit, args.idnits, Path(directory))
    except (OSError, ValueError) as error:
        print(f"Draft build check failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
