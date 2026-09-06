from text import Text
from tag import Tag

def parse_html(body):
    tokens = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: 
                tokens.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            tokens.append(Tag(buffer))
            buffer = ""
        else: 
            buffer += c
    
    if buffer:
        if in_tag:
            tokens.append(Text("<" + buffer))
        else:
            tokens.append(Text(buffer))
            
    return tokens
    
    