#!/usr/bin/env python3
# coding: utf-8

# Python server.　Starting on system boot with cron.sh by cron.

PORT = 80
import http.server
httpd = http.server.HTTPServer(("", PORT), http.server.CGIHTTPRequestHandler)
try:
    print("Server Started at port:", PORT)
    httpd.serve_forever()
except KeyboardInterrupt:
    print('\nShutting down server')
    httpd.socket.close()
