window.onload = function () {
    check_login_status();
    list()
}

function login() {
    /*
    login() attempts to login a user by sending an HTTP request to the webserver
    */
    const xhr = new XMLHttpRequest();
    const username = document.getElementById("username").value;
    xhr.open("POST", "/api/login", true);
    xhr.withCredentials = true
    xhr.setRequestHeader("Content-Type", "text/plain");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status == 200) { //login success
                set_logged_in(true, username)
                //alert(xhr.responseText);
            } else {
                alert("Error: " + xhr.status + " - " + xhr.responseText);
            }
        }
    };
    xhr.send(username);
}

function logout() {
    /*
    logout() logs out a user by sending an HTTP request to the webserver
    */
    const xhr = new XMLHttpRequest();
    xhr.open("DELETE", "/api/login", true);
    xhr.withCredentials = true
    xhr.onreadystatechange = function () {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            set_logged_in(false);
        }
    };
    xhr.send();
}

function check_login_status() {
    /*
    check_login_status() checks if the user is logged in via an api request
    */
   const xhr = new XMLHttpRequest();
   xhr.open("GET", "/api/login", true);
   xhr.withCredentials = true;
   xhr.onreadystatechange = function () {
        if (xhr.readyState == XMLHttpRequest.DONE) {
            if(xhr.status == 200) {
                const username = xhr.responseText;
                set_logged_in(true, username);
            } else {
                set_logged_in(false);
            }
        } 
   };
   xhr.send()
}

function list() {
  const xhr = new XMLHttpRequest();
  xhr.open("GET", "/api/list", true);

  xhr.onreadystatechange = function () {
    if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
      const response = xhr.responseText.trim();
      const tableWrapper = document.getElementById("fileTableWrapper");
      const tableBody = document.querySelector("#fileTable tbody");
      const emptyMessage = document.getElementById("emptyMessage");

      tableBody.innerHTML = ""; // clear previous rows

      if (response === "There are no files on the server.") {
        tableWrapper.style.display = "none";
        emptyMessage.style.display = "block";
        return;
      } else {
        tableWrapper.style.display = "block";
        emptyMessage.style.display = "none";
      }

      const lines = response.split("\n");
      lines.forEach(line => {
        const row = createFileTableRow(line);
        if (row) {
          tableBody.appendChild(row);
        }
      });
    }
  };

  xhr.send();
}

function createFileTableRow(line) {
  const parts = line.split(" - ");
  if (parts.length < 3) return null;

  const filename = parts[0].trim();
  const sizeBytesMatch = parts[1].match(/(\d+)\s+bytes/);
  const sizeBytes = sizeBytesMatch ? parseInt(sizeBytesMatch[1]) : 0;
  const sizeMB = (sizeBytes / (1024 * 1024)).toFixed(2);

  const uploadMatch = parts[2].match(/Uploaded by (.+) on (.+)/);
  const owner = uploadMatch ? uploadMatch[1].trim() : "Unknown";
  const timestamp = uploadMatch ? uploadMatch[2].trim() : "Unknown";

  const tr = document.createElement("tr");

  tr.appendChild(createCell(filename));
  tr.appendChild(createCell(owner));
  tr.appendChild(createCell(sizeMB));
  tr.appendChild(createCell(timestamp));

  const tdActions = document.createElement("td");
  tdActions.appendChild(createDownloadButton(filename));
  tdActions.appendChild(createDeleteButton(filename));
  tr.appendChild(tdActions);

  return tr;
}

function createCell(text) {
  const td = document.createElement("td");
  td.textContent = text;
  return td;
}

function createDownloadButton(filename) {
  const btn = document.createElement("button");
  btn.textContent = "Download";
  btn.onclick = function () {
    window.location.href = "/api/get?file=" + encodeURIComponent(filename);
  };
  return btn;
}

function createDeleteButton(filename) {
  const btn = document.createElement("button");
  btn.textContent = "Delete";
  btn.onclick = function () {
    if (confirm(`Are you sure you want to delete "${filename}"?`)) {
      const xhrDelete = new XMLHttpRequest();
      xhrDelete.open("DELETE", "/api/delete?file=" + encodeURIComponent(filename), true);
      xhrDelete.onload = function () {
        if (xhrDelete.status === 200) {
          alert(`Deleted "${filename}" successfully.`);
          list();
        } else {
          alert(`Failed to delete "${filename}".`);
        }
      };
      xhrDelete.send();
    }
  };
  return btn;
}

function set_logged_in(logged_in, username="") {
    /*
    set_logged_in updates the HTML divs according to if the user is logged in or not
    */
    document.getElementById("logged_in").style.display = logged_in ? "block" : "none";
    document.getElementById("logged_out").style.display = logged_in ? "none" : "block";

    if (logged_in) {
        document.getElementById("welcome_message").textContent = `Welcome ${username}`;
    }
}
