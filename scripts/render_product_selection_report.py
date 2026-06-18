#!/usr/bin/env python3
"""Render an offline HTML product selection report from normalized data."""

from __future__ import annotations

import argparse
import json
import re
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "product_selection_report.template.html"

SCORE_LABELS = {
    "demand_capacity": "需求容量",
    "competition_entry": "竞争强度",
    "profit_space": "利润空间",
    "differentiation_opportunity": "差异化机会",
    "voc_painpoint_opportunity": "VOC 痛点机会",
    "keyword_entry": "关键词入口",
    "compliance_supply_risk": "合规与供应链风险",
}

ANALYSIS_TO_PLACEHOLDER = {
    "category_capacity": "category_capacity",
    "keyword_opportunity": "keyword_opportunity",
    "competitor_structure": "competitor_structure",
    "price_profit": "price_profit",
    "review_voc": "review_voc",
    "differentiation": "differentiation",
    "risk": "risk",
}

PUBLIC_SAFE_NOTICE = (
    "On-Ear Headphones fixture 是 public-safe template sample；不是实时市场数据；"
    "不是完整真实 Top 100；不是真实 provider 原始导出；不代表真实选品结论。"
)
PRIVATE_INTERNAL_NOTICE = (
    "本报告为 private_internal 本地真实 provider response 分析输出；不得提交 GitHub；"
    "报告不包含个人身份、会话信息、接口密钥、授权凭证或原始评论全文。"
)
PROFIT_PUBLIC_SAFE_NOTICE = (
    "公开安全样例中的利润明细仅用于模板展示，不代表实时利润估算。"
    " Profit detail in public-safe fixtures is template-level only and not a live margin estimate."
)

