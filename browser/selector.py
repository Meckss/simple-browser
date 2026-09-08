from .element import Element


"""Selectors used to match elements in the browser's document tree."""


class TagSelector:
    """Select elements whose tag name matches a requested tag."""

    def __init__(self, tag):
        """Create a tag selector.

        Args:
            tag: The tag name to match, such as ``"p"`` or ``"div"``.
        """
        self.tag = tag
        self.priority = 1
        
    def matches(self, node):
        """Return whether ``node`` is an element with the selected tag.

        Args:
            node: The node to test.

        Returns:
            ``True`` when ``node`` is an element with the selected tag;
            otherwise, ``False``.
        """
        return isinstance(node, Element) and self.tag == node.tag
        
class DescendantSelector:
    """Select nodes matching a selector below a matching ancestor."""

    def __init__(self, ancestor, descendant):
        """Create a selector for an ancestor-descendant relationship.

        Args:
            ancestor: Selector that must match an ancestor of the node.
            descendant: Selector that must match the node itself.
        """
        self.ancestor = ancestor
        self.descendant = descendant
        self.priority = ancestor.priority + descendant.priority
        
    def matches(self, node):
        """Return whether ``node`` matches below the selected ancestor.

        The node itself must match ``descendant`` and at least one of its
        parents must match ``ancestor``.

        Args:
            node: The node to test.

        Returns:
            ``True`` if both selector conditions are met; otherwise, ``False``.
        """
        if not self.descendant.matches(node):
            return False
        while node.parent:
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False

def cascade_priority(rule):
    selector, _ = rule
    return selector.priority