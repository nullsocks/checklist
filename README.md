# track-tui

A tiny click-to-tick checklist for the terminal, built with [Textual](https://textual.textualize.io/).
Several lists, pinning, word wrap, hide-ticked, in-place editing, and everything
saved to one plain Markdown file that you (or an agent) can edit by hand too.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/nullsocks/track-tui/main/install.sh | sh
```

Then run `checklist` in any terminal. Run the same line again to update.

- App: `~/.local/share/track-tui/checklist.py`
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
| top-left chevron | every list: open one, or pin it to the front |
| list name | click to open; click the open one to rename it |
| `…` | more lists than fit; opens the same menu |
| `+` / pencil / gear | new list / delete mode (× on each list) / settings |
| tick box | done / not done |
| click an entry | the whole entry as a floating card |
| right-click an entry, or `e` | edit it in place (empty removes it) |
| eye (bottom right) | hide or show ticked entries |
| `Ctrl+←/→`, `Del`, `Esc`, `Ctrl+Q` | switch list, remove entry, close a panel, quit |

Deleted lists are kept in `checklist.deleted.md` next to your lists, just in case.