DECISION_LABELS = {
    "enter": "可进入",
    "cautious": "谨慎验证",
    "weak": "机会偏弱",
    "no-enter": "不建议进入",
    "blocked": "数据阻断",
}
CONFIDENCE_LABELS = {"high": "高", "medium": "中", "low": "低"}
MARKET_STAGE_LABELS = {
    "growth": "增长期",
    "mature": "成熟期",
    "price_war": "价格战",
    "seasonal": "季节性",
    "declining": "下行期",
    "unknown": "未知",
}
RAMP_LABELS = {"low": "低", "medium": "中", "high": "高", "very_high": "很高"}
RISK_LABELS = {"info": "信息", "warning": "预警", "critical": "严重"}
CORRUPT_PLACEHOLDER = "???"
MISSING_VALUE = "未提供"
EMPTY_VALUE = "暂无数据"
NO_MISSING_DATA = "无缺失数据"
ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")
AMAZON_DOMAINS = {
    "US": "www.amazon.com",
    "UK": "www.amazon.co.uk",
    "CA": "www.amazon.ca",
}
SAFE_AMAZON_HREF = re.compile(r"^https://www\.amazon\.(?:com|co\.uk|ca)(?:/|$)", re.IGNORECASE)
UNSAFE_HREF = re.compile(
    r"(?:https?://(?:localhost|127\.0\.0\.1)\b|file://|(?<![A-Za-z])[A-Za-z]:[\\/]|[?&](?:token|key|secret|password|cookie)=)",
    re.IGNORECASE,
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Product selection data root must be an object.")
    return payload


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and set(stripped) == {"?"}:
            return fallback or "未提供"
        return value
    return str(value)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def html_list(items: list[Any]) -> str:
    if not items:
        return f'<p class="muted">{EMPTY_VALUE}。</p>'
    return "<ul>" + "".join(f"<li>{escape(text(item))}</li>" for item in items) + "</ul>"


def badge(value: Any, tone: str = "") -> str:
    cls = "badge" + (f" {tone}" if tone else "")
    return f'<span class="{cls}">{escape(text(value, "未知"))}</span>'


def kv_table(mapping: dict[str, Any]) -> str:
    rows = []
    for key, value in mapping.items():
        if isinstance(value, list):
            rendered = ", ".join(text(item) for item in value) or EMPTY_VALUE
        elif isinstance(value, dict):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = text(value, MISSING_VALUE)
        rows.append(f"<tr><th>{escape(text(key))}</th><td>{escape(rendered)}</td></tr>")
    return "<table><tbody>" + "".join(rows) + "</tbody></table>"


def html_table(headers: list[str], rows: list[list[str]], empty_text: str = EMPTY_VALUE) -> str:
    if not rows:
        rows = [[f'<span class="muted">{escape(empty_text)}。</span>']]
    header = "".join(f"<th>{escape(label)}</th>" for label in headers)
    body = []
    for row in rows:
        if len(row) == 1 and len(headers) > 1:
            body.append(f'<tr><td colspan="{len(headers)}">{row[0]}</td></tr>')
        else:
            body.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def object_table(items: list[Any], columns: list[tuple[str, str]]) -> str:
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cells = []
        for key, _label in columns:
            value = item.get(key)
            if isinstance(value, list):
                rendered = ", ".join(text(entry) for entry in value) or EMPTY_VALUE
            elif isinstance(value, dict):
                rendered = json.dumps(value, ensure_ascii=False)
            else:
                rendered = text(value, MISSING_VALUE)
            cells.append(f"<td>{escape(rendered)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    if not rows:
        rows.append(f'<tr><td colspan="{len(columns)}" class="muted">{EMPTY_VALUE}。</td></tr>')
    header = "".join(f"<th>{escape(label)}</th>" for _key, label in columns)
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def marketplace_code(marketplace: Any) -> str:
    value = text(marketplace, "US").upper()
    if "UK" in value or "UNITED KINGDOM" in value or "AMAZON.CO.UK" in value:
        return "UK"
    if "CA" in value or "CANADA" in value or "AMAZON.CA" in value:
        return "CA"
    return "US"


def marketplace_domain(marketplace: Any) -> str:
    return AMAZON_DOMAINS.get(marketplace_code(marketplace), AMAZON_DOMAINS["US"])


def is_valid_asin(value: Any) -> bool:
    return bool(ASIN_PATTERN.fullmatch(text(value).strip().upper()))


def is_public_safe_mode(privacy_mode: Any) -> bool:
    return text(privacy_mode) in {"public_safe_real_world", "strict_anonymized"}


def is_anonymized_value(value: Any) -> bool:
    lowered = text(value).strip().lower()
    if not lowered:
        return True
    markers = ["example_", "example-", "anonymized", "anonymous", "template_sample", "sample_", "unknown"]
    return any(marker in lowered for marker in markers)


def is_safe_amazon_href(url: Any) -> bool:
    href = text(url).strip()
    return bool(href and SAFE_AMAZON_HREF.match(href) and not UNSAFE_HREF.search(href))


def amazon_dp_url(marketplace: Any, asin: Any) -> str | None:
    asin_text = text(asin).strip().upper()
    if not is_valid_asin(asin_text):
        return None
    return f"https://{marketplace_domain(marketplace)}/dp/{asin_text}"


def amazon_search_url(marketplace: Any, keyword: Any) -> str | None:
    keyword_text = text(keyword).strip()
    if not keyword_text:
        return None
    return f"https://{marketplace_domain(marketplace)}/s?k={quote_plus(keyword_text)}"


def render_external_link(label: Any, url: Any, css_class: str, title: str = "") -> str:
    href = text(url).strip()
    if not is_safe_amazon_href(href):
        return f'<span class="link-disabled">{escape(text(label, MISSING_VALUE))}</span>'
    title_attr = f' title="{escape(title, quote=True)}"' if title else ""
    return (
        f'<a href="{escape(href, quote=True)}" target="_blank" rel="noopener noreferrer" '
        f'class="{escape(css_class, quote=True)}"{title_attr}>{escape(text(label, MISSING_VALUE))}'
        '<span class="external-hint">↗</span></a>'
    )


def disabled_link(label: str, title: str = "") -> str:
    title_attr = f' title="{escape(title, quote=True)}"' if title else ""
    return f'<span class="link-disabled"{title_attr}>{escape(label)}</span>'


def truncate_text(value: Any, limit: int = 96) -> str:
    value_text = text(value, MISSING_VALUE).strip()
    if len(value_text) <= limit:
        return value_text
    return value_text[: limit - 1].rstrip() + "…"


def competitor_title(competitor: dict[str, Any]) -> str:
    for key in ["title", "product_title", "product_name", "name", "listing_title"]:
        if text(competitor.get(key)).strip():
            return text(competitor.get(key)).strip()
    return text(competitor.get("competitor_id") or competitor.get("asin"), "未命名竞品")


def render_asin_link(asin: Any, marketplace: Any, privacy_mode: Any) -> str:
    asin_text = text(asin).strip().upper()
    if is_public_safe_mode(privacy_mode) and (is_anonymized_value(asin_text) or not is_valid_asin(asin_text)):
        return disabled_link("匿名竞品", "public-safe 样例不提供真实商品链接")
    if text(privacy_mode) == "private_internal" and is_valid_asin(asin_text):
        return render_external_link(asin_text, amazon_dp_url(marketplace, asin_text), "link-asin")
    return escape(text(asin, MISSING_VALUE))


def render_brand_link(brand: Any, marketplace: Any, privacy_mode: Any) -> str:
    brand_text = text(brand).strip()
    if not brand_text:
        return "未提供"
    if is_public_safe_mode(privacy_mode) and is_anonymized_value(brand_text):
        return disabled_link("匿名品牌")
    return render_external_link(brand_text, amazon_search_url(marketplace, brand_text), "link-brand")


def render_keyword_link(keyword: Any, marketplace: Any, privacy_mode: Any) -> str:
    keyword_text = text(keyword).strip()
    if not keyword_text:
        return escape(MISSING_VALUE)
    if is_public_safe_mode(privacy_mode) and is_anonymized_value(keyword_text):
        return disabled_link("匿名关键词")
    return render_external_link(keyword_text, amazon_search_url(marketplace, keyword_text), "link-keyword")


def render_competitor_title_link(competitor: dict[str, Any], marketplace: Any, privacy_mode: Any) -> str:
    title = competitor_title(competitor)
    asin = competitor.get("asin")
    if is_public_safe_mode(privacy_mode):
        return disabled_link("匿名竞品", "public-safe 样例不提供真实商品链接")
    if text(privacy_mode) == "private_internal" and is_valid_asin(asin):
        return render_external_link(truncate_text(title), amazon_dp_url(marketplace, asin), "link-title", title=title)
    return escape(truncate_text(title))


def render_category_url(value: Any, marketplace: Any) -> str:
    url = text(value).strip()
    if not url:
        return MISSING_VALUE
    if is_safe_amazon_href(url):
        return render_external_link("打开 Amazon 类目页", url, "link-keyword")
    return escape("类目链接未通过安全校验")


def input_info_table(input_info: dict[str, Any]) -> str:
    marketplace = input_info.get("marketplace") or input_info.get("site")
    rows = []
    for key, value in input_info.items():
        if key == "category_url":
            rendered = render_category_url(value, marketplace)
        elif isinstance(value, list):
            rendered = escape(", ".join(text(item) for item in value) or EMPTY_VALUE)
        elif isinstance(value, dict):
            rendered = escape(json.dumps(value, ensure_ascii=False))
        else:
            rendered = escape(text(value, MISSING_VALUE))
        rows.append(f"<tr><th>{escape(text(key))}</th><td>{rendered}</td></tr>")
    return "<table><tbody>" + "".join(rows) + "</tbody></table>"


def competitor_clusters_table(clusters: dict[str, Any]) -> str:
    rows = []
    for cluster_key, values in clusters.items():
        for item in as_list(values):
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "cluster_type": cluster_key,
                    "cluster_name": item.get("cluster_name"),
                    "summary": item.get("summary"),
                    "competition_pressure": item.get("competition_pressure"),
                    "entry_implication": item.get("entry_implication"),
                    "evidence_level": item.get("evidence_level"),
                }
            )
    return object_table(
        rows,
        [
            ("cluster_type", "集群类型"),
            ("cluster_name", "集群名称"),
            ("summary", "摘要"),
            ("competition_pressure", "竞争压力"),
            ("entry_implication", "进入含义"),
            ("evidence_level", "证据等级"),
        ],
    )


