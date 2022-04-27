# -*- coding: utf-8 -*-

import ast
import base64
import sys

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions. Currently, testing authentication from GitHub Repo Secrets.
"""

oauth_str = sys.argv[1]

if __name__ == '__main__':
    print('Hello world :)')
    oauth = ast.literal_eval(base64.urlsafe_b64decode(oauth_str).decode('utf-8'))
    print(oauth.keys())
