#!/usr/bin/env python3
"""把 AI 生成的底图裁成 3:1 横幅并叠加标题，输出 assets/header.jpg"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC = "assets/Ultra_wide_cinematic_banner__d_2026-11-03T07-33-30.png"
OUT = "assets/header.jpg"
W, H = 900, 300

img = Image.open(SRC).convert("RGB")
# 裁中间 3:1 带（1536 宽 -> 512 高），避开底部水印
band_h = img.width // 3
top = 200
img = img.crop((0, top, img.width, top + band_h)).resize((W, H), Image.LANCZOS)
img = img.convert("RGBA")

MENLO = "/System/Library/Fonts/Menlo.ttc"
title_font = ImageFont.truetype(MENLO, 58, index=1)
cn_font = None
for p, idx in [
    ("/System/Library/Fonts/PingFang.ttc", 0),
    ("/System/Library/Fonts/STHeiti Light.ttc", 0),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 0),
]:
    for i in (idx, 1, 2):
        try:
            f = ImageFont.truetype(p, 20, index=i)
            # 验证真的能画出中文
            if ImageDraw.Draw(Image.new("RGB", (40, 40))).textbbox((0, 0), "逸", font=f)[2] > 0:
                cn_font = f
                break
        except Exception:
            continue
    if cn_font:
        break
if cn_font is None:
    cn_font = title_font.font_variant(size=20)
print("cn font:", cn_font.path if hasattr(cn_font, "path") else cn_font)

d = ImageDraw.Draw(img)
t = "YCHECH"
bb = d.textbbox((0, 0), t, font=title_font)
tx, ty = (W - (bb[2] - bb[0])) // 2 - bb[0], 66 - bb[1]

# 辉光
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.text((tx, ty), t, font=title_font, fill=(120, 255, 205, 150))
glow = glow.filter(ImageFilter.GaussianBlur(8))
img.alpha_composite(glow)

d = ImageDraw.Draw(img)
d.text((tx, ty), t, font=title_font, fill=(240, 255, 250, 250),
       stroke_width=1, stroke_fill=(200, 255, 235, 220))

sub = "逸尘 · CODE / AI / FUN"
bb2 = d.textbbox((0, 0), sub, font=cn_font)
sx, sy = (W - (bb2[2] - bb2[0])) // 2, 156
sub_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sub_glow).text((sx, sy), sub, font=cn_font, fill=(120, 255, 205, 120))
img.alpha_composite(sub_glow.filter(ImageFilter.GaussianBlur(5)))
d.text((sx, sy), sub, font=cn_font, fill=(225, 245, 238, 235))

img.convert("RGB").save(OUT, quality=90)
import os
print("saved", OUT, os.path.getsize(OUT) // 1024, "KB")
