"""Expose a small JavaScript and DOM bridge for a browser tab."""

from pathlib import Path

import dukpy

from browser.css.parser import CSSParser
from ..html.parser import HTMLParser
from ..html.text import Text


class JSContext:
    """Execute page scripts and expose selected browser APIs to JavaScript."""

    RUNTIME_JS = Path(__file__).with_name("runtime.js").read_text()
    EVENT_DISPATCH_JS = "new Node(dukpy.handle).dispatchEvent(dukpy.event_type)"

    def __init__(self, tab):
        """Create a JavaScript interpreter associated with ``tab``.

        Args:
            tab: The :class:`~browser.ui.tab.Tab` whose parsed document is
                exposed to JavaScript.
        """
        self.tab = tab
        self.node_to_handle = {}
        self.handle_to_node = {}
        self.next_handle = 0
        self.interpreter = dukpy.JSInterpreter()
        self.install_exports()
        self.interpreter.evaljs(self.RUNTIME_JS)

    def install_exports(self):
        """Register Python callbacks used by the JavaScript runtime.

        The callbacks are installed on the current Dukpy interpreter. This
        method must be called after creating or replacing
        :attr:`interpreter`, and it does not execute the runtime source.
        """
        self.interpreter.export_function("log", print)
        self.interpreter.export_function("querySelectorAll", self.query_selector_all)
        self.interpreter.export_function("getAttribute", self.get_attributes)
        self.interpreter.export_function("innerHTML_set", self.innerHTML_set)
        self.interpreter.export_function("textContent_set", self.textContent_set)

    def run(self, script):
        """Run page JavaScript and report interpreter errors.

        Args:
            script: JavaScript source code to evaluate.

        Returns:
            The value returned by Dukpy, or ``None`` if the script fails.
        """
        try:
            return self.interpreter.evaljs(script)
        except dukpy.JSRuntimeError as e:
            print("Script", script, "crashed", e)

    def query_selector_all(self, selector_text):
        """Return handles for elements matching a CSS selector.

        ``Tab.elementNodes`` is a flat, document-order list of element
        nodes, so matching it directly avoids treating the list itself as a
        tree node.

        Args:
            selector_text: CSS selector text understood by ``CSSParser``.

        Returns:
            A list of integer handles for matching elements.
        """
        selector = CSSParser(selector_text).selector()
        nodes = [node for node in self.tab.elementNodes if selector.matches(node)]
        return [self.get_handle(node) for node in nodes]

    def get_handle(self, elt):
        """Return the stable JavaScript handle assigned to an element.

        Handles are unique for the lifetime of this document's JavaScript
        context. The counter is intentionally monotonic so that removing a
        handle later cannot cause a stale JavaScript wrapper to refer to a
        different element.

        Args:
            elt: The parsed HTML element to expose to JavaScript.

        Returns:
            An integer handle that can be passed back through the bridge.
        """
        if elt not in self.node_to_handle:
            handle = self.next_handle
            self.next_handle += 1
            self.node_to_handle[elt] = handle
            self.handle_to_node[handle] = elt
        else:
            handle = self.node_to_handle[elt]
        return handle

    def get_attributes(self, handle, attr):
        """Return one element attribute for a JavaScript node handle.

        Missing attributes are represented as an empty string, matching the
        behavior expected from the small ``Node.getAttribute`` wrapper in
        ``runtime.js``.

        Args:
            handle: Integer handle previously returned by :meth:`get_handle`.
            attr: Attribute name to read.

        Returns:
            The attribute value, or ``""`` when the attribute is absent.
        """
        node = self.handle_to_node[handle]
        attr = node.attributes.get(attr, None)
        return attr if attr else ""

    def dispatch_event(self, event_type, elt):
        """Dispatch an event to an element's registered JavaScript listeners.

        The element is converted to its stable integer handle before the
        event is dispatched inside the JavaScript interpreter. Listeners run
        with the element's ``Node`` wrapper as ``this``.

        Args:
            event_type: The event type, e.g. ``"click"`` or ``"submit"``.
            elt: The parsed HTML element to dispatch the event to.
        """
        handle = self.get_handle(elt)
        self.interpreter.evaljs(
            self.EVENT_DISPATCH_JS,
            event_type=event_type,
            handle=handle,
        )

    def innerHTML_set(self, handle, s):
        """Replace an element's children with an HTML fragment.

        Args:
            handle: Integer handle for the element to update.
            s: HTML source to parse as the element's new contents.
        """
        doc = HTMLParser("<html><body>" + s + "</body></html>").parse_html()
        new_nodes = doc.children[0].children
        elt = self.handle_to_node[handle]
        elt.children = new_nodes
        for child in elt.children:
            child.parent = elt

        self.tab.relayout()

    def textContent_set(self, handle, value):
        """Replace an element's children with one literal text node.

        Args:
            handle: Integer handle for the element to update.
            value: Text value to assign, or an empty string to clear it.
        """
        elt = self.handle_to_node[handle]
        elt.children = [] if value == "" else [Text(value, elt)]
        self.tab.relayout()

    def reset_document(self):
        """Replace the JavaScript environment for the current document.

        Navigation invalidates all handles and page-owned JavaScript state.
        Clearing the Python-side maps releases the old DOM elements, while
        replacing the interpreter releases JavaScript listeners and globals
        belonging to the previous document. The caller must update the tab's
        parsed document and ``elementNodes`` before calling this method so the
        runtime can initialize against the new DOM.
        """
        self.node_to_handle.clear()
        self.handle_to_node.clear()
        self.next_handle = 0

        self.interpreter = dukpy.JSInterpreter()
        self.install_exports()
        self.interpreter.evaljs(self.RUNTIME_JS)
