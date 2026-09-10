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
