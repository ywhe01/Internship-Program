from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class StoreProfile:
    store_name: str = "北门饭堂"
    category: str = "快餐简餐"
    product_name: str = "照烧鸡腿饭"
    list_price: float = 18.0
    ingredient_cost: float = 7.2
    packaging_cost: float = 1.0
    platform_fee_rate: float = 0.0
    remaining_stock: int = 20
    weather: str = "小雨"
    campus_rhythm: str = "晚课日"
    goal: str = "清库存"
    channels: tuple[str, ...] = ("微信群", "小红书", "抖音同城")

    @property
    def fixed_unit_cost(self) -> float:
        return self.ingredient_cost + self.packaging_cost

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["channels"] = list(self.channels)
        return data


@dataclass(frozen=True)
class CampaignPlan:
    campaign_name: str
    rationale: str
    publish_time: str
    offer_price: float
    quantity_limit: int
    contribution_per_unit: float
    break_even_units: int
    target_units: int
    coupon_code: str
    group_copy: str
    rednote_copy: str
    video_storyboard: tuple[str, ...]
    risk_note: str
    source: str = "离线策略引擎"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["video_storyboard"] = list(self.video_storyboard)
        return data


@dataclass(frozen=True)
class CampaignMetrics:
    redeemed_units: int
    redemption_rate: float
    revenue: float
    contribution_profit: float
    incremental_profit: float
    roi: float
    verdict: str


@dataclass(frozen=True)
class ValidationRecord:
    store: str
    paid: bool
    asset_adoption_rate: float
    operation_minutes: float
    incremental_profit: float


@dataclass
class ValidationSummary:
    records: list[ValidationRecord] = field(default_factory=list)

    @property
    def paid_count(self) -> int:
        return sum(record.paid for record in self.records)

    @property
    def paid_rate(self) -> float:
        return self.paid_count / len(self.records) if self.records else 0.0

    @property
    def average_adoption_rate(self) -> float:
        if not self.records:
            return 0.0
        return sum(record.asset_adoption_rate for record in self.records) / len(self.records)

    @property
    def average_operation_minutes(self) -> float:
        if not self.records:
            return 0.0
        return sum(record.operation_minutes for record in self.records) / len(self.records)

    @property
    def total_incremental_profit(self) -> float:
        return sum(record.incremental_profit for record in self.records)

    def go_no_go(self, monthly_price: float = 199.0) -> tuple[bool, list[str]]:
        checks = [
            (self.paid_count >= 3, f"真实付费 {self.paid_count}/5（目标 >= 3/5）"),
            (
                self.average_adoption_rate >= 0.60,
                f"素材采用率 {self.average_adoption_rate:.0%}（目标 >= 60%）",
            ),
            (
                self.average_operation_minutes <= 5,
                f"平均操作 {self.average_operation_minutes:.1f} 分钟（目标 <= 5 分钟）",
            ),
            (
                self.total_incremental_profit >= monthly_price * 2,
                f"新增贡献毛利 ¥{self.total_incremental_profit:.0f}（目标 >= ¥{monthly_price * 2:.0f}）",
            ),
        ]
        return all(passed for passed, _ in checks), [
            ("通过｜" if passed else "未通过｜") + label for passed, label in checks
        ]
