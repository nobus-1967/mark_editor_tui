# Mark Editor TUI — Themes

The editor has four themes: `default`, `green`, `magenta` and `blue`. The switch order is `default → green → magenta → blue → default`.

- **File → Toggle Theme** (the last item before **Quit**) or `Alt+T` switches the theme.
- The selected theme is saved in `~/.config/mark_editor/theme.json` under the `mode` key and restored on the next launch.
- Delete this file to return to the `default` theme.

This document is a reference for users and GitHub. It is not included in the package and is not used by the program. The source palettes are in `src/mark_editor_tui/themes.py`, and the shell layout is in `src/mark_editor_tui/styles.tcss`.

Each HEX color is from the xterm-256 palette; its index is shown in parentheses (see `/home/nobus/OpenCode/xterm-256colors.md`). For the dark-blue roles in the `blue` theme, adjacent palette steps (17/18/19) are used to keep different components distinct.

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
| `secondary`         | `#a8a8a8` (248)                  |
| `accent`            | `#ffffff` (231)                  |
| `foreground`        | `#ffffff` (231)                  |
| `background`        | `#000000` (16)                   |
| `surface`           | `#000000` (16)                   |
| `panel`             | `#1c1c1c` (234)                  |
| `success`           | `#a8a8a8` (248)                  |
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
| `status-background`      | `#1c1c1c` (234)                  |
| `status-foreground`      | `#ffffff` (231)                  |
| `keybar-background`      | `#1c1c1c` (234)                  |
| `dialog-background`      | `#1c1c1c` (234)                  |
| `dialog-foreground`      | `#ffffff` (231)                  |

### Editor `mark_editor_tui-default`

| Style                      | Foreground      | Background      |
| :---                       | :---            | :---            |
| `base_style`               | `#ffffff` (231) | `#000000` (16)  |
| `gutter_style`             | `#ffffff` (231) | `#000000` (16)  |
| `cursor_style`             | `#000000` (16) | `#ffffff` (231) |
| `cursor_line_style`        | not set         | `#1c1c1c` (234) |
| `cursor_line_gutter_style` | `#ffffff` (231) | `#1c1c1c` (234) |
| `selection_style`          | `#000000` (16)  | `#ffffff` (231) |

## 2. green

Based on `default`: all white elements are replaced with bright green `#00ff00` (46), and inverted white blocks with black text become green blocks with black text. The black background, gray `secondary` and `#1c1c1c` (234) panel are preserved.

### Application palette

| Role                | HEX value (xterm-256color index) |
| :---                | :---                             |
| `primary`           | `#00ff00` (46)                   |
| `secondary`         | `#00af00` (34)                   |
| `accent`            | `#00ff00` (46)                   |
| `foreground`        | `#00ff00` (46)                   |
| `background`        | `#000000` (16)                   |
| `surface`           | `#000000` (16)                   |
| `panel`             | `#1c1c1c` (234)                  |
| `success`           | `#00af00` (34)                   |
| `warning` / `error` | `#870000` (88)                   |

### Theme variables

| Variable                 | HEX value (xterm-256color index) |
| :---                     | :---                             |
| `menu-background`        | `#000000` (16)                   |
| `menu-foreground`        | `#00ff00` (46)                   |
| `menu-active-background` | `#00ff00` (46)                   |
| `menu-active-foreground` | `#000000` (16)                   |
| `editor-background`      | `#000000` (16)                   |
| `editor-foreground`      | `#00ff00` (46)                   |
| `status-background`      | `#1c1c1c` (234)                  |
| `status-foreground`      | `#00ff00` (46)                   |
| `keybar-background`      | `#1c1c1c` (234)                  |
| `dialog-background`      | `#1c1c1c` (234)                  |
| `dialog-foreground`      | `#00ff00` (46)                   |

### Editor `mark_editor_tui-green`

| Style                      | Foreground     | Background      |
| :---                       | :---           | :---            |
| `base_style`               | `#00ff00` (46) | `#000000` (16)  |
| `gutter_style`             | `#00ff00` (46) | `#000000` (16)  |
| `cursor_style`             | `#000000` (16) | `#00ff00` (46)  |
| `cursor_line_style`        | not set        | `#1c1c1c` (234) |
| `cursor_line_gutter_style` | `#00ff00` (46) | `#1c1c1c` (234) |
| `selection_style`          | `#000000` (16) | `#00ff00` (46)  |

## 3. magenta

