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


def _uptime(sec) -> str:
    if sec is None:
        return "—"
    s = int(sec)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, _ = divmod(s, 60)
    parts = []
    if d:
        parts.append(f"{d}天")
    if h:
        parts.append(f"{h}小时")
    parts.append(f"{m}分钟")
    return " ".join(parts)


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


# ── Main ─────────────────────────────────────────────

def render_status_card(stats: dict) -> bytes:
    ft = _f(28)
    fs = _f(13)
    fh = _f(17)
    fl = _f(13)
    fv = _f(18)
    fbl = _f(13)
    fbv = _f(22)

    inner_w = W - 2 * PAD - 2 * INNER
    badge_gap = 12
    badge_w = (inner_w - 3 * badge_gap) // 4

    # Status breakdown
    status_breakdown: dict[str, int] = stats.get("status_breakdown", {})
    breakdown_rows = (len(status_breakdown) + 1) // 2
    breakdown_h = (breakdown_rows * ROW_H + 40 + INNER) if status_breakdown else 0

    # Section heights
    hdr = 78
    acc_h = 120 + INNER
    traffic_h = 2 * ROW_H + 40 + INNER
    token_h = ROW_H + 40 + INNER
    sys_h = ROW_H + 40 + INNER

    total_h = (
        PAD + hdr
        + SEC_GAP + acc_h
        + (SEC_GAP + breakdown_h if breakdown_h else 0)
        + SEC_GAP + traffic_h
        + SEC_GAP + token_h
        + SEC_GAP + sys_h
        + PAD + 4
    )

    img = Image.new("RGB", (W, total_h), BG)
    draw = ImageDraw.Draw(img)
    y = PAD

    # ── Header ──
    draw.text((PAD, y), "Codex2API 状态面板", font=ft, fill=BLACK)
    my = y + 40
    ua = stats.get("updated_at", "")
    if ua:
        draw.text((PAD, my), f"更新于  {ua}", font=fs, fill=LIGHT)
    ut = f"已运行  {_uptime(stats.get('uptime'))}"
    draw.text((W - PAD - _tw(fs, ut), my), ut, font=fs, fill=LIGHT)
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
        ("锁定", _fmt(stats.get("locked_accounts")), GRAY, GRAY_BG),
    ]:
        _badge(draw, bx, ny, badge_w, 62, lbl, val, fg, bg, fbl, fbv)
        bx += badge_w + badge_gap
    y += acc_h

    # ── Status Breakdown ──
    if breakdown_h:
        y += SEC_GAP
        cx, cy = _card(draw, y, breakdown_h)
        ny = _title(draw, cx, cy, "异常详情", fh)
        items = sorted(status_breakdown.items(), key=lambda x: -x[1])
        _kvgrid(draw, cx, ny, [(msg, str(cnt)) for msg, cnt in items], fl, fv)
        y += breakdown_h

    # ── Traffic ──
    y += SEC_GAP
    cx, cy = _card(draw, y, traffic_h)
    ny = _title(draw, cx, cy, "流量统计", fh)
    err_rate = stats.get("error_rate", 0)
    err_pct = f"{float(err_rate):.1f}%" if err_rate else "0%"
    _kvgrid(draw, cx, ny, [
        ("今日请求", _fmt(stats.get("today_requests"))),
        ("活跃请求", _fmt(stats.get("active_requests"))),
        ("QPS", f"{float(stats.get('qps', 0)):.1f}"),
        ("RPM", _fmt(stats.get("rpm"))),
    ], fl, fv)
    y += traffic_h

    # ── Tokens ──
    y += SEC_GAP
    cx, cy = _card(draw, y, token_h)
    ny = _title(draw, cx, cy, "Token 用量", fh)
    _kvgrid(draw, cx, ny, [
        ("今日 Token", _fmt(stats.get("today_tokens"))),
        ("TPM", _fmt(stats.get("tpm"))),
    ], fl, fv)
    y += token_h

    # ── System ──
    y += SEC_GAP
    cx, cy = _card(draw, y, sys_h)
    ny = _title(draw, cx, cy, "系统信息", fh)
    _kvgrid(draw, cx, ny, [
        ("错误率", err_pct),
        ("Goroutines", _fmt(stats.get("goroutines"))),
    ], fl, fv)

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
