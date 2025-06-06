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
  /*
  Request the file list from the server,
  creates a table of files to display on the webpage
  */
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
  /*
  Creates a formatted row for the file-table on the webpage. Takes in a line and formats it to the expected format
  */
  const parts = line.split(" - ");
  if (parts.length < 3) return null;

  const filename = decodeURIComponent(parts[0].trim());
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
  /*
  Helper function to create a single cell in the file-table
  */ 
  const td = document.createElement("td");
  td.textContent = text;
  return td;
}

function createDownloadButton(filename) {
  /*
  Create a download button in the table
  */
  const btn = document.createElement("button");
  btn.textContent = "Download";
  btn.onclick = function () {
    download_file(filename);
  };
  return btn;
}

function createDeleteButton(filename) {
  /*
  Create a delete button in the table
  */
  const btn = document.createElement("button");
  btn.textContent = "Delete";
  btn.onclick = function () {
    delete_file(filename);
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
        document.getElementById("welcome_message").textContent = `Welcome ${username}, to TreeDrive File Sharing`;
    }
}

let selectedFile = null;

function handleFileSelected() {
  /*
  Handles selecting a file for upload
  */
  const fileInput = document.getElementById("fileInput");
  if (fileInput.files.length > 0) {
    selectedFile = fileInput.files[0];
    document.getElementById("selectedFilename").textContent = selectedFile.name;
  } else {
    selectedFile = null;
    document.getElementById("selectedFilename").textContent = "No file chosen";
  }
}

function uploadFile() {
  /*
  Uploads a selected file to the server
  */
  if (!selectedFile) {
    alert("Please select a file first.");
    return;
  }

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/push?file=" + encodeURIComponent(selectedFile.name), true);

  xhr.onload = function () {
    if (xhr.status === 200) {
      alert("File uploaded successfully.");
      list(); // Optionally refresh file list
    } else if (xhr.status === 401) {
        alert("Permission denied. You can not overwrite a file you do not own.")
    } else {
        alert("Upload failed.");
    }
  };

  xhr.send(selectedFile);
}

function delete_file(filenameFromButton = null) {
  /*
  Delete a file based on the name filled out in the delete_field on webpage
  */
  const filename = filenameFromButton || document.getElementById("delete_field").value.trim();
  if (!filename) {
    alert("Please enter a filename to delete.");
    return;
  }

  if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

  const xhr = new XMLHttpRequest();
  xhr.open("DELETE", "/api/delete?file=" + encodeURIComponent(filename), true);
  xhr.onload = function () {
    if (xhr.status === 200) {
      alert(`Deleted "${filename}" successfully.`);
      list();
      if (!filenameFromButton) {
        document.getElementById("delete_field").value = "";
      }
    } else if (xhr.status === 404) {
      alert(`File "${filename}" not found.`);
    } else if (xhr.status === 401) {
      alert("Permission denied. You can not delete a file you do not own.");
    } else {
      alert(`Failed to delete "${filename}". Server responded with status ${xhr.status}.`);
    }
  };
  xhr.send();
}

function download_file(filenameFromButton = null) {
  /*
  Download a selected file. Can be passed as parameter, or if the download field is filled
  */
  const filename = filenameFromButton || document.getElementById("download_field").value.trim();
  if (!filename) {
    alert("Please enter a filename to download.");
    return;
  }

  if (!confirm(`Download "${filename}"?`)) return;

  window.location.href = "/api/get?file=" + encodeURIComponent(filename);
}
