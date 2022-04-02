# -*- coding: utf-8 -*-

import json
import youtube_req

"""File Information
@file_name: main.py
@author: Dylan "dyl-m" Monfret
Main process (still in test phase).
"""

"YOUTUBE OAUTH 2.0 SETUP"

YOUTUBE_OAUTH = youtube_req.get_authenticated_service()

"GLOBAL"

with open('../data/music_channels.json', 'r', encoding='utf8') as music_channel_file:
    MUSIC_CHANNELS = json.load(music_channel_file)

with open('../data/playlists.json', 'r', encoding='utf8') as playlists_file:
    PLAYLISTS = json.load(playlists_file)

PLAYLIST_MIXES, PLAYLIST_LIVES = PLAYLISTS['mixes']['id'], PLAYLISTS['lives']['id']
MUSIC_CHANNELS_IDS = [channel['id'] for channel in MUSIC_CHANNELS]
MUSIC_CHANNELS_UPLOADS = [channel['uploads'] for channel in MUSIC_CHANNELS]

"MAIN"  # TODO: implement logging

# Update live playlist
CURRENT_LIVE = youtube_req.iter_livestreams(channel_list=MUSIC_CHANNELS_IDS)
youtube_req.update_playlist(service=YOUTUBE_OAUTH, playlist_id=PLAYLIST_LIVES, videos_to_add=CURRENT_LIVE, is_live=True)

# Update mixes playlist
LAST_DAY = youtube_req.iter_playlists(playlist_list=MUSIC_CHANNELS_UPLOADS, service=YOUTUBE_OAUTH, day_ago=1)
youtube_req.update_playlist(service=YOUTUBE_OAUTH, playlist_id=PLAYLIST_MIXES, videos_to_add=LAST_DAY)
