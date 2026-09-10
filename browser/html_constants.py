"""HTML tag groups used by the forgiving HTML parser."""

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]

IMPLICITLY_CLOSED_BY_SAME_TAG = {"p", "li"}

HEAD_TAGS = [
    "base", "basefont", "bgsound", "noscript",
    "link", "meta", "title", "style", "script",
]

RAW_TEXT_TAGS = {"script", "style"}

# Named character references supported by the parser. Numeric references are
# handled by ``unescape`` in html_parser.py.
HTML_ENTITIES = {
    "amp": "&",
    "apos": "'",
    "gt": ">",
    "lt": "<",
    "nbsp": "\xa0",
    "quot": '"',
    "copy": "\xa9",
    "reg": "\xae",
    "trade": "\u2122",
    "hellip": "\u2026",
    "ndash": "\u2013",
    "mdash": "\u2014",
    "lsquo": "\u2018",
    "rsquo": "\u2019",
    "ldquo": "\u201c",
    "rdquo": "\u201d",
    "bull": "\u2022",
    "cent": "\xa2",
    "pound": "\xa3",
    "yen": "\xa5",
    "euro": "\u20ac",
}

LEGACY_ENTITIES = {"amp", "apos", "gt", "lt", "nbsp", "quot"}
