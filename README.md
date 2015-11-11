# GithubChatworkBot
Send github event messages to specified Chatwork room with corresponding "To:" field. See code commentaries for more details.
## General information:
Before using class you must get Chatwork API Key, add bot account to all designated Chatwork rooms and configure Github webhooks.
Webhook config (go to Github repository configuration page and open "Webhooks & Services" tab):
- Payload url - set to url, where GithubChatworkBot.execute() method is called;
- Content type - application/x-www-form-urlencoded
- Select individual events - Commit comment, Issues, Pull Request, Issue comment, Pull Request review comment

To start cgi http server execute this in server home folder (i.e. folder, that contains "cgi-bin" folder):
<pre>
python3 -m http.server --cgi
</pre>
To start server on reboot copy pyserv to /etc/init.d, change path to scripts inside it and launch
<pre>
chkconfig --add pyserv
</pre>
For testing environment you can use ngrok to make server available from internet:
<pre>
./ngrok http 80
</pre>

Rename cgi-bin/config.py.sample to cgi-bin/config.py and set required configuration. Rename logs/log.txt.sample to logs/log.txt and add write rights.

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

## 個人開発環境構築:
- IDEはpyCharm SEがお勧め。公式サイトからダウンロードしてインストール。
- pyenvをインストール https://github.com/yyuu/pyenv
- リポジトリをクローンします（例えばユザーホームディレクトリーで）
```
cd ~
git clone https://github.com/arith-alexander/GithubChatworkBot
```
- ngrokをインストールして起動します　https://ngrok.com/
```
./ngrok http 8000
```
- ngrokを起動してこのような割り当てられたurlをコピーします。
```
http://cf98d1e8.ngrok.io
```
- リポジトリをクローンしたディレクトリー下でHTTPサーバーを起動します。
```
cd ~
python3 -m http.server --cgi 80
```
- 自分用テストのためリポジトリを作ります。このテストリポジトリ https://github.com/arith-alexander/cwprcbot を使ってもおkですが、使う場合は権限をサーシャさんから貰ってください。
- githubでテストリポジトリの設定をします。
Go to Github repository configuration page and open "Webhooks & Services" tab.
Webhook config:
  - Payload url - set to url, where GithubChatworkBot.execute() method is called (http://cf98d1e8.ngrok.io/cgi-bin/index.py)
  - Content type - application/x-www-form-urlencoded
  - Select individual events - Commit comment, Issues, Pull Request, Issue comment, Pull Request review comment
- config.pyスクリプトを編集します。
ChatworkのテストAPIトークンは新しく作ってもいいけど、1日かかりますのでサーシャさんから貰った方が早いです。
chatwork_github_account_mapとrepository_room_mapは例えば以下の通りです。
```
# "chatworkユザーid": "githubユザーの名前"
chatwork_github_account_map = {
    "1471208": "arith-alexander",
}

# "テストリポジトリ": "通知のためのChatworkテスト部屋のid"
repository_room_map = {
    "cwprcbot": ["36410221"],
}
```
- テストChatwork APIキーが発行されたChatworkアカウント（botのアカウント）をテスト部屋に招待します。サーシャさんからChatwork APIを貰った場合は、botのアカウントの名前はArithmetic Github Botです。
- 以上です。動作確認のためgithubでテストリポジトリを開いてIssueを立てます。Chatworkテスト部屋に通知がくるはずです。

##　開発の流れ
- まずはarismileの開発マニュアルを読んでください　https://github.com/ArithmeticCoLtd/arismile-documents
- arismileと同じ流れでタスクブランチ作って、タスクを完成したらgithubへプッシュします。
- githubでPRを作って、PR確認を依頼します。
- 指摘されたところ直したら、マージを依頼します。今のところマージができるのはサーシャさんか首藤さんだけです。マージ権限はサーシャさんから貰えます。
- マージされたら、本番サーバーでgit pullをサーシャさんに依頼するか、sshキーを川井さんから貰って自分でgit pullします。
本番サーバーはEC2インスタンスです。sshでアクセスするには以下のコマンドをターミナルで実行してください。
```
ssh ec2-user@52.32.113.36 -i krpgms.pem
```
`krpgms.pem`はキーへのパスです。キーは川井さんから貰えます。
本番サーバーでのプロジェクトホームディレクトリーは　`/usr/scripts/GithubChatworkBot`です。
```
＄ cd　/usr/scripts/GithubChatworkBot
＄ git pull
```
