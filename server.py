"""
Name:           Ian Spellman
Student number: 7891649
Course:         A01 - COMP3010
Instructor:     Dr. Saulo dos Santos

Assignment 2

server.py
    From Assignment 1:

    a stateful file-sharing server. Allows clients to connect and authenticate, 
    upload, download, list, and delete files in a shared server environment.

    server.py maintains file and user metadata to ensure proper ownership and access.

    Requires a file_metadata.json with metadata for files on the server.
    Requires a directory ./ServerFiles/ to store server files. 

    If neither of these exists, the server will attempt to create them automatically.

    If metadata is lost for files, those files are as good as invisible to the 
    server as metadata is expected to operate on files.

    It is recommended to launch the server in an empty directory to allow it to set itself up. 

    Can change the HOST to be match the host ip address of the server's machine
"""

import socket as sock
import sys
import select
import json
import os
from datetime import datetime     #Used for timestamps

"""Constants"""
SERVER_SELECT_TIMEOUT = 5
SERVER_FILE_PATH = "ServerFiles"
METADATA_FILE = "file_metadata.json"
TIMESTAMP_FORMAT = "%a %b %d %H:%M:%S %Y"
"""---------"""

# Load the configured Host and Port for server socket to bind to
HOST = '0.0.0.0'
PORT = 8270
#-------------------------------

"""Enum for keeping track of ClientState"""
class ClientState:
    LOGGED_OUT = "LOGGED_OUT"
    WAITING = "WAITING_FOR_COMMAND"
    RECEIVING_FILE_SIZE = "RECEIVING_FILE_SIZE"
    RECEIVING_FILE = "RECEIVING_FILE"
    SENDING_FILE_SIZE = "SENDING_FILE_SIZE"
    SENDING_FILE = "SENDING_FILE"
"""---------"""

# The expected schema of the commands for the server. "
# Includes the number of arguments (command name included) as well as the command signature."
COMMANDS = {

    "LOGIN": {

        "args": 2,

        "signature": "LOGIN <username>"

    },

    "PUSH": {

        "args": 2,

        "signature": "PUSH <filename>"

    },

    "LIST": {

        "args": 1,

        "signature": "LIST"

    },

    "GET": {

        "args": 2,

        "signature": "GET <filename>"

    },

    "DELETE": {
        "args": 2,
        "signature": "DELETE <filename>"
    }
}

#-----------------------------
#
# Functions for Managing the file Metadata
#
def loadMetadata():
    """
    Attemps to load metadata from METADATA_FILE into a dictionary and return the metadata as a dictionary
    """
    metadata = {}
    try:
        with open(METADATA_FILE, "r") as f:
            content = f.read().strip()
            if content:  # Not empty
                metadata = json.loads(content)
    except FileNotFoundError:
        print(f"Metadata file does not exist. Creating file '{METADATA_FILE}'")
        f = open(METADATA_FILE, "x")
    return metadata

def saveMetadata(metadata):
    """
    Saves metadata to METADATA_FILE
    """
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=6)

def addMetadata(filename, owner):
    """
    Adds relevant metadata (owner, timestamp, filesize) to filename and then saves the metadata 
    """
    try:
        metadata = loadMetadata()
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        metadata[filename] = {
            "owner": owner,
            "filesize": os.path.getsize(f"{SERVER_FILE_PATH}/{filename}"),
            "timestamp": timestamp
        }
        saveMetadata(metadata)
    except FileNotFoundError as e:
        print(f"Error: {e}")

def deleteMetadata(filename):
    """
    Removes metadata for filename from METADATA_FILE
    """
    try:
        metadata = loadMetadata()
        if filename in metadata:
            metadata.pop(filename)
            saveMetadata(metadata)
    except FileNotFoundError as e:
        print(f"Error: {e}")
# end of Functions for Managing the file Metadata
#-----------------------------

#-----------------------------
#
# Functions for each valid server command
#
def com_LIST():
    """Returns the files in the SERVER_FILE_PATH that have existing metadata as a formatted string"""
    files = os.listdir(SERVER_FILE_PATH)
    message = ""
    meta = loadMetadata()
    if not files:
        message = "There are no files on the server.\n"
    else:
        for file in files:
            if file in meta:
                message += f"{file} - {meta[file]['filesize']} bytes - Uploaded by {meta[file]['owner']} on {meta[file]['timestamp']}\n"
            else:
                print(f"Error: Missing metadata for file '{file}'.\n")
    return message


