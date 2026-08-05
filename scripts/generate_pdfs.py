"""Generate short and long CV PDFs from the real Markdown content in docs/.

Usage: uv run --extra pdf python scripts/generate_pdfs.py
"""

import re
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "assets"

MD_EXTENSIONS = [
    "abbr",
    "admonition",
    "attr_list",
    "def_list",
    "footnotes",
    "tables",
    "sane_lists",
    "pymdownx.betterem",
    "pymdownx.caret",
    "pymdownx.details",
    "pymdownx.mark",
    "pymdownx.smartsymbols",
    "pymdownx.superfences",
    "pymdownx.tabbed",
    "pymdownx.tilde",
]
MD_EXTENSION_CONFIGS = {
    "pymdownx.tabbed": {"alternate_style": True},
}

EMOJI_SHORTCODE_RE = re.compile(r"\s*:[a-z_]+:")
INTERNAL_LINK_RE = re.compile(r'<a\s+href="([^"]+)"([^>]*)>(.*?)</a>', re.DOTALL)
HEADING_IMG_RE = re.compile(
    r'^!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)(?:\{[^}]*\})?\s*(?P<title>.*)$'
)
H2_RE = re.compile(r"(?m)^## (.+)$")
TAB_BLOCK_RE = re.compile(r'(?m)^=== "(?P<title>.*)"\n(?P<body>(?:[ \t].*(?:\n|\Z)|\n)+)')


def strip_emoji_shortcodes(text: str) -> str:
    return EMOJI_SHORTCODE_RE.sub("", text)


def unwrap_internal_links(html: str) -> str:
    def repl(m: re.Match) -> str:
        href, _attrs, inner = m.group(1), m.group(2), m.group(3)
        if href.startswith("http") or href.startswith("mailto:"):
            return m.group(0)
        return inner

    return INTERNAL_LINK_RE.sub(repl, html)


def md_to_html(text: str) -> str:
    text = strip_emoji_shortcodes(text)
    html = markdown.markdown(
        text, extensions=MD_EXTENSIONS, extension_configs=MD_EXTENSION_CONFIGS
    )
    return unwrap_internal_links(html)


def md_inline(text: str) -> str:
    """Render a short markdown fragment (a table cell, a heading) without the
    wrapping <p> block that markdown.markdown() always adds."""
    html = md_to_html(text).strip()
    return re.sub(r"^<p>(.*)</p>$", r"\1", html, flags=re.S)


def read(name: str) -> str:
    return (DOCS / name).read_text()


def section(text: str, start_heading: str, end_heading: str | None = None) -> str:
    """Extract markdown between two headings (exclusive of end_heading)."""
    start = text.index(start_heading)
    if end_heading:
        end = text.index(end_heading, start + len(start_heading))
        return text[start:end]
    return text[start:]


