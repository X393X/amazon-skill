#!/usr/bin/env python3
"""Scan a skill or repository for public-release privacy risks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    "tmp",
    "dist",
    "runtime",
    "real_data",
    "exports",
    "private",
    "secrets",
}

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".xlsx",
    ".xls",
    ".zip",
    ".gz",
    ".7z",
    ".exe",
    ".dll",
    ".pyd",
}

PATTERNS = [
    (
        "windows_user_path",
        re.compile(r"[A-Za-z]:[\\/]Users[\\/][^\\/\r\n]+(?:[\\/][^\\/\r\n]+)+"),
    ),
    (
        "wechat_or_chat_file_path",
        re.compile(r"[A-Za-z]:[\\/][^\r\n]*(?:xwechat_files|WeChat Files|wxid_[A-Za-z0-9_]+)[^\r\n]*", re.IGNORECASE),
    ),
    (
        "email_address",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    (
        "phone_number",
        re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b1[3-9]\d{9}\b)"),
    ),
    (
        "credential_assignment",
        re.compile(
            r"\b(?:api[_ -]?key|token|cookie|secret|password)\b\s*[:=]\s*[\"']?[^\"'\s]{8,}",
            re.IGNORECASE,
        ),
    ),
    (
        "internal_endpoint",
        re.compile(
            r"https?://(?:localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+|[^/\s]+\.internal)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "raw_review_text_field",
        re.compile(r'"(?:review_text|review_body|raw_reviews?)"\s*:', re.IGNORECASE),
    ),
]

UNFINISHED_TOKENS = ["TO" + "DO", "[TO" + "DO]", "FIX" + "ME", "T" + "BD"]
REAL_ASIN_PATTERN = re.compile(r"\bB0[A-Z0-9]{8}\b")
URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def is_private_terms_file(path: Path) -> bool:
    return path.name == "private_terms.txt" or (
        path.name.startswith("private_terms") and path.suffix.lower() == ".txt"
    )


def should_scan(path: Path, include_private_output: bool = False) -> bool:
    if is_private_terms_file(path):
        return False
    skip_dirs = SKIP_DIRS if not include_private_output else {
        item for item in SKIP_DIRS if item not in {"dist", "runtime", "tmp", "real_data", "exports", "private"}
    }
    if any(part in skip_dirs for part in path.parts):
        return False
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    return path.is_file()


def iter_files(root: Path, include_private_output: bool = False) -> Iterable[Path]:
    if root.is_file():
        if should_scan(root, include_private_output):
            yield root
        return
    for path in root.rglob("*"):
        if should_scan(path, include_private_output):
            yield path


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return None


def relative_name(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def load_private_terms(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []
    terms: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            terms.append(stripped)
    return terms


def is_inside_url(content: str, start: int, end: int) -> bool:
    return any(match.start() <= start and end <= match.end() for match in URL_PATTERN.finditer(content))


def is_public_marketplace_numeric_id(content: str, start: int, end: int) -> bool:
    value = content[start:end]
    if not re.fullmatch(r"\d{10,13}", value):
        return False
    context = content[max(0, start - 100): min(len(content), end + 100)].lower()
    marketplace_markers = [
        "nodeid",
        "node id",
        "category node",
        "category_node_id",
        "category_url",
        "bestsellers",
        "amazon.com/gp/bestsellers",
        "electronics/",
    ]
    return any(marker in context for marker in marketplace_markers)


def scan_text(content: str, filename: str, private_terms: list[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for pattern_name, pattern in PATTERNS:
        for match in pattern.finditer(content):
            if pattern_name == "phone_number" and is_inside_url(content, match.start(), match.end()):
                continue
            if pattern_name == "phone_number" and is_public_marketplace_numeric_id(content, match.start(), match.end()):
                continue
            findings.append({"file": filename, "type": pattern_name, "sample": match.group(0)[:120]})
            break
    upper_content = content.upper()
    for token in UNFINISHED_TOKENS:
        if token in upper_content:
            findings.append({"file": filename, "type": "unfinished_placeholder", "sample": token})
            break
    real_asins = {match.group(0) for match in REAL_ASIN_PATTERN.finditer(content)}
    if real_asins:
        findings.append({"file": filename, "type": "real_asin_like_identifier", "sample": sorted(real_asins)[0]})
    if len(real_asins) >= 80:
        findings.append({"file": filename, "type": "complete_top100_export_risk", "sample": f"{len(real_asins)} asin-like values"})
    for term in private_terms:
        if term and term in content:
            findings.append({"file": filename, "type": "private_term_match", "sample": "<private_term>"})
            break
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan a skill or repository for privacy risks.")
    parser.add_argument("path", nargs="?", default=".", help="Path to scan.")
    parser.add_argument(
        "--private-terms",
        default=None,
        help="Optional local private_terms.txt path. This file is not scanned.",
    )
    parser.add_argument(
        "--include-private-output",
        action="store_true",
        help="Also scan generated output directories such as dist, runtime, tmp, private, real_data, and exports.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.path).resolve()
    private_terms_path = Path(args.private_terms).resolve() if args.private_terms else root / "private_terms.txt"
    private_terms = load_private_terms(private_terms_path)

    findings: list[dict[str, str]] = []
    scanned_files = 0
    for path in iter_files(root, include_private_output=args.include_private_output):
        content = read_text(path)
        if content is None:
            continue
        scanned_files += 1
        findings.extend(scan_text(content, relative_name(path, root), private_terms))

    result = {
        "ok": not findings,
        "scanned_files": scanned_files,
        "private_terms_loaded": len(private_terms),
        "findings_count": len(findings),
        "findings": findings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
