"""Builds the night-sky SVG cards used in README.md.

Every card is a self-contained SVG: fonts (Geist and Geist Mono, subset to the
characters used) and images are embedded as data URIs, because GitHub shows SVGs
as images and blocks anything they would load from elsewhere. Animation is plain
CSS inside the SVG and turns off for people who prefer reduced motion.

Edit the CONTENT section below, then run:

    pip install fonttools brotli pillow
    python scripts/build_cards.py

Fonts: Geist and Geist Mono by Vercel, SIL Open Font License (scripts/fonts/OFL.txt).
"""

import base64
import io
import random
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
SRC = ROOT / "scripts" / "src"
OUT = ROOT / "assets"

# ------------------------------------------------------------------ CONTENT

NAME = "Joshua Mathias"
TAGLINE = "Backend and cloud infrastructure."
INTRO = "CS student at Ontario Tech. Looking for a Winter 2027 co-op."
SITE = "jmscripts1.github.io"

# **double asterisks** mark bold words in ABOUT and RIGHT_NOW.
ABOUT = [
    "CS student at **Ontario Tech** in Whitby, ON. I work on backend and infrastructure: "
    "APIs, databases, containers and the CI pipelines around them.",
    "Before uni I did IT support at a managed service provider, imaging about 100 machines "
    "for about 40 small businesses, which is where **OpsWatch** came from.",
    "Off the clock I make soul beats, cut the occasional edit, read too much manhwa and lift.",
]

RIGHT_NOW = [
    "looking for a **Winter 2027 co-op** in backend, cloud or infrastructure",
    "building **OpsWatch**, self-hosted IT health monitoring",
    "happy to talk about Python, Docker and SQL, or why your PC won't boot",
]

PROJECTS = [
    {
        "file": "project-opswatch.svg",
        "title": "OpsWatch",
        "area": "systems & devops",
        "status": "in progress",
        "repo": "github.com/JMScripts1/opswatch",
        "summary": "Self-hosted IT health monitoring modelled on the remote monitoring tools "
                   "managed service providers use. Linux and Windows agents report to a FastAPI "
                   "server over outbound HTTPS with token authentication.",
        "steps": [
            ("Agents check", "Disk, services, backup age, TLS expiry, pending updates"),
            ("Server stores", "FastAPI and PostgreSQL, run with Docker Compose"),
            ("Rules engine", "One ticket per problem, escalated, closed once it clears"),
            ("Alerts send", "Discord or Slack, plus a daily summary"),
        ],
        "tags": ["Python", "FastAPI", "PostgreSQL", "Docker Compose", "GitHub Actions", "PowerShell", "pytest"],
    },
    {
        "file": "project-game-deal-tracker.svg",
        "title": "Game Deal Tracker",
        "area": "backend & data",
        "repo": "jmscripts1.github.io/game-deal-tracker",  # the card links to the live page
        "image": "game-deal-tracker.jpg",
        "crop": (340, 30, 1400, 880),  # the main dashboard panel of the screenshot
        "summary": "Tracks prices across 30+ PC game stores through the CheapShark API, stores "
                   "timestamped snapshots in SQLite, and sends a Discord alert when a watched game "
                   "hits its target price.",
        "facts": [
            ("storage", "5-table SQLite schema"),
            ("dashboard", "Streamlit: deals, price history, stores, watchlist"),
            ("ci", "pytest with mocked API responses, Python 3.10 to 3.14"),
        ],
        "tags": ["Python", "SQL", "SQLite", "pandas", "Streamlit", "pytest"],
    },
]

EXPERIENCE = [
    {
        "role": "IT Support & Systems Co-op",
        "org": "Personal Touch Computers",
        "when": "Sep 2023 to Feb 2024",
        "points": [
            "Service desk and on-site support at an MSP for about 40 small and mid-sized businesses",
            "Imaged and deployed about 100 devices; supported Microsoft 365, endpoint security and backups",
        ],
    },
    {
        "role": "Court Monitor & Guest Services (part-time)",
        "org": "Flying Squirrel Sports",
        "when": "Jun 2023 to Nov 2026",
        "points": [
            "Safety briefings for groups of 30+ and escalations on the spot, 3+ years alongside school",
        ],
    },
]

EDUCATION = {
    "school": "Ontario Tech University",
    "degree": "BSc Computer Science",
    "when": "Expected Apr 2029",
    "coursework": "Programming Workshop I & II (C++), OOP, Computer Architecture, Discrete Mathematics",
}

