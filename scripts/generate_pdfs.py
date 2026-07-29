"""Generate short and long CV PDFs from the real Markdown content in docs/.

Usage: uv run --group pdf python scripts/generate_pdfs.py
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


def read(name: str) -> str:
    return (DOCS / name).read_text()


def section(text: str, start_heading: str, end_heading: str | None = None) -> str:
    """Extract markdown between two headings (exclusive of end_heading)."""
    start = text.index(start_heading)
    if end_heading:
        end = text.index(end_heading, start + len(start_heading))
        return text[start:end]
    return text[start:]


PRINT_CSS = """
@page {
    size: A4;
    margin: 1.8cm 2cm;
    @bottom-center {
        content: "Gareth Thomas — CV  ·  " counter(page) " / " counter(pages);
        font-size: 8pt;
        color: #888;
    }
}
body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 10.2pt;
    line-height: 1.45;
    color: #1a1a1a;
}
h1 { font-size: 22pt; margin-bottom: 0.1em; }
h2 { font-size: 14pt; margin-top: 1.3em; margin-bottom: 0.4em; border-bottom: 1.5pt solid #2e7d32; padding-bottom: 0.15em; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin-top: 0.9em; margin-bottom: 0.2em; page-break-after: avoid; }
h1 img, h2 img, h3 img {
    height: 20pt; width: auto; vertical-align: middle; margin-right: 8pt;
}
p { margin: 0.35em 0; }
a { color: #2e7d32; text-decoration: none; }
ul, ol { margin: 0.3em 0; padding-left: 1.3em; }
li { margin: 0.15em 0; }
table { border-collapse: collapse; width: 100%; margin: 0.5em 0 1em 0; font-size: 9.3pt; }
th, td { border: 0.5pt solid #ccc; padding: 3pt 6pt; text-align: left; vertical-align: top; }
th { background: #f0f4f0; }
blockquote { border-left: 3pt solid #2e7d32; margin: 0.6em 0; padding: 0.1em 1em; color: #333; font-style: italic; }
blockquote p { margin: 0.3em 0; }
.header { margin-bottom: 0.6em; }
.header .tagline { font-size: 12pt; color: #444; margin: 0.15em 0 0.4em 0; }
.header .contact { font-size: 9.5pt; color: #555; }
.header .contact a { margin-right: 1em; }
hr { border: none; border-top: 0.5pt solid #ccc; margin: 1.2em 0; }
/* pymdownx.tabbed (alternate_style) renders radio-toggle tabs; flatten for print.
   Structure: .tabbed-set > input* , .tabbed-labels > label* , .tabbed-content > .tabbed-block* */
.tabbed-set { border: none; }
.tabbed-set > input { display: none; }
.tabbed-labels { display: block; }
.tabbed-labels > label {
    display: block; font-weight: bold; font-size: 10.8pt; margin-top: 0.9em; color: #2e7d32;
}
.tabbed-labels > label img {
    height: 20pt; width: auto; vertical-align: middle; margin-right: 8pt; display: inline;
}
.tabbed-content, .tabbed-block { display: block !important; }
"""


def wrap(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>{PRINT_CSS}</style>
</head><body>{body_html}</body></html>"""


def header_html() -> str:
    return """
<div class="header">
<h1>Gareth Thomas</h1>
<div class="tagline">Consultant, technologist, and founder based in Eindhoven, Netherlands</div>
<div class="contact">
<a href="mailto:gareth.bj.thomas@gmail.com">gareth.bj.thomas@gmail.com</a>
<a href="https://nl.linkedin.com/in/g-thomas">linkedin.com/in/g-thomas</a>
Eindhoven, Netherlands
</div>
</div>
"""


def build_long_pdf() -> str:
    index_md = read("index.md")
    experience_md = read("experience.md")
    skills_md = read("skills.md")
    education_md = read("education.md")

    about = section(index_md, "## At a glance", "## What people say")
    testimonials = section(index_md, "## What people say", "See [Experience]")

    education = section(education_md, "## ![Instituto", "## LinkedIn Learning Courses")
    earlier_education = section(education_md, "## Earlier Education")
    education_full = education + "\n\n" + earlier_education

    parts = [
        header_html(),
        md_to_html(about),
        "<h2>Experience</h2>",
        md_to_html(experience_md.split("\n", 2)[-1]),
        "<h2>Skills</h2>",
        md_to_html(section(skills_md, "Self-rated")),
        "<h2>Education</h2>",
        md_to_html(education_full),
        md_to_html(testimonials),
    ]
    return wrap("Gareth Thomas — CV", "\n".join(parts))


def build_short_pdf() -> str:
    index_md = read("index.md")
    skills_md = read("skills.md")

    about_para = re.search(r"## About\n\n(.+?)\n\n", index_md, re.S).group(1)
    about_html = md_to_html(about_para)
    at_a_glance = section(index_md, "## At a glance", "## By the numbers")

    # Hand-transcribed one-liners of the same roles documented in experience.md,
    # condensed for a one-page summary (dates/titles verified against that file).
    roles = [
        ("CGI Nederland", "Consultant", "Jan 2026 – Present"),
        ("CGI Nederland", "Director Consulting Services", "Mar 2025 – Feb 2026"),
        ("VersionBay", "Co-Founder", "Nov 2018 – Mar 2025"),
        ("Open iT, Inc.", "Country Manager Benelux", "Jan 2020 – Sep 2021"),
        ("MathWorks", "Application Engineer → Business Development Manager", "Jan 2009 – Sep 2018"),
        ("Oceanscan", "Software Engineer", "Jan 2007 – Dec 2008"),
        ("Altran CIS", "Consultant", "Dec 2005 – Dec 2006"),
    ]

    top_skills = re.findall(r"\| ([\w /&().,+-]+?) \| ★★★★ \|", skills_md)

    edu_line = "Instituto Superior Técnico — MSc, Control Theory, 2000–2005, Lisbon, Portugal"

    experience_html = "<ul>"
    for company, role, dates in roles:
        experience_html += f"<li><strong>{company}</strong> — {role} <em>({dates})</em></li>"
    experience_html += "</ul>"

    skills_html = "<p>" + " · ".join(top_skills) + "</p>"

    parts = [
        header_html(),
        about_html,
        md_to_html(at_a_glance),
        "<h2>Experience</h2>",
        experience_html,
        "<h2>Top Skills</h2>",
        skills_html,
        "<h2>Education</h2>",
        f"<p>{edu_line}</p>",
    ]
    return wrap("Gareth Thomas — CV (Short)", "\n".join(parts))


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
