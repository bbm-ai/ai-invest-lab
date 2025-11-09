#!/usr/bin/env bash
set -Eeuo pipefail
echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
echo "Last tag: $(git describe --tags --abbrev=0 2>/dev/null || echo 'none')"
echo "CI file: .github/workflows/ci.yml $( [ -f .github/workflows/ci.yml ] && echo '✅' || echo '❌')"
echo "Release entry: scripts/make_release.sh $( [ -f scripts/make_release.sh ] && echo '✅' || echo '❌')"
echo "direnv: $( [ -f .envrc ] && echo '.envrc present ✅' || echo 'missing ❌')"
