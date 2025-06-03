import socket as sock
import sys
import threading

#-------------------------------
# Load the configured Host and Port for webserver socket to bind to
HOST = '0.0.0.0'
PORT = 8271

# Load the configured Host and Port for server socket for webserver to connect to
FILESERVER_HOST = '127.0.0.1'
FILESERVER_PORT = 8270
#-------------------------------

def build_http_response(status_code=200, status_text="OK", body="", content_type="text/plain", headers=None):
    """
    Constructs a complete HTTP response message.

    Parameters:
        status_code (int): HTTP status code (e.g., 200, 404).
        status_text (str): Text description of the status (e.g., "OK", "Not Found").
        body (str or bytes): The response body. If a string, it is encoded to bytes.
        content_type (str): The MIME type of the response body (default is "text/plain").
        headers (list of tuples): Optional additional headers as (key, value) pairs.

    Returns:
        bytes: A full HTTP response ready to be sent over a socket.
    """
    if isinstance(body, str):
        bytes = body.encode()
    else:
        bytes = body # handles raw binary if body is not a string
    length = len(bytes)

    # Default Headers #
    default_headers = [
        ("Content-Length", length),
        ("Content-Type", content_type),
    ]

    # Extra headers (passed by parameter) #
    if headers:
        for header in headers:
            default_headers.append(header)

    response = f"HTTP/1.1 {status_code} {status_text}\r\n"
    for key, val in default_headers:
        response += f"{key}: {val}\r\n"
    response += "\r\n"
    return response.encode() + bytes

class HTTPResponses:
    UNAUTHORIZED = build_http_response(401, "Unauthorized", "Unauthorized", "text/plain")
    NOT_FOUND = build_http_response(404, "Not Found", "Not Found", "text/plain")
    INTERNAL_SERVER_ERROR = build_http_response(500, "Internal Server Error", "Internal Server Error", "text/plain")
    NOT_IMPLEMENTED = build_http_response(501, "Not Implemented", "Not Implemented", "text/plain")
    BAD_GATEWAY = build_http_response(502, "Bad Gateway", "File server error", "text/plain")

def login_fileserver(username, fileserver_socket):
    '''Attempts to login a user to the fileserver'''
    _ = fileserver_socket.recv(1024) # Get arbitrary welcome message from server, can cast it away after
    fileserver_socket.sendall(f"LOGIN {username}\n".encode())
    response = fileserver_socket.recv(1024) # Get login message from server
    return response

def send_command(command, username, fileserver_socket):
    '''Send a command to the fileserver as a user'''
    login_fileserver(username, fileserver_socket) # Login as user
    fileserver_socket.sendall((command + "\n").encode()) # File server expects new-line terminated commands
    response = b''
    # Await response
    while True:
        chunk = fileserver_socket.recv(1024)
        if not chunk:
            break
        response += chunk
        if chunk.endswith(b"\n"):
            break
    return response.decode()

def talk_to_file_server(username: str, command: str):
    '''Establish a connection between the webserver and file server. Webserver sends a command to the fileserver as a user and receives a response'''
    try:
        with sock.create_connection((FILESERVER_HOST, FILESERVER_PORT)) as fileserver_socket:
            response = send_command(command, username, fileserver_socket)
            return response
    except Exception as e:
        print(f"[ERROR] File server connection failed: {e}")
        return None


def handle_get_list(username):
    """Handles calling get list from the file server. Returns the formatted http response"""
    fs_response = talk_to_file_server(username, "LIST")
    if fs_response is not None:
        body = fs_response
        response = build_http_response(200, "OK", body, "application/octet-stream")
    else:
        response = HTTPResponses.BAD_GATEWAY
    return response

def handle_download_file(username, filename):
    """Handles downloading a file from the server. Returns the formatted http response"""
    return HTTPResponses.NOT_IMPLEMENTED

def handle_delete(username, filename):
    """Handles calling delete <filename> from the file server. Returns the formatted http response"""
    fs_response = talk_to_file_server(username, f"DELETE {filename}")
    if fs_response is not None:
        response = build_http_response(200, "OK", fs_response, "application/octet-stream")
    else:
        response = HTTPResponses.BAD_GATEWAY
    return response

