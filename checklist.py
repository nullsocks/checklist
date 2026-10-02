#!/usr/bin/env python3
"""checklist: a tiny click-to-tick scratchpad with several lists.

Everything lives in one plain Markdown file (default ~/agent_workspace/checklist.md):

    ## 📌 UI changes          <- pinned lists carry a pin and sit first
    - [ ] rounder corners
    - [x] cheat sheet

    ## ToDo
    - [ ] call the bank

Edit it by hand or let an agent add to it; the app picks changes up within a
second. Colours follow the liquid theme (~/.config/quickshell/palette.json).
Settings (word wrap, where the file lives) are in
~/.config/liquid-checklist/settings.json.

Top row:  ⌄ every list (pin / open)   names: click to open, click the open one
          to rename   …  more lists than fit   + new   ✎ delete mode   ⚙ settings
Bottom:   type + Enter to add          👁 show / hide ticked items

Keys:  click / Space  tick or untick      ↑ ↓ / Tab  move around
       right-click / e  edit an item in place (Enter saves, Esc cancels,
                        empty removes it)    Delete  remove item
       Ctrl+←/→       previous / next list   Esc     close a panel
       Ctrl+Q         quit
"""
import json, sys
from pathlib import Path

from rich.cells import cell_len
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Input, Static, TextArea

# ── settings ────────────────────────────────────────────────
SETTINGS = Path.home() / ".config/liquid-checklist/settings.json"
DEFAULT_FILE = Path.home() / "agent_workspace/checklist.md"
PALETTE = Path.home() / ".config/quickshell/palette.json"
PIN = "📌 "


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def write_settings(cfg: dict) -> None:
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(cfg, indent=2) + "\n")


CFG = read_json(SETTINGS)
# A path on the command line wins for that run; otherwise the saved setting.
FILE = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path(CFG.get("file", str(DEFAULT_FILE))).expanduser()


# ── the file ────────────────────────────────────────────────
def load() -> list[dict]:
    lists, cur = [], None
    if FILE.exists():
        for line in FILE.read_text().splitlines():
            if line.startswith("## "):
                name = line[3:].strip()
                pinned = name.startswith(PIN.strip())
                cur = {"name": name.removeprefix(PIN.strip()).strip(), "pinned": pinned, "items": []}
                lists.append(cur)
            elif line.lstrip()[:6] in ("- [ ] ", "- [x] ", "- [X] ", "* [ ] ", "* [x] "):
                if cur is None:
                    cur = {"name": "ToDo", "pinned": False, "items": []}
                    lists.append(cur)
                s = line.lstrip()
                cur["items"].append({"text": s[6:], "done": s[3] != " "})
    return lists or [{"name": "ToDo", "pinned": False, "items": []}]


def save(lists: list[dict]) -> None:
    out = []
    for l in lists:
        out.append(f"## {PIN if l.get('pinned') else ''}{l['name']}")
        out += [f"- [{'x' if i['done'] else ' '}] {i['text']}" for i in l["items"]]
        out.append("")
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text("\n".join(out))
    tmp.replace(FILE)


# ── look ────────────────────────────────────────────────────
P = read_json(PALETTE)
C = lambda k, d: P.get(k, d)
BASE, MANTLE, SURF0, SURF1 = C("base", "#1e1e2e"), C("mantle", "#181825"), C("surface0", "#313244"), C("surface1", "#45475a")
OVER0, SUB0, TEXT, RED = C("overlay0", "#6c7086"), C("subtext0", "#a6adc8"), C("text", "#cdd6f4"), C("red", "#f38ba8")
DEEP, ACCENT_T, BUBBLE = C("liquidDeep", "#533e79"), C("accentText", "#9a86cd"), C("liquidBubble", "#9a86cd")


def mix(a: str, b: str, t: float) -> str:
    """Blend two #rrggbb colours (t = how far toward b)."""
    ca, cb = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


FAINT = mix(mix(BASE, SURF0, 0.6), DEEP, 0.18)   # every other row: a touch lighter, a hint of plum