def split_h2_sections(md_text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) pairs at each top-level '## ' heading."""
    matches = list(H2_RE.finditer(md_text))
    out = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        out.append((m.group(1).strip(), md_text[start:end].strip("\n")))
    return out


def parse_heading(heading: str) -> tuple[str, str | None]:
    """Return (title, logo_src) from a heading that may start with an image."""
    m = HEADING_IMG_RE.match(heading.strip())
    if m:
        return m.group("title").strip(), m.group("src")
    return heading.strip(), None


def convert_tabs(body_md: str) -> str:
    """Replace pymdownx.tabbed '=== "title"' blocks (used for sub-roles within a
    company) with a title directly followed by its own content, so the two stay
    paired — the tabbed extension's HTML groups all labels before all content,
    which reads as mismatched once flattened for print."""

    def repl(m: re.Match) -> str:
        title_html = md_inline(m.group("title"))
        lines = m.group("body").splitlines()
        dedented = [re.sub(r"^[ \t]{1,4}", "", l) for l in lines]
        content_html = md_to_html("\n".join(dedented).strip("\n"))
        return f'<div class="sub-role"><h4>{title_html}</h4>{content_html}</div>'

    return TAB_BLOCK_RE.sub(repl, body_md)


def parse_md_table(block: str) -> list[list[str]]:
    """Parse a markdown table (heading/intro text may precede it) into data rows,
    dropping the header and separator rows."""
    lines = [l for l in block.splitlines() if l.strip().startswith("|")]
    if len(lines) < 3:
        return []
    rows = []
    for line in lines[2:]:
        rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def parse_testimonials(md_text: str) -> list[tuple[str, str, str]]:
    block = section(md_text, "## What people say", "See [Experience]")
    block = block[block.index("\n> "):]
    out = []
    for chunk in block.split("<!-- -->"):
        lines = [l[1:].strip() for l in chunk.strip().splitlines() if l.strip()]
        if not lines:
            continue
        *quote_lines, attribution = lines
        quote = " ".join(quote_lines).strip()
        m = re.match(r"—\s*\*\*(.+?)\*\*,\s*(.+)", attribution)
        name, role = (m.group(1), m.group(2)) if m else (attribution, "")
        out.append((quote, name, role))
    return out


# ---------------------------------------------------------------------------
# Small inline icon set (Feather-style strokes) for the contact row.
# ---------------------------------------------------------------------------

def icon(paths: str) -> str:
    return (
        '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        f"{paths}</svg>"
    )


def icon_filled(paths: str) -> str:
    return f'<svg class="ic" viewBox="0 0 24 24" fill="currentColor">{paths}</svg>'


ICON_MAIL = icon(
    '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>'
    '<polyline points="22,6 12,13 2,6"/>'
)
ICON_LINKEDIN = icon_filled(
    '<path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.03-1.85-3.03-1.85 0-2.14 1.45-2.14 2.94v5.66H9.34V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.38-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.07 2.07 0 1 1 0-4.14 2.07 2.07 0 0 1 0 4.14zM7.12 20.45H3.56V9h3.56v11.45z"/>'
)
ICON_PIN = icon(
    '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>'
)


# ---------------------------------------------------------------------------
# Design system — navy header, blue accent (matches the site's blue theme),
# warm gold used sparingly for sub-role markers and quote accents.
# ---------------------------------------------------------------------------

PRINT_CSS = """
@page {
    size: A4;
    margin: 2.0cm 2cm 1.7cm 2cm;
    @bottom-center {
        content: "Gareth Thomas  ·  " counter(page) " / " counter(pages);
        font-family: "Avenir Next", "Avenir", "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 7.6pt;
        letter-spacing: 0.06em;
        color: #93a1b0;
    }
    @top-right {
        content: string(doc-section);
        font-family: "Avenir Next", "Avenir", "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 7.6pt;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #93a1b0;
    }
}
@page :first {
    margin-top: 0cm;
}
@page :first {
    @top-right { content: none; }
}

* { box-sizing: border-box; }

body {
    font-family: "Avenir Next", "Avenir", "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 9.6pt;
    line-height: 1.48;
    color: #1b1f24;
    font-weight: 400;
}

