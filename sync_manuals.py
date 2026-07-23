#!/usr/bin/env python3
"""Sync each module's manual + images into the Hugo site.

Reads data/modules.yml (the single source of truth) and, for every module,
generates:

    content/modules/<slug>/index.md   Hugo page (front matter + manual body)
    static/modules/<slug>/images/...  the manual's images (served verbatim)
    static/panels/<slug>.<ext>        the catalog-card panel image

Manuals live in the git submodules under ../modules, so nothing generated here
is committed — the GitHub Actions workflow runs this on every deploy after
checking out submodules. Run it locally with `python sync_manuals.py` (or
`make docs-sync`) to preview.

No third-party dependencies: it extracts only the handful of scalar path fields
it needs from modules.yml, so CI needs nothing but a stock Python 3. All the
display metadata (tags, tagline, series, …) is read straight from the same YAML
by Hugo. Idempotent: generated directories are wiped and rebuilt each run.
"""

from __future__ import annotations

import os
import re
import shutil
import sys

DOCS = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(DOCS)
DATA_FILE = os.path.join(DOCS, "data", "modules.yml")

# Scalar fields the sync needs from each module block in modules.yml.
FIELDS = ("slug", "name", "manual_src", "images_src", "panel_src")


def parse_modules(path: str) -> list[dict[str, str | None]]:
    """Minimal reader for the flat 'list of modules' shape of modules.yml.

    Splits the file on top-level '- ' list items and pulls the scalar fields in
    FIELDS out of each. Deliberately not a general YAML parser — keep modules.yml
    in its documented `key: value` form and this stays reliable.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()

    # Start a new block at each top-level list item ("- slug: ...").
    blocks = re.split(r"(?m)^- ", text)
    modules: list[dict[str, str | None]] = []
    for block in blocks:
        if "slug:" not in block:
            continue  # leading comments / preamble
        block = "- " + block
        entry: dict[str, str | None] = {}
        for key in FIELDS:
            # Key may sit on the list-item line ("- slug: x") or an indented
            # continuation line ("  name: y").
            m = re.search(rf"(?m)^[ \t]*(?:-[ \t]+)?{key}:[ \t]*(.*?)[ \t]*$", block)
            if not m:
                entry[key] = None
                continue
            val = m.group(1).strip().strip('"').strip("'")
            entry[key] = None if val in ("", "~") else val
        modules.append(entry)
    return modules


def die(msg: str) -> None:
    sys.stderr.write(f"  ! {msg}\n")
    sys.stderr.write("    Did you run `git submodule update --init --recursive`?\n")
    sys.exit(1)


def main() -> None:
    modules = parse_modules(DATA_FILE)

    # Fresh start so removed modules / renamed images never linger.
    for d in ("content/modules", "static/modules", "static/panels"):
        shutil.rmtree(os.path.join(DOCS, d), ignore_errors=True)
    os.makedirs(os.path.join(DOCS, "static", "panels"), exist_ok=True)

    for m in modules:
        slug, name = m["slug"], m["name"]
        print(f"-> {name} ({slug})")

        out_dir = os.path.join(DOCS, "content", "modules", slug)
        os.makedirs(out_dir, exist_ok=True)

        # 1. Manual body -> Hugo page. Hugo does not interpret {{ }} in content
        #    (only explicit shortcodes), so no escaping dance is needed.
        manual_path = os.path.join(REPO_ROOT, m["manual_src"])
        if not os.path.isfile(manual_path):
            die(f"manual not found: {manual_path}")
        with open(manual_path, encoding="utf-8") as fh:
            body = fh.read()

        title = (name or slug).replace('"', "'")
        front = (
            "---\n"
            f'title: "{title}"\n'
            f"slug: {slug}\n"
            "---\n\n"
        )
        with open(os.path.join(out_dir, "index.md"), "w", encoding="utf-8") as fh:
            fh.write(front + body)

        # 2. Manual images. Served from static/ at the same URL the page uses,
        #    so relative refs like ./images/Front.png resolve.
        if m["images_src"]:
            img_src = os.path.join(REPO_ROOT, m["images_src"])
            if os.path.isdir(img_src):
                shutil.copytree(
                    img_src, os.path.join(DOCS, "static", "modules", slug, "images")
                )
            else:
                die(f"images dir not found: {img_src}")

        # 3. Catalog-card panel.
        panel_src = os.path.join(REPO_ROOT, m["panel_src"])
        if not os.path.isfile(panel_src):
            die(f"panel image not found: {panel_src}")
        ext = os.path.splitext(panel_src)[1]
        shutil.copy(panel_src, os.path.join(DOCS, "static", "panels", f"{slug}{ext}"))

    print(f"Synced {len(modules)} module(s).")


if __name__ == "__main__":
    main()
