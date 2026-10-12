// Minimal browser-side runtime shared by page scripts.

// Forward console output to the Python browser process.
console = { log: function(x) { call_python("log", x); } }

// Lightweight DOM node wrapper. The Python side stores the actual element
// and JavaScript keeps only its integer handle.
function Node(handle) { this.handle = handle; }
Node.prototype.getAttribute = function(attr) {
    return call_python("getAttribute", this.handle, attr);
}

// Return lightweight Node wrappers for elements selected by CSS selector.
document = { querySelectorAll: function(s) {
    var handles = call_python("querySelectorAll", s);
    return handles.map(function(h) { return new Node(h) });
}}

// Smoke-test the DOM bridge and warn about unusually large input values.
inputs = document.querySelectorAll('input')
for (var i = 0; i < inputs.length; i++) {
    var names = inputs[i].getAttribute("name");
    var value = inputs[i].getAttribute("value");
    if (value.length > 100) {
        console.log("Input " + names + " has too much text.")
    }
}

console.log("Hi from JS!")
