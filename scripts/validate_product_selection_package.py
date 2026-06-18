#!/usr/bin/env python3
"""Validate a generated product selection dist package."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "product_selection_report.html",
    "product_selection_data.json",
    "source_manifest.json",
]

REQUIRED_SECTION_IDS = [
    "executive-summary",
    "input-info",
    "sorftime-status",
    "category-capacity",
    "keyword-opportunity",
    "competitor-structure",
    "price-profit",
    "review-voc",
    "differentiation",
    "risk",
    "scorecard",
    "final-decision",
    "evidence-table",
    "assumptions-missing-data",
    "next-validation",
    "downstream-brief",
    "delivery-notes",
]

REQUIRED_MANIFEST_FIELDS = [
    "privacy_mode",
    "report_language",
    "generated_at",
    "query",
    "data_blocks",
    "confidence",
    "blocked_status",
    "no_user_private_data",
    "contains_user_private_data",
    "contains_raw_sorftime_export",
    "contains_review_text",
    "public_data_reference",
    "data_freshness",
    "delivery",
    "sources",
]

BLOCKED_STATUSES = {
    "blocked_missing_site",
    "blocked_missing_product_type",
    "blocked_invalid_input",
    "blocked_no_data",
    "blocked_missing_fields",
    "blocked_sorftime_unavailable",
    "blocked_insufficient_competitors",
    "blocked_fetch_failed",
}
MARKET_STAGES = {"growth", "mature", "price_war", "seasonal", "declining", "unknown"}
RAMP_LEVELS = {"low", "medium", "high", "very_high"}
ENTRY_TYPES = {
    "keyword_wedge",
    "price_band_wedge",
    "audience_wedge",
    "scenario_wedge",
    "feature_wedge",
    "voc_painpoint_wedge",
    "bundle_wedge",
    "compliance_safe_wedge",
}
DISQUALIFIER_TYPES = {
    "compliance_blocker",
    "patent_or_design_risk",
    "no_viable_margin",
    "unavailable_supply_chain",
    "extreme_return_risk",
    "high_certification_cost",
    "restricted_category",
    "data_unreliable",
}
DISQUALIFIER_STATUSES = {"active", "inactive", "unknown"}
DISQUALIFIER_SEVERITIES = {"info", "warning", "critical"}
EVIDENCE_LEVELS = {
    "A_live_market_data",
    "B_provider_aggregate",
    "C_public_safe_template",
    "D_assumption",
}
CLUSTER_KEYS = [
    "price_band_cluster",
    "review_moat_cluster",
    "brand_dominance_cluster",
    "feature_positioning_cluster",
    "weakness_cluster",
    "newcomer_cluster",
]
CLUSTER_ITEM_FIELDS = [
    "cluster_name",
    "summary",
    "competition_pressure",
    "entry_implication",
    "evidence_level",
]
PROFIT_FIELDS = [
    "target_price",
    "estimated_landed_cost",
    "amazon_fee",
    "fba_fee",
    "return_loss",
    "promotion_buffer",
    "ad_cost_tolerance",
    "target_margin",
]
EXTENDED_MODEL_FIELDS = [
    "data_coverage_score",
    "profit_scenarios",
    "ramp_path",
    "voc_opportunity_matrix",
    "validation_plan",
    "trending_product_signals",
    "voc_trend_summary",
    "product_action_plan",
    "report_delivery_package",
    "optional_charts_manifest",
]
DATA_FRESHNESS_VALUES = {
    "template_sample_not_live_market_data",
    "live_or_latest_available_sorftime_data",
}
RANGE_PATTERN = re.compile(r"^\s*[0-9]+(?:\.[0-9]+)?\s*-\s*[0-9]+(?:\.[0-9]+)?\s*$")
REAL_ASIN_PATTERN = re.compile(r"\bB0[A-Z0-9]{8}\b")

PLACEHOLDER_PATTERN = re.compile(r"\{\{[^}]+\}\}")
UNFINISHED_TOKENS = ["TO" + "DO", "[TO" + "DO]", "FIX" + "ME", "T" + "BD"]
CORRUPT_QUESTION_PLACEHOLDER = "???"
FORBIDDEN_OUTPUT_TERMS = ["token", "secret", "cookie", "password", "api key"]
LOCAL_URL_PATTERN = re.compile(r"https?://(?:localhost|127\.0\.0\.1)\b", re.IGNORECASE)
FORBIDDEN_HREF_PATTERN = re.compile(
    r"(?:https?://(?:localhost|127\.0\.0\.1)\b|file://|(?<![A-Za-z])[A-Za-z]:[\\/]|[?&](?:token|key|secret|password|cookie)=)",
    re.IGNORECASE,
)
ALLOWED_AMAZON_HREF_PATTERN = re.compile(r"^https://www\.amazon\.(?:com|co\.uk|ca)(?:/|$)", re.IGNORECASE)
AMAZON_DP_HREF_PATTERN = re.compile(r"^https://www\.amazon\.(?:com|co\.uk|ca)/dp/[A-Z0-9]{10}(?:[/?#]|$)", re.IGNORECASE)
DELIVERY_PUBLISH_STATUSES = {"not_published", "local_only", "public_safe_published", "internal_published"}
DELIVERY_SHAREABLE_SCOPES = {"none", "public_safe", "internal_only"}


class HrefCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key.lower() == "href" and value is not None:
                self.hrefs.append(value)


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            errors.append(f"{path.name}: JSON root must be an object")
            return {}
        return payload
    except Exception as exc:
        errors.append(f"{path.name}: invalid JSON: {exc}")
        return {}


def check_file_set(dist: Path, errors: list[str]) -> None:
    for filename in REQUIRED_FILES:
        path = dist / filename
        if not path.exists():
            errors.append(f"missing required file: {filename}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required file: {filename}")


def check_forbidden_output_terms(filename: str, content: str, errors: list[str]) -> None:
    lowered = content.lower()
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term in lowered:
            errors.append(f"{filename} contains forbidden sensitive term: {term}")


def check_html_links(html: str, data: dict[str, Any], errors: list[str]) -> None:
    parser = HrefCollector()
    parser.feed(html)
    privacy_mode = data.get("privacy_mode")
    delivery = data.get("delivery") if isinstance(data.get("delivery"), dict) else {}
    shareable_url = delivery.get("shareable_url")
    allowed_shareable = (
        isinstance(shareable_url, str)
        and shareable_url.startswith("https://")
        and privacy_mode in {"public_safe_real_world", "strict_anonymized"}
    )
    dp_links = 0
    for href in parser.hrefs:
        stripped = href.strip()
        if not stripped:
            errors.append("HTML contains empty href")
            continue
        if FORBIDDEN_HREF_PATTERN.search(stripped):
            errors.append(f"HTML contains forbidden href: {stripped[:120]}")
            continue
        if AMAZON_DP_HREF_PATTERN.match(stripped):
            dp_links += 1
        if stripped.startswith("#"):
            continue
        if ALLOWED_AMAZON_HREF_PATTERN.match(stripped):
            continue
        if allowed_shareable and stripped.startswith(shareable_url):
            continue
        errors.append(f"HTML contains non-allowlisted href: {stripped[:120]}")
    if privacy_mode in {"public_safe_real_world", "strict_anonymized"} and dp_links:
        errors.append("public-safe HTML must not contain Amazon dp ASIN links")


def check_html(dist: Path, data: dict[str, Any], errors: list[str]) -> None:
    path = dist / "product_selection_report.html"
    if not path.exists():
        return
    html = path.read_text(encoding="utf-8", errors="replace")
    check_forbidden_output_terms(path.name, html, errors)
    for section_id in REQUIRED_SECTION_IDS:
        if f'id="{section_id}"' not in html:
            errors.append(f"HTML missing section id: {section_id}")
    upper_html = html.upper()
    if PLACEHOLDER_PATTERN.search(html) or any(token in upper_html for token in UNFINISHED_TOKENS):
        errors.append("HTML contains unresolved placeholder or unfinished marker")
    if CORRUPT_QUESTION_PLACEHOLDER in html:
        errors.append("HTML contains corrupt question-mark placeholder: ???")
    if data.get("privacy_mode") == "private_internal":
        required_notice = [
            "private_internal",
            "本地真实 Sorftime MCP 分析输出",
            "不得提交 GitHub",
            "Profit detail in public-safe fixtures is template-level only and not a live margin estimate.",
            "公开安全样例中的利润明细仅用于模板展示，不代表实时利润估算。",
        ]
    else:
        required_notice = [
            "public-safe template sample",
            "不是实时市场数据",
            "不是完整真实 Top 100",
            "不是真实 Sorftime 原始导出",
            "不代表真实选品结论",
            "Profit detail in public-safe fixtures is template-level only and not a live margin estimate.",
            "公开安全样例中的利润明细仅用于模板展示，不代表实时利润估算。",
        ]
    for phrase in required_notice:
        if phrase not in html:
            errors.append(f"HTML missing public-safe notice phrase: {phrase}")
    check_html_links(html, data, errors)


def check_optional_markdown(dist: Path, errors: list[str]) -> None:
    path = dist / "product_selection_report.md"
    if not path.exists():
        return
    if path.stat().st_size == 0:
        errors.append("empty optional markdown report: product_selection_report.md")
        return
    content = path.read_text(encoding="utf-8", errors="replace")
    check_forbidden_output_terms(path.name, content, errors)
    upper_content = content.upper()
    if PLACEHOLDER_PATTERN.search(content) or any(token in upper_content for token in UNFINISHED_TOKENS):
        errors.append("Markdown report contains unresolved placeholder or unfinished marker")
    if CORRUPT_QUESTION_PLACEHOLDER in content:
        errors.append("Markdown report contains corrupt question-mark placeholder: ???")


def check_data(data: dict[str, Any], errors: list[str]) -> None:
    check_forbidden_output_terms(
        "product_selection_data.json",
        json.dumps(data, ensure_ascii=False),
        errors,
    )
    question_paths = find_question_placeholders(data)
    for path in question_paths[:20]:
        errors.append(f"product_selection_data.json contains corrupt question-mark placeholder at {path}")
    if len(question_paths) > 20:
        errors.append(f"product_selection_data.json contains {len(question_paths) - 20} additional corrupt question-mark placeholders")
    for key in [
        "privacy_mode",
        "report_language",
        "input",
        "sorftime_status",
        "data_quality",
        "scores",
        "decision",
        "analysis",
        "evidence",
        "market_stage",
        "new_product_ramp_difficulty",
        "entry_strategy",
        "voc_productization_score",
        "disqualifiers",
        "evidence_level",
        "competitor_clusters",
        "profit_space_detail",
        *EXTENDED_MODEL_FIELDS,
        "assumptions",
        "missing_data",
        "next_validation_actions",
        "downstream_brief",
    ]:
        if key not in data:
            errors.append(f"product_selection_data.json missing field: {key}")
    decision = data.get("decision") if isinstance(data.get("decision"), dict) else {}
    if data.get("report_language") != "zh-CN":
        errors.append("product_selection_data.report_language must be zh-CN")
    blocked = decision.get("blocked_status")
    if blocked is not None and blocked not in BLOCKED_STATUSES:
        errors.append(f"invalid blocked_status in product_selection_data.json: {blocked}")
    label = decision.get("label")
    if blocked and label != "blocked":
        errors.append("blocked package decision.label must be blocked")
    if not blocked and label not in {"enter", "cautious", "weak", "no-enter"}:
        errors.append(f"invalid decision.label: {label}")
    check_model_fields(data, errors)
    analysis = data.get("analysis") if isinstance(data.get("analysis"), dict) else {}
    for key, item in analysis.items():
        if not isinstance(item, dict):
            errors.append(f"analysis.{key} must be an object")
            continue
        for required in ["conclusion", "evidence", "source", "confidence", "assumption", "missing_data"]:
            if required not in item:
                errors.append(f"analysis.{key} missing field: {required}")


def find_question_placeholders(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            findings.extend(find_question_placeholders(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_question_placeholders(child, f"{path}[{index}]"))
    elif isinstance(value, str) and CORRUPT_QUESTION_PLACEHOLDER in value:
        findings.append(path)
    return findings


def is_valid_profit_value(value: Any) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    if value in {"unknown", "template_sample"}:
        return True
    if isinstance(value, str) and RANGE_PATTERN.match(value):
        return True
    return False


def check_model_fields(data: dict[str, Any], errors: list[str]) -> None:
    if data.get("market_stage") not in MARKET_STAGES:
        errors.append(f"invalid market_stage: {data.get('market_stage')}")
    if data.get("evidence_level") not in EVIDENCE_LEVELS:
        errors.append(f"invalid evidence_level: {data.get('evidence_level')}")

    ramp = data.get("new_product_ramp_difficulty")
    if not isinstance(ramp, dict):
        errors.append("new_product_ramp_difficulty must be an object")
    else:
        for field in [
            "level",
            "ramp_reason",
            "review_threshold",
            "low_review_high_sales_count",
            "ad_dependency",
            "brand_concentration",
            "organic_ranking_barrier",
            "rating_requirement",
            "variation_complexity",
        ]:
            if field not in ramp:
                errors.append(f"new_product_ramp_difficulty missing field: {field}")
        if ramp.get("level") not in RAMP_LEVELS:
            errors.append(f"invalid new_product_ramp_difficulty.level: {ramp.get('level')}")
        if not isinstance(ramp.get("ramp_reason"), str) or not ramp.get("ramp_reason"):
            errors.append("new_product_ramp_difficulty.ramp_reason must be a non-empty string")

    entry_strategy = data.get("entry_strategy")
    if not isinstance(entry_strategy, list):
        errors.append("entry_strategy must be an array")
    else:
        for index, item in enumerate(entry_strategy):
            if not isinstance(item, dict):
                errors.append(f"entry_strategy[{index}] must be an object")
                continue
            for field in ["entry_type", "entry_point", "reason", "required_validation"]:
                if field not in item:
                    errors.append(f"entry_strategy[{index}] missing field: {field}")
            if item.get("entry_type") not in ENTRY_TYPES:
                errors.append(f"invalid entry_strategy[{index}].entry_type: {item.get('entry_type')}")
            if not isinstance(item.get("required_validation"), list):
                errors.append(f"entry_strategy[{index}].required_validation must be an array")

    voc_scores = data.get("voc_productization_score")
    if not isinstance(voc_scores, list):
        errors.append("voc_productization_score must be an array")
    else:
        for index, item in enumerate(voc_scores):
            if not isinstance(item, dict):
                errors.append(f"voc_productization_score[{index}] must be an object")
                continue
            for field in [
                "painpoint",
                "solution_feasibility",
                "buyer_willingness_to_pay",
                "cost_impact",
                "listing_visibility",
                "productization_score",
            ]:
                if field not in item:
                    errors.append(f"voc_productization_score[{index}] missing field: {field}")
            score = item.get("productization_score")
            if not isinstance(score, (int, float)) or isinstance(score, bool) or score < 0 or score > 10:
                errors.append(f"voc_productization_score[{index}].productization_score must be 0-10")

    disqualifiers = data.get("disqualifiers")
    active_critical = False
    if not isinstance(disqualifiers, list):
        errors.append("disqualifiers must be an array")
    else:
        for index, item in enumerate(disqualifiers):
            if not isinstance(item, dict):
                errors.append(f"disqualifiers[{index}] must be an object")
                continue
            for field in ["type", "status", "severity", "reason", "required_validation"]:
                if field not in item:
                    errors.append(f"disqualifiers[{index}] missing field: {field}")
            if item.get("type") not in DISQUALIFIER_TYPES:
                errors.append(f"invalid disqualifiers[{index}].type: {item.get('type')}")
            if item.get("status") not in DISQUALIFIER_STATUSES:
                errors.append(f"invalid disqualifiers[{index}].status: {item.get('status')}")
            if item.get("severity") not in DISQUALIFIER_SEVERITIES:
                errors.append(f"invalid disqualifiers[{index}].severity: {item.get('severity')}")
            if not isinstance(item.get("required_validation"), list):
                errors.append(f"disqualifiers[{index}].required_validation must be an array")
            if item.get("status") == "active" and item.get("severity") == "critical":
                active_critical = True
    decision = data.get("decision") if isinstance(data.get("decision"), dict) else {}
    if active_critical and decision.get("label") == "enter":
        errors.append("decision.label cannot be enter when an active critical disqualifier exists")

    clusters = data.get("competitor_clusters")
    if not isinstance(clusters, dict):
        errors.append("competitor_clusters must be an object")
    else:
        for cluster_key in CLUSTER_KEYS:
            values = clusters.get(cluster_key)
            if not isinstance(values, list):
                errors.append(f"competitor_clusters.{cluster_key} must be an array")
                continue
            for index, item in enumerate(values):
                if not isinstance(item, dict):
                    errors.append(f"competitor_clusters.{cluster_key}[{index}] must be an object")
                    continue
                for field in CLUSTER_ITEM_FIELDS:
                    if field not in item:
                        errors.append(f"competitor_clusters.{cluster_key}[{index}] missing field: {field}")
                if item.get("evidence_level") not in EVIDENCE_LEVELS:
                    errors.append(
                        f"invalid competitor_clusters.{cluster_key}[{index}].evidence_level: {item.get('evidence_level')}"
                    )

    profit = data.get("profit_space_detail")
    if not isinstance(profit, dict):
        errors.append("profit_space_detail must be an object")
    else:
        for field in PROFIT_FIELDS:
            if field not in profit:
                errors.append(f"profit_space_detail missing field: {field}")
                continue
            value = profit.get(field)
            if not is_valid_profit_value(value):
                errors.append(f"profit_space_detail.{field} has invalid value: {value}")
            if data.get("privacy_mode") == "public_safe_real_world" and value not in {"unknown", "template_sample"}:
                errors.append(
                    f"public_safe_real_world profit_space_detail.{field} must be unknown or template_sample"
                )
    check_extended_fields(data, errors)
    check_public_safe_identifiers(data, errors)


def require_fields(item: Any, path: str, fields: list[str], errors: list[str]) -> bool:
    if not isinstance(item, dict):
        errors.append(f"{path} must be an object")
        return False
    ok = True
    for field in fields:
        if field not in item:
            errors.append(f"{path} missing field: {field}")
            ok = False
    return ok


def check_delivery(delivery: Any, privacy_mode: Any, path: str, errors: list[str]) -> None:
    if not require_fields(
        delivery,
        path,
        [
            "local_preview_url",
            "is_localhost_only",
            "report_file_path",
            "package_zip_path",
            "publish_status",
            "shareable_url",
            "shareable_url_scope",
            "notes",
        ],
        errors,
    ):
        return
    if delivery.get("publish_status") not in DELIVERY_PUBLISH_STATUSES:
        errors.append(f"invalid {path}.publish_status: {delivery.get('publish_status')}")
    if delivery.get("shareable_url_scope") not in DELIVERY_SHAREABLE_SCOPES:
        errors.append(f"invalid {path}.shareable_url_scope: {delivery.get('shareable_url_scope')}")
    if not isinstance(delivery.get("is_localhost_only"), bool):
        errors.append(f"{path}.is_localhost_only must be boolean")
    local_preview = delivery.get("local_preview_url")
    shareable_url = delivery.get("shareable_url")
    if isinstance(local_preview, str) and LOCAL_URL_PATTERN.search(local_preview) and delivery.get("is_localhost_only") is not True:
        errors.append(f"{path}.local_preview_url uses localhost but is_localhost_only is not true")
    if isinstance(shareable_url, str) and LOCAL_URL_PATTERN.search(shareable_url):
        errors.append(f"{path}.shareable_url must not use localhost or 127.0.0.1")
    if shareable_url in {"", None} and delivery.get("shareable_url_scope") != "none":
        errors.append(f"{path}.shareable_url_scope must be none when shareable_url is empty")
    if privacy_mode == "private_internal":
        if delivery.get("shareable_url_scope") in {"public", "public_safe"}:
            errors.append(f"{path}: private_internal must not expose a public shareable URL")
        if delivery.get("publish_status") == "public_safe_published":
            errors.append(f"{path}: private_internal must not use public_safe_published")


def check_profit_value_fields(item: dict[str, Any], path: str, fields: list[str], privacy_mode: str, errors: list[str]) -> None:
    for field in fields:
        if field not in item:
            continue
        value = item.get(field)
        if not is_valid_profit_value(value):
            errors.append(f"{path}.{field} has invalid value: {value}")
        if privacy_mode == "public_safe_real_world" and value not in {"unknown", "template_sample"}:
            errors.append(f"public_safe_real_world {path}.{field} must be unknown or template_sample")


def check_extended_fields(data: dict[str, Any], errors: list[str]) -> None:
    privacy_mode = data.get("privacy_mode")
    coverage = data.get("data_coverage_score")
    if require_fields(
        coverage,
        "data_coverage_score",
        ["score", "status", "ready_blocks", "total_blocks", "missing_blocks", "field_coverage", "missing_fields"],
        errors,
    ):
        if not isinstance(coverage.get("score"), (int, float)) or not 0 <= coverage.get("score") <= 100:
            errors.append("data_coverage_score.score must be 0-100")
        if coverage.get("status") not in {"high", "medium", "low", "blocked"}:
            errors.append(f"invalid data_coverage_score.status: {coverage.get('status')}")
        if not isinstance(coverage.get("ready_blocks"), int) or not isinstance(coverage.get("total_blocks"), int):
            errors.append("data_coverage_score ready_blocks and total_blocks must be integers")
        if not isinstance(coverage.get("missing_blocks"), list) or not isinstance(coverage.get("missing_fields"), list):
            errors.append("data_coverage_score missing_blocks and missing_fields must be arrays")
        if not isinstance(coverage.get("field_coverage"), (int, float)) or not 0 <= coverage.get("field_coverage") <= 1:
            errors.append("data_coverage_score.field_coverage must be 0-1")

    profit_scenarios = data.get("profit_scenarios")
    if not isinstance(profit_scenarios, list):
        errors.append("profit_scenarios must be an array")
    else:
        for index, item in enumerate(profit_scenarios):
            path = f"profit_scenarios[{index}]"
            if require_fields(
                item,
                path,
                ["scenario", "target_price", "estimated_landed_cost", "fees", "ad_cost", "return_loss", "target_margin", "conclusion", "evidence_level"],
                errors,
            ):
                check_profit_value_fields(
                    item,
                    path,
                    ["target_price", "estimated_landed_cost", "fees", "ad_cost", "return_loss", "target_margin"],
                    privacy_mode,
                    errors,
                )
                if item.get("evidence_level") not in EVIDENCE_LEVELS:
                    errors.append(f"invalid {path}.evidence_level: {item.get('evidence_level')}")

    ramp_path = data.get("ramp_path")
    if not isinstance(ramp_path, list):
        errors.append("ramp_path must be an array")
    else:
        for index, item in enumerate(ramp_path):
            path = f"ramp_path[{index}]"
            if require_fields(item, path, ["stage", "goal", "actions", "validation_standard", "risk"], errors):
                if not isinstance(item.get("actions"), list):
                    errors.append(f"{path}.actions must be an array")

    voc_matrix = data.get("voc_opportunity_matrix")
    if not isinstance(voc_matrix, list):
        errors.append("voc_opportunity_matrix must be an array")
    else:
        for index, item in enumerate(voc_matrix):
            path = f"voc_opportunity_matrix[{index}]"
            if require_fields(
                item,
                path,
                ["painpoint", "frequency_signal", "buyer_motive", "product_action", "listing_message", "priority", "evidence_level"],
                errors,
            ) and item.get("evidence_level") not in EVIDENCE_LEVELS:
                errors.append(f"invalid {path}.evidence_level: {item.get('evidence_level')}")

    validation_plan = data.get("validation_plan")
    if not isinstance(validation_plan, list):
        errors.append("validation_plan must be an array")
    else:
        for index, item in enumerate(validation_plan):
            path = f"validation_plan[{index}]"
            if require_fields(
                item,
                path,
                ["validation_item", "method", "pass_standard", "priority", "blocked_if_missing"],
                errors,
            ) and not isinstance(item.get("blocked_if_missing"), bool):
                errors.append(f"{path}.blocked_if_missing must be boolean")

    signals = data.get("trending_product_signals")
    if require_fields(
        signals,
        "trending_product_signals",
        [
            "new_product_count",
            "low_review_high_sales_count",
            "recent_launch_success_cases",
            "rising_keywords",
            "seasonal_peak_months",
            "product_format_shift",
            "buyer_need_shift",
            "trend_strength_score",
        ],
        errors,
    ):
        for field in ["recent_launch_success_cases", "rising_keywords", "seasonal_peak_months"]:
            if not isinstance(signals.get(field), list):
                errors.append(f"trending_product_signals.{field} must be an array")
        score = signals.get("trend_strength_score")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or score < 0 or score > 100:
            errors.append("trending_product_signals.trend_strength_score must be 0-100")

    voc_summary = data.get("voc_trend_summary")
    if require_fields(voc_summary, "voc_trend_summary", ["summary", "trend_direction", "evidence", "missing_data"], errors):
        if not isinstance(voc_summary.get("evidence"), list) or not isinstance(voc_summary.get("missing_data"), list):
            errors.append("voc_trend_summary.evidence and missing_data must be arrays")

    product_actions = data.get("product_action_plan")
    if not isinstance(product_actions, list):
        errors.append("product_action_plan must be an array")
    else:
        for index, item in enumerate(product_actions):
            path = f"product_action_plan[{index}]"
            if require_fields(item, path, ["action", "why", "validation", "priority", "evidence_level"], errors):
                if item.get("evidence_level") not in EVIDENCE_LEVELS:
                    errors.append(f"invalid {path}.evidence_level: {item.get('evidence_level')}")

    package = data.get("report_delivery_package")
    if require_fields(
        package,
        "report_delivery_package",
        ["primary_report", "data_package", "source_manifest", "validation_result", "optional_markdown_report", "optional_charts_manifest", "package_zip_path", "privacy_mode", "delivery_notes"],
        errors,
    ):
        if package.get("privacy_mode") not in {"public_safe_real_world", "strict_anonymized", "private_internal"}:
            errors.append(f"invalid report_delivery_package.privacy_mode: {package.get('privacy_mode')}")

    check_delivery(data.get("delivery"), data.get("privacy_mode"), "product_selection_data.delivery", errors)

    charts = data.get("optional_charts_manifest")
    if require_fields(charts, "optional_charts_manifest", ["enabled", "charts_dir", "items", "note"], errors):
        if not isinstance(charts.get("enabled"), bool):
            errors.append("optional_charts_manifest.enabled must be boolean")
        if not isinstance(charts.get("items"), list):
            errors.append("optional_charts_manifest.items must be an array")


def check_public_safe_identifiers(data: dict[str, Any], errors: list[str]) -> None:
    if data.get("privacy_mode") != "public_safe_real_world":
        return
    blocks = data.get("normalized_blocks") if isinstance(data.get("normalized_blocks"), dict) else {}
    competitors = blocks.get("competitors")
    if not isinstance(competitors, list):
        return
    for index, item in enumerate(competitors):
        if not isinstance(item, dict):
            continue
        asin = item.get("asin")
        if isinstance(asin, str) and REAL_ASIN_PATTERN.search(asin) and not asin.startswith("example_asin_"):
            errors.append(f"public_safe_real_world competitor[{index}].asin looks like a real ASIN")


def check_manifest(manifest: dict[str, Any], data: dict[str, Any], errors: list[str]) -> None:
    check_forbidden_output_terms(
        "source_manifest.json",
        json.dumps(manifest, ensure_ascii=False),
        errors,
    )
    for key in REQUIRED_MANIFEST_FIELDS:
        if key not in manifest:
            errors.append(f"source_manifest.json missing field: {key}")
    if manifest.get("no_user_private_data") is not True:
        errors.append("source_manifest.no_user_private_data must be true")
    if manifest.get("contains_user_private_data") is not False:
        errors.append("source_manifest.contains_user_private_data must be false")
    if manifest.get("contains_raw_sorftime_export") is not False:
        errors.append("source_manifest.contains_raw_sorftime_export must be false")
    if manifest.get("contains_review_text") is not False:
        errors.append("source_manifest.contains_review_text must be false")
    if manifest.get("public_data_reference") is not True:
        errors.append("source_manifest.public_data_reference must be true")
    if manifest.get("report_language") != "zh-CN":
        errors.append("source_manifest.report_language must be zh-CN")
    if manifest.get("data_freshness") not in DATA_FRESHNESS_VALUES:
        errors.append("source_manifest.data_freshness has invalid value")
    if manifest.get("privacy_mode") in {"public_safe_real_world", "strict_anonymized"} and manifest.get("data_freshness") != "template_sample_not_live_market_data":
        errors.append("public-safe source_manifest.data_freshness must be template_sample_not_live_market_data")
    if manifest.get("privacy_mode") == "private_internal" and manifest.get("data_freshness") != "live_or_latest_available_sorftime_data":
        errors.append("private_internal source_manifest.data_freshness must be live_or_latest_available_sorftime_data")
    blocked = manifest.get("blocked_status")
    if blocked is not None and blocked not in BLOCKED_STATUSES:
        errors.append(f"invalid blocked_status in source_manifest.json: {blocked}")
    data_blocked = (data.get("decision") or {}).get("blocked_status") if isinstance(data.get("decision"), dict) else None
    if blocked != data_blocked:
        errors.append("source_manifest.blocked_status must match product_selection_data decision.blocked_status")
    check_delivery(manifest.get("delivery"), manifest.get("privacy_mode"), "source_manifest.delivery", errors)


def check_delivery_zip(dist: Path, data: dict[str, Any], manifest: dict[str, Any], errors: list[str]) -> None:
    delivery = data.get("delivery") if isinstance(data.get("delivery"), dict) else {}
    zip_name = delivery.get("package_zip_path") or "product_selection_delivery_package.zip"
    zip_path = Path(str(zip_name))
    if not zip_path.is_absolute():
        zip_path = dist / zip_path.name
    if not zip_path.exists():
        return
    required = {
        "product_selection_report.html",
        "product_selection_report.md",
        "product_selection_data.json",
        "source_manifest.json",
        "validation_result.json",
        "README_OPEN_REPORT.txt",
    }
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
            missing = sorted(required - names)
            if missing:
                errors.append(f"delivery ZIP missing files: {', '.join(missing)}")
            if "README_OPEN_REPORT.txt" in names:
                readme = archive.read("README_OPEN_REPORT.txt").decode("utf-8", errors="replace")
                if "product_selection_report.html" not in readme:
                    errors.append("README_OPEN_REPORT.txt must explain opening product_selection_report.html")
                if manifest.get("privacy_mode") == "private_internal" and "不得上传 GitHub" not in readme:
                    errors.append("private_internal README_OPEN_REPORT.txt must include GitHub/public sharing warning")
    except Exception as exc:
        errors.append(f"invalid delivery ZIP: {exc}")


def check_existing_validation_result(dist: Path, privacy_mode: Any, errors: list[str]) -> None:
    path = dist / "validation_result.json"
    if not path.exists():
        return
    existing = load_json(path, errors)
    delivery = existing.get("delivery") if isinstance(existing.get("delivery"), dict) else None
    if delivery is not None:
        check_delivery(delivery, privacy_mode, "validation_result.delivery", errors)


def write_result(dist: Path, errors: list[str]) -> None:
    delivery: dict[str, Any] = {}
    manifest_path = dist / "source_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(manifest, dict) and isinstance(manifest.get("delivery"), dict):
                delivery = manifest["delivery"]
        except Exception:
            delivery = {}
    result = {
        "ok": not errors,
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "required_files": REQUIRED_FILES,
        "delivery": delivery,
        "errors": errors,
    }
    with (dist / "validation_result.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a product selection dist package.")
    parser.add_argument("dist_dir", help="Directory containing the generated dist files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dist = Path(args.dist_dir)
    errors: list[str] = []
    if not dist.exists() or not dist.is_dir():
        errors.append("dist directory does not exist")
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False))
        return 1

    check_file_set(dist, errors)
    data = load_json(dist / "product_selection_data.json", errors) if (dist / "product_selection_data.json").exists() else {}
    manifest = load_json(dist / "source_manifest.json", errors) if (dist / "source_manifest.json").exists() else {}
    check_html(dist, data, errors)
    check_optional_markdown(dist, errors)
    check_data(data, errors)
    check_manifest(manifest, data, errors)
    check_delivery_zip(dist, data, manifest, errors)
    check_existing_validation_result(dist, data.get("privacy_mode") or manifest.get("privacy_mode"), errors)
    write_result(dist, errors)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
