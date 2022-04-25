# -*- coding: utf-8 -*-

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
    service_account_file = glob.glob("../gha-creds-*.json")[0]
    auth_scopes = ['https://www.googleapis.com/auth/devstorage.read_only']
    # api_scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']
    serv_acc = 'github-x-google@youtube-automatic-playlists.iam.gserviceaccount.com'

    source_credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=auth_scopes)

    credentials = impersonated_credentials.Credentials(source_credentials=source_credentials,
                                                       target_principal=serv_acc,
                                                       target_scopes=auth_scopes)

    service = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
    return service


if __name__ == '__main__':
    print(create_service())
