"""Helpers for converting CSS length values to pixels."""


def css_size_to_px(value, reference=None):
    """Convert a CSS size to pixels.

    ``reference`` is the containing size used to resolve percentages.  A
    reference is required for percentage values because their pixel value
    depends on the property being laid out.

    Supported units are unitless numbers, ``px``, ``pt``, ``em``, ``rem``,
    and ``%``.  ``reference`` is also the font size used to resolve ``em``
    values; callers should pass the appropriate reference for the property.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        raise ValueError(f"Unsupported CSS size: {value!r}")

    value = value.strip().lower()
    if value.endswith("px"):
        return float(value[:-2])
    if value.endswith("pt"):
        return float(value[:-2]) * 96 / 72
    if value.endswith("rem"):
        return float(value[:-3]) * 16
    if value.endswith("em"):
        if reference is None:
            raise ValueError("A reference size is required for em values")
        return float(value[:-2]) * float(reference)
    if value == ("inherit"):
        if reference is None:
            raise ValueError("A refernece size is required for inherit values")
        return float(reference)
    if value.endswith("%"):
        if reference is None:
            raise ValueError("A reference size is required for percentages")
        return float(value[:-1]) * float(reference) / 100
    return float(value)
