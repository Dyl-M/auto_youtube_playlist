# -*- coding: utf-8 -*-

import googleapiclient.discovery
import glob
import json
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""


def create_service():
    """"
    :return:
    """
    cred_file = glob.glob("../gha-creds-*.json")[0]

    with open(cred_file, 'r', encoding='utf8') as cred_f:
        cred_d = json.load(cred_f)

    print(cred_d.keys())

    cred = Credentials.from_authorized_user_file(cred_file)  # Retrieve credentials

    if not cred or not cred.valid:  # Cover outdated credentials
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())

    try:
        service = googleapiclient.discovery.build('youtube', 'v3', credentials=cred)
        print('YouTube Service created successfully.')
        return service

    except Exception as error:  # skipcq: PYL-W0703 - No known errors at the moment.
        print(error)
        print('Failed to create service instance for YouTube')
        sys.exit()


if __name__ == '__main__':
    YOUTUBE = create_service()
