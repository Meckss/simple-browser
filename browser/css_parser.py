from .selector import TagSelector
from .selector import DescendantSelector

class CSSParser:
    def __init__(self, s):
        """
        Initializes the CSS parser

        Args:
            s (str): The CSS text to parse
        """
        self.i = 0
        self.s = s
    
    
    def word(self):
        """
        Parse and returns the word starting at the current index
        
        Returns:
            str: The parsed word
            
        Raises: 
            ValueError: If no word is found at the current index
        """
        
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else: 
                break
        if not self.i > start:
            raise ValueError("Word parsing error")
        return self.s[start:self.i]
    
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
        val = self.word()
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
    
    def selector(self):
        """Parse a descendant selector at the current input position.

        Selectors consist of one or more tag names separated by whitespace,
        such as ``"div p"``. The first tag becomes the ancestor-most
        selector, and each subsequent tag is nested as a
        :class:`DescendantSelector`.

        Returns:
            TagSelector | DescendantSelector: The selector represented by the
            parsed tag names.

        Raises:
            ValueError: If no tag name can be parsed at the current position.
        """
        out = TagSelector(self.word().casefold())
        self.whitespace()
        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.casefold())
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