CSS = f"""
Screen {{ background: {BASE}; color: {TEXT}; }}
#bar {{ height: 1; background: {MANTLE}; }}
.list {{ width: auto; padding: 0 1; color: {SUB0}; }}
.list:hover {{ color: {TEXT}; }}
.list.on {{ color: {TEXT}; background: {DEEP}; text-style: bold; }}
.rename {{ width: 22; height: 1; border: none; padding: 0 1; background: {DEEP}; color: {TEXT}; }}
.fill {{ width: 1fr; }}
.icon {{ width: 3; content-align: center middle; color: {OVER0}; }}
.icon:hover, .icon.on {{ color: {TEXT}; }}
.plus {{ color: {ACCENT_T}; }}
.x {{ width: 2; color: {RED}; }}
.x:hover {{ background: {SURF0}; }}

EntryCard {{ align: center middle; background: {BASE} 60%; }}
#card {{ width: 90%; height: auto; max-height: 90%; padding: 1 2; background: {MANTLE}; border: round {DEEP}; color: {TEXT}; }}
#card.done {{ color: {OVER0}; text-style: strike; }}
.panel {{ display: none; height: auto; max-height: 10; padding: 0 1; background: {MANTLE}; border-bottom: solid {SURF0}; }}
#wrap {{ color: {TEXT}; }}
#wrap:hover, #grow:hover {{ background: {SURF0}; }}
#grow {{ color: {TEXT}; }}
.label {{ color: {OVER0}; margin-top: 1; }}
#path {{ height: 1; border: none; padding: 0; background: {SURF0}; color: {TEXT}; }}
MenuRow {{ height: 1; }}
MenuRow:hover {{ background: {SURF0}; }}
.pin {{ width: 3; color: {OVER0}; }}
.pin.on {{ color: {BUBBLE}; }}
.menuname {{ width: 1fr; color: {SUB0}; }}
.menuname.on {{ color: {TEXT}; text-style: bold; }}

#items {{ height: 1fr; scrollbar-size-vertical: 1; scrollbar-color: {DEEP}; scrollbar-background: {BASE}; }}
Item {{ height: auto; padding: 0 1; }}
Item:odd {{ background: {FAINT}; }}
Item:focus {{ background: {mix(SURF0, DEEP, 0.5)}; }}
Item .box {{ width: 2; color: {SURF1}; }}
Item.done .box {{ color: {BUBBLE}; }}
Item .text {{ width: 1fr; height: auto; }}
Item.done .text {{ color: {OVER0}; text-style: strike; }}
#items.nowrap Item .text {{ height: 1; text-wrap: nowrap; text-overflow: ellipsis; }}

#bottom {{ height: 1; dock: bottom; background: {MANTLE}; }}
#bottom:focus-within {{ background: {SURF0}; }}
#entry {{ width: 1fr; height: 1; border: none; padding: 0 1; background: transparent; color: {TEXT}; }}
#entry:focus {{ background: transparent; }}
#bottom {{ height: auto; max-height: 8; }}
GrowInput {{ height: 1; border: none; padding: 0 1; background: transparent; color: {TEXT}; scrollbar-size: 0 0; }}
GrowInput:focus {{ border: none; background: transparent; }}
.itemedit, .itemedit:focus {{ width: 1fr; height: 1; border: none; padding: 0; background: {SURF0}; color: {TEXT}; }}
.eye {{ width: 3; content-align: center middle; background: transparent; color: {OVER0}; }}
.eye:hover {{ color: {SUB0}; }}
"""

G_CHEVRON, G_CHEVRON_UP = "\U000F0140", "\U000F0143"
G_PENCIL, G_GEAR = "\U000F03EB", "\U000F0493"
G_EYE, G_EYE_OFF = "\U000F0208", "\U000F0209"
G_PIN, G_PIN_OFF = "\U000F0403", "\U000F0931"
G_BOX, G_BOX_DONE = "\U000F0131", "\U000F0132"


# ── widgets ─────────────────────────────────────────────────
class Click(Static):
    """A Static that runs a callback when clicked."""
    def __init__(self, text: str, action, **kw):
        super().__init__(text, **kw)
        self.action = action

    def on_click(self, event) -> None:
        event.stop()                        # handled here; don't also click what's behind
        self.action()


