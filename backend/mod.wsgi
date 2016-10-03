# WSGI entry script. Set path to it in Apache config directive WSGIScriptAlias.

import sys
sys.path.insert(0, '/usr/scripts/GithubChatworkBot/backend')
import index
import cgi

def application(env, start_response):
	method = env.get('REQUEST_METHOD')

	if 'GET' == method:
		parameters = cgi.FieldStorage(environ=env,keep_blank_values=True)
		if "heartbeat" in parameters:
			start_response('200 OK', [('Content-Type','text/html')])
			return []

	output = str.encode(index.main(env))
	response_headers = [('Content-type', 'text/html'), ('Content-Length', str(len(output)))]
	start_response('200 OK', response_headers)
	return [output]
