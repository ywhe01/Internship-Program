from __future__ import annotations

import json
import os
from dataclasses import replace
from typing import Any

from demo.domain import CampaignPlan, StoreProfile
from demo.engine import build_campaign


def _client_settings() -> tuple[str | None, str | None, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    return api_key, base_url, model


def model_available() -> bool:
    api_key, _, _ = _client_settings()
    return bool(api_key)


def build_campaign_with_optional_model(
    profile: StoreProfile, owner_note: str, use_model: bool
) -> tuple[CampaignPlan, str | None]:
    deterministic_plan = build_campaign(profile, owner_note)
    if not use_model:
        return deterministic_plan, None

    api_key, base_url, model = _client_settings()
    if not api_key:
        return deterministic_plan, "未配置 OPENAI_API_KEY，已使用离线策略引擎。"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url or None)
        payload = {
            "store": profile.to_dict(),
            "owner_note": owner_note,
            "safe_plan": deterministic_plan.to_dict(),
        }
        prompt = (
            "你是校园周边餐饮门店的经营编辑。保留 safe_plan 中所有价格、数量、"
            "毛利、核销码和风险约束，只润色 campaign_name、rationale、group_copy、"
            "rednote_copy 与 video_storyboard。输出 JSON，不得夸大、不得制造虚假评价。\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        response = client.responses.create(
            model=model,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        data: dict[str, Any] = json.loads(response.output_text)
        plan = replace(
            deterministic_plan,
            campaign_name=str(data.get("campaign_name", deterministic_plan.campaign_name)),
            rationale=str(data.get("rationale", deterministic_plan.rationale)),
            group_copy=str(data.get("group_copy", deterministic_plan.group_copy)),
            rednote_copy=str(data.get("rednote_copy", deterministic_plan.rednote_copy)),
            video_storyboard=tuple(
                data.get("video_storyboard", deterministic_plan.video_storyboard)
            ),
            source=f"离线决策 + {model} 内容润色",
        )
        return plan, None
    except Exception as exc:  # Network/model failures must not break the interview demo.
        return deterministic_plan, f"模型调用失败，已安全回退离线模式：{exc}"
