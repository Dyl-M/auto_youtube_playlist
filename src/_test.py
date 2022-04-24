# -*- coding: utf-8 -*-

import googleapiclient.discovery
import glob

from google.oauth2 import service_account

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions: currently testing Google Cloud authentication.
"""


def create_service():
    """Retrieve authentication credentials"""
    import json
    service_account_file = glob.glob("../gha-creds-*.json")[0]

    with open(service_account_file, 'r', encoding='utf8') as service_account_json:
        json_file = json.load(service_account_json)

    print(json_file.keys())

    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
    return service


if __name__ == '__main__':
    print(create_service())
