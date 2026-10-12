from pathlib import Path

from browser.css.parser import CSSParser
from browser.html.tree_utils import tree_to_list
import dukpy

class JSContext:
    RUNTIME_JS = (Path(__file__).with_name("runtime.js").read_text())

    def __init__(self, tab):
        self.tab = tab
        self.node_to_handle = {}
        self.handle_to_node = {}
        self.interpreter = dukpy.JSInterpreter()
        self.interpreter.export_function("log", print)
        self.interpreter.export_function("querySelectorAll", self.query_selector_all)
        self.interpreter.evaljs(self.RUNTIME_JS)

    def run(self, script):
        """Run the given JavaScript code in the context of this interpreter."""
        try:
            return self.interpreter.evaljs(script)
        except dukpy.JSRuntimeError as e:
            print("Script", script, "crashed", e)

    def query_selector_all(self, selector_text):
        selector = CSSParser(selector_text).selector()
        nodes = [node for node in self.tab.elementNodes if selector.matches(node)]
        return [self.get_handle(node) for node in nodes]
    
    def get_handle(self, elt):
        if elt not in self.node_to_handle:
            handle = len(self.node_to_handle)
            self.node_to_handle[elt] = handle
            self.handle_to_node[handle] = elt
        else:
            handle = self.node_to_handle[elt]
        return handle
    
    def get_attributes(self, handle, attr):
        node = self.handle_to_node[handle]
        attr = node.attributes.get(attr, None)
        return attr if attr else ""