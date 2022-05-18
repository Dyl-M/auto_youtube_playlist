# -*- coding: utf-8 -*-

import json
import pandas as pd
import youtube_req

pd.set_option('display.max_columns', None)  # pd.set_option('display.max_rows', None)
pd.set_option('display.width', 250)

"""File Information
@file_name: analytics.py
@author: Dylan "dyl-m" Monfret
Script containing methods to perform analytics on YouTube videos retrieved with youtube_req.py / main.py
"""

# Open and read data files
with open('../data/playlists.json', 'r', encoding='utf8') as playlists_file:
    playlists = json.load(playlists_file)

p_mixes = playlists['mixes']['id']
YOUTUBE_LOCAL = youtube_req.create_service_local(log=False)

"MAIN"

if __name__ == "__main__":
    videos = youtube_req.get_playlist_items(service=YOUTUBE_LOCAL, playlist_id=p_mixes)
    videos_df = pd.DataFrame(videos)
    print(videos_df)
