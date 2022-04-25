# -*- coding: utf-8 -*-

import sys

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""

try:
    exe_mode = sys.argv[1]
except IndexError:
    exe_mode = 'local'

if __name__ == '__main__':
    print('Hello world :)')
    print(f'Executing script {sys.argv[0]} in {exe_mode} mode.')
