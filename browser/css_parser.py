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
        while self.i < len(self.s):
            try:
                prop, val = self.pair()
                pairs[prop] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except ValueError:
                why = self.ignore_until([";"])
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
