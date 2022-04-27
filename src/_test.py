# -*- coding: utf-8 -*-

import sys
import base64

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions. Currently, testing authentication from GitHub Repo Secrets.
"""

oauth = sys.argv[1]

if __name__ == '__main__':
    print('Hello world :)')
    print(base64.urlsafe_b64decode(oauth)[:100])
