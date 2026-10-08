"""ascii_art.json + stats.json으로 neofetch 스타일 프로필 카드 SVG(라이트/다크)를 만든다.

결과물: .github/images/profile-card-{light,dark}.svg, link-{slug}-{light,dark}.svg
패널 문구를 바꾸려면 PROFILE / ACTIVITY만 고치면 된다.
SVG 안의 링크는 GitHub README에서 클릭되지 않으므로, 링크는 카드와 같은 스타일의
버튼 SVG로 따로 만들고 README에서 각각 <a>로 감싼다. (주소는 README에 있다)
"""
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGES = HERE.parent / "images"
USER = "Archibald1948"

PROFILE = [
    ("Role", "Full-stack Developer"),
    ("Agent", "Claude"),
    ("Stack.Core", "React, Next.js, TypeScript"),
    ("Stack.Style", "Tailwind CSS"),
    ("Stack.Package", "npm, yarn, pnpm"),
    ("Tools", "Git, GitHub, Figma, Notion, Vercel"),
]
ACTIVITY = [
    ("Open Source", "Toss contributor"),
    ("Community", "GDGoC, Kakao Univ LikeLion admin"),
    ("Hackathons", "6 so far"),
    ("Partner", "Jocoding AX Partners"),
    ("Watching", "Microsoft, Anthropic, Toss"),
]

# (파일 이름용 slug, 앞 기호, 이름)
LINKS = [
    ("dashboard", "~/", "dashboard"),
    ("til", "~/", "TIL"),
    ("agent-kit", "~/", "agent-kit"),
    ("sync-forks", "~/", "sync-forks"),
    ("jocodingax", "", "jocodingax.ai"),
    ("microsoft", "@", "microsoft"),
    ("anthropic", "@", "anthropics"),
    ("toss", "@", "toss"),
]

FONT = "Menlo,Consolas,'DejaVu Sans Mono','SFMono-Regular','Liberation Mono',monospace"
PAD = 32
# 아트: 한 칸 = 가로 6.6 x 세로 13.2(위아래 두 픽셀)
ART_CW, ART_RH = 6.6, 13.2
# 패널: 고정폭 글자를 textLength로 고정해 폰트가 달라도 정렬이 유지되게 한다.
CW, LH, FS = 8.4, 19.6, 14
PANEL_COLS = 60
STAT_SPLIT = 33  # 통계 줄에서 왼쪽 항목이 차지하는 글자 수
GAP = 40
# 링크 버튼
LINK_CW, LINK_FS, LINK_PAD, LINK_H = 7.2, 12, 10, 26

THEMES = {
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "text": "#e6edf3", "muted": "#7d8590",
        "rule": "#30363d", "key": "#ffa657", "add": "#3fb950", "del": "#f85149",
    },
    "light": {
        "bg": "#f6f8fa", "border": "#d0d7de", "text": "#1f2328", "muted": "#8c959f",
        "rule": "#d0d7de", "key": "#bc4c00", "add": "#1a7f37", "del": "#cf222e",
    },
}

Seg = tuple[str, str]  # (텍스트, 테마 색상 키 또는 #hex)


def art_color(hex_color: str, theme: str) -> str:
    """다크 테마에서는 검은 선·머리카락이 배경에 묻히지 않도록 밝은 회색 쪽으로 올린다."""
    if theme != "dark":
        return hex_color
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    if 0.299 * r + 0.587 * g + 0.114 * b < 70:
        return "#444c56"
    return hex_color


