#!/usr/bin/env python3
import sys
from pathlib import Path
from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw

inky = auto()
inky.set_border(inky.WHITE)

# Load text from file
if len(sys.argv) < 2:
    print("Usage: python3 display_inky_text.py <textfile>")
    sys.exit(1)

file_path = Path(sys.argv[1])
if not file_path.exists():
    print(f"File not found: {file_path}")
    sys.exit(1)

text = file_path.read_text().strip()

# Create image
img = Image.new("P", inky.resolution, color=inky.WHITE)
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)

draw.multiline_text((10, 10), text, fill=inky.BLACK, font=font, spacing=4)
inky.set_image(img)
inky.show()
