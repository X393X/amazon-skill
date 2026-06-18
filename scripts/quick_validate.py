#!/usr/bin/env python3
"""Repository-level validation for the BYO-MCP product-selection skill."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FIXTURE = ROOT / "fixtures" / "best_sellers_on_ear_headphones_us_public_safe.json"
BLOCKED_FIXTURES = [
    ROOT / "fixtures" / "blocked_no_data.json",
    ROOT / "fixtures" / "blocked_missing_fields.json",
    ROOT / "fixtures" / "blocked_sorftime_unavailable.json",
]


def run_step(args: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    result = {
        "command": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }
    if completed.returncode != 0:
        raise RuntimeError(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def run_package_pipeline(fixture: Path, out_dir: Path) -> dict[str, Any]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_path = out_dir / "product_selection_data.json"
    html_path = out_dir / "product_selection_report.html"
    md_path = out_dir / "product_selection_report.md"
    zip_path = out_dir / "product_selection_delivery_package.zip"

    steps = [
        run_step([sys.executable, "scripts/normalize_market_data_response.py", str(fixture), "--out", str(data_path)]),
        run_step([sys.executable, "scripts/render_product_selection_report.py", str(data_path), "--out", str(html_path)]),
        run_step([sys.executable, "scripts/export_markdown_report.py", str(data_path), "--out", str(md_path)]),
        run_step([sys.executable, "scripts/package_report.py", "--input-dir", str(out_dir), "--out", str(zip_path)]),
        run_step([sys.executable, "scripts/validate_product_selection_package.py", str(out_dir)]),
        run_step([sys.executable, "scripts/package_report.py", "--input-dir", str(out_dir), "--out", str(zip_path)]),
        run_step([sys.executable, "scripts/validate_product_selection_package.py", str(out_dir)]),
    ]
    data = json.loads(data_path.read_text(encoding="utf-8"))
    validation = json.loads((out_dir / "validation_result.json").read_text(encoding="utf-8"))
    return {
        "fixture": str(fixture),
        "out_dir": str(out_dir),
        "decision": data.get("decision", {}).get("label"),
        "blocked_status": data.get("decision", {}).get("blocked_status"),
        "validation_ok": validation.get("ok") is True,
        "steps": steps,
    }


def validate_expected_blocked(results: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    expected = {
        "blocked_no_data": "blocked_no_data",
        "blocked_missing_fields": "blocked_missing_fields",
        "blocked_sorftime_unavailable": "blocked_sorftime_unavailable",
    }
    for result in results:
        stem = Path(result["fixture"]).stem
        if stem in expected:
            if result.get("decision") != "blocked":
                errors.append(f"{stem}: decision must be blocked")
            if result.get("blocked_status") != expected[stem]:
                errors.append(f"{stem}: blocked_status must be {expected[stem]}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run public-safe and blocked fixture validation.")
    parser.add_argument("--keep-output", action="store_true", help="Keep tmp/quick_validate outputs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results: list[dict[str, Any]] = []
    tmp_root = ROOT / "tmp" / "quick_validate"

    run_step([sys.executable, "-m", "py_compile", *[str(path) for path in (ROOT / "scripts").glob("*.py")]])
    results.append(run_package_pipeline(PUBLIC_FIXTURE, ROOT / "dist"))
    for fixture in BLOCKED_FIXTURES:
        results.append(run_package_pipeline(fixture, tmp_root / fixture.stem))
    privacy = run_step([sys.executable, "scripts/privacy_scan.py", "."])

    errors = validate_expected_blocked(results)
    for result in results:
        if not result["validation_ok"]:
            errors.append(f"{result['fixture']}: package validator failed")

    output = {
        "ok": not errors,
        "results": [
            {
                "fixture": item["fixture"],
                "out_dir": item["out_dir"],
                "decision": item["decision"],
                "blocked_status": item["blocked_status"],
                "validation_ok": item["validation_ok"],
            }
            for item in results
        ],
        "privacy_scan": privacy,
        "errors": errors,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if not args.keep_output and tmp_root.exists():
        shutil.rmtree(tmp_root)
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