def model_context(data: dict[str, Any]) -> str:
    return kv_table(
        {
            "市场阶段": MARKET_STAGE_LABELS.get(text(data.get("market_stage")), text(data.get("market_stage"), "未知")),
            "证据等级": data.get("evidence_level"),
        }
    )


def limited(items: list[Any], count: int) -> list[Any]:
    return items[:count] if count > 0 else items


def data_coverage_block(data: dict[str, Any]) -> str:
    coverage = data.get("data_coverage_score") if isinstance(data.get("data_coverage_score"), dict) else {}
    missing_blocks = as_list(coverage.get("missing_blocks"))
    missing_fields = as_list(coverage.get("missing_fields"))
    return (
        '<div class="cards">'
        f'<div class="kpi"><span>覆盖评分</span><strong>{escape(text(coverage.get("score"), "0"))}</strong></div>'
        f'<div class="kpi"><span>覆盖状态</span><strong>{escape(text(coverage.get("status"), "未知"))}</strong></div>'
        f'<div class="kpi"><span>已就绪数据块</span><strong>{escape(text(coverage.get("ready_blocks"), "0"))}/{escape(text(coverage.get("total_blocks"), "0"))}</strong></div>'
        f'<div class="kpi"><span>字段覆盖率</span><strong>{escape(text(coverage.get("field_coverage"), "0"))}</strong></div>'
        '</div>'
        + "<h3>缺失数据块</h3>"
        + html_list(missing_blocks)
        + "<h3>缺失字段</h3>"
        + html_list(missing_fields)
    )


def trending_signals_block(data: dict[str, Any]) -> str:
    signals = data.get("trending_product_signals") if isinstance(data.get("trending_product_signals"), dict) else {}
    return kv_table(
        {
            "新品数量信号": signals.get("new_product_count"),
            "低评论高销量数量": signals.get("low_review_high_sales_count"),
            "近期起量样本": as_list(signals.get("recent_launch_success_cases")),
            "上升关键词": as_list(signals.get("rising_keywords")),
            "季节峰值月份": as_list(signals.get("seasonal_peak_months")),
            "产品形态变化": signals.get("product_format_shift"),
            "买家需求变化": signals.get("buyer_need_shift"),
            "趋势强度评分": signals.get("trend_strength_score"),
        }
    )


