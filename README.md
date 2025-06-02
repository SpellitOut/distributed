# TreeDrive File Transfer System
### Ian Spellman - 7891649

TreeDrive is a stateful file-sharing server and thin client. TreeDrive allows clients to authenticate, upload, download, list, and delete files in a shared server environment. TreeDrive maintains file and user metadata to ensure proper ownership and access.

## Table of Contents

- [Features](#features)

- [Getting Started](#getting-started)

    - [Server Setup](#server-setup)

    - [Client Setup](#client-setup)

- [How to Interact](#how-to-interact)

    - [Logging In](#logging-in)

    - [Available Commands](#available-commands)

- [Reliable Aviary Birds](#reliable-aviary-birds)

## Features

- Authentication: Clients must log in with a username to access server commands and functionalities.

- File hosting: View a list of files on the server, including their owner, size, and when they were uploaded.

- Upload files: Upload files from the client to the server. Owners can overwrite their own files.

- Download files: Download files from the server to the client.

- Delete files: Owners of files may delete them from the server.

- Concurrent access: Server manages many clients concurrently across a single-thread.

## Getting Started

Follow these instructions to get the TreeDrive server and client up and running.
Prerequisites

    Python 3.x: Ensure you have Python 3 installed on your system.

### Server Setup

It is recommended to run the server in an empty directory at first to allow it to create it's necessary files and directories. 

Run the Server: Open a terminal or command prompt, navigate to the directory where you saved `server.py`, and run:

    python3 server.py
You should see a message indicating that the server is listening on 0.0.0.0:8270.

### Client Setup

To run the client and connect to your server, you will first need to setup the host in the `client.py` file.

Right at the top of `client.py` you will see these lines of code:

    #-------------------------------
    #Load the configured Host and Port for server socket to bind to
    HOST = '130.179.x.x'    # The remote host
    PORT = 8270              # The same port as used by the server
    #-------------------------------

You will need to change the `HOST` to match the ip of your server's host machine. On unix based machines, you can find the IPv4 address using `ip a` in your terminal.

**Note:** if you are using one of the aviary birds to host, please refer to [the list of reliable birds](#reliable-aviary-birds)

After setting the `HOST` in `client.py` run the client in terminal or command prompt (separate from the server) with:       

    python3 client.py

Upon successful setup you should see a "Welcome to TreeDrive" message from the server.

## How to Interact

Once both the server and client are running, you can interact with the system through the client's command line.
### Logging In

Before you can access the functionalities of the server, you must log in using:

`LOGIN <username>`

### Available Commands

After logging in, you can use the following commands:

`LIST` : Displays all files currently stored on the server.

`PUSH <filename>` : Upload a file to the server. Associated the signed in user with the file.

**Note:** logged-in users can only overwrite files that they own.

`GET <filename>` : Download a file from the server to your client.

`DELETE <filename>` : Delete a file from the server. 

**Note:** logged-in users can only delete files that they own.

## Reliable Aviary Birds

This is a list of the reliable aviary birds at UManitoba. Please refer to this list for their IP addresses.

    130.179.28.110  rookery.cs.umanitoba.ca
    130.179.28.111  cormorant.cs.umanitoba.ca
    130.179.28.112  crow.cs.umanitoba.ca
    130.179.28.113  eagle.cs.umanitoba.ca
    130.179.28.114  falcon.cs.umanitoba.ca
    130.179.28.115  finch.cs.umanitoba.ca
    130.179.28.116  goose.cs.umanitoba.ca
    130.179.28.117  grebe.cs.umanitoba.ca
    130.179.28.118  grouse.cs.umanitoba.ca
    130.179.28.119  hawk.cs.umanitoba.ca
    130.179.28.120  heron.cs.umanitoba.ca
    130.179.28.121  killdeer.cs.umanitoba.ca
    130.179.28.122  kingfisher.cs.umanitoba.ca
    130.179.28.123  loon.cs.umanitoba.ca
    130.179.28.124  nuthatch.cs.umanitoba.ca
    130.179.28.125  oriole.cs.umanitoba.ca
    130.179.28.126  osprey.cs.umanitoba.ca
    130.179.28.127  owl.cs.umanitoba.ca
    130.179.28.128  pelican.cs.umanitoba.ca