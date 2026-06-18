"""Read and write Zola recipe content under content/menu/."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MENU_ROOT = ROOT / "content" / "menu"

FRONT_MATTER = re.compile(r"^\+{3}\s*\r?\n(.*?)\r?\n\+{3}\s*(?:\r?\n|$)", re.DOTALL)

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore

SECTION_DEFAULTS: dict[str, Any] = {
    "template": "section.html",
    "sort_by": "weight",
    "page_template": "recipe.html",
    "insert_anchor_links": "none",
}

SUBSECTION_DEFAULTS: dict[str, Any] = {
    "render": False,
    "sort_by": "weight",
}

RECIPE_DEFAULTS: dict[str, Any] = {
    "template": "recipe.html",
    "weight": 100,
}


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-") or "item"


def escape_toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def format_toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        inner = ", ".join(f'"{escape_toml_string(str(v))}"' for v in value)
        return f"[{inner}]"
    if isinstance(value, str):
        if "\n" in value:
            return f'"""\n{value}"""\n'
        return f'"{escape_toml_string(value)}"'
    raise TypeError(f"Unsupported TOML value: {type(value)!r}")


def dump_front_matter(data: dict[str, Any]) -> str:
    order = [
        "title",
        "description",
        "path",
        "template",
        "weight",
        "sort_by",
        "page_template",
        "insert_anchor_links",
        "render",
    ]
    lines: list[str] = []
    for key in order:
        if key in data and key != "extra":
            lines.append(f"{key} = {format_toml_value(data[key]).rstrip()}")
    extra = data.get("extra") or {}
    if extra:
        lines.append("")
        lines.append("[extra]")
        for key, value in extra.items():
            lines.append(f"{key} = {format_toml_value(value).rstrip()}")
    return "\n".join(lines)


def parse_markdown(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    front = tomllib.loads(match.group(1))
    body = text[match.end() :]
    if body.startswith("\r\n"):
        body = body[2:]
    elif body.startswith("\n"):
        body = body[1:]
    return front, body


def write_markdown(path: Path, front: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"+++\n{dump_front_matter(front)}\n+++\n"
    if body.strip():
        content += f"\n{body.rstrip()}\n"
    else:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def node_kind(path: Path) -> str:
    rel = path.relative_to(MENU_ROOT)
    parts = rel.parts
    if path.name == "_index.md":
        return "section" if len(parts) == 2 else "subsection"
    return "recipe"


@dataclass
class TreeNode:
    kind: str
    path: Path
    title: str
    children: list[TreeNode] = field(default_factory=list)

    @property
    def rel(self) -> str:
        return str(self.path.relative_to(ROOT))


def read_title(path: Path) -> str:
    front, _ = parse_markdown(path)
    return str(front.get("title") or path.stem)


def scan_tree() -> TreeNode:
    root = TreeNode(kind="menu", path=MENU_ROOT, title="Menu")
    if not MENU_ROOT.is_dir():
        return root

    sections = sorted(
        (p for p in MENU_ROOT.iterdir() if p.is_dir()),
        key=lambda p: _section_weight(p / "_index.md"),
    )
    for section_dir in sections:
        index = section_dir / "_index.md"
        if not index.is_file():
            continue
        section = TreeNode(
            kind="section",
            path=index,
            title=read_title(index),
        )
        subsections = sorted(
            (p for p in section_dir.iterdir() if p.is_dir()),
            key=lambda p: _section_weight(p / "_index.md"),
        )
        for sub_dir in subsections:
            sub_index = sub_dir / "_index.md"
            if not sub_index.is_file():
                continue
            subsection = TreeNode(
                kind="subsection",
                path=sub_index,
                title=read_title(sub_index),
            )
            recipes = sorted(
                (p for p in sub_dir.glob("*.md") if p.name != "_index.md"),
                key=lambda p: read_title(p).lower(),
            )
            for recipe_path in recipes:
                subsection.children.append(
                    TreeNode(
                        kind="recipe",
                        path=recipe_path,
                        title=read_title(recipe_path),
                    )
                )
            section.children.append(subsection)
        root.children.append(section)
    return root


def _section_weight(index_path: Path) -> int:
    if not index_path.is_file():
        return 9999
    front, _ = parse_markdown(index_path)
    return int(front.get("weight") or 9999)


def next_section_weight() -> int:
    weights = []
    for section_dir in MENU_ROOT.iterdir():
        if section_dir.is_dir():
            weights.append(_section_weight(section_dir / "_index.md"))
    return max(weights, default=0) + 1


def next_subsection_weight(section_dir: Path) -> int:
    weights = []
    for sub in section_dir.iterdir():
        if sub.is_dir():
            weights.append(_section_weight(sub / "_index.md"))
    return max(weights, default=0) + 1


def default_section(name: str) -> dict[str, Any]:
    return {
        "title": name,
        "description": "",
        "weight": next_section_weight(),
        **SECTION_DEFAULTS,
    }


def default_subsection(name: str, section_dir: Path) -> dict[str, Any]:
    return {
        "title": name,
        "weight": next_subsection_weight(section_dir),
        **SUBSECTION_DEFAULTS,
    }


def default_recipe(name: str) -> dict[str, Any]:
    slug = slugify(name)
    return {
        "title": name,
        "description": "",
        "path": slug,
        **RECIPE_DEFAULTS,
        "extra": {
            "dietary": [],
            "ingredients": "",
        },
    }


def create_section(name: str) -> Path:
    folder = MENU_ROOT / slugify(name)
    folder.mkdir(parents=True, exist_ok=False)
    index = folder / "_index.md"
    write_markdown(index, default_section(name), "")
    return index


def create_subsection(section_dir: Path, name: str) -> Path:
    folder = section_dir / slugify(name)
    folder.mkdir(parents=True, exist_ok=False)
    index = folder / "_index.md"
    write_markdown(index, default_subsection(name, section_dir), "")
    return index


def create_recipe(subsection_dir: Path, name: str) -> Path:
    front = default_recipe(name)
    path = subsection_dir / f"{front['path']}.md"
    write_markdown(path, front, "")
    return path


def duplicate_recipe(recipe_path: Path) -> Path:
    front, body = parse_markdown(recipe_path)
    base_title = str(front.get("title") or recipe_path.stem)
    new_title = f"{base_title} (copy)"
    front["title"] = new_title
    slug = slugify(new_title)
    front["path"] = slug
    target = recipe_path.parent / f"{slug}.md"
    n = 2
    while target.exists():
        slug = f"{slugify(base_title)}-copy-{n}"
        front["path"] = slug
        front["title"] = f"{base_title} (copy {n})"
        target = recipe_path.parent / f"{slug}.md"
        n += 1
    write_markdown(target, front, body)
    return target


def delete_node(node: TreeNode) -> None:
    if node.kind == "recipe":
        node.path.unlink(missing_ok=True)
        return
    folder = node.path.parent
    shutil.rmtree(folder)


def move_recipe(recipe_path: Path, target_subsection_dir: Path) -> Path:
    front, body = parse_markdown(recipe_path)
    slug = str(front.get("path") or slugify(str(front.get("title") or recipe_path.stem)))
    target = target_subsection_dir / f"{slug}.md"
    if target.resolve() == recipe_path.resolve():
        return recipe_path
    n = 2
    while target.exists():
        slug = f"{slugify(str(front.get('title') or recipe_path.stem))}-{n}"
        target = target_subsection_dir / f"{slug}.md"
        front["path"] = slug
        n += 1
    write_markdown(target, front, body)
    recipe_path.unlink()
    return target


def move_subsection(subsection_index: Path, target_section_dir: Path) -> Path:
    src_dir = subsection_index.parent
    dst_dir = target_section_dir / src_dir.name
    if dst_dir.resolve() == src_dir.resolve():
        return subsection_index
    if dst_dir.exists():
        raise FileExistsError(f"Subsection folder already exists: {dst_dir.name}")
    shutil.move(str(src_dir), str(dst_dir))
    return dst_dir / "_index.md"


def save_recipe(path: Path, front: dict[str, Any], body: str) -> Path:
    slug = str(front.get("path") or slugify(str(front.get("title") or path.stem)))
    front["path"] = slug
    target = path.parent / f"{slug}.md"
    write_markdown(target, front, body)
    if target.resolve() != path.resolve() and path.is_file():
        path.unlink()
    return target


def save_section_index(path: Path, front: dict[str, Any]) -> None:
    _, body = parse_markdown(path)
    write_markdown(path, front, body)


def save_subsection_index(path: Path, front: dict[str, Any]) -> None:
    write_markdown(path, front, "")


def all_subsections() -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    for section_dir in sorted(MENU_ROOT.iterdir()):
        if not section_dir.is_dir():
            continue
        section_title = read_title(section_dir / "_index.md") if (section_dir / "_index.md").is_file() else section_dir.name
        for sub_dir in sorted(section_dir.iterdir()):
            if sub_dir.is_dir() and (sub_dir / "_index.md").is_file():
                sub_title = read_title(sub_dir / "_index.md")
                items.append((f"{section_title} → {sub_title}", sub_dir))
    return items


def all_sections() -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    for section_dir in sorted(MENU_ROOT.iterdir()):
        if section_dir.is_dir() and (section_dir / "_index.md").is_file():
            items.append((read_title(section_dir / "_index.md"), section_dir))
    return items
