#!/usr/bin/env python
# coding: utf-8

# Dependencies of CWUI class
import sys
import socket
import json
import logging
import re
import requests
import pickledb
import os


class ChatworkUI:
    """
    Class for communication with Chatwork through UI (as API alternative).
    """

    # Logging On/Off
    logging = True
    # Chatwork UI URL
    url = "https://kcw.kddi.ne.jp"
    # Cookies dictionary
    cookies = {}
    # Access token (GET parameter "_t")
    access_token = ""
    # Request timeout in seconds
    request_timeout = 10
    # Login account email
    login_email = ""
    # Login account ID
    login_id = ""
    # Login password
    login_password = ""
    # Storage exemplar
    storage = ""

    def __init__(self, login_email, login_id, login_password, logging=True):
        """
        Initialize class properties
        :param login_email: String - Login account email
        :param login_id: Int - Login account ID
        :param login_password: String - Login password
        :return: void
        """
        self.logging = logging
        self.login_email = login_email
        self.login_id = login_id
        self.login_password = login_password

        # Get cookies and access_token from external storage.
        # If external storage is empty or values expired, it will be requested from Chatwork later.
        self.storage = pickledb.load(os.path.dirname(__file__) + '/cwui.db', True)
        if self.storage.get("cwssid"):
            self.cookies["cwssid"] = self.storage.get("cwssid")
        if self.storage.get("AWSELB"):
            self.cookies["AWSELB"] = self.storage.get("AWSELB")
        if self.storage.get("access_token"):
            self.access_token = self.storage.get("access_token")

        # Request cookies and access_token from Chatwork
        if not self.cookies:
            if not self._login():
                self._log("Login failed!", 'CRITICAL')
        if not self.access_token:
            if not self._getAccessToken():
                self._log("ACCESS_TOKEN not found!", 'CRITICAL')

    def _request(self, query_string, post_parameters={}):
        """
        Send request to Chatwork UI (for internal usage)
        :param query_string: String - Part of request url string, that will be added to self.url
        :param post_parameters: Dict - Post parameters. Request will be GET, if post_parameters is not specified.
        :return: [Response] object of [requests] module
        """

        # Set realistic headers just in case
        headers = {
            "Host": "kcw.kddi.ne.jp",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:45.0) Gecko/20100101 Firefox/45.0"
        }

        if post_parameters:
            req = requests.post(self.url + query_string, post_parameters, headers=headers, cookies=self.cookies, allow_redirects=False, timeout=self.request_timeout)
        else:
            req = requests.get(self.url + query_string, headers=headers, cookies=self.cookies, allow_redirects=False, timeout=self.request_timeout)
        return req

    def _login(self):
        """
        Send POST request to Chatwork login url and get response cookies "cwssid" and "AWSELB"
        ("AWSELB" is not necessary for message posting).
        :return: Dict - Cookies dictionary or False if failed
        """
        post = {
            "auto_login": "on",
            "email": self.login_email,
            "login": "ログイン",
            "password": self.login_password
        }

        req = self._request("/login.php?lang=ja&args=", post)

        try:
            req.cookies["cwssid"]
        except IndexError:
            self._log("Login failed: can't get cwssid cookie", 'INFO')
            return False
        try:
            req.cookies["AWSELB"]
        except IndexError:
            self._log("Login failed: can't get AWSELB cookie", 'INFO')
            return False

        self.cookies = {
            "cwssid": req.cookies["cwssid"],
            "AWSELB": req.cookies["AWSELB"]
        }

        self.storage.set('cwssid', req.cookies["cwssid"])
        self.storage.set('AWSELB', req.cookies["AWSELB"])

        return self.cookies

    def _getAccessToken(self):
        """
        Parse ACCESS_TOKEN from page content
        :return: String - ACCESS_TOKEN or False if failed
        """
        req = self._request("")
        response_data = req.text
        if response_data:
            match = re.search("ACCESS_TOKEN = '([a-z0-9]+)'", response_data)
            if match:
                self.access_token = match.group(1)
                self.storage.set('access_token', self.access_token)
                return self.access_token

        self._log("Request failed: ACCESS_TOKEN not found", 'INFO')
        return False

    def request(self, query_string, post_parameters={}):
        """
        Send request to Chatwork UI (for external usage).
        :param query_string: String - Part of request url string, that will be added to self.url
        :param post_parameters: Dict - Post parameters. Request will be GET, if post_parameters is not specified.
        :return: String - Response from Chatwork (headers not included)
        """

        response = self._request(query_string + "&_t=" + self.access_token, post_parameters)
        return response.text

    def message(self, text, room_id, tries=2):
        """
        Send message with [text] content to [room_id] room
        :param text: String - Message content
        :param room_id: Int - Room id, to which post will be send.
        :param tries: Int - Message post tries before False is returned.
        :return: Bool - True if message post is succeeded or False otherwise.
        """

        # last_chat_id is dummy (better to be real last sended message id, though it is not necessary for post)
        pdata = {
            "text": text,
            "room_id": room_id,
            "last_chat_id": 1157396100,
            "read": 1,
            "edit_id": 0
        }

        post = {
            "pdata": json.dumps(pdata)
        }

        response = self.request("/gateway.php?cmd=send_chat&myid=" + self.login_id + "&_v=1.80a&_av=4&ln=ja", post)
        response_json = json.loads(response)

        if response_json["status"]["success"]:
            return True
        if response_json["status"]["message"] == "NO LOGIN":
            # Cookies expired, try to login again
            if not self._login():
                self._log("Login failed!", 'CRITICAL')
            if not self._getAccessToken():
                self._log("ACCESS_TOKEN not found!", 'CRITICAL')

        tries -= 1
        if tries:
            return self.message(text, room_id, tries)

        return False

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
