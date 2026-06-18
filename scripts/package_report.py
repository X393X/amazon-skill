#!/usr/bin/env python3
"""Package product selection report outputs into a portable ZIP."""

from __future__ import annotations

import argparse
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_FILES = [
    "product_selection_report.html",
    "product_selection_report.md",
    "product_selection_data.json",
    "source_manifest.json",
    "validation_result.json",
    "README_OPEN_REPORT.txt",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def build_delivery(input_dir: Path, out_zip: Path, privacy_mode: str) -> dict[str, Any]:
    return {
        "local_preview_url": "for local validation only",
        "is_localhost_only": True,
        "report_file_path": "product_selection_report.html",
        "package_zip_path": out_zip.name,
        "publish_status": "local_only",
        "shareable_url": None,
        "shareable_url_scope": "none",
        "notes": (
            "This package is private_internal and must remain local or internal-only."
            if privacy_mode == "private_internal"
            else "This package is public-safe; publish only after validator and privacy scan pass."
        ),
    }


def write_open_readme(path: Path, privacy_mode: str) -> None:
    if privacy_mode == "private_internal":
        scope = "private_internal"
        warning = "private_internal 报告不得上传 GitHub，不得公开分享，不得发布到公网。"
    else:
        scope = "public-safe"
        warning = "public-safe 报告可在通过 validator 与 privacy_scan 后发布到公开静态站。"
    text = "\n".join(
        [
            "Amazon Product Selection Research Delivery Package",
            "",
            "Open instructions:",
            "1. Double-click product_selection_report.html.",
            "2. Or drag product_selection_report.html into a browser window.",
            "",
            f"Package scope: {scope}",
            warning,
            "",
            "Do not use a local preview URL as a shareable delivery link.",
            "Use this ZIP package or a configured public-safe/internal publishing channel.",
            "",
        ]
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def ensure_validation_result(path: Path, delivery: dict[str, Any]) -> None:
    if path.exists():
        payload = read_json(path)
    else:
        payload = {
            "ok": None,
            "checked_at": utc_now(),
            "required_files": [],
            "errors": [],
            "note": "Run scripts/validate_product_selection_package.py after packaging for final validation.",
        }
    payload["delivery"] = delivery
    write_json(path, payload)


def update_delivery(input_dir: Path, out_zip: Path) -> tuple[str, dict[str, Any]]:
    data_path = input_dir / "product_selection_data.json"
    manifest_path = input_dir / "source_manifest.json"
    data = read_json(data_path)
    manifest = read_json(manifest_path)
    privacy_mode = str(data.get("privacy_mode") or manifest.get("privacy_mode") or "public_safe_real_world")
    delivery = build_delivery(input_dir, out_zip, privacy_mode)

    if data:
        data["delivery"] = delivery
        package = data.get("report_delivery_package") if isinstance(data.get("report_delivery_package"), dict) else {}
        package["package_zip_path"] = out_zip.name
        package["privacy_mode"] = privacy_mode
        data["report_delivery_package"] = package
        write_json(data_path, data)
    if manifest:
        manifest["delivery"] = delivery
        write_json(manifest_path, manifest)
    ensure_validation_result(input_dir / "validation_result.json", delivery)
    write_open_readme(input_dir / "README_OPEN_REPORT.txt", privacy_mode)
    return privacy_mode, delivery


def package(input_dir: Path, out_zip: Path) -> dict[str, Any]:
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"input directory not found: {input_dir}")
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    privacy_mode, delivery = update_delivery(input_dir, out_zip)
    missing = [name for name in PACKAGE_FILES if not (input_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"missing package files: {', '.join(missing)}")
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in PACKAGE_FILES:
            archive.write(input_dir / name, arcname=name)
    return {
        "ok": True,
        "package_zip_path": str(out_zip),
        "privacy_mode": privacy_mode,
        "files": PACKAGE_FILES,
        "delivery": delivery,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a portable product selection delivery ZIP.")
    parser.add_argument("--input-dir", required=True, help="Directory containing generated report outputs.")
    parser.add_argument("--out", required=True, help="Output ZIP path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = package(Path(args.input_dir), Path(args.out))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