TOOLBOX = [
    ("Languages", ["Python", "C++", "SQL", "Java", "Bash", "PowerShell"]),
    ("Frameworks", ["FastAPI", "SQLAlchemy", "Streamlit", "pandas", "pytest"]),
    ("Databases", ["PostgreSQL", "SQLite"]),
    ("Infrastructure", ["Docker", "Docker Compose", "Git", "GitHub Actions", "Linux (systemd)", "Windows Server", "Microsoft 365"]),
]

# ------------------------------------------------------------------ STYLE

W = 1200
BG, SURF, TEXT, SOFT, MUTED, LINE, WHITE = "#0A0A0B", "#131315", "#F2F2F2", "#D4D4D8", "#A3A3A8", "#2A2A2E", "#F4F4F5"
SANS = "G,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "GM,ui-monospace,Menlo,Consolas,monospace"


class Font:
    """One variable font: measures text with Pillow and embeds a subset as woff2."""

    def __init__(self, filename):
        tt = TTFont(FONTS / filename)
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        self.ttf = buf.getvalue()
        self._cache = {}

    def measure(self, text, size, weight=400):
        key = (size, weight)
        if key not in self._cache:
            f = ImageFont.truetype(io.BytesIO(self.ttf), size=size)
            f.set_variation_by_axes([weight])
            self._cache[key] = f
        return self._cache[key].getlength(text)

    def embed(self, chars):
        tt = TTFont(io.BytesIO(self.ttf))
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.drop_tables += ["meta"]
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(set(chars))) + " ")
        sub.subset(tt)
        out = io.BytesIO()
        tt.flavor = "woff2"
        tt.save(out)
        return base64.b64encode(out.getvalue()).decode()


SANS_FONT = Font("Geist-Variable.woff2")
MONO_FONT = Font("GeistMono-Variable.woff2")


def wrap(text, size, maxw, weight=400, font=SANS_FONT):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if font.measure(trial, size, weight) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def glint(x, y, s, fill=WHITE, extra=""):
    """Four-point star, the same shape as the glints in the night sky."""
    return (f'<path d="M{x:.1f} {y - s:.1f}Q{x:.1f} {y:.1f} {x + s:.1f} {y:.1f}Q{x:.1f} {y:.1f} {x:.1f} {y + s:.1f}'
            f'Q{x:.1f} {y:.1f} {x - s:.1f} {y:.1f}Q{x:.1f} {y:.1f} {x:.1f} {y - s:.1f}Z" fill="{fill}"{extra}/>')


def image_uri(name, size=None, crop=None, quality=80):
    im = Image.open(SRC / name).convert("L")
    if crop:
        im = im.crop(crop)
    if size:
        im = im.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


