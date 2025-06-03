function login() {
    const xhr = new XMLHttpRequest();
    const username = document.getElementById("username").value;
    xhr.open("POST", "/api/login", true);
    xhr.setRequestHeader("Content-Type", "text/plain");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status == 200) { //login success
                alert(xhr.responseText);
            } else {
                alert("Error: " + xhr.status + " - " + xhr.responseText);
            }
        }
    };
    xhr.send(username);
}

function logout() {
    const xhr = new XMLHttpRequest();
    xhr.open("DELETE", "/api/login", true);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE) {
                alert(xhr.responseText);
        }
    };
    xhr.send();
}
