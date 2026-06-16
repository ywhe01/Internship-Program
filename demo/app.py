from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from demo.domain import StoreProfile, ValidationRecord, ValidationSummary
from demo.engine import calculate_metrics, minimum_safe_price
from demo.llm_adapter import build_campaign_with_optional_model, model_available


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(__file__).resolve().parent / "data"

NAVY = "#18324A"
TEAL = "#0E7C74"
ORANGE = "#F28C45"
INK = "#20262D"
MUTED = "#65737C"
PAPER = "#F4F6F5"


def load_json(name: str):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def find_font(size: int, bold: bool = False):
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def campaign_poster(store: StoreProfile, plan) -> Image.Image:
    image = Image.new("RGB", (900, 1120), "#F1F4F1")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 900, 250), fill=NAVY)
    draw.text((70, 60), plan.campaign_name, font=find_font(70, True), fill="white")
    draw.text(
        (74, 155),
        f"{store.campus_rhythm} · {store.weather} · 限量 {plan.quantity_limit} 份",
        font=find_font(30),
        fill="#D9E7E8",
    )
    draw.rounded_rectangle((65, 310, 835, 760), radius=20, fill="white")
    draw.text((110, 355), store.product_name, font=find_font(46, True), fill=INK)
    draw.text((110, 445), "到店核销价", font=find_font(28), fill=MUTED)
    draw.text((105, 495), f"¥ {plan.offer_price:.1f}", font=find_font(92, True), fill=ORANGE)
    draw.line((110, 625, 790, 625), fill="#D9E0E2", width=3)
    draw.text(
        (110, 660),
        f"口令：{plan.coupon_code}",
        font=find_font(34, True),
        fill=TEAL,
    )
    draw.text((70, 825), "晚课结束，向北门走 3 分钟", font=find_font(40, True), fill=NAVY)
    draw.text(
        (70, 900),
        "现做热饭 · 售完即止 · 活动不与其他优惠同享",
        font=find_font(25),
        fill=MUTED,
    )
    draw.rectangle((70, 1015, 830, 1023), fill=TEAL)
    return image


def inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {PAPER}; }}
        .block-container {{ max-width: 1180px; padding-top: 1.5rem; padding-bottom: 4rem; }}
        h1, h2, h3 {{ color: {NAVY}; letter-spacing: 0; }}
        h1 {{ font-size: 2rem !important; margin-bottom: 0.2rem !important; }}
        h2 {{ font-size: 1.25rem !important; margin-top: 1rem !important; }}
        div[data-testid="stMetric"] {{
            background: white; border: 1px solid #D7DFE1; border-radius: 6px;
            padding: 0.8rem 1rem;
        }}
        div[data-testid="stMetricLabel"] {{ color: {MUTED}; }}
        .action-strip {{
            background: {NAVY}; color: white; padding: 18px 22px; border-radius: 6px;
            margin: 12px 0 18px 0;
        }}
        .action-strip b {{ color: white; font-size: 1.15rem; }}
        .eyebrow {{ color: {TEAL}; font-weight: 700; font-size: 0.82rem; }}
        .quiet {{ color: {MUTED}; font-size: 0.9rem; }}
        .risk {{
            border-left: 4px solid {ORANGE}; background: #FFF4EC; padding: 12px 14px;
            color: {INK}; margin-top: 8px;
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 10px; }}
        .stTabs [data-baseweb="tab"] {{ border-radius: 4px; padding: 8px 14px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="邻校掌柜｜AI 增长值班经理",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

sample = load_json("sample_store.json")
with st.sidebar:
    st.markdown("### 门店档案")
    store_name = st.text_input("门店名", sample["store_name"])
    category = st.selectbox("品类", ["快餐简餐", "茶饮", "烘焙", "夜宵"], index=0)
    product_name = st.text_input("主推单品", sample["product_name"])
    price_col, stock_col = st.columns(2)
    list_price = price_col.number_input("原价", 1.0, 200.0, float(sample["list_price"]), 0.5)
    stock = stock_col.number_input("库存", 1, 200, int(sample["remaining_stock"]), 1)
    cost_col, pack_col = st.columns(2)
    ingredient_cost = cost_col.number_input(
        "食材成本", 0.0, 100.0, float(sample["ingredient_cost"]), 0.1
    )
    packaging_cost = pack_col.number_input(
        "包装成本", 0.0, 50.0, float(sample["packaging_cost"]), 0.1
    )
    platform_fee = st.slider("平台费率", 0, 30, int(sample["platform_fee_rate"] * 100))
    weather = st.selectbox("天气", ["小雨", "晴", "高温", "降温", "大风"])
    rhythm = st.selectbox("校园节奏", ["晚课日", "普通上课日", "考试周", "周末", "开学周"])
    goal = st.segmented_control(
        "今日目标", ["清库存", "拉新", "复购", "提客单"], default="清库存"
    )
    channels = st.multiselect(
        "发布渠道", ["微信群", "小红书", "抖音同城"], default=sample["channels"]
    )
    use_model = st.toggle(
        "使用真实模型润色",
        value=False,
        help="仅润色内容，不允许模型修改价格、毛利与数量约束。",
        disabled=not model_available(),
    )
    if not model_available():
        st.caption("当前为稳定离线模式；配置环境变量后可启用模型润色。")

profile = StoreProfile(
    store_name=store_name,
    category=category,
    product_name=product_name,
    list_price=list_price,
    ingredient_cost=ingredient_cost,
    packaging_cost=packaging_cost,
    platform_fee_rate=platform_fee / 100,
    remaining_stock=int(stock),
    weather=weather,
    campus_rhythm=rhythm,
    goal=goal or "清库存",
    channels=tuple(channels),
)

st.markdown('<div class="eyebrow">CAMPUS MICRO BUSINESS AI</div>', unsafe_allow_html=True)
st.title("邻校掌柜")
st.markdown(
    '<div class="quiet">校园周边餐饮店的 AI 增长值班经理。先算清楚，再生成内容，最后用核销结果复盘。</div>',
    unsafe_allow_html=True,
)

owner_note = st.text_area(
    "老板今天补充了什么？",
    value="今天下雨，鸡腿饭还剩20份；晚课学生多，想清库存但不能亏。",
    height=85,
)

if "plan" not in st.session_state:
    st.session_state.plan, _ = build_campaign_with_optional_model(profile, owner_note, False)
if st.button("生成今日行动", type="primary", width="stretch"):
    st.session_state.plan, warning = build_campaign_with_optional_model(
        profile, owner_note, use_model
    )
    st.session_state.warning = warning

plan = st.session_state.plan
if st.session_state.get("warning"):
    st.warning(st.session_state.warning)

st.markdown(
    f"""
    <div class="action-strip">
      <b>{plan.publish_time} 发起「{plan.campaign_name}」</b><br>
      {plan.rationale}
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(5)
metric_cols[0].metric("建议价", f"¥{plan.offer_price:.1f}", f"原价 ¥{profile.list_price:.1f}")
metric_cols[1].metric("单份贡献毛利", f"¥{plan.contribution_per_unit:.1f}")
metric_cols[2].metric("限量", f"{plan.quantity_limit} 份")
metric_cols[3].metric("目标核销", f"{plan.target_units} 份")
metric_cols[4].metric("安全底价", f"¥{minimum_safe_price(profile):.1f}")
st.markdown(f'<div class="risk">{plan.risk_note}</div>', unsafe_allow_html=True)

action_tab, asset_tab, review_tab, validation_tab = st.tabs(
    ["经营动作", "素材工坊", "核销复盘", "两周验证看板"]
)

with action_tab:
    left, right = st.columns([1.15, 0.85])
    with left:
        st.subheader("为什么是这条动作")
        st.write(plan.rationale)
        st.subheader("老板只需完成三步")
        st.markdown(
            f"""
            1. **{plan.publish_time}** 将生成素材发布到所选渠道<br>
            2. 收银时记录专属口令 **{plan.coupon_code}**<br>
            3. 营业结束填写核销数，决定明天是否复用
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.subheader("决策边界")
        st.write(f"活动价格不得低于 ¥{minimum_safe_price(profile):.1f}")
        st.write(f"最多释放 {plan.quantity_limit} 份库存")
        st.write(f"目标为核销 {plan.target_units} 份，而非追求播放量")
        st.caption(f"决策来源：{plan.source}")

with asset_tab:
    copy_col, poster_col = st.columns([1, 0.9])
    with copy_col:
        st.subheader("微信群文案")
        st.code(plan.group_copy, language=None)
        st.subheader("小红书图文")
        st.code(plan.rednote_copy, language=None)
        st.subheader("15 秒视频分镜")
        for item in plan.video_storyboard:
            st.write(item)
    with poster_col:
        poster = campaign_poster(profile, plan)
        st.image(poster, caption="活动海报实时预览", width="stretch")
        from io import BytesIO

        buffer = BytesIO()
        poster.save(buffer, format="PNG")
        st.download_button(
            "下载活动海报",
            data=buffer.getvalue(),
            file_name="campaign-poster.png",
            mime="image/png",
            width="stretch",
        )

with review_tab:
    st.subheader("输入实际结果")
    col1, col2, col3 = st.columns(3)
    redeemed = col1.number_input(
        "核销份数", 0, plan.quantity_limit, min(16, plan.quantity_limit), 1
    )
    baseline = col2.number_input("自然销量基线", 0, int(redeemed), min(5, int(redeemed)), 1)
    campaign_cost = col3.number_input("额外活动成本", 0.0, 1000.0, 0.0, 5.0)
    results = calculate_metrics(
        profile, plan, int(redeemed), float(campaign_cost), int(baseline)
    )
    result_cols = st.columns(4)
    result_cols[0].metric("核销率", f"{results.redemption_rate:.0%}")
    result_cols[1].metric("活动流水", f"¥{results.revenue:.1f}")
    result_cols[2].metric("贡献毛利", f"¥{results.contribution_profit:.1f}")
    result_cols[3].metric("增量贡献毛利", f"¥{results.incremental_profit:.1f}")
    st.info(results.verdict)

with validation_tab:
    records = [
        ValidationRecord(**row) for row in load_json("validation_results.json")
    ]
    summary = ValidationSummary(records)
    passed, checks = summary.go_no_go()
    summary_cols = st.columns(4)
    summary_cols[0].metric("真实付费", f"{summary.paid_count}/5")
    summary_cols[1].metric("素材采用率", f"{summary.average_adoption_rate:.0%}")
    summary_cols[2].metric("平均操作时长", f"{summary.average_operation_minutes:.1f} 分钟")
    summary_cols[3].metric("新增贡献毛利", f"¥{summary.total_incremental_profit:.0f}")
    chart_col, conclusion_col = st.columns([1.25, 0.75])
    with chart_col:
        st.image(ROOT / "assets" / "dashboard.png", width="stretch")
    with conclusion_col:
        st.subheader("模拟验证结论")
        st.success("GO：进入下一轮验证" if passed else "NO-GO：缩小场景或停止开发")
        for check in checks:
            st.write(check)
        st.caption("本页为演示数据，真实两周实验需替换为商户核销记录。")

st.divider()
st.caption(
    "演示边界：不自动发布、不生成虚假评价、不把模型输出直接用于定价。"
    "价格与毛利由确定性规则计算，真实模型仅可润色内容。"
)