class Card:
    """Collects SVG elements and the text they use, then writes a finished file."""

    def __init__(self, height, title, desc):
        self.h, self.title, self.desc = height, title, desc
        self.els, self.css, self.defs = [], [], []
        self.sans_chars, self.mono_chars = set(), set()

    def text(self, x, y, s, size, fill=TEXT, weight=400, mono=False, anchor="start", extra=""):
        (self.mono_chars if mono else self.sans_chars).update(s)
        fam = MONO if mono else SANS
        self.els.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(s)}</text>'
        )

    def label(self, x, y, s):
        """Section heading inside a card: a glint and a lowercase title."""
        self.els.append(glint(x + 8, y - 8, 9))
        self.text(x + 26, y, s, 24, TEXT, 600, extra=' letter-spacing="-.6"')

    def rich(self, x, y, s, size, maxw, lh, fill=MUTED, bold_fill=TEXT, measure_only=False):
        """Wrapped paragraph where **words** are bold. Returns the y after the last line."""
        words = []
        for i, part in enumerate(s.split("**")):
            words += [(w, i % 2 == 1) for w in part.split()]
        space = SANS_FONT.measure(" ", size)
        lines, cur, curw = [], [], 0.0
        for w, b in words:
            ww = SANS_FONT.measure(w, size, 600 if b else 400)
            if cur and curw + space + ww > maxw:
                lines.append(cur)
                cur, curw = [], 0.0
            curw += (space if cur else 0) + ww
            cur.append((w, b))
        if cur:
            lines.append(cur)
        if not measure_only:
            for ln in lines:
                spans = []
                for j, (w, b) in enumerate(ln):
                    self.sans_chars.update(w + " ")
                    t = escape(w) + (" " if j < len(ln) - 1 else "")
                    spans.append(f'<tspan font-weight="600" fill="{bold_fill}">{t}</tspan>' if b else t)
                self.els.append(
                    f'<text x="{x:.1f}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" fill="{fill}" '
                    f'xml:space="preserve">{"".join(spans)}</text>'
                )
                y += lh
        else:
            y += lh * len(lines)
        return y

    def chips(self, x, y, tags, maxw, size=13):
        """Outline pills that wrap onto new rows. Returns the y below the last row."""
        cx, cy, h, gap = x, y, 30, 8
        for t in tags:
            w = MONO_FONT.measure(t, size, 450) + 26
            if cx + w > x + maxw and cx > x:
                cx, cy = x, cy + h + gap
            self.els.append(f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{SURF}" stroke="{LINE}"/>')
            self.text(cx + w / 2, cy + h / 2 + size * 0.36, t, size, SOFT, 450, mono=True, anchor="middle")
            cx += w + gap
        return cy + h

    def write(self, name):
        font_css = (
            "@font-face{font-family:G;src:url(data:font/woff2;base64,%s) format('woff2');font-weight:100 900}"
            "@font-face{font-family:GM;src:url(data:font/woff2;base64,%s) format('woff2');font-weight:100 900}"
            % (SANS_FONT.embed(self.sans_chars), MONO_FONT.embed(self.mono_chars))
        )
        motion = "@media (prefers-reduced-motion:reduce){.tw{animation:none!important}.m{display:none}}"
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" width="{W}" height="{self.h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>'
            f'<defs><style>{font_css}{"".join(self.css)}{motion}</style>'
            f'<clipPath id="card"><rect width="{W}" height="{self.h}" rx="20"/></clipPath>{"".join(self.defs)}</defs>'
            f'<g clip-path="url(#card)"><rect width="{W}" height="{self.h}" fill="{BG}"/>{"".join(self.els)}</g>'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{self.h - 1}" rx="19.5" fill="none" stroke="#FFFFFF" stroke-opacity=".08"/>'
            "</svg>"
        )
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"{name}: {len(svg) // 1024} KB")


# ------------------------------------------------------------------ SKY


def sky(card, rng, density=1.0, meteors=2, top=None, glints=True, dim=1.0):
    """Twinkling stars, a few four-point glints, and shooting stars on a loop."""
    h = top or card.h
    card.defs.append(
        '<linearGradient id="tail" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#FFFFFF" stop-opacity=".95"/>'
        '<stop offset=".25" stop-color="#E4E4E7" stop-opacity=".4"/>'
        '<stop offset="1" stop-color="#E4E4E7" stop-opacity="0"/></linearGradient>'
    )
    card.css.append(
        "@keyframes tw{from{opacity:var(--a)}to{opacity:calc(var(--a)*.25)}}"
        ".tw{animation:tw ease-in-out infinite alternate}"
    )
    n = int(W * h / 2600 * density)
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, h)
        z = rng.random() ** 2.2  # most stars far and faint
        r = 0.45 + z * 1.25
        a = (0.25 + z * 0.65) * dim
        if rng.random() < 0.45:
            card.els.append(
                f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{WHITE}" '
                f'style="--a:{a:.2f};opacity:{a:.2f};animation-duration:{rng.uniform(2.5, 6):.1f}s;animation-delay:-{rng.uniform(0, 6):.1f}s"/>'
            )
        else:
            card.els.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{WHITE}" opacity="{a:.2f}"/>')
    for _ in range(max(2, int(5 * density)) if glints else 0):
        x, y, s = rng.uniform(40, W - 40), rng.uniform(20, h - 20), rng.uniform(5, 9)
        card.els.append(glint(x, y, s, extra=(
            f' class="tw" style="--a:.85;opacity:.85;animation-duration:{rng.uniform(3, 5):.1f}s;'
            f'animation-delay:-{rng.uniform(0, 4):.1f}s"')))
    # Shooting stars: each crosses in about a second, then waits for the rest of its cycle.
    for i in range(meteors):
        dur = rng.uniform(7, 11)
        sx, sy = rng.uniform(W * 0.35, W * 1.05), rng.uniform(-20, h * 0.35)
        dist = rng.uniform(360, 520)
        ang = rng.uniform(148, 160)  # degrees: down and to the left
        import math
        dx, dy = math.cos(math.radians(ang)) * dist, math.sin(math.radians(ang)) * dist
        travel = 1.1 / dur * 100
        card.css.append(
            f"@keyframes m{i}{{0%{{transform:translate({sx:.0f}px,{sy:.0f}px);opacity:0}}"
            f"{travel * 0.15:.1f}%{{opacity:1}}"
            f"{travel:.1f}%{{transform:translate({sx + dx:.0f}px,{sy + dy:.0f}px);opacity:0}}"
            f"100%{{transform:translate({sx + dx:.0f}px,{sy + dy:.0f}px);opacity:0}}}}"
            f".m{i}{{animation:m{i} {dur:.1f}s linear {rng.uniform(0.5, 6):.1f}s infinite;opacity:0}}"
        )
        length = rng.uniform(130, 200)
        card.els.append(
            f'<g class="m m{i}"><g transform="rotate({ang - 180:.1f})">'
            f'<rect x="0" y="-.8" width="{length:.0f}" height="1.6" rx=".8" fill="url(#tail)"/>'
            f'<circle r="2.2" fill="#FFFFFF"/></g></g>'
        )


