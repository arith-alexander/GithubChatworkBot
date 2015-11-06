#!/usr/bin/env python

# Bot entry script.
# Set url to this script as "Payload url" on Github repository configuration page "Webhooks & Services" tab.
# See detailed documentation inside gcbot.py script.

# todo send messages from one repo to several rooms

import cgitb  # error handling
import gcbot # GithubChatworkBot class
import config # global configuration
import logging

# Make script output visible from browser
print("Content-Type: text/html")
print()

# Write error reports to logs/errors folder
cgitb.enable(False, 'logs/errors', format=0)

# Logger format and rooting
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", filename="logs/log.txt", filemode="a", level=logging.INFO)

botInstance = gcbot.GithubChatworkBot()
botInstance.chatwork_token = config.chatwork_token
botInstance.logging = config.logging
botInstance.chatwork_github_account_map = config.chatwork_github_account_map
botInstance.repository_room_map = config.repository_room_map
botInstance.execute()
