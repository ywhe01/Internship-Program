from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DATA = ROOT / "demo" / "data"

NAVY = "#18324A"
TEAL = "#0E7C74"
ORANGE = "#F28C45"
INK = "#20262D"
MUTED = "#66757E"
PAPER = "#F3F5F3"
PALE_TEAL = "#E3F0ED"
PALE_ORANGE = "#FFF0E5"
LINE = "#D4DCDE"
WHITE = "#FFFFFF"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
        if bold
        else Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        if bold
        else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def wrapped_lines(
    draw: ImageDraw.ImageDraw, text: str, text_font, max_width: int
) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        current = ""
        for char in paragraph:
            candidate = current + char
            if draw.textlength(candidate, font=text_font) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = char
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    text_font,
    fill: str,
    max_width: int,
    line_gap: int = 10,
    max_lines: int | None = None,
) -> int:
    lines = wrapped_lines(draw, text, text_font, max_width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + "…"
    for line in lines:
        draw.text((x, y), line, font=text_font, fill=fill)
        y += text_font.size + line_gap
    return y


def rounded(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill: str,
    outline: str | None = None,
    width: int = 1,
):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def title_block(draw, eyebrow: str, title: str, subtitle: str, width: int):
    draw.text((80, 58), eyebrow, font=font(23, True), fill=TEAL)
    draw.text((80, 100), title, font=font(50, True), fill=NAVY)
    draw_wrapped(draw, subtitle, 80, 172, font(24), MUTED, width - 160, 8, 2)
    draw.rectangle((80, 238, width - 80, 244), fill=ORANGE)


def generate_workflow():
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    title_block(
        draw,
        "PRODUCT WORKFLOW",
        "从一句老板话，到一条可复盘的经营动作",
        "不是再做一个文案生成器，而是把成本约束、内容执行和核销结果放进同一个闭环。",
        width,
    )
    steps = [
        ("01", "老板输入", "语音、菜单、库存、昨日订单"),
        ("02", "场景补充", "天气、校历、课程节奏、门店历史"),
        ("03", "先算清楚", "安全底价、单份贡献毛利、限量"),
        ("04", "一键执行", "海报、群文案、短视频分镜"),
        ("05", "核销复盘", "增量订单、贡献毛利、次日建议"),
    ]
    card_w, gap = 270, 25
    start_x, y = 80, 330
    for index, (number, heading, body) in enumerate(steps):
        x = start_x + index * (card_w + gap)
        fill = WHITE if index not in (2, 4) else (PALE_ORANGE if index == 2 else PALE_TEAL)
        rounded(draw, (x, y, x + card_w, y + 330), 12, fill, LINE, 2)
        draw.text((x + 28, y + 28), number, font=font(28, True), fill=ORANGE)
        draw.text((x + 28, y + 90), heading, font=font(34, True), fill=NAVY)
        draw_wrapped(draw, body, x + 28, y + 150, font(24), INK, card_w - 56, 12, 4)
        if index < len(steps) - 1:
            ax = x + card_w + 8
            ay = y + 165
            draw.line((ax, ay, ax + 12, ay), fill=TEAL, width=4)
            draw.polygon(
                [(ax + 12, ay - 8), (ax + 24, ay), (ax + 12, ay + 8)], fill=TEAL
            )
    rounded(draw, (80, 725, 1520, 820), 8, NAVY)
    draw.text(
        (112, 754),
        "最终交付：今天做什么  ·  为什么这样做  ·  是否赚钱  ·  明天要不要复用",
        font=font(31, True),
        fill=WHITE,
    )
    image.save(ASSETS / "workflow.png")


def generate_chat_demo():
    image = Image.new("RGB", (900, 1220), "#E9EEEE")
    draw = ImageDraw.Draw(image)
    rounded(draw, (115, 35, 785, 1185), 45, WHITE, "#AAB8BD", 3)
    draw.rectangle((140, 70, 760, 200), fill=NAVY)
    draw.text((185, 98), "邻校掌柜", font=font(42, True), fill=WHITE)
    draw.text((185, 154), "今日经营值班 · 北门饭堂", font=font(23), fill="#D9E6E9")
    draw.ellipse((695, 120, 720, 145), fill="#4DC7A1")

    rounded(draw, (280, 245, 720, 385), 18, "#DDF0EA")
    draw.text((310, 267), "老板", font=font(21, True), fill=TEAL)
    draw_wrapped(
        draw,
        "今天下雨，鸡腿饭还剩20份；晚课学生多，想清库存但不能亏。",
        310,
        308,
        font(24),
        INK,
        370,
        9,
        3,
    )

    draw.text((175, 430), "17:10 · 今日建议", font=font(23, True), fill=TEAL)
    rounded(draw, (155, 470, 745, 695), 16, PALE_ORANGE)
    draw.text((190, 500), "晚课续命餐", font=font(35, True), fill=NAVY)
    draw.text((190, 560), "限20份  ·  到店 ¥12.9", font=font(31, True), fill=ORANGE)
    draw.text((190, 620), "单份贡献毛利 ¥4.1  ·  目标核销 14份", font=font(23), fill=INK)
    draw.text((190, 660), "安全底价 ¥10.9，禁止追加无上限折扣", font=font(21), fill=MUTED)

    rounded(draw, (155, 730, 745, 880), 16, PALE_TEAL)
    draw.text((190, 760), "素材已备好", font=font(29, True), fill=TEAL)
    draw.text((190, 815), "海报  ·  群文案  ·  15秒视频分镜", font=font(24), fill=INK)
    draw.text((190, 853), "发布前仍由老板确认，不自动代发", font=font(20), fill=MUTED)

    rounded(draw, (155, 920, 745, 1070), 16, "#EEF2F5")
    draw.text((190, 950), "专属核销码", font=font(23, True), fill=NAVY)
    draw.text((190, 995), "WK20A7D", font=font(38, True), fill=INK)
    draw.text((430, 1003), "预计售出 ≥14份即达标", font=font(20), fill=MUTED)
    image.save(ASSETS / "chat-demo.png")


def generate_campaign_poster():
    width, height = 900, 1200
    image = Image.new("RGB", (width, height), "#F0F3EF")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 285), fill=NAVY)
    draw.text((70, 65), "晚课续命餐", font=font(74, True), fill=WHITE)
    draw.text((75, 180), "雨夜 · 北门 · 限量 20 份", font=font(32), fill="#D8E6E8")

    rounded(draw, (65, 340, 835, 830), 20, WHITE)
    draw.text((110, 395), "照烧鸡腿饭", font=font(50, True), fill=INK)
    draw.text((110, 485), "到店核销价", font=font(29), fill=MUTED)
    draw.text((105, 535), "¥ 12.9", font=font(105, True), fill=ORANGE)
    draw.line((110, 690, 790, 690), fill=LINE, width=3)
    draw.text((110, 728), "口令：WK20A7D", font=font(35, True), fill=TEAL)
    draw.text((110, 782), "单份贡献毛利 ¥4.1，不做亏本折扣", font=font(23), fill=MUTED)

    draw.text((70, 900), "晚课结束，向北门走 3 分钟", font=font(42, True), fill=NAVY)
    draw_wrapped(
        draw,
        "现做热饭 · 售完即止 · 活动不与其他优惠同享",
        70,
        980,
        font(27),
        MUTED,
        760,
    )
    draw.rectangle((70, 1090, 830, 1100), fill=TEAL)
    draw.text((70, 1125), "北门饭堂  /  17:10 开始核销", font=font(25, True), fill=INK)
    image.save(ASSETS / "campaign-poster.png")


