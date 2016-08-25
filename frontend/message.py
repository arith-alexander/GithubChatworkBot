#!/usr/bin/env python
# coding: utf-8

# Dependencies of Message class
import logging #(del?)
import re
import os # (del?)


class Message:
    """
    Contains chatwork message data and methods for its transformation.
    """

    # Logging On/Off (del?)
    logging = True
    # Message title string
    title = ""
    # Message content string
    content = ""
    # Addressee chatwork accounts list (example: [645385, 836492])
    addressee_list = []
    # Chatwork message max length (to prevent flooding)
    chatwork_message_max_len = 200
    # add type property?

    def setTitle(self, title):
        """

        :param title:
        :return:
        """

    def setContent(self, content):
        """

        :param content:
        :return:
        """

    def setAddresseeList(self, addressee_list):
        """

        :param addressee_list:
        :return:
        """

    def _buildAddresseeString(self, chatwork_addressee_list):
        """
        Build addressee string (chatwork "To:" field)
        :param chatwork_addressee_list: List - List of chatwork addressee ids.
        """
        addressee_string = ""

        for addressee in chatwork_addressee_list:
            addressee_string += '[To:' + str(addressee) + '] '
        return addressee_string

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

        # execute this somewhere in gcbot
        # Check if content includes special constructions and execute required actions
        text = self._processSpecialConstruction("create_chatwork_task", text)

        return self._cutInnerContent(text)

    def getContents(self):
        """
        Compile message data to a string, which will be sent to Chatwork later
        :return: String - Compiled message contents.
        """

        return ""

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