def com_DELETE(username, args):
    """
    Delete a file from the server if the username owns that file
    """
    filename = args[0]
    meta = loadMetadata()
    try:
        if username == meta[filename]["owner"]:
            os.remove(f"{SERVER_FILE_PATH}/{filename}")
            message = f"File '{filename}' deleted."
            deleteMetadata(filename)
        else:
            message = f"Permission denied. You are not the owner of this file."
    except Exception:
        message = f"Error: File '{filename}' not found."
    return message
# end of Functions for each valid server command
#-----------------------------

def setupSocket():
    """Set up and return a listening server socket."""
    try:
        serverSocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        serverSocket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
        serverSocket.bind((HOST, PORT))
        serverSocket.listen()
        serverSocket.setblocking(False)
        print(f"Server listening on {HOST}:{PORT}\n")
        return serverSocket
    except Exception as e:
        print(f"Server failed to start on {HOST}:{PORT}\nError: {e}")
        sys.exit(1)

def newConnection(serverSocket, myClients, clientStates, clientBuffers):
    """
    Accept a new incoming connection to the server socket. Sets client state and buffers to defaults.
    Sends a welcome message to client
    """
    conn, addr = serverSocket.accept()
    print(f"Connection from {addr}\n")
    myClients.append(conn)
    clientStates[conn] = {"state": ClientState.LOGGED_OUT}   # Set client to default state
    clientBuffers[conn] = b""   # Set client's buffer to empty
    conn.sendall(f"Welcome to TreeDrive - Please login with: {COMMANDS['LOGIN']['signature']}\n".encode("utf-8"))

def clientDisconnect(clientSocket, myClients, clientStates, clientBuffers, loggedInClients):
    """
    Handle a disconnect of a client from the socket. Removes their states and buffers and logged them out if logged in.
    """
    try:    #need to check try in case the client disconnected immediately
        addr = clientSocket.getpeername()
    except:
        addr = "unknown"

    if clientSocket in loggedInClients:
        username = loggedInClients.pop(clientSocket) # If client was logged in, remove from logged in clients
        print(f"Removing client {username} {addr}\n")
    else:
        print(f"Removing client {addr}\n")

    # Clean Up
    clientSocket.close()
    myClients.remove(clientSocket)
    clientStates.pop(clientSocket)
    clientBuffers.pop(clientSocket)

