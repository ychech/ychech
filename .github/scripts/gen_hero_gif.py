#!/usr/bin/env python3
"""AI 底图 + 动效叠加 -> 无缝循环 GIF（统一调色板，避免颜色错乱）。"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(7)

SRC = "assets/Ultra_wide_cinematic_banner__d_2026-11-04T02-07-04.png"
OUT = "assets/hero.gif"
W, H = 900, 300
FRAMES = 40
DURATION = 50  # ms -> 2.5s 循环

base = Image.open(SRC).convert("RGB")
band_h = base.width // 3
base = base.crop((0, 260, base.width, 260 + band_h)).resize((W, H), Image.LANCZOS).convert("RGBA")

# ---- 标题层（每帧静态叠加，清晰稳定） ----
MENLO = "/System/Library/Fonts/Menlo.ttc"
title_font = ImageFont.truetype(MENLO, 58, index=1)
cn_font = None
for p in ["/System/Library/Fonts/STHeiti Light.ttc", "/System/Library/Fonts/PingFang.ttc"]:
    try:
        f = ImageFont.truetype(p, 20)
        if ImageDraw.Draw(Image.new("RGB", (40, 40))).textbbox((0, 0), "逸", font=f)[2] > 0:
            cn_font = f
            break
    except Exception:
        continue

title_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
td = ImageDraw.Draw(title_layer)
t = "YCHECH"
bb = td.textbbox((0, 0), t, font=title_font)
tx, ty = (W - (bb[2] - bb[0])) // 2 - bb[0], 62 - bb[1]
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).text((tx, ty), t, font=title_font, fill=(110, 255, 205, 135))
title_layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)))
td = ImageDraw.Draw(title_layer)
td.text((tx, ty), t, font=title_font, fill=(242, 255, 250, 250), stroke_width=1, stroke_fill=(200, 255, 235, 230))
sub = "逸尘 · CODE / AI / FUN"
bb2 = td.textbbox((0, 0), sub, font=cn_font)
sx, sy = (W - (bb2[2] - bb2[0])) // 2, 158
sglow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sglow).text((sx, sy), sub, font=cn_font, fill=(110, 255, 205, 110))
title_layer.alpha_composite(sglow.filter(ImageFilter.GaussianBlur(6)))
td.text((sx, sy), sub, font=cn_font, fill=(228, 245, 238, 235))

# ---- 动效素材 ----
# 1) 亮字符列：只在两侧生成，速度取 H 的整数倍/循环保证无缝
digit_font = ImageFont.truetype(MENLO, 16, index=0)
lh = 24
strip_h = H  # 内容周期
col_layer_strips = []
for cx in list(range(20, 210, 34)) + list(range(W - 210, W - 20, 34)):
    strip = Image.new("RGBA", (14, strip_h))
    sd = ImageDraw.Draw(strip)
    y = random.randint(0, lh)
    while y < strip_h:
        sd.text((0, y), random.choice("01"), font=digit_font, fill=(180, 255, 220, random.randint(120, 220)))
        y += lh
    col_layer_strips.append({"x": cx, "strip": strip, "y0": random.uniform(0, H), "m": random.randint(2, 4)})

# 2) 漂浮光点
particles = [{"x": random.uniform(0, W), "y": random.uniform(0, H),
              "r": random.uniform(1.5, 4), "ph": random.uniform(0, 2 * math.pi),
              "m": random.randint(1, 2)} for _ in range(26)]

# ---- 渲染帧 ----
frames = []
for f in range(FRAMES):
    img = base.copy()
    # 亮字符列（轻微发光：先模糊一层再叠清晰层）
    cols_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for c in col_layer_strips:
        y = (c["y0"] + c["m"] * H * f // FRAMES) % H - H
        cols_img.paste(c["strip"], (c["x"], int(y)), c["strip"])
    blur_cols = cols_img.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(blur_cols)
    img.alpha_composite(cols_img)
    # 光点
    pt_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pt_img)
    for p in particles:
        y = (p["y"] + p["m"] * H * f // FRAMES) % H
        a = 100 + 90 * math.sin(2 * math.pi * f / FRAMES * 2 + p["ph"])
        pd.ellipse([p["x"] - p["r"], y - p["r"], p["x"] + p["r"], y + p["r"]],
                   fill=(140, 255, 210, max(0, int(a))))
    img.alpha_composite(pt_img.filter(ImageFilter.GaussianBlur(1)))
    # 全局微呼吸（整数周期无缝）
    flick = 1 + 0.03 * math.sin(2 * math.pi * f / FRAMES)
    img = Image.eval(img.convert("RGB"), lambda v: min(255, int(v * flick))).convert("RGBA")
    # 标题
    img.alpha_composite(title_layer)
    frames.append(img.convert("RGB"))

# ---- 统一调色板（关键：用同一份调色板量化所有帧） ----
pal_img = frames[0].quantize(colors=144, method=Image.MEDIANCUT, dither=Image.Dither.NONE)
qframes = [fr.quantize(palette=pal_img, dither=Image.Dither.NONE) for fr in frames]
qframes[0].save(OUT, save_all=True, append_images=qframes[1:], duration=DURATION, loop=0, optimize=True)

frames[10].save("/tmp/hero_frame.png")
import os
print("saved", OUT, os.path.getsize(OUT) // 1024, "KB")