def handle_download(username, filename):
    """Handles calling the get <filename> from the file server. Returns the formatted http response"""
    try:
        with sock.create_connection((FILESERVER_HOST, FILESERVER_PORT)) as fileserver_socket:
            login_fileserver(username, fileserver_socket) # Login as user

            fileserver_socket.sendall(f"GET {filename}\n".encode()) # Send initial Command

            server_resp = fileserver_socket.recv(1024).decode() # Expect READY back from server
            if not server_resp.startswith("READY"):
                return HTTPResponses.NOT_FOUND
            tokens = server_resp.split() # Check for correct number of tokens
            if len(tokens) != 3:
                return HTTPResponses.INTERNAL_SERVER_ERROR

            incoming_filename = tokens[1]
            filesize = int(tokens[2])

            fileserver_socket.sendall("OK\n".encode()) # ping server OK
            server_resp = fileserver_socket.recv(1024).decode() # last shake from server
            fileserver_socket.sendall("OK\n".encode()) # ping server OK

            # Receive in the file
            file_data = bytearray()
            received = 0
            while received < filesize:
                packet = fileserver_socket.recv(min(1024, filesize - received))
                if not packet:
                    break
                file_data.extend(packet)
                received += len(packet)
                fileserver_socket.sendall("CONTINUE\n".encode()) # ping server to continue download

            fileserver_socket.sendall("DONE\n".encode("utf-8")) # ping server so it knows we are DONE
           
            # Add new headers to our response
            headers = [
                 # this header isn't necessary for the implementation, but I liked having access 
                 #  to the filename while testing with Insomnia
                ("Content-Disposition", f'attachment; filename="{incoming_filename}"'),
            ]
            
            response = build_http_response(200, "OK", body=file_data, headers=headers)
            return response
    
    except Exception as e:
        #print(f"[ERROR] File server connection failed: {e}")
        return HTTPResponses.INTERNAL_SERVER_ERROR

def handle_upload(username, filename):
    pass

def parse_pathquery(path_in):
    """
    Parses a path and returns the path and query if there is one
    
    Parameters:
        path_in (str):
    Returns:
        path (str):
        query (dict):
    """
    if '?' not in path_in:  # if there is no query return the path back with an empty dictionary
        return path_in, {}
    
    path, query_token = path_in.split('?', maxsplit=1)
    query = {}

    # tokenize the query and store it in a dictionary
    for part in query_token.split('&'):
        if '=' in part:
            key, val = part.split('=', maxsplit=1)
            query[key] = val
        else:
            query[part] = ""

    return path, query

def parse_http_request(lines):
    # Parse HTTP request line
    method, path_in, _ = lines[0].split()

    # Parse remaining headers
    headers = {}
    for line in lines[1:]:
        if line == "":
            break # end of headers
        if ": " in line:
            key, val = line.split(": ", maxsplit=1)
            headers[key] = val.strip()
    return method, path_in, headers

def parse_cookies(headers):
    cookie_header = headers.get("Cookie")
    cookies = {}

    if cookie_header:
        cookie_pairs = cookie_header.split(";")
        for pair in cookie_pairs:
            if "=" in pair:
                key, val = pair.split("=", maxsplit=1)
                cookies[key] = val
    return cookies


def handle_client(conn, addr):
    try:
        request = conn.recv(1024).decode()
        if not request:
            return
        
        print(f"[INFO] Request from {addr}:\n{request.splitlines()[0]}")
        lines = request.splitlines()
        if not lines:
            return
        
        method, path_in, headers = parse_http_request(lines)
        path, query = parse_pathquery(path_in) # Split path and query
        cookies = parse_cookies(headers)

        # Get username (if logged in)
        username = cookies.get("username")

        #USERNAME = "ian" ### SHOULD NOT BE HARDCODED

        if path == "/api/login":
            if method == "POST":
                ####
                ####
                response = HTTPResponses.NOT_IMPLEMENTED
                ####
                ####
            elif method == "DELETE":
                ####
                ####
                response = HTTPResponses.NOT_IMPLEMENTED
                ####
                ####
            else:
                response = HTTPResponses.NOT_FOUND
        elif path == "/api/list" and method == "GET":
            if username:
                response = handle_get_list(username)
            else:
                response = HTTPResponses.UNAUTHORIZED
        elif path == "/api/get" and method == "GET":
            if username:
                filename = query.get("file")
                response = handle_download(username, filename)
                ####
                ####
                #response = HTTPResponses.NOT_IMPLEMENTED
                ####
                ####
            else:
                response = HTTPResponses.UNAUTHORIZED
        elif path == "/api/push" and method == "POST":
            if username:
                # upload a new file on the server
                response = HTTPResponses.NOT_IMPLEMENTED
            else:
                response = HTTPResponses.UNAUTHORIZED
        elif path == "/api/delete" and method == "DELETE":
            if username:
                filename = query.get("file")
                response = handle_delete(username, filename)
            else:
                response = HTTPResponses.UNAUTHORIZED
        else:
            response = HTTPResponses.NOT_FOUND

        conn.sendall(response)   

    except Exception as e:
        print(f"Error: handle_client error: {e}")
        #respond(conn, 500, "Internal Server Error")
    finally:
        conn.close()

def startup_server():
    """Start up the server and continue to accept connection. Each new connection is assigned a new thread."""
    try:
        server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        server_socket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Webserver listening on port {PORT}\n")
    except Exception as e:
        print(f"Webserver failed to start on {HOST}:{PORT}\nError: {e}")
        sys.exit(1)

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True) #enable multi-threading
        thread.start()

#-------------------------------
"""
Main Program Loop
"""
if __name__ == "__main__":
    startup_server()

#-------------------------------
