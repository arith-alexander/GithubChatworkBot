#!/usr/bin/env python
# coding: utf-8

# Admin page.

import sys
import cgitb  # error handling
import cgi  # to get POST fields from Github
import json  # to convert payload from json to dictionary

# Make script output visible from browser
print("Content-Type: text/html; charset=utf-8'")
print()

# Write error reports to logs/errors folder
cgitb.enable(1, '../logs/errors', format=0)

# Write incoming POST data to cgi-bin/config.py
post_data = cgi.FieldStorage()
if "config" in post_data:
    # Exec to prevent saving invalid code. If code is invalid, exec throws error.
    try:
        config = json.loads(post_data['config'].value)
    except json.decoder.JSONDecodeError:
        print('<center style="color:red;">Config format invalid!</center>')
    else:
        f = open('../config.json', 'w')
        f.write(post_data["config"].value)
        f.close()
        print('<center style="color:green;">Config saved!</center>')

# Show textaria with contents of config.py
f = open('../config.json', 'r')
print('<center><h2> Chatwork Bot config editor</h2><form method="post"><div>Please be careful while editing <input style="width:100px;" type="submit" /><div><textarea style="width:500px; height:450px;" name="config">' + f.read() + '</textarea></center></form>')
f.close()



