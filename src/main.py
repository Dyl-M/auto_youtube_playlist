# -*- coding: utf-8 -*-

import json
import logging
import re
import sys
import youtube_req

"""File Information
@file_name: main.py
@author: Dylan "dyl-m" Monfret
Main process (still in test phase).
"""

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
    with open('../data/music_channels.json', 'r', encoding='utf8') as music_channel_file:
        music_channels = json.load(music_channel_file)

    with open('../data/playlists.json', 'r', encoding='utf8') as playlists_file:
        playlists = json.load(playlists_file)

    playlists_mixes, playlists_lives = playlists['mixes']['id'], playlists['lives']['id']
    music_channels_ids = [channel['id'] for channel in music_channels]
    music_channels_uploads = [channel['uploads'] for channel in music_channels]

    # Start
    history_main.info('Process started.')

    if exe_mode == 'local':  # YouTube service creation
        YOUTUBE_OAUTH = youtube_req.create_service_local()  # YouTube service in local mode
        PROG_BAR = True  # Display progress bar

    else:
        YOUTUBE_OAUTH = youtube_req.create_service_workflow()  # YouTube service with GitHub workflow
        PROG_BAR = False  # Do not display progress bar

    # Update live playlist
    current_live = youtube_req.iter_livestreams(music_channels_ids, prog_bar=PROG_BAR)
    youtube_req.update_playlist(YOUTUBE_OAUTH, playlists_lives, current_live, is_live=True, prog_bar=PROG_BAR)

    # Update mixes playlist
    to_add = youtube_req.iter_playlists(YOUTUBE_OAUTH, music_channels_uploads, prog_bar=PROG_BAR)
    youtube_req.update_playlist(YOUTUBE_OAUTH, playlists_mixes, to_add, prog_bar=PROG_BAR)

    # End
    history_main.info('Process ended.')
    copy_last_exe_log()  # Copy what happened during process execution to the associated file.

    if exe_mode == 'local':  # Optional end: credentials in base64 update
        youtube_req.encode_key(json_path='../tokens/credentials.json')
        youtube_req.encode_key(json_path='../tokens/oauth.json')
