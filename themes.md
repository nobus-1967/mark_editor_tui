# Mark Editor TUI — Themes

The editor has four themes: `default`, `green`, `magenta` and `blue`. The switch order is `default → green → magenta → blue → default`.

- **File → Toggle Theme** (the last item before **Quit**) or `Alt+T` switches the theme.
- The selected theme is saved in `~/.config/mark_editor/theme.json` under the `mode` key and restored on the next launch.
- Delete this file to return to the `default` theme.

This document is a reference for users and GitHub. It is not included in the package and is not used by the program. The source palettes are in `src/mark_editor_tui/themes.py`, and the shell layout is in `src/mark_editor_tui/styles.tcss`.

Next to every HEX code, the nearest xterm-256color match is shown in parentheses.

## Shell elements

| Element                        | Variable / Property                                         |
| :---                           | :---                                                        |
| Menu bar and menu items        | `menu-background`, `menu-foreground`                        |
| Hovered and selected menu item | `menu-active-background`, `menu-active-foreground`          |
| Editor                         | `editor-background`, `editor-foreground`                    |
| Status line                    | `status-background`, `status-foreground`                    |
| F1–F12 key bar                 | `keybar-background`; keys use the menu colors               |
| Dialogs                        | `dialog-background`, `dialog-foreground`; border — `accent` |
| Drop-down menu list            | `menu-*` colors                                             |

F1–F12 keys: the label uses `menu-background`/`menu-foreground`, the key uses `menu-active-background`/`menu-active-foreground`.

## 1. default (dark)

A dark theme: black background, white text, white active elements.

### Application palette

| Role                | HEX value (xterm-256color index) |
| :---                | :---                             |
| `primary`           | `#ffffff` (231)                  |
| `secondary`         | `#aaaaaa` (248)                  |
| `accent`            | `#ffffff` (231)                  |
| `foreground`        | `#ffffff` (231)                  |
| `background`        | `#000000` (16)                   |
| `surface`           | `#000000` (16)                   |
| `panel`             | `#1a1a1a` (234)                  |
| `success`           | `#00aa00` (34)                   |
| `warning` / `error` | `#ff00ff` (201)                  |

### Theme variables

| Variable                 | HEX value (xterm-256color index) |
| :---                     | :---                             |
| `menu-background`        | `#000000` (16)                   |
| `menu-foreground`        | `#ffffff` (231)                  |
| `menu-active-background` | `#ffffff` (231)                  |
| `menu-active-foreground` | `#000000` (16)                   |
| `editor-background`      | `#000000` (16)                   |
| `editor-foreground`      | `#ffffff` (231)                  |
| `status-background`      | `#1a1a1a` (234)                  |
| `status-foreground`      | `#ffffff` (231)                  |
| `keybar-background`      | `#1a1a1a` (234)                  |
| `dialog-background`      | `#1a1a1a` (234)                  |
| `dialog-foreground`      | `#ffffff` (231)                  |

### Editor `mark_editor_tui-default`

| Style                      | Foreground      | Background      |
| :---                       | :---            | :---            |
| `base_style`               | `#ffffff` (231) | `#000000` (16)  |
| `gutter_style`             | `#ffffff` (231) | `#000000` (16)  |
| `cursor_style`             | `#000000` (16)  | `#ffffff` (231) |
| `cursor_line_style`        | not set         | `#1a1a1a` (234) |
| `cursor_line_gutter_style` | `#ffffff` (231) | `#1a1a1a` (234) |
| `selection_style`          | `#000000` (16)  | `#ffffff` (231) |

## 2. green

Based on `default`: all white elements are replaced with bright green `#00ff00` (46), and inverted white blocks with black text become green blocks with black text. The black background, gray `secondary` and `#1a1a1a` (234) panel are preserved.

### Application palette

| Role                | HEX value (xterm-256color index) |
| :---                | :---                             |
| `primary`           | `#00ff00` (46)                   |
| `secondary`         | `#00aa00` (34)                   |
| `accent`            | `#00ff00` (46)                   |
| `foreground`        | `#00ff00` (46)                   |
| `background`        | `#000000` (16)                   |
| `surface`           | `#000000` (16)                   |
| `panel`             | `#1a1a1a` (234)                  |
| `success`           | `#00aa00` (34)                   |
| `warning` / `error` | `#ffffff` (231)                  |

### Theme variables

| Variable                 | HEX value (xterm-256color index) |
| :---                     | :---                             |
| `menu-background`        | `#000000` (16)                   |
| `menu-foreground`        | `#00ff00` (46)                   |
| `menu-active-background` | `#00ff00` (46)                   |
| `menu-active-foreground` | `#000000` (16)                   |
| `editor-background`      | `#000000` (16)                   |
| `editor-foreground`      | `#00ff00` (46)                   |
| `status-background`      | `#1a1a1a` (234)                  |
| `status-foreground`      | `#00ff00` (46)                   |
| `keybar-background`      | `#1a1a1a` (234)                  |
| `dialog-background`      | `#1a1a1a` (234)                  |
| `dialog-foreground`      | `#00ff00` (46)                   |

### Editor `mark_editor_tui-green`