def keyword_opportunity_table(data: dict[str, Any], count: int = 20) -> str:
    blocks = data.get("normalized_blocks") if isinstance(data.get("normalized_blocks"), dict) else {}
    input_info = data.get("input") if isinstance(data.get("input"), dict) else {}
    marketplace = input_info.get("marketplace") or input_info.get("site")
    privacy_mode = data.get("privacy_mode")
    rows: list[list[str]] = []
    for item in limited(as_list(blocks.get("keywords")), count):
        if not isinstance(item, dict):
            continue
        rows.append(
            [
                render_keyword_link(item.get("keyword"), marketplace, privacy_mode),
                escape(text(item.get("monthly_search_volume"), MISSING_VALUE)),
                escape(text(item.get("weekly_search_volume"), MISSING_VALUE)),
                escape(text(item.get("cpc"), MISSING_VALUE)),
                escape(text(item.get("search_results"), MISSING_VALUE)),
                escape(text(item.get("peak_season"), MISSING_VALUE)),
                escape(text(item.get("front_3_page_brand_share"), MISSING_VALUE)),
            ]
        )
    return html_table(
        ["关键词", "月搜索量", "周搜索量", "CPC", "搜索结果数", "旺季/季节性", "前三页头部品牌占比"],
        rows,
    )


def competitor_matrix(data: dict[str, Any], count: int = 20) -> str:
    blocks = data.get("normalized_blocks") if isinstance(data.get("normalized_blocks"), dict) else {}
    input_info = data.get("input") if isinstance(data.get("input"), dict) else {}
    marketplace = input_info.get("marketplace") or input_info.get("site")
    privacy_mode = data.get("privacy_mode")
    rows: list[list[str]] = []
    for item in limited(as_list(blocks.get("competitors")), count):
        if not isinstance(item, dict):
            continue
        brand = render_brand_link(item.get("brand"), marketplace, privacy_mode)
        title_cell = (
            render_competitor_title_link(item, marketplace, privacy_mode)
            + f'<div class="cell-sub">{brand}</div>'
        )
        rows.append(
            [
                escape(text(item.get("competitor_id"), MISSING_VALUE)),
                title_cell,
                render_asin_link(item.get("asin"), marketplace, privacy_mode),
                brand,
                escape(text(item.get("positioning"), MISSING_VALUE)),
                escape(text(item.get("price_band"), MISSING_VALUE)),
                escape(text(item.get("review_band"), MISSING_VALUE)),
                escape(text(item.get("rating_band"), MISSING_VALUE)),
            ]
        )
    return html_table(
        ["竞品编号", "产品标题 / 品牌", "ASIN", "品牌", "定位", "价格带", "评论带", "评分带"],
        rows,
    )


def ramp_difficulty_block(data: dict[str, Any]) -> str:
    ramp = data.get("new_product_ramp_difficulty") if isinstance(data.get("new_product_ramp_difficulty"), dict) else {}
    clusters = data.get("competitor_clusters") if isinstance(data.get("competitor_clusters"), dict) else {}
    return (
        "<h3>竞品 Top20 表</h3>"
        '<p class="muted">点击 ASIN / 产品标题 / 品牌可在 Amazon 新窗口打开。public-safe 样例可能禁用真实竞品链接。</p>'
        + competitor_matrix(data)
        + "<h3>新品爬坡难度</h3>"
        + kv_table(ramp)
        + "<h3>竞品集群</h3>"
        + competitor_clusters_table(clusters)
    )


def profit_detail_block(data: dict[str, Any]) -> str:
    detail = data.get("profit_space_detail") if isinstance(data.get("profit_space_detail"), dict) else {}
    return (
        f'<p class="muted">{escape(PROFIT_PUBLIC_SAFE_NOTICE)}</p>'
        + kv_table(detail)
    )


def profit_scenarios_block(data: dict[str, Any]) -> str:
    return object_table(
        as_list(data.get("profit_scenarios")),
        [
            ("scenario", "情景"),
            ("target_price", "目标售价"),
            ("estimated_landed_cost", "到岸成本"),
            ("fees", "平台/FBA费用"),
            ("ad_cost", "广告容忍"),
            ("return_loss", "退货损耗"),
            ("target_margin", "目标利润"),
            ("conclusion", "结论"),
            ("evidence_level", "证据等级"),
        ],
    )


def ramp_path_block(data: dict[str, Any]) -> str:
    return object_table(
        as_list(data.get("ramp_path")),
        [
            ("stage", "阶段"),
            ("goal", "目标"),
            ("actions", "动作"),
            ("validation_standard", "验证标准"),
            ("risk", "风险"),
        ],
    )


def voc_trend_summary_block(data: dict[str, Any]) -> str:
    summary = data.get("voc_trend_summary") if isinstance(data.get("voc_trend_summary"), dict) else {}
    return kv_table(
        {
            "趋势摘要": summary.get("summary"),
            "趋势方向": summary.get("trend_direction"),
            "证据": as_list(summary.get("evidence")),
            "缺失数据": as_list(summary.get("missing_data")),
        }
    )


def voc_opportunity_matrix_block(data: dict[str, Any]) -> str:
    return object_table(
        as_list(data.get("voc_opportunity_matrix")),
        [
            ("painpoint", "痛点"),
            ("frequency_signal", "频率信号"),
            ("buyer_motive", "购买动机"),
            ("product_action", "产品动作"),
            ("listing_message", "页面表达"),
            ("priority", "优先级"),
            ("evidence_level", "证据等级"),
        ],
    )


