# -*- coding: utf-8 -*-

import googleapiclient.discovery
import googleapiclient.errors
import json
import random
import requests

from bs4 import BeautifulSoup

"""File Information

@file_name: youtube_req.py
@author: Dylan "dyl-m" Monfret
Script containing methods using YouTube API or doing scrapping / GET-requests on youtube.com.
"""

"GLOBAL"

with open('../tokens/api_key.txt', 'r', encoding='utf8') as api_key_file:
    API_KEY = api_key_file.read()

with open('../data/pocket_tube.json', 'r', encoding='utf8') as music_channel_file:
    POCKET_TUBE = json.load(music_channel_file)

YOUTUBE = googleapiclient.discovery.build("youtube", version="v3", developerKey=API_KEY)

"FUNCTIONS"


def get_channels(service: googleapiclient.discovery, channel_list: list, save: bool = False,
                 save_name: str = 'channels'):
    """Get YouTube channels basic information
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param channel_list: list of YouTube channel ID
    :param save: to save results or not as JSON file
    :param save_name: JSON save name
    :return information: a dictionary with channels names, IDs and uploads playlist IDs.
    """
    information = []

    if len(channel_list) > 50:  # Divide task in chunk of 50 channel ID to request on 50 channel at each iteration
        channels_chunks = [channel_list[i:i + 50] for i in range(0, len(channel_list), 50)]

        for chunk in channels_chunks:
            try:
                request = service.channels().list(part=['snippet', 'contentDetails'], id=",".join(chunk),
                                                  maxResults=50).execute()  # Request channels

                # Extract upload playlists, channel names and their ID.
                information += [{'uploads': an_item['contentDetails']['relatedPlaylists']['uploads'],
                                 'title': an_item['snippet']['title'],
                                 'id': an_item['id']} for an_item in request['items']]

            except googleapiclient.errors.HttpError:
                raise

    else:  # If less than 50 channels concerned, do the single request at once
        try:
            request = service.channels().list(part=['snippet', 'contentDetails'],
                                              id=channel_list,
                                              maxResults=len(channel_list)).execute()  # Request channels

            # Extract upload playlists, channel names and their ID.
            information += [{'uploads': an_item['contentDetails']['relatedPlaylists']['uploads'],
                             'title': an_item['snippet']['title'],
                             'id': an_item['id']} for an_item in request['items']]

        except googleapiclient.errors.HttpError:
            raise

    if save:  # If you choose to save the requests results
        information = sorted(information, key=lambda dic: dic['title'].lower())  # Sort by alphabetical order

        with open(f'../data/{save_name}.json', 'w', encoding='utf-8') as save_file:  # Export as JSON file
            json.dump(information, save_file, indent=2, ensure_ascii=False)

    return information


def get_playlist_items(service: googleapiclient.discovery, playlist_id: str):
    """Get the videos in a YouTube playlist
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :return p_items: playlist items (videos) as a list.
    """
    p_items = []
    next_page_token = None

    try:
        while 1:

            request = service.playlistItems().list(part=['snippet', 'contentDetails', 'status'], playlistId=playlist_id,
                                                   maxResults=50, pageToken=next_page_token).execute()
            p_items += request['items']
            next_page_token = request.get('nextPageToken')

            print(next_page_token)

            if next_page_token is None:
                break

    except googleapiclient.errors.HttpError:
        raise

    return p_items


def find_lives(channel_id: str):
    """Find live streams on YouTube using a channel ID
    :param channel_id: a YouTube channel ID
    :return live_list: list of live stream ID (or empty list if no live at the moment).
    """
    cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(random.randint(100, 999))}  # Cookies settings
    web_page = requests.get(f'https://www.youtube.com/channel/{channel_id}', cookies=cookies)  # Page request
    soup = BeautifulSoup(web_page.text, "html.parser")  # HTML parsing

    # Filtering JS part only, then convert to string
    js_scripts = [script for script in soup.find_all("script") if "sectionListRenderer" in str(script)][0].text
    sections_as_dict = json.loads(js_scripts.replace("var ytInitialData = ", '')[:-1])  # Parse JS as dictionary

    # Extract content from page tabs
    tab = sections_as_dict['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']

    # Extract content from channel page items
    section = tab['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]

    if 'channelFeaturedContentRenderer' in section.keys():  # If at least one live stream is running
        featured = section['channelFeaturedContentRenderer']['items']  # Extract each live stream item
        live_list = [item['videoRenderer']['videoId'] for item in featured]  # Extract video / live stream IDs
        return live_list

    return []  # To return if no live stream at the moment
