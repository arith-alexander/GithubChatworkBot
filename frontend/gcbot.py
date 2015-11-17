#!/usr/bin/env python
# coding: utf-8

# Dependencies of GithubChatworkBot class
import sys
import pycurl  # to send  POST to Chatwork
import urllib  # to dictionary urlencode
import cgi  # to get POST fields from Github
import json  # to convert payload from json to dictionary
import logging  # log handling
import re

class GithubChatworkBot:
    """
    # Class for sending github event messages to specified Chatwork room with corresponding "To:" field.
    #
    # ------------Preparations:------------
    # Before using class you must get Chatwork API Key, add bot account to all designated Chatwork rooms and configure Github webhooks.
    # Webhook config (go to Github repository configuration page and open "Webhooks & Services" tab):
    #   - Payload url - set to url, where GithubChatworkBot.execute() method is called;
    #   - Content type - application/x-www-form-urlencoded
    #   - Select individual events - Commit comment, Issues, Pull Request, Issue comment, Pull Request review comment
    # To start cgi http server execute this in server home folder (i.e. folder, that contains "cgi-bin" folder):
    #   python3 -m http.server --cgi
    # For testing environment you can use ngrok to make server available from internet:  ./ngrok http 8000

    # ------------Class usage:------------
    # Creating instance:
    botInstance = GithubChatworkBot()

    # Setting payload:
    botInstance.setPayload(cgi.FieldStorage())

    # Setting chatwork room id, where messages goes, and corresponding repository names.
    # Example below means, that events from repository somerepo goes to chatwork room 36410221 and 34543645,
    # also events from moreonerepo goes to room 34543645.
    # Do not forget to add bot to all rooms and configure webhooks on all repositories!!
    botInstance.repository_room_map = {"somerepo": ["36410221", "34543645"], "moreonerepo": ["34543645"]}

    # Setting chatwork API token
    botInstance.chatwork_token = "4033...12c7"

    # Switch logging ON (better to switch OFF for production):
    botInstance.logging = True

    # Setting chatwork message max length to prevent flooding
    botInstance.chatwork_message_max_len = 200

    # Setting account map in format {"github user account id": "chatwork user account name"}
    # Example below means, that Github user arith_tanaka has Chatwork account id 123456
    botInstance.chatwork_github_account_map = {"123456": "arith_tanaka", "567890": "arith_yamada"}

    # Execute POST to Chatwork:
    botInstance.execute()
    """

    # Account map in dictionary format {"chatwork user account id": "github user account name", ...}
    chatwork_github_account_map = {}
    # Logging On/Off
    logging = True
    # Chatwork room id, where messages goes, and corresponding repository names
    # in dictionary format {"github repository name": "chatwork room id", ...}
    repository_room_map = {}
    # Chatwork API token
    chatwork_token = ''
    # Chatwork message max length (to prevent flooding)
    chatwork_message_max_len = 200
    # Payload, that comes from Github. For internal usage.
    _payload = {}

    def setPayload(self, github_post_data):
        """
        Set payload property according to payload POST fields, incoming from Github
        :param github_post_data: Dictionary - POST fields, incoming from Github
        """
        try:
            github_post_data['payload']
        except TypeError:
            self._log('Payload is empty.', 'CRITICAL')
        except KeyError:
            self._log('Payload format is wrong.', 'CRITICAL')

        self._log(github_post_data['payload'].value, 'INFO')
        self._payload = json.loads(github_post_data['payload'].value)

    def _getChatworkUsericonByGithubName(self, github_account):
        """
        Convert github account name into Chatwork "icon+username" code.
        :param github_account: String
        :return: String - "icon+username" code [piconname:123]
        """
        for map_chatwork_acount, map_github_account in self.chatwork_github_account_map.items():
            if github_account == map_github_account:
                return '[piconname:' + map_chatwork_acount + ']'
        return "unknown (" + github_account + ")"

    def _buildAddresseeString(self, guthub_addressee_list, text=""):
        """
        Build addressee string (chatwork "To:" field)
        :param guthub_addressee_list: List - List of github addressee, if present.
        :param text: String - Contents of comment on github, if present (need for additional parsing, such as @username).
        """
        chatwork_addressee_list = []
        addressee_string = ''

        # Parsing @username from github comment text. If found, add this username as chatwork addressee.
        for chatwork_acount, github_account in self.chatwork_github_account_map.items():
            if text.find(github_account) > -1:
                chatwork_addressee_list.append(chatwork_acount)

        # Converting guthub_addressee_list to chatwork_addressee_list.
        for chatwork_acount, github_account in self.chatwork_github_account_map.items():
            if github_account in guthub_addressee_list:
                chatwork_addressee_list.append(chatwork_acount)

        # Remove duplicates.
        chatwork_addressee_list = list(set(chatwork_addressee_list))

        # Remove event sender account from list. He already knows about event.
        for chatwork_acount, github_account in self.chatwork_github_account_map.items():
            if github_account == self._payload['sender']['login']:
                if chatwork_acount in chatwork_addressee_list:
                    chatwork_addressee_list.remove(chatwork_acount)

        # Building and returning chatwork addressee string.
        for addressee in chatwork_addressee_list:
            addressee_string += '[To:' + str(addressee) + '] '
        return addressee_string

    def _buildIssueCommentedMessage(self):
        """
        Build message content, corresponding to github "Issue commented" event.
        To: issue assignee, issue author and @username.
        """
        to_list = [self._payload['issue']['user']['login']]

        if self._payload['issue']['assignee']:
            if self._payload['issue']['assignee']['login'] != self._payload['issue']['user']['login']:
                to_list.append(self._payload['issue']['assignee']['login'])

        return self._buildAddresseeString(to_list, self._payload['comment']['body']) + \
            '[info][title]Issue Commented by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['comment']['html_url'] + '[/title]' + \
            self._filterInnerContent(self._payload['comment']['body']) + '[/info]'

    def _buildIssueOpenedMessage(self):
        """
        Build message content, corresponding to github "Issue opened" event
        To all and @username.
        """
        return self._buildAddresseeString(guthub_addressee_list=[], text=self._payload['issue']['body']) + \
            '[info][title]Issue Opened by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['issue']['html_url'] + '[/title]' + \
            str(self._payload['issue']['title']) + '\n\n' + \
            self._filterInnerContent(self._payload['issue']['body']) + '[/info]'

    def _buildIssueAssignedMessage(self):
        """
        Build message content, corresponding to github "Issue assigned" event.
        To: issue assignee and @username in body.
        """
        to_list = [self._payload['assignee']['login']]

        return self._buildAddresseeString(guthub_addressee_list=to_list, text=self._payload['issue']['body']) + \
            '[info][title]Issue Assigned to ' + self._getChatworkUsericonByGithubName(self._payload['assignee']['login']) + \
            ' by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['issue']['html_url'] + '[/title]' + \
            str(self._payload['issue']['title']) + '[/info]'

    def _buildIssueClosedMessage(self):
        """
        Build message content, corresponding to github "Issue closed" event.
        To: issue assignee and issue author and @username in body.
        """
        to_list = [self._payload['issue']['user']['login']]
        if self._payload['issue']['assignee']:
            if self._payload['issue']['assignee']['login'] != self._payload['issue']['user']['login']:
                to_list.append(self._payload['issue']['assignee']['login'])

        return self._buildAddresseeString(guthub_addressee_list=to_list, text=self._payload['issue']['body']) + \
            '[info][title]Issue Closed by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['issue']['html_url'] + '[/title]' + \
            str(self._payload['issue']['title']) + '\n\n' + \
            self._filterInnerContent(self._payload['issue']['body']) + '[/info]'

    def _buildPROpenedMessage(self):
        """
        Build message content, corresponding to github "PR opened" event.
        To all.
        """
        return '[info][title]PR Opened by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['pull_request']['html_url'] + '[/title]' + \
            str(self._payload['pull_request']['title']) + '\n\n' + \
            self._filterInnerContent(self._payload['pull_request']['body']) + '[/info]'

    def _buildPRClosedMessage(self):
        """
        Build message content, corresponding to github "PR closed" event.
        To: pull request author.
        """
        to_list = [self._payload['pull_request']['user']['login']]

        return self._buildAddresseeString(guthub_addressee_list=to_list) + \
            '[info][title]PR Closed by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['pull_request']['html_url'] + '[/title]' + \
            str(self._payload['pull_request']['title']) + '\n\n' + \
            self._filterInnerContent(self._payload['pull_request']['body']) + '[/info]'

    def _buildPRCommentedMessage(self):
        """
        Build message content, corresponding to github "PR commented" event.
        To: pull request author and @username.
        """
        to_list = [self._payload['pull_request']['user']['login']]

        return self._buildAddresseeString(to_list, self._payload['comment']['body']) + \
            '[info][title]PR Commented by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['comment']['html_url'] + '[/title]' + \
            self._filterInnerContent(self._payload['comment']['body']) + '[/info]'

    def _buildCommitCommentedMessage(self):
        """
        Build message content, corresponding to github "Commit commented" event.
        To: All and @username (API does not return commit author, maybe need additional request).
        """
        return self._buildAddresseeString(guthub_addressee_list=[], text=self._payload['comment']['body']) + \
            '[info][title]Commit Commented by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['comment']['html_url'] + '[/title]' + \
            self._filterInnerContent(self._payload['comment']['body']) + '[/info]'

    def _buildPRAssignedMessage(self):
        """
        Build message content, corresponding to github "Issue assigned" event.
        To: issue assignee.
        """
        to_list = [self._payload['assignee']['login']]

        return self._buildAddresseeString(guthub_addressee_list=to_list) + \
            '[info][title]PR Assigned to ' + self._getChatworkUsericonByGithubName(self._payload['assignee']['login']) + \
            ' by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['pull_request']['html_url'] + '[/title]' + \
            str(self._payload['pull_request']['title']) + '[/info]'

    def _send(self, body):
        """
        Sending POST request to Chatwork with Curl
        :param body: String - Content of message, that will be sent to Chatwork
        """
        room_ids = []
        if self._payload['repository']['name'] not in self.repository_room_map.keys():
            self._log('Execution failed: room not set for repository ' + self._payload['repository']['name'], 'CRITICAL')
        else:
            room_ids = self.repository_room_map[self._payload['repository']['name']]
        for room_id in room_ids:
            c = pycurl.Curl()
            c.setopt(pycurl.URL, 'https://api.chatwork.com/v1/rooms/' + str(room_id) + '/messages')
            c.setopt(pycurl.HTTPHEADER, ['X-ChatWorkToken: ' + self.chatwork_token])
            c.setopt(pycurl.POST, 1)
            c.setopt(pycurl.POSTFIELDS, urllib.parse.urlencode({'body': body}))
            c.perform()

    def execute(self):
        """
        Setting event handlers and executing POST process.
        """
        if not self._payload:
            self._log('Execution failed: payload is empty.', 'CRITICAL')
        if not self.repository_room_map:
            self._log('Execution failed: repository-room map not set.', 'CRITICAL')
        if not self.chatwork_token:
            self._log('Execution failed: chatwork token not set.', 'CRITICAL')

        body = ''
        if self._payload['action'] == 'created' and 'issue' in self._payload.keys():
            body = self._buildIssueCommentedMessage()
        elif self._payload['action'] == 'opened' and 'issue' in self._payload.keys():
            body = self._buildIssueOpenedMessage()
        elif self._payload['action'] == 'assigned' and 'issue' in self._payload.keys():
            body = self._buildIssueAssignedMessage()
        elif self._payload['action'] == 'closed' and 'issue' in self._payload.keys():
            body = self._buildIssueClosedMessage()
        elif self._payload['action'] == 'opened' and 'pull_request' in self._payload.keys():
            body = self._buildPROpenedMessage()
        elif self._payload['action'] == 'closed' and 'pull_request' in self._payload.keys():
            body = self._buildPRClosedMessage()
        elif self._payload['action'] == 'created' and 'pull_request' in self._payload.keys():
            body = self._buildPRCommentedMessage()
        elif self._payload['action'] == 'assigned' and 'pull_request' in self._payload.keys():
            body = self._buildPRAssignedMessage()
        elif self._payload['action'] == 'created' and 'comment' in self._payload.keys():
            body = self._buildCommitCommentedMessage()
        else:
            self._log('Execution failed: event handler is not set.', 'CRITICAL')

        self._send(body)

    def _filterInnerContent(self, text):
        """
        Filtering inner content of the message. Cutting and replacing.
        :param text: String - Inner content of the message (after [title] tag inside [info] tag)
        :return: text: String - Filtered inner content of the message
        """
        text = str(text)

        # adding dots at the end of contents if contents length too large
        dots = ''
        if len(text) > self.chatwork_message_max_len:
            dots = '\n...'

        # cutting to chatwork_message_max_len
        text = text[:self.chatwork_message_max_len]

        # Replace ``` with [code] tag
        p = re.compile('```(.*?)(```|$)', re.DOTALL)
        text = p.sub('[code]\g<1>[/code]', text)

        return text + dots

    def _log(self, text, level):
        """
        Logger. Wrapper for python "logging" module.
        :param text: String - Text, that will be logged.
        :param level: String - Level of severity. Similar to logging module level of severity (see python logging documentation).
        """
        if self.logging:
            if level == 'DEBUG':
                logging.debug(text)
            if level == 'INFO':
                logging.info(text)
            if level == 'WARNING':
                logging.warning(text)
            if level == 'ERROR':
                logging.error(text)
            if level == 'CRITICAL':
                logging.critical(text)
                sys.exit(0)
