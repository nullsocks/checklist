#!/usr/bin/env python3
"""checklist: a tiny click-to-tick scratchpad with several lists.

Everything lives in one plain Markdown file (default ~/agent_workspace/checklist.md):

    ## 📌 UI changes          <- pinned lists carry a pin and sit first
    - [ ] ! rounder corners   <- "! " marks a priority item
    - [x] cheat sheet

    ## ToDo
    - [ ] call the bank

Edit it by hand or let an agent add to it; the app picks changes up within a
second. Colours follow the liquid theme (~/.config/quickshell/palette.json).
Settings and view state (word wrap, growing input, show ticked, the open
list, where the file lives) are in ~/.config/liquid-checklist/settings.json.

Top row:  ⌄ every list (pin, edit, open)   names: click to open, click the
          open one to rename   …  more lists than fit   + new   ⚙ settings
Bottom:   the add box (always ready: just type)   ! add the next item as priority

Keys:  type + Enter     add          Shift+Enter (or start with "!")  add as priority
       ↑ from the box   into the list    ↑ ↓  move    Space  tick    Enter  open card
       e                edit in place    !  priority    Del  remove
       Ctrl+C           the list menu (↑ ↓ Enter)       Ctrl+←/→  previous / next list
       Esc              close / back to the add box     Ctrl+Q  quit
Mouse: tick box ticks; click an entry for its card (click the card's text to
       edit it, its ! for priority); right-click an entry to edit in place;
       click empty space to get back to the add box.
"""
import json, sys
from pathlib import Path

from rich.cells import cell_len
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Input, Static, TextArea

# ── settings ────────────────────────────────────────────────
SETTINGS = Path.home() / ".config/liquid-checklist/settings.json"
DEFAULT_FILE = Path.home() / "agent_workspace/checklist.md"
PALETTE = Path.home() / ".config/quickshell/palette.json"
PIN = "📌"
PRIO = "! "


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
def new_list(name: str) -> dict:
    return {"name": name, "pinned": False, "items": []}


def load() -> list[dict]:
    lists, cur = [], None
    if FILE.exists():
        for line in FILE.read_text().splitlines():
            if line.startswith("## "):
                name = line[3:].strip()
                cur = new_list(name.removeprefix(PIN).strip())
                cur["pinned"] = name.startswith(PIN)
                lists.append(cur)
            elif line.lstrip()[:6] in ("- [ ] ", "- [x] ", "- [X] ", "* [ ] ", "* [x] "):
                if cur is None:
                    cur = new_list("ToDo")
                    lists.append(cur)
                s = line.lstrip()
                text = s[6:]
                prio = text.startswith(PRIO)
                cur["items"].append({"text": text.removeprefix(PRIO), "done": s[3] != " ", "prio": prio})
    return lists or [new_list("ToDo")]


def save(lists: list[dict]) -> None:
    out = []
    for l in lists:
        out.append(f"## {PIN + ' ' if l.get('pinned') else ''}{l['name']}")
        out += [f"- [{'x' if i['done'] else ' '}] {PRIO if i.get('prio') else ''}{i['text']}" for i in l["items"]]
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
FOCUS = mix(SURF0, DEEP, 0.5)

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

#items {{ height: 1fr; scrollbar-size-vertical: 1; scrollbar-color: {DEEP}; scrollbar-background: {BASE}; }}
Item {{ height: auto; padding: 0 1; }}
Item:odd {{ background: {FAINT}; }}
Item:focus {{ background: {FOCUS}; }}
Item .box {{ width: 2; color: {SURF1}; }}
Item.done .box {{ color: {BUBBLE}; }}
Item.prio .box {{ color: {RED}; }}
Item .text {{ width: 1fr; height: auto; }}
Item.done .text {{ color: {OVER0}; text-style: strike; }}
#items.nowrap Item .text {{ height: 1; text-wrap: nowrap; text-overflow: ellipsis; }}
.itemedit, .itemedit:focus {{ width: 1fr; height: 1; border: none; padding: 0; background: {SURF0}; color: {TEXT}; }}

