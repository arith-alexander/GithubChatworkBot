# WSGI entry script. Set path to it in Apache config directive WSGIScriptAlias.

import sys
sys.path.insert(0, '/usr/scripts/GithubChatworkBot/backend')
import index

def application(env, start_response):
    status = '200 OK'
    output = str.encode(index.main(env))
    response_headers = [('Content-type', 'text/html'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]