def product_action_plan_block(data: dict[str, Any]) -> str:
    return object_table(
        as_list(data.get("product_action_plan")),
        [
            ("action", "产品动作"),
            ("why", "原因"),
            ("validation", "验证方式"),
            ("priority", "优先级"),
            ("evidence_level", "证据等级"),
        ],
    )


def validation_plan_block(data: dict[str, Any]) -> str:
    return object_table(
        as_list(data.get("validation_plan")),
        [
            ("validation_item", "验证项"),
            ("method", "方法"),
            ("pass_standard", "通过标准"),
            ("priority", "优先级"),
            ("blocked_if_missing", "缺失是否阻断"),
        ],
    )


def delivery_package_block(data: dict[str, Any]) -> str:
    package = data.get("report_delivery_package") if isinstance(data.get("report_delivery_package"), dict) else {}
    return kv_table(package)


def delivery_notes_block(data: dict[str, Any]) -> str:
    delivery = data.get("delivery") if isinstance(data.get("delivery"), dict) else {}
    privacy_mode = text(data.get("privacy_mode"), "public_safe_real_world")
    if privacy_mode == "private_internal":
        notice = "该报告为内部真实数据报告，不得发布到公网或提交 GitHub。"
    elif privacy_mode == "public_safe_real_world":
        notice = "该报告为 public-safe 样例，只有通过 validator 与 privacy scan 后才可公开分享。"
    else:
        notice = "该报告为严格匿名样例，按 public-safe 边界处理。"
    local_note = "local_preview_url 仅限本机临时预览，不能作为外部分享链接。"
    return (
        f'<div class="callout">{escape(local_note)} {escape(notice)}</div>'
        + kv_table(
            {
                "local_preview_url": delivery.get("local_preview_url"),
                "is_localhost_only": delivery.get("is_localhost_only"),
                "report_file_path": delivery.get("report_file_path"),
                "package_zip_path": delivery.get("package_zip_path"),
                "publish_status": delivery.get("publish_status"),
                "shareable_url": delivery.get("shareable_url"),
                "shareable_url_scope": delivery.get("shareable_url_scope"),
                "notes": delivery.get("notes"),
            }
        )
    )


def charts_manifest_block(data: dict[str, Any]) -> str:
    manifest = data.get("optional_charts_manifest") if isinstance(data.get("optional_charts_manifest"), dict) else {}
    return kv_table(
        {
            "是否启用": manifest.get("enabled"),
            "图表目录": manifest.get("charts_dir"),
            "图表数量": len(as_list(manifest.get("items"))),
            "说明": manifest.get("note"),
        }
    )


def voc_productization_block(data: dict[str, Any]) -> str:
    return object_table(
        as_list(data.get("voc_productization_score")),
        [
            ("painpoint", "痛点"),
            ("solution_feasibility", "方案可行性"),
            ("buyer_willingness_to_pay", "支付意愿"),
            ("cost_impact", "成本影响"),
            ("listing_visibility", "页面可见性"),
            ("productization_score", "产品化评分"),
        ],
    )


def voc_rank_block(data: dict[str, Any]) -> str:
    rows = []
    for index, item in enumerate(as_list(data.get("voc_productization_score")), start=1):
        if not isinstance(item, dict):
            continue
        rows.append(
            '<div class="rank-item">'
            f'<span class="rank-no">{index}</span>'
            '<div>'
            f'<strong>{escape(text(item.get("painpoint"), "未命名痛点"))}</strong>'
            f'<p class="muted">方案可行性：{escape(text(item.get("solution_feasibility"), "未知"))}；'
            f'成本影响：{escape(text(item.get("cost_impact"), "未知"))}；'
            f'页面可见性：{escape(text(item.get("listing_visibility"), "未知"))}</p>'
            '</div>'
            f'{badge("产品化 " + text(item.get("productization_score"), "0") + "/10")}'
            '</div>'
        )
    if not rows:
        return '<p class="muted">无可展示的 VOC 产品化评分。</p>'
    return '<div class="rank-list">' + "".join(rows) + "</div>"


def entry_strategy_block(data: dict[str, Any]) -> str:
    return object_table(
        as_list(data.get("entry_strategy")),
        [
            ("entry_type", "切入类型"),
            ("entry_point", "切入点"),
            ("reason", "理由"),
            ("required_validation", "必需验证"),
        ],
    )


def disqualifier_block(data: dict[str, Any]) -> str:
    return object_table(
        as_list(data.get("disqualifiers")),
        [
            ("type", "否决项类型"),
            ("status", "状态"),
            ("severity", "等级"),
            ("reason", "原因"),
            ("required_validation", "必需验证"),
        ],
    )


def risk_flags_block(data: dict[str, Any]) -> str:
    blocks = data.get("normalized_blocks") if isinstance(data.get("normalized_blocks"), dict) else {}
    risks = as_list(blocks.get("risks"))
    rows = [{"risk": item, "status": "待验证"} for item in risks]
    return object_table(rows, [("risk", "风险点"), ("status", "状态")])


