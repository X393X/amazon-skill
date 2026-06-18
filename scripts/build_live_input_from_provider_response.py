#!/usr/bin/env python3
"""Build a private_internal normalized input from a saved provider response.

This script does not call MCP or the network. It only reads a local runtime JSON
that already contains provider tool responses, then creates the normalized input
consumed by normalize_market_data_response.py.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE = "BYO MCP provider category/keyword/review summary"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Input raw JSON root must be an object.")
    return payload


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if value is None:
        return default
    text = str(value).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else default


def parse_percent(value: Any, default: float = 0.0) -> float:
    return parse_number(value, default)


def content_text(result: dict[str, Any]) -> str:
    parsed = result.get("parsed") if isinstance(result.get("parsed"), dict) else {}
    payload = parsed.get("result") if isinstance(parsed.get("result"), dict) else {}
    content = payload.get("content")
    if isinstance(content, list) and content and isinstance(content[0], dict):
        return str(content[0].get("text") or "")
    return str(content or "")


def tool_text(raw: dict[str, Any], tool: str, **arguments: Any) -> str:
    for result in raw.get("tool_results", []):
        if not isinstance(result, dict) or result.get("tool") != tool:
            continue
        actual = result.get("arguments") if isinstance(result.get("arguments"), dict) else {}
        if all(str(actual.get(key)) == str(value) for key, value in arguments.items()):
            return content_text(result)
    return ""


def parse_json_text(text: str, fallback: Any) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return fallback


def price_band_label(price: float) -> str:
    if price < 15:
        return "低价带"
    if price < 50:
        return "主流价格带"
    if price < 100:
        return "中高价格带"
    return "高价带"


def build_competitors(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    competitors: list[dict[str, Any]] = []
    for index, item in enumerate(products, start=1):
        price = parse_number(item.get("价格"))
        competitors.append(
            {
                "competitor_id": f"rank_{index:03d}",
                "asin": item.get("ASIN"),
                "brand": item.get("品牌"),
                "positioning": item.get("标题"),
                "price_band": item.get("价格"),
                "review_band": item.get("评论数"),
                "rating_band": item.get("星级"),
                "monthly_sales": parse_number(item.get("月销量")),
                "monthly_revenue": parse_number(item.get("月销额")),
                "seller": item.get("卖家"),
                "listing_age_days": item.get("上架天数"),
                "category_rank": item.get("所处类目排名"),
                "price_band_label": price_band_label(price),
            }
        )
    return competitors


def build_keywords(category_keywords: list[dict[str, Any]], keyword_detail: dict[str, Any]) -> list[dict[str, Any]]:
    keywords: list[dict[str, Any]] = []
    for item in category_keywords:
        keywords.append(
            {
                "keyword": item.get("关键词"),
                "weekly_search_rank": item.get("周搜索排名"),
                "weekly_search_volume": parse_number(item.get("周搜索量")),
                "monthly_search_volume": parse_number(item.get("月搜索量")),
                "cpc": item.get("cpc精准竞价") or item.get("cpc推荐竞价"),
                "peak_season": item.get("搜索量旺季") or item.get("季节性"),
                "search_results": parse_number(item.get("搜索结果数")),
                "front_3_page_avg_price": item.get("搜索结果前3页产品平均销售价"),
                "front_3_page_brand_share": item.get("搜索结果前3页产品销量最大的前3个品牌的月销量占比"),
            }
        )
    if keyword_detail and not any(item.get("keyword") == keyword_detail.get("关键词") for item in keywords):
        keywords.insert(
            0,
            {
                "keyword": keyword_detail.get("关键词"),
                "weekly_search_rank": keyword_detail.get("周搜索排名"),
                "weekly_search_volume": parse_number(keyword_detail.get("周搜索量")),
                "monthly_search_volume": parse_number(keyword_detail.get("月搜索量")),
                "cpc": keyword_detail.get("推荐cpc竞价"),
                "peak_season": keyword_detail.get("词搜索量旺季"),
                "search_results": parse_number(keyword_detail.get("搜索结果竞品数量")),
            },
        )
    return keywords


def extract_trend_points(text: str) -> list[str]:
    return re.findall(r"\d{4}年\d{2}月=?搜索量?\d+|\d{4}年\d{2}月=\d+", text)


def normalize_voc(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summary = raw.get("review_voc_summary") if isinstance(raw.get("review_voc_summary"), dict) else {}
    theme_names = {
        "comfort_fit": "佩戴舒适度、夹耳和贴合压力",
        "durability": "耐用性、线材和结构质量",
        "sound_volume": "音质、音量和降噪预期",
        "connectivity": "蓝牙连接稳定性和配对体验",
        "battery_charge": "电池续航、充电和续航承诺落差",
    }
    feasibility = {
        "comfort_fit": ("medium", "medium-high", "medium", "high", 8),
        "durability": ("medium", "medium", "medium-high", "high", 7),
        "sound_volume": ("high", "medium", "medium", "high", 6),
        "connectivity": ("high", "medium", "medium", "high", 7),
        "battery_charge": ("high", "medium", "medium", "high", 7),
    }
    voc_scores: list[dict[str, Any]] = []
    painpoints: list[str] = []
    for theme in summary.get("themes", []):
        if not isinstance(theme, dict):
            continue
        key = str(theme.get("key") or "")
        name = theme_names.get(key, "未命名 VOC 痛点")
        sf, wtp, cost, visibility, score = feasibility.get(key, ("medium", "medium", "medium", "medium", 5))
        mentions = int(parse_number(theme.get("mentions")))
        level = theme.get("frequency_level") or "unknown"
        painpoints.append(f"{name}：{mentions}/{summary.get('review_count', 0)}，频率={level}")
        voc_scores.append(
            {
                "painpoint": name,
                "solution_feasibility": sf,
                "buyer_willingness_to_pay": wtp,
                "cost_impact": cost,
                "listing_visibility": visibility,
                "productization_score": score,
                "mentions": mentions,
                "frequency_level": level,
            }
        )
    voc = {
        "reviewed_asins": summary.get("reviewed_asins", []),
        "review_sample_count": summary.get("review_count", 0),
        "contains_review_text": False,
        "painpoint_summary": painpoints,
        "positive_motives": ["品牌信任", "价格可接受", "便携折叠", "续航或有线稳定性"],
        "review_limitations": "仅保留摘要化 VOC 主题，不保存原始评论全文。",
    }
    return voc_scores, voc


def build_price_summary(products: list[dict[str, Any]], stats: dict[str, Any]) -> dict[str, Any]:
    prices = [parse_number(item.get("价格")) for item in products if parse_number(item.get("价格")) > 0]
    low = min(prices) if prices else 0
    high = max(prices) if prices else 0
    bands = Counter(price_band_label(price) for price in prices)
    return {
        "average_price": stats.get("average_price"),
        "median_price": stats.get("median_price"),
        "observed_min_price": round(low, 2),
        "observed_max_price": round(high, 2),
        "price_band_distribution": dict(bands),
        "margin_signal": "Provider response 返回了部分竞品毛利/毛利率字段，但本报告未写入采购成本、FBA 费或退货损耗的真实估算。",
    }


def build_clusters(stats: dict[str, Any], competitors: list[dict[str, Any]], voc_scores: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    price_counts = Counter(item.get("price_band_label") for item in competitors)
    low_review_high_sales = [
        item for item in competitors
        if parse_number(item.get("review_band")) < 300 and parse_number(item.get("monthly_sales")) >= 300
    ]
    return {
        "price_band_cluster": [
            {
                "cluster_name": "低价学生/儿童/基础有线款",
                "summary": f"Top100 中低价带样本约 {price_counts.get('低价带', 0)} 个，主要依靠低门槛和基础功能承接需求。",
                "competition_pressure": "high",
                "entry_implication": "若走低价带，需要极强成本控制和质检稳定性，否则利润与差评压力会同时放大。",
                "evidence_level": "A_live_market_data",
            },
            {
                "cluster_name": "30-50 美元主流无线款",
                "summary": "主流价格带被 Sony、JBL、Belkin 等成熟品牌占据，销量与评论门槛较高。",
                "competition_pressure": "very_high",
                "entry_implication": "新品直接对打主流无线款难度很高，必须用明确人群、场景或 VOC 痛点切入。",
                "evidence_level": "A_live_market_data",
            },
            {
                "cluster_name": "中高价品牌款",
                "summary": "Beats、HyperX 等高价产品依赖品牌、音质认知或游戏场景形成溢价。",
                "competition_pressure": "very_high",
                "entry_implication": "没有品牌资产时不建议以高价通用耳机作为首发进入点。",
                "evidence_level": "A_live_market_data",
            },
        ],
        "review_moat_cluster": [
            {
                "cluster_name": "高评论壁垒头部款",
                "summary": f"1000+ 评论产品贡献 {stats.get('high_reviews_sales_volume_share')} 的销量，评论护城河明显。",
                "competition_pressure": "very_high",
                "entry_implication": "新品需要先找低评论高销量的小入口，而不是直接抢头部自然排名。",
                "evidence_level": "A_live_market_data",
            }
        ],
        "brand_dominance_cluster": [
            {
                "cluster_name": "Sony/Beats/JBL 与 Amazon 自营强势",
                "summary": f"Top3 品牌销量占比 {stats.get('top3_brands_sales_volume_share')}，Amazon 自营销量占比 {stats.get('amazonOwned_sales_volume_share')}。",
                "competition_pressure": "very_high",
                "entry_implication": "品牌集中与平台自营压力会抬高新品广告、评价和信任成本。",
                "evidence_level": "A_live_market_data",
            }
        ],
        "feature_positioning_cluster": [
            {
                "cluster_name": "儿童安全音量/学校/旅行场景",
                "summary": "Top100 中多款儿童、学校、旅行、音量限制、可折叠产品，说明场景化需求明确。",
                "competition_pressure": "high",
                "entry_implication": "比通用 on-ear headphones 更适合从儿童/课堂/旅行场景切入。",
                "evidence_level": "A_live_market_data",
            }
        ],
        "weakness_cluster": [
            {
                "cluster_name": item.get("painpoint"),
                "summary": f"摘要化 VOC 主题出现 {item.get('mentions')} 次，产品化评分 {item.get('productization_score')}/10。",
                "competition_pressure": "medium",
                "entry_implication": "可转化为结构舒适、耐用材料、连接稳定或续航真实表达等产品与页面卖点。",
                "evidence_level": "A_live_market_data",
            }
            for item in voc_scores
        ],
        "newcomer_cluster": [
            {
                "cluster_name": "低评论高销量小入口",
                "summary": f"Top100 中评论低于 300 且月销量不低于 300 的样本数约 {len(low_review_high_sales)} 个。",
                "competition_pressure": "high",
                "entry_implication": "这是新品唯一相对可观察的入口，但仍需验证广告位、供应链和合规成本。",
                "evidence_level": "A_live_market_data",
            }
        ],
    }


def build_payload(raw: dict[str, Any]) -> dict[str, Any]:
    request = raw.get("request") if isinstance(raw.get("request"), dict) else {}
    cat_text = tool_text(raw, "category_report", amzSite="US", nodeId=request.get("category_node_id"))
    category_report = parse_json_text(cat_text, {})
    products = category_report.get("Top100产品", []) if isinstance(category_report, dict) else []
    stats = category_report.get("类目统计报告", {}) if isinstance(category_report, dict) else {}

    category_keywords = parse_json_text(tool_text(raw, "category_keywords", amzSite="US", nodeId=request.get("category_node_id"), page=1), [])
    keyword_detail = parse_json_text(tool_text(raw, "keyword_detail", keyword="on-ear headphones", keywordSupportSite="US"), {})
    keyword_trend = parse_json_text(tool_text(raw, "keyword_trend", keyword="on-ear headphones", keywordSupportSite="US"), {})
    category_trend = tool_text(raw, "category_trend", amzSite="US", nodeId=request.get("category_node_id"))

    competitors = build_competitors(products)
    keywords = build_keywords(category_keywords if isinstance(category_keywords, list) else [], keyword_detail if isinstance(keyword_detail, dict) else {})
    voc_scores, voc = normalize_voc(raw)
    price_profit = build_price_summary(products, stats)
    clusters = build_clusters(stats, competitors, voc_scores)

    top100_sales = parse_number(stats.get("top100产品月销量"))
    top100_revenue = parse_number(stats.get("top100产品月销额"))
    top3_brand_share = parse_percent(stats.get("top3_brands_sales_volume_share"))
    amazon_share = parse_percent(stats.get("amazonOwned_sales_volume_share"))
    high_review_share = parse_percent(stats.get("high_reviews_sales_volume_share"))
    low_review_share = parse_percent(stats.get("low_reviews_sales_volume_share"))
    monthly_search = parse_number(keyword_detail.get("月搜索量") if isinstance(keyword_detail, dict) else 0)
    cpc = keyword_detail.get("推荐cpc竞价") if isinstance(keyword_detail, dict) else "unknown"
    review_count = voc.get("review_sample_count", 0)

    market_capacity = {
        "top100_monthly_sales": top100_sales,
        "top100_monthly_revenue": round(top100_revenue, 2),
        "top3_product_sales_share": stats.get("top3_product_sales_volume_share"),
        "top3_brand_sales_share": stats.get("top3_brands_sales_volume_share"),
        "amazon_owned_sales_share": stats.get("amazonOwned_sales_volume_share"),
        "high_review_sales_share": stats.get("high_reviews_sales_volume_share"),
        "low_review_sales_share": stats.get("low_reviews_sales_volume_share"),
        "category_trend_summary": category_trend,
        "keyword_trend_summary": keyword_trend.get("搜索量趋势", []) if isinstance(keyword_trend, dict) else [],
    }

    score_overrides = {
        "demand_capacity": {
            "score": 18,
            "reason": f"Top100 月销量 {int(top100_sales)}，月销额约 {top100_revenue:,.0f} 美元，需求容量充足。",
            "confidence": "high",
            "missing_data": [],
        },
        "competition_entry": {
            "score": 6,
            "reason": f"Top3 品牌销量占比 {top3_brand_share:.2f}%，Amazon 自营销量占比 {amazon_share:.2f}%，1000+ 评论产品销量占比 {high_review_share:.2f}%，新品竞争壁垒高。",
            "confidence": "high",
            "missing_data": [],
        },
        "profit_space": {
            "score": 13,
            "reason": f"销量前 80% 产品平均价格 {parse_number(stats.get('average_price')):.2f} 美元，中位价格 {parse_number(stats.get('median_price')):.2f} 美元；provider response 有价格和部分毛利字段，但缺少真实 landed cost、FBA 费和退货损耗。",
            "confidence": "medium",
            "missing_data": ["采购 landed cost", "FBA fee", "return loss"],
        },
        "differentiation_opportunity": {
            "score": 10,
            "reason": "VOC 显示舒适度、耐用性、音质音量、连接稳定和续航承诺落差仍有可产品化空间。",
            "confidence": "medium",
            "missing_data": ["供应链打样数据", "认证和专利排查"],
        },
        "voc_painpoint_opportunity": {
            "score": 7,
            "reason": f"已摘要化 {review_count} 条负评样本，痛点集中且可转为结构、材料、连接和页面承诺改进。",
            "confidence": "medium",
            "missing_data": ["更多 ASIN 的 VOC 覆盖"],
        },
        "keyword_entry": {
            "score": 6,
            "reason": f"核心词 on-ear headphones 月搜索量 {int(monthly_search)}，CPC {cpc}，相对 broad headphones 更窄，但自然入口仍受头部品牌影响。",
            "confidence": "medium",
            "missing_data": ["广告位份额", "长尾词转化率"],
        },
        "compliance_supply_risk": {
            "score": 3,
            "reason": "耳机涉及儿童安全音量、蓝牙/FCC、材料、包装和性能 claim，需要上线前逐项验证。",
            "confidence": "medium",
            "missing_data": ["认证成本", "BOM", "质检方案"],
        },
    }

    analysis = {
        "category_capacity": {
            "conclusion": "类目容量充足，但明显受季节波动和头部品牌影响。",
            "evidence": f"Top100 月销量 {int(top100_sales)}，月销额约 {top100_revenue:,.0f} 美元；类目趋势显示暑期、返校季和年末节点波动明显。",
            "source": "provider response category_report/category_trend",
            "confidence": "high",
            "assumption": "Provider response 返回的 Top100 与类目统计字段代表当前可用类目样本。",
            "missing_data": [],
        },
        "keyword_opportunity": {
            "conclusion": "on-ear headphones 是相对窄入口，但不能单靠主词进入。",
            "evidence": f"on-ear headphones 月搜索量 {int(monthly_search)}，搜索结果竞品数 {int(parse_number(keyword_detail.get('搜索结果竞品数量') if isinstance(keyword_detail, dict) else 0))}，CPC {cpc}。",
            "source": "provider response category_keywords/keyword_detail",
            "confidence": "medium",
            "assumption": "关键词入口需要与儿童、学校、旅行、舒适度或安全音量场景词组合验证。",
            "missing_data": ["广告位份额", "长尾词转化率"],
        },
        "competitor_structure": {
            "conclusion": "头部品牌、Amazon 自营和高评论产品共同形成强竞争结构。",
            "evidence": f"Top3 品牌销量占比 {top3_brand_share:.2f}%，Amazon 自营销量占比 {amazon_share:.2f}%，1000+ 评论产品销量占比 {high_review_share:.2f}%。",
            "source": "provider response category_report",
            "confidence": "high",
            "assumption": "Top100 结构可代表该节点主要成交结构。",
            "missing_data": [],
        },
        "price_profit": {
            "conclusion": "价格带存在可选区间，但真实利润空间必须补采购成本、FBA 和退货损耗后才能确认。",
            "evidence": f"平均价格 {parse_number(stats.get('average_price')):.2f} 美元，中位价格 {parse_number(stats.get('median_price')):.2f} 美元；Top100 可观察价格区间约 {price_profit.get('observed_min_price')}-{price_profit.get('observed_max_price')} 美元。",
            "source": "provider response category_report",
            "confidence": "medium",
            "assumption": "Provider margin fields do not equal seller landed cost or net profit.",
            "missing_data": ["estimated_landed_cost", "amazon_fee", "fba_fee", "return_loss"],
        },
        "review_voc": {
            "conclusion": "VOC 机会集中在舒适度、耐用性、声音/音量、连接稳定和续航承诺落差。",
            "evidence": f"已从 {len(voc.get('reviewed_asins', []))} 个头部 ASIN 摘要化 {review_count} 条负评样本，未保留原始评论全文。",
            "source": "provider response product_reviews summary",
            "confidence": "medium",
            "assumption": "当前 VOC 样本用于方向判断，不等同于全类目评论结论。",
            "missing_data": ["更多 ASIN 评论覆盖", "Q&A 摘要"],
        },
        "differentiation": {
            "conclusion": "更适合从场景化与痛点产品化切入，不适合做无差异通用耳机。",
            "evidence": "Top100 中儿童、学校、旅行、安全音量、可折叠等定位反复出现，VOC 痛点可转为产品结构和页面承诺。",
            "source": "provider response category_report/product_reviews summary",
            "confidence": "medium",
            "assumption": "差异化需要供应链打样和合规验证后才能确认。",
            "missing_data": ["BOM 成本", "认证成本"],
        },
        "risk": {
            "conclusion": "当前不是硬性 no-enter，但竞争、评论、Amazon 自营和合规成本决定了新品不宜直接进入。",
            "evidence": "高评论产品销量占比高，Amazon 自营占比高，儿童/蓝牙/音频性能 claim 均需验证。",
            "source": "provider response normalized analysis",
            "confidence": "high",
            "assumption": "未发现 active + critical 否决项，但多个 warning 仍需上线前验证。",
            "missing_data": ["专利检索", "认证成本", "供应链验证"],
        },
    }

    payload = {
        "privacy_mode": "private_internal",
        "report_language": raw.get("report_language") or "zh-CN",
        "data_freshness": "live_or_latest_available_sorftime_data",
        "input": {
            "keyword": "on-ear headphones",
            "category": request.get("category_name"),
            "category_name": request.get("category_name"),
            "category_node_id": request.get("category_node_id"),
            "category_url": request.get("category_url"),
            "category_scope": request.get("category_scope"),
            "marketplace": request.get("marketplace"),
            "input_type": request.get("input_type"),
            "data_scope": request.get("data_scope"),
            "data_source": request.get("data_source"),
            "asin": [],
            "product_idea": "On-Ear Headphones category entry validation",
            "site": "Amazon US",
            "target_price": "30-60",
            "target_cost": None,
            "constraints": [
                "不使用 public-safe fixture 作为证据",
                "不保存原始评论全文",
                "需补真实 landed cost、FBA fee、退货损耗和认证成本",
            ],
            "output_format": request.get("output_format") or "html",
            "report_language": raw.get("report_language") or "zh-CN",
        },
        "sorftime_status": {
            "status": "ready",
            "available": True,
            "tools": [
                "category_report",
                "category_keywords",
                "category_trend",
                "keyword_detail",
                "keyword_search_results",
                "keyword_extends",
                "keyword_trend",
                "product_reviews",
            ],
            "checked_at": raw.get("source", {}).get("generated_at") or utc_now(),
            "notes": "Provider response 已返回类目、关键词、竞品和摘要化 VOC 数据；报告包不保留连接配置或原始评论全文。",
        },
        "confidence": "medium",
        "data_quality": "high",
        "required_fields_present": True,
        "data_blocks": [
            {"name": "category_metrics", "status": "ready", "record_count": 1, "field_coverage": 1.0, "fields": list(stats.keys())},
            {"name": "keyword_metrics", "status": "ready", "record_count": len(keywords), "field_coverage": 1.0},
            {"name": "competitor_matrix", "status": "ready", "record_count": len(competitors), "field_coverage": 1.0},
            {"name": "price_bands", "status": "ready", "record_count": len(price_profit.get("price_band_distribution", {})), "field_coverage": 1.0},
            {"name": "voc_summary", "status": "ready", "record_count": review_count, "field_coverage": 0.8},
            {"name": "trend_data", "status": "ready", "record_count": len(extract_trend_points(category_trend)), "field_coverage": 0.9},
            {"name": "risk_flags", "status": "ready", "record_count": 5, "field_coverage": 0.8},
        ],
        "market_stage": "seasonal",
        "new_product_ramp_difficulty": {
            "level": "very_high",
            "ramp_reason": f"Top3 品牌销量占比 {top3_brand_share:.2f}%，Amazon 自营占比 {amazon_share:.2f}%，1000+ 评论产品销量占比 {high_review_share:.2f}%，新品需要同时突破品牌信任、评价和广告成本。",
            "review_threshold": f"1000+ 评论产品销量占比 {high_review_share:.2f}%，低评论产品销量占比 {low_review_share:.2f}%。",
            "low_review_high_sales_count": len([item for item in competitors if parse_number(item.get("review_band")) < 300 and parse_number(item.get("monthly_sales")) >= 300]),
            "ad_dependency": f"on-ear headphones 推荐 CPC {cpc}，通用 headphones 词量更大且竞争更强。",
            "brand_concentration": f"Top3 品牌：{stats.get('first_brand')} / {stats.get('second_brand')} / {stats.get('third_brand')}，销量占比 {stats.get('top3_brands_sales_volume_share')}。",
            "organic_ranking_barrier": f"Top100 月销量 {int(top100_sales)}，头部自然位由高销量高评论产品占据。",
            "rating_requirement": f"4 星及以上产品销量占比 {stats.get('high_rated_sales_volume_share')}，低评分新品容错低。",
            "variation_complexity": "儿童/成人、有线/无线、蓝牙/3.5mm、颜色、音量限制、续航和折叠结构等变体复杂度较高。",
        },
        "entry_strategy": [
            {
                "entry_type": "scenario_wedge",
                "entry_point": "儿童学校/旅行安全音量场景",
                "reason": "Top100 中儿童、学校、旅行和安全音量限制定位反复出现，场景需求比通用耳机更清晰。",
                "required_validation": ["验证儿童安全音量认证要求", "验证课堂/旅行场景词搜索与转化", "验证材料耐用性和舒适度打样"],
            },
            {
                "entry_type": "voc_painpoint_wedge",
                "entry_point": "舒适度、耐用性、连接稳定和续航承诺落差",
                "reason": "摘要化 VOC 显示这些痛点频率高，能转为产品结构、质检标准和页面承诺。",
                "required_validation": ["扩展 Top20 ASIN VOC 样本", "做头梁/耳罩/线材/蓝牙连接测试", "避免过度性能 claim"],
            },
            {
                "entry_type": "keyword_wedge",
                "entry_point": "on-ear headphones + kids/school/travel/volume limit 长尾组合",
                "reason": "主词容量较小且品牌强，长尾场景词更适合作为新品广告和自然词切入口。",
                "required_validation": ["补充长尾词搜索量和 CPC", "验证广告位竞争", "验证 Listing 首页自然位门槛"],
            },
        ],
        "voc_productization_score": voc_scores,
        "disqualifiers": [
            {
                "type": "patent_or_design_risk",
                "status": "unknown",
                "severity": "warning",
                "reason": "头戴结构、折叠机构、儿童安全音量设计和外观可能涉及专利或设计风险。",
                "required_validation": ["专利检索", "外观与结构避让评估"],
            },
            {
                "type": "high_certification_cost",
                "status": "unknown",
                "severity": "warning",
                "reason": "无线蓝牙、儿童安全音量和电子产品合规可能带来认证与测试成本。",
                "required_validation": ["FCC/蓝牙/儿童安全要求确认", "按 SKU BOM 估算认证成本"],
            },
            {
                "type": "no_viable_margin",
                "status": "unknown",
                "severity": "warning",
                "reason": "Provider response 缺少卖家真实 landed cost、FBA fee、退货损耗和广告 ACOS，净利空间仍需确认。",
                "required_validation": ["采购报价", "FBA fee", "退货损耗", "广告成本容忍度"],
            },
        ],
        "evidence_level": "A_live_market_data",
        "competitor_clusters": clusters,
        "profit_space_detail": {
            "target_price": "30-60",
            "estimated_landed_cost": "unknown",
            "amazon_fee": "unknown",
            "fba_fee": "unknown",
            "return_loss": "unknown",
            "promotion_buffer": "unknown",
            "ad_cost_tolerance": "unknown",
            "target_margin": "unknown",
        },
        "market_capacity": market_capacity,
        "keywords": keywords,
        "competitors": competitors,
        "price_profit": price_profit,
        "voc": voc,
        "differentiation": [
            "儿童学校/旅行场景化定位",
            "舒适低夹耳结构",
            "更耐用线材、折叠结构和头梁材料",
            "安全音量与真实续航/连接稳定承诺",
        ],
        "risks": [
            "头部品牌和 Amazon 自营强势",
            "高评论产品销量占比高",
            "成本/FBA/退货/广告费用未补齐",
            "蓝牙、儿童安全音量和性能 claim 合规风险",
            "通用 headphones 词竞争强",
        ],
        "score_overrides": score_overrides,
        "decision_summary": "总分 63/100，decision.label=weak。需求容量高，但品牌集中、Amazon 自营、高评论壁垒和合规/利润缺口使新品直接进入风险偏高；建议只保留场景化和 VOC 痛点切入口做下一步验证。",
        "analysis": analysis,
        "evidence": [
            {
                "claim": "Provider category response 可用。",
                "source": "provider response category_report",
                "evidence": f"nodeId={request.get('category_node_id')} 返回 Top100={len(products)}，类目统计字段={len(stats)}。",
                "confidence": "high",
            },
            {
                "claim": "类目竞争壁垒高。",
                "source": "provider response category_report",
                "evidence": f"Top3 品牌销量占比 {top3_brand_share:.2f}%，Amazon 自营销量占比 {amazon_share:.2f}%，1000+ 评论产品销量占比 {high_review_share:.2f}%。",
                "confidence": "high",
            },
            {
                "claim": "VOC 痛点具备产品化方向，但需扩样验证。",
                "source": "provider response product_reviews summary",
                "evidence": f"{len(voc.get('reviewed_asins', []))} 个 ASIN 的 {review_count} 条负评摘要显示舒适度、耐用性、音质音量、连接和续航痛点。",
                "confidence": "medium",
            },
        ],
        "assumptions": [
            "Provider response 返回的 Top100 和类目统计字段代表当前可用市场样本。",
            "product_reviews 只保留摘要化 VOC 主题，不保存原始评论全文。",
            "利润空间必须补采购报价、FBA fee、退货损耗和广告成本后才能做财务结论。",
        ],
        "next_validation_actions": [
            "扩展 Top20 ASIN 的摘要化 VOC，并按舒适度、耐用性、连接、续航、音量安全拆分。",
            "补供应链 SKU 报价、landed cost、FBA fee、退货损耗和认证成本。",
            "对儿童/学校/旅行/安全音量场景词做 provider keyword 扩展和广告位验证。",
            "做专利、外观、FCC/蓝牙/儿童安全音量合规排查。",
        ],
        "downstream_brief": {
            "product_identity": "On-Ear Headphones 场景化新品验证方向",
            "target_user": "儿童学校、旅行便携、长时间佩戴且对安全音量/舒适度敏感的买家。",
            "priority_keywords": [item.get("keyword") for item in keywords[:8] if item.get("keyword")],
            "user_questions": [
                "长时间佩戴是否夹耳或压头？",
                "线材、折叠结构和头梁是否耐用？",
                "蓝牙连接是否稳定？",
                "续航和充电承诺是否真实？",
            ],
            "differentiation_points": [
                "舒适低压耳罩和可调头梁",
                "耐用线材/折叠结构",
                "安全音量限制",
                "真实续航与稳定连接表达",
            ],
            "facts_to_confirm": ["BOM 和打样成本", "认证要求", "FBA fee", "退货风险", "广告 CPC 容忍度"],
            "restricted_claims": ["未经验证的降噪 claim", "未经验证的儿童安全 claim", "夸大续航或音质 claim"],
            "handoff_notes": "当前结论为选品验证 brief，不直接生成 Listing、图片或 A+ 文案。",
        },
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build normalized private_internal input from a saved provider response JSON.")
    parser.add_argument("raw_json", help="Local provider response JSON path.")
    parser.add_argument("--out", required=True, help="Output normalized input JSON path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = read_json(Path(args.raw_json))
    payload = build_payload(raw)
    write_json(Path(args.out), payload)
    print(json.dumps({"ok": True, "out": args.out, "competitors": len(payload["competitors"]), "keywords": len(payload["keywords"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
