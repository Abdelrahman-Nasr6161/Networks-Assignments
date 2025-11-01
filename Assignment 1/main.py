from socket import *
import sys
import os

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)

cache = {}
tcpSerSock = socket(AF_INET, SOCK_STREAM)
tcpSerSock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
tcpSerSock.bind(('', 8888))
tcpSerSock.listen(5)
print("Proxy Server is running on port 8888...\n")

while True:
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('Received a connection from:', addr)
    print(f'current cache {cache}')
    
    # Receive initial request
    message = tcpCliSock.recv(4096).decode()
    if not message:
        tcpCliSock.close()
        continue
    
    print(message)
    
    try:
        # Parse HTTP method and URL
        request_line = message.split('\n')[0]
        method = request_line.split()[0]
        url = request_line.split()[1]
        
        # Handle full URLs (proxy requests) vs paths (direct requests)
        if url.startswith('http://'):
            # Proxy request: http://example.com/path
            filename = url[7:]  # Remove 'http://'
        elif url.startswith('https://'):
            # HTTPS proxy request
            filename = url[8:]  # Remove 'https://'
        else:
            # Direct request: /path
            filename = url.partition("/")[2] if url.startswith('/') else url
    except IndexError:
        tcpCliSock.close()
        continue
    
    print(f"Method: {method}")
    print("Requested file:", filename)
    
    # Convert filename to safe cache key
    cache_filename = filename.replace("/", "_")
    if not cache_filename:
        cache_filename = "index.html"
    print("Cache key:", cache_filename)
    
    # Only use cache for GET requests
    if method == "GET" and cache_filename in cache:
        print("Cache HIT")
        filepath = cache[cache_filename]
        try:
            with open(filepath, "rb") as f:
                outputdata = f.read()
            tcpCliSock.send(outputdata)
            print("Served from cache.\n")
            tcpCliSock.close()
            continue
        except IOError:
            print("Cache map stale: file missing. Removing.")
            del cache[cache_filename]
    
    # Cache MISS or POST request
    if method == "GET":
        print("Cache MISS → fetching from server...")
    else:
        print(f"{method} request → forwarding to server...")
    
    filepath = "./" + cache_filename
    hostn = filename.replace("www.", "", 1).split('/')[0]
    
    # Handle port numbers in URLs
    if ":" in hostn:
        parts = hostn.split(":")
        host = parts[0]
        port = int(parts[1])
    else:
        host = hostn
        port = 80
    
    print(f"Connecting to {host}:{port}")
    
    try:
        c = socket(AF_INET, SOCK_STREAM)
        c.connect((host, port))
        
        # Construct path
        path = filename[len(hostn):]
        if not path:
            path = "/"
        elif not path.startswith("/"):
            path = "/" + path
        
        # Build request with proper method
        request = f"{method} {path} HTTP/1.1\r\n"
        request += f"Host: {host}\r\n"
        request += "User-Agent: Mozilla/5.0\r\n"
        request += "Accept: */*\r\n"
        
        # For POST requests, preserve headers and body
        if method == "POST":
            # Extract headers from original message
            headers_end = message.find("\r\n\r\n")
            if headers_end == -1:
                headers_end = message.find("\n\n")
                body_start = headers_end + 2 if headers_end != -1 else len(message)
            else:
                body_start = headers_end + 4
            
            # Parse Content-Length and Content-Type
            content_length = 0
            content_type = "application/x-www-form-urlencoded"
            
            for line in message.split('\n'):
                if line.lower().startswith('content-length:'):
                    content_length = int(line.split(':')[1].strip())
                elif line.lower().startswith('content-type:'):
                    content_type = line.split(':', 1)[1].strip()
            
            request += f"Content-Type: {content_type}\r\n"
            request += f"Content-Length: {content_length}\r\n"
            request += "Connection: close\r\n\r\n"
            
            # Add body if present in initial message
            body = message[body_start:]
            request += body
            
            # If body is incomplete, read remaining data
            bytes_received = len(body.encode())
            if bytes_received < content_length:
                remaining = content_length - bytes_received
                additional_data = tcpCliSock.recv(remaining)
                request += additional_data.decode()
        else:
            request += "Connection: close\r\n\r\n"
        
        # Send request to server
        c.send(request.encode())
        
        # Receive response
        buffer = b""
        while True:
            data = c.recv(4096)
            if not data:
                break
            buffer += data
        c.close()
        
        # Cache only GET responses with successful status codes
        if method == "GET" and buffer.startswith(b"HTTP/1.1 200") or buffer.startswith(b"HTTP/1.0 200"):
            with open(filepath, "wb") as tmpFile:
                tmpFile.write(buffer)
            cache[cache_filename] = filepath
            print("Fetched from server → Cached → Sent.\n")
        else:
            print("Fetched from server → Sent (not cached).\n")
        
        # Send response to client
        tcpCliSock.send(buffer)
        
    except Exception as e:
        print("Error:", e)
        tcpCliSock.send(b"HTTP/1.0 502 Bad Gateway\r\n\r\n")
    
    tcpCliSock.close()
