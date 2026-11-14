# Mark Editor TUI — темы оформления

В редакторе четыре темы: `default`, `green`, `magenta` и `blue`. Порядок
переключения — `default → green → magenta → blue → default`.

- **File → Toggle Theme** (последний пункт перед **Quit**) или `Alt+T`
  переключает тему.
- Выбранная тема сохраняется в `~/.config/mark_editor/theme.json` в ключе
  `mode` и восстанавливается при следующем запуске.
- Удалите этот файл, чтобы вернуться к теме `default`.

Этот документ — справочник для пользователей и GitHub. Он не входит в пакет и
не используется программой. Исходные палитры находятся в
`src/mark_editor_tui/themes.py`, раскладка оболочки — в
`src/mark_editor_tui/styles.tcss`.

## Общие элементы оболочки

| Элемент | Переменная / свойство |
| :--- | :--- |
| Меню-бар и пункты меню | `menu-background`, `menu-foreground` |
| Наведение и выбранный пункт меню | `menu-active-background`, `menu-active-foreground` |
| Редактор | `editor-background`, `editor-foreground` |
| Строка состояния | `status-background`, `status-foreground` |
| Панель F1–F12 | `keybar-background`; клавиши используют цвета меню |
| Диалоги | `dialog-background`, `dialog-foreground`, рамка — `accent` |
| Выпадающий список меню | цвета `menu-*` |

Клавиши F1–F12: подпись — `menu-background`/`menu-foreground`, клавиша —
`menu-active-background`/`menu-active-foreground`.

## 1. default (тёмная)

Тёмная тема: чёрный фон, белый текст, белые активные элементы.

### Палитра приложения

| Роль | Значение |
| :--- | :--- |
| `primary` | `#ffffff` |
| `secondary` | `#aaaaaa` |
| `accent` | `#ffffff` |
| `foreground` | `#ffffff` |
| `background` | `#000000` |
| `surface` | `#000000` |
| `panel` | `#1a1a1a` |
| `success` | `#00aa00` |
| `warning` / `error` | `#ff00ff` |

### Переменные темы

| Переменная | Значение |
| :--- | :--- |
| `menu-background` | `#000000` |
| `menu-foreground` | `#ffffff` |
| `menu-active-background` | `#ffffff` |
| `menu-active-foreground` | `#000000` |
| `editor-background` | `#000000` |
| `editor-foreground` | `#ffffff` |
| `status-background` | `#1a1a1a` |
| `status-foreground` | `#ffffff` |
| `keybar-background` | `#1a1a1a` |
| `dialog-background` | `#1a1a1a` |
| `dialog-foreground` | `#ffffff` |

### Редактор `mark_editor_tui-default`

| Стиль | Текст | Фон |
| :--- | :--- | :--- |
| `base_style` | `#ffffff` | `#000000` |
| `gutter_style` | `#ffffff` | `#000000` |
| `cursor_style` | `#000000` | `#ffffff` |
| `cursor_line_style` | не задан | `#1a1a1a` |
| `cursor_line_gutter_style` | `#ffffff` | `#1a1a1a` |
| `selection_style` | `#000000` | `#ffffff` |

## 2. green

Основана на `default`: все белые элементы заменены ярким зелёным `#00ff00`, а
инвертированные белые плашки с чёрным текстом — зелёными плашками с чёрным
текстом. Чёрный фон, серый `secondary` и панель `#1a1a1a` сохраняются.

### Палитра приложения

| Роль | Значение |
| :--- | :--- |
| `primary` | `#00ff00` |
| `secondary` | `#00aa00` |
| `accent` | `#00ff00` |
| `foreground` | `#00ff00` |
| `background` | `#000000` |
| `surface` | `#000000` |
| `panel` | `#1a1a1a` |
| `success` | `#00aa00` |
| `warning` / `error` | `#ffffff` |

### Переменные темы

| Переменная | Значение |
| :--- | :--- |
| `menu-background` | `#000000` |
| `menu-foreground` | `#00ff00` |
| `menu-active-background` | `#00ff00` |
| `menu-active-foreground` | `#000000` |
| `editor-background` | `#000000` |
| `editor-foreground` | `#00ff00` |
| `status-background` | `#1a1a1a` |
| `status-foreground` | `#00ff00` |
| `keybar-background` | `#1a1a1a` |
| `dialog-background` | `#1a1a1a` |
| `dialog-foreground` | `#00ff00` |