#bottom {{ height: auto; max-height: 8; dock: bottom; background: {MANTLE}; }}
#bottom:focus-within {{ background: {SURF0}; }}
#entry {{ width: 1fr; height: 1; border: none; padding: 0 1; background: transparent; color: {TEXT}; }}
#entry:focus {{ background: transparent; }}
GrowInput {{ height: 1; border: none; padding: 0 1; background: transparent; color: {TEXT}; scrollbar-size: 0 0; }}
GrowInput:focus {{ border: none; background: transparent; }}
.bang {{ width: 3; content-align: center top; background: transparent; color: {OVER0}; }}
.bang:hover {{ color: {SUB0}; }}
.bang.on {{ color: {RED}; }}

/* overlays: a click outside closes them and goes no further */
Overlay {{ background: {C("crust", "#11111b")} 75%; }}
#menu {{ width: 34; height: auto; max-height: 80%; margin: 1 0 0 0; background: {MANTLE}; border: round {DEEP}; padding: 0 1; }}
#settings {{ width: 92%; height: 90%; background: {MANTLE}; border: round {DEEP}; padding: 0 2; scrollbar-size-vertical: 1; scrollbar-color: {DEEP}; scrollbar-background: {MANTLE}; }}
#settings .section.first {{ margin-top: 0; }}
.keys {{ color: {SUB0}; }}
.section {{ color: {ACCENT_T}; text-style: bold; margin-top: 1; }}
MenuScreen {{ align: left top; }}
SettingsScreen {{ align: center middle; }}
.head {{ height: 1; color: {OVER0}; }}
MenuRow {{ height: 1; }}
MenuRow:hover {{ background: {SURF0}; }}
MenuRow.sel {{ background: {FOCUS}; }}
.pin {{ width: 3; color: {OVER0}; }}
.pin.on {{ color: {BUBBLE}; }}
.menuname {{ width: 1fr; color: {SUB0}; }}
.menuname.on {{ color: {TEXT}; text-style: bold; }}
.x {{ width: 2; color: {RED}; }}
.x:hover {{ background: {SURF0}; }}
.menurename {{ width: 1fr; height: 1; border: none; padding: 0; background: {SURF0}; color: {TEXT}; }}
.opt {{ height: 1; color: {TEXT}; }}
.opt:hover {{ background: {SURF0}; }}
.label {{ color: {OVER0}; margin-top: 1; }}
#path {{ height: 1; border: none; padding: 0; background: {SURF0}; color: {TEXT}; }}