Based on `default`: all white elements are replaced with dark magenta `#af00af` (127), and inverted white blocks with black text become magenta blocks with black text. The black background, muted `secondary` `#800080` (5) and `#1c1c1c` (234) panel are preserved.

### Application palette

| Role                | HEX value (xterm-256color index) |
| :---                | :---                             |
| `primary`           | `#af00af` (127)                  |
| `secondary`         | `#800080` (5)                   |
| `accent`            | `#af00af` (127)                  |
| `foreground`        | `#af00af` (127)                  |
| `background`        | `#000000` (16)                   |
| `surface`           | `#000000` (16)                   |
| `panel`             | `#1c1c1c` (234)                  |
| `success`           | `#800080` (5)                   |
| `warning` / `error` | `#87005f` (89)                   |

### Theme variables

| Variable                 | HEX value (xterm-256color index) |
| :---                     | :---                             |
| `menu-background`        | `#000000` (16)                   |
| `menu-foreground`        | `#af00af` (127)                  |
| `menu-active-background` | `#af00af` (127)                  |
| `menu-active-foreground` | `#000000` (16)                   |
| `editor-background`      | `#000000` (16)                   |
| `editor-foreground`      | `#af00af` (127)                  |
| `status-background`      | `#1c1c1c` (234)                  |
| `status-foreground`      | `#af00af` (127)                  |
| `keybar-background`      | `#1c1c1c` (234)                  |
| `dialog-background`      | `#1c1c1c` (234)                  |
| `dialog-foreground`      | `#af00af` (127)                  |

### Editor `mark_editor_tui-magenta`

| Style                      | Foreground      | Background      |
| :---                       | :---            | :---            |
| `base_style`               | `#af00af` (127) | `#000000` (16)  |
| `gutter_style`             | `#af00af` (127) | `#000000` (16)  |
| `cursor_style`             | `#000000` (16)  | `#af00af` (127) |
| `cursor_line_style`        | not set         | `#1c1c1c` (234) |
| `cursor_line_gutter_style` | `#af00af` (127) | `#1c1c1c` (234) |
| `selection_style`          | `#000000` (16)  | `#af00af` (127) |

## 4. blue

The **blue** theme is based on `default`: the same roles and contrast, but the neutral surfaces are replaced with deep blue and the text with light blue. The editor and menu background is `#000087` (18), panels and dialogs are `#0000af` (19), and active elements are `#d7d7ff` (189) with dark blue text.

### Application palette

| Role                | HEX value (xterm-256color index) |
| :---                | :---                             |
| `primary`           | `#d7d7ff` (189)                  |
| `secondary`         | `#87afd7` (110)                  |
| `accent`            | `#d7d7ff` (189)                  |
| `foreground`        | `#eeeeee` (255)                  |
| `background`        | `#000087` (18)                   |
| `surface`           | `#000087` (18)                   |
| `panel`             | `#0000af` (19)                   |
| `success`           | `#87afd7` (110)                  |
| `warning` / `error` | `#af0087` (126)                  |

### Theme variables

| Variable                 | HEX value (xterm-256color index) |
| :---                     | :---                             |
| `menu-background`        | `#000087` (18)                   |
| `menu-foreground`        | `#eeeeee` (255)                  |
| `menu-active-background` | `#d7d7ff` (189)                  |
| `menu-active-foreground` | `#00005f` (17)                   |
| `editor-background`      | `#000087` (18)                   |
| `editor-foreground`      | `#eeeeee` (255)                  |
| `status-background`      | `#0000af` (19)                   |
| `status-foreground`      | `#eeeeee` (255)                  |
| `keybar-background`      | `#0000af` (19)                   |
| `dialog-background`      | `#0000af` (19)                   |
| `dialog-foreground`      | `#eeeeee` (255)                  |

### Editor `mark_editor_tui-blue`

| Style                      | Foreground      | Background      |
| :---                       | :---            | :---            |
| `base_style`               | `#eeeeee` (255) | `#000087` (18)  |
| `gutter_style`             | `#87afd7` (110) | `#000087` (18)  |
| `cursor_style`             | `#00005f` (17)  | `#d7d7ff` (189) |
| `cursor_line_style`        | not set         | `#0000af` (19)  |
| `cursor_line_gutter_style` | `#87afd7` (110) | `#0000af` (19)  |
| `selection_style`          | `#00005f` (17)  | `#d7d7ff` (189) |
