#!/usr/bin/env python
# coding: utf-8

# Dependencies of Message class
import re

class ChatworkMessage:
    """
    Contains chatwork message data and methods for its transformation.
    """

    # Message title string
    _title = ""
    # Message body contents string
    _body = ""
    # Addressee chatwork accounts list (example: [645385, 836492])
    _addressee_list = []
    # Chatwork message max length (to prevent flooding)
    _chatwork_message_max_len = 200

    def setTitle(self, title):
        """
        Title setter.
        :param title: String - Title string
        """

        self._title = title

    def setBody(self, body):
        """
        Body setter.
        :param body: String - Body contents string
        """

        self._body = body

    def setAddresseeList(self, addressee_list):
        """
        Addressee list setter.
        :param addressee_list: List - Addressee list (example: [645385, 836492])
        """

        self._addressee_list = addressee_list

    def getRawBody(self):
        """
        Body getter.
        :return: String - Raw body content.
        """

        return self._body

    def getAddresseeList(self):
        """
        Addressee list getter.
        :return: List - Addressee list (example: [645385, 836492])
        """

        return self._addressee_list;

    def _buildAddresseeString(self, chatwork_addressee_list):
        """
        Build addressee string (chatwork "To:" field)
        :param chatwork_addressee_list: List - List of chatwork addressee ids (example: [645385, 836492]).
        :return: String - Chatwork formatted addressee string (example: "[To:645385] [To:836492]")
        """
        addressee_string = ""

        for addressee in chatwork_addressee_list:
            addressee_string += '[To:' + str(addressee) + '] '
        return addressee_string

    def _cutBody(self, body_contents):
        """
        Cut message body to designated length and add "..." at the end.
        :param body_contents: String - Body (inner contents) of the message.
        :return: String - Trimmed inner content of the message
        """
        body_contents = str(body_contents)

        # adding dots at the end of contents if contents length too large
        dots = ''
        if len(body_contents) > self._chatwork_message_max_len:
            dots = '\n...'

        # Cut to chatwork_message_max_len.
        body_contents = body_contents[:self._chatwork_message_max_len]
        # Use /n, whitespace,、 and 。as cut border.
        trimmed_body_contents = "".join(re.split("([\n 。　、]+)", body_contents)[:-1])
        if trimmed_body_contents and dots:
            body_contents = trimmed_body_contents
        # Cut excessive newlines at the end
        body_contents = body_contents.strip('\n')

        # If [/code] tag was trimmed, then add it
        if body_contents.find("[code]") != -1 and body_contents.find("[/code]") == -1:
            body_contents += "[/code]"

        # If [/code] tag was trimmed, then add it
        if body_contents.find("[code]") != -1 and body_contents.find("[/code]") == -1:
            body_contents += "[/code]"

        return body_contents + dots

    def _formatBody(self, body_contents):
        """
        Formatting inner content of the message. Replace markdown constructions, cut to max allowed length.
        :param body_contents: String - Inner content of the message (after [title] tag inside [info] tag)
        :return: text: String - Filtered inner content of the message
        """
        body_contents = str(body_contents)

        # Replace github image tag ![alt](src) with plain url
        p = re.compile('!\[.*?\]\((.*?)\)')
        body_contents = p.sub('\g<1>', body_contents)

        # Replace github image tag <img> with plain url
        p = re.compile('<img.*src="(.*?)".*>')
        body_contents = p.sub('\g<1>', body_contents)

        # Replace ``` with [code] tag
        p = re.compile('```(.*?)(```|$)', re.DOTALL)
        body_contents = p.sub('[code]\g<1>[/code]', body_contents)

        return self._cutBody(body_contents)

    def getFormattedContents(self):
        """
        Format message data to a string, which will be sent to Chatwork later
        :return: String - Compiled message contents.
        """

        return self._buildAddresseeString(self._addressee_list) + \
            '[info][title]' + self._title + '[/title]' + \
            self._formatBody(self._body) + '[/info]'