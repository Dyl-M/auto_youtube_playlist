# -*- coding: utf-8 -*-

import json
import logging
import youtube_req

"""File Information
@file_name: main.py
@author: Dylan "dyl-m" Monfret
Main process (still in test phase).
"""

"LOGGERS"

# Create loggers
history_main = logging.Logger(name='history_main', level=0)
last_exe_main_s = logging.Logger(name='last_exe_main_start', level=0)
last_exe_main_e = logging.Logger(name='last_exe_main_end', level=0)

# Create file handlers
history_main_file = logging.FileHandler(filename='../log/history.log')  # mode='a'
last_exe_main_s_file = logging.FileHandler(filename='../log/last_exe.log', mode='w')  # Last exe. logging start
last_exe_main_e_file = logging.FileHandler(filename='../log/last_exe.log')  # Last exe. logging end

# Create formatter
formatter_main = logging.Formatter(fmt='%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S%z')

# Set file handlers' level
history_main_file.setLevel(logging.DEBUG)
last_exe_main_s_file.setLevel(logging.DEBUG)
last_exe_main_e_file.setLevel(logging.DEBUG)

# Assign file handlers and formatter to loggers
history_main_file.setFormatter(formatter_main)
history_main.addHandler(history_main_file)
last_exe_main_s_file.setFormatter(formatter_main)
last_exe_main_s.addHandler(last_exe_main_s_file)
last_exe_main_e_file.setFormatter(formatter_main)
last_exe_main_e.addHandler(last_exe_main_e_file)

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
last_exe_main_s.info('Process started.')

YOUTUBE_OAUTH = youtube_req.get_authenticated_service()  # Init. YouTube service

# Update live playlist
CURRENT_LIVE = youtube_req.iter_livestreams(MUSIC_CHANNELS_IDS)
youtube_req.update_playlist(YOUTUBE_OAUTH, PLAYLIST_LIVES, CURRENT_LIVE, is_live=True)

# Update mixes playlist
TO_ADD = youtube_req.iter_playlists(YOUTUBE_OAUTH, MUSIC_CHANNELS_UPLOADS)
youtube_req.update_playlist(YOUTUBE_OAUTH, PLAYLIST_MIXES, TO_ADD)

# End
history_main.info('Process ended.')
last_exe_main_e.info('Process ended.')
