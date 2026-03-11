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
    Pixel-art AEM robot.  Head lives in the white strip; base straddles the
    white/dark boundary.  All dimensions are multiples of P (=16 px).

    Vertical layout (from top):
      ant_top  = WHITE_H - 9P  = 185 - 144 = 41
      head_top = WHITE_H - 5P  = 185 - 80  = 105
      head_bot = WHITE_H       = 185          ← white/dark boundary
      base_top = WHITE_H + P   = 201
      base_bot = WHITE_H + 4P  = 249
    """
    cx = W // 2   # 540

    head_top = WHITE_H - 5 * P   # 105
    ant_top  = head_top - 4 * P  # 41

    # ── Antennas ─────────────────────────────────────────────────────────────
    # Each antenna: shaft (1P wide) + square cap on top
    ant_shaft_w = P                         # 16 px
    cap_w       = P + P // 2               # 24 px  (wider cap)
    cap_h       = P                         # 16 px

    for side in (-1, 1):
        if side == -1:
            shaft_x0 = cx - 3 * P
        else:
            shaft_x0 = cx + 3 * P - ant_shaft_w
        shaft_x1 = shaft_x0 + ant_shaft_w

        # shaft
        rect(draw, shaft_x0, ant_top + cap_h, shaft_x1, head_top, TEAL)
        # cap (slightly wider, square)
        cap_x0 = shaft_x0 - (cap_w - ant_shaft_w) // 2
        rect(draw, cap_x0, ant_top, cap_x0 + cap_w, ant_top + cap_h, TEAL)

    # ── Head ─────────────────────────────────────────────────────────────────
    hw  = 9 * P      # 144 px wide
    hx  = cx - hw // 2  # 468

    # Outer frame  (dark fill + teal border)
    rect(draw, hx, head_top, hx + hw, WHITE_H, BODY_DARK, outline=TEAL, width=3)

    # Inner screen  (light teal)
    sp = P - 2   # 14 px padding
    rect(draw, hx + sp, head_top + sp, hx + hw - sp, WHITE_H - sp, SCREEN_COL)

    # Pixel eyes — two dark rectangles centered on screen
    eye_w = P + P // 2   # 24 px
    eye_h = P + P // 3   # ~21 px
    eye_y = head_top + sp + P
    eye_gap = P      # gap from screen edge and between eyes
    # left eye
    rect(draw, cx - eye_w - eye_gap, eye_y, cx - eye_gap, eye_y + eye_h, EYE_COL)
    # right eye
    rect(draw, cx + eye_gap, eye_y, cx + eye_gap + eye_w, eye_y + eye_h, EYE_COL)

    # Mouth — short dark bar near bottom of screen
    m_y = WHITE_H - sp - P
    rect(draw, cx - P - P // 2, m_y, cx + P + P // 2, m_y + P // 3, EYE_COL)

    # ── Base / body ───────────────────────────────────────────────────────────
    bw = 11 * P   # 176 px  (wider than head)
    bh = 3 * P    # 48 px
    bx = cx - bw // 2   # 452
    by = WHITE_H + P     # 201

    rect(draw, bx, by, bx + bw, by + bh, BODY_DARK, outline=TEAL, width=3)

    # Small teal display panel centred on base
    pw = 3 * P    # 48 px
    ph = P + P // 3
    px0 = cx - pw // 2
    py0 = by + P // 2
    rect(draw, px0, py0, px0 + pw, py0 + ph, TEAL)


# ── AEM logo ──────────────────────────────────────────────────────────────────

# Path to the real AEM logo PNG (aem_logo.png should be in same directory)
LOGO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aem_logo.png")


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
    Uses aem_logo.png if present (pixel-perfect), otherwise draws via code.
    """
    logo_y  = H - 115

    if os.path.exists(LOGO_FILE):
        # ── Use real logo file ────────────────────────────────────────────────
        logo_img = Image.open(LOGO_FILE).convert("RGBA")
        # Scale logo to fit within 220px wide × 80px tall keeping aspect ratio
        logo_img.thumbnail((220, 80), Image.Resampling.LANCZOS)
        lw, lh = logo_img.size
        lx = (W - lw) // 2
        ly = logo_y + (80 - lh) // 2
        img.paste(logo_img, (lx, ly), logo_img)
        return

    # ── Drawn fallback (supersampled for smoothness) ──────────────────────────
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

def generate_card(term, explanation, output_path, day_num=None):
    """Generate a branded 1080×1080 AEM Algorithm card."""
    img  = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # White top strip
    draw.rectangle([(0, 0), (W, WHITE_H)], fill=WHITE)

    # Pixel robot (head in white strip, base in dark navy)
    draw_robot(draw)

    # Fonts
    f_term = load_font(BOLD_FONTS,    58)
    f_body = load_font(REGULAR_FONTS, 32)
    f_aem  = load_font(BOLD_FONTS,    40)
    f_algo = load_font(REGULAR_FONTS, 20)

    # Day badge (white strip, top-right)
    if day_num:
        f_badge = load_font(REGULAR_FONTS, 22)
        badge   = f"Day {day_num}"
        bb      = draw.textbbox((0, 0), badge, font=f_badge)
        draw.text((W - (bb[2] - bb[0]) - 48, 60), badge, fill=BLUE, font=f_badge)

    # Content zone: from just below robot base to just above logo
    content_top    = WHITE_H + 4 * P + 30   # ~281 px
    content_bottom = H - 120                # ~960 px
    max_w = W - 200

    term_lines = wrap_text(term.upper(), f_term, max_w, draw)
    expl_lines = wrap_text(explanation,  f_body, max_w, draw)

    th = block_height(term_lines, f_term, draw, 1.3)
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
    draw_block(draw, expl_lines, f_body, TEXT_WHITE, sep_y + 32, 1.5)

    # AEM logo bottom centre
    draw_aem_logo(img, draw, f_aem, f_algo)

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
            day_num=i + 1,
        )
        print(f"  Generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AEM crypto definition cards")
    parser.add_argument("--term", help="Crypto term to define")
    parser.add_argument("--explanation", help="Short explanation/analogy")
    parser.add_argument("--output", help="Output PNG path", default="card.png")
    parser.add_argument("--day", type=int, help="Day number badge")
    parser.add_argument("--json", help="Batch mode: path to posts.json")
    parser.add_argument("--output-dir", help="Batch mode: output directory", default="./cards/")
    args = parser.parse_args()

    if args.json:
        generate_from_json(args.json, args.output_dir)
    elif args.term and args.explanation:
        generate_card(args.term, args.explanation, args.output, day_num=args.day)
        print(f"Generated: {args.output}")
    else:
        parser.print_help()
