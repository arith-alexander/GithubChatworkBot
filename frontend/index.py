#!/usr/bin/env python
# coding: utf-8

# Bot entry script.
# Set url to this script as "Payload url" on Github repository configuration page "Webhooks & Services" tab.
# See detailed documentation inside gcbot.py script.

import cgitb  # error handling
import logging
import cgi
import gcbot
import json

# Make script output visible from browser
print("Content-Type: text/html; charset=utf-8'")
print()

# Write error reports to logs/errors folder
cgitb.enable(False, '../logs/errors', format=0)

# Logger format and rooting
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", filename="../logs/log.txt", filemode="a", level=logging.INFO)

# Check incoming POST data.
# If "payload" key exists in POST data, then this is request from Github.
post_data = cgi.FieldStorage()
if "payload" in post_data:
    f = open('../config.json', 'r')
    config = json.load(f)
    f.close()

    botInstance = gcbot.GithubChatworkBot()
    botInstance.setPayload(post_data)
    botInstance.chatwork_token = config["chatwork_token"]
    botInstance.logging = config["logging"]
    botInstance.chatwork_github_account_map = config["chatwork_github_account_map"]
    botInstance.repository_room_map = config["repository_room_map"]
    botInstance.execute()

