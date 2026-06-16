import pytest

from demo.domain import StoreProfile, ValidationRecord, ValidationSummary
from demo.engine import (
    build_campaign,
    calculate_metrics,
    contribution_per_unit,
    minimum_safe_price,
)


def sample_profile(**overrides):
    values = StoreProfile().to_dict()
    values.update(overrides)
    values["channels"] = tuple(values["channels"])
    return StoreProfile(**values)


def test_minimum_safe_price_respects_target_contribution_rate():
    profile = sample_profile(
        ingredient_cost=7.2,
        packaging_cost=1.0,
        platform_fee_rate=0.0,
    )
    floor = minimum_safe_price(profile)
    assert floor == 10.9
    assert contribution_per_unit(profile, floor) / floor >= 0.24


def test_campaign_never_prices_below_floor_or_above_list_price():
    profile = sample_profile(list_price=18.0)
    plan = build_campaign(profile, "不能亏")
    assert plan.offer_price >= minimum_safe_price(profile)
    assert plan.offer_price <= profile.list_price
    assert plan.quantity_limit <= profile.remaining_stock


def test_campaign_rejects_empty_stock():
    profile = sample_profile(remaining_stock=0)
    with pytest.raises(ValueError, match="库存"):
        build_campaign(profile)


def test_metrics_use_baseline_to_calculate_incremental_profit():
    profile = sample_profile()
    plan = build_campaign(profile)
    metrics = calculate_metrics(
        profile,
        plan,
        redeemed_units=16,
        baseline_units=5,
        campaign_cost=10,
    )
    expected = round((16 - 5) * plan.contribution_per_unit - 10, 2)
    assert metrics.incremental_profit == expected
    assert metrics.redemption_rate == pytest.approx(0.8)


def test_validation_summary_go_no_go():
    records = [
        ValidationRecord("A", True, 0.7, 4.0, 120),
        ValidationRecord("B", True, 0.7, 4.0, 100),
        ValidationRecord("C", True, 0.7, 4.0, 100),
        ValidationRecord("D", False, 0.6, 5.0, 50),
        ValidationRecord("E", False, 0.6, 5.0, 50),
    ]
    passed, checks = ValidationSummary(records).go_no_go()
    assert passed is True
    assert len(checks) == 4
