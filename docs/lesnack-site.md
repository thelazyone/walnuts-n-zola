# Lesnack site — publish checklist

Use this when creating the private **lesnack** GitHub repository.

## Repository layout

```
lesnack/
  config.toml
  content/
    _index.md
    menu/
      ...
  static/
    images/
      logo.png          # your logo (overrides theme default)
  .github/
    workflows/
      deploy.yml
```

## config.toml

```toml
title = "Lesnack"
description = "A menu of recipes"
base_url = "https://thelazyone.github.io/lesnack/"
theme = "walnuts-n-zola"
compile_sass = false
minify_html = true
default_language = "en"

[markdown]
highlight_code = false
smart_punctuation = true

[extra]
dishes_of_the_day_count = 6
```

## GitHub Actions (`.github/workflows/deploy.yml`)

```yaml
name: Deploy site

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Install theme
        run: |
          docker run --rm \
            -v "${{ github.workspace }}":/project \
            -w /project \
            ghcr.io/getzola/zola:v0.19.2 \
            install https://github.com/thelazyone/walnuts-n-zola

      - name: Build with Zola
        run: |
          docker run --rm \
            -v "${{ github.workspace }}":/project \
            -w /project \
            ghcr.io/getzola/zola:v0.19.2 \
            build --base-url "https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}/"

      - name: Upload site
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

## Steps

1. Create a **private** repo named `lesnack` on GitHub.
2. Copy `lesnack/` contents from this machine (config, content, optional static assets).
3. Add the workflow above and push to `main`.
4. In the repo **Settings → Pages**, set source to **GitHub Actions**.
5. The site will be at https://thelazyone.github.io/lesnack/

The theme is installed from `main` on each build (`zola install`). Pin to a release tag later if you want stricter stability.

## Recipe editor

Clone both repos locally, or keep using the theme repo with `--root`:

```bash
python -m scripts.recipe_editor --root /path/to/lesnack
```
