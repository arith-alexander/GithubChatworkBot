#!/usr/bin/env python
# coding: utf-8

# Bot entry script.
# Set url to this script as "Payload url" on Github repository configuration page "Webhooks & Services" tab.
# See detailed documentation inside gcbot.py script.

import cgitb  # error handling
import gcbot # GithubChatworkBot class
import config # global configuration
import logging
import cgi
import urllib

# Make script output visible from browser
print("Content-Type: text/html; charset=utf-8'")
print()

# Write error reports to logs/errors folder
cgitb.enable(False, 'logs/errors', format=0)

# Logger format and rooting
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", filename="logs/log.txt", filemode="a", level=logging.INFO)

# Check incoming POST data.
# If "config" key exists in POST data, then this is request from browser to change config.
# Write incoming POST data to cgi-bin/config.py
# @todo Dramatically lowering security! Temporary solution, i hope.
github_post_data = cgi.FieldStorage()
if "config" in github_post_data:
    # Exec to prevent saving invalid code. If code is invalid, exec throws error.
    exec(github_post_data["config"].value)
    f = open('cgi-bin/config.py', 'w')
    f.write(github_post_data["config"].value)
    f.close()
    print('<center>Config saved!</center>')
# If "payload" key exists in POST data, then this is request from Github.
elif "payload" in github_post_data:
    botInstance = gcbot.GithubChatworkBot()
    botInstance.chatwork_token = config.chatwork_token
    botInstance.logging = config.logging
    botInstance.chatwork_github_account_map = config.chatwork_github_account_map
    botInstance.repository_room_map = config.repository_room_map
    botInstance.execute()

# Show textaria with contents of config.py
f = open('cgi-bin/config.py', 'r')
print('<center><h2> Chatwork Bot config editor</h2><form method="post"><div>Please be careful while editing <input style="width:100px;" type="submit" /><div><textarea style="width:500px; height:450px;" name="config">' + f.read() + '</textarea></center></form>')
f.close()



