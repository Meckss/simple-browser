"""CSS inheritance and cascade application for element trees."""

from .css_parser import CSSParser
from .element import Element

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
        self.rules = rules

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
        return {
            prop: parent_style.get(prop, default)
            for prop, default in INHERITED_PROPERTIES.items()
        }

    def _apply_rules(self, node):
        for selector, declarations in self.rules:
            if selector.matches(node):
                node.style.update(declarations)

    def _apply_inline_style(self, node):
        if "style" in node.attributes:
            node.style.update(CSSParser(node.attributes["style"]).body())

    def _resolve_font_size(self, node):
        value = node.style["font-size"]
        if not value.endswith("%"):
            return
        parent_style = getattr(node.parent, "style", {}) if node.parent else {}
        parent_size = parent_style.get("font-size", INHERITED_PROPERTIES["font-size"])
        percentage = float(value[:-1]) / 100
        pixels = float(parent_size[:-2])
        node.style["font-size"] = f"{percentage * pixels}px"


def style(node, rules):
    """Apply stylesheet and inline CSS declarations to an element subtree."""
    StyleResolver(rules).apply(node)
