from __future__ import annotations

import hashlib
import math
from datetime import date

from demo.content_templates import GOAL_TITLES, group_copy, rednote_copy, storyboard
from demo.domain import CampaignMetrics, CampaignPlan, StoreProfile


MIN_CONTRIBUTION_RATE = 0.25


def contribution_per_unit(profile: StoreProfile, selling_price: float) -> float:
    platform_fee = selling_price * profile.platform_fee_rate
    return round(selling_price - profile.fixed_unit_cost - platform_fee, 2)


def minimum_safe_price(
    profile: StoreProfile, minimum_rate: float = MIN_CONTRIBUTION_RATE
) -> float:
    denominator = 1 - profile.platform_fee_rate - minimum_rate
    if denominator <= 0:
        raise ValueError("平台费率与目标贡献率之和必须小于 100%")
    return round(profile.fixed_unit_cost / denominator, 1)


def recommend_price(profile: StoreProfile) -> float:
    floor = minimum_safe_price(profile)
    discount_rate = {
        "清库存": 0.72,
        "拉新": 0.78,
        "复购": 0.82,
        "提客单": 0.90,
    }.get(profile.goal, 0.80)
    candidate = round(profile.list_price * discount_rate, 1)
    return min(profile.list_price, max(floor, candidate))


def _coupon_code(profile: StoreProfile) -> str:
    seed = (
        f"{profile.store_name}|{profile.product_name}|{profile.goal}|{date.today().isoformat()}"
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:3].upper()
    prefix = {
        "清库存": "WK",
        "拉新": "NEW",
        "复购": "BACK",
        "提客单": "TEAM",
    }.get(profile.goal, "GO")
    return f"{prefix}{profile.remaining_stock}{digest}"


def build_campaign(profile: StoreProfile, owner_note: str = "") -> CampaignPlan:
    if profile.list_price <= 0 or profile.fixed_unit_cost < 0:
        raise ValueError("价格和成本必须为合理的非负数")
    if profile.remaining_stock <= 0:
        raise ValueError("剩余库存必须大于 0")

    price = recommend_price(profile)
    contribution = contribution_per_unit(profile, price)
    quantity_limit = min(profile.remaining_stock, 30)
    target_units = max(1, math.ceil(quantity_limit * 0.70))
    campaign_cost = 0.0
    break_even = (
        math.ceil(campaign_cost / contribution) if contribution > 0 and campaign_cost else 0
    )
    code = _coupon_code(profile)

    timing = "17:10" if "晚" in profile.campus_rhythm else "11:10"
    weather_reason = (
        f"{profile.weather}降低了远距离就餐意愿"
        if any(word in profile.weather for word in ("雨", "雪", "冷"))
        else f"{profile.weather}适合做短时段触达"
    )
    owner_context = f"；结合老板补充「{owner_note.strip()}」" if owner_note.strip() else ""
    rationale = (
        f"{weather_reason}，{profile.campus_rhythm}带来集中下课客流；"
        f"用限量 {quantity_limit} 份控制折扣风险{owner_context}。"
    )
    risk = (
        f"建议价不低于安全价 ¥{minimum_safe_price(profile):.1f}；"
        f"当前单份贡献毛利 ¥{contribution:.1f}，禁止追加无上限折扣。"
    )

    return CampaignPlan(
        campaign_name=GOAL_TITLES.get(profile.goal, "今日限量行动"),
        rationale=rationale,
        publish_time=timing,
        offer_price=price,
        quantity_limit=quantity_limit,
        contribution_per_unit=contribution,
        break_even_units=break_even,
        target_units=target_units,
        coupon_code=code,
        group_copy=group_copy(profile, price, quantity_limit, code),
        rednote_copy=rednote_copy(profile, price, quantity_limit),
        video_storyboard=storyboard(profile, price),
        risk_note=risk,
    )


def calculate_metrics(
    profile: StoreProfile,
    plan: CampaignPlan,
    redeemed_units: int,
    campaign_cost: float = 0.0,
    baseline_units: int = 0,
) -> CampaignMetrics:
    redeemed = max(0, min(redeemed_units, plan.quantity_limit))
    baseline = max(0, min(baseline_units, redeemed))
    revenue = round(redeemed * plan.offer_price, 2)
    contribution = round(redeemed * plan.contribution_per_unit - campaign_cost, 2)
    incremental = round(
        (redeemed - baseline) * plan.contribution_per_unit - campaign_cost, 2
    )
    roi = round(incremental / campaign_cost, 2) if campaign_cost > 0 else 0.0
    rate = redeemed / plan.quantity_limit if plan.quantity_limit else 0.0

    if incremental <= 0:
        verdict = "停止复用：活动未产生正向增量贡献毛利。"
    elif redeemed >= plan.target_units:
        verdict = "达到目标：保留时段和价格，下次只测试素材变量。"
    else:
        verdict = "部分有效：保留限量机制，缩短文案并提前 20 分钟发布。"

    return CampaignMetrics(
        redeemed_units=redeemed,
        redemption_rate=rate,
        revenue=revenue,
        contribution_profit=contribution,
        incremental_profit=incremental,
        roi=roi,
        verdict=verdict,
    )