def uptime(created_at: str) -> str:
    start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    months = (now.year - start.year) * 12 + now.month - start.month
    if now.day < start.day:
        months -= 1
    anchor_month = start.month + months
    anchor = start.replace(year=start.year + (anchor_month - 1) // 12, month=(anchor_month - 1) % 12 + 1)
    days = (now - anchor).days
    years, months = divmod(months, 12)
    parts = [(years, "year"), (months, "month"), (days, "day")]
    return ", ".join(f"{n} {unit}{'s' if n != 1 else ''}" for n, unit in parts if n or unit == "day")


def kv(key: str, value: list[Seg], width: int, bullet: bool = True) -> list[Seg]:
    """'. Key: ........ value' 한 칸을 width 글자에 맞춰 만든다."""
    head = (". " if bullet else "") + key + ":"
    value_len = sum(len(t) for t, _ in value)
    dots = max(width - len(head) - value_len - 2, 1)
    lead = [(". ", "muted")] if bullet else []
    return lead + [(key, "key"), (":", "muted"), (" " + "." * dots + " ", "rule")] + value


def rule(title: str, color: str = "text") -> list[Seg]:
    return [(title + " ", color), ("─" * (PANEL_COLS - len(title) - 1), "rule")]


def num(n: int) -> str:
    return f"{n:,}"


def build_panel(stats: dict) -> list[list[Seg]]:
    def pair(k1: str, v1: list[Seg], k2: str, v2: list[Seg]) -> list[Seg]:
        right = PANEL_COLS - STAT_SPLIT - 3
        return kv(k1, v1, STAT_SPLIT) + [(" | ", "muted")] + kv(k2, v2, right, bullet=False)

    lines = [[(USER, "key"), ("@github ", "text"), ("─" * (PANEL_COLS - len(USER) - 8), "rule")]]
    lines.append(kv("Uptime", [(uptime(stats["created_at"]), "text")], PANEL_COLS))
    lines += [kv(k, [(v, "text")], PANEL_COLS) for k, v in PROFILE]
    lines.append(rule("- Activity"))
    lines += [kv(k, [(v, "text")], PANEL_COLS) for k, v in ACTIVITY]
    lines.append(rule("- GitHub Stats"))
    lines.append(pair(
        "Repos", [(num(stats["repos_total"]), "text"), (" {Public: ", "muted"),
                  (num(stats["repos_public"]), "text"), ("}", "muted")],
        "Stars", [(num(stats["stars"]), "text")],
    ))
    lines.append(pair(
        "Commits", [(num(stats["commits"]), "text")],
        "Followers", [(num(stats["followers"]), "text")],
    ))
    lines.append(kv("Lines of Code", [
        (num(stats["loc_additions"] - stats["loc_deletions"]), "text"), (" ( ", "muted"),
        (num(stats["loc_additions"]) + "++", "add"), (", ", "muted"),
        (num(stats["loc_deletions"]) + "--", "del"), (" )", "muted"),
    ], PANEL_COLS))
    return lines


def tspan(x: float, text: str, fill: str, cw: float) -> str:
    return (f'<tspan x="{x:.1f}" fill="{fill}" textLength="{len(text) * cw:.1f}" '
            f'lengthAdjust="spacingAndGlyphs">{escape(text)}</tspan>')


def render_art(art: dict, theme: str, x0: float, y0: float) -> list[str]:
    """반블록 아트를 픽셀 단위 rect로 그린다.

    ▀▄█ 글리프를 텍스트로 쓰면 폰트마다 칸을 채우는 높이가 달라 격자 틈이 비친다.
    그래서 같은 격자(한 칸 = 가로 ART_CW, 위아래 픽셀 각 ART_RH / 2)를 rect로 찍고,
    같은 색이 가로로 이어지면 하나로 합친다.
    """
    out = []
    ph = ART_RH / 2
    for y, row in enumerate(art["pixels"]):
        x = 0
        while x < len(row):
            color = row[x]
            run = 1
            while x + run < len(row) and row[x + run] == color:
                run += 1
            if color:
                out.append(f'<rect x="{x0 + x * ART_CW:.1f}" y="{y0 + y * ph:.1f}" '
                           f'width="{run * ART_CW:.1f}" height="{ph:.1f}" fill="{art_color(color, theme)}"/>')
            x += run
    return out


def render(theme: str, art: dict, stats: dict) -> str:
    colors = THEMES[theme]
    panel = build_panel(stats)
    art_w, art_h = art["cols"] * ART_CW, art["rows"] * ART_RH
    panel_w, panel_h = PANEL_COLS * CW, len(panel) * LH
    width = PAD * 2 + art_w + GAP + panel_w
    height = PAD * 2 + max(art_h, panel_h)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="{USER} GitHub profile card">',
        f'<rect x="0.5" y="0.5" width="{width - 1:.0f}" height="{height - 1:.0f}" rx="8" '
        f'fill="{colors["bg"]}" stroke="{colors["border"]}"/>',
        '<g shape-rendering="crispEdges">',
        *render_art(art, theme, PAD, PAD + (height - PAD * 2 - art_h) / 2),
        "</g>",
        f'<g font-family="{FONT}" font-size="{FS}" xml:space="preserve">',
    ]
    px = PAD + art_w + GAP
    py = PAD + (height - PAD * 2 - panel_h) / 2
    for i, line in enumerate(panel):
        x, body = px, []
        for text, color in line:
            body.append(tspan(x, text, colors.get(color, color), CW))
            x += len(text) * CW
        parts.append(f'<text y="{py + (i + 1) * LH - 5:.1f}">{"".join(body)}</text>')
    parts += ["</g>", "</svg>"]
    return "\n".join(parts) + "\n"


def render_link(theme: str, prefix: str, name: str) -> str:
    """README 한 줄(약 830px)에 8개가 다 들어가도록 작게 만든 링크 버튼."""
    colors = THEMES[theme]
    pad, height = LINK_PAD, LINK_H
    width = pad * 2 + (len(prefix) + len(name)) * LINK_CW
    x = pad
    spans = []
    for text, color in [(prefix, "muted"), (name, "key")]:
        if text:
            spans.append(tspan(x, text, colors[color], LINK_CW))
            x += len(text) * LINK_CW
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height}" '
        f'viewBox="0 0 {width:.0f} {height}" role="img" aria-label="{escape(prefix + name)}">',
        f'<rect x="0.5" y="0.5" width="{width - 1:.0f}" height="{height - 1}" rx="6" '
        f'fill="{colors["bg"]}" stroke="{colors["border"]}"/>',
        f'<text y="{height / 2 + LINK_FS * 0.35:.1f}" font-family="{FONT}" font-size="{LINK_FS}" '
        f'xml:space="preserve">{"".join(spans)}</text>',
        "</svg>",
    ]) + "\n"


def main() -> None:
    art = json.loads((HERE / "ascii_art.json").read_text())
    stats = json.loads((HERE / "stats.json").read_text())
    for theme in THEMES:
        path = IMAGES / f"profile-card-{theme}.svg"
        path.write_text(render(theme, art, stats))
        print(f"saved {path.name}")
        for slug, prefix, name in LINKS:
            (IMAGES / f"link-{slug}-{theme}.svg").write_text(render_link(theme, prefix, name))
    print(f"saved {len(LINKS)} link buttons x {len(THEMES)} themes")


if __name__ == "__main__":
    main()
