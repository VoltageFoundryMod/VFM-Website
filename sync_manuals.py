#!/usr/bin/env python3
"""Fetch each module's manual + images and sync them into the Hugo site.

`data/modules.yml` is the single source of truth. Every module names one `src`:

    src: ForgeSeries/apps/clk     <repo>/<path within it>
    src: IRONMix                  a repo whose root *is* the module

From that, everything else follows by convention:

    <src>/Manual.md               the manual body
    <src>/images/                 its image folder
    <src>/images/Front.png        the catalog-card panel

so a well-behaved module needs exactly one line. `manual` / `images` / `panel`
override a default when a repo does something different (IRONMix capitalises
`Images/`); `images: ~` means the module has no image folder at all.

This script also *acquires* the sources, so the repo list lives in one place
instead of being mirrored in the Makefile and the CI workflow. Per repo it
picks, in order:

  1. a sibling working copy at ../<repo> — so editing a manual in the module
     repo and running `make serve` here shows it immediately, no commit needed;
  2. an existing clone in modules/<repo>, refreshed with a pull;
  3. a fresh shallow, sparse clone into modules/<repo>.

The sparse checkout matters: ForgeSeries is a ~354 MB monorepo and the site
wants four Manual.md files and their images out of it. Cone-mode sparse on each
module's image dir also picks up the files sitting next to it (Manual.md), which
is exactly the set we need and none of the firmware or the 18 MB panel SVGs.

Everything generated here is gitignored — CI reruns it on every deploy:

    content/modules/<slug>/index.md   Hugo page (front matter + manual body)
    static/modules/<slug>/<Images>/…  the manual's images (served verbatim)
    static/panels/<slug>.<ext>        the catalog-card panel image

No third-party dependencies: it extracts only the handful of scalar fields it
needs from modules.yml, so CI needs nothing but a stock Python 3 and git. All
the display metadata (tags, tagline, series, …) is read straight from the same
YAML by Hugo. Idempotent: generated directories are wiped and rebuilt each run.
"""

from __future__ import annotations

import os
import posixpath
import re
import shutil
import subprocess
import sys

# This script lives at the site root.
SITE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SITE, "data", "modules.yml")
CLONE_DIR = os.path.join(SITE, "modules")  # gitignored; see .gitignore
SIBLING_DIR = os.path.dirname(SITE)  # ../  — where local checkouts live
GITHUB_ORG = "VoltageFoundryMod"

# Layout every module is assumed to follow unless it says otherwise.
DEFAULT_MANUAL = "Manual.md"
DEFAULT_IMAGES = "images"
DEFAULT_PANEL = "images/Front.png"

# Scalar fields the sync needs from each module block in modules.yml.
FIELDS = ("slug", "name", "src", "manual", "images", "panel", "draft")