| Style                      | Foreground     | Background      |
| :---                       | :---           | :---            |
| `base_style`               | `#00ff00` (46) | `#000000` (16)  |
| `gutter_style`             | `#00ff00` (46) | `#000000` (16)  |
| `cursor_style`             | `#000000` (16) | `#00ff00` (46)  |
| `cursor_line_style`        | not set        | `#1a1a1a` (234) |
| `cursor_line_gutter_style` | `#00ff00` (46) | `#1a1a1a` (234) |
| `selection_style`          | `#000000` (16) | `#00ff00` (46)  |

## 3. magenta

Based on `default`: all white elements are replaced with dark magenta `#aa00aa` (127), and inverted white blocks with black text become magenta blocks with black text. The black background, muted `secondary` `#770077` (90) and `#1a1a1a` (234) panel are preserved.

### Application palette

| Role                | HEX value (xterm-256color index) |
| :---                | :---                             |
| `primary`           | `#aa00aa` (127)                  |
| `secondary`         | `#770077` (90)                   |
| `accent`            | `#aa00aa` (127)                  |
| `foreground`        | `#aa00aa` (127)                  |
| `background`        | `#000000` (16)                   |
| `surface`           | `#000000` (16)                   |
| `panel`             | `#1a1a1a` (234)                  |
| `success`           | `#00aa00` (34)                   |
| `warning` / `error` | `#aa0000` (124)                  |

### Theme variables

| Variable                 | HEX value (xterm-256color index) |
| :---                     | :---                             |
| `menu-background`        | `#000000` (16)                   |
| `menu-foreground`        | `#aa00aa` (127)                  |
| `menu-active-background` | `#aa00aa` (127)                  |
| `menu-active-foreground` | `#000000` (16)                   |
| `editor-background`      | `#000000` (16)                   |
| `editor-foreground`      | `#aa00aa` (127)                  |
| `status-background`      | `#1a1a1a` (234)                  |
| `status-foreground`      | `#aa00aa` (127)                  |
| `keybar-background`      | `#1a1a1a` (234)                  |
| `dialog-background`      | `#1a1a1a` (234)                  |
| `dialog-foreground`      | `#aa00aa` (127)                  |

### Editor `mark_editor_tui-magenta`

| Style                      | Foreground      | Background      |
| :---                       | :---            | :---            |
| `base_style`               | `#aa00aa` (127) | `#000000` (16)  |
| `gutter_style`             | `#aa00aa` (127) | `#000000` (16)  |
| `cursor_style`             | `#000000` (16)  | `#aa00aa` (127) |
| `cursor_line_style`        | not set         | `#1a1a1a` (234) |
| `cursor_line_gutter_style` | `#aa00aa` (127) | `#1a1a1a` (234) |
| `selection_style`          | `#000000` (16)  | `#aa00aa` (127) |

## 4. blue

The **blue** theme is based on `default`: the same roles and contrast, but the neutral surfaces are replaced with deep blue and the text with light blue. The editor and menu background is `#000055` (18), panels and dialogs are `#00106b` (19), and active elements are `#d6e6ff` (189) with dark blue text.

### Application palette

| Role                | HEX value (xterm-256color index) |
| :---                | :---                             |
| `primary`           | `#d6e6ff` (189)                  |
| `secondary`         | `#8aa9d6` (110)                  |
| `accent`            | `#d6e6ff` (189)                  |
| `foreground`        | `#e8f1ff` (255)                  |
| `background`        | `#000055` (18)                   |
| `surface`           | `#000055` (18)                   |
| `panel`             | `#00106b` (19)                   |
| `success`           | `#00ff00` (46)                   |
| `warning` / `error` | `#ff00ff` (201)                  |

### Theme variables

| Variable                 | HEX value (xterm-256color index) |
| :---                     | :---                             |
| `menu-background`        | `#000055` (18)                   |
| `menu-foreground`        | `#e8f1ff` (255)                  |
| `menu-active-background` | `#d6e6ff` (189)                  |
| `menu-active-foreground` | `#000033` (17)                   |
| `editor-background`      | `#000055` (18)                   |
| `editor-foreground`      | `#e8f1ff` (255)                  |
| `status-background`      | `#00106b` (19)                   |
| `status-foreground`      | `#e8f1ff` (255)                  |
| `keybar-background`      | `#00106b` (19)                   |
| `dialog-background`      | `#00106b` (19)                   |
| `dialog-foreground`      | `#e8f1ff` (255)                  |

### Editor `mark_editor_tui-blue`

| Style                      | Foreground      | Background      |
| :---                       | :---            | :---            |
| `base_style`               | `#e8f1ff` (255) | `#000055` (18)  |
| `gutter_style`             | `#8aa9d6` (110) | `#000055` (18)  |
| `cursor_style`             | `#000033` (17)  | `#d6e6ff` (189) |
| `cursor_line_style`        | not set         | `#00106b` (19)  |
| `cursor_line_gutter_style` | `#8aa9d6` (110) | `#00106b` (19)  |
| `selection_style`          | `#000033` (17)  | `#d6e6ff` (189) |

In the `default` and `blue` themes, warnings and errors are magenta `#ff00ff` (201); in the `green` and `magenta` themes they are white `#ffffff` (231).