# ------------------------------------------------------------------ CARDS


def banner():
    c = Card(400, NAME, f"{NAME}. {TAGLINE} {INTRO} A black and white night sky with twinkling and shooting stars.")
    c.defs.append(
        '<radialGradient id="glow" cx="80%" cy="20%" r="60%"><stop offset="0" stop-color="#FFFFFF" stop-opacity=".07"/>'
        '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>'
        '<clipPath id="av"><rect width="300" height="300" rx="18"/></clipPath>'
    )
    c.els.append(f'<rect width="{W}" height="400" fill="url(#glow)"/>')
    sky(c, random.Random(7), density=1.0, meteors=3)
    c.text(64, 168, NAME, 70, TEXT, 600, extra=' letter-spacing="-2.4"')
    c.text(64, 222, TAGLINE, 34, MUTED, 500, extra=' letter-spacing="-1"')
    c.text(64, 276, INTRO, 19, SOFT, 400)
    c.text(64, 344, SITE, 15, MUTED, 450, mono=True)
    c.els.append(
        f'<g transform="translate(840 50) rotate(-2 150 150)">'
        f'<g clip-path="url(#av)"><image href="{image_uri("avatar.jpg", (420, 420), quality=82)}" width="300" height="300" preserveAspectRatio="xMidYMid slice"/></g>'
        f'<rect x=".5" y=".5" width="299" height="299" rx="17.5" fill="none" stroke="#FFFFFF" stroke-opacity=".12"/></g>'
    )
    c.write("banner.svg")


def about():
    lx, lw = 48, 720
    rx, rw = 840, W - 840 - 48
    probe = Card(10, "", "")
    ly = 64 + 46
    for para in ABOUT:
        ly = probe.rich(lx, ly, para, 18, lw, 29, measure_only=True) + 14
    ry = 64 + 46 + 26
    for item in RIGHT_NOW:
        ry = probe.rich(rx + 22, ry, item, 16, rw - 22, 25, measure_only=True) + 12
    h = max(ly, ry) + 30
    plain = lambda t: t.replace("**", "")
    c = Card(int(h), "hi, i'm josh", " ".join(plain(t) for t in ABOUT) + " Right now: " + "; ".join(plain(t) for t in RIGHT_NOW))
    sky(c, random.Random(5), density=0.3, meteors=1, glints=False, dim=0.5)
    c.label(lx, 64, "hi, i'm josh")
    y = 64 + 46
    for para in ABOUT:
        y = c.rich(lx, y, para, 18, lw, 29, fill=SOFT) + 14
    c.els.append(f'<rect x="{rx - 32}" y="{64 + 46 - 18}" width="1" height="{ry - 64 - 46:.0f}" fill="{LINE}"/>')
    y = 64 + 46
    c.text(rx, y, "right now", 13, MUTED, 450, mono=True)
    y += 26
    for item in RIGHT_NOW:
        c.els.append(glint(rx + 6, y - 5, 5, fill=SOFT))
        y = c.rich(rx + 22, y, item, 16, rw - 22, 25, fill=MUTED) + 12
    c.write("about.svg")


