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

VAR_FUNCTION = re.compile(r"var\(", re.IGNORECASE)


def _is_custom_property(prop):
    """Return whether *prop* is a CSS custom property name."""
    return prop.startswith("--")


def _split_var_arguments(arguments):
    """Split a var() argument into its name and optional fallback."""
    depth = 0
    for index, char in enumerate(arguments):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            return arguments[:index].strip(), arguments[index + 1:].strip()
    return arguments.strip(), None


def _substitute_vars(value, custom_properties, resolving=None):
    """Substitute CSS var() functions, returning None for invalid values."""
    resolving = set() if resolving is None else resolving
    output = []
    index = 0
    while index < len(value):
        match = VAR_FUNCTION.search(value, index)
        if match is None:
            output.append(value[index:])
            break

        output.append(value[index:match.start()])
        open_paren = match.end() - 1
        depth = 1
        close_paren = open_paren + 1
        while close_paren < len(value) and depth:
            if value[close_paren] == "(":
                depth += 1
            elif value[close_paren] == ")":
                depth -= 1
            close_paren += 1
        if depth:
            return None

        name, fallback = _split_var_arguments(
            value[open_paren + 1:close_paren - 1]
        )
        if name in custom_properties and name not in resolving:
            replacement = _substitute_vars(
                custom_properties[name], custom_properties, resolving | {name}
            )
        else:
            replacement = fallback
            if replacement is not None and "var(" in replacement.lower():
                replacement = _substitute_vars(replacement, custom_properties,
                                               resolving)
        if replacement is None:
            return None
        output.append(replacement)
        index = close_paren
    return "".join(output)

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
        self._resolve_inherit(node)
        self._resolve_custom_properties(node)
        self._resolve_font_size(node)

        for child in node.children:
            self.apply(child)

    def _inherited_style(self, node):
        parent_style = getattr(node.parent, "style", {}) if node.parent else {}
        style = {
            prop: parent_style.get(prop, default)
            for prop, default in INHERITED_PROPERTIES.items()
        }
        style.update({
            prop: value for prop, value in parent_style.items()
            if _is_custom_property(prop)
        })
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

    def _resolve_custom_properties(self, node):
        """Resolve var() references in declarations on the styled element."""
        custom_properties = {
            prop: value for prop, value in node.style.items()
            if _is_custom_property(prop)
        }
        for prop, value in list(custom_properties.items()):
            resolved = _substitute_vars(value, custom_properties, {prop})
            if resolved is None:
                node.style.pop(prop, None)
                custom_properties.pop(prop, None)
            else:
                node.style[prop] = resolved
                custom_properties[prop] = resolved

        for prop, value in list(node.style.items()):
            if not _is_custom_property(prop) and "var(" in value.lower():
                resolved = _substitute_vars(value, custom_properties)
                if resolved is None:
                    inherited = self._inherited_style(node)
                    if prop in inherited:
                        node.style[prop] = inherited[prop]
                    else:
                        node.style.pop(prop, None)
                else:
                    if prop == "font":
                        try:
                            expanded = expand_font_shorthand(resolved)
                        except ValueError:
                            expanded = None
                        if expanded is None:
                            node.style.pop(prop, None)
                        else:
                            node.style.pop(prop)
                            node.style.update(expanded)
                    else:
                        node.style[prop] = resolved

    def _resolve_inherit(self, node):
        """Resolve explicit CSS ``inherit`` values after the cascade."""
        parent_style = getattr(node.parent, "style", {}) if node.parent else {}

        for prop, value in list(node.style.items()):
            if not isinstance(value, str) or value.strip().lower() != "inherit":
                continue

            if prop in parent_style:
                node.style[prop] = parent_style[prop]
            elif prop in INHERITED_PROPERTIES:
                node.style[prop] = INHERITED_PROPERTIES[prop]
            else:
                node.style.pop(prop, None)

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
            if prop == "font" and "var(" not in value.lower()
            else {prop: value}
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
