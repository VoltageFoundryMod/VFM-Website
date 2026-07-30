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
├── sync_manuals.py      fetches each module's manual + images at build time
└── Makefile             sync + serve/build helpers
```

Nothing about the manuals is committed. They live in the module repos: the Forge
Series modules share the **ForgeSeries** monorepo (one app per `apps/<key>`
directory), and older modules are each their own repo. On every deploy CI just
runs `sync_manuals.py`, which reads `modules.yml`, fetches what it names and
generates, for each module:

- `content/modules/<slug>/index.md` — a page containing that module's manual
- `static/modules/<slug>/<Images>/…` — the manual's images, under the folder name
  the module itself uses, so its relative links resolve (Pages URLs are
  case-sensitive: `images/` and `Images/` are not the same)
- `static/panels/<slug>.<ext>` — the catalog-card panel image

`modules.yml` is the **only** list of module sources — the Makefile and the
workflow have none of their own. Each module names one `src` (`<repo>` or
`<repo>/<path in it>`) and everything else follows by convention:

| | |
| --- | --- |
| `<src>/Manual.md` | the manual |
| `<src>/images/` | its image folder |
| `<src>/images/Front.png` | the catalog-card panel |

`manual` / `images` / `panel` override one of those when a repo differs (IRONMix
predates the convention and capitalises `Images/`); `images: ~` means the module
has no image folder at all.

The cloned `modules/` dir and the generated paths are git-ignored. The script has
**no third-party dependencies**: it pulls only the handful of scalar fields it
needs out of `modules.yml`, while Hugo reads the same file for all display
metadata (tags, tagline, series, …). It needs only stock Python 3 and git.

### How the sources are fetched

Per repo, `sync_manuals.py` picks the first of:

1. **a sibling checkout** at `../<repo>` — so if you have `ForgeSeries` cloned
   next to this repo, `make serve` shows your uncommitted manual edits directly,
   with no commit or push;
2. an existing clone in `modules/<repo>`, refreshed with a pull;
3. a fresh clone into `modules/<repo>`.

CI has no siblings, so it always lands on the clone. That clone is shallow,
blobless and **sparse** — it matters, because ForgeSeries is a ~354 MB monorepo
and the site wants four `Manual.md` files and their images out of it. The sparse
set is derived from the same `src` paths: cone-mode on each module's image
directory, which also picks up the files sitting beside it (`Manual.md`) without
pulling any firmware or the 18 MB panel SVGs.

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

Add one block to [`data/modules.yml`](data/modules.yml) — that's the whole job.
Set `slug`, `name`, `tagline`, `tags` and `src`; a module that follows the
convention above needs nothing else:

```yaml
- slug: gravityforge
  name: Gravity Forge
  tagline: Dual physics-based generative sequencer — notes fall out of bouncing balls.
  series: Forge Series
  hp: 6HP
  src: ForgeSeries/apps/gen
  tags: [Sequencer, Random, Dual, Digital, Hardware clone, 6HP]
```

That single block feeds the card, the generated manual page, the GitHub source
link and what the sync fetches. No other file, template or code change.

A module whose repo is still private gets `draft: true`: the site hides it and
the sync skips it entirely, so CI never tries to clone it.

Keep `modules.yml` in its documented `key: value` form so the sync script keeps
parsing it.

A module with no VCV Rack version (a fully analog one, say) gets `vcv: false` in
its block: the site then marks it **Hardware only** on the card and the manual
page.

## Local preview

Needs [Hugo](https://gohugo.io/installation/) and Python 3 (no Ruby, no Bundler).

```sh
make serve      # fetch + sync manuals, run `hugo server`
```

Or step by step: `python3 sync_manuals.py` then `hugo server`. Use `make build`
for a production build into `public/`, and `make clean` to drop the cloned repos
and everything generated.

If you keep the module repos checked out next to this one (`../ForgeSeries`,
`../IRONMix`, …), the sync uses them as-is, so editing a manual there and
re-running `make serve` shows it immediately.

> No Hugo binary handy but have Go? `go install github.com/gohugoio/hugo@latest`.

## Publishing

Deployment is automatic via
[`.github/workflows/pages.yml`](.github/workflows/pages.yml) on every push to
`main`. The workflow installs Hugo, runs the Python sync (which fetches the
module repos itself) and builds — nothing else.

**One-time setup:** repository → **Settings → Pages → Build and deployment →
Source: “GitHub Actions,”** then set the custom domain to `vfmod.com`. DNS for
vfmod.com points at `voltagefoundrymod.github.io`.
