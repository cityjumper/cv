# Gareth Thomas — CV

A CV site built with [Zensical](https://zensical.org/), the modern static site generator from the Material for MkDocs team. Content is authored in Markdown, dependencies are managed with [uv](https://docs.astral.sh/uv/), and the site is published to GitHub Pages via GitHub Actions.

## Structure

- `docs/` — Markdown content (one file per nav page: Home, Experience, Education, Timeline, Community & Talks, Languages)
- `docs/assets/` — downloadable PDFs (CV, thesis, talk slides)
- `zensical.toml` — site config: theme, navigation, palette, extensions
- `pyproject.toml` / `uv.lock` — Python environment, managed by uv

## Local development

```bash
uv sync              # install Zensical and dependencies into .venv
uv run zensical serve # serve the site locally with live reload
uv run zensical build # build the static site into site/
```

## Regenerating the CV PDFs

`docs/assets/gareth-thomas-cv-short.pdf` and `-long.pdf` are generated from the real Markdown content in `docs/` (not hand-authored), so they should be regenerated whenever `index.md`, `experience.md`, `skills.md`, or `education.md` change:

```bash
uv run --extra pdf python scripts/generate_pdfs.py
```

## Publish on GitHub Pages

The `.github/workflows/deploy-pages.yml` workflow builds the site with uv + Zensical and deploys the `site/` output to GitHub Pages automatically on every push to `main`. In the repository's Settings → Pages, set the source to "GitHub Actions".
