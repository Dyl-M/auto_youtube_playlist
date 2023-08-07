# -*- coding: utf-8 -*-

import github
import json
import logging
import os
import re
import requests
import sys

import youtube_req

"""File Information
@file_name: main.py
@author: Dylan "dyl-m" Monfret
Main process.
"""

"ENVIRONMENT"

try:
    github_repo = os.environ['GITHUB_REPOSITORY']
    PAT = os.environ['PAT']

except KeyError:
    github_repo = 'Dyl-M/auto_youtube_playlist'

    with open('../tokens/TMP_PAT.txt', 'r', encoding='utf-8') as PAT_FILE:
        PAT = PAT_FILE.readlines()[0]

"SYSTEM"

try:
    exe_mode = sys.argv[1]
except IndexError:
    exe_mode = 'local'

"FUNCTIONS"


def copy_last_exe_log():
    """Copy last execution logging from main history file."""
    with open('../log/history.log', 'r', encoding='utf8') as history_file:
        history = history_file.read()

    last_exe = re.findall(r".*?Process started\.", history)[-1]
    last_exe_idx = history.rfind(last_exe)
    last_exe_log = history[last_exe_idx:]

    with open('../log/last_exe.log', 'w', encoding='utf8') as last_exe_file:
        last_exe_file.write(last_exe_log)


def update_repo_secrets(secret_name: str, new_value: str, logger: logging.Logger = None):
    """Update a GitHub repository Secret value
    :param secret_name: GH repository Secret name
    :param new_value: new value for selected Secret
    :param logger: object for logging
    """
    repo = github.Github(PAT).get_repo(github_repo)
    try:
        repo.create_secret(secret_name, new_value)
        if logger:
            logger.info(f"Repository Secret '{secret_name}' updated successfully.")
        else:
            print(f"Repository Secret '{secret_name}' updated successfully.")

    except Exception as error:  # skipcq: PYL-W0703 - No error found so far
        if logger:
            logger.error(f"Failed to update Repository Secret '{secret_name}' : {error}")
        else:
            print(f"Failed to update secret {secret_name}. Error: {error}")
        sys.exit()


if __name__ == '__main__':
    # Create loggers
    history_main = logging.Logger(name='history_main', level=0)

    # Create file handlers
    history_main_file = logging.FileHandler(filename='../log/history.log')  # mode='a'

    # Create formatter
    formatter_main = logging.Formatter(fmt='%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S%z')

    # Set file handlers' level
    history_main_file.setLevel(logging.DEBUG)

    # Assign file handlers and formatter to loggers
    history_main_file.setFormatter(formatter_main)
    history_main.addHandler(history_main_file)

    # Open and read data files
    with open('../data/pocket_tube.json', 'r', encoding='utf8') as pt_file:
        music_channels = json.load(pt_file)["MUSIQUE"]

    with open('../data/playlists.json', 'r', encoding='utf8') as playlists_file:
        playlists = json.load(playlists_file)

    playlists_mixes, playlists_lives = playlists['mixes']['id'], playlists['lives']['id']

    # Start
    history_main.info('Process started.')

    if exe_mode == 'local':  # YouTube service creation
        YOUTUBE_OAUTH, CREDS_B64 = youtube_req.create_service_local(), None  # YouTube service in local mode
        PROG_BAR = True  # Display progress bar

    else:
        # YouTube service with GitHub workflow + Credentials
        YOUTUBE_OAUTH, CREDS_B64 = youtube_req.create_service_workflow()
        PROG_BAR = False  # Do not display progress bar

    try:  # Try to update & sort livestreams playlist
        current_live = youtube_req.iter_livestreams(music_channels, prog_bar=PROG_BAR)
        youtube_req.update_playlist(YOUTUBE_OAUTH, playlists_lives, current_live, is_live=True, prog_bar=PROG_BAR)
        youtube_req.sort_livestreams(YOUTUBE_OAUTH, playlists_lives, prog_bar=PROG_BAR)

    except requests.exceptions.ReadTimeout as timeout_error:
        history_main.warning('TIMEOUT ERROR: Livestreams playlist update cancelled.')

    # Update mixes playlist
    to_add = youtube_req.iter_channels(YOUTUBE_OAUTH, music_channels, prog_bar=PROG_BAR)
    youtube_req.update_playlist(YOUTUBE_OAUTH, playlists_mixes, to_add, prog_bar=PROG_BAR)

    if exe_mode == 'local':  # Credentials in base64 update - Local option
        youtube_req.encode_key(json_path='../tokens/credentials.json')
        youtube_req.encode_key(json_path='../tokens/oauth.json')

    else:  # Credentials in base64 update - Remote option
        update_repo_secrets(secret_name='CREDS_B64', new_value=CREDS_B64, logger=history_main)

    history_main.info('Process ended.')  # End
    copy_last_exe_log()  # Copy what happened during process execution to the associated file.
