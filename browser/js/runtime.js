console = { log: function(x) { call_python("log", x); } }
function Node(handle) { this.handle = handle; }
Node.prototype.getAttribute = function(attr) {
    return call_python("getAttribute", this.handle, attr);
}

document = { querySelectorAll: function(s) {
    var handles = call_python("querySelectorAll", s);
    return handles.map(function(h) { return new Node(h) });
}}

inputs = document.querySelectorAll('input')
for (var i = 0; i < inputs.length; i++) {
    var names = inputs[i].getAttribute("name");
    var value = inputs[i].getAttribute("value");
    if (value.length > 100) {
        console.log("Input " + names + " has too much text.")
    }
}

console.log("Hi from JS!")