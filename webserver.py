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
    print(f"Sending command: {command}\n")

    response = b''

    # Await response
    while True:
        chunk = fileserver_socket.recv(1024)
        if not chunk:
            break
        response += chunk
        if chunk.endswith(b"\n"):
            break

    print(f"Response: {response}")
    return response.decode()

def talk_to_file_server(username: str, command: str):
    '''Establish a connection between the webserver and file server. Webserver sends a sequence of commands to the fileserver and receives a response'''
    try:
        fileserver_socket = sock.create_connection((FILESERVER_HOST, FILESERVER_PORT))
        response = send_command(command, username, fileserver_socket) # Send command to fileserver and save the response
        return response
    except Exception as e:
        print(f"[ERROR] File server connection failed: {e}")
        return None
    
def build_http_response(status_code=200, status_text="OK", body="", content_type="text/plain", headers=None):

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
        response += f"{key} {val}\r\n"

    response += "\r\n"

    print("Response", response)

    return response.encode + bytes

def handle_client(conn, addr):
    try:
        request = conn.recv(1024).decode()
        if not request:
            return
        
        print(f"[INFO] Request from {addr}:\n{request.splitlines()[0]}")
        lines = request.splitlines()
        if not lines:
            return
        
        # Parse HTTP request line
        method, path, _ = lines[0].split()

        if path == "/api/list" and method == "GET":
            username = "ian"
            fs_response = talk_to_file_server(username, "LIST")
            if fs_response is not None:
                body = fs_response.strip()
                response = build_http_response(200, "OK", body, "application/json")
                # response = (
                #     "HTTP/1.1 200 OK\r\n"
                #     "Content-Type: application/json\r\n"
                #     "Access-Control-Allow-Origin: *\r\n"
                #     f"Content-Length: {len(body)}\r\n"
                #     "\r\n"
                #     f"{body}"
                #)
            else:
                response = (
                    "HTTP/1.1 502 Bad Gateway\r\n"
                    "Content-Type: text/plain\r\n"
                    "Content-Length: 20\r\n"
                    "\r\n"
                    "File server error"
                )
        else:
            response = (
                "HTTP/1.1 404 Not Found\r\n"
                "Content-Type: text/plain\r\n"
                "Content-Length: 13\r\n"
                "\r\n"
                "Not Found"
            )

        conn.sendall(response.encode())   

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
