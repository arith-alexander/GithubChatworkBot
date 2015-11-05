#!/usr/bin/env python

# Dependencies of GithubChatworkBot class
import sys
import pycurl  # to send  POST to Chatwork
import urllib  # to dictionary urlencode
import cgi  # to get POST fields from Github
import json  # to convert payload from json to dictionary
import logging  # log handling

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

    # Setting chatwork room id, where messages goes, and corresponding repository names.
    # Example below means, that events from repository somerepo goes to chatwork room 36410221
    # and events from moreonerepo goes to room 34543645
    # Do not forget to add bot to all rooms and configure webhooks on all repositories!!
    botInstance.repository_room_map = {"somerepo": "36410221", "moreonerepo": "34543645"}

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

    def __init__(self):
        """
        Initialize instance
        """
        self._setPayload()

    def _setPayload(self):
        """
        Set payload property according to payload POST fields, incoming from Github
        """
        github_post_data = cgi.FieldStorage()
        try:
            github_post_data['payload']
        except TypeError:
            self._log('Payload is empty.', 'CRITICAL')
        except KeyError:
            self._log('Payload format is wrong.', 'CRITICAL')

        self._log(github_post_data['payload'].value, 'INFO')
        self.payload = json.loads(github_post_data['payload'].value)

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
            if github_account == self.payload['sender']['login']:
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
        dots = ''
        if len(self.payload['comment']['body']) > self.chatwork_message_max_len:
            dots = '\n...'

        to_list = [self.payload['issue']['user']['login']]
        if self.payload['issue']['assignee']:
            if self.payload['issue']['assignee']['login'] != self.payload['issue']['user']['login']:
                to_list.append(self.payload['issue']['assignee']['login'])

        return self._buildAddresseeString(to_list, self.payload['comment']['body']) + \
            '[info][title]Issue Commented ' + self.payload['comment']['html_url'] + '[/title]' + \
            str(self.payload['comment']['body'][:self.chatwork_message_max_len]) + dots + '[/info]'

    def _buildIssueOpenedMessage(self):
        """
        Build message content, corresponding to github "Issue opened" event
        To all.
        """
        dots = ''
        if len(self.payload['issue']['body']) > self.chatwork_message_max_len:
            dots = '\n...'

        return '[info][title]Issue Opened ' + self.payload['issue']['html_url'] + '[/title]' + \
            str(self.payload['issue']['title']) + '\n\n' + \
            str(self.payload['issue']['body'][:self.chatwork_message_max_len]) + dots + '[/info]'

    def _buildIssueAssignedMessage(self):
        """
        Build message content, corresponding to github "Issue assigned" event.
        To: issue assignee.
        """
        dots = ''
        if len(self.payload['issue']['body']) > self.chatwork_message_max_len:
            dots = '\n...'

        return self._buildAddresseeString([self.payload['assignee']['login']]) + \
            '[info][title]Issue Assigned to ' + self.payload['assignee']['login'] + ' ' + \
            self.payload['issue']['html_url'] + '[/title]' + \
            str(self.payload['issue']['title']) + '\n\n' + \
            str(self.payload['issue']['body'][:self.chatwork_message_max_len]) + dots + '[/info]'

    def _buildIssueClosedMessage(self):
        """
        Build message content, corresponding to github "Issue closed" event.
        To: issue assignee and issue author.
        """
        dots = ''
        if len(self.payload['issue']['body']) > self.chatwork_message_max_len:
            dots = '\n...'

        to_list = [self.payload['issue']['user']['login']]
        if self.payload['issue']['assignee']:
            if self.payload['issue']['assignee']['login'] != self.payload['issue']['user']['login']:
                to_list.append(self.payload['issue']['assignee']['login'])

        return self._buildAddresseeString(to_list) + \
            '[info][title]Issue Closed ' + self.payload['issue']['html_url'] + '[/title]' + \
            str(self.payload['issue']['title']) + '\n\n' + \
            str(self.payload['issue']['body'][:self.chatwork_message_max_len]) + dots + '[/info]'

    def _buildPROpenedMessage(self):
        """
        Build message content, corresponding to github "PR opened" event.
        To all.
        """
        dots = ''
        if len(self.payload['pull_request']['body']) > self.chatwork_message_max_len:
            dots = '\n...'

        return '[info][title]PR Opened ' + self.payload['pull_request']['html_url'] + '[/title]' + \
            str(self.payload['pull_request']['title']) + '\n\n' + \
            str(self.payload['pull_request']['body'][:self.chatwork_message_max_len]) + dots + '[/info]'

    def _buildPRClosedMessage(self):
        """
        Build message content, corresponding to github "PR closed" event.
        To: pull request author.
        """
        dots = ''
        if len(self.payload['pull_request']['body']) > self.chatwork_message_max_len:
            dots = '\n...'

        return self._buildAddresseeString([self.payload['pull_request']['user']['login']]) + \
            '[info][title]PR Closed ' + self.payload['pull_request']['html_url'] + '[/title]' + \
            str(self.payload['pull_request']['title']) + '\n\n' + \
            str(self.payload['pull_request']['body'][:self.chatwork_message_max_len]) + dots + '[/info]'

    def _buildPRCommentedMessage(self):
        """
        Build message content, corresponding to github "PR commented" event.
        To: pull request author and @username.
        """
        dots = ''
        if len(self.payload['comment']['body']) > self.chatwork_message_max_len:
            dots = '\n...'

        return self._buildAddresseeString([self.payload['pull_request']['user']['login']], self.payload['comment']['body']) + \
            '[info][title]PR Commented ' + self.payload['comment']['html_url'] + '[/title]' + \
            str(self.payload['comment']['body'][:self.chatwork_message_max_len] + dots + '[/info]')

    def _buildCommitCommentedMessage(self):
        """
        Build message content, corresponding to github "Commit commented" event.
        To: All and @username (API does not return commit author, maybe need additional request).
        """
        dots = ''
        if len(self.payload['comment']['body']) > self.chatwork_message_max_len:
            dots = '\n...'

        return self._buildAddresseeString(self.payload['comment']['body']) + \
            '[info][title]Commit Commented ' + self.payload['comment']['html_url'] + '[/title]' + \
            str(self.payload['comment']['body'][:self.chatwork_message_max_len]) + dots + '[/info]'

    def _send(self, body):
        """
        Sending POST request to Chatwork with Curl
        :param body: String - Content of message, that will be sent to Chatwork
        """
        room_id = self.repository_room_map[self.payload['repository']['name']]
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
        if not self.payload:
            self._log('Execution failed: payload is empty.', 'CRITICAL')
        if not self.repository_room_map:
            self._log('Execution failed: repository-room map not set.', 'CRITICAL')
        if not self.chatwork_token:
            self._log('Execution failed: chatwork token not set.', 'CRITICAL')

        if self.payload['action'] == 'created' and 'issue' in self.payload.keys():
            self._send(self._buildIssueCommentedMessage())
        elif self.payload['action'] == 'opened' and 'issue' in self.payload.keys():
            self._send(self._buildIssueOpenedMessage())
        elif self.payload['action'] == 'assigned' and 'issue' in self.payload.keys():
            self._send(self._buildIssueAssignedMessage())
        elif self.payload['action'] == 'closed' and 'issue' in self.payload.keys():
            self._send(self._buildIssueClosedMessage())
        elif self.payload['action'] == 'opened' and 'pull_request' in self.payload.keys():
            self._send(self._buildPROpenedMessage())
        elif self.payload['action'] == 'closed' and 'pull_request' in self.payload.keys():
            self._send(self._buildPRClosedMessage())
        elif self.payload['action'] == 'created' and 'pull_request' in self.payload.keys():
            self._send(self._buildPRCommentedMessage())
        # if self.payload['action'] == 'created' and 'comment' in self.payload.keys():
        #     self._send(self._buildCommitCommentedMessage())
        else:
            self._log('Execution failed: event handler is not set.', 'CRITICAL')

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