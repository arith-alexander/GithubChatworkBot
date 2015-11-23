#!/usr/bin/env python
# coding: utf-8

# Admin page.

import sys
import cgi  # to get POST fields from Github
import json  # to convert payload from json to dictionary
import os

here = os.path.dirname(__file__)
config_path = os.path.normpath(here+'/../config.json')

def main(env):

    output = ""

    # Write incoming POST data to config.json
    post_env = env.copy()
    post_env['QUERY_STRING'] = ''
    post_data = cgi.FieldStorage(
        fp=env['wsgi.input'],
        environ=post_env,
        keep_blank_values=True
    )
    if "config" in post_data:
        # Prevent saving invalid code.
        try:
            config = json.loads(post_data['config'].value)
        except ValueError:
            output += '<center style="color:red;">Config format invalid!</center>'
        else:
            with open(config_path, 'w') as f:
                f.write(post_data["config"].value)
                output += '<center style="color:green;">Config saved!</center>'

    # Show textaria with contents of config.py
    with open(config_path, 'r') as f:
        output += '<center><h2> Chatwork Bot config editor</h2><form method="post"><div>Please be careful while editing <input style="width:100px;" type="submit" /><div><textarea style="width:500px; height:450px;" name="config">' + f.read() + '</textarea></center></form>'

    return(output)
