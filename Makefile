# VFM website (Hugo → GitHub Pages, vfmod.com).
#
# Each module's manual + images live in its own repo. `modules-clone` pulls the
# published module repos into modules/ (kept out of git — see .gitignore), then
# `sync` copies each manual + images into the site. CI does the same in
# .github/workflows/pages.yml; keep MODULE_REPOS here in sync with that file.
#
# Local preview:
#   make serve     # clone modules, sync manuals, run `hugo server`
# Needs the `hugo` binary and Python 3.

# Public module repos whose manuals this site publishes.
MODULE_REPOS := \
  VoltageFoundryMod/ForgeSeries-CLK \
  VoltageFoundryMod/ForgeSeries-DQ \
  VoltageFoundryMod/ForgeSeries-SCP \
  VoltageFoundryMod/IRONMix

# Clone each module repo into modules/<Repo> (shallow). Safe to re-run.
modules-clone:
	@for repo in $(MODULE_REPOS); do \
	  name=$${repo##*/}; \
	  if [ -d "modules/$$name/.git" ]; then \
	    echo "-> updating modules/$$name"; git -C "modules/$$name" pull --ff-only; \
	  else \
	    echo "-> cloning $$repo into modules/$$name"; \
	    git clone --depth 1 "https://github.com/$$repo.git" "modules/$$name"; \
	  fi; \
	done

sync: modules-clone
	python3 sync_manuals.py

serve: sync
	hugo server

build: sync
	hugo --gc --minify

.PHONY: modules-clone sync serve build
