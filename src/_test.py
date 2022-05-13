# -*- coding: utf-8 -*-

import os

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions. Testing authentication.
"""


def create_service_test():
    """Retrieve authentication credentials from dedicated repository secrets
    :return service: a Google API service object build with 'googleapiclient.discovery.build'.
    """
    oauth_b64 = os.environ.get('OAUTH_B64')
    print(oauth_b64[:10])


if __name__ == '__main__':
    create_service_test()