class EntryCard(ModalScreen):
    """The whole entry, floating as a card. Any click or Esc closes it."""
    BINDINGS = [Binding("escape", "dismiss", show=False)]

    def __init__(self, text: str, done: bool):
        super().__init__()
        self.text, self.done = text, done

    def compose(self) -> ComposeResult:
        yield Static(self.text, id="card", classes="done" if self.done else "", markup=False)

    def on_click(self) -> None:
        self.dismiss()


class GrowInput(TextArea):
    """A text box that grows downward as you type (wraps instead of scrolling).
    Enter submits, like a one-line input; it reads and writes `value`."""
    class Submitted(Message):
        def __init__(self, input: "GrowInput", value: str):
            super().__init__()
            self.input, self.value = input, value

    def __init__(self, value: str = "", **kw):
        super().__init__(value, soft_wrap=True, compact=True, show_line_numbers=False,
                         highlight_cursor_line=False, **kw)

    @property
    def value(self) -> str:
        return self.text

    @value.setter
    def value(self, v: str) -> None:
        self.text = v
        self.move_cursor(self.document.end)

    # Height follows the wrapped text: one row per line, up to 8.
    def fit(self) -> None:
        self.styles.height = max(1, min(8, self.wrapped_document.height))

    def on_mount(self) -> None:
        self.call_after_refresh(self.fit)

    def on_resize(self) -> None:
        self.call_after_refresh(self.fit)

    def on_text_area_changed(self) -> None:
        self.call_after_refresh(self.fit)

    async def _on_key(self, event) -> None:
        if event.key == "enter":
            event.stop(); event.prevent_default()
            self.post_message(self.Submitted(self, self.text.replace("\n", " ")))
            return
        await super()._on_key(event)


def text_box(value: str = "", grow: bool = False, **kw):
    """One-line Input, or the growing box when that setting is on."""
    return GrowInput(value, **kw) if grow else Input(value, compact=True, **kw)


class Item(Horizontal, can_focus=True):
    """One item: a box and its text. The text wraps (or not, per settings)."""
    BINDINGS = [Binding("space", "toggle", show=False),
                Binding("down", "app.focus_next", show=False),
                Binding("up", "app.focus_previous", show=False)]

    def __init__(self, idx: int, text: str, done: bool):
        super().__init__(classes="done" if done else "")
        self.idx, self.label, self.done = idx, text, done

    def compose(self) -> ComposeResult:
        yield Click(G_BOX_DONE if self.done else G_BOX, lambda: self.app.toggle_item(self), classes="box")
        yield Static(self.label, classes="text", markup=False)

    def set_done(self, done: bool) -> None:
        self.done = done
        self.set_class(done, "done")
        self.query_one(".box", Static).update(G_BOX_DONE if done else G_BOX)

    def on_click(self, event) -> None:
        if self.query(".itemedit"):
            return                          # clicks inside the editor stay there
        if event.button == 3:
            self.start_edit()               # right-click: edit the text in place
        else:
            self.focus()                    # click the text: the whole entry as a card
            self.app.push_screen(EntryCard(self.label, self.done))

    def start_edit(self) -> None:
        if self.query(".itemedit"):
            return
        self.query_one(".text").display = False
        box = text_box(self.label, self.app.grow, classes="itemedit")
        self.mount(box)
        self.app.item_editing = self
        box.focus()

    def stop_edit(self) -> None:
        for box in self.query(".itemedit"):
            box.remove()
        self.query_one(".text").display = True
        if self.app.item_editing is self:
            self.app.item_editing = None

    def action_toggle(self) -> None:
        self.app.toggle_item(self)


class MenuRow(Horizontal):
    """A line in the chevron menu: pin + name."""
    def __init__(self, idx: int, name: str, pinned: bool, current: bool):
        super().__init__()
        self.idx, self.name_, self.pinned, self.current = idx, name, pinned, current

    def compose(self) -> ComposeResult:
        yield Click(G_PIN if self.pinned else G_PIN_OFF, lambda: self.app.toggle_pin(self.idx),
                    classes="pin on" if self.pinned else "pin")
        yield Click(self.name_, lambda: self.app.pick_list(self.idx),
                    classes="menuname on" if self.current else "menuname", markup=False)


