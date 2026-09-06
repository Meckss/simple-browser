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
        self.line =[]
        
        for token in tokens:
            self.process_token(token)
            
        self.flush()
        self.content_height = self.cursor_y + VSTEP
        
    def process_token(self, token):
        if isinstance(token, Text):
            self.process_text(token)
                    
        elif isinstance(token, Tag):
            self.process_tag(token)
                
    def process_text(self, text):
        content = re.sub(r"\s+", " ", text.text)

        for word in content.split():
            font = self.get_font()
            word_width = font.measure(word)
            space_width = font.measure(" ")

            required_width = word_width
            if self.line:
                required_width += space_width

            if self.cursor_x + required_width > self.width - HSTEP:
                self.flush()

            self.line.append((self.cursor_x, word, font))
            self.cursor_x += word_width + space_width
                    
    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        
        baseline = self.cursor_y + 1.25 * max_ascent
        
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x,y,word,font))
        
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        
        self.cursor_x = HSTEP
        self.line = []

    
    def process_tag(self, tag):
        self.style.apply(tag)
        
        if tag.tag == "br":
            self.flush()
            self.cursor_y += VSTEP
        
        elif tag.tag == "/p":
            self.flush()
            self.cursor_y += PARAGRAPH_STEP
    
    def get_font(self):
        key = (self.style.weight, self.style.slant, self.style.size)

        if key not in self.fonts:
            self.fonts[key] = tkinter.font.Font(
                size=self.style.size,
                weight=self.style.weight,
                slant=self.style.slant,
            )

        return self.fonts[key]