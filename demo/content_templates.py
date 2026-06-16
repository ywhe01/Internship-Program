from __future__ import annotations

from demo.domain import StoreProfile


GOAL_TITLES = {
    "清库存": "晚课续命餐",
    "拉新": "新同学第一餐",
    "复购": "老朋友返场券",
    "提客单": "宿舍拼单套餐",
}


def group_copy(profile: StoreProfile, price: float, limit: int, code: str) -> str:
    return (
        f"今晚晚课别饿着｜{profile.store_name} 的{profile.product_name}"
        f"限量 {limit} 份，到店出示「{code}」仅 ¥{price:.1f}。"
        f"{profile.weather}天热饭更舒服，售完即止。"
    )


def rednote_copy(profile: StoreProfile, price: float, limit: int) -> str:
    return (
        f"标题：晚课后还能吃到的热饭，{profile.product_name} ¥{price:.1f}\n\n"
        f"今天是{profile.campus_rhythm}，店里把最后 {limit} 份做成限量晚餐。"
        "不是预制图，按到店顺序现取；建议下课前十分钟出发。\n\n"
        f"#校园美食 #{profile.product_name} #晚课吃什么"
    )


def storyboard(profile: StoreProfile, price: float) -> tuple[str, ...]:
    return (
        f"0–3秒｜雨夜校门与晚课铃声：『下课了，食堂又关了？』",
        f"3–8秒｜鸡腿切面和热气特写：『{profile.product_name}，今晚限量』",
        f"8–12秒｜价格牌入镜：『到店 ¥{price:.1f}，售完即止』",
        "12–15秒｜门店路线与核销口令：『下课向北门走 3 分钟』",
    )
