#!/usr/bin/env python
# coding: utf-8

# This script is called by cron. You can find crontab config in config.json
# To view all crontab tasks, use this ssh command: for user in $(cut -f1 -d: /etc/passwd); do crontab -u $user -l; done
# To execute task directly by ssh, use this command in script root directory: python3 frontend/cron.py taskname
# You can test cron definition here http://cron.schlitt.info
# Log is here /var/log/cron

# To add new task, you must:
# - define its config in config.json;
# - add handler in executeCronTask method of GithubChatworkBot class.

import sys
import logging
import gcbot
import json
import os
import time


def main():
    # Acquire initialisation variables
    try:
        sys.argv[1]
    except IndexError:
        return "You must define task name as first argument"

    cron_task_name = sys.argv[1]

    here = os.path.dirname(__file__)
    config_path = os.path.normpath(here+'/../config.json')
    log_path = os.path.join(here, '../logs/log.txt')

    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", filename=log_path, filemode="a", level=logging.INFO)

    with open(config_path, 'r') as f:
        config = json.load(f)

    if cron_task_name not in config["cron"].keys():
        return "Defined task name is not found in configuration file"

    # Execute cron task, if current date is not excluded in config
    if time.strftime("%Y.%m.%d") not in config["cron"][cron_task_name]["exclude_days"]:
        botInstance = gcbot.GithubChatworkBot()
        botInstance.chatwork_token = config["chatwork_token"]
        botInstance.github_token = config["github_token"]
        botInstance.logging = config["logging"]
        botInstance.chatwork_github_account_map = config["chatwork_github_account_map"]
        botInstance.repository_room_map = config["repository_room_map"]
        botInstance.ui_login_email = config["ui"]["login_email"]
        botInstance.ui_login_id = config["ui"]["login_id"]
        botInstance.ui_login_password = config["ui"]["login_password"]
        return botInstance.executeCronTask(cron_task_name, config["cron"][cron_task_name])

if __name__ == "__main__":
    print(main())
