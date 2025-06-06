# TreeDrive File Transfer System
### Ian Spellman - 7891649

TreeDrive is a stateful file-sharing server and thin client. TreeDrive allows clients to authenticate, upload, download, list, and delete files in a shared server environment. TreeDrive maintains file and user metadata to ensure proper ownership and access.

As of Assignment 2, TreeDrive now supports web-browser functionality, allowing users to connect through their browser and use all features of TreeDrive.

## Table of Contents

- [Features](#features)

- [Getting Started](#getting-started)

    - [Server Setup](#server-setup)

    - [Webserver Setup](#webserver-setup-and-web-client)

    - [Terminal Client Setup](#terminal-client-setup)

- [How to Interact](#how-to-interact)

    - [Using the Web-Client](#using-the-web-client)

        - [Functions](#functions)

    - [Using the Terminal Client](#using-the-terminal-client)

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

- **NEW (as of Assignment 2):** A Web-Client to access TreeDrive and use the above features.

## Getting Started

Follow these instructions to get the TreeDrive server and client up and running.
Prerequisites

    Python 3.x: Ensure you have Python 3 installed on your system.

### Server Setup

The server is required whether you run the Web-Client version of TreeDrive, or the Terminal Client

It is recommended to run the server in an empty directory at first to allow it to create it's necessary files and directories. 

Run the Server: Open a terminal or command prompt, navigate to the directory where you saved `server.py`, and run:

    python3 server.py
You should see a message indicating that the server is listening on 0.0.0.0:8270.

If you wish to run TreeDrive as a Web-Client, jump to the setup [here](#webserver-setup-and-web-client).

If you wish to run TreeDrive from a terminal-based client, jump to that setup, [here](#terminal-client-setup)

### Webserver Setup and Web-Client

*The following section refers to running a web-client used for Assignment 2*

If you choose to run TreeDrive as a Web-Client you will need to configure and run the Webserver.

Before you run the webserver, you must make sure you have the host and port setup correctly in the `webserver.py` file.

Right at the top of `webserver.py` you will see these lines of code:

    #-------------------------------
    # Load the configured Host and Port for webserver socket to bind to
    HOST = '0.0.0.0'
    PORT = 8271

    # Load the configured Host and Port for server socket for webserver to connect to
    FILESERVER_HOST = '127.0.0.1'
    FILESERVER_PORT = 8270
    #-------------------------------

You will need to change the `FILESERVER_HOST` and `FILESERVER_PORT` to match the ip of your server's host machine, as well as the port that the server is running on. On unix based machines, you can find the IPv4 address using `ip a` in your terminal.

**Note:** by default, the `FILESERVER_PORT` is  `8270`, which is the default also configured in `server.py`. If you change the port in `server.py` you must ensure `FILESERVER_PORT` matches.

**Note:** if you are using one of the aviary birds to host, please refer to [the list of reliable birds](#reliable-aviary-birds)

After setting the `FILESERVER_HOST` in `webserver.py` run the program in terminal or command prompt (separate from the server) with:       

    python3 webserver.py

Upon successful setup you should see a "Webserver started on port [assigned port]" message.

To use the webserver, jump to ["Using the Web-Client"](#using-the-web-client)

### Terminal Client Setup

*The following section refers to running a terminal-based client that was used for Assignment 1.*

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

To use the terminal-client, jump to ["Using the Terminal Client"](#using-the-terminal-client)

## How to Interact

## Using the Web-Client

To access the web-client, make sure `server.py` and `webserver.py` are both running. Once they are both running you can access the web-client through your browser.

In your address bar navigate to:

    http://bird.cs.umanitoba.ca:port

Replace `bird` with the aviary bird that `webserver.py` is running on.

Replace `port` with the port that `webserver.py` is running on.

If you have not logged in before you will be presented with a login screen.

Once you have logged in you will be able to access the functions of TreeDrive.

### Functions

TreeDrive's Web-client allows users to view an up-to-date list of the files stored on the server, as well as upload new files right from their browser.

Users can download and delete files from the browser as well.

The webpage saves a cookie to keep you logged in until you press `Logout`.

## Using the Terminal Client

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