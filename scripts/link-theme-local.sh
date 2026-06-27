#!/usr/bin/env bash
# Link the repo root as the theme for local exampleSite / lesnack builds.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"

link_theme() {
  local site="$1"
  mkdir -p "$site/themes"
  ln -sfn "$root" "$site/themes/walnuts-n-zola"
  echo "Linked $site/themes/walnuts-n-zola -> $root"
}

link_theme "$root/exampleSite"
if [[ -d "$root/lesnack" ]]; then
  link_theme "$root/lesnack"
fi
