#!/usr/bin/env python3
"""逐帧渲染电影感二进制雨 GIF 头图：多层景深（远/中/近），近景虚化，中央标题。"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

random.seed(42)

W, H = 720, 240
FRAMES = 60
DURATION = 40  # ms/帧 -> 25fps，循环 2.4s
OUT = "assets/header.gif"

# 每层：字号、每帧位移、模糊、亮度权重
LAYERS = {
    "far":  {"size": 9,  "speed": 4,  "blur": 0.0, "alpha": 110},
    "mid":  {"size": 13, "speed": 8,  "blur": 0.0, "alpha": 185},
    "near": {"size": 21, "speed": 12, "blur": 2.8, "alpha": 230},
}

MENLO = "/System/Library/Fonts/Menlo.ttc"
CN_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]


def load_font(path, size, bold=False):
    idxs = [1, 0] if bold else [0, 1]
    for i in idxs:
        try:
            return ImageFont.truetype(path, size, index=i)
        except Exception:
            continue
    return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def load_cn(size):
    for p in CN_CANDIDATES:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return None


def make_strip(font, alpha, n_chars):
    """一根 H 高的字符条（内容上下平铺即可无缝循环），返回 2H 高的图。"""
    lh = int(font.size * 1.4)
    n = H // lh + 2
    strip = Image.new("RGBA", (int(font.size * 1.2) + 6, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    y = 0
    while y < H:
        ch = random.choice("01")
        # 每个字符亮度微抖动，模拟原片质感
        a = max(30, int(alpha * random.uniform(0.45, 1.0)))
        d.text((3, y), ch, font=font, fill=(120, 235, 190, a))
        y += lh
    tall = Image.new("RGBA", (strip.width, 2 * H))
    tall.paste(strip, (0, 0))
    tall.paste(strip, (0, H))
    return tall, lh


# 预生成所有列
cols = []
x = 0
while x < W:
    r = random.random()
    layer = "near" if r < 0.14 else ("mid" if r < 0.5 else "far")
    cfg = LAYERS[layer]
    font = load_font(MENLO, cfg["size"])
    strip, lh = make_strip(font, cfg["alpha"], 20)
    cols.append({
        "x": x, "layer": layer, "strip": strip,
        "y0": random.uniform(0, H), "speed": cfg["speed"],
    })
    x += int(cfg["size"] * 1.15) + random.randint(2, 14)

far_mid = [c for c in cols if c["layer"] != "near"]
near = [c for c in cols if c["layer"] == "near"]

# 暗角遮罩（预生成）
vignette = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vignette)
for i in range(60):
    a = int(120 * (1 - i / 60))
    vd.rectangle([i * 2, i * 2, W - 1 - i * 2, H - 1 - i * 2], outline=a)
vignette = vignette.filter(ImageFilter.GaussianBlur(30))
dark = Image.new("RGBA", (W, H), (4, 12, 10, 255))
vign_layer = Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)), dark, vignette.point(lambda v: 255 - v))

title_font = load_font(MENLO, 58, bold=True)
cn_font = load_cn(20)


def draw_title(img, f):
    d = ImageDraw.Draw(img)
    t = "YCHECH"
    bb = d.textbbox((0, 0), t, font=title_font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx, ty = (W - tw) // 2 - bb[0], 78 - bb[1]
    # 呼吸辉光（循环内整数个周期，保证无缝）
    pulse = 0.55 + 0.45 * math.sin(2 * math.pi * f / FRAMES * 2)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.text((tx, ty), t, font=title_font, fill=(110, 255, 200, int(160 * pulse)))
    glow = glow.filter(ImageFilter.GaussianBlur(7))
    img.alpha_composite(glow)
    d.text((tx, ty), t, font=title_font, fill=(235, 255, 248, 245), stroke_width=1, stroke_fill=(235, 255, 248, 245))
    sub = "逸尘 · CODE / AI / FUN" if cn_font else "YICHEN · CODE / AI / FUN"
    sf = cn_font or title_font
    bb2 = d.textbbox((0, 0), sub, font=sf)
    d.text(((W - (bb2[2] - bb2[0])) // 2, 158), sub, font=sf, fill=(190, 230, 215, 210))


frames = []
for f in range(FRAMES):
    img = Image.new("RGBA", (W, H), (6, 16, 13, 255))
    # 远/中景：清晰
    d = ImageDraw.Draw(img)
    for c in far_mid:
        y = (c["y0"] + f * c["speed"]) % H - H
        img.paste(c["strip"], (c["x"], int(y)), c["strip"])
    # 近景：整层虚化再叠回
    near_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for c in near:
        y = (c["y0"] + f * c["speed"]) % H - H
        near_img.paste(c["strip"], (c["x"], int(y)), c["strip"])
    near_img = near_img.filter(ImageFilter.GaussianBlur(LAYERS["near"]["blur"]))
    img.alpha_composite(near_img)
    img.alpha_composite(vign_layer)
    draw_title(img, f)
    frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=160))

frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=DURATION, loop=0, optimize=True)

# 输出一帧静态图供检查
frames[FRAMES // 3].convert("RGB").save("/tmp/header_frame.png")
import os
print("saved", OUT, os.path.getsize(OUT) // 1024, "KB")
