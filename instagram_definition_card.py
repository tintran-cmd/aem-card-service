"""
Instagram Card Generator — AEM Algorithm
Matches the official AEM Algorithm template exactly:
  - Pure white top strip (~17%) with pixel-art robot straddling the boundary
  - Very dark navy main area
  - AEM Algorithm logo (hex network icon + aem + ALGORITHM) centred at bottom
"""

import argparse
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 1080, 1080

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY        = (10,  22,  48)    # #0A1630 — deep navy background
WHITE       = (255, 255, 255)
BLUE        = (24,  144, 255)   # #1890FF — AEM brand blue
TEAL        = (52,  207, 201)   # #34CFC9 — robot teal/cyan
SCREEN_COL  = (195, 238, 236)   # light teal for robot screen face
BODY_DARK   = (18,  30,  55)    # dark robot body
EYE_COL     = (18,  30,  55)    # dark pixel eyes
TEXT_WHITE  = (255, 255, 255)
TEXT_MUTED  = (140, 162, 196)   # muted grey-blue for explanation text

# ── Layout ────────────────────────────────────────────────────────────────────
WHITE_H = 185    # pixels — height of the white top strip
P       = 16     # pixel-art unit (1 robot pixel = 16 canvas pixels)

# ── Font paths (fallback chain) ───────────────────────────────────────────────
BOLD_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
REGULAR_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


# ── Utilities ─────────────────────────────────────────────────────────────────

def load_font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_w, draw):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = f"{cur} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def block_height(lines, font, draw, ls=1.4):
    total = 0
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        total += int((bb[3] - bb[1]) * ls)
    return total