def conclusion_block(item: dict[str, Any]) -> str:
    missing = as_list(item.get("missing_data"))
    return (
        "<div class=\"conclusion-block\">"
        f"<p><strong>结论：</strong>{escape(text(item.get('conclusion'), MISSING_VALUE))}</p>"
        f"<p><strong>证据：</strong>{escape(text(item.get('evidence'), MISSING_VALUE))}</p>"
        f"<p><strong>来源：</strong>{escape(text(item.get('source'), MISSING_VALUE))}</p>"
        f"<p><strong>置信度：</strong>{escape(text(item.get('confidence'), MISSING_VALUE))}</p>"
        f"<p><strong>假设：</strong>{escape(text(item.get('assumption'), MISSING_VALUE))}</p>"
        f"<p><strong>缺失数据：</strong>{escape(', '.join(text(x) for x in missing) or NO_MISSING_DATA)}</p>"
        "</div>"
    )


def scorecard(scores: dict[str, Any]) -> str:
    rows = []
    for key, label in SCORE_LABELS.items():
        item = scores.get(key) if isinstance(scores.get(key), dict) else {}
        score = float(item.get("score") or 0)
        max_score = float(item.get("max_score") or 1)
        percent = max(0, min(100, score / max_score * 100))
        rows.append(
            '<div class="scorebar">'
            f'<strong>{escape(label)}</strong>'
            '<div class="track">'
            f'<div class="fill" style="width:{percent:.1f}%"></div>'
            '</div>'
            f'<span>{escape(text(item.get("score"), "0"))}/{escape(text(item.get("max_score"), "0"))}</span>'
            '</div>'
            f'<p class="muted">{escape(text(item.get("reason"), MISSING_VALUE))} 缺失数据：'
            f'{escape(", ".join(text(x) for x in as_list(item.get("missing_data"))) or NO_MISSING_DATA)}</p>'
        )
    rows.append(f'<div class="callout"><strong>总分：</strong>{escape(text(scores.get("total"), "0"))} / 100</div>')
    return "".join(rows)


def active_critical_exists(data: dict[str, Any]) -> bool:
    for item in as_list(data.get("disqualifiers")):
        if isinstance(item, dict) and item.get("status") == "active" and item.get("severity") == "critical":
            return True
    return False


def keyword_strength(data: dict[str, Any]) -> str:
    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    keyword = scores.get("keyword_entry") if isinstance(scores.get("keyword_entry"), dict) else {}
    score = float(keyword.get("score") or 0)
    max_score = float(keyword.get("max_score") or 10)
    ratio = score / max(max_score, 1)
    if ratio >= .75:
        return "强"
    if ratio >= .5:
        return "中"
    if score > 0:
        return "弱"
    return "未知"


def primary_risk(data: dict[str, Any]) -> str:
    if active_critical_exists(data):
        return "严重"
    severities = [item.get("severity") for item in as_list(data.get("disqualifiers")) if isinstance(item, dict)]
    if "critical" in severities:
        return "严重待核"
    if "warning" in severities:
        return "预警"
    return "可控/未知"