### Редактор `mark_editor_tui-green`

| Стиль | Текст | Фон |
| :--- | :--- | :--- |
| `base_style` | `#00ff00` | `#000000` |
| `gutter_style` | `#00ff00` | `#000000` |
| `cursor_style` | `#000000` | `#00ff00` |
| `cursor_line_style` | не задан | `#1a1a1a` |
| `cursor_line_gutter_style` | `#00ff00` | `#1a1a1a` |
| `selection_style` | `#000000` | `#00ff00` |

## 3. magenta

Основана на `default`: все белые элементы заменены тёмным magenta `#aa00aa`, а
инвертированные белые плашки с чёрным текстом — magenta-плашками с чёрным
текстом. Чёрный фон, приглушённый `secondary` `#770077` и панель `#1a1a1a`
сохраняются.

### Палитра приложения

| Роль | Значение |
| :--- | :--- |
| `primary` | `#aa00aa` |
| `secondary` | `#770077` |
| `accent` | `#aa00aa` |
| `foreground` | `#aa00aa` |
| `background` | `#000000` |
| `surface` | `#000000` |
| `panel` | `#1a1a1a` |
| `success` | `#00aa00` |
| `warning` / `error` | `#aa0000` |

### Переменные темы

| Переменная | Значение |
| :--- | :--- |
| `menu-background` | `#000000` |
| `menu-foreground` | `#aa00aa` |
| `menu-active-background` | `#aa00aa` |
| `menu-active-foreground` | `#000000` |
| `editor-background` | `#000000` |
| `editor-foreground` | `#aa00aa` |
| `status-background` | `#1a1a1a` |
| `status-foreground` | `#aa00aa` |
| `keybar-background` | `#1a1a1a` |
| `dialog-background` | `#1a1a1a` |
| `dialog-foreground` | `#aa00aa` |

### Редактор `mark_editor_tui-magenta`

| Стиль | Текст | Фон |
| :--- | :--- | :--- |
| `base_style` | `#aa00aa` | `#000000` |
| `gutter_style` | `#aa00aa` | `#000000` |
| `cursor_style` | `#000000` | `#aa00aa` |
| `cursor_line_style` | не задан | `#1a1a1a` |
| `cursor_line_gutter_style` | `#aa00aa` | `#1a1a1a` |
| `selection_style` | `#000000` | `#aa00aa` |

## 4. blue (CRT Classic)

Палитра **CRT Classic** (стандартный вид Midnight Commander):
синий редактор, светло-голубой текст, голубые меню, жёлтые выделения и серые
диалоги.

### Палитра приложения

| Роль | Значение |
| :--- | :--- |
| `primary` | `#55ffff` |
| `secondary` | `#aaaaaa` |
| `accent` | `#ffff55` |
| `foreground` | `#55ffff` |
| `background` | `#0000aa` |
| `surface` | `#0000aa` |
| `panel` | `#00aaaa` |
| `success` | `#00ff00` |
| `warning` / `error` | `#ff00ff` |

### Переменные темы

| Переменная | Значение |
| :--- | :--- |
| `menu-background` | `#00aaaa` |
| `menu-foreground` | `#ffffff` |
| `menu-active-background` | `#000000` |
| `menu-active-foreground` | `#ffff55` |
| `editor-background` | `#0000aa` |
| `editor-foreground` | `#55ffff` |
| `status-background` | `#00aaaa` |
| `status-foreground` | `#000000` |
| `keybar-background` | `#000000` |
| `dialog-background` | `#aaaaaa` |
| `dialog-foreground` | `#000000` |

### Редактор `mark_editor_tui-blue`

| Стиль | Текст | Фон |
| :--- | :--- | :--- |
| `base_style` | `#55ffff` | `#0000aa` |
| `gutter_style` | `#ffff55` | `#0000aa` |
| `cursor_style` | `#000000` | `#00aaaa` |
| `cursor_line_style` | не задан | `#000080` |
| `cursor_line_gutter_style` | `#ffff55` | `#000080` |
| `selection_style` | `#000000` | `#00aaaa` |

В темах `default` и `blue` предупреждения и ошибки — magenta (`#ff00ff`), в
теме `green` — white (`#ffffff`), в теме `magenta` — dark red (`#aa0000`).