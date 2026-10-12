// Minimal browser-side runtime shared by page scripts.

// Forward console output to the Python browser process.
console = { log: function(x) { call_python("log", x); } };

/** Map element handles to their listeners, grouped by event type. */
var LISTENERS = {};

/**
 * Lightweight DOM node wrapper backed by a Python-side element.
 *
 * @param {number} handle Integer handle for the wrapped element.
 */
function Node(handle) { this.handle = handle; }

/**
 * Register a callback for an event type on this node.
 *
 * @param {string} type Event type, such as "click" or "keydown".
 * @param {Function} listener Callback invoked when the event is dispatched.
 */
Node.prototype.addEventListener = function(type, listener) {
    if (!LISTENERS[this.handle]) LISTENERS[this.handle] = {};
    var dict = LISTENERS[this.handle];
    if (!dict[type]) dict[type] = [];
    var list = dict[type];
    list.push(listener);
};

/**
 * Invoke callbacks registered for an event on this node.
 *
 * @param {string} type Event type to dispatch.
 */
Node.prototype.dispatchEvent = function(type) {
    var handle = this.handle;
    var list = (LISTENERS[handle] && LISTENERS[handle][type]) || [];
    for (var i = 0; i < list.length; i++) {
        list[i].call(this);
    }
};

/**
 * Warn when an input's current value exceeds the browser's simple limit.
 *
 * @this {Node} Input node receiving the keydown event.
 */
function lengthCheck() {
    var name = this.getAttribute("name");
    var value = this.getAttribute("value");
    if (value.length > 100) {
        console.log("Input " + name + " has too much text.");
    }
}

/** Return the value of an attribute on the wrapped element. */
Node.prototype.getAttribute = function(attr) {
    return call_python("getAttribute", this.handle, attr);
};

/**
 * Return lightweight Node wrappers for elements selected by a CSS selector.
 *
 * @param {string} s CSS selector text.
 * @returns {Node[]} Matching node wrappers.
 */
var document = { querySelectorAll: function(s) {
    var handles = call_python("querySelectorAll", s);
    return handles.map(function(h) { return new Node(h); });
} };

// Install the built-in input listener after the DOM bridge is available.
var inputs = document.querySelectorAll("input");
for (var i = 0; i < inputs.length; i++) {
    inputs[i].addEventListener("keydown", lengthCheck);
}

console.log("Hi from JS!");
