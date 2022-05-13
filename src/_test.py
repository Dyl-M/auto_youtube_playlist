# -*- coding: utf-8 -*-

import ast
import base64
import googleapiclient.discovery
import googleapiclient.errors
import json
import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions. Testing authentication.
"""


def create_service_test():
    """Retrieve authentication credentials from dedicated repository secrets
    :return service: a Google API service object build with 'googleapiclient.discovery.build'.
    """

    def import_env_var(var_name: str):
        """Import variable environment and perform base64 decoding
        :param var_name: environment variable name
        :return value: decoded value
        """
        v_b64 = os.environ.get(var_name)  # Get environment variable
        v_str = base64.urlsafe_b64decode(v_b64).decode(encoding='utf8')  # Decode
        value = ast.literal_eval(v_str)  # Eval
        return value

    creds_dict = import_env_var(var_name='CREDS_B64')  # Import pre-registered credentials
    creds = Credentials.from_authorized_user_info(creds_dict)  # Conversion to suitable object
    instance_fail_message = 'Failed to create service instance for YouTube'

    if not creds.valid:  # Cover outdated credentials
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh token

            # Get refreshed token as JSON-like string
            creds_str = json.dumps(ast.literal_eval(creds.to_json())).encode('utf-8')

            creds_b64 = str(base64.urlsafe_b64encode(creds_str))[2:-1]  # Encode token
            os.environ["CREDS_B64"] = creds_b64  # Update environment variable value
            print('API credentials refreshed.')

        else:
            print('ERROR: Unable to refresh credentials. Check Google API OAUTH parameter.')
            sys.exit()

    try:
        service = googleapiclient.discovery.build('youtube', 'v3', credentials=creds)  # Build service.
        print('YouTube service created successfully.')
        return service

    except Exception as error:  # skipcq: PYL-W0703 - No known errors at the moment.
        print(f'({error}) {instance_fail_message}')
        sys.exit()


if __name__ == '__main__':
    SERVICE = create_service_test()
