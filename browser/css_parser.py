"""Parser for the browser's small tag-and-descendant CSS subset."""

from .selector import TagSelector
from .selector import DescendantSelector
from .selector import ClassSelector
from .selector import SelectorSequence

class CSSParser:
    """Parse simple CSS rules into selectors and declaration dictionaries."""
    def __init__(self, s):
        """
        Initializes the CSS parser

        Args:
            s (str): The CSS text to parse
        """
        self.i = 0
        self.s = s
    
    def word(self):
        """Parse a CSS identifier/token."""
        start = self.i
        while self.i < len(self.s) and (
            self.s[self.i].isalnum() or self.s[self.i] in "#-.%"
        ):
            self.i += 1
        if self.i == start:
            raise ValueError("Word parsing error")
        return self.s[start:self.i]

    def value(self):
        """
        Parse and returns the value starting at the current index

        Returns:
            str: The parsed value

        Raises:
            ValueError: If no value is found at the current index
        """

        start = self.i
        while self.i < len(self.s) and self.s[self.i] not in ";}":
            self.i += 1
        if not self.i > start:
            raise ValueError("Value parsing error")
        return self.s[start:self.i].strip()

    def literal(self, literal):
        """
        Parses and moves the index to after the input literal

        Args:
            literal (str): The literal expected at the current index

        Raises:
            ValueError: If the expected literal is not found
        """
        if self.i >= len(self.s) or self.s[self.i] != literal:
            raise ValueError("Literal parsing error")
        self.i += 1

    def whitespace(self):
        """
        Advances past any whitespace characters
        """ 
        while (self.i < len(self.s) and self.s[self.i].isspace()):
            self.i += 1
    
    def pair(self):
        """
        Parses a CSS property-value pair

        Returns:
            tuple[str, str]: The property name, converted to lowercase, and its value
            
        Raises: 
            ValueError: If the property, value or colon cannot be parsed
        """
        prop = self.word()
        self.whitespace()
        self.literal(":")
        self.whitespace()

        val = self.value()
        if not val:
            raise ValueError("Missing property value")

        return prop.casefold(), val
    
    def body(self):
        """
        Parse the CSS body into a dictionary of property-value pairs
        
        Returns:
            dict[str,str]: A dictionary mapping CSS properties to values.
        """
        pairs = {}
        while self.i < len(self.s) and self.s[self.i] != "}":
            try:
                prop, val = self.pair()
                pairs[prop] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except ValueError:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        return pairs
            
    def ignore_until(self, chars):
        """
        Advances until one of the specified character values is found

        Args:
            chars (str): Characters that mark the stopping point

        Returns:
            str | None: The matching character, or `None` if the end is reached
        """
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            self.i += 1
        return None
    
    def selector_sequence(self):
        """Parse a compound selector at the current input position.

        Compound selectors have no whitespace between their components, for
        example ``div.warning`` or ``.warning.important``.
        """
        selectors = []
        if self.s[self.i] == ".":
            self.i += 1
            selectors.append(ClassSelector(self.selector_word().casefold()))
        else:
            selectors.append(TagSelector(self.selector_word().casefold()))

        while self.i < len(self.s) and self.s[self.i] == ".":
            self.i += 1
            selectors.append(ClassSelector(self.selector_word().casefold()))

        return selectors[0] if len(selectors) == 1 \
            else SelectorSequence(selectors)

    def selector_word(self):
        """Parse a tag or class name without consuming a selector delimiter."""
        start = self.i
        while self.i < len(self.s) and (
            self.s[self.i].isalnum() or self.s[self.i] in "-_"
        ):
            self.i += 1
        if self.i == start:
            raise ValueError("Selector parsing error")
        return self.s[start:self.i]

    def selector(self):
        """Parse a selector containing compound and descendant selectors.

        Whitespace separates descendants, while adjacent tag/class components
        form a :class:`SelectorSequence` matching one element. For example,
        ``"main .warning.important"`` means a warning and important element
        somewhere below ``main``.

        Returns:
            SelectorSequence | DescendantSelector: The parsed selector.

        Raises:
            ValueError: If no tag name can be parsed at the current position.
        """
        self.whitespace()
        if self.i >= len(self.s):
            raise ValueError("Missing selector")
        
        out = self.selector_sequence()
        self.whitespace()

        while self.i < len(self.s) and self.s[self.i] != "{":
            descendant = self.selector_sequence()
            out = DescendantSelector(out, descendant)
            self.whitespace()
        return out
    
    def parse(self):
        """Parse the CSS text into selector and declaration rules.

        Each rule has the form ``selector { property: value; }``. Whitespace
        is ignored, property names are normalized to lowercase, and malformed
        input is skipped through the end of the current rule when possible.
        Parsing starts at the current input position.

        Returns:
            list[tuple[TagSelector | DescendantSelector, dict[str, str]]]:
            Parsed selector/body pairs, where each body maps CSS property
            names to their values.
        """
        rules = []
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector()
                self.literal("{")
                self.whitespace()
                body = self.body()
                self.literal("}")
                rules.append((selector, body))
            except ValueError:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break
        return rules