def generate_validation_plan():
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    title_block(
        draw,
        "14-DAY VALIDATION",
        "两周只验证一件事：老板是否愿为增量毛利付费",
        "每一阶段都有行为证据和停止条件，不用“觉得不错”代替真实付费。",
        width,
    )

    phases = [
        ("D1–3", "问题验证", "15位老板 + 30名学生\n确认痛点、现有做法、付费上限", TEAL),
        ("D4–6", "人工 MVP", "招募5店，每店交付≥3次行动\n记录采用率与老板修改次数", NAVY),
        ("D7–10", "核销实验", "普通促销 vs AI方案\n记录核销、客单与贡献毛利", ORANGE),
        ("D11–14", "真实付费", "收取69元订金/首月费\n复访未付费原因并做去留判断", TEAL),
    ]
    x_positions = [85, 460, 835, 1210]
    draw.line((150, 490, 1450, 490), fill="#B8C4C8", width=8)
    for x, (days, heading, body, color) in zip(x_positions, phases):
        draw.ellipse((x + 80, 455, x + 150, 525), fill=color, outline=WHITE, width=5)
        draw.text((x, 330), days, font=font(34, True), fill=color)
        draw.text((x, 385), heading, font=font(31, True), fill=NAVY)
        rounded(draw, (x, 560, x + 305, 745), 10, WHITE, LINE, 2)
        draw_wrapped(draw, body, x + 24, 592, font(22), INK, 257, 12, 5)

    rounded(draw, (80, 790, 1520, 850), 7, NAVY)
    draw.text(
        (110, 805),
        "GO：≥3/5店付费  ·  素材采用率≥60%  ·  日操作≤5分钟  ·  7天增量毛利≥月费2倍",
        font=font(26, True),
        fill=WHITE,
    )
    image.save(ASSETS / "validation-plan.png")


