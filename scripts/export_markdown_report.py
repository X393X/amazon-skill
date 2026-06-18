#!/usr/bin/env python3
"""Export an auxiliary Markdown product selection report from normalized data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DECISION_LABELS = {
    "enter": "可进入",
    "cautious": "谨慎验证",
    "weak": "机会偏弱",
    "no-enter": "不建议进入",
    "blocked": "数据阻断",
}

SCORE_LABELS = {
    "demand_capacity": "需求容量",
    "competition_entry": "竞争强度",
    "profit_space": "利润空间",
    "differentiation_opportunity": "差异化机会",
    "voc_painpoint_opportunity": "VOC 痛点机会",
    "keyword_entry": "关键词入口",
    "compliance_supply_risk": "合规与供应链风险",
}


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
        return value
    if isinstance(value, list):
        return "；".join(text(item) for item in value if text(item))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def cell(value: Any) -> str:
    return text(value, "未知").replace("|", "\\|").replace("\n", " ")


def table(items: list[Any], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _key, label in columns) + " |"
    sep = "| " + " | ".join("---" for _key, _label in columns) + " |"
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        rows.append("| " + " | ".join(cell(item.get(key)) for key, _label in columns) + " |")
    if not rows:
        rows.append("| " + " | ".join("暂无数据" for _key, _label in columns) + " |")
    return "\n".join([header, sep, *rows])


def kv_table(mapping: dict[str, Any]) -> str:
    return table([{"key": key, "value": value} for key, value in mapping.items()], [("key", "字段"), ("value", "值")])


def title(data: dict[str, Any]) -> str:
    input_info = data.get("input") if isinstance(data.get("input"), dict) else {}
    parts = [
        input_info.get("category_name") or input_info.get("category"),
        input_info.get("keyword"),
        "选品调研决策报告",
    ]
    return " - ".join(text(part) for part in parts if text(part).strip())


def analysis_section(data: dict[str, Any], key: str, heading: str) -> str:
    analysis = data.get("analysis") if isinstance(data.get("analysis"), dict) else {}
    item = analysis.get(key) if isinstance(analysis.get(key), dict) else {}
    return "\n".join(
        [
            f"## {heading}",
            kv_table(
                {
                    "结论": item.get("conclusion"),
                    "证据": item.get("evidence"),
                    "来源": item.get("source"),
                    "置信度": item.get("confidence"),
                    "假设": item.get("assumption"),
                    "缺失数据": as_list(item.get("missing_data")),
                }
            ),
        ]
    )


def render(data: dict[str, Any]) -> str:
    input_info = data.get("input") if isinstance(data.get("input"), dict) else {}
    decision = data.get("decision") if isinstance(data.get("decision"), dict) else {}
    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    blocks = data.get("normalized_blocks") if isinstance(data.get("normalized_blocks"), dict) else {}
    data_quality = data.get("data_quality") if isinstance(data.get("data_quality"), dict) else {}
    ramp = data.get("new_product_ramp_difficulty") if isinstance(data.get("new_product_ramp_difficulty"), dict) else {}
    trend = data.get("trending_product_signals") if isinstance(data.get("trending_product_signals"), dict) else {}
    coverage = data.get("data_coverage_score") if isinstance(data.get("data_coverage_score"), dict) else {}
    charts = data.get("optional_charts_manifest") if isinstance(data.get("optional_charts_manifest"), dict) else {}

    score_rows = []
    for key, label in SCORE_LABELS.items():
        item = scores.get(key) if isinstance(scores.get(key), dict) else {}
        score_rows.append(
            {
                "dimension": label,
                "score": f"{text(item.get('score'), '0')}/{text(item.get('max_score'), '0')}",
                "reason": item.get("reason"),
                "confidence": item.get("confidence"),
            }
        )

    lines = [
        f"# {title(data)}",
        "",
        "HTML 是主交付格式；本 Markdown 仅作为辅助阅读和外部交接文本。",
        "",
        "## 执行摘要",
        kv_table(
            {
                "选品结论": DECISION_LABELS.get(text(decision.get("label")), decision.get("label")),
                "decision.label": decision.get("label"),
                "blocked_status": decision.get("blocked_status"),
                "综合评分": decision.get("score"),
                "置信度": decision.get("confidence"),
                "市场阶段": data.get("market_stage"),
                "新品爬坡难度": ramp.get("level"),
                "证据等级": data.get("evidence_level"),
                "结论摘要": decision.get("summary"),
            }
        ),
        "",
        "## 输入信息",
        kv_table(input_info),
        "",
        "## 数据源状态",
        kv_table(
            {
                "privacy_mode": data.get("privacy_mode"),
                "report_language": data.get("report_language"),
                "data_quality": data_quality.get("status"),
                "row_count": data_quality.get("row_count"),
                "field_coverage": data_quality.get("field_coverage"),
                "data_freshness": data_quality.get("data_freshness"),
                "coverage_score": coverage.get("score"),
                "missing_blocks": as_list(coverage.get("missing_blocks")),
                "missing_fields": as_list(coverage.get("missing_fields")),
            }
        ),
        "",
        analysis_section(data, "category_capacity", "类目容量判断"),
        "",
        "### 趋势产品信号",
        kv_table(trend),
        "",
        analysis_section(data, "keyword_opportunity", "关键词机会判断"),
        "",
        "### 关键词机会 Top20",
        table(
            as_list(blocks.get("keywords"))[:20],
            [
                ("keyword", "关键词"),
                ("monthly_search_volume", "月搜索量"),
                ("weekly_search_volume", "周搜索量"),
                ("cpc", "CPC"),
                ("search_results", "结果数"),
                ("peak_season", "旺季"),
            ],
        ),
        "",
        analysis_section(data, "competitor_structure", "竞品结构判断"),
        "",
        "### 新品爬坡难度",
        kv_table(ramp),
        "",
        "### 竞品 Top20",
        table(
            as_list(blocks.get("competitors"))[:20],
            [
                ("competitor_id", "竞品编号"),
                ("asin", "ASIN"),
                ("brand", "品牌"),
                ("positioning", "定位"),
                ("price_band", "价格带"),
                ("review_band", "评论带"),
                ("rating_band", "评分带"),
            ],
        ),
        "",
        analysis_section(data, "price_profit", "价格带与利润判断"),
        "",
        "### 利润明细与三情景",
        "公开安全样例中的利润明细仅用于模板展示，不代表实时利润估算。",
        "",
        kv_table(data.get("profit_space_detail") if isinstance(data.get("profit_space_detail"), dict) else {}),
        "",
        table(
            as_list(data.get("profit_scenarios")),
            [
                ("scenario", "情景"),
                ("target_price", "目标售价"),
                ("estimated_landed_cost", "到岸成本"),
                ("fees", "费用"),
                ("ad_cost", "广告容忍"),
                ("target_margin", "目标利润"),
                ("conclusion", "结论"),
            ],
        ),
        "",
        analysis_section(data, "review_voc", "评论 VOC 痛点判断"),
        "",
        "### VOC 趋势与机会矩阵",
        kv_table(data.get("voc_trend_summary") if isinstance(data.get("voc_trend_summary"), dict) else {}),
        "",
        table(
            as_list(data.get("voc_opportunity_matrix")),
            [
                ("painpoint", "痛点"),
                ("frequency_signal", "频率信号"),
                ("buyer_motive", "购买动机"),
                ("product_action", "产品动作"),
                ("listing_message", "页面表达"),
                ("priority", "优先级"),
            ],
        ),
        "",
        analysis_section(data, "differentiation", "差异化机会判断"),
        "",
        "### 产品动作计划",
        table(
            as_list(data.get("product_action_plan")),
            [
                ("action", "动作"),
                ("why", "原因"),
                ("validation", "验证"),
                ("priority", "优先级"),
                ("evidence_level", "证据等级"),
            ],
        ),
        "",
        analysis_section(data, "risk", "风险判断"),
        "",
        "### 硬性否决项",
        table(
            as_list(data.get("disqualifiers")),
            [
                ("type", "类型"),
                ("status", "状态"),
                ("severity", "等级"),
                ("reason", "原因"),
                ("required_validation", "验证"),
            ],
        ),
        "",
        "## 评分表",
        table(score_rows, [("dimension", "维度"), ("score", "分数"), ("reason", "原因"), ("confidence", "置信度")]),
        "",
        "## 切入策略与爬坡路径",
        table(
            as_list(data.get("entry_strategy")),
            [
                ("entry_type", "类型"),
                ("entry_point", "切入点"),
                ("reason", "理由"),
                ("required_validation", "验证"),
            ],
        ),
        "",
        table(
            as_list(data.get("ramp_path")),
            [
                ("stage", "阶段"),
                ("goal", "目标"),
                ("actions", "动作"),
                ("validation_standard", "验证标准"),
                ("risk", "风险"),
            ],
        ),
        "",
        "## 证据表",
        table(
            as_list(data.get("evidence")),
            [("claim", "结论点"), ("source", "来源"), ("evidence", "证据摘要"), ("confidence", "置信度")],
        ),
        "",
        "## 假设与缺失数据",
        kv_table({"assumptions": as_list(data.get("assumptions")), "missing_data": as_list(data.get("missing_data"))}),
        "",
        "## 下一步验证计划",
        table(
            as_list(data.get("validation_plan")),
            [
                ("validation_item", "验证项"),
                ("method", "方法"),
                ("pass_standard", "通过标准"),
                ("priority", "优先级"),
                ("blocked_if_missing", "缺失是否阻断"),
            ],
        ),
        "",
        "## 下游 Brief 与交付包",
        kv_table(data.get("downstream_brief") if isinstance(data.get("downstream_brief"), dict) else {}),
        "",
        kv_table(data.get("report_delivery_package") if isinstance(data.get("report_delivery_package"), dict) else {}),
        "",
        "## 交付说明 Delivery Notes",
        "local_preview_url 仅限本机临时预览，不能作为外部分享链接。",
        "",
        kv_table(data.get("delivery") if isinstance(data.get("delivery"), dict) else {}),
        "",
        "## 可选图表清单",
        kv_table(
            {
                "enabled": charts.get("enabled"),
                "charts_dir": charts.get("charts_dir"),
                "items_count": len(as_list(charts.get("items"))),
                "note": charts.get("note"),
            }
        ),
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export product_selection_report.md from product_selection_data.json.")
    parser.add_argument("product_selection_data", help="Path to product_selection_data.json.")
    parser.add_argument("--out", default="dist/product_selection_report.md", help="Output Markdown path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = read_json(Path(args.product_selection_data))
    rendered = render(data)
    if "{{" in rendered or "???" in rendered:
        raise ValueError("Markdown report contains unresolved placeholders.")
    write_text(Path(args.out), rendered)
    print(json.dumps({"ok": True, "markdown_report": Path(args.out).name}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
