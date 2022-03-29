# -*- coding: utf-8 -*-

import googleapiclient.discovery
import youtube_req

"""File Information

@file_name: _test.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""

"GLOBAL"

with open('../tokens/api_key.txt', 'r', encoding='utf8') as api_key_file:
    API_KEY = api_key_file.read()

YOUTUBE = googleapiclient.discovery.build("youtube", version="v3", developerKey=API_KEY)

MUSIC_LIVES = "https://www.youtube.com/playlist?list=PLOMUdQFdS-XNaPVSol9qCUJvQvN5hO4hJ"
MUSIC_MIXES = "https://www.youtube.com/playlist?list=PLOMUdQFdS-XMJ4NFHJlSALYAt4l-LPgS1"  # Unlisted

"MAIN"

url1 = "UCSJ4gkVC6NrvII8umztf0Ow"  # Lofi Girl (lives: 5qap5aO4i9A, DWcJFNfaw9c)
url2 = "UCalCDSmZAYD73tqVZ4l8yJg"  # A State Of Trance (live: 5lMmnfVylEE)
url3 = "UCmKm7HJdOfkWLyml-fzKlVg"  # Afrojack
url4 = "UC8y7Xa0E1Lo6PnVsu2KJbOA"  # Don Diablo

chan1 = youtube_req.find_lives(url1)
chan2 = youtube_req.find_lives(url2)
chan3 = youtube_req.find_lives(url3)
chan4 = youtube_req.find_lives(url4)

print(chan1)
print(chan2)
print(chan3)
print(chan4)
