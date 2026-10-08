from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont, ImageOps


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


def add_glow(canvas: Image.Image, center: tuple[int, int], size: tuple[int, int], color: tuple[int, int, int], opacity: int) -> None:
    gradient = ImageOps.invert(Image.radial_gradient("L")).resize(size, Image.Resampling.LANCZOS)
    gradient = gradient.point(lambda value: value * opacity // 255)
    glow = Image.new("RGBA", size, (*color, 0))
    glow.putalpha(gradient)
    canvas.alpha_composite(glow, (center[0] - size[0] // 2, center[1] - size[1] // 2))


def main() -> None:
    random.seed(2026)
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (*BACKGROUND, 255))

    add_glow(canvas, (950, 250), (1800, 1000), BLUE, 76)
    add_glow(canvas, (3670, 360), (1300, 950), (91, 164, 255), 58)

    draw = ImageDraw.Draw(canvas)
    for _ in range(280):
        x = random.randrange(WIDTH)
        y = random.randrange(HEIGHT)
        radius = random.choice((1, 1, 1, 2, 2, 3))
        alpha = random.randrange(85, 225)
        color = (255, 255, 255, alpha) if random.random() > 0.28 else (143, 188, 255, alpha)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

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
    tagline_font = ImageFont.truetype(str(rounded_font), 58)

    title_x = logo_x + logo.width + 32
    title_y = 190
    draw = ImageDraw.Draw(canvas)
    draw.text((title_x, title_y), "software.llc", font=title_font, fill=(*BLUE, 255), stroke_width=1)

    tagline = "Thoughtful software for a more decent web."
    draw.text((760, 465), tagline, font=tagline_font, fill=(244, 247, 251, 245))

    draw.rounded_rectangle((650, 570, 2360, 578), radius=4, fill=(*BLUE, 220))

    rgb = Image.new("RGB", canvas.size, BACKGROUND)
    rgb.paste(canvas, mask=canvas.getchannel("A"))
    rgb.save(OUTPUT, "JPEG", quality=93, optimize=True, progressive=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
