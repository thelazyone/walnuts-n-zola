# walnuts-n-zola

A minimal, menu-style recipe theme for [Zola](https://www.getzola.org/).

**Live demo:** https://thelazyone.github.io/walnuts-n-zola/

## Install

```bash
zola install https://github.com/thelazyone/walnuts-n-zola
```

Add to your site's `config.toml`:

```toml
theme = "walnuts-n-zola"

[extra]
dishes_of_the_day_count = 6
```

Place a logo at `static/images/logo.png` in your site (overrides the theme placeholder).

## Content structure

```
content/
  _index.md              # Homepage
  menu/
    _index.md            # All dishes (sections overview)
    pastas/
      _index.md          # Section page
      red-pastas/
        _index.md        # Subsection (anchor only, render = false)
        arrabbiata.md    # Recipe → /arrabbiata/
```

- **Homepage** — logo, navigation, dishes of the day (count set in `[extra]`, rotated daily in the browser)
- **All dishes** (`/menu/`) — section list with short descriptions
- **Section pages** — subsections as anchors, recipes listed alphabetically (or by `weight`)
- **Recipe pages** — flat URLs like `/arrabbiata/`

See `exampleSite/content/` for a minimal working menu.

### New section

Create `content/menu/your-section/_index.md`:

```toml
+++
title = "Your Section"
description = "A short blurb for the All dishes page."
weight = 10
+++
```

### New subsection

Create `content/menu/your-section/your-subsection/_index.md`:

```toml
+++
title = "Your Subsection"
render = false
weight = 1
+++
```

### New recipe

Create `content/menu/.../your-subsection/recipe-name.md`:

```toml
+++
title = "Recipe Name"
description = "Short menu line."
path = "recipe-slug"
template = "recipe.html"
weight = 100

[extra]
recommended = true
dietary = ["vegan", "gluten-free"]
ingredients = """
- item one
- item two
"""
notes = "Optional note below the body."
+++
```

Optional markdown body for method or longer text.

**Chef's pick:** set `recommended = true` under `[extra]` to show the chef icon next to the title.

**Dietary flags:** any string works — e.g. `meat`, `fish`, `vegetarian`, `vegan`, `gluten-free`, `dairy-free`.

**Ordering:** set `weight` to 1, 2, 3… to pin order; leave at `100` for alphabetical sorting within the subsection.

## Dishes of the day

The homepage embeds the full recipe catalog at build time. On load, `static/js/dishes-of-the-day.js` picks recipes deterministically from today's date using SHA-256 ranking — same picks all day until midnight. Adding or editing recipes only requires a normal `zola build`; the daily rotation needs no rebuild.

Sections can opt out by setting `exclude_from_dishes_of_the_day = true` under `[extra]` in the section's `_index.md`.

## Recipe editor (GUI)

Optional visual editor for menu content:

```bash
python -m scripts.recipe_editor --root /path/to/your/zola/site
```

If you run it from this repo with a local `lesnack/` site folder, `--root` can be omitted (defaults to `lesnack/` when present).

Requires Python 3.10+ (uses tkinter).

## Theme development

One-time setup — link this repo as the theme (needed for local builds):

```bash
# Linux / macOS
./scripts/link-theme-local.sh

# Windows (PowerShell)
./scripts/link-theme-local.ps1
```

Then:

```bash
cd exampleSite
zola serve
```

Open http://127.0.0.1:1111

Build the demo:

```bash
cd exampleSite
zola build
```

Requires [Zola 0.19+](https://www.getzola.org/documentation/getting-started/installation/) (matches CI).

## Personal site setup

See [docs/lesnack-site.md](docs/lesnack-site.md) for deploying your own site with this theme (GitHub Actions, private repo, etc.).

## License

MIT — see [LICENSE](LICENSE).
