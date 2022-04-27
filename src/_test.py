# -*- coding: utf-8 -*-

import sys

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions. Currently, testing authentication from GitHub Repo Secrets.
"""

oauth = sys.argv[1]

if __name__ == '__main__':
    print('Hello world :)')
    print(oauth[:100])
