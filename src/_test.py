# -*- coding: utf-8 -*-


import glob
import json

"""File Information
@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions: currently testing Google Cloud authentication.
"""


def create_service():
    """"Retrieve authentication credentials"""
    cred_file = glob.glob("../gha-creds-*.json")[0]
    with open(cred_file, 'r', encoding='utf8') as cred_f:
        cred_d = json.load(cred_f)
    return cred_d.keys()


if __name__ == '__main__':
    print(create_service())
