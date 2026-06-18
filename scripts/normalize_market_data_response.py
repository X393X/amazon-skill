#!/usr/bin/env python3
"""Normalize BYO-MCP provider-response market data into a product selection package."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_PRIVACY_MODES = {"public_safe_real_world", "strict_anonymized", "private_internal"}
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
TEMPLATE_DATA_FRESHNESS = "template_sample_not_live_market_data"
LIVE_DATA_FRESHNESS = "live_or_latest_available_sorftime_data"
DEFAULT_REPORT_LANGUAGE = "zh-CN"
SOURCE_NAME = "BYO MCP provider response"
PUBLIC_SAFE_SOURCE_NAME = "public-safe normalized provider response"

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
    "delivery",
    "optional_charts_manifest",
]

SCORE_DIMENSIONS = [
    ("demand_capacity", "需求容量", 20),
    ("competition_entry", "竞争强度", 20),
    ("profit_space", "利润空间", 20),
    ("differentiation_opportunity", "差异化机会", 15),
    ("voc_painpoint_opportunity", "VOC 痛点机会", 10),
    ("keyword_entry", "关键词入口", 10),
    ("compliance_supply_risk", "合规与供应链风险", 5),
]

ANALYSIS_KEYS = [
    "category_capacity",
    "keyword_opportunity",
    "competitor_structure",
    "price_profit",
    "review_voc",
    "differentiation",
    "risk",
]

SECTION_LABELS = {
    "category_capacity": "类目容量判断",
    "keyword_opportunity": "关键词机会判断",
    "competitor_structure": "竞品结构判断",
    "price_profit": "价格带与利润判断",
    "review_voc": "评论 VOC 痛点判断",
    "differentiation": "差异化机会判断",
    "risk": "风险判断",
}

REQUIRED_BLOCKS = [
    "market_capacity",
    "keywords",
    "competitors",
    "price_profit",
    "voc",
    "differentiation",
    "risks",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Input JSON root must be an object.")
    return payload


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def as_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value
    return str(value)


def normalize_site(value: Any, marketplace: Any = None) -> str:
    raw = as_text(value).strip()
    if raw:
        return raw
    market = as_text(marketplace).strip().upper()
    if market == "US":
        return "Amazon US"
    if market:
        return f"Amazon {market}"
    return "Amazon US"


def collect_input(raw: dict[str, Any]) -> dict[str, Any]:
    embedded = raw.get("input") if isinstance(raw.get("input"), dict) else {}
    top_keys = [
        "keyword",
        "category",
        "category_name",
        "category_node_id",
        "category_url",
        "category_scope",
        "marketplace",
        "site",
        "input_type",
        "data_scope",
        "data_source",
        "asin",
        "product_idea",
        "target_price",
        "target_cost",
        "constraints",
        "output_format",
        "report_language",
    ]
    merged = {key: raw.get(key) for key in top_keys if key in raw}
    merged.update(embedded)
    return merged


def safe_input(raw_input: dict[str, Any], privacy_mode: str) -> dict[str, Any]:
    result = {
        "keyword": raw_input.get("keyword"),
        "category": raw_input.get("category") or raw_input.get("category_name"),
        "category_name": raw_input.get("category_name") or raw_input.get("category"),
        "category_node_id": raw_input.get("category_node_id"),
        "category_url": raw_input.get("category_url"),
        "category_scope": raw_input.get("category_scope"),
        "marketplace": raw_input.get("marketplace"),
        "input_type": raw_input.get("input_type"),
        "data_scope": raw_input.get("data_scope"),
        "data_source": raw_input.get("data_source"),
        "asin": as_list(raw_input.get("asin")),
        "product_idea": raw_input.get("product_idea"),
        "site": normalize_site(raw_input.get("site"), raw_input.get("marketplace")),
        "target_price": raw_input.get("target_price"),
        "target_cost": raw_input.get("target_cost"),
        "constraints": as_list(raw_input.get("constraints")),
        "output_format": raw_input.get("output_format"),
        "report_language": raw_input.get("report_language") or DEFAULT_REPORT_LANGUAGE,
    }
    if privacy_mode in {"public_safe_real_world", "strict_anonymized"}:
        result["asin"] = [
            f"example_asin_input_{index:03d}" for index, _ in enumerate(result["asin"], start=1)
        ]
    if privacy_mode == "strict_anonymized":
        result["keyword"] = "example keyword"
        result["category"] = "example category"
        result["product_idea"] = "example product idea"
    return result


def anonymize_competitors(raw_competitors: list[Any], privacy_mode: str) -> list[dict[str, Any]]:
    competitors: list[dict[str, Any]] = []
    for index, item in enumerate(raw_competitors, start=1):
        source = item if isinstance(item, dict) else {"title": as_text(item)}
        if privacy_mode in {"public_safe_real_world", "strict_anonymized"}:
            brand_suffix = chr(96 + index) if 1 <= index <= 26 else str(index)
            competitors.append(
                {
                    "competitor_id": f"example_competitor_{index:03d}",
                    "asin": f"example_asin_{index:03d}",
                    "brand": f"example_brand_{brand_suffix}",
                    "positioning": source.get("positioning") or f"example product cluster {index:03d}",
                    "price_band": source.get("price_band"),
                    "review_band": source.get("review_band"),
                    "rating_band": source.get("rating_band"),
                }
            )
        else:
            competitors.append(
                {
                    "competitor_id": source.get("competitor_id") or f"internal_competitor_{index:03d}",
                    "asin": source.get("asin"),
                    "brand": source.get("brand"),
                    "title": source.get("title") or source.get("product_title") or source.get("name"),
                    "positioning": source.get("positioning") or source.get("title"),
                    "price_band": source.get("price_band"),
                    "review_band": source.get("review_band"),
                    "rating_band": source.get("rating_band"),
                }
            )
    return competitors


def non_empty_block(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, dict):
        return any(non_empty_block(child) for child in value.values())
    if isinstance(value, list):
        return any(non_empty_block(child) for child in value)
    if isinstance(value, str):
        return bool(value.strip())
    return True


def infer_blocked_status(raw: dict[str, Any]) -> str | None:
    status = raw.get("sorftime_status") if isinstance(raw.get("sorftime_status"), dict) else {}
    explicit = raw.get("blocked_status") or status.get("blocking_status")
    if explicit in BLOCKED_STATUSES:
        return explicit
    status_text = as_text(status.get("status") or raw.get("status")).lower()
    if status.get("available") is False or status_text in {"unavailable", "failed", "error"}:
        return "blocked_sorftime_unavailable"
    if raw.get("required_fields_present") is False:
        return "blocked_missing_fields"
    if not any(non_empty_block(raw.get(block)) for block in REQUIRED_BLOCKS):
        return "blocked_no_data"
    missing = as_list(raw.get("missing_fields")) + as_list(status.get("missing_fields"))
    critical_missing = [item for item in missing if as_text(item).strip()]
    if critical_missing and raw.get("allow_partial") is not True:
        return "blocked_missing_fields"
    return None


def data_blocks(raw: dict[str, Any]) -> list[dict[str, Any]]:
    blocks = raw.get("data_blocks")
    if isinstance(blocks, list):
        return [block for block in blocks if isinstance(block, dict)]
    generated: list[dict[str, Any]] = []
    for block in REQUIRED_BLOCKS:
        value = raw.get(block)
        record_count = len(value) if isinstance(value, list) else (1 if non_empty_block(value) else 0)
        generated.append(
            {
                "name": block,
                "status": "ready" if record_count else "missing",
                "record_count": record_count,
                "field_coverage": 1.0 if record_count else 0.0,
            }
        )
    return generated


def build_query(input_data: dict[str, Any], raw_input: dict[str, Any]) -> dict[str, Any]:
    query = {
        "marketplace": input_data.get("marketplace") or raw_input.get("marketplace"),
        "site": input_data.get("site"),
        "input_type": input_data.get("input_type") or raw_input.get("input_type"),
        "keyword": input_data.get("keyword"),
        "category": input_data.get("category"),
        "category_name": input_data.get("category_name") or input_data.get("category"),
        "category_node_id": input_data.get("category_node_id"),
        "category_url": input_data.get("category_url"),
        "category_scope": input_data.get("category_scope"),
        "data_scope": input_data.get("data_scope"),
        "data_source": input_data.get("data_source"),
        "product_idea": input_data.get("product_idea"),
        "asin_count": len(as_list(input_data.get("asin"))),
        "asin_policy": "anonymized_or_not_supplied",
    }
    return {key: value for key, value in query.items() if value not in (None, "", [])}


def score_label(total: float) -> str:
    if total >= 80:
        return "enter"
    if total >= 65:
        return "cautious"
    if total >= 50:
        return "weak"
    return "no-enter"


def evidence_level(raw: dict[str, Any], blocked_status: str | None, privacy_mode: str) -> str:
    value = raw.get("evidence_level")
    if value:
        return as_text(value)
    if blocked_status:
        return "D_assumption"
    if privacy_mode == "private_internal":
        return "A_live_market_data"
    if privacy_mode == "public_safe_real_world":
        return "C_public_safe_template"
    return "B_provider_aggregate"


def data_freshness(raw: dict[str, Any], privacy_mode: str) -> str:
    value = as_text(raw.get("data_freshness")).strip()
    allowed = {TEMPLATE_DATA_FRESHNESS, LIVE_DATA_FRESHNESS}
    if value in allowed:
        return value
    if privacy_mode == "private_internal":
        return LIVE_DATA_FRESHNESS
    return TEMPLATE_DATA_FRESHNESS


def source_name_for(privacy_mode: str) -> str:
    return SOURCE_NAME if privacy_mode == "private_internal" else PUBLIC_SAFE_SOURCE_NAME


def build_market_stage(raw: dict[str, Any], blocked_status: str | None) -> str:
    if blocked_status:
        return "unknown"
    return as_text(raw.get("market_stage"), "unknown")


def build_ramp_difficulty(raw: dict[str, Any], blocked_status: str | None) -> dict[str, Any]:
    source = raw.get("new_product_ramp_difficulty")
    if not isinstance(source, dict):
        source = {}
    if blocked_status:
        return {
            "level": "very_high",
            "ramp_reason": "Blocked package: ramp difficulty cannot be validated without usable provider evidence.",
            "review_threshold": "unknown",
            "low_review_high_sales_count": "unknown",
            "ad_dependency": "unknown",
            "brand_concentration": "unknown",
            "organic_ranking_barrier": "unknown",
            "rating_requirement": "unknown",
            "variation_complexity": "unknown",
        }
    return {
        "level": as_text(source.get("level"), "medium"),
        "ramp_reason": as_text(
            source.get("ramp_reason"),
            "Template-level ramp assessment; validate with local provider evidence before acting.",
        ),
        "review_threshold": source.get("review_threshold", "template_sample"),
        "low_review_high_sales_count": source.get("low_review_high_sales_count", "template_sample"),
        "ad_dependency": source.get("ad_dependency", "template_sample"),
        "brand_concentration": source.get("brand_concentration", "template_sample"),
        "organic_ranking_barrier": source.get("organic_ranking_barrier", "template_sample"),
        "rating_requirement": source.get("rating_requirement", "template_sample"),
        "variation_complexity": source.get("variation_complexity", "template_sample"),
    }


def build_entry_strategy(raw: dict[str, Any], blocked_status: str | None) -> list[dict[str, Any]]:
    if blocked_status:
        return []
    source = raw.get("entry_strategy")
    if isinstance(source, dict):
        source = [source]
    if not isinstance(source, list) or not source:
        return [
            {
                "entry_type": "keyword_wedge",
                "entry_point": "public-safe keyword segment",
                "reason": "Default template entry route; validate with local provider data.",
                "required_validation": ["local provider keyword evidence", "product fact confirmation"],
            }
        ]
    result: list[dict[str, Any]] = []
    for item in source:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "entry_type": as_text(item.get("entry_type"), "keyword_wedge"),
                "entry_point": as_text(item.get("entry_point"), "template entry point"),
                "reason": as_text(item.get("reason"), "Template entry strategy."),
                "required_validation": [
                    as_text(value) for value in as_list(item.get("required_validation")) if as_text(value).strip()
                ],
            }
        )
    return result


def build_voc_productization(raw: dict[str, Any], blocked_status: str | None) -> list[dict[str, Any]]:
    if blocked_status:
        return []
    source = raw.get("voc_productization_score")
    if isinstance(source, dict):
        source = [source]
    if not isinstance(source, list) or not source:
        voc = raw.get("voc") if isinstance(raw.get("voc"), dict) else {}
        source = [
            {"painpoint": painpoint}
            for painpoint in as_list(voc.get("painpoint_summary"))
            if as_text(painpoint).strip()
        ]
    result: list[dict[str, Any]] = []
    for item in source:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "painpoint": as_text(item.get("painpoint"), "template VOC pain point"),
                "solution_feasibility": as_text(item.get("solution_feasibility"), "template_sample"),
                "buyer_willingness_to_pay": as_text(item.get("buyer_willingness_to_pay"), "template_sample"),
                "cost_impact": as_text(item.get("cost_impact"), "template_sample"),
                "listing_visibility": as_text(item.get("listing_visibility"), "template_sample"),
                "productization_score": item.get("productization_score", 5),
            }
        )
    return result


def build_disqualifiers(raw: dict[str, Any], blocked_status: str | None) -> list[dict[str, Any]]:
    source = raw.get("disqualifiers")
    if isinstance(source, dict):
        source = [source]
    if not isinstance(source, list) or not source:
        if blocked_status:
            return [
                {
                    "type": "data_unreliable",
                    "status": "active",
                    "severity": "critical",
                    "reason": f"Package is blocked by {blocked_status}.",
                    "required_validation": ["restore usable provider evidence"],
                }
            ]
        return [
            {
                "type": "data_unreliable",
                "status": "inactive",
                "severity": "info",
                "reason": "Public-safe template sample requires live validation before action.",
                "required_validation": ["local BYO-MCP provider response"],
            }
        ]
    result: list[dict[str, Any]] = []
    for item in source:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "type": as_text(item.get("type"), "data_unreliable"),
                "status": as_text(item.get("status"), "unknown"),
                "severity": as_text(item.get("severity"), "warning"),
                "reason": as_text(item.get("reason"), "Template disqualifier note."),
                "required_validation": [
                    as_text(value) for value in as_list(item.get("required_validation")) if as_text(value).strip()
                ],
            }
        )
    return result


def has_active_critical_disqualifier(disqualifiers: list[dict[str, Any]]) -> bool:
    return any(
        item.get("status") == "active" and item.get("severity") == "critical"
        for item in disqualifiers
    )


def build_competitor_clusters(raw: dict[str, Any], blocked_status: str | None, level: str) -> dict[str, list[dict[str, Any]]]:
    source = raw.get("competitor_clusters") if isinstance(raw.get("competitor_clusters"), dict) else {}
    clusters: dict[str, list[dict[str, Any]]] = {}
    for key in CLUSTER_KEYS:
        values = source.get(key)
        if isinstance(values, dict):
            values = [values]
        if not isinstance(values, list):
            values = []
        cluster_items: list[dict[str, Any]] = []
        for item in values:
            if not isinstance(item, dict):
                continue
            cluster_items.append(
                {
                    "cluster_name": as_text(item.get("cluster_name"), key),
                    "summary": as_text(item.get("summary"), "Template competitor cluster."),
                    "competition_pressure": as_text(item.get("competition_pressure"), "unknown"),
                    "entry_implication": as_text(item.get("entry_implication"), "Validate before entry."),
                    "evidence_level": as_text(item.get("evidence_level"), level),
                }
            )
        clusters[key] = cluster_items
    return clusters


def build_profit_space_detail(raw: dict[str, Any], blocked_status: str | None, privacy_mode: str) -> dict[str, Any]:
    source = raw.get("profit_space_detail") if isinstance(raw.get("profit_space_detail"), dict) else {}
    if blocked_status:
        return {field: "unknown" for field in PROFIT_FIELDS}
    if not source and privacy_mode == "public_safe_real_world":
        return {
            "target_price": "template_sample",
            "estimated_landed_cost": "template_sample",
            "amazon_fee": "unknown",
            "fba_fee": "unknown",
            "return_loss": "unknown",
            "promotion_buffer": "template_sample",
            "ad_cost_tolerance": "template_sample",
            "target_margin": "unknown",
        }
    return {field: source.get(field, "unknown") for field in PROFIT_FIELDS}


def build_data_coverage_score(
    blocks: list[dict[str, Any]],
    blocked_status: str | None,
    missing_fields: list[str],
) -> dict[str, Any]:
    total_blocks = len(blocks)
    ready_blocks = [
        block for block in blocks
        if as_text(block.get("status")).lower() in {"ready", "success", "ok", "partial"}
        and int(block.get("record_count") or 0) > 0
    ]
    coverage = (
        sum(float(block.get("field_coverage") or 0) for block in blocks) / max(total_blocks, 1)
    )
    block_score = len(ready_blocks) / max(total_blocks, 1)
    score = 0 if blocked_status else round((coverage * 0.55 + block_score * 0.45) * 100, 1)
    return {
        "score": score,
        "status": "blocked" if blocked_status else ("high" if score >= 80 else "medium" if score >= 55 else "low"),
        "ready_blocks": len(ready_blocks),
        "total_blocks": total_blocks,
        "missing_blocks": [
            as_text(block.get("name"), "unknown")
            for block in blocks
            if block not in ready_blocks
        ],
        "field_coverage": round(coverage, 4),
        "missing_fields": missing_fields,
    }


def build_profit_scenarios(
    raw: dict[str, Any],
    blocked_status: str | None,
    privacy_mode: str,
    profit_detail: dict[str, Any],
) -> list[dict[str, Any]]:
    source = raw.get("profit_scenarios")
    if isinstance(source, dict):
        source = [source]
    if isinstance(source, list) and source:
        return [item for item in source if isinstance(item, dict)]
    if blocked_status:
        return [
            {
                "scenario": "blocked",
                "target_price": "unknown",
                "estimated_landed_cost": "unknown",
                "fees": "unknown",
                "ad_cost": "unknown",
                "return_loss": "unknown",
                "target_margin": "unknown",
                "conclusion": "阻断状态下不能推导利润情景。",
                "evidence_level": "D_assumption",
            }
        ]
    if privacy_mode in {"public_safe_real_world", "strict_anonymized"}:
        return [
            {
                "scenario": name,
                "target_price": "template_sample",
                "estimated_landed_cost": "unknown",
                "fees": "unknown",
                "ad_cost": "unknown",
                "return_loss": "unknown",
                "target_margin": "unknown",
                "conclusion": "公开安全样例只展示利润情景结构，不代表实时利润估算。",
                "evidence_level": "C_public_safe_template",
            }
            for name in ["conservative", "base", "aggressive"]
        ]
    return [
        {
            "scenario": "conservative",
            "target_price": profit_detail.get("target_price", "unknown"),
            "estimated_landed_cost": profit_detail.get("estimated_landed_cost", "unknown"),
            "fees": "unknown",
            "ad_cost": profit_detail.get("ad_cost_tolerance", "unknown"),
            "return_loss": profit_detail.get("return_loss", "unknown"),
            "target_margin": profit_detail.get("target_margin", "unknown"),
            "conclusion": "保守情景必须先补采购成本、FBA fee、退货损耗和广告成本。",
            "evidence_level": "A_live_market_data",
        },
        {
            "scenario": "base",
            "target_price": profit_detail.get("target_price", "unknown"),
            "estimated_landed_cost": profit_detail.get("estimated_landed_cost", "unknown"),
            "fees": "unknown",
            "ad_cost": profit_detail.get("ad_cost_tolerance", "unknown"),
            "return_loss": profit_detail.get("return_loss", "unknown"),
            "target_margin": profit_detail.get("target_margin", "unknown"),
            "conclusion": "基准情景只作为验证框架，不把 provider 毛利字段等同于真实净利。",
            "evidence_level": "A_live_market_data",
        },
        {
            "scenario": "aggressive",
            "target_price": profit_detail.get("target_price", "unknown"),
            "estimated_landed_cost": profit_detail.get("estimated_landed_cost", "unknown"),
            "fees": "unknown",
            "ad_cost": profit_detail.get("ad_cost_tolerance", "unknown"),
            "return_loss": profit_detail.get("return_loss", "unknown"),
            "target_margin": profit_detail.get("target_margin", "unknown"),
            "conclusion": "进取情景需在广告和促销容忍度验证后再评估。",
            "evidence_level": "A_live_market_data",
        },
    ]


def build_ramp_path(raw: dict[str, Any], blocked_status: str | None) -> list[dict[str, Any]]:
    source = raw.get("ramp_path")
    if isinstance(source, dict):
        source = [source]
    if isinstance(source, list) and source:
        return [item for item in source if isinstance(item, dict)]
    if blocked_status:
        return [
            {
                "stage": "blocked",
                "goal": "恢复可用 provider 证据",
                "actions": ["补齐阻断字段", "重新生成报告包"],
                "validation_standard": f"blocked_status 解除：{blocked_status}",
                "risk": "数据不可用时不能进入打样或 Listing 执行。",
            }
        ]
    return [
        {
            "stage": "validation",
            "goal": "验证是否存在低评论高销量和可切入长尾词",
            "actions": ["扩展关键词与 SERP", "复核 Top20 竞品", "扩展摘要化 VOC"],
            "validation_standard": "找到明确场景词、可承受 CPC 和低评论起量样本。",
            "risk": "如果入口词被品牌和高评论老品压制，停止投入。",
        },
        {
            "stage": "sample",
            "goal": "验证产品化痛点与供应链可行性",
            "actions": ["打样舒适度/耐用性/连接稳定性", "核算 landed cost 与 FBA fee", "完成认证与专利初筛"],
            "validation_standard": "样品指标、成本和合规风险均达到上线门槛。",
            "risk": "不能用页面文案弥补硬件体验缺陷。",
        },
        {
            "stage": "launch_test",
            "goal": "小批量测试转化和退货风险",
            "actions": ["小预算广告测试", "监控评价和退货", "根据 VOC 调整页面与产品"],
            "validation_standard": "转化、ACOS、退货率和星级均进入可放量区间。",
            "risk": "若早期评价低于类目门槛，应停止放量。",
        },
    ]


def build_voc_opportunity_matrix(raw: dict[str, Any], blocked_status: str | None, voc_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source = raw.get("voc_opportunity_matrix")
    if isinstance(source, dict):
        source = [source]
    if isinstance(source, list) and source:
        return [item for item in source if isinstance(item, dict)]
    if blocked_status:
        return []
    matrix: list[dict[str, Any]] = []
    for index, item in enumerate(voc_scores, start=1):
        painpoint = as_text(item.get("painpoint"), f"VOC pain point {index}")
        score = item.get("productization_score", 0)
        matrix.append(
            {
                "painpoint": painpoint,
                "frequency_signal": as_text(item.get("frequency_level"), "template_sample"),
                "buyer_motive": "降低差评风险并提升购买信任",
                "product_action": f"围绕「{painpoint}」定义材料、结构、质检或功能验证动作。",
                "listing_message": f"页面只表达已验证的「{painpoint}」改进，不夸大性能 claim。",
                "priority": "high" if isinstance(score, (int, float)) and score >= 7 else "medium",
                "evidence_level": as_text(item.get("evidence_level"), "A_live_market_data"),
            }
        )
    return matrix


def build_validation_plan(raw: dict[str, Any], blocked_status: str | None, next_actions: list[str]) -> list[dict[str, Any]]:
    source = raw.get("validation_plan")
    if isinstance(source, dict):
        source = [source]
    if isinstance(source, list) and source:
        return [item for item in source if isinstance(item, dict)]
    if blocked_status:
        return [
            {
                "validation_item": "Provider response 数据可用性",
                "method": "重新获取本地 provider response 并检查字段覆盖",
                "pass_standard": "必须解除 blocked_status 并生成完整 dist 包。",
                "priority": "critical",
                "blocked_if_missing": True,
            }
        ]
    actions = next_actions or ["补充 provider response 数据", "补充成本、认证、供应链事实"]
    return [
        {
            "validation_item": action,
            "method": "按 provider response、供应链报价或人工核验材料执行二次验证",
            "pass_standard": "可形成明确 enter/cautious/weak/no-enter 复核依据。",
            "priority": "high" if index <= 2 else "medium",
            "blocked_if_missing": index <= 2,
        }
        for index, action in enumerate(actions, start=1)
    ]


def build_trending_product_signals(raw: dict[str, Any], blocked_status: str | None, market_stage: str) -> dict[str, Any]:
    source = raw.get("trending_product_signals")
    if isinstance(source, dict) and source:
        return source
    if blocked_status:
        return {
            "new_product_count": "unknown",
            "low_review_high_sales_count": "unknown",
            "recent_launch_success_cases": [],
            "rising_keywords": [],
            "seasonal_peak_months": [],
            "product_format_shift": "unknown",
            "buyer_need_shift": "unknown",
            "trend_strength_score": 0,
        }
    competitors = [item for item in as_list(raw.get("competitors")) if isinstance(item, dict)]
    keywords = [item for item in as_list(raw.get("keywords")) if isinstance(item, dict)]
    ramp = raw.get("new_product_ramp_difficulty") if isinstance(raw.get("new_product_ramp_difficulty"), dict) else {}
    low_review_high_sales = ramp.get("low_review_high_sales_count", "unknown")
    rising_keywords = [
        as_text(item.get("keyword") or item.get("关键词"))
        for item in keywords[:5]
        if as_text(item.get("keyword") or item.get("关键词")).strip()
    ]
    seasonal_peak_months = []
    for item in keywords[:8]:
        if isinstance(item, dict):
            season = as_text(item.get("peak_season") or item.get("搜索量旺季") or item.get("season"))
            if season and season not in seasonal_peak_months:
                seasonal_peak_months.append(season)
    score = 45
    if market_stage in {"growth", "seasonal"}:
        score += 15
    if isinstance(low_review_high_sales, (int, float)) and low_review_high_sales > 0:
        score += min(20, int(low_review_high_sales) * 3)
    return {
        "new_product_count": sum(1 for item in competitors if str(item.get("listing_age_days", "")).isdigit() and int(item.get("listing_age_days")) <= 180),
        "low_review_high_sales_count": low_review_high_sales,
        "recent_launch_success_cases": [
            as_text(item.get("asin") or item.get("competitor_id"))
            for item in competitors
            if as_text(item.get("asin") or item.get("competitor_id")).strip()
        ][:5],
        "rising_keywords": rising_keywords,
        "seasonal_peak_months": seasonal_peak_months[:5],
        "product_format_shift": "场景化、儿童安全音量、无线/有线分层和便携折叠是可观察的格式方向。",
        "buyer_need_shift": "买家更关注佩戴舒适、耐用、稳定连接和真实续航承诺。",
        "trend_strength_score": max(0, min(100, score)),
    }


def build_voc_trend_summary(raw: dict[str, Any], blocked_status: str | None, voc_scores: list[dict[str, Any]]) -> dict[str, Any]:
    source = raw.get("voc_trend_summary")
    if isinstance(source, dict) and source:
        return source
    if blocked_status:
        return {
            "summary": "阻断状态下不能判断 VOC 趋势。",
            "trend_direction": "unknown",
            "evidence": [],
            "missing_data": ["usable provider review evidence"],
        }
    top = sorted(
        voc_scores,
        key=lambda item: item.get("productization_score", 0) if isinstance(item.get("productization_score"), (int, float)) else 0,
        reverse=True,
    )[:3]
    return {
        "summary": "VOC 机会主要集中在可产品化痛点，需通过扩样确认是否稳定存在。",
        "trend_direction": "painpoint_persistent",
        "evidence": [as_text(item.get("painpoint")) for item in top if as_text(item.get("painpoint")).strip()],
        "missing_data": ["更多 ASIN 摘要化评论覆盖", "Q&A 摘要", "退货原因数据"],
    }


def build_product_action_plan(raw: dict[str, Any], blocked_status: str | None, matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source = raw.get("product_action_plan")
    if isinstance(source, dict):
        source = [source]
    if isinstance(source, list) and source:
        return [item for item in source if isinstance(item, dict)]
    if blocked_status:
        return []
    return [
        {
            "action": item.get("product_action"),
            "why": f"对应痛点：{item.get('painpoint')}",
            "validation": "样品测试、竞品对照和页面承诺一致性检查。",
            "priority": item.get("priority", "medium"),
            "evidence_level": item.get("evidence_level", "D_assumption"),
        }
        for item in matrix[:6]
        if isinstance(item, dict)
    ]


def build_report_delivery_package(raw: dict[str, Any], privacy_mode: str) -> dict[str, Any]:
    source = raw.get("report_delivery_package")
    if isinstance(source, dict) and source:
        return source
    return {
        "primary_report": "dist/product_selection_report.html",
        "data_package": "dist/product_selection_data.json",
        "source_manifest": "dist/source_manifest.json",
        "validation_result": "dist/validation_result.json",
        "optional_markdown_report": "dist/product_selection_report.md",
        "optional_charts_manifest": "dist/optional_charts_manifest.json",
        "package_zip_path": "dist/product_selection_delivery_package.zip",
        "privacy_mode": privacy_mode,
        "delivery_notes": (
            "private_internal 输出可包含真实市场数据但不得提交 GitHub。"
            if privacy_mode == "private_internal"
            else "public-safe 输出只能作为模板样例，不代表实时市场结论。"
        ),
    }


def build_delivery(raw: dict[str, Any], privacy_mode: str) -> dict[str, Any]:
    source = raw.get("delivery")
    if isinstance(source, dict) and source:
        delivery = deepcopy(source)
    else:
        delivery = {}
    local_preview_url = as_text(delivery.get("local_preview_url"), "for local validation only")
    publish_status = as_text(delivery.get("publish_status"), "not_published")
    shareable_url = delivery.get("shareable_url")
    shareable_scope = as_text(delivery.get("shareable_url_scope"), "none")
    if not shareable_url:
        shareable_url = None
        shareable_scope = "none"
    if publish_status not in {"not_published", "local_only", "public_safe_published", "internal_published"}:
        publish_status = "not_published"
    return {
        "local_preview_url": local_preview_url,
        "is_localhost_only": bool(delivery.get("is_localhost_only", True)),
        "report_file_path": as_text(delivery.get("report_file_path"), "product_selection_report.html"),
        "package_zip_path": as_text(delivery.get("package_zip_path"), "product_selection_delivery_package.zip"),
        "publish_status": publish_status,
        "shareable_url": shareable_url,
        "shareable_url_scope": shareable_scope,
        "notes": as_text(
            delivery.get("notes"),
            (
                "private_internal reports are local or internal-only and must not be published publicly."
                if privacy_mode == "private_internal"
                else "public-safe reports may be published only after validator and privacy scan pass."
            ),
        ),
    }


def build_optional_charts_manifest(raw: dict[str, Any], blocked_status: str | None) -> dict[str, Any]:
    source = raw.get("optional_charts_manifest")
    if isinstance(source, dict) and source:
        return source
    return {
        "enabled": False,
        "charts_dir": "dist/charts",
        "items": [],
        "note": (
            "Blocked package: charts are not generated without usable data."
            if blocked_status
            else "Optional charts are supported by manifest; SVG generation can be added without changing the main HTML report."
        ),
    }


def score_item(raw_scores: dict[str, Any], key: str, label: str, max_score: int, blocked: bool) -> dict[str, Any]:
    if blocked:
        return {
            "score": 0,
            "max_score": max_score,
            "reason": "Blocked package: scoring is not available without usable provider evidence.",
            "confidence": "low",
            "missing_data": ["usable provider evidence"],
        }
    source = raw_scores.get(key)
    if isinstance(source, dict):
        score = float(source.get("score", 0))
        reason = as_text(source.get("reason"), f"{label} score supplied by normalized fixture.")
        confidence = source.get("confidence") if source.get("confidence") in {"high", "medium", "low"} else "medium"
        missing = as_list(source.get("missing_data"))
    else:
        score = float(source or 0)
        reason = f"{label} score supplied by normalized fixture."
        confidence = "medium"
        missing = []
    score = max(0, min(max_score, score))
    return {
        "score": score,
        "max_score": max_score,
        "reason": reason,
        "confidence": confidence,
        "missing_data": [as_text(item) for item in missing if as_text(item).strip()],
    }


def build_scores(raw: dict[str, Any], blocked_status: str | None) -> dict[str, Any]:
    raw_scores = raw.get("score_overrides") if isinstance(raw.get("score_overrides"), dict) else {}
    blocked = blocked_status is not None
    scores: dict[str, Any] = {}
    total = 0.0
    for key, label, max_score in SCORE_DIMENSIONS:
        item = score_item(raw_scores, key, label, max_score, blocked)
        scores[key] = item
        total += item["score"]
    scores["total"] = round(total, 2)
    return scores


def conclusion_item(
    key: str,
    raw: dict[str, Any],
    blocked_status: str | None,
    missing_fields: list[str],
    privacy_mode: str,
) -> dict[str, Any]:
    raw_analysis = raw.get("analysis") if isinstance(raw.get("analysis"), dict) else {}
    source_item = raw_analysis.get(key) if isinstance(raw_analysis.get(key), dict) else {}
    if blocked_status:
        return {
            "conclusion": f"{SECTION_LABELS[key]}被阻断，不能形成选品结论。",
            "evidence": f"当前状态为 {blocked_status}，缺少可用于判断的 provider response 证据。",
            "source": source_name_for(privacy_mode),
            "confidence": "low",
            "assumption": "阻断状态下不推断市场机会。",
            "missing_data": missing_fields or ["usable provider evidence"],
        }
    return {
        "conclusion": as_text(
            source_item.get("conclusion"),
            f"{SECTION_LABELS[key]}需要结合 provider response 标准化数据判断。",
        ),
        "evidence": as_text(
            source_item.get("evidence"),
            "Normalized public-safe fixture includes evidence summaries only.",
        ),
        "source": as_text(source_item.get("source"), SOURCE_NAME),
        "confidence": source_item.get("confidence") if source_item.get("confidence") in {"high", "medium", "low"} else "medium",
        "assumption": as_text(
            source_item.get("assumption"),
            "This package is a template sample and not live market evidence.",
        ),
        "missing_data": [as_text(item) for item in as_list(source_item.get("missing_data")) if as_text(item).strip()],
    }


def build_evidence(raw: dict[str, Any], blocked_status: str | None, privacy_mode: str) -> list[dict[str, Any]]:
    if blocked_status:
        return [
            {
                "claim": "当前包被阻断，不能支持真实选品进入决策。",
                "source": source_name_for(privacy_mode),
                "evidence": f"blocked_status={blocked_status}",
                "confidence": "high",
            }
        ]
    evidence = raw.get("evidence")
    if isinstance(evidence, list) and evidence:
        result: list[dict[str, Any]] = []
        for item in evidence:
            if not isinstance(item, dict):
                continue
            result.append(
                {
                    "claim": as_text(item.get("claim"), "Public-safe evidence claim."),
                    "source": as_text(item.get("source"), SOURCE_NAME),
                    "evidence": as_text(item.get("evidence"), "Public-safe evidence summary."),
                    "confidence": item.get("confidence") if item.get("confidence") in {"high", "medium", "low"} else "medium",
                }
            )
        if result:
            return result
    return [
        {
            "claim": "The normalized fixture contains enough public-safe summaries for a template report.",
            "source": SOURCE_NAME,
            "evidence": "Evidence is summarized and anonymized; no raw provider export or raw review text is included.",
            "confidence": "medium",
        }
    ]


def build_downstream_brief(raw: dict[str, Any], input_data: dict[str, Any], blocked_status: str | None) -> dict[str, Any]:
    raw_brief = raw.get("downstream_brief") if isinstance(raw.get("downstream_brief"), dict) else {}
    if blocked_status:
        return {
            "product_identity": "blocked product selection brief",
            "target_user": "not available until provider evidence is usable",
            "priority_keywords": [],
            "user_questions": [],
            "differentiation_points": [],
            "facts_to_confirm": ["provider response availability", "required market fields"],
            "restricted_claims": ["unverified performance claims", "unverified compliance claims"],
            "handoff_notes": "Blocked package: do not hand off to Listing, image, or A+ execution.",
        }
    keywords = as_list(raw_brief.get("priority_keywords")) or [
        item.get("keyword") for item in as_list(raw.get("keywords")) if isinstance(item, dict) and item.get("keyword")
    ]
    return {
        "product_identity": as_text(
            raw_brief.get("product_identity"),
            input_data.get("product_idea") or input_data.get("keyword") or "example product opportunity",
        ),
        "target_user": as_text(raw_brief.get("target_user"), "public-safe example buyer segment"),
        "priority_keywords": [as_text(item) for item in keywords if as_text(item).strip()][:8],
        "user_questions": [as_text(item) for item in as_list(raw_brief.get("user_questions")) if as_text(item).strip()],
        "differentiation_points": [
            as_text(item) for item in as_list(raw_brief.get("differentiation_points")) if as_text(item).strip()
        ],
        "facts_to_confirm": [as_text(item) for item in as_list(raw_brief.get("facts_to_confirm")) if as_text(item).strip()],
        "restricted_claims": [
            as_text(item) for item in as_list(raw_brief.get("restricted_claims")) if as_text(item).strip()
        ]
        or ["unverified performance claims", "unverified compliance claims"],
        "handoff_notes": as_text(
            raw_brief.get("handoff_notes"),
            "Use this brief only as a template handoff after local provider evidence and product facts are confirmed.",
        ),
    }


def build_manifest(
    raw: dict[str, Any],
    privacy_mode: str,
    report_language: str,
    generated_at: str,
    query: dict[str, Any],
    blocks: list[dict[str, Any]],
    decision_confidence: str,
    blocked_status: str | None,
    input_name: str,
    freshness: str,
    delivery: dict[str, Any],
) -> dict[str, Any]:
    total_records = sum(int(block.get("record_count") or 0) for block in blocks)
    manifest_confidence = (
        "live_market_data_if_sorftime_success_otherwise_blocked"
        if privacy_mode == "private_internal"
        else decision_confidence
    )
    if privacy_mode == "private_internal":
        source_scope = query.get("category_name") or query.get("category") or query.get("keyword") or "Amazon market request"
        sources = [
            {
                "source_name": "BYO MCP provider response",
                "source_type": "byo_mcp_provider_response",
                "source_scope": f"{query.get('site', 'Amazon')} {source_scope}".strip(),
                "status": "blocked" if blocked_status else "ready",
                "record_count": total_records,
                "usable_for_decision": blocked_status is None,
            }
        ]
    else:
        sources = [
            {
                "source": PUBLIC_SAFE_SOURCE_NAME,
                "input_reference": input_name,
                "status": "blocked" if blocked_status else "ready",
                "record_count": total_records,
                "fields": sorted({str(field) for block in blocks for field in as_list(block.get("fields"))}),
                "missing_fields": [as_text(item) for item in as_list(raw.get("missing_fields")) if as_text(item).strip()],
                "usable_for_decision": blocked_status is None,
            }
        ]
    return {
        "schema_version": "1.0.0",
        "privacy_mode": privacy_mode,
        "report_language": report_language,
        "generated_at": generated_at,
        "query": query,
        "data_blocks": blocks,
        "confidence": manifest_confidence,
        "blocked_status": blocked_status,
        "no_user_private_data": True,
        "contains_user_private_data": False,
        "contains_raw_sorftime_export": False,
        "contains_review_text": False,
        "public_data_reference": True,
        "data_freshness": freshness,
        "delivery": delivery,
        "sources": sources,
    }


def build_provider_blocked_payload(request_payload: dict[str, Any], config_payload: dict[str, Any]) -> dict[str, Any]:
    privacy_mode = request_payload.get("privacy_mode") or config_payload.get("mode") or "private_internal"
    report_language = request_payload.get("report_language") or DEFAULT_REPORT_LANGUAGE
    return {
        "privacy_mode": privacy_mode,
        "report_language": report_language,
        "input": request_payload,
        "blocked_status": "blocked_sorftime_unavailable",
        "missing_fields": [
            "local provider response",
            "category_metrics",
            "keyword_metrics",
            "competitor_matrix",
            "price_bands",
            "voc_summary",
        ],
        "sorftime_status": {
            "status": "failed",
            "available": False,
            "tools": ["byo_mcp_provider"],
            "checked_at": utc_now(),
            "notes": (
                "This repository is BYO-MCP and does not include a live provider connector; "
                "no fallback source was used and no market data was fabricated."
            ),
        },
        "data_freshness": LIVE_DATA_FRESHNESS,
        "data_blocks": [
            {"name": name, "status": "missing", "record_count": 0, "field_coverage": 0.0}
            for name in REQUIRED_BLOCKS
        ],
        "assumptions": [
            "真实 provider 数据采集必须在本仓库外完成。",
            "未回退公开网页、旧文件或样例数据。",
            "当前输出是中文阻断型报告，不是选品结论。",
        ],
        "next_validation_actions": [
            "确认本地 BYO-MCP provider 可生成响应 JSON。",
            "将真实 provider response 保存到 runtime/provider_response.json 后重新标准化。",
            "不要把 runtime、private、real_data 或 dist 真实报告提交 GitHub。",
        ],
    }


def normalize(raw: dict[str, Any], input_name: str = "input.json") -> tuple[dict[str, Any], dict[str, Any]]:
    privacy_mode = raw.get("privacy_mode") or "public_safe_real_world"
    if privacy_mode not in VALID_PRIVACY_MODES:
        raise ValueError(f"Unsupported privacy_mode: {privacy_mode}")

    generated_at = utc_now()
    raw_input = collect_input(raw)
    report_language = as_text(raw.get("report_language") or raw_input.get("report_language"), DEFAULT_REPORT_LANGUAGE)
    input_data = safe_input(raw_input, privacy_mode)
    competitors = anonymize_competitors(as_list(raw.get("competitors")), privacy_mode)
    blocked_status = infer_blocked_status(raw)
    missing_fields = [as_text(item) for item in as_list(raw.get("missing_fields")) if as_text(item).strip()]
    if blocked_status and not missing_fields:
        missing_fields = ["usable provider evidence"]

    scores = build_scores(raw, blocked_status)
    data_quality_status = "blocked" if blocked_status else as_text(raw.get("data_quality"), "medium")
    if data_quality_status not in {"high", "medium", "low", "blocked"}:
        data_quality_status = "medium"
    confidence = "low" if blocked_status else as_text(raw.get("confidence"), "medium")
    if confidence not in {"high", "medium", "low"}:
        confidence = "medium"
    decision_label = "blocked" if blocked_status else score_label(float(scores["total"]))
    model_evidence_level = evidence_level(raw, blocked_status, privacy_mode)
    market_stage = build_market_stage(raw, blocked_status)
    ramp_difficulty = build_ramp_difficulty(raw, blocked_status)
    entry_strategy = build_entry_strategy(raw, blocked_status)
    voc_productization_score = build_voc_productization(raw, blocked_status)
    disqualifiers = build_disqualifiers(raw, blocked_status)
    competitor_clusters = build_competitor_clusters(raw, blocked_status, model_evidence_level)
    profit_space_detail = build_profit_space_detail(raw, blocked_status, privacy_mode)
    downgraded_by_disqualifier = (
        not blocked_status
        and decision_label == "enter"
        and has_active_critical_disqualifier(disqualifiers)
    )
    if downgraded_by_disqualifier:
        decision_label = "cautious"

    blocks = data_blocks(raw)
    freshness = data_freshness(raw, privacy_mode)
    query = build_query(input_data, raw_input)
    delivery = build_delivery(raw, privacy_mode)
    manifest = build_manifest(
        raw,
        privacy_mode,
        report_language,
        generated_at,
        query,
        blocks,
        confidence,
        blocked_status,
        input_name,
        freshness,
        delivery,
    )

    status_raw = raw.get("sorftime_status") if isinstance(raw.get("sorftime_status"), dict) else {}
    analysis = {
        key: conclusion_item(key, raw, blocked_status, missing_fields, privacy_mode)
        for key in ANALYSIS_KEYS
    }
    evidence = build_evidence(raw, blocked_status, privacy_mode)
    assumptions = [as_text(item) for item in as_list(raw.get("assumptions")) if as_text(item).strip()]
    if not assumptions:
        assumptions = (
            ["当前包为本地 private_internal 输出；真实结论必须以可用 provider response 数据为准。"]
            if privacy_mode == "private_internal"
            else ["This package is a public-safe template sample and not live market data."]
        )
    next_actions = [as_text(item) for item in as_list(raw.get("next_validation_actions")) if as_text(item).strip()]
    if not next_actions:
        next_actions = (
            ["Restore local provider response access and rerun normalization."]
            if blocked_status == "blocked_sorftime_unavailable"
            else [
                "Generate a local provider response before making a product-entry decision.",
                "Confirm landed cost, fees, compliance, and supply-chain facts.",
            ]
        )
    data_coverage_score = build_data_coverage_score(blocks, blocked_status, missing_fields)
    profit_scenarios = build_profit_scenarios(raw, blocked_status, privacy_mode, profit_space_detail)
    ramp_path = build_ramp_path(raw, blocked_status)
    voc_opportunity_matrix = build_voc_opportunity_matrix(raw, blocked_status, voc_productization_score)
    validation_plan = build_validation_plan(raw, blocked_status, next_actions)
    trending_product_signals = build_trending_product_signals(raw, blocked_status, market_stage)
    voc_trend_summary = build_voc_trend_summary(raw, blocked_status, voc_productization_score)
    product_action_plan = build_product_action_plan(raw, blocked_status, voc_opportunity_matrix)
    report_delivery_package = build_report_delivery_package(raw, privacy_mode)
    optional_charts_manifest = build_optional_charts_manifest(raw, blocked_status)

    data = {
        "schema_version": "1.0.0",
        "privacy_mode": privacy_mode,
        "report_language": report_language,
        "generated_at": generated_at,
        "input": input_data,
        "sorftime_status": {
            "status": "blocked" if blocked_status else as_text(status_raw.get("status"), "ready"),
            "tools": [as_text(item) for item in as_list(status_raw.get("tools") or ["byo_mcp_provider_response"])],
            "checked_at": as_text(status_raw.get("checked_at"), generated_at),
            "blocking_status": blocked_status,
            "notes": as_text(
                status_raw.get("notes"),
                (
                    "Private internal package; no raw review text or credentials are retained."
                    if privacy_mode == "private_internal"
                    else "Public-safe template sample; not a live provider response."
                ),
            ),
        },
        "data_quality": {
            "status": data_quality_status,
            "row_count": sum(int(block.get("record_count") or 0) for block in blocks),
            "field_coverage": round(
                sum(float(block.get("field_coverage") or 0) for block in blocks) / max(len(blocks), 1),
                4,
            ),
            "missing_fields": missing_fields,
            "limitations": [
                *(
                    [
                        "Private internal provider-response package.",
                        "Raw provider export and raw review text are not retained in the report package.",
                        "授权凭证、本地私有配置路径和接口密钥均不写入交付包。",
                    ]
                    if privacy_mode == "private_internal"
                    else [
                        "Public-safe template sample.",
                        "Not live market data.",
                        "Not a complete real Top 100 export.",
                        "Not a raw provider export.",
                        "Not a real product selection conclusion.",
                    ]
                )
            ],
            "data_freshness": freshness,
        },
        "scores": scores,
        "decision": {
            "label": decision_label,
            "score": scores["total"],
            "summary": as_text(
                raw.get("decision_summary"),
                (
                    f"Package is blocked by {blocked_status}; no market-entry decision is available."
                    if blocked_status
                    else f"Template sample score is {scores['total']} and maps to {decision_label}."
                ),
            ),
            "confidence": confidence,
            "blocked_status": blocked_status,
        },
        "market_stage": market_stage,
        "new_product_ramp_difficulty": ramp_difficulty,
        "entry_strategy": entry_strategy,
        "voc_productization_score": voc_productization_score,
        "disqualifiers": disqualifiers,
        "evidence_level": model_evidence_level,
        "competitor_clusters": competitor_clusters,
        "profit_space_detail": profit_space_detail,
        "data_coverage_score": data_coverage_score,
        "profit_scenarios": profit_scenarios,
        "ramp_path": ramp_path,
        "voc_opportunity_matrix": voc_opportunity_matrix,
        "validation_plan": validation_plan,
        "trending_product_signals": trending_product_signals,
        "voc_trend_summary": voc_trend_summary,
        "product_action_plan": product_action_plan,
        "report_delivery_package": report_delivery_package,
        "delivery": delivery,
        "optional_charts_manifest": optional_charts_manifest,
        "analysis": analysis,
        "evidence": evidence,
        "assumptions": assumptions,
        "missing_data": missing_fields,
        "next_validation_actions": next_actions,
        "downstream_brief": build_downstream_brief(raw, input_data, blocked_status),
        "public_safe_notice": {
            "applies_to": "On-Ear Headphones fixture and all public examples",
            "statements": [
                "This is a public-safe template sample.",
                "It is not live market data.",
                "It is not a complete real Top 100 export.",
                "It is not a raw provider export.",
                "It does not represent a real product selection conclusion.",
            ],
        },
        "normalized_blocks": {
            "competitors": competitors,
            "keywords": deepcopy(as_list(raw.get("keywords"))),
            "market_capacity": deepcopy(raw.get("market_capacity") or {}),
            "price_profit": deepcopy(raw.get("price_profit") or {}),
            "voc": deepcopy(raw.get("voc") or {}),
            "voc_trend_summary": deepcopy(voc_trend_summary),
            "voc_opportunity_matrix": deepcopy(voc_opportunity_matrix),
            "product_action_plan": deepcopy(product_action_plan),
            "trending_product_signals": deepcopy(trending_product_signals),
            "differentiation": deepcopy(as_list(raw.get("differentiation"))),
            "risks": deepcopy(as_list(raw.get("risks"))),
        },
        "source_manifest": manifest,
    }
    if downgraded_by_disqualifier:
        data["decision"]["summary"] = (
            f"{data['decision']['summary']} Active critical disqualifier detected; "
            "decision label was capped at cautious."
        )
    return data, manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize BYO-MCP provider-response market data into product selection JSON.")
    parser.add_argument("input_json", nargs="?", help="Input fixture or local provider response JSON.")
    parser.add_argument("--input", dest="request_json", help="Request JSON used with --provider.")
    parser.add_argument(
        "--provider",
        choices=["sorftime_mcp"],
        default=None,
        help="Deprecated contract-only provider mode. It never connects to MCP or the network.",
    )
    parser.add_argument("--config", default=None, help="Deprecated local config path for contract-only provider mode.")
    parser.add_argument(
        "--out",
        default="dist/product_selection_data.json",
        help="Output product_selection_data.json path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.out)
    if args.provider:
        request_path = Path(args.request_json or args.input_json) if (args.request_json or args.input_json) else None
        request_payload = read_json(request_path) if request_path else {}
        config_payload = read_json(Path(args.config)) if args.config and Path(args.config).exists() else {}
        raw = build_provider_blocked_payload(request_payload, config_payload)
        input_name = f"{args.provider}_request"
    else:
        if not args.input_json:
            raise SystemExit("input_json is required unless --provider is used.")
        input_path = Path(args.input_json)
        raw = read_json(input_path)
        input_name = input_path.name
    data, manifest = normalize(raw, input_name=input_name)
    write_json(output_path, data)
    write_json(output_path.parent / "source_manifest.json", manifest)
    print(
        json.dumps(
            {
                "ok": True,
                "product_selection_data": output_path.name,
                "source_manifest": "source_manifest.json",
                "decision": data["decision"]["label"],
                "blocked_status": data["decision"]["blocked_status"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