def evidence_table(evidence: list[Any]) -> str:
    rows = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        rows.append(
            "<tr>"
            f"<td>{escape(text(item.get('claim')))}</td>"
            f"<td>{escape(text(item.get('source')))}</td>"
            f"<td>{escape(text(item.get('evidence')))}</td>"
            f"<td>{escape(text(item.get('confidence')))}</td>"
            "</tr>"
        )
    if not rows:
        rows.append(f'<tr><td colspan="4" class="muted">{EMPTY_VALUE}。</td></tr>')
    return (
        "<table><thead><tr><th>结论点</th><th>来源</th><th>证据摘要</th><th>置信度</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def downstream_brief(brief: dict[str, Any]) -> str:
    ordered = {
        "推荐产品身份": brief.get("product_identity"),
        "目标人群": brief.get("target_user"),
        "优先关键词入口": as_list(brief.get("priority_keywords")),
        "需要回应的用户问题": as_list(brief.get("user_questions")),
        "可表达差异化": as_list(brief.get("differentiation_points")),
        "必须等待产品事实确认的卖点": as_list(brief.get("facts_to_confirm")),
        "禁止或高风险表达": as_list(brief.get("restricted_claims")),
        "交接备注": brief.get("handoff_notes"),
    }
    return kv_table(ordered)


def assumptions_missing(data: dict[str, Any]) -> str:
    return (
        "<h3>假设</h3>"
        + html_list(as_list(data.get("assumptions")))
        + "<h3>缺失数据</h3>"
        + html_list(as_list(data.get("missing_data")))
    )


def decision_hero_block(decision_cn: str, decision: dict[str, Any], active_critical: bool) -> str:
    label = text(decision.get("label"), "blocked")
    if label in {"blocked", "no-enter"} or active_critical:
        style = "background:linear-gradient(135deg,#d64545,#a72929);box-shadow:0 6px 20px rgba(214,69,69,.22)"
    elif label in {"cautious", "weak"}:
        style = "background:linear-gradient(135deg,#e8a33d,#c7831e);box-shadow:0 6px 20px rgba(232,163,61,.24)"
    else:
        style = ""
    return (
        f'<div class="go" style="{escape(style)}">'
        '<div style="font-size:13px;opacity:.85;letter-spacing:1px">综合结论</div>'
        f'<div class="verdict">{escape(decision_cn)}</div>'
        f'<div class="score">Score {escape(text(decision.get("score"), "0"))} / 100 · '
        f'Confidence {escape(text(decision.get("confidence"), "low"))}</div>'
        '</div>'
    )


def render(data: dict[str, Any], template: str) -> str:
    decision = data.get("decision") if isinstance(data.get("decision"), dict) else {}
    analysis = data.get("analysis") if isinstance(data.get("analysis"), dict) else {}
    input_info = data.get("input") if isinstance(data.get("input"), dict) else {}
    sorftime_status = data.get("sorftime_status") if isinstance(data.get("sorftime_status"), dict) else {}
    data_quality = data.get("data_quality") if isinstance(data.get("data_quality"), dict) else {}
    manifest = data.get("source_manifest") if isinstance(data.get("source_manifest"), dict) else {}

    title_bits = [input_info.get("category_name") or input_info.get("category"), input_info.get("keyword"), "选品调研决策报告"]
    title = " - ".join(text(bit) for bit in title_bits if text(bit).strip())
    blocked_status = decision.get("blocked_status")
    summary = text(decision.get("summary"))
    if blocked_status:
        summary = f"{summary} 当前交付为合法 blocked package，不代表成功选品结论。"
    market_stage_text = MARKET_STAGE_LABELS.get(text(data.get("market_stage")), text(data.get("market_stage"), "未知"))
    evidence_text = text(data.get("evidence_level"), "D_assumption")
    summary = f"{summary} 市场阶段：{market_stage_text}；证据等级：{evidence_text}。"
    ramp = data.get("new_product_ramp_difficulty") if isinstance(data.get("new_product_ramp_difficulty"), dict) else {}
    decision_label = text(decision.get("label"), "blocked")
    decision_cn = DECISION_LABELS.get(decision_label, decision_label)
    active_critical = active_critical_exists(data)
    decision_tone = "risk" if decision_label in {"blocked", "no-enter"} or active_critical else ("good" if decision_label == "enter" else "")
    hero_meta = {
        "站点": input_info.get("site"),
        "类目": input_info.get("category_name") or input_info.get("category"),
        "数据源": input_info.get("data_source") or "sorftime_mcp",
        "隐私模式": data.get("privacy_mode"),
        "生成日期": data.get("generated_at"),
        "样本范围": input_info.get("data_scope") or "standardized",
    }
    hero_meta_html = "".join(
        f'<span class="pill">{escape(key)}：{escape(text(value, "未知"))}</span>'
        for key, value in hero_meta.items()
    )

    values = {
        "report_title": title,
        "hero_subtitle": "基于 BYO-MCP / Sorftime-compatible provider response 的 Amazon 选品、类目调研和进入决策报告。",
        "hero_meta": hero_meta_html,
        "public_safe_notice": PRIVATE_INTERNAL_NOTICE if data.get("privacy_mode") == "private_internal" else PUBLIC_SAFE_NOTICE,
        "footer_notice": (
            "本报告不保存个人身份、会话信息、授权凭证、接口密钥或原始评论全文；"
            "public-safe fixture 仅用于模板测试，不代表实时市场数据或真实选品结论；"
            "public-safe 样例中的竞品链接已禁用或匿名化，不代表真实完整竞品池；"
            "local_preview_url 仅限本机预览，不能作为外部分享链接。"
            if data.get("privacy_mode") != "private_internal"
            else "本报告不保存个人身份、会话信息、授权凭证、接口密钥或原始评论全文；本地真实报告可打开真实 Amazon 商品/品牌/关键词链接，但不得提交 GitHub，不得发布到公网；local_preview_url 仅限本机预览。"
        ),
        "decision_class": decision_label,
        "decision_tone": decision_tone,
        "decision_cn": decision_cn,
        "total_score": text(decision.get("score"), "0"),
        "confidence_cn": CONFIDENCE_LABELS.get(text(decision.get("confidence"), "low"), text(decision.get("confidence"), "低")),
        "data_quality": text(data_quality.get("status"), "blocked"),
        "market_stage_cn": market_stage_text,
        "ramp_level_cn": RAMP_LABELS.get(text(ramp.get("level"), "unknown"), text(ramp.get("level"), "未知")),
        "keyword_strength": keyword_strength(data),
        "primary_risk": primary_risk(data),
        "executive_summary": summary,
        "input_info": input_info_table(input_info),
        "sorftime_status": kv_table(
            {
                "status": sorftime_status.get("status"),
                "blocking_status": sorftime_status.get("blocking_status"),
                "tools": as_list(sorftime_status.get("tools")),
                "checked_at": sorftime_status.get("checked_at"),
                "notes": sorftime_status.get("notes"),
                "privacy_mode": data.get("privacy_mode"),
                "report_language": data.get("report_language"),
                "data_freshness": data_quality.get("data_freshness") or manifest.get("data_freshness"),
            }
        ),
        "scorecard": scorecard(data.get("scores") if isinstance(data.get("scores"), dict) else {}),
        "final_decision": decision_hero_block(decision_cn, decision, active_critical) + kv_table(
            {
                "选品结论": decision_cn,
                "原始标签": decision.get("label"),
                "综合评分": decision.get("score"),
                "置信度": CONFIDENCE_LABELS.get(text(decision.get("confidence"), "low"), decision.get("confidence")),
                "阻断状态": decision.get("blocked_status"),
                "active critical disqualifier": "是" if active_critical else "否",
                "结论摘要": decision.get("summary"),
            }
        ),
        "evidence_table": evidence_table(as_list(data.get("evidence"))),
        "assumptions_missing_data": assumptions_missing(data),
        "next_validation": html_list(as_list(data.get("next_validation_actions"))),
        "downstream_brief": downstream_brief(data.get("downstream_brief") if isinstance(data.get("downstream_brief"), dict) else {}),
    }

    for key, placeholder in ANALYSIS_TO_PLACEHOLDER.items():
        item = analysis.get(key) if isinstance(analysis.get(key), dict) else {}
        values[placeholder] = conclusion_block(item)

    values["sorftime_status"] += "<h3>数据覆盖率</h3>" + data_coverage_block(data)
    values["category_capacity"] += (
        "<h3>市场阶段与证据等级</h3>"
        + model_context(data)
        + "<h3>趋势产品信号</h3>"
        + trending_signals_block(data)
    )
    values["keyword_opportunity"] += "<h3>关键词机会 Top20</h3>" + keyword_opportunity_table(data)
    values["competitor_structure"] += ramp_difficulty_block(data)
    values["price_profit"] += profit_detail_block(data) + "<h3>利润三情景</h3>" + profit_scenarios_block(data)
    values["review_voc"] += (
        "<h3>痛点排行</h3>"
        + voc_rank_block(data)
        + "<h3>VOC 产品化评分</h3>"
        + voc_productization_block(data)
        + "<h3>VOC 趋势摘要</h3>"
        + voc_trend_summary_block(data)
        + "<h3>VOC 机会矩阵</h3>"
        + voc_opportunity_matrix_block(data)
    )
    values["differentiation"] += (
        "<h3>VOC 产品化承接</h3>"
        + voc_productization_block(data)
        + "<h3>产品动作计划</h3>"
        + product_action_plan_block(data)
    )
    if active_critical:
        values["risk"] += '<div class="callout risk">存在 active + critical 硬性否决项，该项目不允许直接判定为“可进入”。</div>'
    values["risk"] += "<h3>硬性否决项</h3>" + disqualifier_block(data) + "<h3>风险标记</h3>" + risk_flags_block(data)
    values["final_decision"] += "<h3>切入策略</h3>" + entry_strategy_block(data) + "<h3>新品爬坡路径</h3>" + ramp_path_block(data)
    values["evidence_table"] += "<h3>可选图表清单</h3>" + charts_manifest_block(data)
    values["next_validation"] += "<h3>验证计划</h3>" + validation_plan_block(data)
    values["downstream_brief"] += "<h3>报告交付包</h3>" + delivery_package_block(data)
    values["delivery_notes"] = delivery_notes_block(data)

    rendered = template
    for key, value in values.items():
        safe_value = value if key in {
            "input_info",
            "sorftime_status",
            "hero_meta",
            "category_capacity",
            "keyword_opportunity",
            "competitor_structure",
            "price_profit",
            "review_voc",
            "differentiation",
            "risk",
            "scorecard",
            "final_decision",
            "evidence_table",
            "assumptions_missing_data",
            "next_validation",
            "downstream_brief",
            "delivery_notes",
        } else escape(text(value))
        rendered = rendered.replace("{{" + key + "}}", safe_value)

    leftovers = sorted(set(re.findall(r"\{\{[^}]+\}\}", rendered)))
    if leftovers:
        raise ValueError(f"Unresolved template placeholders: {', '.join(leftovers)}")
    if CORRUPT_PLACEHOLDER in rendered:
        raise ValueError("Rendered HTML contains corrupt question-mark placeholders.")
    return rendered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render product_selection_report.html from product_selection_data.json.")
    parser.add_argument("product_selection_data", help="Path to product_selection_data.json.")
    parser.add_argument(
        "--out",
        default="dist/product_selection_report.html",
        help="Output HTML path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_path = Path(args.product_selection_data)
    output_path = Path(args.out)
    data = read_json(data_path)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    rendered = render(data, template)
    write_text(output_path, rendered)
    print(json.dumps({"ok": True, "report": output_path.name}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
