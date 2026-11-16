"""Application constants for the Mark Editor TUI."""

from __future__ import annotations

from pathlib import Path

APP_NAME = "Mark Editor TUI"
VERSION = "0.1.1"
RELEASE = "2026.11"

CONFIG_DIR = Path.home() / ".config" / "mark_editor"
THEME_FILE = CONFIG_DIR / "theme.json"

CACHE_DIR = Path.home() / ".cache" / "mark_editor_tui"
TEMP_MD = "Temp.md"

THEMES: tuple[str, ...] = ("default", "green", "magenta", "blue")
DEFAULT_THEME = "default"

PDF_FONT = "Noto Sans Mono"
PDF_CJK_FONTS: dict[str, str] = {
    "ja": "Noto Sans Mono CJK JP",
    "cn": "Noto Sans Mono CJK SC",
    "tw": "Noto Sans Mono CJK TC",
    "hk": "Noto Sans Mono CJK HK",
    "kr": "Noto Sans Mono CJK KR",
}
PDF_SYMBOL_FONT = "Symbola"

EMOJIS: list[str] = [
    "joy",
    "smile",
    "heart",
    "thumbsup",
    "thumbsdown",
    "wink",
    "tada",
    "rocket",
    "fire",
    "star",
    "cry",
    "thinking",
    "100",
    "sparkles",
    "eyes",
    "bulb",
    "warning",
    "ok",
    "check_mark",
]

SPECIAL_SIGNS: list[tuple[str, str]] = [
    ("copyright", "(c)"),
    ("trademark", "(tm)"),
    ("registered trademark", "(r)"),
    ("plus-minus", "+/-"),
    ("not equal to", "!="),
    ("logical equivalence", "<=>"),
    ("less-than/equal to", "<="),
    ("greater-than/equal to", ">="),
    ("left arrow", "<-"),
    ("right arrow", "->"),
    ("up arrow", "&uarr;"),
    ("down arrow", "&darr;"),
    ("logical implication", "=>"),
    ("slash", "&sol;"),
    ("backslash", "&bsol;"),
    ("left angle quote", "<<"),
    ("right angle quote", ">>"),
    ("left double quote", "&ldquo;"),
    ("right double quote", "&rdquo;"),
    ("em dash", "---"),
    ("en dash", "--"),
    ("ellipsis", "..."),
    ("non-breaking space", "&nbsp;"),
]

LANGUAGE_TAGS: tuple[str, ...] = (
    "de",
    "de-AT",
    "de-DE",
    "en",
    "en-GB",
    "en-US",
    "es",
    "fr",
    "ja",
    "it",
    "ko",
    "ko-KR",
    "pt",
    "pt-BR",
    "pt-PT",
    "ru",
    "uk",
    "zh",
    "zh-Hans-CN",
    "zh-Hant",
    "zh-Hant-HK",
    "zh-Hant-TW",
)

LANGUAGE_CODES: tuple[tuple[str, str], ...] = (
    ("de", "German (Generic)"),
    ("de-AT", "German (Austria)"),
    ("de-DE", "German (Germany)"),
    ("en", "English (Generic)"),
    ("en-GB", "British English (United Kingdom)"),
    ("en-US", "American English (United States)"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("it", "Italian"),
    ("ja", "Japanese"),
    ("ru", "Russian"),
    ("uk", "Ukrainian"),
    ("ko", "Korean (Generic)"),
    ("ko-KR", "Korean (South Korea)"),
    ("pt", "Portuguese (Generic)"),
    ("pt-BR", "Brazilian Portuguese (Brazil)"),
    ("pt-PT", "European Portuguese (Portugal)"),
    ("zh", "Chinese (Generic)"),
    ("zh-Hans-CN", "Simplified Chinese (Mainland China)"),
    ("zh-Hant", "Traditional Chinese (Generic)"),
    ("zh-Hant-HK", "Traditional Chinese (Hong Kong)"),
    ("zh-Hant-TW", "Traditional Chinese (Taiwan)"),
)

EXPORT_FORMATS: dict[str, str] = {
    "html": ".html",
    "html_css": ".html",
    "pdf": ".pdf",
    "pdf_landscape": ".pdf",
    "text": ".txt",
}
