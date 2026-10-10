#!/bin/sh
set -eu
project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project"
python3 tools/generate_sounds.py
python3 -m unittest discover -s tests -v
mkdir -p .build/tmp .build/rpmdb .build/rpm/BUILD .build/rpm/BUILDROOT .build/rpm/RPMS .build/rpm/SOURCES .build/rpm/SPECS .build/rpm/SRPMS dist
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT HUP INT TERM
mkdir "$stage/pacman2026-1.0.0"
cp -r pacman2026 assets packaging tools tests README.md LICENSE "$stage/pacman2026-1.0.0/"
find "$stage" -type d -name __pycache__ -exec rm -rf {} +
tar -czf .build/rpm/SOURCES/pacman2026-1.0.0.tar.gz -C "$stage" pacman2026-1.0.0
rpmbuild --define "_topdir $project/.build/rpm" --define "_tmppath $project/.build/tmp" --define "_dbpath $project/.build/rpmdb" --define 'dist .el8' --define '_binary_payload w9.gzdio' -ba packaging/pacman2026.spec
cp .build/rpm/RPMS/noarch/*.rpm dist/
cp .build/rpm/SRPMS/*.rpm dist/
(cd dist && sha256sum *.rpm > SHA256SUMS)
