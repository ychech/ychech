#!/usr/bin/env python3
"""每天抓取 GitHub 公开数据，生成两张霓虹风格 SVG 战绩卡（stats.svg / langs.svg）。"""
import json
import os
import urllib.request

TOKEN = os.environ.get("GH_TOKEN", "")
USER = "ychech"
OUT = os.environ.get("OUT_DIR", "dist")

CYAN, PURPLE, PINK, GREEN = "#36BCF7", "#8A2BE2", "#FF2E97", "#7ee787"
BG, BORDER, GRAY = "#0d1117", "#30363d", "#8b949e"

LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "HTML": "#e34c26", "Go": "#00ADD8", "Rust": "#dea584", "Vue": "#41b883",
    "Shell": "#89e051", "CSS": "#563d7c", "C++": "#f34b7d", "Java": "#b07219",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-stats"})
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


user = get(f"https://api.github.com/users/{USER}")
repos, page = [], 1
while page <= 3:
    rs = get(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
    repos += rs
    if len(rs) < 100:
        break
    page += 1

stars = sum(r["stargazers_count"] for r in repos)
followers = user.get("followers", 0)
repo_n = user.get("public_repos", 0)
joined = (user.get("created_at") or "")[:4]

langs = {}
for r in repos:
    l = r.get("language")
    if l:
        langs[l] = langs.get(l, 0) + 1
top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
total = sum(v for _, v in top) or 1

DEFS = f'''<defs>
    <linearGradient id="ng" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{CYAN}"/><stop offset="0.5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{PINK}"/>
    </linearGradient>
    <filter id="gl" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>'''

W, H = 430, 190

# ---- 战绩卡 ----
rows = [
    ("\u2b50  Total Stars", str(stars), CYAN),
    ("\U0001f465  Followers", str(followers), PURPLE),
    ("\U0001f4e6  Public Repos", str(repo_n), PINK),
    ("\U0001f552  Since", joined, GREEN),
]
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>',
    f'<text x="215" y="42" text-anchor="middle" font-family="Consolas,monospace" font-size="20" font-weight="700" fill="url(#ng)" filter="url(#gl)" letter-spacing="4">&#9889; YCHECH &#183; STATS</text>',
]
for i, (label, val, color) in enumerate(rows):
    y = 80 + i * 28
    parts.append(
        f'<text x="30" y="{y}" font-family="\'PingFang SC\',\'Microsoft YaHei\',sans-serif" font-size="15" fill="{GRAY}">{label}</text>'
        f'<text x="{W-30}" y="{y}" text-anchor="end" font-family="Consolas,monospace" font-size="17" font-weight="700" fill="{color}" filter="url(#gl)">{val}</text>'
    )
parts.append("</svg>")
stats_svg = "\n".join(parts)

# ---- 语言卡 ----
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}',
    f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>',
    f'<text x="215" y="42" text-anchor="middle" font-family="Consolas,monospace" font-size="20" font-weight="700" fill="url(#ng)" filter="url(#gl)" letter-spacing="4">&#9000; TOP LANGS</text>',
]
bar_w = 240
for i, (name, v) in enumerate(top):
    y = 78 + i * 24
    pct = v / total
    color = LANG_COLORS.get(name, CYAN)
    parts.append(
        f'<text x="30" y="{y}" font-family="Consolas,monospace" font-size="13" fill="{GRAY}">{name}</text>'
        f'<rect x="135" y="{y-11}" width="{bar_w}" height="12" rx="6" fill="#21262d"/>'
        f'<rect x="135" y="{y-11}" width="{max(6, round(bar_w*pct))}" height="12" rx="6" fill="{color}" opacity="0.9"/>'
        f'<text x="{W-24}" y="{y}" text-anchor="end" font-family="Consolas,monospace" font-size="12" fill="{color}">{round(pct*100)}%</text>'
    )
parts.append("</svg>")
langs_svg = "\n".join(parts)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "stats.svg"), "w") as f:
    f.write(stats_svg)
with open(os.path.join(OUT, "langs.svg"), "w") as f:
    f.write(langs_svg)
print("generated:", OUT, "| stars:", stars, "| followers:", followers, "| langs:", [n for n, _ in top])
