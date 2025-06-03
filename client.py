"""
Name:           Ian Spellman
Student number: 7891649
Course:         A01 - COMP3010
Instructor:     Dr. Saulo dos Santos

Assignment 2

client.py
    From Assignment 1:
    
    A client to connect to server.py and run commands through. Provides the user with a simple command line interface.

    Can change the HOST to be match the host ip address of the server's machine
"""

import socket
import os

#-------------------------------
#Load the configured Host and Port for server socket to bind to
HOST = 'localhost'    # The remote host
PORT = 8270              # The same port as used by the server
#-------------------------------
#
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

loggedIn = False

def isValidCommand(commandmsg: str) -> tuple[bool, str, str, list]:
    """
    Parses a string to check that the signature is valid for the command.
    Uses the CommandConfig.py file to validate for command signature.

    Args:
        commandmsg (str): The command string to parse for validity.

    Returns:
        :tuple[bool, str, str, list]: A tuple containing:
            - isValid (bool): Whether the command is valid.
            - errorMsg (str): If the command is invalid, an error message is returned. If the command is valid an empty string is returned.
            - command (str): If the command is valid, the command itself is returned.
            - args (list): If the command is valid, the arguments are returned.
    """
    tokens = commandmsg.strip().split()

    if not tokens:
        #If there are no tokens, invalid
        return False, "No command given", None, None
    
    command = tokens[0].upper()

    if command not in COMMANDS:
        #Command does not exist
        return False, f"Unknown command: {command}", None, None
    
    expectedArguments = len(COMMANDS[command]["signature"].split())

    if len(tokens) != expectedArguments:
        #If the number of tokens does not equal the expected tokens for the command
        signature = COMMANDS[command]["signature"]
        return False, f"{command} expects {expectedArguments-1} argument(s): {signature}", None, None

    #The command is valid so ship it
    return True, "", command, tokens[1:]

def push(clientSocket, filename):
    """Client attempts to push a file filename over clientSocket. 
    Client sends command and awaits an okay from the server. 
    Then client sends the file size, then sends the file as raw bytes."""
    try:
        # Send the initial command
        clientSocket.sendall(f"PUSH {filename}\n".encode("utf-8"))

        #Wait for okay from server
        response = clientSocket.recv(1024).decode("utf-8")
        if not response.strip() == "READY":
            print(f"Error: {response}'\n")
            return
        print(f"Uploading file: {filename}\n")

        #Send filesize to server
        filesize = os.path.getsize(filename)
        clientSocket.sendall(f"{filesize}\n".encode("utf-8"))

        #Wait for okay from server
        response = clientSocket.recv(1024).decode("utf-8")
        if not response.strip() == "OK":
            print(f"Error: {response}'\n")
            return
        
        # Send file as raw bytes
        with open(filename, "rb") as f:
            while packet := f.read(1024):
                clientSocket.sendall(packet)

        response = clientSocket.recv(1024).decode("utf-8")
        print(response.strip() + "\n")

    except Exception as e:
        print("Error during file push:", e)

def get(clientSocket, filename):
    """Client attempts to get a file filename over clientSocket. 
    Client sends command and awaits an okay from the server. 
    Then server sends the file size, then sends the file as raw bytes."""
    try:
        # Send the initial command
        clientSocket.sendall(f"GET {filename}\n".encode("utf-8"))

        #Wait for okay from server
        response = clientSocket.recv(1024).decode("utf-8")
        if not response.startswith("READY"):
            print(f"Error: {response}\n")
            return
        print(f"Downloading file: {filename}\n")

        tokens = response.split(" ")
        incomingFilename = tokens[1]
        filesize = int(tokens[2])

        # ping server OK
        clientSocket.sendall(f"OK\n".encode("utf-8"))

        # receive last response
        response = clientSocket.recv(1024).decode("utf-8")
        
        # ping server OK
        clientSocket.sendall(f"OK\n".encode("utf-8"))

        # Start saving
        with open(incomingFilename, "wb") as f:
            received = 0
            f.seek(received)
            while received < filesize:
                packet = clientSocket.recv(min(1024, filesize - received)) #since client is blocking, we need to take the min INCASE transmission ends
                if not packet:
                    break
                f.write(packet)
                received += len(packet)
                clientSocket.sendall("CONTINUE\n".encode("utf-8"))

        # ping server so it knows we are DONE
        clientSocket.sendall("DONE\n".encode("utf-8"))

        print(f"File {incomingFilename} downloaded.\n")

    except Exception as e:
        print("Error during file get:", e)

"""

Setup the client socket and loop running commands

"""
try:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((HOST, PORT))

    data = clientSocket.recv(1024) #receive first message from server
    print(data.decode('utf-8'))

    while True:
        clientInput = input("Enter Command: ")
        valid, message, command, args = isValidCommand(clientInput)

        if valid:   # User sends a valid command

            if command == "PUSH" and loggedIn:
                # Need to check if the file exists
                filename = args[0]
                if os.path.exists(filename):
                    push(clientSocket, filename)
                else:
                    print(f"Error: File '{filename}' does not exist in the current directory.\n")
            elif command == "GET" and loggedIn:
                filename = args[0]
                get(clientSocket, filename)
            else:
                # Send command
                payload = clientInput + "\n"
                clientSocket.sendall(payload.encode("utf-8")) # we only send a command to the server when it is deemed valid client-side
                # Receive server response
                data = clientSocket.recv(1024)

                if command == "LOGIN":  # Client doesn't care if the user attempts to login more than once
                                        # Server will tell us if they are trying to login more than once
                    loggedIn = True     #Mark logged in on client
                print(data.decode("utf-8"))

        else:   # User sends an invalid command
            if loggedIn:
                print(f"Error: {message}") #only give them help if they are logged in
            else:
                # we need to print this here because the client never sends an invalid command to server,
                # since we don't get a response from server we print this so the client is aware of the issue
                print(f"Error: You must login first with: {COMMANDS['LOGIN']['signature']}\n")
except socket.timeout as e:
    print('client timeout')
except OSError as e:
    print(f"Error: {e}")
except Exception as e:
    print("Unexpected Error. Time to get out the hammer!")
    print(f"Error: {e}")
finally:
    clientSocket.close()
#-------------------------------