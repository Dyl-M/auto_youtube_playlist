# -*- coding: utf-8 -*-

import json
import logging
import youtube_req

"""File Information
@file_name: main.py
@author: Dylan "dyl-m" Monfret
Main process (still in test phase).
"""

"YOUTUBE OAUTH 2.0 SETUP"

YOUTUBE_OAUTH = youtube_req.get_authenticated_service()

"LOGGERS"

# Create loggers
history_main = logging.Logger(name='history_main', level=0)
last_exe_main = logging.Logger(name='last_exe_main', level=0)

# Create file handlers
history_main_file = logging.FileHandler(filename='../log/history.log')  # mode='a'
last_exe_main_file = logging.FileHandler(filename='../log/last_exe.log', mode='w')

# Create formatter
formatter_main = logging.Formatter(fmt='%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S%z')

# Set file handlers' level
history_main_file.setLevel(logging.DEBUG)
last_exe_main_file.setLevel(logging.DEBUG)

# Assign file handlers and formatter to loggers
history_main_file.setFormatter(formatter_main)
history_main.addHandler(history_main_file)
last_exe_main_file.setFormatter(formatter_main)
last_exe_main.addHandler(last_exe_main_file)

"GLOBAL"

with open('../data/music_channels.json', 'r', encoding='utf8') as music_channel_file:
    MUSIC_CHANNELS = json.load(music_channel_file)

with open('../data/playlists.json', 'r', encoding='utf8') as playlists_file:
    PLAYLISTS = json.load(playlists_file)

PLAYLIST_MIXES, PLAYLIST_LIVES = PLAYLISTS['mixes']['id'], PLAYLISTS['lives']['id']
MUSIC_CHANNELS_IDS = [channel['id'] for channel in MUSIC_CHANNELS]
MUSIC_CHANNELS_UPLOADS = [channel['uploads'] for channel in MUSIC_CHANNELS]

"MAIN"

# Start
history_main.info('Process started.')
last_exe_main.info('Process started.')

# Update live playlist
CURRENT_LIVE = youtube_req.iter_livestreams(MUSIC_CHANNELS_IDS)
youtube_req.update_playlist(YOUTUBE_OAUTH, PLAYLIST_LIVES, CURRENT_LIVE, is_live=True)

# Update mixes playlist
TO_ADD = youtube_req.iter_playlists(YOUTUBE_OAUTH, MUSIC_CHANNELS_UPLOADS, day_ago=1)
youtube_req.update_playlist(YOUTUBE_OAUTH, PLAYLIST_MIXES, TO_ADD)

# End
history_main.info('Process ended.')
last_exe_main.info('Process ended.')