def head(c, p, x, y, maxw):
    """Title, area and status, and the repo path on the right. Returns the next y."""
    c.text(x, y, p["title"], 34, TEXT, 600, extra=' letter-spacing="-1"')
    y += 30
    c.text(x, y, p["area"], 13, MUTED, 450, mono=True)
    c.text(x + maxw, y, p["repo"], 13, MUTED, 450, mono=True, anchor="end")
    if p.get("status"):
        sx = x + MONO_FONT.measure(p["area"], 13, 450) + 12
        w = MONO_FONT.measure(p["status"], 12, 500) + 18
        c.els.append(f'<rect x="{sx:.1f}" y="{y - 14:.1f}" width="{w:.1f}" height="20" rx="10" fill="{WHITE}"/>')
        c.text(sx + w / 2, y, p["status"], 12, BG, 500, mono=True, anchor="middle")
    return y + 36


def opswatch(p):
    x, maxw = 48, W - 96
    lines = wrap(p["summary"], 17, 820)
    colw = (maxw - 3 * 24) / 4
    step_lines = [wrap(t, 14.5, colw) for _, t in p["steps"]]
    rows = max(len(s) for s in step_lines)
    h = 48 + 40 + 66 + len(lines) * 27 + 28 + 26 + rows * 21 + 30 + 30 + 48 + 56
    c = Card(int(h), p["title"], p["summary"])
    sky(c, random.Random(11), density=0.3, meteors=1, glints=False, dim=0.5)
    c.label(x, 64, "projects")
    y = head(c, p, x, 88 + 56, maxw)
    for ln in lines:
        c.text(x, y, ln, 17, MUTED)
        y += 27
    y += 20
    for i, ((title, _), sl) in enumerate(zip(p["steps"], step_lines)):
        cx = x + i * (colw + 24)
        c.els.append(f'<rect x="{cx:.1f}" y="{y:.1f}" width="{colw:.1f}" height="1.5" fill="{WHITE if i == 0 else LINE}"/>')
        c.text(cx, y + 30, title, 15.5, TEXT, 600)
        for j, ln in enumerate(sl):
            c.text(cx, y + 54 + j * 21, ln, 14.5, MUTED)
    y += 54 + rows * 21 + 14
    c.chips(x, y, p["tags"], maxw)
    c.write(p["file"])


def tracker(p):
    imgw = 520
    x, maxw = imgw + 48, W - imgw - 96
    lines = wrap(p["summary"], 17, maxw)
    fact_lines = [wrap(v, 16, maxw) for _, v in p["facts"]]
    h = 48 + 40 + 66 + len(lines) * 27 + 12 + sum(22 + len(f) * 23 + 12 for f in fact_lines) + 74 + 48
    h = max(h, 400)
    c = Card(int(h), p["title"], p["summary"] + " Facts: " + "; ".join(f"{k}: {v}" for k, v in p["facts"]))
    # Screenshot of the tracker's page, cropped to the left half so its headline stays in frame.
    # Fit the chosen crop to the image column (cover), anchored top-left.
    l, t, r, b = p["crop"]
    cw, ch = r - l, b - t
    if cw / ch > imgw / h:
        r = l + int(ch * imgw / h)
    else:
        b = t + int(cw * h / imgw)
    uri = image_uri(p["image"], (int(imgw * 1.5), int(h * 1.5)), crop=(l, t, r, b), quality=78)
    c.els.append(f'<image href="{uri}" width="{imgw}" height="{h:.0f}" preserveAspectRatio="none" opacity=".9"/>')
    c.defs.append(
        '<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset=".7" stop-color="#0A0A0B" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#0A0A0B"/></linearGradient>'
    )
    c.els.append(f'<rect width="{imgw}" height="{h:.0f}" fill="url(#fade)"/>')
    sky(c, random.Random(19), density=0.2, meteors=0, glints=False, dim=0.5)
    y = head(c, p, x, 88, maxw)
    for ln in lines:
        c.text(x, y, ln, 17, MUTED)
        y += 27
    y += 12
    for (k, _), fl in zip(p["facts"], fact_lines):
        c.text(x, y, k, 13, MUTED, 450, mono=True)
        y += 23
        for ln in fl:
            c.text(x, y, ln, 16, TEXT, 500)
            y += 23
        y += 12
    c.chips(x, y + 4, p["tags"], maxw)
    c.write(p["file"])


