"""
Instagram Card Generator — AEM Algorithm "The Terminal" Style

Generates branded 1080x1080 crypto education cards.
Dark background with electric blue (#1890FF) accents.

Usage:
    python instagram_definition_card.py --term "Bitcoin Halving" --explanation "Every 210,000 blocks..." --output card.png
    python instagram_definition_card.py --json posts.json --output-dir ./cards/
"""

import argparse
import json
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

# --- Brand Config ---
CARD_SIZE = (1080, 1080)
BG_COLOR = (13, 13, 13)          # #0D0D0D — dark black
ACCENT_BLUE = (24, 144, 255)     # #1890FF — AEM brand blue
TEXT_WHITE = (255, 255, 255)
TEXT_GREY = (160, 160, 160)
GRID_COLOR = (30, 30, 30)        # subtle grid lines

# Font sizes
TERM_SIZE = 52
EXPLANATION_SIZE = 30
FOOTER_SIZE = 18

# Try to load fonts (fallback chain)
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_REGULAR_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def load_font(paths, size):
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def text_block_height(lines, font, draw, line_spacing=1.4):
    total = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        total += int((bbox[3] - bbox[1]) * line_spacing)
    return total


def draw_text_block(draw, lines, font, color, start_y, line_spacing=1.4, align="center"):
    y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        if align == "center":
            x = (CARD_SIZE[0] - line_width) // 2
        else:
            x = 80
        draw.text((x, y), line, fill=color, font=font)
        y += int(line_height * line_spacing)
    return y


def draw_grid(draw):
    """Draw subtle grid/matrix pattern in background."""
    spacing = 60
    for x in range(0, CARD_SIZE[0], spacing):
        draw.line([(x, 0), (x, CARD_SIZE[1])], fill=GRID_COLOR, width=1)
    for y in range(0, CARD_SIZE[1], spacing):
        draw.line([(0, y), (CARD_SIZE[0], y)], fill=GRID_COLOR, width=1)


def generate_card(term, explanation, output_path, day_num=None):
    """Generate a single AEM Terminal-style crypto card."""
    img = Image.new("RGB", CARD_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Subtle grid background
    draw_grid(draw)

    # Load fonts
    font_bold = load_font(FONT_PATHS, TERM_SIZE)
    font_body = load_font(FONT_REGULAR_PATHS, EXPLANATION_SIZE)
    font_footer = load_font(FONT_REGULAR_PATHS, FOOTER_SIZE)

    # Blue accent line at top
    draw.rectangle([(0, 0), (CARD_SIZE[0], 4)], fill=ACCENT_BLUE)

    # Day badge (optional, top-right)
    if day_num:
        badge_font = load_font(FONT_REGULAR_PATHS, 16)
        badge_text = f"Day {day_num}"
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        badge_w = bbox[2] - bbox[0]
        draw.text((CARD_SIZE[0] - badge_w - 40, 30), badge_text, fill=TEXT_GREY, font=badge_font)

    # Calculate layout
    max_text_width = CARD_SIZE[0] - 160
    term_lines = wrap_text(term.upper(), font_bold, max_text_width, draw)
    explanation_lines = wrap_text(explanation, font_body, max_text_width, draw)

    term_height = text_block_height(term_lines, font_bold, draw, 1.3)
    explanation_height = text_block_height(explanation_lines, font_body, draw, 1.5)
    separator_space = 40
    total_content = term_height + separator_space + explanation_height

    # Center vertically
    start_y = (CARD_SIZE[1] - total_content) // 2

    # Draw term (blue, bold, uppercase)
    y = draw_text_block(draw, term_lines, font_bold, ACCENT_BLUE, start_y, 1.3, "center")

    # Blue separator line
    line_y = y + 15
    line_width = min(200, max_text_width)
    line_x = (CARD_SIZE[0] - line_width) // 2
    draw.line([(line_x, line_y), (line_x + line_width, line_y)], fill=ACCENT_BLUE, width=2)

    # Draw explanation (white)
    draw_text_block(draw, explanation_lines, font_body, TEXT_WHITE, line_y + 25, 1.5, "center")

    # Footer
    footer_text = "AEM Algorithm"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    footer_w = bbox[2] - bbox[0]
    draw.text(
        ((CARD_SIZE[0] - footer_w) // 2, CARD_SIZE[1] - 60),
        footer_text,
        fill=TEXT_GREY,
        font=font_footer,
    )

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
