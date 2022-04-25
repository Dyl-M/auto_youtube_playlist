# -*- coding: utf-8 -*-

import googleapiclient.discovery
import glob

from google.auth import external_account

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions: currently testing Google Cloud authentication.
"""


def create_service():
    """Retrieve authentication credentials"""
    service_account_file = glob.glob("../gha-creds-*.json")[0]
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    credentials = external_account.Credentials(service_account_file, scopes=scopes)
    service = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
    return service


if __name__ == '__main__':
    print(create_service())
