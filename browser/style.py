"""CSS inheritance and cascade application for element trees."""

from .css_parser import CSSParser
from .element import Element
from .css_utils import css_size_to_px

INHERITED_PROPERTIES = {
    "font-family" : "Times",
    "font-size" : "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black"
}

class StyleResolver:
    """Resolve computed styles for an element tree.

    Keeping cascade and inheritance here gives callers a small object-oriented
    API while retaining the original ``style(node, rules)`` convenience
    function below.
    """

    def __init__(self, rules):
        """Prepare rules, expanding stylesheet shorthands once."""
        self.rules = [
            (selector, expand_declarations(declarations))
            for selector, declarations in rules
        ]

    def apply(self, node):
        """Apply computed styles to ``node`` and all of its descendants."""
        if not isinstance(node, Element):
            return

        node.style = self._inherited_style(node)
        self._apply_rules(node)
        self._apply_inline_style(node)
        self._resolve_font_size(node)

        for child in node.children:
            self.apply(child)

    def _inherited_style(self, node):
        parent_style = getattr(node.parent, "style", {}) if node.parent else {}
        style = {
            prop: parent_style.get(prop, default)
            for prop, default in INHERITED_PROPERTIES.items()
        }
        style["display"] = "inline"
        return style

    def _apply_rules(self, node):
        for selector, declarations in self.rules:
            if selector.matches(node):
                node.style.update(declarations)

    def _apply_inline_style(self, node):
        if "style" in node.attributes:
            declarations = CSSParser(node.attributes["style"]).body()
            node.style.update(expand_declarations(declarations))

    def _resolve_font_size(self, node):
        value = node.style["font-size"]
        parent_style = getattr(node.parent, "style", {}) if node.parent else {}
        parent_size = parent_style.get("font-size", INHERITED_PROPERTIES["font-size"])
        reference = css_size_to_px(parent_size)
        node.style["font-size"] = f"{css_size_to_px(value, reference)}px"


def style(node, rules):
    """Apply stylesheet and inline CSS declarations to an element subtree."""
    StyleResolver(rules).apply(node)

def expand_declarations(declarations):
    """Expand supported CSS shorthand declarations into longhand values.

    The returned dictionary is safe to reuse while styling multiple nodes;
    stylesheet declarations are therefore expanded once by ``StyleResolver``.
    """
    expanded = {}

    for prop, value in declarations.items():
        if prop == "font":
            expanded.update(expand_font_shorthand(value))
        else:
            expanded[prop] = value

    return expanded

def expand_font_shorthand(value):
    """Convert a CSS ``font`` shorthand value into longhand properties.

    Supported optional components are font style and weight, followed by a
    required size and family. A line-height after the size is accepted and
    ignored because layout does not currently use it.

    Raises:
        ValueError: If the size or family is missing.
    """
    FONT_STYLES = {"normal", "italic", "oblique"}
    FONT_WEIGHTS = {"normal", "bold", "bolder", "lighter"}

    tokens = value.split()

    style = "normal"
    weight = "normal"

    while tokens and tokens[0] in FONT_STYLES | FONT_WEIGHTS:
        token = tokens.pop(0)

        if token in FONT_STYLES:
            style = token
        else:
            weight = token

    if not tokens:
        raise ValueError("font shorthand is missing font-size")

    size = tokens.pop(0)

    if "/" in size:
        size, _line_height = size.split("/", 1)

    if not tokens:
        raise ValueError("font shorthand is missing font-family")

    family = " ".join(tokens)

    return {
        "font-style": style,
        "font-weight": weight,
        "font-size": size,
        "font-family": family
    }
