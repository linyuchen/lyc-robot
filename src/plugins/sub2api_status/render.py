from datetime import datetime, timezone, timedelta
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CST = timezone(timedelta(hours=8))

FONT_PATH = Path(__file__).parent.parent.parent / "common/fonts/msyh.ttc"

# Layout
W = 720
PAD = 36
INNER = 24
SEC_GAP = 20
ROW_H = 54

# ── Light palette ────────────────────────────────────
BG = (241, 245, 249)  # slate-100
CARD = (255, 255, 255)
CARD_SHADOW = (203, 213, 225)  # slate-300
CARD_BORDER = (226, 232, 240)  # slate-200

BLACK = (15, 23, 42)  # slate-900
DARK = (30, 41, 59)  # slate-800
BODY = (51, 65, 85)  # slate-700
MUTED = (100, 116, 139)  # slate-500
LIGHT = (148, 163, 184)  # slate-400

ACCENT = (37, 99, 235)  # blue-600
ACCENT_LIGHT = (219, 234, 254)  # blue-100

GREEN = (22, 163, 74)  # green-600
GREEN_BG = (220, 252, 231)  # green-100
RED = (220, 38, 38)  # red-600
RED_BG = (254, 226, 226)  # red-100
ORANGE = (217, 119, 6)  # amber-600
ORANGE_BG = (254, 243, 199)  # amber-100
PURPLE = (147, 51, 234)  # purple-600
PURPLE_BG = (243, 232, 255)  # purple-100
BLUE = (37, 99, 235)  # blue-600
BLUE_BG = (219, 234, 254)  # blue-100


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
    if v is None:
        return "—"
    v = float(v)
    return f"${v:,.2f}" if v >= 100 else f"${v:.4f}"


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
    # subtle shadow
    draw.rounded_rectangle((x0 + 2, y + 2, x1 + 2, y + h + 2), radius=16, fill=CARD_SHADOW)
    draw.rounded_rectangle((x0, y, x1, y + h), radius=16, fill=CARD, outline=CARD_BORDER)
    return x0 + INNER, y + INNER


def _title(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font):
    # colored bar
    draw.rounded_rectangle((x, y + 2, x + 4, y + 20), radius=2, fill=ACCENT)
    draw.text((x + 14, y - 1), text, font=font, fill=BLACK)
    return y + 32


