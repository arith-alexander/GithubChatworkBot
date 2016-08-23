#!/usr/bin/env python
# coding: utf-8

# Dependencies of GithubChatworkBot class
import sys
import urllib
import urllib.request
import socket
import cgi  # to get POST fields from Github
import json  # to convert payload from json to dictionary
import logging  # log handling
import re
from github import Github
import time
import datetime
import cwui

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
    # Github API token
    github_token = ''
    # Chatwork message max length (to prevent flooding)
    chatwork_message_max_len = 200
    # Payload, that comes from Github. For internal usage.
    _payload = {}
    # True for send requests to UI, False for API
    ui_active = True
    # UI login account email
    ui_login_email = ""
    # UI login account ID
    ui_login_id = ""
    # UI login password
    ui_login_password = ""

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
        for map_github_account, account_settings in self.chatwork_github_account_map.items():
            if github_account == map_github_account:
                return '[piconname:' + account_settings['chatwork_account'] + ']'
        return "unknown (" + github_account + ")"

    def _getChatworkUserIdByGithubName(self, github_account):
        """
        Convert github account name into Chatwork user id.
        :param github_account: String - Github account name
        :return: Integer - Chatwork user id or 0, if user not found
        """
        for map_github_account, account_settings in self.chatwork_github_account_map.items():
            if github_account == map_github_account:
                return account_settings['chatwork_account']
        return 0

    def _getAddresseeListFromMessageContents(self, text):
        """
        Extract addressee list from given chatwork-formatted message contents.
        :param text: String - Chatwork-formatted message contents
        :return: List - Chatwork user id list
        """
        addressee_list = []
        for map_github_account, account_settings in self.chatwork_github_account_map.items():
            if re.search('\[To:' + account_settings['chatwork_account'] + '\]', text):
                addressee_list.append(account_settings['chatwork_account'])
        return addressee_list

    def _buildAddresseeString(self, guthub_addressee_list, text=""):
        """
        Build addressee string (chatwork "To:" field)
        :param guthub_addressee_list: List - List of github addressee, if present.
        :param text: String - Contents of comment on github, if present (need for additional parsing, such as @username).
        """
        chatwork_addressee_list = []
        addressee_string = ''

        # Parsing @username from github comment text. If found, add this username as chatwork addressee.
        for github_account, account_settings in self.chatwork_github_account_map.items():
            if text.find(github_account) > -1:
                chatwork_addressee_list.append(account_settings['chatwork_account'])

        # Converting guthub_addressee_list to chatwork_addressee_list.
        for github_account, account_settings in self.chatwork_github_account_map.items():
            if github_account in guthub_addressee_list:
                chatwork_addressee_list.append(account_settings['chatwork_account'])

        # Remove duplicates.
        chatwork_addressee_list = list(set(chatwork_addressee_list))

        # Remove event sender account from list. He already knows about event.
        for github_account, account_settings in self.chatwork_github_account_map.items():
            if github_account == self._payload['sender']['login']:
                if account_settings['chatwork_account'] in chatwork_addressee_list:
                    chatwork_addressee_list.remove(account_settings['chatwork_account'])

        # Building and returning chatwork addressee string.
        for addressee in chatwork_addressee_list:
            addressee_string += '[To:' + str(addressee) + '] '
        return addressee_string

    def _buildIssueCommentedMessage(self):
        """
        Build message content, corresponding to github "Issue commented" event.
        To: issue assignees, issue author and @username.
        """
        to_list = [self._payload['issue']['user']['login']]

        for assignee in self._payload['issue']['assignees']:
            if assignee['login'] != self._payload['issue']['user']['login']:
                to_list.append(assignee['login'])

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
        To: issue assignees and issue author and @username in body.
        """
        to_list = [self._payload['issue']['user']['login']]

        for assignee in self._payload['issue']['assignees']:
            if assignee['login'] != self._payload['issue']['user']['login']:
                to_list.append(assignee['login'])

        return self._buildAddresseeString(guthub_addressee_list=to_list, text=self._payload['issue']['body']) + \
            '[info][title]Issue Closed by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['issue']['html_url'] + '[/title]' + \
            str(self._payload['issue']['title']) + '[/info]'

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
        To: pull request author and assignees.
        """
        to_list = [self._payload['pull_request']['user']['login']]

        for assignee in self._payload['pull_request']['assignees']:
            if assignee['login'] != self._payload['pull_request']['user']['login']:
                to_list.append(assignee['login'])

        return self._buildAddresseeString(guthub_addressee_list=to_list) + \
            '[info][title]PR Closed by ' + self._getChatworkUsericonByGithubName(self._payload['sender']['login']) + '\n' + \
            self._payload['pull_request']['html_url'] + '[/title]' + \
            str(self._payload['pull_request']['title']) + '[/info]'

    def _buildPRCommentedMessage(self):
        """
        Build message content, corresponding to github "PR commented" event.
        To: pull request author, assignees and @username.
        """
        to_list = [self._payload['pull_request']['user']['login']]

        for assignee in self._payload['pull_request']['assignees']:
            if assignee['login'] != self._payload['pull_request']['user']['login']:
                to_list.append(assignee['login'])

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

    def _routeWebhookEventToRoom(self, body):
        """
        Route webhook event message (such as new issues, comments etc) to corresponding Chatwork room.
        :param body: String - Content of message, that will be sent to Chatwork
        """
        # Route message by repository name
        room_ids = []
        if self._payload['repository']['name']  in self.repository_room_map.keys():
            room_ids = self.repository_room_map[self._payload['repository']['name']]

        # Route message by addressee
        addressee_list = self._getAddresseeListFromMessageContents(body)
        for addressee in addressee_list:
            for github_account, account_settings in self.chatwork_github_account_map.items():
                if addressee == account_settings['chatwork_account']:
                    room_ids += account_settings['chatwork_rooms']

        # Send message
        for room_id in room_ids:
            endpoint = '/rooms/' + str(room_id) + '/messages'
            data = {"body": body}
            self.chatworkRequest(endpoint, data)

    def chatworkRequest(self, endpoint, data):
        """
        Send POST request to Chatwork
        :param endpoint: String - Chatwork API endpoint (for example, "/rooms/12345/messages")
        :param data: Dictionary - Post data, that will be sent to Chatwork API
        :return: String - response from Chatwork API
        """

        # Send message requests through UI
        if self.ui_active:
            match = re.search("/rooms/([0-9]+)/messages", endpoint)
            if match:
                room_id = match.group(1)
                cwuiInstance = cwui.ChatworkUI(self.ui_login_email, self.ui_login_id, self.ui_login_password)
                return cwuiInstance.message(data["body"], room_id)

        # Send all other requests through API
        return self.chatworkApiRequest(endpoint, data)

    def chatworkApiRequest(self, endpoint, data):
        """
        Send POST request to Chatwork
        :param endpoint: String - Chatwork API endpoint (for example, "/rooms/12345/messages")
        :param data: Dictionary - Post data, that will be sent to Chatwork API
        :return: String - response from Chatwork API
        """
        response_data = False
        socket.setdefaulttimeout(30)
        url = 'https://api.chatwork.com/v1'
        headers = {"X-ChatWorkToken": self.chatwork_token}
        data = urllib.parse.urlencode(data)
        data = data.encode('utf-8') # data should be bytes
        req = urllib.request.Request(url + endpoint, data, headers)
        with urllib.request.urlopen(req) as response:
            response_data = response.read()
        return response_data

    def executeWebhookHandler(self):
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

        self._routeWebhookEventToRoom(body)

    def _cutInnerContent(self, text):
        """
        Cut message to designated length and add "..." at the end.
        :param text: String - Inner content of the message (after [title] tag inside [info] tag)
        :return: text: String - Cutted inner content of the message
        """
        text = str(text)

        # adding dots at the end of contents if contents length too large
        dots = ''
        if len(text) > self.chatwork_message_max_len:
            dots = '\n...'

        # Cut to chatwork_message_max_len.
        text = text[:self.chatwork_message_max_len]
        # Use /n, whitespace,、 and 。as cut border.
        cutted_text = "".join(re.split("([\n 。　、]+)", text)[:-1])
        if cutted_text and dots:
            text = cutted_text
        # Cut excessive newlines at the end
        text = text.strip('\n')

        # If [/code] tag was cutted, then add it
        if text.find("[code]") != -1 and text.find("[/code]") == -1:
            text += "[/code]"

        return text + dots

    def _filterInnerContent(self, text):
        """
        Filtering inner content of the message. Replace markdown constructions and execute special constructions, if found.
        :param text: String - Inner content of the message (after [title] tag inside [info] tag)
        :return: text: String - Filtered inner content of the message
        """
        text = str(text)

        # Replace github image tag with plain url
        p = re.compile('!\[.*?\]\((.*?)\)')
        text = p.sub('\g<1>', text)

        # Replace ``` with [code] tag
        p = re.compile('```(.*?)(```|$)', re.DOTALL)
        text = p.sub('[code]\g<1>[/code]', text)

        # Check if content includes special constructions and execute required actions
        text = self._processSpecialConstruction("create_chatwork_task", text)

        return self._cutInnerContent(text)

    def _processSpecialConstruction(self, construction_type, text):
        """
        Check if text includes special constructions and execute required actions
        :param construction_type: String - One of the following values: "create_chatwork_task"
        :param text: String - Text, which supposed to include special constructions
        :return: text: String - Filtered text
        """

        if construction_type == "create_chatwork_task":
            # If message content starts with construction like !task:@somename @anothername:2016.01.11:123123 567567
            # then we must create new chatwork task, assigned to chatwork users somename and anothername
            # and send it to chatwork rooms id 123123 and 567567.
            # Task content will be equivalent to message content and deadline will be set to 2016.01.11.
            # Only first parameter are required, the rest are optional.
            # If deadline parameter not set, it will be set with current date.
            # If room parameter not set, it will be set according chatwork_github_account_map configuration.
            match = re.search("^!task:([^:\n]+):?(\d\d\d\d\.\d\d\.\d\d)?:?([\d ]+)?", text)
            if match:
                # Convert data to chatwork format
                github_assignees = match.group(1)
                chatwork_assignees = []
                for github_assignee in github_assignees.split():
                    chatwork_assignees.append(self._getChatworkUserIdByGithubName(github_assignee.replace("@", "")))

                if match.group(2) is None:
                    chatwork_deadline = int(time.time())
                else:
                    dt = datetime.datetime.strptime(match.group(2), '%Y.%m.%d')
                    chatwork_deadline = int(time.mktime(dt.timetuple()))

                if match.group(3) is None:
                    chatwork_rooms = self.repository_room_map[self._payload['repository']['name']]
                else:
                    chatwork_rooms = match.group(3)
                    chatwork_rooms = chatwork_rooms.split()

                # Remove special construction itself from message content
                text = '\n'.join(text.split('\n')[1:])

                # Create new chatwork task
                for chatwork_room in chatwork_rooms:
                    self.chatworkRequest(
                        '/rooms/' + chatwork_room + '/tasks',
                        {"body": text, "limit": chatwork_deadline, "to_ids": ",".join(chatwork_assignees)}
                    )
                sys.exit(0)

        return text

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

    def executeCronTask(self, cron_task_name, params):
        """
        Execute cron task.
        As opposed to webhook handler methods, this method has no need of payload parameters and called by crontab (web server is not needed).
        :param cron_task_name: String - identifier of cron task, that will be executed.
        :param params: Array - Additional parameters (vary from task to task).
        :return: Any - Execution result.
        """
        result = ""

        # Send list of ready PRs to designated Chatwork room, if present.
        if cron_task_name == "ready_pr":
            # Setup Github object
            if not self.github_token:
                return "Github API key not found"
            github = Github(self.github_token)
            repository_str = ""
            for repository in params["repositories"]:
                repository_str += " repo:" + repository
            # Search for PRs with title containing search_patterns, defined in config
            for search_pattern in params["search_patterns"]:
                for pr in github.search_issues(search_pattern + " state:open type:pr in:title " + repository_str, sort="updated", order="asc"):
                    result += pr.title + "\n" + pr.html_url + "\n"
            # Send notification to Chatwork
            if result:
                result = "[info][title]Ready PR is found[/title]" + result + "[/info]"
                self.chatworkRequest('/rooms/' + params["room_id"] + '/messages', {"body": result})
            return result
        else:
            return "Cron task handler not found"