def resume():
    leftx, leftw = 48, 640
    rightx, rightw = 760, W - 760 - 48
    # measure the experience column
    blocks = []
    for e in EXPERIENCE:
        pts = [wrap(pt, 15, leftw - 40) for pt in e["points"]]
        blocks.append((e, pts, 26 + 24 + sum(len(p) * 22 + 6 for p in pts) + 22))
    course = wrap(EDUCATION["coursework"], 15, rightw - 24)
    h = max(48 + 30 + sum(b[2] for b in blocks), 48 + 30 + 26 + 24 + 24 + 30 + len(course) * 22) + 48 + 56
    c = Card(int(h), "Résumé", "Experience: " + "; ".join(f"{e['role']}, {e['org']}, {e['when']}" for e in EXPERIENCE)
             + f". Education: {EDUCATION['school']}, {EDUCATION['degree']}, {EDUCATION['when']}.")
    sky(c, random.Random(23), density=0.3, meteors=1, glints=False, dim=0.5)
    c.label(leftx, 64, "résumé")
    y = 64 + 56
    c.text(leftx, y, "experience", 13, MUTED, 450, mono=True)
    y += 30
    for i, (e, pts, bh) in enumerate(blocks):
        c.els.append(f'<rect x="{leftx}" y="{y - 18}" width="1.5" height="{bh - 18}" fill="{WHITE if i == 0 else LINE}"/>')
        ix = leftx + 22
        c.text(ix, y, e["role"], 18, TEXT, 600)
        c.text(ix, y + 24, f"{e['org']}, {e['when']}", 13, MUTED, 450, mono=True)
        py = y + 50
        for p in pts:
            for j, ln in enumerate(p):
                c.text(ix + (14 if j else 0), py, ("- " if j == 0 else "") + ln, 15, SOFT)
                py += 22
            py += 6
        y += bh
    y = 64 + 56
    c.text(rightx, y, "education", 13, MUTED, 450, mono=True)
    y += 30
    top = y - 18
    ix = rightx + 22
    c.text(ix, y, EDUCATION["school"], 18, TEXT, 600)
    c.text(ix, y + 24, f"{EDUCATION['degree']}, {EDUCATION['when']}", 13, MUTED, 450, mono=True)
    y += 60
    c.text(ix, y, "coursework", 13, MUTED, 450, mono=True)
    y += 24
    for ln in course:
        c.text(ix, y, ln, 15, SOFT)
        y += 22
    c.els.append(f'<rect x="{rightx}" y="{top}" width="1.5" height="{y - 22 + 10 - top:.0f}" fill="{WHITE}"/>')
    c.write("resume.svg")


def toolbox():
    labelw, x0 = 210, 48
    maxw = W - 96 - labelw
    # lay out once to find the height
    probe = Card(10, "", "")
    y = 56 + 52
    rows = []
    for label, tags in TOOLBOX:
        end = probe.chips(x0 + labelw, y, tags, maxw)
        rows.append((label, y))
        y = end + 18
    h = y - 18 + 48
    c = Card(int(h), "Toolbox", "; ".join(f"{l}: {', '.join(t)}" for l, t in TOOLBOX))
    sky(c, random.Random(31), density=0.3, meteors=0, glints=False, dim=0.5)
    c.label(x0, 64, "toolbox")
    for (label, ry), (_, tags) in zip(rows, TOOLBOX):
        c.text(x0, ry + 20, label, 15.5, MUTED, 500)
        c.chips(x0 + labelw, ry, tags, maxw)
    c.write("toolbox.svg")


def footer():
    c = Card(180, "Thanks for stopping by", "Thanks for stopping by. A strip of night sky with a shooting star.")
    c.els.append(f'<image href="{image_uri("star-band.jpg", (1200, 395), quality=72)}" x="420" y="-20" width="780" height="220" '
                 'preserveAspectRatio="xMidYMid slice" opacity=".55"/>')
    c.defs.append(
        '<linearGradient id="ff" x1="0" y1="0" x2="1" y2="0"><stop offset=".3" stop-color="#0A0A0B"/>'
        '<stop offset=".75" stop-color="#0A0A0B" stop-opacity="0"/></linearGradient>'
    )
    c.els.append(f'<rect width="{W}" height="180" fill="url(#ff)"/>')
    sky(c, random.Random(43), density=0.5, meteors=1)
    c.text(48, 92, "thanks for stopping by", 30, TEXT, 500, extra=' letter-spacing="-.8"')
    c.text(48, 126, SITE, 14, MUTED, 450, mono=True)
    c.write("footer.svg")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    banner()
    about()
    opswatch(PROJECTS[0])
    tracker(PROJECTS[1])
    resume()
    toolbox()
    footer()
