# -*- coding: utf-8 -*-

import googleapiclient.discovery
import glob
import sys

from google.oauth2.credentials import Credentials

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""


def create_service():
    """"
    :return:
    """
    cred_files = glob.glob("../gha-creds-*.json")
    print(cred_files)
    cred = Credentials.from_authorized_user_file(cred_files[0])  # Retrieve credentials

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
