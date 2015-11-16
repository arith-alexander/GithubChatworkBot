#!/usr/bin/env python
# coding: utf-8

# "python -m http.server --cgi 80" はタイムアウトがあります。代わりにこのスクリプトを使ってください。

PORT = 8000
import http.server
handler = http.server.CGIHTTPRequestHandler
handler.cgi_directories = ['/']
httpd = http.server.HTTPServer(("", PORT), http.server.CGIHTTPRequestHandler)
try:
    print("Server Started at port:", PORT)
    httpd.serve_forever()
except KeyboardInterrupt:
    print('\nShutting down server')
    httpd.socket.close()
