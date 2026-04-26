from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = Path(__file__).parent.parent.parent / "common/fonts/msyh.ttc"

# Layout
W = 720
PAD = 36
INNER = 24
SEC_GAP = 20
ROW_H = 54

BG = (241, 245, 249)
CARD = (255, 255, 255)
CARD_SHADOW = (203, 213, 225)
CARD_BORDER = (226, 232, 240)

BLACK = (15, 23, 42)
DARK = (30, 41, 59)
MUTED = (100, 116, 139)
LIGHT = (148, 163, 184)

ACCENT = (37, 99, 235)
GREEN = (22, 163, 74)
GREEN_BG = (220, 252, 231)
GRAY = (100, 116, 139)
GRAY_BG = (241, 245, 249)
BLUE = (37, 99, 235)
BLUE_BG = (219, 234, 254)


def _f(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def _tw(font, text: str) -> int:
    bb = font.getbbox(text)
    return bb[2] - bb[0]


def _fmt(n) -> str:
    if n is None:
        return "—"
    n = float(n)
    if n >= 1_000_000_000:
        return f"{n / 1e9:.2f}B"
    if n >= 1_000_000:
        return f"{n / 1e6:.2f}M"
    if n >= 10_000:
        return f"{n / 1e3:.1f}K"
    if n >= 1_000:
        return f"{n / 1e3:.2f}K"
    return f"{int(n)}"


def _card(draw: ImageDraw.ImageDraw, y: int, h: int) -> tuple[int, int]:
    x0, x1 = PAD, W - PAD
    draw.rounded_rectangle((x0 + 2, y + 2, x1 + 2, y + h + 2), radius=16, fill=CARD_SHADOW)
    draw.rounded_rectangle((x0, y, x1, y + h), radius=16, fill=CARD, outline=CARD_BORDER)
    return x0 + INNER, y + INNER


def _title(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font):
    draw.rounded_rectangle((x, y + 2, x + 4, y + 20), radius=2, fill=ACCENT)
    draw.text((x + 14, y - 1), text, font=font, fill=BLACK)
    return y + 32


def _badge(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
           label: str, value: str, fg: tuple, bg: tuple, fl, fv):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=bg)
    lw = _tw(fl, label)
    draw.text((x + (w - lw) // 2, y + 10), label, font=fl, fill=fg)
    vw = _tw(fv, value)
    draw.text((x + (w - vw) // 2, y + 34), value, font=fv, fill=fg)


def _kvgrid(draw: ImageDraw.ImageDraw, x: int, y: int,
            items: list[tuple[str, str]], fl, fv,
            cols: int = 2) -> int:
    cw = (W - 2 * PAD - 2 * INNER) // cols
    cx = x
    for i, (label, value) in enumerate(items):
        draw.text((cx, y), label, font=fl, fill=MUTED)
        draw.text((cx, y + 22), value, font=fv, fill=DARK)
        cx += cw
        if (i + 1) % cols == 0:
            cx = x
            y += ROW_H
    if len(items) % cols != 0:
        y += ROW_H
    return y


# ── Main ─────────────────────────────────────────────

def render_status_card(stats: dict) -> bytes:
    ft = _f(28)
    fs = _f(13)
    fh = _f(17)
    fl = _f(13)
    fv = _f(18)
    fbl = _f(13)
    fbv = _f(22)
    fm = _f(13)

    inner_w = W - 2 * PAD - 2 * INNER
    badge_gap = 12
    badge_w = (inner_w - 2 * badge_gap) // 3

    # Models
    models: list[str] = stats.get("models", [])
    model_line_h = 26
    # Wrap models into lines (multiple per line, separated by comma)
    model_lines = []
    if models:
        models_sorted = sorted(models, key=lambda m: m.lower())
        current_prefix = ""
        line = ""
        for m in models_sorted:
            prefix = m.split("-")[0].lower() if m else ""
            if prefix != current_prefix:
                if line:
                    model_lines.append(line)
                    model_lines.append("")
                    line = ""
                current_prefix = prefix
            test = f"{line}, {m}" if line else m
            if _tw(fm, test) > inner_w and line:
                model_lines.append(line)
                line = m
            else:
                line = test
        if line:
            model_lines.append(line)
    model_h = (len(model_lines) * model_line_h + 40 + INNER) if model_lines else 0

    # Section heights
    hdr = 78
    stat_h = 2 * ROW_H + 40 + INNER

    total_h = (
        PAD + hdr
        + SEC_GAP + stat_h
        + (SEC_GAP + model_h if model_h else 0)
        + PAD + 4
    )

    img = Image.new("RGB", (W, total_h), BG)
    draw = ImageDraw.Draw(img)
    y = PAD

    # ── Header ──
    draw.text((PAD, y), "NewAPI 状态面板", font=ft, fill=BLACK)
    ua = stats.get("updated_at", "")
    if ua:
        draw.text((PAD, y + 40), f"更新于  {ua}", font=fs, fill=LIGHT)
    y += hdr

    # ── Stats ──
    y += SEC_GAP
    cx, cy = _card(draw, y, stat_h)
    ny = _title(draw, cx, cy, "Token用量统计", fh)
    _kvgrid(draw, cx, ny, [
        ("今日消耗", _fmt(stats.get("today_quota"))),
        ("累计消耗", _fmt(stats.get("total_quota"))),
        ("RPM", _fmt(stats.get("today_rpm"))),
        ("TPM", _fmt(stats.get("today_tpm"))),
    ], fl, fv)
    y += stat_h

    # ── Models ──
    if model_h:
        y += SEC_GAP
        cx, cy = _card(draw, y, model_h)
        ny = _title(draw, cx, cy, f"可用模型 ({len(models)})", fh)
        ry = ny
        for line in model_lines:
            draw.text((cx, ry), line, font=fm, fill=DARK)
            ry += model_line_h

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
