# VFM website (Hugo → GitHub Pages, vfmod.com).
#
# `sync_manuals.py` reads data/modules.yml — the only list of modules — and
# fetches each one's manual + images into the site. There is no repo list to
# keep in step here or in CI; both just run the script.
#
# It prefers a sibling checkout (../ForgeSeries, ../IRONMix, …) when you have
# one, so `make serve` picks up manual edits in those repos with no commit or
# push. Otherwise it shallow-clones into modules/ (gitignored).
#
# Local preview:
#   make serve     # sync manuals, run `hugo server`
# Needs the `hugo` binary, Python 3 and git.

sync:
	python3 sync_manuals.py

serve: sync
	hugo server

build: sync
	hugo --gc --minify

# Drop the cloned module repos and everything the sync generates.
clean:
	rm -rf modules content/modules static/modules static/panels public resources

.PHONY: sync serve build clean
