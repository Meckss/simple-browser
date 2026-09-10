"""CSS inheritance and cascade application for element trees."""

import re

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
            (selector, _expand_declarations_with_importance(declarations))
            for selector, declarations in rules
        ]

    def apply(self, node):
        """Apply computed styles to ``node`` and all of its descendants."""
        if not isinstance(node, Element):
            return

        node.style = self._inherited_style(node)
        winners = self._apply_rules(node)
        self._apply_inline_style(node, winners)
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
        winners = {}
        for rule_order, (selector, declarations) in enumerate(self.rules):
            if selector.matches(node):
                for prop, (value, important) in declarations.items():
                    priority = (int(important), 0, selector.priority, rule_order)
                    if prop not in winners or priority >= winners[prop][0]:
                        winners[prop] = (priority, value)

        for prop, (_priority, value) in winners.items():
            node.style[prop] = value
        return winners

    def _apply_inline_style(self, node, winners):
        if "style" in node.attributes:
            declarations = CSSParser(node.attributes["style"]).body()
            declarations = _expand_declarations_with_importance(declarations)
            for prop, (value, important) in declarations.items():
                priority = (int(important), 1, 0, len(self.rules))
                if prop not in winners or priority >= winners[prop][0]:
                    node.style[prop] = value

    def _resolve_font_size(self, node):
        value = node.style["font-size"]
        parent_style = getattr(node.parent, "style", {}) if node.parent else {}
        parent_size = parent_style.get("font-size", INHERITED_PROPERTIES["font-size"])
        reference = css_size_to_px(parent_size)
        node.style["font-size"] = f"{css_size_to_px(value, reference)}px"


def style(node, rules):
    """Apply stylesheet and inline CSS declarations to an element subtree."""
    StyleResolver(rules).apply(node)

IMPORTANT_SUFFIX = re.compile(r"\s*!\s*important\s*$", re.IGNORECASE)


def _split_important(value):
    """Return a declaration value and its CSS importance flag."""
    match = IMPORTANT_SUFFIX.search(value)
    if match is None:
        return value.strip(), False
    return value[:match.start()].rstrip(), True


def _expand_declarations_with_importance(declarations):
    """Expand declarations while retaining importance for every longhand."""
    expanded = {}
    for prop, raw_value in declarations.items():
        value, important = _split_important(raw_value)
        values = (
            expand_font_shorthand(value)
            if prop == "font" else {prop: value}
        )
        for expanded_prop, expanded_value in values.items():
            expanded[expanded_prop] = (expanded_value, important)
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