# ── the app ─────────────────────────────────────────────────
class Checklist(App):
    CSS = CSS
    TITLE = "checklist"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("ctrl+left", "prev_list", "prev", priority=True),
        Binding("ctrl+right", "next_list", "next", priority=True),
        Binding("delete", "delete_item", "remove item"),
        Binding("e", "edit_item", "edit item"),
        Binding("ctrl+q", "quit", "quit", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.lists = load()
        self.cur = 0
        self.editing = None        # item index being edited in the entry line
        self.renaming = False
        self.hide_done = False
        self.deleting = False
        self.panel = ""            # "", "menu" or "settings"
        self.wrap = CFG.get("wrap", True)
        self.grow = CFG.get("grow", False)
        self.item_editing = None   # Item being edited in place
        self.mtime = FILE.stat().st_mtime if FILE.exists() else 0

    def compose(self) -> ComposeResult:
        yield Horizontal(id="bar")
        yield VerticalScroll(id="menu", classes="panel")
        with VerticalScroll(id="settings", classes="panel"):
            yield Click("", self.toggle_wrap, id="wrap")
            yield Click("", self.toggle_grow, id="grow")
            yield Static("save file", classes="label")
            yield Input(str(FILE), id="path", compact=True)
        yield VerticalScroll(id="items")
        with Horizontal(id="bottom"):
            yield text_box(placeholder="+ add…", id="entry", grow=self.grow)
            yield Click(G_EYE, self.toggle_done, classes="eye")

    def on_mount(self) -> None:
        if not FILE.exists():
            save(self.lists)
        self.apply_wrap()
        self.refresh_items()
        self.query_one("#entry").focus()
        self.set_interval(1.0, self.watch_file)
        self.call_after_refresh(self.draw_bar)

    def on_resize(self) -> None:
        self.call_after_refresh(self.draw_bar, self.renaming)

    # ── the top row ──
    def draw_bar(self, rename: bool = False) -> None:
        """Lists that fit, then … for the rest. The open list always shows."""
        bar = self.query_one("#bar", Horizontal)
        width = bar.size.width or self.size.width
        tab_w = lambda i: (24 if rename and i == self.cur else cell_len(self.lists[i]["name"]) + 2) + (2 if self.deleting else 0)
        room = width - 3 - 9 - 3          # chevron, + ✎ ⚙, and room for …
        shown, used = [], 0
        for i in range(len(self.lists)):
            if used + tab_w(i) > room:
                break
            shown.append(i); used += tab_w(i)
        if self.cur not in shown:         # make room for the open list
            while shown and used + tab_w(self.cur) > room:
                used -= tab_w(shown.pop())
            shown.append(self.cur)
        hidden = len(shown) < len(self.lists)

        widgets = [Click(G_CHEVRON_UP if self.panel == "menu" else G_CHEVRON, self.toggle_menu,
                         classes="icon on" if self.panel == "menu" else "icon")]
        for i in shown:
            l = self.lists[i]
            if rename and i == self.cur:
                self.rename_box = Input(l["name"], classes="rename", compact=True, select_on_focus=True)
                widgets.append(self.rename_box)
            else:
                widgets.append(Click(l["name"], lambda i=i: self.clicked_list(i),
                                     classes="list on" if i == self.cur else "list", markup=False))
            if self.deleting:
                widgets.append(Click("×", lambda i=i: self.delete_list(i), classes="x"))
        if hidden:
            widgets.append(Click("…", self.toggle_menu, classes="icon"))
        widgets += [Static("", classes="fill"),
                    Click("+", self.new_list, classes="icon plus"),
                    Click(G_PENCIL, self.toggle_deleting, classes="icon on" if self.deleting else "icon"),
                    Click(G_GEAR, self.toggle_settings, classes="icon on" if self.panel == "settings" else "icon")]
        with self.batch_update():
            bar.remove_children()
            bar.mount_all(widgets)
        self.renaming = rename
        if rename:
            self.call_after_refresh(self.rename_box.focus)

    def clicked_list(self, i: int) -> None:
        if i == self.cur:
            self.draw_bar(rename=True)
        else:
            self.cur = i
            self.draw_bar(); self.refresh_items()

    def new_list(self) -> None:
        self.lists.append({"name": "new list", "pinned": False, "items": []})
        self.cur = len(self.lists) - 1
        self.persist(); self.refresh_items()
        self.draw_bar(rename=True)          # straight into naming it

    def end_rename(self, name: str | None) -> None:
        if name:
            self.lists[self.cur]["name"] = name
            self.persist()
        self.draw_bar()
        self.query_one("#entry").focus()

    def toggle_deleting(self) -> None:
        self.deleting = not self.deleting
        self.draw_bar()

    def delete_list(self, i: int) -> None:
        # A safety net, not a menu: deleted lists are appended to
        # checklist.deleted.md next to the checklist.
        gone = self.lists.pop(i)
        with FILE.with_name(FILE.stem + ".deleted.md").open("a") as f:
            f.write(f"## {gone['name']}\n" + "".join(f"- [{'x' if it['done'] else ' '}] {it['text']}\n" for it in gone["items"]) + "\n")
        if not self.lists:
            self.lists = [{"name": "ToDo", "pinned": False, "items": []}]
            self.deleting = False
        if self.cur >= i and self.cur > 0:
            self.cur -= 1
        self.persist(); self.draw_bar(); self.refresh_items()

    # ── panels (menu / settings): one at a time, Esc closes ──
    def show_panel(self, name: str) -> None:
        self.panel = "" if self.panel == name else name
        self.query_one("#menu").display = self.panel == "menu"
        self.query_one("#settings").display = self.panel == "settings"
        if self.panel == "menu":
            self.fill_menu()
        if self.panel == "settings":
            self.query_one("#path", Input).value = str(FILE)
        self.draw_bar()

    def toggle_menu(self) -> None: self.show_panel("menu")
    def toggle_settings(self) -> None: self.show_panel("settings")

    def fill_menu(self) -> None:
        menu = self.query_one("#menu", VerticalScroll)
        with self.batch_update():
            menu.remove_children()
            menu.mount_all([MenuRow(i, l["name"], l.get("pinned", False), i == self.cur) for i, l in enumerate(self.lists)])

    def pick_list(self, i: int) -> None:
        self.cur = i
        self.show_panel("menu")             # closes it
        self.refresh_items()

    def toggle_pin(self, i: int) -> None:
        """Pinned lists sit first, in the order you pinned them."""
        l = self.lists.pop(i)
        current = self.lists[self.cur if self.cur < i else self.cur - 1] if self.cur != i else l
        l["pinned"] = not l.get("pinned", False)
        n_pinned = sum(1 for x in self.lists if x.get("pinned"))
        self.lists.insert(n_pinned, l)      # end of the pinned block / start of the rest
        self.cur = self.lists.index(current)
        self.persist(); self.fill_menu(); self.draw_bar()

    # ── settings ──
    def save_cfg(self) -> None:
        CFG["wrap"] = self.wrap
        CFG["grow"] = self.grow
        CFG["file"] = str(FILE)
        write_settings(CFG)

    def apply_wrap(self) -> None:
        self.query_one("#wrap", Click).update(f"word wrap      {'on' if self.wrap else 'off'}")
        self.query_one("#grow", Click).update(f"growing input  {'on' if self.grow else 'off'}")
        self.query_one("#items").set_class(not self.wrap, "nowrap")

    def toggle_grow(self) -> None:
        """Swap the add box between one scrolling line and a growing box."""
        self.grow = not self.grow
        self.apply_wrap(); self.save_cfg()
        old = self.query_one("#entry")
        new = text_box(old.value, self.grow, placeholder="+ add…", id="entry")

        async def swap() -> None:           # the old box must be gone before the new one (same id)
            await old.remove()
            await self.query_one("#bottom").mount(new, before=0)
        self.call_later(swap)

    def toggle_wrap(self) -> None:
        self.wrap = not self.wrap
        self.apply_wrap(); self.save_cfg()

    def move_file(self, new: str) -> None:
        """Point the checklist at another file. An existing checklist there is
        opened; otherwise your current lists are saved there."""
        global FILE
        path = Path(new).expanduser()
        if path.is_dir():
            path = path / "checklist.md"
        if path == FILE:
            return
        FILE = path
        if path.exists():
            self.lists = load()
        else:
            save(self.lists)
        self.cur = 0
        self.mtime = FILE.stat().st_mtime
        self.save_cfg()
        self.query_one("#path", Input).value = str(FILE)
        self.draw_bar(); self.refresh_items()

    # ── items ──
    def refresh_items(self) -> None:
        box = self.query_one("#items", VerticalScroll)
        items = self.lists[self.cur]["items"]
        # Open items first, ticked ones sink to the bottom.
        order = [i for i, it in enumerate(items) if not it["done"]]
        if not self.hide_done:
            order += [i for i, it in enumerate(items) if it["done"]]
        with self.batch_update():
            box.remove_children()
            box.mount_all([Item(i, items[i]["text"], items[i]["done"]) for i in order])

    def toggle_item(self, item: Item) -> None:
        done = not item.done
        self.lists[self.cur]["items"][item.idx]["done"] = done
        item.set_done(done)
        self.persist()
        if self.hide_done and done:
            item.remove()

    def toggle_done(self) -> None:
        self.hide_done = not self.hide_done
        # Eye open = ticked items showing; eye crossed out = hidden.
        self.query_one(".eye", Click).update(G_EYE_OFF if self.hide_done else G_EYE)
        self.refresh_items()

    def persist(self) -> None:
        save(self.lists)
        self.mtime = FILE.stat().st_mtime

    # Someone (you in an editor, another window, or an agent) changed the file.
    def watch_file(self) -> None:
        try:
            m = FILE.stat().st_mtime
        except FileNotFoundError:
            return
        if m != self.mtime and not self.renaming and self.editing is None and self.item_editing is None:
            self.mtime = m
            self.lists = load()
            self.cur = min(self.cur, len(self.lists) - 1)
            self.draw_bar(); self.refresh_items()
            if self.panel == "menu":
                self.fill_menu()

    # ── events ──
    def on_grow_input_submitted(self, event: GrowInput.Submitted) -> None:
        self.on_input_submitted(event)

    def finish_item_edit(self, text: str | None) -> None:
        it = self.item_editing
        if it is None:
            return
        items = self.lists[self.cur]["items"]
        it.stop_edit()
        if text is None:
            return                          # Esc: unchanged
        if text:
            items[it.idx]["text"] = text
        else:
            items.pop(it.idx)
        self.persist(); self.refresh_items()

    def on_input_submitted(self, event) -> None:
        text = event.value.strip()
        if event.input.has_class("itemedit"):
            self.finish_item_edit(text)
            return
        if event.input.has_class("rename"):
            self.end_rename(text)
            return
        if event.input.id == "path":
            if text:
                self.move_file(text)
            return
        entry = event.input
        entry.value = ""
        items = self.lists[self.cur]["items"]
        if self.editing is not None:
            if text:
                items[self.editing]["text"] = text
            else:
                items.pop(self.editing)
            self.editing = None
            entry.placeholder = "+ add…"
        elif text:
            items.append({"text": text, "done": False})
        else:
            return
        self.persist(); self.refresh_items()
        self.query_one("#items", VerticalScroll).scroll_end(animate=False)

    # Clicking away from a rename keeps what was typed.
    def on_descendant_blur(self, event) -> None:
        if self.renaming and event.widget.has_class("rename"):
            self.end_rename(event.widget.value.strip())
        elif event.widget.has_class("itemedit") and self.item_editing is not None:
            self.finish_item_edit(event.widget.value.strip())

    def on_key(self, event) -> None:
        if event.key != "escape":
            return
        if self.item_editing is not None:
            self.finish_item_edit(None)
        elif self.panel:
            self.show_panel(self.panel)
            self.query_one("#entry").focus()
        elif self.renaming:
            self.renaming = False
            self.end_rename(None)
        elif self.editing is not None:
            self.editing = None
            entry = self.query_one("#entry")
            entry.value, entry.placeholder = "", "+ add…"

    # ── keys ──
    def switch(self, step: int) -> None:
        self.cur = (self.cur + step) % len(self.lists)
        self.draw_bar(); self.refresh_items()

    def action_prev_list(self) -> None: self.switch(-1)
    def action_next_list(self) -> None: self.switch(1)

    def focused_item(self):
        return self.focused if isinstance(self.focused, Item) else None

    def action_delete_item(self) -> None:
        if (it := self.focused_item()):
            self.lists[self.cur]["items"].pop(it.idx)
            self.persist(); self.refresh_items()

    def action_edit_item(self) -> None:
        if (it := self.focused_item()):
            it.start_edit()


if __name__ == "__main__":
    Checklist().run()
