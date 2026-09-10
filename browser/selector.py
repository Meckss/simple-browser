"""Selectors used to match elements in the browser's document tree."""

from .element import Element


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

        if isinstance(ancestor, DescendantSelector):
            self.selectors = ancestor.selectors + (descendant,)
        else:
            self.selectors = (ancestor, descendant)
        
    def matches(self, node):
        """Return whether ``node`` matches below the selected ancestor.

        The node itself must match ``descendant`` and at least one of its
        parents must match ``ancestor``.

        Args:
            node: The node to test.

        Returns:
            ``True`` if both selector conditions are met; otherwise, ``False``.
        """
        selector_index = len(self.selectors) - 1
        if not self.selectors[selector_index].matches(node):
            return False

        selector_index -= 1
        node = node.parent
        while node is not None:
            if self.selectors[selector_index].matches(node):
                selector_index -= 1
                if selector_index < 0:
                    return True
            node = node.parent
        return False
    
class ClassSelector:
    """Select elements whose attributes contains the requested class"""
    
    def __init__(self, class_name):
        """Create a class selector
        
        Args:
            class: The class name to match, such as "warn"
        """
        self.class_name = class_name
        self.priority = 10
        
    def matches(self, node):
        """Return whether ``node`` is an element with the selected class.
        
            Args:
                node: The node to test.
    
            Returns:
                ``True`` when ``node`` is an element with the selected class;
                otherwise, ``False``.
        """
        if not isinstance(node, Element):
            return False
        classes = node.attributes.get("class")
        if classes is None:
            return False
        return self.class_name in classes.split()


class SelectorSequence:
    """Select elements matching several simple selectors at once.

    A sequence represents a compound selector, such as ``p.warning`` or
    ``.warning.important``.  Every selector in the sequence is tested against
    the same element; descendant relationships are represented separately by
    :class:`DescendantSelector`.
    """

    def __init__(self, selectors):
        """Create a compound selector from an iterable of simple selectors."""
        self.selectors = tuple(selectors)
        if not self.selectors:
            raise ValueError("A selector sequence cannot be empty")
        self.priority = sum(selector.priority for selector in self.selectors)

    def matches(self, node):
        """Return whether every selector matches ``node``."""
        return all(selector.matches(node) for selector in self.selectors)


def cascade_priority(rule):
    """Return the selector priority used to order a CSS rule."""
    selector, _ = rule
    return selector.priority