EntryCard {{ align: center middle; }}
#moveto {{ width: auto; padding: 0 1; color: {SUB0}; }}
#moveto:hover {{ color: {TEXT}; background: {SURF0}; }}
#moves {{ display: none; height: auto; margin-bottom: 1; }}
.movechoice {{ width: auto; padding: 0 1; margin-right: 1; color: {TEXT}; background: {SURF0}; }}
.movechoice:hover {{ background: {DEEP}; }}
#card {{ width: 90%; height: auto; max-height: 90%; padding: 0 2 1 2; background: {MANTLE}; border: round {DEEP}; }}
#cardhead {{ height: 1; margin-bottom: 1; }}
#cardtext {{ color: {TEXT}; }}
#cardtext.done {{ color: {OVER0}; text-style: strike; }}
#cardedit {{ height: 1; border: none; padding: 0; background: {SURF0}; color: {TEXT}; }}
#cardhint {{ width: 1fr; color: {OVER0}; content-align: right middle; }}
"""

G_CHEVRON, G_CHEVRON_UP = "\U000F0140", "\U000F0143"
G_PENCIL, G_GEAR = "\U000F03EB", "\U000F0493"
G_PIN, G_PIN_OFF = "\U000F0403", "\U000F0931"
G_BOX, G_BOX_DONE = "\U000F0131", "\U000F0132"
G_BANG = "\uf12a"                  # a chunky ! (Font Awesome): grey = off, red = priority


# ── widgets ─────────────────────────────────────────────────
class Click(Static):
    """A Static that runs a callback when clicked (and stops the click there)."""
    def __init__(self, text: str, action, **kw):
        super().__init__(text, **kw)
        self.action = action

    def on_click(self, event) -> None:
        event.stop()
        self.action()


class GrowInput(TextArea):
    """A text box that grows downward as you type (wraps instead of scrolling).
    Enter submits (Shift+Enter submits as priority); it reads and writes `value`."""
    class Submitted(Message):
        def __init__(self, input: "GrowInput", value: str, prio: bool = False):
            super().__init__()
            self.input, self.value, self.prio = input, value, prio

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
        if event.key in ("enter", "shift+enter"):
            event.stop(); event.prevent_default()
            self.post_message(self.Submitted(self, self.text.replace("\n", " "), event.key == "shift+enter"))
            return
        await super()._on_key(event)


def text_box(value: str = "", grow: bool = False, **kw):
    """One-line Input, or the growing box when that setting is on."""
    return GrowInput(value, **kw) if grow else Input(value, compact=True, **kw)


def submitted_prio(event) -> bool:
    return getattr(event, "prio", False)


class Item(Horizontal, can_focus=True):
    """One item: a box and its text. The text wraps (or not, per settings)."""
    BINDINGS = [Binding("space", "toggle", show=False),
                Binding("enter", "card", show=False),
                Binding("e", "edit", show=False),
                Binding("exclamation_mark", "prio", show=False),
                Binding("delete", "remove", show=False),
                Binding("down", "down", show=False),
                Binding("up", "up", show=False)]

    def __init__(self, idx: int, item: dict):
        super().__init__()
        self.idx, self.label, self.done, self.prio = idx, item["text"], item["done"], item.get("prio", False)
        self.set_class(self.done, "done")
        self.set_class(self.prio, "prio")

    def compose(self) -> ComposeResult:
        yield Click(G_BOX_DONE if self.done else G_BOX, lambda: self.app.toggle_item(self), classes="box")
        yield Static(self.label, classes="text", markup=False)

    def set_done(self, done: bool) -> None:
        self.done = done
        self.set_class(done, "done")
        self.query_one(".box", Static).update(G_BOX_DONE if done else G_BOX)

    def on_click(self, event) -> None:
        event.stop()
        if self.query(".itemedit"):
            return                          # clicks inside the editor stay there
        if event.button == 3:
            self.start_edit()               # right-click: edit the text in place
        else:
            self.app.open_card(self.idx)    # click the text: the whole entry as a card

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

    def action_toggle(self) -> None: self.app.toggle_item(self, keep_focus=True)
    def action_card(self) -> None: self.app.open_card(self.idx)
    def action_edit(self) -> None: self.start_edit()
    def action_prio(self) -> None: self.app.set_prio(self.idx)
    def action_remove(self) -> None: self.app.remove_item(self.idx)

    def action_down(self) -> None:
        rows = list(self.app.query(Item))
        i = rows.index(self)
        (rows[i + 1] if i + 1 < len(rows) else self.app.query_one("#entry")).focus()

    def action_up(self) -> None:
        rows = list(self.app.query(Item))
        i = rows.index(self)
        if i > 0:
            rows[i - 1].focus()


# ── overlays ────────────────────────────────────────────────
class Overlay(ModalScreen):
    """Sits over the app. A click outside the panel closes it and is used up
    (it never reaches whatever is underneath). Esc closes too."""
    BINDINGS = [Binding("escape", "close", show=False)]

    def on_click(self, event) -> None:
        if event.widget is self:            # the dimmed area, not the panel
            event.stop()
            self.action_close()

    def action_close(self) -> None:
        self.dismiss()


class MenuRow(Horizontal):
    """A line in the list menu: pin + name (+ × while editing)."""
    def __init__(self, idx: int, l: dict, current: bool, editing: bool):
        super().__init__()
        self.idx, self.l, self.current, self.editing = idx, l, current, editing

    def compose(self) -> ComposeResult:
        app = self.app
        yield Click(G_PIN if self.l.get("pinned") else G_PIN_OFF, lambda: self.screen.pin(self.idx),
                    classes="pin on" if self.l.get("pinned") else "pin")
        yield Click(self.l["name"], lambda: self.screen.clicked(self.idx),
                    classes="menuname on" if self.current else "menuname", markup=False)
        if self.editing:
            yield Click("×", lambda: self.screen.delete(self.idx), classes="x")


class MenuScreen(Overlay):
    """Every list. Click or ↑ ↓ Enter to open; pin to keep it first; the pencil
    turns on editing (click a name to rename it, × to delete)."""
    BINDINGS = [Binding("up", "move(-1)", show=False), Binding("down", "move(1)", show=False),
                Binding("enter", "choose", show=False), Binding("ctrl+c", "close", show=False, priority=True)]

    def __init__(self):
        super().__init__()
        self.sel = None
        self.editing = False

    def compose(self) -> ComposeResult:
        with Vertical(id="menu"):
            with Horizontal(classes="head"):
                yield Static("lists", classes="fill")
                yield Click(G_PENCIL, self.toggle_edit, id="menupencil", classes="icon")
            yield VerticalScroll(id="menurows")

    def on_mount(self) -> None:
        self.sel = self.app.cur
        self.fill()

    def fill(self) -> None:
        rows = self.query_one("#menurows", VerticalScroll)
        rows.remove_children()
        rows.mount_all([MenuRow(i, l, i == self.app.cur, self.editing) for i, l in enumerate(self.app.lists)])
        self.query_one("#menupencil").set_class(self.editing, "on")
        self.call_after_refresh(self.highlight)

    def highlight(self) -> None:
        for r in self.query(MenuRow):
            r.set_class(r.idx == self.sel, "sel")

    def action_move(self, step: int) -> None:
        self.sel = (self.sel + step) % len(self.app.lists)
        self.highlight()

    def action_choose(self) -> None:
        self.app.go_to(self.sel)
        self.dismiss()

    def clicked(self, i: int) -> None:
        if not self.editing:
            self.app.go_to(i)
            self.dismiss()
            return
        row = next(r for r in self.query(MenuRow) if r.idx == i)   # editing: rename in place
        name = row.query_one(".menuname")
        box = Input(self.app.lists[i]["name"], compact=True, classes="menurename", select_on_focus=True)
        box.rename_idx = i
        row.mount(box, after=name)
        name.display = False
        box.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        i = getattr(event.input, "rename_idx", None)
        if i is not None and event.value.strip():
            self.app.lists[i]["name"] = event.value.strip()
            self.app.persist(); self.app.draw_bar()
        self.fill()

    def pin(self, i: int) -> None:
        self.app.toggle_pin(i)
        self.sel = self.app.cur
        self.fill()

    def delete(self, i: int) -> None:
        self.app.delete_list(i)
        self.sel = self.app.cur
        self.fill()

    def toggle_edit(self) -> None:
        self.editing = not self.editing
        self.fill()


KEYS = """\
Ctrl+C      lists: ↑ ↓ to pick, Enter opens it (back to the add box)
Ctrl+S      settings (this page)
Ctrl+I/Tab  into the items: ↑ ↓ to move, Enter opens the card
Esc         back out; focus returns where you came from
Enter       add        Shift+Enter (or start with !)  add as priority

