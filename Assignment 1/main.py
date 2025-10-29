from socket import *
import sys
import os

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
# Fill in start.
tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
tcpSerSock.bind(('', 8888))
tcpSerSock.listen(5)
# Fill in end.

while 1:
    # Start receiving data from the client
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('Received a connection from:', addr)
    message = None
    # Fill in start.
    message = tcpCliSock.recv(4096).decode()
    # Fill in end.
    print(message)
    
    # Extract the filename from the given message
    print(message.split()[1])
    filename = message.split()[1].partition("/")[2]
    print(filename)
    fileExist = "false"
    
    # Create a valid cache filename by replacing / with _
    cache_filename = filename.replace("/", "_")
    if not cache_filename:
        cache_filename = "index.html"
    
    filetouse = "./" + cache_filename
    print(filetouse)
    
    try:
        # Check whether the file exist in the cache
        f = open(filetouse, "rb")
        outputdata = f.read()
        f.close()
        fileExist = "true"
        
        # ProxyServer finds a cache hit and generates a response message
        # Fill in start.
        tcpCliSock.send(outputdata)
        # Fill in end.
        print('Read from cache')
    
    # Error handling for file not found in cache
    except IOError:
        if fileExist == "false":
            # Create a socket on the proxyserver
            print('File not found in cache. Fetching from server...')
            c = None
            # Fill in start.
            c = socket(AF_INET, SOCK_STREAM)
            # Fill in end.
            hostn = filename.replace("www.", "", 1).split('/')[0]
            print(hostn)
            
            # Parse hostname and port
            if ':' in hostn:
                host_parts = hostn.split(':')
                hostn = host_parts[0]
                port = int(host_parts[1])
            else:
                port = 80
            
            print(f"Connecting to {hostn}:{port}")
            
            try:
                # Connect to the socket to port 80
                # Fill in start.
                c.connect((hostn, port))
                # Fill in end.
                
                # Create a temporary file on this socket and ask port 80 for the file requested by the client
                # Extract the path from filename
                path_parts = filename.split('/', 1)
                if len(path_parts) > 1:
                    request_path = "/" + path_parts[1]
                else:
                    request_path = "/"
                
                request = "GET " + request_path + " HTTP/1.1\r\n"
                request += "Host: " + hostn + "\r\n"
                request += "User-Agent: Mozilla/5.0\r\n"
                request += "Accept: */*\r\n"
                request += "Connection: close\r\n\r\n"
                c.send(request.encode())
                
                # Read the response into buffer
                # Fill in start.
                buffer = b""
                while True:
                    data = c.recv(4096)
                    if len(data) == 0:
                        break
                    buffer += data
                # Fill in end.
                
                # Create a new file in the cache for the requested file.
                # Also send the response in the buffer to client socket and the corresponding file in the cache
                tmpFile = open(filetouse, "wb")
                # Fill in start.
                tmpFile.write(buffer)
                tcpCliSock.send(buffer)
                tmpFile.close()
                # Fill in end.
                c.close()
                print('Fetched from server and cached')
            except Exception as e:
                print(f"Illegal request: {e}")
                tcpCliSock.send("HTTP/1.0 502 Bad Gateway\r\n\r\n".encode())
        else:
            # HTTP response message for file not found
            # Fill in start.
            tcpCliSock.send("HTTP/1.0 404 Not Found\r\n".encode())
            tcpCliSock.send("Content-Type:text/html\r\n".encode())
            tcpCliSock.send("\r\n".encode())
            # Fill in end.
    
    # Close the client and the server sockets
    tcpCliSock.close()
    # Fill in start.
    # Note: We don't close tcpSerSock here as it needs to keep listening
    # If you want to close it, it should be outside the while loop
    # Fill in end.