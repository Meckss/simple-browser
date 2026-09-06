import re
import tkinter.font

from text import Text
from tag import Tag

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
PARAGRAPH_STEP = 30
    
class Layout:
    
    def __init__(self, tokens, width):
        self.display_list = []
        self.width = width
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        
        for token in tokens:
            self.tokenize(token)
            
        self.content_height = self.cursor_y + VSTEP
        
    def tokenize(self, token):
        if isinstance(token, Text):
            for part in re.split(r"(\n+)", token.text):
                if part.startswith("\n"):
                    if part == "\n\n":
                        self.cursor_y += PARAGRAPH_STEP
                    else:
                        self.cursor_y += VSTEP

                    self.cursor_x = HSTEP
                    continue
                
                for word in part.split():
                    font = tkinter.font.Font(
                        size = 16,
                        weight = self.weight,
                        slant = self.style
                    )
                    word_width = font.measure(word)

                    if self.cursor_x + word_width >= self.width - HSTEP:
                        self.cursor_y += font.metrics("linespace") * 1.25
                        self.cursor_x = HSTEP

                    self.display_list.append((self.cursor_x, self.cursor_y, word, font))
                    self.cursor_x += word_width + font.measure(" ")
                    
        if isinstance(token, Tag):
            if token.tag == "i":
                self.style = "italic"
            elif token.tag == "/i":
                self.style = "roman"
            elif token.tag == "b":
                self.weight = "bold"
            elif token.tag == "/b":
                self.weight = "normal"
                
        
    