h1, h2, h3 { font-weight: 700; color: #0d2038; }

a { color: #1a5fb4; text-decoration: none; }

p { margin: 0.32em 0; }
ul, ol { margin: 0.25em 0; padding-left: 1.15em; }
li { margin: 0.12em 0; }

hr { border: none; border-top: 0.5pt solid #dde5ee; margin: 1em 0; }

/* ---------- Header banner ---------- */
.cv-header {
    background: #0d2038;
    color: #ffffff;
    margin: 0 -2cm 1.1em -2cm;
    padding: 0.95cm 2cm 0.7cm 2cm;
}
.cv-header .name {
    font-size: 25pt;
    font-weight: 800;
    letter-spacing: -0.01em;
    margin: 0;
    color: #ffffff;
}
.cv-header .tagline {
    font-size: 10.8pt;
    font-weight: 400;
    color: #c3d3e6;
    margin: 0.24em 0 0.55em 0;
}
.cv-header .contact {
    font-size: 8.6pt;
    letter-spacing: 0.02em;
    color: #dbe6f2;
    display: flex;
    flex-wrap: wrap;
    gap: 0.4em 1.3em;
}
.cv-header .contact span { display: inline-flex; align-items: center; gap: 5pt; white-space: nowrap; }
.cv-header .contact a { color: #dbe6f2; }
.ic { width: 10.5pt; height: 10.5pt; flex: none; color: #8fb3de; }

/* ---------- Section kickers ---------- */
h2.kicker {
    font-size: 8.6pt;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #1a5fb4;
    border-bottom: 1pt solid #c9d8ea;
    padding-bottom: 4pt;
    margin: 1.5em 0 0.65em 0;
    page-break-after: avoid;
    string-set: doc-section content();
}
h2.kicker:first-of-type { margin-top: 0; }

h3 { font-size: 10.6pt; margin: 0 0 0.15em 0; page-break-after: avoid; color: #0d2038; }

/* ---------- Stat strip ---------- */
.stats { display: flex; gap: 10pt; margin: 0 0 0.3em 0; }
.stat-card {
    flex: 1;
    background: #eaf2fb;
    border-top: 2pt solid #1a5fb4;
    padding: 8pt 9pt 7pt 9pt;
}
.stat-card .num { font-size: 16.5pt; font-weight: 800; color: #0d2038; line-height: 1; }
.stat-card .cap { font-size: 7.6pt; color: #4a5666; margin-top: 3pt; line-height: 1.25; }

.meta-line { font-size: 9pt; color: #4a5666; margin: 0.5em 0 0.9em 0; }
.meta-line strong { color: #1b1f24; }
.meta-line .sep { color: #b9c4d1; margin: 0 0.55em; }

/* ---------- Timeline (experience) ---------- */
.timeline { margin-top: 0.2em; }
.tl-item {
    position: relative;
    border-left: 1.6pt solid #c9d8ea;
    padding: 0 0 0.7em 15pt;
    margin-left: 3pt;
}
.tl-item:last-child { padding-bottom: 0; }
.tl-item .tl-dot {
    position: absolute;
    left: -4.6pt;
    top: 2pt;
    width: 7.2pt;
    height: 7.2pt;
    border-radius: 50%;
    background: #1a5fb4;
    border: 1.5pt solid #ffffff;
    outline: 1pt solid #c9d8ea;
}
.tl-head { display: flex; align-items: center; gap: 7pt; margin-bottom: 1pt; page-break-after: avoid; }
.tl-head img { height: 15pt; width: auto; }
.tl-head h3 { margin: 0; }
.tl-item .role-line { font-size: 9.3pt; color: #3d4a58; margin: 0 0 0.3em 0; }
.tl-item .role-line strong { color: #1b1f24; }
.tl-item p { font-size: 9.3pt; }
.tl-item ul { font-size: 9.3pt; }

/* Sub-roles within a company (from '=== "title"' tab blocks). */
.sub-role { margin: 0.6em 0 0.2em 8pt; padding-left: 8pt; border-left: 2pt solid #cf9f42; }
.sub-role h4 { margin: 0 0 0.15em 0; font-size: 9.4pt; font-weight: 700; color: #0d2038; }
.sub-role img { height: 13pt; width: auto; vertical-align: middle; margin-right: 6pt; }
.sub-role p, .sub-role ul { font-size: 9.3pt; }

/* ---------- Skills ---------- */
.skill-group { margin-bottom: 0.2em; }
.skill-row {
    display: flex;
    gap: 10pt;
    padding: 4.5pt 0;
    border-bottom: 0.5pt solid #e6ebf1;
    align-items: baseline;
}
.skill-row:last-child { border-bottom: none; }
.skill-name { flex: 0 0 28%; font-weight: 700; font-size: 9.1pt; color: #0d2038; }
.skill-dots { flex: 0 0 34pt; font-size: 8pt; letter-spacing: 1.5pt; white-space: nowrap; }
.skill-dots .on { color: #1a5fb4; }
.skill-dots .off { color: #d3dce6; }
.skill-evidence { flex: 1; font-size: 8.5pt; color: #4a5666; }

/* Compact chip list for short-CV top skills / certifications */
.chips { display: flex; flex-wrap: wrap; gap: 5pt; }
.chip {
    display: inline-flex;
    align-items: center;
    gap: 4pt;
    background: #eaf2fb;
    color: #133a63;
    border: 0.5pt solid #c9d8ea;
    border-radius: 3pt;
    padding: 2.5pt 7pt;
    font-size: 8pt;
    font-weight: 600;
}
.chip img { height: 9pt; width: auto; }
.chip .date { color: #6c7887; font-weight: 400; }

/* ---------- Education cards ---------- */
.edu-card { margin-bottom: 0.6em; }
.edu-head { display: flex; align-items: center; gap: 7pt; }
.edu-head img { height: 15pt; width: auto; }
.edu-head h3 { margin: 0; }
.edu-card .role-line { font-size: 9.3pt; color: #3d4a58; margin: 1pt 0 0.35em 0; }
.edu-card p, .edu-card ul { font-size: 9.3pt; }

.cert-block { margin-top: 0.55em; }
.cert-block .cert-title { font-weight: 700; font-size: 8.9pt; color: #0d2038; margin-bottom: 4pt; }
.course-cols { display: flex; flex-wrap: wrap; gap: 0 16pt; font-size: 8.3pt; color: #3d4a58; }
.course-cols .course-cat-block { flex: 0 0 47%; margin: 0.35em 0; }
.course-cols .course-cat { font-weight: 700; color: #0d2038; font-size: 8.6pt; margin: 0 0 0.15em 0; }
.course-cols .course-line { margin: 0.1em 0; }
.course-cols .course-line .date { color: #8b96a3; }

/* ---------- Testimonials ---------- */
.quotes { display: flex; flex-wrap: wrap; gap: 10pt; margin-top: 0.2em; }
.quote-card {
    flex: 1 1 45%;
    background: #f6f8fb;
    border-left: 2.5pt solid #cf9f42;
    padding: 8pt 10pt;
    font-size: 8.7pt;
    color: #2c3644;
}
.quote-card .q { font-style: italic; }
.quote-card .attr { margin-top: 5pt; font-size: 8pt; color: #5b6673; font-style: normal; }
.quote-card .attr strong { color: #1b1f24; }

/* ---------- About ---------- */
.about p { font-size: 9.6pt; }
"""


def wrap(title: str, body_html: str, extra_css: str = "") -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>{PRINT_CSS}{extra_css}</style>
</head><body>{body_html}</body></html>"""


def header_html() -> str:
    return f"""
<div class="cv-header">
<div class="name">Gareth Thomas</div>
<div class="tagline">Consultant, technologist &amp; founder — Eindhoven, Netherlands</div>
<div class="contact">
<span>{ICON_MAIL}<a href="mailto:gareth.bj.thomas@gmail.com">gareth.bj.thomas@gmail.com</a></span>
<span>{ICON_LINKEDIN}<a href="https://nl.linkedin.com/in/g-thomas">linkedin.com/in/g-thomas</a></span>
<span>{ICON_PIN}Eindhoven, Netherlands</span>
</div>
</div>
"""


def kicker(text: str) -> str:
    return f'<h2 class="kicker">{text}</h2>'


def stats_html(index_md: str) -> str:
    block = section(index_md, "## By the numbers", "## About")
    lines = [l for l in block.splitlines() if l.strip().startswith("|")]
    numbers = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    captions = [c.strip() for c in lines[2].strip().strip("|").split("|")]
    cards = "".join(
        f'<div class="stat-card"><div class="num">{n}</div><div class="cap">{c}</div></div>'
        for n, c in zip(numbers, captions)
    )
    return f'<div class="stats">{cards}</div>'


def at_a_glance_meta(index_md: str) -> str:
    block = section(index_md, "## At a glance", "## By the numbers")
    rows = parse_md_table(block)
    parts = []
    for label, value in rows:
        label = label.strip("*")
        parts.append(f"<strong>{label}:</strong> {md_inline(value)}")
    return f'<div class="meta-line">{"<span class=\"sep\">·</span>".join(parts)}</div>'


def experience_timeline_html(experience_md: str) -> str:
    body_md = experience_md.split("\n", 2)[-1]
    intro_md, rest_md = body_md.split("\n\n", 1)
    items = []
    for heading, body in split_h2_sections(rest_md):
        title, logo = parse_heading(heading)
        logo_html = f'<img src="{logo}" alt="">' if logo else ""
        items.append(
            f'<div class="tl-item"><div class="tl-dot"></div>'
            f'<div class="tl-head">{logo_html}<h3>{title}</h3></div>'
            f"{md_to_html(convert_tabs(body))}</div>"
        )
    return (
        f'<div class="about"><p>{md_inline(intro_md)}</p></div>'
        f'<div class="timeline">{"".join(items)}</div>'
    )


def skills_group_html(skills_md: str, start: str, end: str | None) -> str:
    block = section(skills_md, start, end)
    rows = parse_md_table(block)
    out = []
    for name, rating, evidence in rows:
        n = rating.count("★")
        dots = "".join(
            f'<span class="{"on" if i < n else "off"}">●</span>' for i in range(4)
        )
        out.append(
            '<div class="skill-row">'
            f'<div class="skill-name">{md_inline(name)}</div>'
            f'<div class="skill-dots">{dots}</div>'
            f'<div class="skill-evidence">{md_inline(evidence)}</div>'
            "</div>"
        )
    return f'<div class="skill-group">{"".join(out)}</div>'


def cert_chips_html(
    edu_md: str, heading: str, next_heading: str, logo: str | None = None
) -> str:
    block = section(edu_md, heading, next_heading)
    rows = parse_md_table(block)
    chips = []
    for name, date in rows:
        logo_html = f'<img src="{logo}" alt="">' if logo else ""
        chips.append(
            f'<span class="chip">{logo_html}{md_inline(name)} <span class="date">{date}</span></span>'
        )
    return f'<div class="chips">{"".join(chips)}</div>'


def courses_html(edu_md: str) -> str:
    block = section(edu_md, "## LinkedIn Learning Courses", "## Earlier Education")
    cats = re.split(r"(?m)^\*\*(.+?)\*\*\s*$", block)
    # cats[0] is intro text, then alternating (category, body)
    out = ['<div class="course-cols">']
    for i in range(1, len(cats), 2):
        cat_name = cats[i]
        cat_body = cats[i + 1]
        rows = parse_md_table(cat_body)
        out.append(f'<div class="course-cat-block"><div class="course-cat">{cat_name}</div>')
        for course, date in rows:
            out.append(
                f'<div class="course-line">{md_inline(course)} <span class="date">— {date}</span></div>'
            )
        out.append("</div>")
    out.append("</div>")
    return "".join(out)


def earlier_education_html(edu_md: str) -> str:
    block = section(edu_md, "## Earlier Education")
    body = block.split("\n", 1)[1] if "\n" in block else ""
    return md_to_html(body)


def testimonials_html(index_md: str) -> str:
    cards = []
    for quote, name, role in parse_testimonials(index_md):
        cards.append(
            '<div class="quote-card">'
            f"<div class=\"q\">&ldquo;{md_inline(quote)}&rdquo;</div>"
            f'<div class="attr"><strong>{name}</strong> — {role}</div>'
            "</div>"
        )
    return f'<div class="quotes">{"".join(cards)}</div>'


# ---------------------------------------------------------------------------
# Long CV
# ---------------------------------------------------------------------------

def build_long_pdf() -> str:
    index_md = read("index.md")
    experience_md = read("experience.md")
    skills_md = read("skills.md")
    education_md = read("education.md")

    about_block = section(index_md, "## About", "## What people say")
    about_para = about_block.split("\n\n", 1)[1] if "\n\n" in about_block else about_block

    ist_block = section(
        education_md, "## ![Instituto", "## LinkedIn Learning Certifications"
    )
    ist_lines = ist_block.splitlines()
    ist_title, ist_logo = parse_heading(ist_lines[0][3:])
    ist_body = "\n".join(ist_lines[1:])

    parts = [
        header_html(),
        stats_html(index_md),
        at_a_glance_meta(index_md),
        kicker("About"),
        f'<div class="about">{md_to_html(about_para)}</div>',
        kicker("Experience"),
        experience_timeline_html(experience_md),
        kicker("Skills — Technical"),
        skills_group_html(skills_md, "## Technical", "## Leadership"),
        kicker("Skills — Leadership, Communication &amp; Delivery"),
        skills_group_html(
            skills_md, "## Leadership, Communication & Delivery", None
        ),
        kicker("Education"),
        '<div class="edu-card">'
        f'<div class="edu-head">{f"<img src=\"{ist_logo}\" alt=\"\">" if ist_logo else ""}<h3>{ist_title}</h3></div>'
        f"{md_to_html(ist_body)}"
        "</div>",
        '<div class="cert-block"><div class="cert-title">Anthropic Academy Certifications</div>'
        + cert_chips_html(
            education_md,
            "## ![Anthropic",
            "## LinkedIn Learning Courses",
            logo="assets/logos/anthropic.png",
        )
        + "</div>",
        '<div class="cert-block"><div class="cert-title">LinkedIn Learning Certifications</div>'
        + cert_chips_html(
            education_md, "## LinkedIn Learning Certifications", "## ![Anthropic"
        )
        + "</div>",
        '<div class="cert-block"><div class="cert-title">LinkedIn Learning Courses (691 completed 2017–2026, selection below)</div>'
        + courses_html(education_md)
        + "</div>",
        '<div class="cert-block"><div class="cert-title">Earlier Education</div>'
        + earlier_education_html(education_md)
        + "</div>",
        kicker("What people say"),
        testimonials_html(index_md),
    ]
    return wrap("Gareth Thomas — CV", "\n".join(parts))


# ---------------------------------------------------------------------------
# Short CV (one page, two columns)
# ---------------------------------------------------------------------------

SHORT_EXTRA_CSS = """
.short-body { display: flex; gap: 22pt; }
.short-sidebar {
    flex: 0 0 33%;
    background: #eaf2fb;
    margin: 0 0 -1.7cm -2cm;
    padding: 0 12pt 1.7cm 2cm;
}
.short-main { flex: 1; padding-top: 1pt; }
.side-block { margin-bottom: 8pt; }
.side-title {
    font-size: 7.6pt; letter-spacing: 0.12em; text-transform: uppercase;
    color: #1a5fb4; font-weight: 700; margin-bottom: 4pt;
    border-bottom: 1pt solid #c9d8ea; padding-bottom: 2.5pt;
}
.side-block p { font-size: 8.3pt; line-height: 1.35; color: #2c3644; margin: 0.15em 0; }
.stat-mini { display: flex; justify-content: space-between; font-size: 8.2pt; line-height: 1.25; padding: 2pt 0; }
.stat-mini .num { font-weight: 800; color: #0d2038; }
.stat-mini .cap { color: #4a5666; text-align: right; }
.lang-row { display: flex; justify-content: space-between; align-items: baseline; font-size: 8.2pt; padding: 1pt 0; }
.lang-row .dots { font-size: 7pt; letter-spacing: 1.2pt; }
.lang-row .on { color: #1a5fb4; }
.lang-row .off { color: #cdd8e4; }
.chips .chip { padding: 2pt 6pt; font-size: 7.5pt; }
.short-main h2.kicker { margin-top: 0.9em; }
.short-main h2.kicker:first-child { margin-top: 0; }
.short-exp-item { margin-bottom: 5.5pt; }
.short-exp-item .role-line { font-size: 8.7pt; margin: 0 0 1pt 0; }
.short-exp-item .role-line strong { color: #0d2038; }
.short-exp-item .dates { color: #6c7887; font-weight: 400; }
.short-exp-item .blurb { font-size: 8.3pt; line-height: 1.35; color: #4a5666; margin: 0; }
.edu-mini { font-size: 8.3pt; line-height: 1.4; color: #2c3644; }
.edu-mini strong { color: #0d2038; }
"""


def build_short_pdf() -> str:
    index_md = read("index.md")
    skills_md = read("skills.md")

    about_para = re.search(r"## About\n\n(.+?)\n\n", index_md, re.S).group(1)
    sentences = about_para.split(". ")
    condensed_about = ". ".join(sentences[:2]).rstrip(".") + "."

    # Hand-transcribed one-liners of the same roles documented in experience.md,
    # condensed for a one-page summary (dates/titles verified against that file).
    roles = [
        (
            "CGI Nederland",
            "Consultant",
            "Jan 2026 – Present",
            "Delivery &amp; consulting in the Eindhoven area, incl. front-end testing for ProRail.",
        ),
        (
            "CGI Nederland",
            "Director Consulting Services",
            "Mar 2025 – Feb 2026",
            "Led a 17-person consulting practice against a &euro;4M+ sales target.",
        ),
        (
            "VersionBay",
            "Co-Founder",
            "Nov 2018 – Mar 2025",
            "Ran the company for 6.5 years; clients included ASML, DNB and ESA.",
        ),
        (
            "Open iT, Inc.",
            "Country Manager Benelux",
            "Jan 2020 – Sep 2021",
            "Ran the Benelux territory alongside VersionBay.",
        ),
        (
            "MathWorks",
            "Application Engineer → Business Development Manager",
            "Jan 2009 – Sep 2018",
            "9.5 years; led MathWorks&rsquo; global Academic strategy.",
        ),
        (
            "Oceanscan",
            "Software Engineer",
            "Jan 2007 – Dec 2008",
            "Sonar GUI to acoustic signal-processing system integration.",
        ),
        (
            "Altran CIS",
            "Consultant",
            "Dec 2005 – Dec 2006",
            "Telecom access-network design, implementation &amp; testing.",
        ),
    ]

    top_skills = re.findall(r"\| ([\w /&().,+-]+?) \| ★★★★ \|", skills_md)[:9]

    languages = [
        ("English", 4),
        ("Portuguese", 3),
        ("Italian", 3),
        ("Dutch", 2),
    ]
    lang_rows = "".join(
        '<div class="lang-row"><span>{}</span><span class="dots">{}</span></div>'.format(
            name,
            "".join(
                f'<span class="{"on" if i < lvl else "off"}">●</span>'
                for i in range(4)
            ),
        )
        for name, lvl in languages
    )

    stat_rows = [
        ("20+", "years in engineering, consulting &amp; entrepreneurship"),
        ("1", "company founded — VersionBay"),
        ("6+", "years chairing PyData Eindhoven"),
        ("4", "languages spoken"),
    ]
    stat_html = "".join(
        f'<div class="stat-mini"><span class="num">{n}</span><span class="cap">{c}</span></div>'
        for n, c in stat_rows
    )

    exp_html = "".join(
        '<div class="short-exp-item">'
        f'<div class="role-line"><strong>{company}</strong> — {role} <span class="dates">({dates})</span></div>'
        f'<p class="blurb">{blurb}</p>'
        "</div>"
        for company, role, dates, blurb in roles
    )

    chips_html = "".join(f'<span class="chip">{s}</span>' for s in top_skills)

    sidebar = f"""
<div class="short-sidebar">
<div class="side-block">
<div class="side-title">Profile</div>
<p>{md_inline(condensed_about)}</p>
</div>
<div class="side-block">
<div class="side-title">At a Glance</div>
{stat_html}
</div>
<div class="side-block">
<div class="side-title">Languages</div>
{lang_rows}
</div>
<div class="side-block">
<div class="side-title">Education</div>
<p class="edu-mini"><strong>Instituto Superior T&eacute;cnico</strong><br>MSc, Control Theory &middot; 2000&ndash;2005<br>Lisbon, Portugal</p>
</div>
<div class="side-block">
<div class="side-title">Top Skills</div>
<div class="chips">{chips_html}</div>
</div>
</div>
"""

    main = f"""
<div class="short-main">
<h2 class="kicker">Experience</h2>
{exp_html}
<h2 class="kicker">Community &amp; Recognition</h2>
<p style="font-size:8.6pt; color:#4a5666;">Chairs PyData Eindhoven (6+ yrs, 1,200+ members) &middot; co-hosts the Inspiring Computing podcast &middot; MATLAB Jokes toolbox featured as a MathWorks Pick of the Week (Oct 2025) &middot; organizes/moderates six technical communities across Eindhoven.</p>
<h2 class="kicker">Certifications</h2>
<p style="font-size:8.6pt; color:#4a5666;"><strong>Anthropic Academy:</strong> Claude Code in Action, Introduction to Agent Skills, Introduction to MCP, Introduction to Subagents (Aug 2026). <strong>LinkedIn Learning:</strong> 12 certifications and 691 courses completed 2017&ndash;2026, spanning AI, DevOps, and leadership.</p>
</div>
"""

    parts = [
        header_html(),
        f'<div class="short-body">{sidebar}{main}</div>',
    ]
    return wrap("Gareth Thomas — CV (Short)", "\n".join(parts), SHORT_EXTRA_CSS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    long_html = build_long_pdf()
    long_path = OUT / "gareth-thomas-cv-long.pdf"
    HTML(string=long_html, base_url=str(DOCS)).write_pdf(str(long_path))
    print(f"Wrote {long_path}")

    short_html = build_short_pdf()
    short_path = OUT / "gareth-thomas-cv-short.pdf"
    HTML(string=short_html, base_url=str(DOCS)).write_pdf(str(short_path))
    print(f"Wrote {short_path}")


if __name__ == "__main__":
    main()