def handleClient(clientSocket, myClients, clientStates, clientBuffers, loggedInClients):
    """
    handleClient()

    Manages a client socket by receiving data from it and updating the clients buffer.
    handleClient(...) manages the state of clients based on their inputs sent to the server.
    handleClient(...) handles the processing of client command and pushes the socket to the correct state to handle concurrent requests.

    """
    try:
        data = clientSocket.recv(1024)
        if not data:
            clientDisconnect(clientSocket, myClients, clientStates, clientBuffers, loggedInClients)
            return

        clientBuffers[clientSocket] += data     #update buffers

        client = clientStates[clientSocket]
        buffer = clientBuffers[clientSocket]
        # Get client current state
        state = client["state"]

        # Server says Client is LOGGED_OUT
        if state == ClientState.LOGGED_OUT:
            if b"\n" not in buffer: #wait for a full line
                return
            # We have received a full line, so pull the command_line out
            line, remainder = buffer.split(b"\n", 1)
            clientBuffers[clientSocket] = remainder #store remainder in the buffer
            command_line = line.decode("utf-8").strip()
            tokens = command_line.split(" ", 1)
            # Try to log them in if they send a login command
            if len(tokens) == 2 and tokens[0].upper() == "LOGIN":
                username = tokens[1].strip()
                loggedInClients[clientSocket] = username    # Store username
                client["state"] = ClientState.WAITING
                clientSocket.sendall(f"Logged in as {username}.\nAvailable commands: PUSH <file>, GET <file>, LIST, DELETE <file>\n".encode("utf-8"))
                print(f"User {username} logged in from {clientSocket.getpeername()}\n")
                return
            else:
                clientSocket.sendall(f"Error: You must login first with: {COMMANDS['LOGIN']['signature']}\n".encode("utf-8"))
                return

        # Server WAITING_FOR_COMMANDS
        elif state == ClientState.WAITING:
            if b"\n" not in buffer: #wait for a full line
                return
            # We have received a full line, so pull the receivedCommand out
            line, remainder = buffer.split(b"\n", 1)
            clientBuffers[clientSocket] = remainder #store remainder in the buffer
            receivedCommand = line.decode("utf-8").strip()
            tokens = receivedCommand.split(" ", 1)
            username = loggedInClients[clientSocket]

            command = tokens[0].upper()
            args = tokens[1:] # args is a list in case we feel like adding more arguments to some commands later
            message = ""
            match command:
                case "LOGIN":
                    message = "You are already logged in.\n"
                case "LIST":
                    message = com_LIST()
                case "DELETE":
                    message = com_DELETE(username, args) + "\n"
                case "PUSH":
                    # Prepare the server to receive a file from client
                    filename = args[0]
                    metadata = loadMetadata()

                    if os.path.exists(f"{SERVER_FILE_PATH}/{filename}"):
                        fileOwner = metadata[filename]["owner"]
                        if username == fileOwner:
                            # Owner tries to overwrite their file, this is allowed
                            client["state"] = ClientState.RECEIVING_FILE_SIZE
                            client["filename"] = filename
                            client["filebytes"] = b""
                            client["filesize"] = None
                            message = "READY\n"
                            print(f"Receiving file {filename} from {username} on {clientSocket.getpeername()}\n")
                        else:
                            message = "Permission denied. You cannot overwrite a file you do not own.\n"
                    else:
                        # File does not exist so it can be received
                        client["state"] = ClientState.RECEIVING_FILE_SIZE
                        client["filename"] = filename
                        client["filebytes"] = b""
                        client["filesize"] = None
                        message = "READY\n"
                        print(f"Receiving file {filename} from {username} on {clientSocket.getpeername()}\n")
                case "GET":
                    # Prepare the server to send a file to client
                    filename = args[0]
                    if os.path.exists(f"{SERVER_FILE_PATH}/{filename}"): # check if file exists
                        filesize = os.path.getsize(f"{SERVER_FILE_PATH}/{filename}")
                        client["state"] = ClientState.SENDING_FILE_SIZE
                        client["filename"] = filename
                        client["filesize"] = filesize
                        client["sentbytes"] = 0
                        message = f"READY {filename} {filesize}\n"
                        print(f"Sending file {filename} to {username} on {clientSocket.getpeername()}\n")
                    else:
                        message = f"File '{filename}' does not exist."
                case _:
                    message = "Error: Command does not exist.\n"

            clientSocket.sendall(f"{message}".encode("utf-8"))

        # Client has said it will be sending a file, server now wants the file size
        elif client["state"] == ClientState.RECEIVING_FILE_SIZE:
            if b"\n" not in buffer: #wait for a full line
                return
            # We have received a full line, so pull the receivedCommand out
            line, remainder = buffer.split(b"\n", 1)
            clientBuffers[clientSocket] = remainder #store remainder in the buffer
            try:
                filesize = int(line.decode("utf-8").strip())
                client["filesize"] = filesize
                client["state"] = ClientState.RECEIVING_FILE
                client["filebytes"] = b""
                clientSocket.sendall(b"OK\n")
                print(f"File size: {filesize} bytes\n")
            except ValueError:
                clientSocket.sendall(b"Error: Invalid filesize.\n")
                client["state"] = ClientState.WAITING

        # Client has sent the filesize, server now waiting on the file
        elif client["state"] == ClientState.RECEIVING_FILE:
            expectedSize = client["filesize"]
            client["filebytes"] += buffer
            clientBuffers[clientSocket] = b"" #empty out the temp buffer
            if len(client["filebytes"]) < expectedSize:
                return  # have not received the full file yet

            filename = client["filename"]
            # Save the received file
            filePath = os.path.join(SERVER_FILE_PATH, filename)
            with open(filePath, "wb") as f:
                f.write(client["filebytes"])
            addMetadata(filename, owner=loggedInClients[clientSocket])

            clientSocket.sendall(f"File '{filename}' uploaded successfully.\n".encode("utf-8"))

            print(f"File saved: {filename}")

            # Clean up states
            client["state"] = ClientState.WAITING
            client["filename"] = None
            client["filesize"] = None
            client["filebytes"] = b""

        # Client has been sent the file size
        elif client["state"] == ClientState.SENDING_FILE_SIZE:
            if b"\n" not in buffer: #wait for a full line
                return
            # We have received a full line, so pull the receivedCommand out
            line, remainder = buffer.split(b"\n", 1)
            clientBuffers[clientSocket] = remainder #store remainder in the buffer
            if line.strip().decode("utf-8") == "OK":
                client["state"] = ClientState.SENDING_FILE
                clientSocket.sendall(b"SERVER OK\n")
            else:
                clientSocket.sendall("Error: Expected OK\n".encode("utf-8"))
                client["state"] = ClientState.WAITING

        # Client has requested a file download
        elif client["state"] == ClientState.SENDING_FILE:
            # Open the file for reading bytes
            filepath = os.path.join(SERVER_FILE_PATH, client["filename"])
            with open(filepath, "rb") as f:
                f.seek(client["sentbytes"])
                packet = f.read(1024)
                if packet:
                    clientSocket.sendall(packet)
                    client["sentbytes"] += len(packet)
                else:
                    # File sent
                    print(f"File sent: {client['filename']}")
                    # Clean up states
                    clientBuffers[clientSocket] = b""
                    client["state"] = ClientState.WAITING
                    client["filename"] = None
                    client["filesize"] = None
                    client["sentbytes"] = 0

    except (ConnectionResetError, BrokenPipeError):
        clientDisconnect(clientSocket, myClients, clientStates, clientBuffers, loggedInClients)
    except Exception as e:
        print("Error:", e)