def generate_dashboard():
    records = json.loads((DATA / "validation_results.json").read_text(encoding="utf-8"))
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(image)
    title_block(
        draw,
        "VALIDATION DASHBOARD · SIMULATED DATA",
        "种子店验证看板",
        "示例数据仅用于展示指标体系。真实实验将替换为商户核销记录与付款凭证。",
        width,
    )

    paid_count = sum(row["paid"] for row in records)
    adoption = sum(row["asset_adoption_rate"] for row in records) / len(records)
    minutes = sum(row["operation_minutes"] for row in records) / len(records)
    profit = sum(row["incremental_profit"] for row in records)
    metrics = [
        ("真实付费", f"{paid_count}/5", "目标 ≥3/5"),
        ("素材采用率", f"{adoption:.0%}", "目标 ≥60%"),
        ("平均操作时长", f"{minutes:.1f} 分钟", "目标 ≤5分钟"),
        ("新增贡献毛利", f"¥{profit:.0f}", "目标 ≥¥398"),
    ]
    for index, (label, value, target) in enumerate(metrics):
        x = 80 + index * 370
        rounded(draw, (x, 300, x + 335, 470), 10, WHITE, LINE, 2)
        draw.text((x + 24, 327), label, font=font(23), fill=MUTED)
        draw.text((x + 24, 370), value, font=font(42, True), fill=NAVY)
        draw.text((x + 24, 430), target, font=font(19), fill=TEAL)

    max_profit = max(row["incremental_profit"] for row in records)
    chart_left, chart_top, chart_bottom = 110, 555, 790
    chart_width = 900
    draw.line(
        (chart_left, chart_bottom, chart_left + chart_width, chart_bottom),
        fill="#9EACB1",
        width=2,
    )
    bar_w, gap = 120, 50
    for i, row in enumerate(records):
        x = chart_left + i * (bar_w + gap)
        bar_h = int(row["incremental_profit"] / max_profit * 190)
        color = TEAL if row["paid"] else "#A9B6BA"
        draw.rectangle((x, chart_bottom - bar_h, x + bar_w, chart_bottom), fill=color)
        draw.text(
            (x + 18, chart_bottom - bar_h - 34),
            f"¥{row['incremental_profit']:.0f}",
            font=font(19, True),
            fill=INK,
        )
        draw.text((x, chart_bottom + 18), row["store"], font=font(18), fill=INK)
    draw.text((110, 510), "各店 7 天新增贡献毛利", font=font(25, True), fill=NAVY)

    rounded(draw, (1110, 555, 1520, 840), 10, NAVY)
    draw.text((1150, 590), "阶段结论", font=font(25), fill="#D9E7E9")
    draw.text((1150, 640), "GO", font=font(70, True), fill=WHITE)
    draw_wrapped(
        draw,
        "进入下一轮验证，但继续追踪未付费门店：是价值不足，还是执行成本过高。",
        1150,
        720,
        font(19),
        "#E8EFF0",
        320,
        7,
        5,
    )
    image.save(ASSETS / "dashboard.png")


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    generate_workflow()
    generate_chat_demo()
    generate_campaign_poster()
    generate_validation_plan()
    generate_dashboard()
    for path in sorted(ASSETS.glob("*.png")):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