def draw_block(draw, lines, font, color, y0, ls=1.4):
    y = y0
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        lw, lh = bb[2] - bb[0], bb[3] - bb[1]
        draw.text(((W - lw) // 2, y), line, fill=color, font=font)
        y += int(lh * ls)
    return y


def rect(draw, x0, y0, x1, y1, fill, outline=None, width=0):
    if outline:
        draw.rectangle([(x0, y0), (x1, y1)], fill=fill, outline=outline, width=width)
    else:
        draw.rectangle([(x0, y0), (x1, y1)], fill=fill)


# ── Pixel-art robot ───────────────────────────────────────────────────────────

def draw_robot(draw):
    """
    Pixel-art AEM robot — refined to match template exactly.
    Head lives in the white strip; base straddles the white/dark boundary.
    """
    cx = W // 2   # 540
    head_top = WHITE_H - 5 * P   # 105
    ant_top  = head_top - 5 * P  # 25 — antennas higher up

    # ── Antennas — tall & prominent ─────────────────────────────────────────
    ant_shaft_w = P * 1.5   # 24 px — thicker shaft
    cap_w       = P * 1.8   # 29 px — wider cap
    cap_h       = P * 1.2   # 19 px — taller cap

    for side in (-1, 1):
        if side == -1:
            shaft_x0 = cx - int(3.5 * P)
        else:
            shaft_x0 = cx + int(2.5 * P)
        shaft_x1 = shaft_x0 + int(ant_shaft_w)

        # Shaft
        rect(draw, shaft_x0, int(ant_top + cap_h), shaft_x1, head_top, TEAL)
        # Cap — wider square on top
        cap_x0 = int(shaft_x0 - (cap_w - ant_shaft_w) / 2)
        rect(draw, cap_x0, int(ant_top), int(cap_x0 + cap_w), int(ant_top + cap_h), TEAL)

    # ── Head — clean & simple ──────────────────────────────────────────────
    hw  = int(9 * P)      # 144 px wide
    hx  = cx - hw // 2    # 468

    # Outer frame
    rect(draw, hx, head_top, hx + hw, WHITE_H, BODY_DARK, outline=TEAL, width=3)

    # Inner screen (light teal)
    sp = int(P * 1.5)     # ~24 px padding
    rect(draw, hx + sp, head_top + sp, hx + hw - sp, WHITE_H - sp, SCREEN_COL)

    # Eyes — 2 simple dark squares
    eye_sz = int(P * 1.3)  # ~21 px
    eye_y  = head_top + int(P * 2)
    eye_gap = int(P * 0.5)
    # left eye
    rect(draw, cx - eye_sz - eye_gap - int(P * 0.5), eye_y, 
         cx - eye_gap, eye_y + eye_sz, EYE_COL)
    # right eye  
    rect(draw, cx + eye_gap, eye_y, 
         cx + eye_gap + eye_sz + int(P * 0.5), eye_y + eye_sz, EYE_COL)

    # Mouth — simple short bar
    m_y = WHITE_H - sp - int(P * 2)
    rect(draw, cx - int(P * 1.2), m_y, cx + int(P * 1.2), m_y + int(P // 2), EYE_COL)

    # ── Base / body pedestal ────────────────────────────────────────────────
    bw = int(11 * P)   # 176 px
    bh = int(3.5 * P)  # 56 px
    bx = cx - bw // 2
    by = WHITE_H + P

    rect(draw, bx, by, bx + bw, by + bh, BODY_DARK, outline=TEAL, width=3)

    # Control panel — small teal rectangle centered
    pw = int(3 * P)
    ph = int(P * 1.2)
    px0 = cx - pw // 2
    py0 = by + int(P * 0.8)
    rect(draw, px0, py0, px0 + pw, py0 + ph, TEAL)


# ── AEM logo ──────────────────────────────────────────────────────────────────

# Logo is drawn programmatically (not from file)


def _draw_network_icon_hires(scale=4):
    """
    Render the AEM network icon at `scale`x resolution then return a
    PIL Image downsampled with LANCZOS for smooth anti-aliasing.
    """
    sz    = 60 * scale
    img   = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
    d     = ImageDraw.Draw(img)

    cx, cy   = sz // 2, sz // 2
    outer_r  = int(22 * scale)
    r_node   = int(6  * scale)
    lw       = max(1, int(2 * scale))

    # AEM logo icon has 4 outer nodes + 1 centre, arranged like a diamond
    # with one extra node — approximated from the brand image
    angles   = [330, 30, 150, 210, 90, 270]   # 6-node hex, same as brand
    ring     = [
        (int(cx + outer_r * math.cos(math.radians(a))),
         int(cy + outer_r * math.sin(math.radians(a))))
        for a in angles
    ]

    # Spokes centre → each ring node
    for nx, ny in ring:
        d.line([(cx, cy), (nx, ny)], fill=BLUE + (255,), width=lw)

    # Ring connections (alternate pairs to form the brand "X" cross-links)
    pairs = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (0, 3), (1, 4)]
    for i, j in pairs:
        d.line([ring[i], ring[j]], fill=BLUE + (255,), width=lw)

    # Node circles
    for nx, ny in ring:
        d.ellipse([(nx - r_node, ny - r_node),
                   (nx + r_node, ny + r_node)], fill=BLUE + (255,))
    d.ellipse([(cx - r_node, cy - r_node),
               (cx + r_node, cy + r_node)], fill=BLUE + (255,))

    # Downsample → smooth edges
    return img.resize((sz // scale, sz // scale), Image.Resampling.LANCZOS)


def draw_aem_logo(img, draw, font_aem, font_algo):
    """
    Paste the AEM Algorithm logo at bottom centre.
    Draws network icon + text (fallback — most reliable for matching template).
    """
    logo_y  = H - 115

    # ── Drawn logo (supersampled for smoothness) ──────────────────────────────
    aem_bb  = draw.textbbox((0, 0), "aem",       font=font_aem)
    algo_bb = draw.textbbox((0, 0), "ALGORITHM", font=font_algo)
    aem_w   = aem_bb[2] - aem_bb[0]
    aem_h   = aem_bb[3] - aem_bb[1]
    algo_w  = algo_bb[2] - algo_bb[0]

    icon_img = _draw_network_icon_hires(scale=4)
    icon_w, icon_h = icon_img.size   # 60×60

    text_gap = 12
    total_w  = icon_w + text_gap + max(aem_w, algo_w)
    left_x   = (W - total_w) // 2

    # Paste icon (RGBA onto RGB)
    iy = logo_y + (icon_h - aem_h) // 2
    img.paste(icon_img, (left_x, iy), icon_img)

    # Text
    tx = left_x + icon_w + text_gap
    ty = logo_y - aem_bb[1]
    draw.text((tx, ty), "aem", fill=BLUE, font=font_aem)
    draw.text(
        (tx + (aem_w - algo_w) // 2, ty + aem_h + 2),
        "ALGORITHM", fill=TEXT_MUTED, font=font_algo,
    )


# ── Main card generator ───────────────────────────────────────────────────────

def _split_unstructured_lines(text: str) -> list:
    """
    Last-resort splitter for LLM output that ignored bullet formatting.

    If the LLM dumped 5 topics into a single paragraph with only URLs as
    separators, reconstruct lines by splitting on URL anchors (`↳` or
    pure-URL substrings), then trim leading filler words.

    Heuristic:
      - Split on `↳ [Link](url)` markers (LLM usually keeps the link markers)
      - Then split top-level sentences by `.` only when sentence is long
        and contains numeric/dollar hint typical of crypto headlines
      - Drop hashtags / footer artifacts
    """
    import re
    if not text:
        return []

    # Step 1: remove the trailing hashtags line so we don't treat them as a "topic"
    # (card_text should not have hashtags anyway, but defensive)
    cleaned = text.strip()

    # Step 2: split on `↳` link markers if present — keep what's before each link
    if "↳" in cleaned:
        parts = []
        buf = []
        for chunk in cleaned.split("↳"):
            chunk = chunk.strip()
            if not chunk:
                continue
            # The chunk BEFORE a URL is the topic summary text — keep it
            # The chunk AFTER is the next topic's leading text (or trailing hashtags)
            if chunk.startswith("http"):
                # We hit a URL directly; previous buffer already captured its topic
                continue
            # Drop the "Link](url)" markers that wrap URLs
            chunk = re.sub(r"\[Link\]\([^)]+\)", "", chunk).strip()
            if chunk:
                buf.append(chunk)
        return [p for p in buf if len(p) > 5]

    # Step 3: no link markers — split on runs of whitespace between capitalised
    # topic starters when they look glued together
    # Pattern: "...$115M 40x BTC short just..." (no separator)
    # Try splitting before $XXX / +XX% / Topic-style prefixes
    glued_splits = re.split(
        r"(?=(?:\$[\d,]+|\+?\d+%|DTCC|Kraken|Venice|US Treasury|Bitcoin|Ethereum|BTC|ETH|SOL|XRP))",
        cleaned,
        flags=re.IGNORECASE,
    )
    glued_splits = [s.strip(" ,.;:\n") for s in glued_splits if s.strip()]
    if len(glued_splits) >= 3:
        return [s for s in glued_splits if len(s) > 10]

    return [cleaned]


def _clean_bullet_text(raw: str, max_bullets: int = 4, max_chars_per_bullet: int = 52):
    """
    Normalise LLM output into a clean bullet list for the card image.

    - Auto-splits glued unstructured text (e.g. when LLM ignored bullet rules)
    - Strips markdown bullets (`* `, `- `, `• `) at line start
    - Strips `[SourceName]` / `[X]` / `[CoinDesk]` prefixes (saves chars, cleaner card)
    - Removes sub-bullet lines that start with `↳` (link markers)
    - Drops trailing hashtag lines
    - Caps to `max_bullets` items
    - Truncates each bullet to `max_chars_per_bullet` so it fits one line
    """
    import re
    if not raw:
        return []
    out = []

    # First pass: split into lines
    lines = raw.splitlines()

    # If only 1 line and looks like LLM dumped everything together,
    # attempt glued-text recovery
    if len(lines) == 1:
        lines = _split_unstructured_lines(lines[0])

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Drop link/sub-bullet lines (LLM ignore "NO links" rule sometimes)
        if stripped.startswith("↳") or stripped.startswith("→"):
            continue
        # Drop trailing-hashtag standalone line (defensive — card_text should never have these)
        if stripped.startswith("#"):
            continue
        # Strip the URL wrapping defensively
        stripped = re.sub(r"\[Link\]\([^)]+\)", "", stripped).strip()
        # Strip leading markdown bullet markers
        for marker in ("* ", "- ", "• "):
            if stripped.startswith(marker):
                stripped = stripped[len(marker):]
                break
        # Strip [Source] prefix — saves 3-10 chars per bullet & cleaner card
        # Match patterns: "[X] ", "[CoinDesk] ", "[CoinGecko] ", "[Cointelegraph] " etc.
        stripped = re.sub(r'^\[[^\]]{1,20}\]\s*', '', stripped).strip()
        if not stripped:
            continue
        # Do NOT hard-truncate — let wrap_text handle overflow per line.
        # Truncating here causes ugly "DTCC to tokenize Russell 1000 stocks (NVDA, AAPL, MSFT) in Oc…"
        # on the card. With wrap_text(f_bullet, max_w) we get a clean 2-line wrap instead.
        out.append(stripped)
        if len(out) >= max_bullets:
            break
    return out


def generate_card(term, explanation, output_path):
    """
    Generate Instagram card by overlaying text on template image.
    Template contains: robot, logo, white strip, navy background.
    This function adds: term (bold blue), explanation (white), day badge (blue).

    Args:
        term: Crypto term or topic (will be uppercased)
        explanation: Definition text OR bullet-point format
                     (e.g., "* BTC: $65K surge\n* ETH: Gas drops")
        output_path: Where to save the PNG
    """
    # Load template base image
    template_path = os.path.join(os.path.dirname(__file__), "template_base.png")
    if not os.path.exists(template_path):
        # Fallback: generate from scratch (old method)
        print(f"⚠ Template not found at {template_path}, falling back to code generation")
        img = Image.new("RGB", (W, H), NAVY)
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (W, WHITE_H)], fill=WHITE)
        draw_robot(draw)
    else:
        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)

    # Fonts
    f_term = load_font(BOLD_FONTS,    58)
    f_body = load_font(REGULAR_FONTS, 32)
    f_bullet = load_font(REGULAR_FONTS, 28)
    f_aem  = load_font(BOLD_FONTS,    40)
    f_algo = load_font(REGULAR_FONTS, 20)

    # Content zone: from just below robot base to just above logo
    content_top    = WHITE_H + 4 * P + 30   # ~281 px
    content_bottom = H - 120                # ~960 px
    max_w = W - 200

    term_lines = wrap_text(term.upper(), f_term, max_w, draw)
    th = block_height(term_lines, f_term, draw, 1.3)

    # Detect bullet format: `*`, `-`, or `•` markers (LLM uses `*` not `•`)
    is_bullet_format = bool(explanation) and any(
        explanation.lstrip().startswith(m) or f"\n{m}" in explanation
        for m in ("* ", "- ", "• ")
    )

    if is_bullet_format:
        # Clean + cap to 4 bullets
        bullets = _clean_bullet_text(explanation, max_bullets=4, max_chars_per_bullet=62)
        if len(bullets) < 2:
            # Not enough bullets after cleaning — fall back to paragraph
            is_bullet_format = False

    if is_bullet_format:
        # ── Bullet render path ──────────────────────────────────────────────
        # Wrap each bullet (still capped by _clean_bullet_text above)
        wrapped_lines = []
        for line in bullets:
            wrapped_lines.extend(wrap_text(line, f_bullet, max_w, draw))
        # Insert a blank line between bullets for breathing room
        spaced = []
        for i, ln in enumerate(wrapped_lines):
            spaced.append(ln)
            # If next line exists and current line starts with a bullet marker OR
            # we are at a bullet boundary, add a gap row
            if i + 1 < len(wrapped_lines):
                # Detect transition to a new bullet by `*` at start of next line
                if any(wrapped_lines[i + 1].lstrip().startswith(m) for m in ("*", "-", "•")):
                    spaced.append("")  # blank gap row
        expl_lines = spaced
        # Tighter line spacing since we already added gap rows
        eh = block_height(expl_lines, f_bullet, draw, 1.25)
    else:
        # ── Regular paragraph render path ────────────────────────────────────
        expl_lines = wrap_text(explanation, f_body, max_w, draw)
        eh = block_height(expl_lines, f_body, draw, 1.5)

    total = th + 55 + eh

    start_y = content_top + (content_bottom - content_top - total) // 2

    # Term (bold, BLUE, uppercase)
    end_y = draw_block(draw, term_lines, f_term, BLUE, start_y, 1.3)

    # Thin separator line
    sep_y = end_y + 22
    sep_w = min(360, max_w)
    draw.line([((W - sep_w) // 2, sep_y), ((W + sep_w) // 2, sep_y)],
              fill=BLUE, width=2)

    # Explanation (white)
    line_spacing = 1.25 if is_bullet_format else 1.4
    draw_block(draw, expl_lines, f_bullet if is_bullet_format else f_body,
               TEXT_WHITE, sep_y + 32, line_spacing)

    img.save(output_path, "PNG")
    return output_path


def generate_from_json(json_path, output_dir):
    """Batch generate cards from a posts.json file."""
    with open(json_path, "r", encoding="utf-8") as f:
        posts = json.load(f)
    os.makedirs(output_dir, exist_ok=True)

    day_files = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    for i, post in enumerate(posts):
        day_file = day_files[i] if i < 7 else f"day_{i+1}"
        output_path = os.path.join(output_dir, f"{day_file}.png")
        generate_card(
            term=post["term"],
            explanation=post["card_text"],
            output_path=output_path,
        )
        print(f"  Generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AEM crypto definition cards")
    parser.add_argument("--term", help="Crypto term to define")
    parser.add_argument("--explanation", help="Short explanation/analogy")
    parser.add_argument("--output", help="Output PNG path", default="card.png")
    parser.add_argument("--json", help="Batch mode: path to posts.json")
    parser.add_argument("--output-dir", help="Batch mode: output directory", default="./cards/")
    args = parser.parse_args()

    if args.json:
        generate_from_json(args.json, args.output_dir)
    elif args.term and args.explanation:
        generate_card(args.term, args.explanation, args.output)
        print(f"Generated: {args.output}")
    else:
        parser.print_help()
