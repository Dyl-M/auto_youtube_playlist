# -*- coding: utf-8 -*-

import random
import string
import os
import github

try:
    github_repo = os.environ['GITHUB_REPOSITORY']
    PAT = os.environ['PAT']

except KeyError:
    print("Environment variables not found, checking local variable...")

    github_repo = 'Dyl-M/auto_youtube_playlist'

    with open('../tokens/TMP_PAT.txt', 'r', encoding='utf-8') as PAT_FILE:
        PAT = PAT_FILE.readlines()[0]

"""File Information
@file_name: _sandbox.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""


def generate_secrets(n):
    if n <= 0:
        return ""
    else:
        characters = string.ascii_letters + string.digits + string.punctuation
        random_string = ''.join(random.choice(characters) for _ in range(n))
        return random_string


def update_repo_secrets(secret_name: str, new_value: str):
    """Update a GitHub repository Secret value
    :param secret_name: GH repository Secret name
    :param new_value: new value for selected Secret
    """
    gh_object = github.Github(PAT)
    repo = gh_object.get_repo(github_repo)

    try:
        repo.create_secret(secret_name, new_value)
        print(f"Secret {secret_name} updated successfully.")

    except Exception as e:
        print(f"Failed to update secret {secret_name}. Error: {e}")


if __name__ == '__main__':
    new_secrets = generate_secrets(21)
    update_repo_secrets(secret_name='TEST', new_value=new_secrets)
