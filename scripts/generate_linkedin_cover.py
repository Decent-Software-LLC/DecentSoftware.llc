from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "images"
OUTPUT = ASSETS / "decent-software-linkedin-cover.jpg"

WIDTH, HEIGHT = 4200, 700
BLUE = (59, 134, 246)
BACKGROUND = (7, 9, 14)


def contain(path: Path, max_width: int, max_height: int) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    return image


def main() -> None:
    random.seed(2026)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (*BACKGROUND, 255))

    draw = ImageDraw.Draw(canvas)
    for _ in range(280):
        x = random.randrange(WIDTH)
        y = random.randrange(HEIGHT)
        radius = random.choice((1, 1, 1, 2, 2, 3))
        alpha = random.randrange(85, 225)
        color = (255, 255, 255, alpha) if random.random() > 0.28 else (143, 188, 255, alpha)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    nebula = contain(ASSETS / "linkedin-nebula.png", 1800, 820)
    nebula.putalpha(nebula.getchannel("A").point(lambda value: value * 105 // 255))
    canvas.alpha_composite(nebula, (-120, -270))

    earth = contain(ASSETS / "clay-world.png", 900, 900)
    canvas.alpha_composite(earth, (WIDTH - 730, -95))

    shuttle = contain(ASSETS / "clay-shuttle-columbia.png", 680, 340)
    shuttle.putalpha(shuttle.getchannel("A").point(lambda value: value * 190 // 255))
    canvas.alpha_composite(shuttle, (2920, 58))

    logo = contain(ASSETS / "decent.png", 720, 285)
    logo_x = 650
    logo_y = 115
    canvas.alpha_composite(logo, (logo_x, logo_y))

    rounded_font = Path("/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf")
    title_font = ImageFont.truetype(str(rounded_font), 142)

    title_x = logo_x + logo.width + 32
    title_y = 190
    draw = ImageDraw.Draw(canvas)
    draw.text((title_x, title_y), "software.llc", font=title_font, fill=(*BLUE, 255), stroke_width=1)

    tagline = "Thoughtful software for a more decent web."
    title_box = draw.textbbox((title_x, title_y), "software.llc", font=title_font, stroke_width=1)
    lockup_width = title_box[2] - logo_x
    tagline_size = 58
    tagline_font = ImageFont.truetype(str(rounded_font), tagline_size)
    while draw.textlength(tagline, font=tagline_font) < lockup_width:
        tagline_size += 1
        tagline_font = ImageFont.truetype(str(rounded_font), tagline_size)
    tagline_size -= 1
    tagline_font = ImageFont.truetype(str(rounded_font), tagline_size)
    tagline_x = logo_x
    tagline_y = 465
    draw.text((tagline_x, tagline_y), tagline, font=tagline_font, fill=(244, 247, 251, 245))

    rgb = Image.new("RGB", canvas.size, BACKGROUND)
    rgb.paste(canvas, mask=canvas.getchannel("A"))
    rgb.save(OUTPUT, "JPEG", quality=93, optimize=True, progressive=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