def serverLoop(serverSocket):
    """
    Loop through the socket using a select statement to manage many sockets on a single-thread.
    Calls:
        newConnection(...) : when a new client connects.
        handleClient(...) : when an existing client is readable.
        clientDisconnect(...) : when a client is disconnected through an exception.
    """
    myClients = []                  # Clients will come-and-go
    loggedInClients = {}            # Maintain a dictionary of who is currently logged in
    clientStates = {}               # Maintains the state of connected clients
    clientBuffers =  {}             # Client Buffers to store received bytestrings
    myReadables = [serverSocket, ]  # server socket should stay in myReadables as we want to maintain it
    while True:
        try:
            readable, writeable, exceptions = select.select(
                myReadables + myClients,
                [],
                myReadables + myClients,
                SERVER_SELECT_TIMEOUT
            )
            for eachSocket in readable:
                if eachSocket is serverSocket:  # New client (since serverSocket is in myReadable)
                    newConnection(serverSocket, myClients, clientStates, clientBuffers)
                else:                           # Existing Connection
                    handleClient(eachSocket, myClients, clientStates, clientBuffers, loggedInClients)
            for eachSocket in exceptions:
                print(f"Error: sock is stinky")
                clientDisconnect(eachSocket, myClients, clientStates, clientBuffers, loggedInClients)
        except KeyboardInterrupt:
            print("Terminating server...")
            for client in myClients:
                client.close()
            serverSocket.close()
            sys.exit(0)
        except Exception as e:
            print("Unexpected Error. Time to get out the hammer!")
            print(f"Error: {e}")

def main():
    """
    Main Loop:
        Sets up the server socket.
        Listens repeatedley on that socket.
    """

    # If the server file directory is missing, creates it
    if not os.path.exists(SERVER_FILE_PATH):
        print(f"{SERVER_FILE_PATH} directory missing. Creating directory.")
        os.mkdir(SERVER_FILE_PATH)

    # Load metadata
    loadMetadata()

    # Setup the socket
    serverSocket = setupSocket()

    # Listen to that socket for a while
    serverLoop(serverSocket)

#------------------
main()
#------------------