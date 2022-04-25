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
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    with open(service_account_file, 'r', encoding='utf8') as json_file:
        cred_dict = json.load(json_file)

    print(cred_dict.keys())
    print(cred_dict)

    credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
    service = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
    return service


if __name__ == '__main__':
    print(create_service())
