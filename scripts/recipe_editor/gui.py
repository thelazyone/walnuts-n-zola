"""Tkinter GUI for editing Lesnack menu content."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Any

from . import content


class ConfirmDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, title: str, message: str) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = False
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=message, wraplength=360, justify=tk.LEFT).pack(anchor=tk.W)
        ttk.Label(
            frame,
            text="This cannot be undone.",
            foreground="#8b4513",
        ).pack(anchor=tk.W, pady=(8, 16))

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Delete", command=self._confirm).pack(side=tk.RIGHT)

        self.bind("<Escape>", lambda _e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx() + 80}+{parent.winfo_rooty() + 80}")

    def _confirm(self) -> None:
        self.result = True
        self.destroy()

    def _cancel(self) -> None:
        self.result = False
        self.destroy()


class MoveDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, title: str, options: list[tuple[str, Any]]) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.selected: Any = None
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Move to:").pack(anchor=tk.W)
        labels = [label for label, _ in options]
        self.combo = ttk.Combobox(frame, values=labels, state="readonly", width=48)
        if labels:
            self.combo.current(0)
        self.combo.pack(fill=tk.X, pady=(8, 16))

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(buttons, text="Move", command=self._ok).pack(side=tk.RIGHT)
        self._options = options

        self.bind("<Escape>", lambda _e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _ok(self) -> None:
        idx = self.combo.current()
        if idx >= 0:
            self.selected = self._options[idx][1]
        self.destroy()

    def _cancel(self) -> None:
        self.selected = None
        self.destroy()


class RecipeEditorApp(tk.Tk):
    DIETARY = ["meat", "vegan", "gluten-free", "dairy-free"]

    def __init__(self) -> None:
        super().__init__()
        self.title("Lesnack Recipe Editor")
        self.geometry("980x640")
        self.minsize(820, 520)

        self._tree_nodes: dict[str, content.TreeNode] = {}
        self._current_node: content.TreeNode | None = None
        self._dirty = False
        self._form_vars: dict[str, Any] = {}

        self._build_toolbar()
        self._build_main()
        self._build_form()
        self.refresh_tree()
        self._show_empty_form()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(8, 8, 8, 0))
        bar.pack(fill=tk.X)

        ttk.Button(bar, text="Refresh", command=self.refresh_tree).pack(side=tk.LEFT)
        ttk.Button(bar, text="Sync folders", command=self.sync_folders).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(bar, text="Add section", command=self.add_section).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(bar, text="Add subsection", command=self.add_subsection).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(bar, text="Add recipe", command=self.add_recipe).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(bar, text="Duplicate", command=self.duplicate_item).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(bar, text="Move…", command=self.move_item).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(bar, text="Delete", command=self.delete_item).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(bar, text="Save", command=self.save_current).pack(side=tk.RIGHT)

    def _build_main(self) -> None:
        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Frame(paned, padding=(0, 0, 4, 0))
        paned.add(left, weight=1)

        ttk.Label(left, text="Menu").pack(anchor=tk.W)
        tree_frame = ttk.Frame(left)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        right = ttk.Frame(paned, padding=(4, 0, 0, 0))
        paned.add(right, weight=2)
        self.form_outer = right

    def _build_form(self) -> None:
        self.form_canvas = tk.Canvas(self.form_outer, highlightthickness=0)
        form_scroll = ttk.Scrollbar(self.form_outer, orient=tk.VERTICAL, command=self.form_canvas.yview)
        self.form_frame = ttk.Frame(self.form_canvas, padding=8)
        self.form_window = self.form_canvas.create_window((0, 0), window=self.form_frame, anchor=tk.NW)
        self.form_canvas.configure(yscrollcommand=form_scroll.set)
        self.form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        form_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.form_frame.bind("<Configure>", self._on_form_configure)
        self.form_canvas.bind("<Configure>", self._on_canvas_configure)
        self.form_canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

        self.form_title = ttk.Label(self.form_frame, text="Select an item", font=("Segoe UI", 12, "bold"))
        self.form_title.pack(anchor=tk.W, pady=(0, 12))
        self.fields_frame = ttk.Frame(self.form_frame)
        self.fields_frame.pack(fill=tk.BOTH, expand=True)

    def _on_form_configure(self, _event: tk.Event) -> None:
        self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.form_canvas.itemconfig(self.form_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.form_canvas.winfo_containing(event.x_root, event.y_root) is self.form_canvas:
            self.form_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _clear_fields(self) -> None:
        for child in self.fields_frame.winfo_children():
            child.destroy()
        self._form_vars = {}

    def _field(self, label: str, key: str, default: str = "") -> ttk.Entry:
        ttk.Label(self.fields_frame, text=label).pack(anchor=tk.W, pady=(8, 2))
        var = tk.StringVar(value=default)
        entry = ttk.Entry(self.fields_frame, textvariable=var, width=60)
        entry.pack(fill=tk.X)
        entry.bind("<KeyRelease>", lambda _e: self._mark_dirty())
        self._form_vars[key] = var
        return entry

    def _text_field(self, label: str, key: str, default: str = "", height: int = 6) -> tk.Text:
        ttk.Label(self.fields_frame, text=label).pack(anchor=tk.W, pady=(8, 2))
        text = tk.Text(self.fields_frame, height=height, wrap=tk.WORD, width=60)
        text.pack(fill=tk.BOTH, expand=True)
        if default:
            text.insert("1.0", default)
        text.bind("<KeyRelease>", lambda _e: self._mark_dirty())
        self._form_vars[key] = text
        return text

    def _mark_dirty(self) -> None:
        self._dirty = True
        if self._current_node:
            self.title(f"Lesnack Recipe Editor — {self._current_node.title} *")
        else:
            self.title("Lesnack Recipe Editor *")

    def _show_empty_form(self) -> None:
        self._clear_fields()
        self.form_title.config(text="Select an item")
        ttk.Label(
            self.fields_frame,
            text="Choose a section, subsection, or recipe in the tree.",
            foreground="#666",
        ).pack(anchor=tk.W)

    def _show_section_form(self, node: content.TreeNode) -> None:
        front, _ = content.parse_markdown(node.path)
        self._clear_fields()
        self.form_title.config(text=f"Section: {node.title}")
        self._field("Title", "title", str(front.get("title") or ""))
        self._field("Description (shown on All dishes)", "description", str(front.get("description") or ""))
        self._field("Weight (nav order)", "weight", str(front.get("weight") or ""))

    def _show_subsection_form(self, node: content.TreeNode) -> None:
        front, _ = content.parse_markdown(node.path)
        self._clear_fields()
        self.form_title.config(text=f"Subsection: {node.title}")
        self._field("Title", "title", str(front.get("title") or ""))
        self._field("Weight", "weight", str(front.get("weight") or ""))

    def _show_recipe_form(self, node: content.TreeNode) -> None:
        front, body = content.parse_markdown(node.path)
        extra = front.get("extra") or {}
        dietary = extra.get("dietary") or []

        self._clear_fields()
        self.form_title.config(text=f"Recipe: {node.title}")

        title_entry = self._field("Title", "title", str(front.get("title") or ""))
        self._field("Description (menu line)", "description", str(front.get("description") or ""))
        self._field("URL path", "path", str(front.get("path") or ""))
        self._field("Weight", "weight", str(front.get("weight") or ""))

        def autofill_path() -> None:
            title = self._form_vars["title"].get().strip()
            if title:
                self._form_vars["path"].set(content.slugify(title))
                self._mark_dirty()

        ttk.Button(self.fields_frame, text="Generate path from title", command=autofill_path).pack(
            anchor=tk.W, pady=(4, 0)
        )

        ttk.Label(self.fields_frame, text="Dietary flags").pack(anchor=tk.W, pady=(12, 2))
        diet_frame = ttk.Frame(self.fields_frame)
        diet_frame.pack(anchor=tk.W)
        diet_vars: dict[str, tk.BooleanVar] = {}
        for flag in self.DIETARY:
            var = tk.BooleanVar(value=flag in dietary)
            diet_vars[flag] = var
            ttk.Checkbutton(diet_frame, text=flag, variable=var, command=self._mark_dirty).pack(side=tk.LEFT, padx=(0, 12))
        self._form_vars["dietary"] = diet_vars

        self._text_field("Ingredients", "ingredients", str(extra.get("ingredients") or ""), height=5)
        self._text_field("Notes", "notes", str(extra.get("notes") or ""), height=3)
        self._text_field("Body (method, story…)", "body", body, height=8)

        title_entry.focus_set()

    def refresh_tree(self) -> None:
        selected = self.tree.selection()
        selected_rel = None
        if selected and selected[0] in self._tree_nodes:
            selected_rel = self._tree_nodes[selected[0]].rel

        for item in self.tree.get_children():
            self.tree.delete(item)
        self._tree_nodes.clear()

        root = content.scan_tree()
        menu_id = self.tree.insert("", tk.END, text="All dishes (menu root)", open=True)
        self._tree_nodes[menu_id] = content.TreeNode(kind="menu", path=content.MENU_ROOT, title="Menu")

        def add_children(parent_id: str, nodes: list[content.TreeNode]) -> None:
            for node in nodes:
                icon = {"section": "§", "subsection": "·", "recipe": "◦"}.get(node.kind, "")
                item_id = self.tree.insert(parent_id, tk.END, text=f"{icon} {node.title}", open=True)
                self._tree_nodes[item_id] = node
                if node.children:
                    add_children(item_id, node.children)

        add_children(menu_id, root.children)

        if selected_rel:
            for item_id, node in self._tree_nodes.items():
                if node.rel == selected_rel:
                    self.tree.selection_set(item_id)
                    self.tree.see(item_id)
                    break

        self._dirty = False
        self.title("Lesnack Recipe Editor")

    def _on_tree_select(self, _event: tk.Event | None = None) -> None:
        if self._dirty:
            if not messagebox.askyesno("Unsaved changes", "Discard unsaved changes?"):
                return
        selection = self.tree.selection()
        if not selection:
            self._current_node = None
            self._show_empty_form()
            return
        node = self._tree_nodes.get(selection[0])
        if not node or node.kind == "menu":
            self._current_node = None
            self._show_empty_form()
            return
        self._current_node = node
        self._dirty = False
        self.title(f"Lesnack Recipe Editor — {node.title}")
        if node.kind == "section":
            self._show_section_form(node)
        elif node.kind == "subsection":
            self._show_subsection_form(node)
        elif node.kind == "recipe":
            self._show_recipe_form(node)

    def _selected_node(self) -> content.TreeNode | None:
        selection = self.tree.selection()
        if not selection:
            return None
        node = self._tree_nodes.get(selection[0])
        if not node or node.kind == "menu":
            return None
        return node

    def save_current(self) -> None:
        node = self._current_node
        if not node:
            messagebox.showinfo("Save", "Nothing selected.")
            return
        try:
            if node.kind == "section":
                front, _ = content.parse_markdown(node.path)
                front["title"] = self._form_vars["title"].get().strip()
                front["description"] = self._form_vars["description"].get().strip()
                front["weight"] = int(self._form_vars["weight"].get().strip() or "0")
                node.path = content.save_section_index(node.path, front)
                node.title = front["title"]
            elif node.kind == "subsection":
                front, _ = content.parse_markdown(node.path)
                front["title"] = self._form_vars["title"].get().strip()
                front["weight"] = int(self._form_vars["weight"].get().strip() or "0")
                front.setdefault("render", False)
                front.setdefault("sort_by", "weight")
                node.path = content.save_subsection_index(node.path, front)
                node.title = front["title"]
            elif node.kind == "recipe":
                front, _ = content.parse_markdown(node.path)
                extra = dict(front.get("extra") or {})
                front["title"] = self._form_vars["title"].get().strip()
                front["description"] = self._form_vars["description"].get().strip()
                front["path"] = self._form_vars["path"].get().strip() or content.slugify(front["title"])
                front["weight"] = int(self._form_vars["weight"].get().strip() or "100")
                front.setdefault("template", "recipe.html")
                dietary = [flag for flag, var in self._form_vars["dietary"].items() if var.get()]
                extra["dietary"] = dietary
                ingredients = self._form_vars["ingredients"].get("1.0", tk.END).strip()
                notes = self._form_vars["notes"].get("1.0", tk.END).strip()
                body = self._form_vars["body"].get("1.0", tk.END).strip()
                if ingredients:
                    extra["ingredients"] = ingredients
                else:
                    extra.pop("ingredients", None)
                if notes:
                    extra["notes"] = notes
                else:
                    extra.pop("notes", None)
                front["extra"] = extra
                new_path = content.save_recipe(node.path, front, body)
                node.path = new_path
                node.title = front["title"]
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return

        self._dirty = False
        self.title("Lesnack Recipe Editor")
        self.refresh_tree()
        messagebox.showinfo("Saved", "Changes saved.")

    def add_section(self) -> None:
        name = simpledialog.askstring("New section", "Section name:", parent=self)
        if not name or not name.strip():
            return
        try:
            content.create_section(name.strip())
        except FileExistsError:
            messagebox.showerror("Error", "A section with that folder name already exists.")
            return
        self.refresh_tree()

    def sync_folders(self) -> None:
        try:
            changes = content.sync_all_folder_names()
        except Exception as exc:
            messagebox.showerror("Sync failed", str(exc))
            return
        self.refresh_tree()
        if changes:
            messagebox.showinfo("Folders synced", "\n".join(changes))
        else:
            messagebox.showinfo("Folders synced", "All folder names already match their titles.")

    def add_subsection(self) -> None:
        node = self._selected_node()
        if not node or node.kind != "section":
            messagebox.showinfo("Add subsection", "Select a section first.")
            return
        name = simpledialog.askstring("New subsection", "Subsection name:", parent=self)
        if not name or not name.strip():
            return
        try:
            content.create_subsection(node.path.parent, name.strip())
        except FileExistsError:
            messagebox.showerror("Error", "A subsection with that folder name already exists.")
            return
        self.refresh_tree()

    def add_recipe(self) -> None:
        node = self._selected_node()
        if not node or node.kind != "subsection":
            messagebox.showinfo("Add recipe", "Select a subsection first.")
            return
        name = simpledialog.askstring("New recipe", "Recipe title:", parent=self)
        if not name or not name.strip():
            return
        content.create_recipe(node.path.parent, name.strip())
        self.refresh_tree()

    def duplicate_item(self) -> None:
        node = self._selected_node()
        if not node or node.kind != "recipe":
            messagebox.showinfo("Duplicate", "Select a recipe to duplicate.")
            return
        content.duplicate_recipe(node.path)
        self.refresh_tree()

    def move_item(self) -> None:
        node = self._selected_node()
        if not node:
            return
        if node.kind == "recipe":
            options = content.all_subsections()
            dialog = MoveDialog(self, "Move recipe", options)
            self.wait_window(dialog)
            if dialog.selected is None:
                return
            try:
                content.move_recipe(node.path, dialog.selected)
            except Exception as exc:
                messagebox.showerror("Move failed", str(exc))
                return
        elif node.kind == "subsection":
            options = content.all_sections()
            dialog = MoveDialog(self, "Move subsection", options)
            self.wait_window(dialog)
            if dialog.selected is None:
                return
            try:
                content.move_subsection(node.path, dialog.selected)
            except Exception as exc:
                messagebox.showerror("Move failed", str(exc))
                return
        else:
            messagebox.showinfo("Move", "Only recipes and subsections can be moved.")
            return
        self.refresh_tree()

    def delete_item(self) -> None:
        node = self._selected_node()
        if not node:
            return
        if node.kind == "section" and node.children:
            msg = f"Delete section “{node.title}” and ALL its subsections and recipes?"
        elif node.kind == "subsection" and node.children:
            msg = f"Delete subsection “{node.title}” and ALL its recipes?"
        else:
            msg = f"Delete “{node.title}”?"
        dialog = ConfirmDialog(self, "Confirm delete", msg)
        self.wait_window(dialog)
        if not dialog.result:
            return
        try:
            content.delete_node(node)
        except Exception as exc:
            messagebox.showerror("Delete failed", str(exc))
            return
        self._current_node = None
        self._dirty = False
        self.refresh_tree()
        self._show_empty_form()

    def _on_close(self) -> None:
        if self._dirty:
            if not messagebox.askyesno("Unsaved changes", "Discard unsaved changes and quit?"):
                return
        self.destroy()


def run() -> None:
    app = RecipeEditorApp()
    app.mainloop()