def _badge(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
           label: str, value: str, fg: tuple, bg: tuple, fl, fv):
    draw.rounded_rectangle((x, y, x + w, y + h), radius=12, fill=bg)
    # label centered
    lw = _tw(fl, label)
    draw.text((x + (w - lw) // 2, y + 10), label, font=fl, fill=fg)
    # value centered
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
    ft = _f(28)   # title
    fs = _f(13)   # small / meta
    fh = _f(17)   # section heading
    fl = _f(13)   # kv label
    fv = _f(18)   # kv value
    fbl = _f(13)  # badge label
    fbv = _f(22)  # badge value

    inner_w = W - 2 * PAD - 2 * INNER
    badge_gap = 12
    badge_w = (inner_w - 4 * badge_gap) // 5

    # heights (INNER added as bottom padding for each card)
    hdr = 78
    acc_h = 120 + INNER
    req_h = 2 * ROW_H + 40 + INNER
    tok_h = 2 * (ROW_H + 30) + 44 + INNER
    cst_h = 2 * ROW_H + 40 + INNER
    usr_h = 2 * ROW_H + 40 + INNER
    sys_h = ROW_H + 40 + INNER

    total = (
        PAD + hdr
        + SEC_GAP + acc_h
        + SEC_GAP + req_h
        + SEC_GAP + tok_h
        + SEC_GAP + cst_h
        + SEC_GAP + usr_h
        + SEC_GAP + sys_h
        + PAD + 4  # shadow
    )

    img = Image.new("RGB", (W, total), BG)
    draw = ImageDraw.Draw(img)
    y = PAD

    # ── Header ──
    draw.text((PAD, y), "Sub2API 状态面板", font=ft, fill=BLACK)
    my = y + 40
    ua = stats.get("stats_updated_at", "")
    if ua:
        try:
            dt = datetime.fromisoformat(str(ua).replace("Z", "+00:00"))
            ts = dt.astimezone(CST).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            ts = str(ua)[:19].replace("T", " ")
        draw.text((PAD, my), f"更新于  {ts}", font=fs, fill=LIGHT)
    ut = f"已运行  {_uptime(stats.get('uptime'))}"
    draw.text((W - PAD - _tw(fs, ut), my), ut, font=fs, fill=LIGHT)
    y += hdr

    # ── Accounts ──
    y += SEC_GAP
    cx, cy = _card(draw, y, acc_h)
    ny = _title(draw, cx, cy, "账号状态", fh)
    # available = normal - ratelimit - overload (temporarily unschedulable excluded)
    normal = int(stats.get("normal_accounts") or 0)
    ratelimit = int(stats.get("ratelimit_accounts") or 0)
    overload = int(stats.get("overload_accounts") or 0)
    available = normal - ratelimit - overload

    bx = cx
    for lbl, val, fg, bg in [
        ("总数", _fmt(stats.get("total_accounts")), BLUE, BLUE_BG),
        ("可用", _fmt(available), GREEN, GREEN_BG),
        ("异常", _fmt(stats.get("error_accounts")), RED, RED_BG),
        ("限流", _fmt(ratelimit), ORANGE, ORANGE_BG),
        ("过载", _fmt(overload), PURPLE, PURPLE_BG),
    ]:
        _badge(draw, bx, ny, badge_w, 62, lbl, val, fg, bg, fbl, fbv)
        bx += badge_w + badge_gap
    y += acc_h

    # ── Requests ──
    y += SEC_GAP
    cx, cy = _card(draw, y, req_h)
    ny = _title(draw, cx, cy, "请求统计", fh)
    _kvgrid(draw, cx, ny, [
        ("总请求数", _fmt(stats.get("total_requests"))),
        ("今日请求", _fmt(stats.get("today_requests"))),
        ("每分钟请求 (RPM)", _fmt(stats.get("rpm"))),
        ("每分钟 Token (TPM)", _fmt(stats.get("tpm"))),
    ], fl, fv)
    y += req_h

    # ── Token ──
    y += SEC_GAP
    cx, cy = _card(draw, y, tok_h)
    ny = _title(draw, cx, cy, "Token 用量", fh)
    # cumulative
    draw.text((cx, ny), "累计", font=fl, fill=ACCENT)
    ry = ny + 22
    ry = _kvgrid(draw, cx, ry, [
        ("输入 Token", _fmt(stats.get("total_input_tokens"))),
        ("输出 Token", _fmt(stats.get("total_output_tokens"))),
        ("合计", _fmt(stats.get("total_tokens"))),
    ], fl, fv, cols=3)
    _sep(draw, cx, ry - 6, inner_w)
    # today
    draw.text((cx, ry + 2), "今日", font=fl, fill=ACCENT)
    ry += 24
    _kvgrid(draw, cx, ry, [
        ("输入 Token", _fmt(stats.get("today_input_tokens"))),
        ("输出 Token", _fmt(stats.get("today_output_tokens"))),
        ("合计", _fmt(stats.get("today_tokens"))),
    ], fl, fv, cols=3)
    y += tok_h

    # ── Cost ──
    y += SEC_GAP
    cx, cy = _card(draw, y, cst_h)
    ny = _title(draw, cx, cy, "费用统计", fh)
    _kvgrid(draw, cx, ny, [
        ("总费用", _cost(stats.get("total_cost"))),
        ("实际费用", _cost(stats.get("total_actual_cost"))),
        ("今日费用", _cost(stats.get("today_cost"))),
        ("今日实际", _cost(stats.get("today_actual_cost"))),
    ], fl, fv)
    y += cst_h

    # ── Users ──
    y += SEC_GAP
    cx, cy = _card(draw, y, usr_h)
    ny = _title(draw, cx, cy, "用户与密钥", fh)
    _kvgrid(draw, cx, ny, [
        ("总用户", _fmt(stats.get("total_users"))),
        ("活跃用户", _fmt(stats.get("active_users"))),
        ("今日新增", _fmt(stats.get("today_new_users"))),
        ("活跃 / 总密钥", f"{_fmt(stats.get('active_api_keys'))} / {_fmt(stats.get('total_api_keys'))}"),
    ], fl, fv)
    y += usr_h

    # ── System ──
    y += SEC_GAP
    cx, cy = _card(draw, y, sys_h)
    ny = _title(draw, cx, cy, "系统信息", fh)
    avg = stats.get("average_duration_ms")
    _kvgrid(draw, cx, ny, [
        ("平均延迟", f"{float(avg):,.0f} ms" if avg is not None else "—"),
        ("每小时活跃", _fmt(stats.get("hourly_active_users"))),
    ], fl, fv)

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
