import re
import tkinter.font

from .style import Style
from .text import Text
from .tag import Tag

WIDTH = 800
HSTEP, VSTEP = 13, 18
PARAGRAPH_STEP = 30
    
class Layout:
    def __init__(self, tokens, width):
        self.display_list = []
        self.width = width
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.fonts = {}
        self.style = Style()
        
        for token in tokens:
            self.process_token(token)
            
        self.content_height = self.cursor_y + VSTEP
        
    def process_token(self, token):
        if isinstance(token, Text):
            self.process_text(token)
                    
        elif isinstance(token, Tag):
            self.process_tag(token)
                
    def process_text(self, text):
        for part in re.split(r"(\n+)", text.text):
            if part.startswith("\n"):
                if len(part) >= 2:
                    self.cursor_y += PARAGRAPH_STEP
                else:
                    self.cursor_y += VSTEP

                self.cursor_x = HSTEP
                continue
            
            for word in part.split():
                font = self.get_font()
                word_width = font.measure(word)

                if self.cursor_x + word_width >= self.width - HSTEP:
                    self.cursor_y += font.metrics("linespace") * 1.25
                    self.cursor_x = HSTEP

                self.display_list.append((self.cursor_x, self.cursor_y, word, font))
                self.cursor_x += word_width + font.measure(" ")
                    
    def process_tag(self, tag):
        self.style.apply(tag)
    
    def get_font(self):
        key = (self.style.weight, self.style.slant, self.style.size)

        if key not in self.fonts:
            self.fonts[key] = tkinter.font.Font(
                size=self.style.size,
                weight=self.style.weight,
                slant=self.style.slant,
            )

        return self.fonts[key]