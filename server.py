#!/usr/bin/env python
# coding: utf-8

# Python server. Same as "python -m http.server --cgi 80", currently not used, replaced by pyserv service.

PORT = 80
import http.server
httpd = http.server.HTTPServer(("", PORT), http.server.CGIHTTPRequestHandler)
try:
    print("Server Started at port:", PORT)
    httpd.serve_forever()
except KeyboardInterrupt:
    print('\nShutting down server')
    httpd.socket.close()
