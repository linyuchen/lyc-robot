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

# ── Light palette ────────────────────────────────────
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
RED = (220, 38, 38)
RED_BG = (254, 226, 226)
ORANGE = (217, 119, 6)
ORANGE_BG = (254, 243, 199)
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


# ── Drawing helpers ──────────────────────────────────

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


def _sep(draw: ImageDraw.ImageDraw, x: int, y: int, w: int):
    draw.line([(x, y), (x + w, y)], fill=CARD_BORDER, width=1)


# ── Main ─────────────────────────────────────────────

def render_status_card(stats: dict) -> bytes:
    ft = _f(28)
    fs = _f(13)
    fh = _f(17)
    fl = _f(13)
    fv = _f(18)
    fbl = _f(13)
    fbv = _f(22)
    fm = _f(14)  # model list font

    inner_w = W - 2 * PAD - 2 * INNER
    badge_gap = 12
    badge_w = (inner_w - 4 * badge_gap) // 5  # 5 badges

    # Top models
    top_models: list[tuple[str, dict]] = stats.get("top_models", [])
    model_rows = min(len(top_models), 8)

    # Section heights
    hdr = 78
    acc_h = 120 + INNER
    req_h = 2 * ROW_H + 40 + INNER
    tok_h = ROW_H + 40 + INNER
    model_h = (model_rows * 32 + 50 + INNER) if model_rows else 0
    provider_counts = stats.get("provider_counts", {})
    prov_rows = (len(provider_counts) + 2) // 3  # 3 cols
    prov_h = (prov_rows * ROW_H + 40 + INNER) if provider_counts else 0

    total = (
        PAD + hdr
        + SEC_GAP + acc_h
        + SEC_GAP + req_h
        + SEC_GAP + tok_h
        + (SEC_GAP + model_h if model_h else 0)
        + (SEC_GAP + prov_h if prov_h else 0)
        + PAD + 4
    )

    img = Image.new("RGB", (W, total), BG)
    draw = ImageDraw.Draw(img)
    y = PAD

    # ── Header ──
    draw.text((PAD, y), "CPA 状态面板", font=ft, fill=BLACK)
    ua = stats.get("updated_at", "")
    if ua:
        draw.text((PAD, y + 40), f"更新于  {ua}", font=fs, fill=LIGHT)
    y += hdr

    # ── Accounts ──
    y += SEC_GAP
    cx, cy = _card(draw, y, acc_h)
    ny = _title(draw, cx, cy, "账号状态", fh)
    bx = cx
    for lbl, val, fg, bg in [
        ("总数", _fmt(stats.get("total_accounts")), BLUE, BLUE_BG),
        ("可用", _fmt(stats.get("active_accounts")), GREEN, GREEN_BG),
        ("异常", _fmt(stats.get("error_accounts")), RED, RED_BG),
        ("暂时", _fmt(stats.get("transient_accounts")), ORANGE, ORANGE_BG),
        ("禁用", _fmt(stats.get("disabled_accounts")), GRAY, GRAY_BG),
    ]:
        _badge(draw, bx, ny, badge_w, 62, lbl, val, fg, bg, fbl, fbv)
        bx += badge_w + badge_gap
    y += acc_h

    # ── Requests ──
    y += SEC_GAP
    cx, cy = _card(draw, y, req_h)
    ny = _title(draw, cx, cy, "请求统计", fh)
    _kvgrid(draw, cx, ny, [
        ("总请求", _fmt(stats.get("total_requests"))),
        ("今日请求", _fmt(stats.get("today_requests"))),
        ("成功", _fmt(stats.get("success_count"))),
        ("失败", _fmt(stats.get("failure_count"))),
    ], fl, fv)
    y += req_h

    # ── Token ──
    y += SEC_GAP
    cx, cy = _card(draw, y, tok_h)
    ny = _title(draw, cx, cy, "Token 用量", fh)
    _kvgrid(draw, cx, ny, [
        ("总 Token", _fmt(stats.get("total_tokens"))),
        ("今日 Token", _fmt(stats.get("today_tokens"))),
    ], fl, fv)
    y += tok_h

    # ── Top Models ──
    if model_h:
        y += SEC_GAP
        cx, cy = _card(draw, y, model_h)
        ny = _title(draw, cx, cy, "模型用量 TOP", fh)
        # table header
        draw.text((cx, ny), "模型", font=fl, fill=MUTED)
        draw.text((cx + inner_w - 220, ny), "请求数", font=fl, fill=MUTED)
        draw.text((cx + inner_w - 100, ny), "Token", font=fl, fill=MUTED)
        ry = ny + 24
        for model_name, model_data in top_models:
            # truncate long model names
            display_name = model_name if len(model_name) <= 32 else model_name[:30] + "..."
            draw.text((cx, ry), display_name, font=fm, fill=DARK)
            req_text = _fmt(model_data["requests"])
            tok_text = _fmt(model_data["tokens"])
            draw.text((cx + inner_w - 220, ry), req_text, font=fm, fill=DARK)
            draw.text((cx + inner_w - 100, ry), tok_text, font=fm, fill=DARK)
            ry += 32
        y += model_h

    # ── Providers ──
    if prov_h:
        y += SEC_GAP
        cx, cy = _card(draw, y, prov_h)
        ny = _title(draw, cx, cy, "账号类型分布", fh)
        items = [(k, str(v)) for k, v in sorted(provider_counts.items(), key=lambda x: -x[1])]
        _kvgrid(draw, cx, ny, items, fl, fv, cols=3)
        y += prov_h

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