In the items:  Space tick   Enter card   e edit   ! priority   Del remove
In a card:     m move to another list   ! priority   e edit
Ctrl+←/→    previous / next list        Ctrl+Q  quit"""


class SettingsScreen(Overlay):
    BINDINGS = [Binding("ctrl+s", "close", show=False, priority=True)]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="settings"):
            yield Static("settings", classes="section first")
            yield Click("", lambda: self.flip("wrap"), id="o_wrap", classes="opt")
            yield Click("", lambda: self.flip("grow"), id="o_grow", classes="opt")
            yield Click("", lambda: self.flip("hide_done"), id="o_hide", classes="opt")
            yield Static("save file (Enter to move it)", classes="label")
            yield Input(str(FILE), id="path", compact=True)
            yield Static("keys", classes="section")
            yield Static(KEYS, classes="keys", markup=False)

    def on_mount(self) -> None:
        self.show()

    def show(self) -> None:
        a = self.app
        on = lambda b: "on" if b else "off"
        self.query_one("#o_wrap", Click).update(f"word wrap       {on(a.wrap)}")
        self.query_one("#o_grow", Click).update(f"growing input   {on(a.grow)}")
        self.query_one("#o_hide", Click).update(f"show ticked     {on(not a.hide_done)}")

    def flip(self, what: str) -> None:
        self.app.flip_setting(what)
        self.show()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        if event.value.strip():
            self.app.move_file(event.value.strip())
            self.query_one("#path", Input).value = str(FILE)


class EntryCard(Overlay):
    """The whole entry as a card. Its ! sets priority; click the text to edit
    it (Enter saves, empty removes it). Esc or a click outside closes."""
    def __init__(self, idx: int):
        super().__init__()
        self.idx = idx

    @property
    def item(self) -> dict:
        return self.app.lists[self.app.cur]["items"][self.idx]

    def compose(self) -> ComposeResult:
        it = self.item
        with Vertical(id="card"):
            with Horizontal(id="cardhead"):
                yield Click(G_BANG, self.flip_prio, id="cardbang", classes="bang on" if it.get("prio") else "bang")
                yield Click("move to ▸", self.show_moves, id="moveto")
                yield Static("click the text to edit", id="cardhint")
            yield Horizontal(id="moves")
            yield Click(it["text"], self.edit, id="cardtext", classes="done" if it["done"] else "", markup=False)

    BINDINGS = [Binding("m", "moves", show=False), Binding("exclamation_mark", "prio", show=False),
                Binding("e", "edit", show=False)]

    def flip_prio(self) -> None:
        self.app.set_prio(self.idx)
        self.query_one("#cardbang", Click).set_class(self.item.get("prio", False), "on")

    def show_moves(self) -> None:
        """The other lists, as choices: click one to move the item there."""
        row = self.query_one("#moves", Horizontal)
        if row.children:
            row.remove_children(); row.display = False
            return
        row.display = True
        row.mount_all([Click(l["name"], lambda i=i: self.move(i), classes="movechoice", markup=False)
                       for i, l in enumerate(self.app.lists) if i != self.app.cur])

    def move(self, to: int) -> None:
        self.app.move_item(self.idx, to)
        self.dismiss("moved")

    def action_moves(self) -> None: self.show_moves()
    def action_prio(self) -> None: self.flip_prio()
    def action_edit(self) -> None: self.edit()

    def edit(self) -> None:
        if self.query("#cardedit"):
            return
        text = self.query_one("#cardtext")
        box = GrowInput(self.item["text"], id="cardedit")
        self.query_one("#card").mount(box, after=text)
        text.display = False
        box.focus()
        box.move_cursor(box.document.end)

    def on_grow_input_submitted(self, event: GrowInput.Submitted) -> None:
        event.stop()
        self.app.edit_item(self.idx, event.value.strip())
        self.dismiss("edited")


# ── the app ─────────────────────────────────────────────────
class Checklist(App):
    CSS = CSS
    TITLE = "checklist"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("ctrl+c", "menu", "lists", priority=True),
        Binding("ctrl+s", "settings", "settings", priority=True),
        Binding("ctrl+i", "to_items", "items", priority=True),
        Binding("ctrl+left", "prev_list", "prev", priority=True),
        Binding("ctrl+right", "next_list", "next", priority=True),
        Binding("ctrl+q", "quit", "quit", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.lists = load()
        names = [l["name"] for l in self.lists]
        self.cur = names.index(CFG["list"]) if CFG.get("list") in names else 0
        self.renaming = False
        self.hide_done = CFG.get("hide_done", False)
        self.wrap = CFG.get("wrap", True)
        self.grow = CFG.get("grow", False)
        self.next_prio = False     # the bottom-right !: next item added is priority
        self.item_editing = None   # Item being edited in place
        self.mtime = FILE.stat().st_mtime if FILE.exists() else 0

    def compose(self) -> ComposeResult:
        yield Horizontal(id="bar")
        yield VerticalScroll(id="items")
        with Horizontal(id="bottom"):
            yield text_box(placeholder="+ add…", id="entry", grow=self.grow)
            yield Click(G_BANG, self.flip_next_prio, id="bang", classes="bang")

    def on_mount(self) -> None:
        if not FILE.exists():
            save(self.lists)
        self.apply_wrap()
        self.refresh_items()
        self.home()
        self.set_interval(1.0, self.watch_file)
        self.call_after_refresh(self.draw_bar)

    def on_resize(self) -> None:
        self.call_after_refresh(self.draw_bar, self.renaming)

    # ── focus: the add box is home ──
    def home(self) -> None:
        if self.screen is self.screen_stack[0]:
            self.query_one("#entry").focus()

    def on_click(self, event) -> None:
        # A click that nothing else used (empty space): back to the add box.
        if not self.renaming and self.item_editing is None:
            self.home()

    # ── the top row ──
    def draw_bar(self, rename: bool = False) -> None:
        """Lists that fit, then … for the rest. The open list always shows."""
        bar = self.query_one("#bar", Horizontal)
        width = bar.size.width or self.size.width
        tab_w = lambda i: 24 if rename and i == self.cur else cell_len(self.lists[i]["name"]) + 2
        room = width - 3 - 6 - 3          # chevron, + ⚙, and room for …
        shown, used = [], 0
        for i in range(len(self.lists)):
            if used + tab_w(i) > room:
                break
            shown.append(i); used += tab_w(i)
        if self.cur not in shown:         # make room for the open list
            while shown and used + tab_w(self.cur) > room:
                used -= tab_w(shown.pop())
            shown.append(self.cur)

        widgets = [Click(G_CHEVRON, self.action_menu, classes="icon")]
        for i in shown:
            l = self.lists[i]
            if rename and i == self.cur:
                self.rename_box = Input(l["name"], classes="rename", compact=True, select_on_focus=True)
                widgets.append(self.rename_box)
            else:
                widgets.append(Click(l["name"], lambda i=i: self.clicked_list(i),
                                     classes="list on" if i == self.cur else "list", markup=False))
        if len(shown) < len(self.lists):
            widgets.append(Click("…", self.action_menu, classes="icon"))
        widgets += [Click("", self.home, classes="fill"),
                    Click("+", self.add_list, classes="icon plus"),
                    Click(G_GEAR, self.action_settings, classes="icon")]
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
            self.go_to(i)

    def go_to(self, i: int) -> None:
        self.cur = i
        self.save_cfg()
        self.draw_bar(); self.refresh_items(); self.home()

    def add_list(self) -> None:
        self.lists.append(new_list("new list"))
        self.cur = len(self.lists) - 1
        self.persist(); self.save_cfg(); self.refresh_items()
        self.draw_bar(rename=True)          # straight into naming it

    def end_rename(self, name: str | None) -> None:
        if name:
            self.lists[self.cur]["name"] = name
            self.persist(); self.save_cfg()
        self.draw_bar()
        self.home()

    def delete_list(self, i: int) -> None:
        # A safety net, not a prompt: deleted lists are appended to
        # checklist.deleted.md next to the checklist.
        gone = self.lists.pop(i)
        with FILE.with_name(FILE.stem + ".deleted.md").open("a") as f:
            f.write(f"## {gone['name']}\n" + "".join(f"- [{'x' if it['done'] else ' '}] {it['text']}\n" for it in gone["items"]) + "\n")
        if not self.lists:
            self.lists = [new_list("ToDo")]
        if self.cur >= i and self.cur > 0:
            self.cur -= 1
        self.persist(); self.save_cfg(); self.draw_bar(); self.refresh_items()

    def toggle_pin(self, i: int) -> None:
        """Pinned lists sit first, in the order you pinned them."""
        current = self.lists[self.cur]
        l = self.lists.pop(i)
        l["pinned"] = not l.get("pinned", False)
        n_pinned = sum(1 for x in self.lists if x.get("pinned"))
        self.lists.insert(n_pinned, l)      # end of the pinned block / start of the rest
        self.cur = self.lists.index(current)
        self.persist(); self.draw_bar()

    # ── settings (remembered) ──
    def save_cfg(self) -> None:
        CFG.update(wrap=self.wrap, grow=self.grow, hide_done=self.hide_done,
                   list=self.lists[self.cur]["name"], file=str(FILE))
        write_settings(CFG)

    def apply_wrap(self) -> None:
        self.query_one("#items").set_class(not self.wrap, "nowrap")

    def flip_setting(self, what: str) -> None:
        if what == "wrap":
            self.wrap = not self.wrap
            self.apply_wrap()
        elif what == "hide_done":
            self.hide_done = not self.hide_done
            self.refresh_items()
        elif what == "grow":
            self.grow = not self.grow
            old = self.query_one("#entry")
            new = text_box(old.value, self.grow, placeholder="+ add…", id="entry")

            async def swap() -> None:       # the old box must be gone before the new one (same id)
                await old.remove()
                await self.query_one("#bottom").mount(new, before=0)
            self.call_later(swap)
        self.save_cfg()

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
        self.draw_bar(); self.refresh_items()

    # ── items ──
    @property
    def items(self) -> list[dict]:
        return self.lists[self.cur]["items"]

    def refresh_items(self, focus_idx: int | None = None) -> None:
        box = self.query_one("#items", VerticalScroll)
        items = self.items
        # Priority first, then the rest; ticked items sink to the bottom.
        order = [i for i, it in enumerate(items) if not it["done"] and it.get("prio")]
        order += [i for i, it in enumerate(items) if not it["done"] and not it.get("prio")]
        if not self.hide_done:
            order += [i for i, it in enumerate(items) if it["done"]]
        rows = [Item(i, items[i]) for i in order]
        with self.batch_update():
            box.remove_children()
            box.mount_all(rows)
        if focus_idx is not None:
            for r in rows:
                if r.idx == focus_idx:
                    self.call_after_refresh(r.focus)

    def add_item(self, text: str, prio: bool) -> None:
        if text.startswith("!"):            # "!" at the start also means priority
            text, prio = text.lstrip("! ").strip(), True
        if not text:
            return
        self.items.append({"text": text, "done": False, "prio": prio or self.next_prio})
        if self.next_prio:
            self.flip_next_prio()           # one item at a time
        self.persist(); self.refresh_items()
        self.query_one("#items", VerticalScroll).scroll_end(animate=False)

    def toggle_item(self, item: Item, keep_focus: bool = False) -> None:
        done = not item.done
        self.items[item.idx]["done"] = done
        item.set_done(done)
        self.persist()
        if self.hide_done and done:
            item.remove()
        if not keep_focus:
            self.home()

    def set_prio(self, idx: int) -> None:
        it = self.items[idx]
        it["prio"] = not it.get("prio", False)
        self.persist()
        self.refresh_items(focus_idx=idx if isinstance(self.focused, Item) else None)

    def edit_item(self, idx: int, text: str) -> None:
        if text:
            self.items[idx]["text"] = text
        else:
            self.items.pop(idx)
        self.persist(); self.refresh_items()

    def remove_item(self, idx: int) -> None:
        rows = [r.idx for r in self.query(Item)]
        pos = rows.index(idx)
        self.items.pop(idx)
        self.persist(); self.refresh_items()
        rows = list(self.query(Item))
        # keep the cursor near where it was
        self.call_after_refresh(lambda: (rows[min(pos, len(rows) - 1)] if rows else self.query_one("#entry")).focus())

    def open_card(self, idx: int) -> None:
        def back(result) -> None:
            if result is None:              # Esc / click outside: back on the item you viewed
                for r in self.query(Item):
                    if r.idx == idx:
                        r.focus(); return
            self.home()
        self.push_screen(EntryCard(idx), back)

    def move_item(self, idx: int, to: int) -> None:
        it = self.items.pop(idx)
        self.lists[to]["items"].append(it)
        self.persist(); self.refresh_items()
        self.notify(f"moved to {self.lists[to]['name']}", timeout=2)

    def flip_next_prio(self) -> None:
        self.next_prio = not self.next_prio
        bang = self.query_one("#bang", Click)
        bang.set_class(self.next_prio, "on")
        self.home()

    def finish_item_edit(self, text: str | None) -> None:
        it = self.item_editing
        if it is None:
            return
        it.stop_edit()
        if text is not None:                # None = Esc: unchanged
            self.edit_item(it.idx, text)
        self.home()

    def persist(self) -> None:
        save(self.lists)
        self.mtime = FILE.stat().st_mtime

    # Someone (you in an editor, another window, or an agent) changed the file.
    def watch_file(self) -> None:
        try:
            m = FILE.stat().st_mtime
        except FileNotFoundError:
            return
        busy = self.renaming or self.item_editing is not None or len(self.screen_stack) > 1
        if m != self.mtime and not busy:
            self.mtime = m
            name = self.lists[self.cur]["name"]
            self.lists = load()
            names = [l["name"] for l in self.lists]
            self.cur = names.index(name) if name in names else min(self.cur, len(self.lists) - 1)
            self.draw_bar(); self.refresh_items()

    # ── events ──
    def on_grow_input_submitted(self, event: GrowInput.Submitted) -> None:
        self.on_input_submitted(event)

    def on_input_submitted(self, event) -> None:
        text = event.value.strip()
        if event.input.has_class("itemedit"):
            self.finish_item_edit(text)
        elif event.input.has_class("rename"):
            self.end_rename(text)
        elif event.input.id == "entry":
            event.input.value = ""
            self.add_item(text, submitted_prio(event))

    # Clicking away from a rename or an edit keeps what was typed.
    def on_descendant_blur(self, event) -> None:
        if self.renaming and event.widget.has_class("rename"):
            self.end_rename(event.widget.value.strip())
        elif event.widget.has_class("itemedit") and self.item_editing is not None:
            self.finish_item_edit(event.widget.value.strip())

    def on_key(self, event) -> None:
        f = self.focused
        # Shift+Enter in the one-line add box: add as priority.
        if event.key == "shift+enter" and isinstance(f, Input) and f.id == "entry":
            event.stop()
            text, f.value = f.value.strip(), ""
            self.add_item(text, True)
        # Tab from the add box (also what Ctrl+I sends): into the items.
        if event.key == "tab" and getattr(f, "id", None) == "entry" and list(self.query(Item)):
            event.stop(); event.prevent_default()
            self.action_to_items()
            return
        # ↑ from the add box steps into the list (last item first).
        elif event.key == "up" and getattr(f, "id", None) == "entry":
            rows = list(self.query(Item))
            if rows:
                event.stop()
                rows[-1].focus()
        elif event.key == "escape":
            if self.item_editing is not None:
                self.finish_item_edit(None)
            elif self.renaming:
                self.renaming = False
                self.end_rename(None)
            else:
                self.home()
        # Typing while a list row has focus goes to the add box.
        elif isinstance(f, Item) and event.is_printable and event.character not in (" ", "e", "!"):
            event.stop()
            entry = self.query_one("#entry")
            entry.focus()
            entry.value += event.character

    # ── keys ──
    def action_menu(self) -> None:
        if isinstance(self.screen, MenuScreen):
            self.screen.dismiss()           # Ctrl+C again closes it
        elif len(self.screen_stack) == 1:
            self.push_screen(MenuScreen(), lambda _: self.home())

    def action_settings(self) -> None:
        if isinstance(self.screen, SettingsScreen):
            self.screen.dismiss()
        elif len(self.screen_stack) == 1:
            self.push_screen(SettingsScreen(), lambda _: self.home())

    def action_to_items(self) -> None:
        if len(self.screen_stack) > 1:
            return
        rows = list(self.query(Item))
        if rows:
            (self.focused if isinstance(self.focused, Item) else rows[0]).focus()

    def switch(self, step: int) -> None:
        self.go_to((self.cur + step) % len(self.lists))

    def action_prev_list(self) -> None: self.switch(-1)
    def action_next_list(self) -> None: self.switch(1)


if __name__ == "__main__":
    Checklist().run()
