#!/usr/bin/env python3
"""Run the public-safe product selection demo end to end."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "fixtures" / "best_sellers_on_ear_headphones_us_public_safe.json"


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


def package_and_validate(out_dir: Path) -> list[dict[str, Any]]:
    zip_path = out_dir / "product_selection_delivery_package.zip"
    steps = [
        run_step([sys.executable, "scripts/package_report.py", "--input-dir", str(out_dir), "--out", str(zip_path)]),
        run_step([sys.executable, "scripts/validate_product_selection_package.py", str(out_dir)]),
        run_step([sys.executable, "scripts/package_report.py", "--input-dir", str(out_dir), "--out", str(zip_path)]),
        run_step([sys.executable, "scripts/validate_product_selection_package.py", str(out_dir)]),
    ]
    return steps


def run_demo(fixture: Path, out_dir: Path, clean: bool, skip_privacy_scan: bool) -> dict[str, Any]:
    if clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    steps: list[dict[str, Any]] = []
    data_path = out_dir / "product_selection_data.json"
    html_path = out_dir / "product_selection_report.html"
    md_path = out_dir / "product_selection_report.md"

    steps.append(
        run_step(
            [
                sys.executable,
                "scripts/normalize_market_data_response.py",
                str(fixture),
                "--out",
                str(data_path),
            ]
        )
    )
    steps.append(
        run_step(
            [
                sys.executable,
                "scripts/render_product_selection_report.py",
                str(data_path),
                "--out",
                str(html_path),
            ]
        )
    )
    steps.append(
        run_step(
            [
                sys.executable,
                "scripts/export_markdown_report.py",
                str(data_path),
                "--out",
                str(md_path),
            ]
        )
    )
    steps.extend(package_and_validate(out_dir))
    if not skip_privacy_scan:
        steps.append(run_step([sys.executable, "scripts/privacy_scan.py", "."]))

    validation_path = out_dir / "validation_result.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else {}
    data = json.loads(data_path.read_text(encoding="utf-8")) if data_path.exists() else {}
    return {
        "ok": validation.get("ok") is True,
        "mode": "public_safe_demo",
        "fixture": str(fixture),
        "out_dir": str(out_dir),
        "decision": data.get("decision", {}).get("label"),
        "blocked_status": data.get("decision", {}).get("blocked_status"),
        "validation": validation,
        "steps": steps,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the public-safe demo pipeline.")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE), help="Public-safe fixture JSON.")
    parser.add_argument("--out-dir", default="dist", help="Output directory. Default: dist.")
    parser.add_argument("--no-clean", action="store_true", help="Do not clear the output directory first.")
    parser.add_argument("--skip-privacy-scan", action="store_true", help="Skip repository privacy scan.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_demo(
        fixture=Path(args.fixture),
        out_dir=Path(args.out_dir),
        clean=not args.no_clean,
        skip_privacy_scan=args.skip_privacy_scan,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
