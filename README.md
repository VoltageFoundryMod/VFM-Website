# Voltage Foundry Modular — website

The company landing page and module catalog, built with [Hugo](https://gohugo.io)
and published to GitHub Pages. No Ruby — just the Hugo binary and Python 3.

## How it works

```text
docs/
├── hugo.toml            Site-wide settings (baseURL, params, links)
├── data/
│   ├── company.yml       Landing-page copy — edit this for company info
│   └── modules.yml       Module catalog — the single source of truth
├── layouts/
│   ├── _default/         baseof + section list templates
│   ├── modules/single.html   the per-module manual page
│   ├── partials/         head, header, footer, module card
│   └── index.html        the landing page
├── static/              css, logos (panels + manual images are generated)
├── content/_index.md    home page stub
└── sync_manuals.py      copies each module's manual + images in at build time
```

Nothing about the manuals is committed. On every deploy the workflow checks out
the module submodules and runs `sync_manuals.py`, which reads `modules.yml` and
generates, for each module:

- `content/modules/<slug>/index.md` — a page containing that module's manual
- `static/modules/<slug>/images/…` — the manual's images (served at the page URL)
- `static/panels/<slug>.<ext>` — the catalog-card panel image

Those generated paths are git-ignored. The script has **no third-party
dependencies**: it pulls only the file-path fields it needs out of
`modules.yml`, while Hugo reads the same file for all display metadata (tags,
tagline, series, …).

## Editing content

- **Company info / hero copy** → [`data/company.yml`](data/company.yml)
- **The module catalog** → [`data/modules.yml`](data/modules.yml)
- **Colors / layout** → [`static/css/style.css`](static/css/style.css)

### Adding a module

1. Add its repository as a submodule under `../modules`.
2. Add a block to [`data/modules.yml`](data/modules.yml) — set `slug`, `name`,
   `tagline`, `repo`, the `manual_src` / `images_src` / `panel_src` paths, and
   `tags`. That single block feeds both the card and the generated manual page.

No template or code changes are needed. Keep `modules.yml` in its documented
`key: value` form so the sync script keeps parsing it.

## Local preview

Needs [Hugo](https://gohugo.io/installation/) and Python 3 (no Ruby, no Bundler).

```sh
cd docs
python3 sync_manuals.py          # pull manuals out of the submodules
hugo server                      # → http://localhost:1313/VFM-VCV/
```

From the repo root you can also run `make docs-serve` (sync + serve) or
`make docs-build`.

> No Hugo binary handy but have Go? `go install github.com/gohugoio/hugo@latest`.

## Publishing

Deployment is automatic via
[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) on every push to
`main` that touches `docs/`, the submodule pins, or the workflow itself. The
workflow installs Hugo, runs the Python sync, and builds — nothing else.

**One-time setup:** repository → **Settings → Pages → Build and deployment →
Source: “GitHub Actions.”** After the first successful run the site is live at
`https://voltagefoundrymod.github.io/VFM-VCV/`.
