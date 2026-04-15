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


def _cost(v) -> str:
    if v is None or float(v) == 0:
        return "—"
    v = float(v)
    return f"${v:,.2f}" if v >= 100 else f"${v:.4f}"


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


def _status_dot(draw: ImageDraw.ImageDraw, x: int, y: int, online: bool):
    color = GREEN if online else RED
    draw.ellipse((x, y, x + 10, y + 10), fill=color)


# ── Main ─────────────────────────────────────────────

def render_status_card(stats: dict) -> bytes:
    ft = _f(28)
    fs = _f(13)
    fh = _f(17)
    fl = _f(13)
    fv = _f(18)
    fbl = _f(13)
    fbv = _f(22)
    fm = _f(15)

    inner_w = W - 2 * PAD - 2 * INNER
    badge_gap = 12
    badge_w = (inner_w - 2 * badge_gap) // 3

    services = stats.get("services", [])
    svc_count = len(services)

    # Section heights
    hdr = 78
    overview_h = 120 + INNER
    usage_h = 2 * ROW_H + 40 + INNER
    has_7d = bool(stats.get("usage_7d_avg"))
    quota_h = (ROW_H + 40 + INNER) if has_7d else 0
    cost_h = (ROW_H + 40 + INNER) if (stats.get("total_cost", 0) or stats.get("today_cost", 0)) else 0
    svc_row_h = 36
    svc_h = svc_count * svc_row_h + 40 + INNER

    total_h = (
        PAD + hdr
        + SEC_GAP + overview_h
        + SEC_GAP + usage_h
        + (SEC_GAP + quota_h if has_7d else 0)
        + (SEC_GAP + cost_h if cost_h else 0)
        + SEC_GAP + svc_h
        + PAD + 4
    )

    img = Image.new("RGB", (W, total_h), BG)
    draw = ImageDraw.Draw(img)
    y = PAD

    # ── Header ──
    draw.text((PAD, y), "AI 服务总览", font=ft, fill=BLACK)
    my = y + 40
    ua = stats.get("updated_at", "")
    if ua:
        draw.text((PAD, my), f"更新于  {ua}", font=fs, fill=LIGHT)
    online_text = f"{stats.get('online_count', 0)}/{stats.get('total_count', 0)} 服务在线"
    draw.text((W - PAD - _tw(fs, online_text), my), online_text, font=fs, fill=LIGHT)
    y += hdr

    # ── Overview Badges ──
    y += SEC_GAP
    cx, cy = _card(draw, y, overview_h)
    ny = _title(draw, cx, cy, "账号总览", fh)
    bx = cx
    for lbl, val, fg, bg in [
        ("总账号", _fmt(stats.get("total_accounts")), BLUE, BLUE_BG),
        ("可用", _fmt(stats.get("available_accounts")), GREEN, GREEN_BG),
        ("不可用", _fmt(stats.get("unavailable_accounts")), RED, RED_BG),
    ]:
        _badge(draw, bx, ny, badge_w, 62, lbl, val, fg, bg, fbl, fbv)
        bx += badge_w + badge_gap
    y += overview_h

    # ── Usage ──
    y += SEC_GAP
    cx, cy = _card(draw, y, usage_h)
    ny = _title(draw, cx, cy, "用量统计", fh)
    _kvgrid(draw, cx, ny, [
        ("今日请求", _fmt(stats.get("today_requests"))),
        ("今日 Token", _fmt(stats.get("today_tokens"))),
        ("累计请求", _fmt(stats.get("total_requests"))),
        ("累计 Token", _fmt(stats.get("total_tokens"))),
    ], fl, fv)
    y += usage_h

    # ── 7d Usage ──
    if has_7d:
        y += SEC_GAP
        cx, cy = _card(draw, y, quota_h)
        ny = _title(draw, cx, cy, "7天额度", fh)
        avg_used = float(stats.get("usage_7d_avg") or 0)
        avg_remain = 100 - avg_used
        _kvgrid(draw, cx, ny, [
            ("已用", f"{avg_used:.1f}%"),
            ("剩余", f"{avg_remain:.1f}%"),
        ], fl, fv)
        y += quota_h

    # ── Cost (only if any cost data) ──
    if cost_h:
        y += SEC_GAP
        cx, cy = _card(draw, y, cost_h)
        ny = _title(draw, cx, cy, "费用", fh)
        _kvgrid(draw, cx, ny, [
            ("今日费用", _cost(stats.get("today_cost"))),
            ("累计费用", _cost(stats.get("total_cost"))),
        ], fl, fv)
        y += cost_h

    # ── Per-service breakdown ──
    y += SEC_GAP
    cx, cy = _card(draw, y, svc_h)
    ny = _title(draw, cx, cy, "各服务状态", fh)

    # Table header
    col_name = cx
    col_acct = cx + inner_w - 380
    col_avail = cx + inner_w - 280
    col_req = cx + inner_w - 170
    col_tok = cx + inner_w - 70

    draw.text((col_name, ny), "服务", font=fl, fill=MUTED)
    draw.text((col_acct, ny), "账号", font=fl, fill=MUTED)
    draw.text((col_avail, ny), "可用", font=fl, fill=MUTED)
    draw.text((col_req, ny), "今日请求", font=fl, fill=MUTED)
    draw.text((col_tok, ny), "今日Token", font=fl, fill=MUTED)
    ry = ny + 24

    for svc in services:
        online = svc.get("status") == "online"
        _status_dot(draw, col_name, ry + 4, online)
        draw.text((col_name + 16, ry), svc["name"], font=fm, fill=DARK if online else LIGHT)
        if online:
            draw.text((col_acct, ry), str(svc.get("total", 0)), font=fm, fill=DARK)
            draw.text((col_avail, ry), str(svc.get("available", 0)), font=fm, fill=GREEN)
            draw.text((col_req, ry), _fmt(svc.get("today_requests")), font=fm, fill=DARK)
            draw.text((col_tok, ry), _fmt(svc.get("today_tokens")), font=fm, fill=DARK)
        else:
            draw.text((col_acct, ry), "离线", font=fm, fill=RED)
        ry += svc_row_h

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
