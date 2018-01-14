var messageContainer = document.getElementById("messages");
var infoContainer = document.getElementById("info");
var errorContainer = document.getElementById("error");

function WebSocketTest() {
    if ("WebSocket" in window) {
        infoContainer.innerText = "WebSocket is supported by your Browser!";
        var ws = new WebSocket("ws://localhost:8888/ws/");
        infoContainer.innerText += '\nws created';
        ws.onopen = function () {
            ws.send("Add me )");
            // infoContainer.innerText += '\nTry send to message';
        };
        ws.onmessage = function (ev) {
            var received_msg = ev.data;
            messageContainer.innerHTML = "Message is received :" + received_msg;
        };
        ws.onclose = function () {
            infoContainer.innerHTML += "\nConnection is closed...";
        };
        ws.onerror = function (ev) {
            errorContainer.innerHTML = ev;
        }
    } else {
        infoContainer.innerHTML = "WebSocket NOT supported by your Browser!";
    }
}

WebSocketTest();