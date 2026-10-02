# checklist

A tiny click-to-tick checklist for the terminal, built with [Textual](https://textual.textualize.io/).
Several lists, pinning, word wrap, hide-ticked, in-place editing, and everything
saved to one plain Markdown file that you (or an agent) can edit by hand too.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/nullsocks/checklist/main/install.sh | sh
```

Then run `checklist` in any terminal. Run the same line again to update.

- App: `~/.local/share/checklist/checklist.py`
- Command: `~/.local/bin/checklist`
- Your lists: `~/agent_workspace/checklist.md` by default (change it in ⚙ settings)
- Settings: `~/.config/liquid-checklist/settings.json`
- Needs: Python 3.11+, `textual` (Arch: `sudo pacman -S python-textual`), a Nerd Font for the icons

Uninstall: `sh install.sh --uninstall` (your lists are kept).

## Developing

This checkout is the source, not what runs. After changing `checklist.py`:

```sh
sh install.sh --local
```

## Using it

| | |
|---|---|
| top-left chevron / `Ctrl+C` | every list: ↑ ↓ Enter to open, pin to keep first, pencil to rename or delete |
| list name | click to open; click the open one to rename it |
| `…` | more lists than fit; opens the same menu |
| `+` / gear / `Ctrl+S` | new list / settings (wrap, growing input, show ticked, save file, keys) |
| add box | always ready: type + Enter; Shift+Enter or a leading `!` adds as priority |
| `!` (bottom right) | the next item you add is priority |
| tick box | done / not done (priority items have a red box and sort first) |
| click an entry, or Enter | its card: `!` priority, `m` move to another list, click text or `e` to edit |
| right-click an entry | edit it in place (empty removes it) |
| `Tab` / `Ctrl+I` | into the items: ↑ ↓, Space tick, `!`, `e`, `Del` |
| `Esc` | back out; focus returns where you came from |
| `Ctrl+←/→`, `Ctrl+Q` | previous / next list, quit |

Deleted lists are kept in `checklist.deleted.md` next to your lists, just in case.
