"""Shared font construction and caching for layout objects."""

from .css_utils import css_size_to_px
from .font import Font


FONT_CACHE = {}


def _font_weight_for_tk(weight):
    """Map a CSS font weight to a value accepted by Tk."""
    if isinstance(weight, (int, float)):
        return "bold" if weight >= 600 else "normal"

    value = str(weight).strip().lower()
    if value in {"bold", "bolder"}:
        return "bold"
    if value in {"normal", "lighter"}:
        return "normal"

    try:
        return "bold" if int(value) >= 600 else "normal"
    except ValueError:
        return "normal"


def get_font(node):
    """Return a cached font matching a styled node's computed properties.

    Args:
        node: The styled element whose font should be constructed.

    Returns:
        A shared :class:`Font` instance for the node's font settings.
    """
    styles = getattr(node, "style", {})
    size = styles.get("font-size", "16px")
    size = int(round(css_size_to_px(size)))

    weight = _font_weight_for_tk(styles.get("font-weight", "normal"))
    slant = styles.get("font-style", "normal")
    if slant == "normal":
        slant = "roman"

    family = styles.get("font-family", "Times")
    key = (family, size, weight, slant)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = Font(family, size, weight, slant)
    return FONT_CACHE[key]
