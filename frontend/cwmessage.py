#!/usr/bin/env python
# coding: utf-8

# Dependencies of Message class
import logging #(del?)
import re
import os # (del?)


class ChatworkMessage:
    """
    Contains chatwork message data and methods for its transformation.
    """

    # Logging On/Off (del?)
    logging = True
    # Message title string
    title = ""
    # Message body contents string
    body = ""
    # Addressee chatwork accounts list (example: [645385, 836492])
    addressee_list = []
    # Chatwork message max length (to prevent flooding)
    chatwork_message_max_len = 200
    # add type property?

    def setTitle(self, title):
        """
        Title setter.
        :param title: String - Title string
        """

        self.title = title

    def setBody(self, body):
        """
        Body setter.
        :param body: String - Body contents string
        """

        self.body = body

    def setAddresseeList(self, addressee_list):
        """
        Addressee list setter.
        :param addressee_list: String - Addressee list (example: [645385, 836492])
        """

        self.addressee_list = addressee_list

    def _buildAddresseeString(self, chatwork_addressee_list):
        """
        Build addressee string (chatwork "To:" field)
        :param chatwork_addressee_list: List - List of chatwork addressee ids.
        """
        addressee_string = ""

        for addressee in chatwork_addressee_list:
            addressee_string += '[To:' + str(addressee) + '] '
        return addressee_string

    def _cutBody(self, body_contents):
        """
        Cut message body to designated length and add "..." at the end.
        :param body_contents: String - Body (inner contents) of the message.
        :return: String - Cutted inner content of the message
        """
        body_contents = str(body_contents)

        # adding dots at the end of contents if contents length too large
        dots = ''
        if len(body_contents) > self.chatwork_message_max_len:
            dots = '\n...'

        # Cut to chatwork_message_max_len.
        body_contents = body_contents[:self.chatwork_message_max_len]
        # Use /n, whitespace,、 and 。as cut border.
        cutted_body_contents = "".join(re.split("([\n 。　、]+)", body_contents)[:-1])
        if cutted_body_contents and dots:
            body_contents = cutted_body_contents
        # Cut excessive newlines at the end
        body_contents = body_contents.strip('\n')

        # If [/code] tag was cutted, then add it
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

        # Replace github image tag with plain url
        p = re.compile('!\[.*?\]\((.*?)\)')
        body_contents = p.sub('\g<1>', body_contents)

        # Replace ``` with [code] tag
        p = re.compile('```(.*?)(```|$)', re.DOTALL)
        body_contents = p.sub('[code]\g<1>[/code]', body_contents)

        # execute this somewhere in gcbot
        # Check if content includes special constructions and execute required actions
        body_contents = self._processSpecialConstruction("create_chatwork_task", body_contents)

        return self._cutBody(body_contents)

    def getFormattedContents(self):
        """
        Format message data to a string, which will be sent to Chatwork later
        :return: String - Compiled message contents.
        """

        return self._buildAddresseeString(self.addressee_list) + \
            '[info][title]' + self.title + '[/title]' + \
            self._formatBody(self.body) + '[/info]'

    def _log(self, text, level):
        """
        (del?)
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
