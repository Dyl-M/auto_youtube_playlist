# -*- coding: utf-8 -*-

import google.auth
import googleapiclient.discovery
import glob

from google.auth import impersonated_credentials
from google.oauth2 import service_account

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions: currently testing Google Cloud authentication.
"""


def create_service():
    """Retrieve authentication credentials"""
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    credentials, _ = google.auth.default(scopes=scopes)
    service = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
    return service


if __name__ == '__main__':
    print(create_service())