def parse_modules(path: str) -> list[dict[str, str | None]]:
    """Minimal reader for the flat 'list of modules' shape of modules.yml.

    Splits the file on top-level '- ' list items and pulls the scalar fields in
    FIELDS out of each. Deliberately not a general YAML parser — keep modules.yml
    in its documented `key: value` form and this stays reliable.

    An absent key is left out of the dict; a key written as `~` maps to None.
    The difference is load-bearing for `images`, where `~` means "this module has
    no image folder" and absence means "use the default one".
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
                continue
            val = m.group(1).strip().strip('"').strip("'")
            entry[key] = None if val in ("", "~") else val
        modules.append(entry)
    return modules


def die(msg: str) -> None:
    sys.stderr.write(f"  ! {msg}\n")
    sys.exit(1)


def run(cmd: list[str]) -> None:
    """Run a git command, failing loudly (its own stderr is the error message)."""
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        die(f"command failed: {' '.join(cmd)}")


def is_ancestor(parent: str, child: str) -> bool:
    """True if `parent` is `child` or contains it. Both are posix-style paths."""
    return parent == child or child.startswith(parent + "/")


# ── module records ───────────────────────────────────────────────────────────


class Module:
    """One entry from modules.yml, with the convention already applied."""

    def __init__(self, entry: dict[str, str | None]) -> None:
        self.slug = entry.get("slug")
        self.name = entry.get("name") or self.slug
        self.draft = (entry.get("draft") or "").lower() == "true"

        src = entry.get("src")
        if not src:
            die(f"module '{self.slug}' has no `src:`")
        src = src.strip("/")
        # "ForgeSeries/apps/clk" -> repo "ForgeSeries", sub "apps/clk".
        # "IRONMix"              -> repo "IRONMix",     sub "".
        self.repo, _, self.sub = src.partition("/")

        # Paths below are relative to the module's own directory, not the repo.
        self.manual = entry.get("manual") or DEFAULT_MANUAL
        self.panel = entry.get("panel") or DEFAULT_PANEL
        # Absent -> the conventional folder; explicit `~` -> no images at all.
        self.images = entry.get("images", DEFAULT_IMAGES)

    def rel(self, path: str) -> str:
        """A module-relative path, made relative to the repo root."""
        return posixpath.join(self.sub, path) if self.sub else path

    def sparse_dirs(self) -> list[str]:
        """Cone-mode sparse dirs that cover this module's files.

        Cone mode checks out each named directory recursively *plus* the plain
        files sitting in its ancestors. That second half is what keeps this
        cheap: asking for `apps/clk/images` also yields `apps/clk/Manual.md`
        without dragging in `apps/clk/src`, `lib` and `vcv-plugin`.

        So the asset dirs are listed, and the manual's directory only when it
        isn't already an ancestor of one of them — naming it unconditionally
        would ask for `apps/clk`, i.e. the entire module.
        """
        dirs = {posixpath.dirname(self.rel(self.panel))}
        if self.images:
            dirs.add(self.rel(self.images).rstrip("/"))
        dirs.discard("")

        manual_dir = posixpath.dirname(self.rel(self.manual))
        if manual_dir and not any(is_ancestor(manual_dir, d) for d in dirs):
            dirs.add(manual_dir)
        return sorted(dirs)


# ── acquiring the sources ────────────────────────────────────────────────────


def clone_url(repo: str) -> str:
    return f"https://github.com/{GITHUB_ORG}/{repo}.git"


def repo_root(repo: str, mods: list[Module]) -> str:
    """Return a checkout of `repo`, cloning or updating one if needed."""
    sibling = os.path.join(SIBLING_DIR, repo)
    if os.path.isdir(os.path.join(sibling, ".git")):
        print(f"== {repo}: using local checkout at ../{repo}")
        return sibling

    dest = os.path.join(CLONE_DIR, repo)
    url = clone_url(repo)

    if os.path.isdir(os.path.join(dest, ".git")):
        print(f"== {repo}: updating modules/{repo}")
        run(["git", "-C", dest, "pull", "--ff-only"])
        return dest

    print(f"== {repo}: cloning {url}")
    os.makedirs(CLONE_DIR, exist_ok=True)
    # Shallow + blobless + sparse: we want a handful of markdown files and
    # images, not the repo's history or its firmware sources.
    run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", url, dest])

    # A module that *is* the repo root has nothing to narrow down to.
    dirs = sorted({d for m in mods for d in m.sparse_dirs()})
    if dirs:
        print(f"   sparse-checkout: {' '.join(dirs)}")
        run(["git", "-C", dest, "sparse-checkout", "set", *dirs])
    else:
        run(["git", "-C", dest, "sparse-checkout", "disable"])
    return dest


# ── syncing into the site ────────────────────────────────────────────────────


def sync(m: Module, root: str) -> None:
    out_dir = os.path.join(SITE, "content", "modules", m.slug)
    os.makedirs(out_dir, exist_ok=True)

    # 1. Manual body -> Hugo page. Hugo does not interpret {{ }} in content
    #    (only explicit shortcodes), so no escaping dance is needed.
    manual_path = os.path.join(root, m.rel(m.manual).replace("/", os.sep))
    if not os.path.isfile(manual_path):
        die(f"{m.slug}: manual not found: {manual_path}")
    with open(manual_path, encoding="utf-8") as fh:
        body = fh.read()

    title = m.name.replace('"', "'")
    front = f'---\ntitle: "{title}"\nslug: {m.slug}\n---\n\n'
    with open(os.path.join(out_dir, "index.md"), "w", encoding="utf-8") as fh:
        fh.write(front + body)

    # 2. Manual images. Served from static/ at the same URL the page uses, so
    #    relative refs like ./images/Front.png resolve. The source folder name
    #    is kept verbatim — modules spell it differently (images/, Images/) and
    #    Pages serves case-sensitive URLs.
    if m.images:
        img_src = os.path.join(root, m.rel(m.images).replace("/", os.sep))
        if not os.path.isdir(img_src):
            die(f"{m.slug}: images dir not found: {img_src}")
        dest = os.path.join(SITE, "static", "modules", m.slug, m.images.rstrip("/"))
        shutil.copytree(img_src, dest)

    # 3. Catalog-card panel.
    panel_src = os.path.join(root, m.rel(m.panel).replace("/", os.sep))
    if not os.path.isfile(panel_src):
        die(f"{m.slug}: panel image not found: {panel_src}")
    ext = os.path.splitext(panel_src)[1]
    shutil.copy(panel_src, os.path.join(SITE, "static", "panels", f"{m.slug}{ext}"))


def main() -> None:
    modules = [Module(e) for e in parse_modules(DATA_FILE)]
    live = [m for m in modules if not m.draft]
    for m in modules:
        if m.draft:
            # A draft's repo may not even be public yet, so don't touch it.
            print(f"-- {m.name} ({m.slug}) [draft — skipped]")

    # Group by repo so a monorepo is cloned once, with one sparse checkout
    # covering every module it holds.
    by_repo: dict[str, list[Module]] = {}
    for m in live:
        by_repo.setdefault(m.repo, []).append(m)

    roots = {repo: repo_root(repo, mods) for repo, mods in by_repo.items()}

    # Fresh start so removed modules / renamed images never linger.
    for d in ("content/modules", "static/modules", "static/panels"):
        shutil.rmtree(os.path.join(SITE, d), ignore_errors=True)
    os.makedirs(os.path.join(SITE, "static", "panels"), exist_ok=True)

    for m in live:
        print(f"-> {m.name} ({m.slug}) from {m.repo}/{m.sub}".rstrip("/"))
        sync(m, roots[m.repo])

    print(f"Synced {len(live)} module(s) from {len(by_repo)} repo(s).")


if __name__ == "__main__":
    main()
