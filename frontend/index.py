#!/usr/bin/env python
# coding: utf-8

# Bot entry script.
# Set url to this script as "Payload url" on Github repository configuration page "Webhooks & Services" tab.
# See detailed documentation inside gcbot.py script.

import logging
import cgi
import gcbot
import json
import os

here = os.path.dirname(__file__)
config_path = os.path.normpath(here+'/../config.json')
log_path = os.path.join(here, '../logs/log.txt')

# Logger format and rooting
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", filename=log_path, filemode="a", level=logging.INFO)

def main(env):
    # Check incoming POST data.
    # If "payload" key exists in POST data, then this is request from Github.
    post_env = env.copy()
    post_env['QUERY_STRING'] = ''
    post_data = cgi.FieldStorage(
        fp=env['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )
    if "payload" in post_data:
        with open(config_path, 'r') as f:
            config = json.load(f)

        botInstance = gcbot.GithubChatworkBot()
        botInstance.setPayload(post_data)
        botInstance.chatwork_token = config["chatwork_token"]
        botInstance.logging = config["logging"]
        botInstance.chatwork_github_account_map = config["chatwork_github_account_map"]
        botInstance.repository_room_map = config["repository_room_map"]
        botInstance.executeWebhookHandler()
    return "ok"
