# GithubChatworkBot
Send github event messages to specified Chatwork room with corresponding "To:" field. See code commentaries for more details.
## Preparations:
Before using class you must get Chatwork API Key, add bot account to all designated Chatwork rooms and configure Github webhooks.
Webhook config (go to Github repository configuration page and open "Webhooks & Services" tab):
- Payload url - set to url, where GithubChatworkBot.execute() method is called;
- Content type - application/x-www-form-urlencoded
- Select individual events - Commit comment, Issues, Pull Request, Issue comment, Pull Request review comment

To start cgi http server execute this in server home folder (i.e. folder, that contains "cgi-bin" folder):
<pre>
python3 -m http.server --cgi
</pre>
For testing environment you can use ngrok to make server available from internet:
<pre>
./ngrok http 8000
</pre>

Rename cgi-bin/config.py.sample to cgi-bin/config.py and set required configuration.

## Class usage:
Creating instance:
<pre>
botInstance = GithubChatworkBot()
</pre>

Setting chatwork room id, where messages goes, and corresponding repository names.
Example below means, that events from repository somerepo goes to chatwork room 36410221 and 34543645,
also events from moreonerepo goes to room 34543645.
Do not forget to add bot to all rooms and configure webhooks on all repositories!!
<pre>
botInstance.repository_room_map = {"somerepo": ["36410221", "34543645"], "moreonerepo": ["34543645"]}
</pre>

Setting chatwork API token
<pre>
botInstance.chatwork_token = "4033...12c7"
</pre>

Switch logging ON (better to switch OFF for production):
<pre>
botInstance.logging = True
</pre>

Setting chatwork message max length to prevent flooding
<pre>
botInstance.chatwork_message_max_len = 200
</pre>

Setting account map in format {"github user account id": "chatwork user account name"}
Example below means, that Github user arith_tanaka has Chatwork account id 123456
<pre>
botInstance.chatwork_github_account_map = {"123456": "arith_tanaka", "567890": "arith_yamada"}
</pre>

Execute POST to Chatwork:
<pre>
botInstance.execute()
</pre>
