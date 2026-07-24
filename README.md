# Voltage Foundry Modular — website

The company landing page and module catalog, built with [Hugo](https://gohugo.io)
and published to GitHub Pages at **[vfmod.com](https://vfmod.com)**. No Ruby —
just the Hugo binary and Python 3.

## How it works

```text
.
├── hugo.toml            Site-wide settings (baseURL, params, links)
├── data/
│   ├── company.yml       Landing-page copy — edit this for company info
│   └── modules.yml       Module catalog — the single source of truth
├── layouts/
│   ├── _default/         baseof + section list templates
│   ├── modules/single.html   the per-module manual page
│   ├── partials/         head, header, footer, module card
│   └── index.html        the landing page
├── static/              css, js, logos (panels + manual images are generated)
│   └── js/panel-zoom.js  hover magnifier for the module-page panel image
├── content/_index.md    home page stub
├── sync_manuals.py      copies each module's manual + images in at build time
└── Makefile             modules-clone + sync + serve/build helpers
```

Nothing about the manuals is committed. Each module's manual + images live in
its **own** repo. On every deploy the workflow clones the published module repos
into `modules/` and runs `sync_manuals.py`, which reads `modules.yml` and
generates, for each module:

- `content/modules/<slug>/index.md` — a page containing that module's manual
- `static/modules/<slug>/<Images>/…` — the manual's images, under the folder name
  the module itself uses, so its relative links resolve (Pages URLs are
  case-sensitive: `images/` and `Images/` are not the same)
- `static/panels/<slug>.<ext>` — the catalog-card panel image

The cloned `modules/` dir and those generated paths are git-ignored. The script
has **no third-party dependencies**: it pulls only the file-path fields it needs
out of `modules.yml`, while Hugo reads the same file for all display metadata
(tags, tagline, series, …).

## Editing content

- **Company info / hero copy** → [`data/company.yml`](data/company.yml)
- **The module catalog** → [`data/modules.yml`](data/modules.yml)
- **Colors / layout** → [`static/css/style.css`](static/css/style.css)

On a module page, hovering the panel image opens a large zoom pane floating over
the page, showing the slice of the panel under the cursor, while a marker on the
panel itself highlights which slice that is — silkscreen and jack labels stay
readable without leaving the page. Magnification follows the image's own
resolution (the panels are ~4× the size they render at), so it never blurs;
`ZOOM_MIN` / `ZOOM_MAX` / `PANE_W` at the top of
[`static/js/panel-zoom.js`](static/js/panel-zoom.js) bound it. The whole thing is
skipped on touch devices and other coarse pointers.

### Adding a module

1. Add its `owner/repo` to **`MODULE_REPOS`** in **both**
   [`Makefile`](Makefile) and
   [`.github/workflows/pages.yml`](.github/workflows/pages.yml) — the list of
   module repos cloned in for the manuals. A repo that is still private stays out
   of both lists and gets `draft: true` below (the sync skips drafts), since CI
   can only clone public repos here.
2. Add a block to [`data/modules.yml`](data/modules.yml) — set `slug`, `name`,
   `tagline`, `repo`, the `manual_src` / `images_src` / `panel_src` paths
   (relative to the repo root, e.g. `modules/<Repo>/Manual.md`), and `tags`.
   That single block feeds both the card and the generated manual page.

No template or code changes are needed. Keep `modules.yml` in its documented
`key: value` form so the sync script keeps parsing it.

A module with no VCV Rack version (a fully analog one, say) gets `vcv: false` in
its block: the site then marks it **Hardware only** on the card and the manual
page.

## Local preview

Needs [Hugo](https://gohugo.io/installation/) and Python 3 (no Ruby, no Bundler).

```sh
make serve      # clone module repos, sync manuals, run `hugo server`
```

Or step by step: `make modules-clone` then `python3 sync_manuals.py` then
`hugo server`. Use `make build` for a production build into `public/`.

> No Hugo binary handy but have Go? `go install github.com/gohugoio/hugo@latest`.

## Publishing

Deployment is automatic via
[`.github/workflows/pages.yml`](.github/workflows/pages.yml) on every push to
`main`. The workflow installs Hugo, clones the module repos, runs the Python
sync, and builds — nothing else.

**One-time setup:** repository → **Settings → Pages → Build and deployment →
Source: “GitHub Actions,”** then set the custom domain to `vfmod.com`. DNS for
vfmod.com points at `voltagefoundrymod.github.io`.
