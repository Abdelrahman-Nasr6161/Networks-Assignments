from socket import *
import sys
import os

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server]')
    sys.exit(2)

# cache map: key = cache filename, value = full file path
cache = {}

# Create server socket
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
    message = tcpCliSock.recv(4096).decode()
    if not message:
        tcpCliSock.close()
        continue

    print(message)

    # GET /www.google.com/index.html HTTP/1.1
    try:
        filename = message.split()[1].partition("/")[2]
    except IndexError:
        tcpCliSock.close()
        continue

    print("Requested file:", filename)

    # Convert filename to safe cache key
    cache_filename = filename.replace("/", "_")
    if not cache_filename:
        cache_filename = "index.html"

    print("Cache key:", cache_filename)

    # ✅ Check in map instead of filesystem directly
    if cache_filename in cache:
        print("Cache HIT")
        filepath = cache[cache_filename]

        try:
            with open(filepath, "rb") as f:
                outputdata = f.read()
            tcpCliSock.send(outputdata)
            print("Served from cache.\n")

        except IOError:
            print("Cache map stale: file missing. Removing.")
            del cache[cache_filename]

    # ✅ Cache MISS → Fetch from remote server
    if cache_filename not in cache:
        print("Cache MISS → fetching from server...")
        filepath = "./" + cache_filename

        # Extract hostname
        hostn = filename.replace("www.", "", 1).split('/')[0]

        # Handle optional port
        if ":" in hostn:
            parts = hostn.split(":")
            host = parts[0]
            port = int(parts[1])
        else:
            host = hostn
            port = 80

        print(f"Connecting to {host}:{port}")

        # Create socket to web server
        try:
            c = socket(AF_INET, SOCK_STREAM)
            c.connect((host, port))

            # Extract path for GET
            path = filename[len(hostn):]
            if not path:
                path = "/"
            elif not path.startswith("/"):
                path = "/" + path

            request = f"GET {path} HTTP/1.1\r\n"
            request += f"Host: {host}\r\n"
            request += "User-Agent: Mozilla/5.0\r\n"
            request += "Accept: */*\r\n"
            request += "Connection: close\r\n\r\n"

            c.send(request.encode())

            buffer = b""
            while True:
                data = c.recv(4096)
                if not data:
                    break
                buffer += data

            c.close()

            # Save to cache file + map
            with open(filepath, "wb") as tmpFile:
                tmpFile.write(buffer)

            cache[cache_filename] = filepath
            tcpCliSock.send(buffer)
            print("Fetched from server → Cached → Sent.\n")

        except Exception as e:
            print("Error:", e)
            tcpCliSock.send(b"HTTP/1.0 502 Bad Gateway\r\n\r\n")

    tcpCliSock.close()
