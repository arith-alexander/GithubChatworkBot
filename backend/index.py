#!/usr/bin/env python
# coding: utf-8

# Admin page.

import sys
import cgi  # to get POST fields from Github
import json
import os
from crontab import CronTab
from crontab import CronSlices

def main(env):

    here = os.path.dirname(__file__)
    config_path = os.path.normpath(here+'/../config.json')
    root_path = os.path.normpath(here+'/../')

    output = ""
    error = ""

    # Get POST request data
    post_env = env.copy()
    post_env['QUERY_STRING'] = ''
    post_data = cgi.FieldStorage(
        fp=env['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )

    # If this is request from configuration form data
    if "config" in post_data:
        # Prevent saving invalid code.
        try:
            config = json.loads(post_data['config'].value)
        except ValueError:
            error += '<center style="color:red;">Config format is invalid!</center>'
        else:
            # Check and update crontab tasks
            for cron_task_name, cron_task in config["cron"].items():
                cron = CronTab(user=cron_task["cron_user"])
                command = "python3 " + root_path + "/frontend/cron.py " + cron_task_name + " >/dev/null 2>&1"

                # Remove old similar jobs, if present
                old_jobs = cron.find_command(command)
                for old_job in old_jobs:
                    cron.remove(old_job)
                # Create new job
                job = cron.new(command=command)
                job.setall(cron_task["cron_definition"])
                if cron_task["active"]:
                    job.enable()
                else:
                    job.disable()
                # Verify and save cron changes
                if job.is_valid() and CronSlices.is_valid(cron_task["cron_definition"]):
                    cron.write()
                else:
                    error += '<center style="color:red;">Cron definition format is invalid (' + cron_task_name + ')!</center>'

            # Write incoming POST data to config.json
            if not error:
                with open(config_path, 'w') as f:
                    f.write(post_data["config"].value)
                    output += '<center style="color:green;">Config saved!</center>'

    # Show textaria with contents of config.py
    with open(config_path, 'r') as f:
        output += error + '<center><h2> Chatwork Bot config editor</h2><form method="post"><div>Please be careful while editing <input style="width:100px;" type="submit" /><div><textarea style="width:500px; height:450px;" name="config">' + f.read() + '</textarea></center></form>'

    return(output)
