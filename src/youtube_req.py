# -*- coding: utf-8 -*-

import ast
import bs4
import datetime as dt
import googleapiclient.discovery
import googleapiclient.errors
import isodate
import itertools
import json
import os
import pandas as pd
import random
import requests
import sys
import tqdm
import tzlocal

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

"""File Information
@file_name: youtube_req.py
@author: Dylan "dyl-m" Monfret
Script containing methods using YouTube API or doing scrapping / GET-requests on youtube.com.
"""

"OPTIONS"

pd.set_option('display.max_columns', None)  # pd.set_option('display.max_rows', None)
pd.set_option('display.width', 250)

"GLOBAL"

NOW = dt.datetime.now(tz=tzlocal.get_localzone())

"FUNCTIONS"


def get_authenticated_service():
    """Retrieve authentification credentials at specified path or create new ones, mostly inspired by this source
    code: https://learndataanalysis.org/google-py-file-source-code/
    :return: a Google API service object build with 'googleapiclient.discovery.build'.
    """
    oauth_file = '../tokens/oauth.json'  # OAUTH 2.0 ID path
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    instance_fail_message = 'Failed to create service instance for YouTube'
    cred = None

    if os.path.exists('../tokens/credentials.json'):
        cred = Credentials.from_authorized_user_file('../tokens/credentials.json')  # Retrieve credentials

    if not cred or not cred.valid:  # Cover outdated credentials
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(oauth_file, scopes)  # Create a Flow from 'oauth_file'
            cred = flow.run_local_server()  # Run authentification process

        with open('../tokens/credentials.json', 'w') as cred_file:  # Save credentials as a JSON file
            json.dump(ast.literal_eval(cred.to_json()), cred_file, ensure_ascii=False, indent=4)

    try:
        return googleapiclient.discovery.build('youtube', 'v3', credentials=cred)  # Return a functional service

    except Exception as e:  # skipcq: PYL-W0703 - No known errors at the moment.
        print(f'{e} - {instance_fail_message}')  # TODO: Define what to do in this case (logging).
        sys.exit()


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

    # Split task in chunks of size 50 to request on a maximum of 50 channels at each iteration.
    channels_chunks = [channel_list[i:i + min(50, len(channel_list))] for i in range(0, len(channel_list), 50)]

    for chunk in channels_chunks:
        try:
            request = service.channels().list(part=['snippet', 'contentDetails'], id=",".join(chunk),
                                              maxResults=50).execute()  # Request channels

            # Extract upload playlists, channel names and their ID.
            information += [{'uploads': an_item['contentDetails']['relatedPlaylists']['uploads'],
                             'title': an_item['snippet']['title'],
                             'id': an_item['id']} for an_item in request['items']]

        except googleapiclient.errors.HttpError:
            print('googleapiclient.errors.HttpError')
            sys.exit()

    information = sorted(information, key=lambda dic: dic['title'].lower())  # Sort by channel name alphabetical order

    if save:  # If you choose to save the requests results
        with open(f'../data/{save_name}.json', 'w', encoding='utf-8') as save_file:  # Export as JSON file
            json.dump(information, save_file, indent=2, ensure_ascii=False)

    return information


def get_playlist_items(service: googleapiclient.discovery, playlist_id: str, day_ago: int = None,
                       ref_date: dt.datetime = NOW):
    """Get the videos in a YouTube playlist
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param day_ago: day difference with a reference date, delimits items' collection field
    :param ref_date: reference date (NOW by default)
    :return p_items: playlist items (videos) as a list.
    """
    p_items = []
    next_page_token = None
    date_format = '%Y-%m-%dT%H:%M:%S%z'

    while 1:
        try:
            request = service.playlistItems().list(part=['snippet', 'contentDetails', 'status'],
                                                   playlistId=playlist_id,
                                                   maxResults=50,
                                                   pageToken=next_page_token).execute()  # Request playlist's items

            p_items += [{'video_id': item['contentDetails']['videoId'],
                         'release_date': dt.datetime.strptime(item['contentDetails']['videoPublishedAt'], date_format),
                         'channel_id': item['snippet']['videoOwnerChannelId'],
                         'channel_name': item['snippet']['videoOwnerChannelTitle'],
                         'item_id': item['id'],
                         'status': item['status']['privacyStatus']} for item in request['items']]  # Keep necessary data

            if day_ago is not None:  # In case we want to keep videos published x days ago from your ref_date
                # Days subtraction
                date_delta = ref_date - dt.timedelta(days=day_ago)

                # Filtering
                p_items = [item for item in p_items if ref_date > item['release_date'] > date_delta]

                if len(p_items) <= 50:  # No need for more requests (the playlist must be ordered chronologically!)
                    break

            next_page_token = request.get('nextPageToken')

            if next_page_token is None:
                break

        except googleapiclient.errors.HttpError as http_error:
            error_reason = http_error.error_details[0]['reason']

            if error_reason == 'playlistNotFound':
                break  # TODO: Define what to do if there is no public video (logging).

            print(f"Unknown error\n{http_error}")  # TODO: Define what to do in this case (logging).
            sys.exit()

    return p_items


def get_videos(service: googleapiclient.discovery, videos_list: list):
    """Get information from YouTube videos
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param videos_list: list of YouTube video IDs
    :return: request results.
    """
    return service.videos().list(part=['snippet', 'contentDetails'], id=",".join(videos_list), maxResults=50).execute()


def find_livestreams(channel_id: str):
    """Find livestreams on YouTube using a channel ID
    :param channel_id: a YouTube channel ID
    :return live_list: list of livestream ID (or empty list if no livestream at the moment).
    """
    cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(random.randint(100, 999))}  # Cookies settings
    web_page = requests.get(f'https://www.youtube.com/channel/{channel_id}', cookies=cookies)  # Page request
    soup = bs4.BeautifulSoup(web_page.text, "html.parser")  # HTML parsing

    # Filtering JS part only, then convert to string
    js_scripts = [script for script in soup.find_all("script") if "sectionListRenderer" in str(script)][0].text
    sections_as_dict = json.loads(js_scripts.replace("var ytInitialData = ", '')[:-1])  # Parse JS as dictionary

    # Extract content from page tabs
    tab = sections_as_dict['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']

    # Extract content from channel page items
    section = tab['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]

    if 'channelFeaturedContentRenderer' in section.keys():  # If at least one livestream is running
        # Extract each livestream item
        featured = section['channelFeaturedContentRenderer']['items']

        # Extract livestream IDs channel_id
        livestream_ids = [{'channel_id': channel_id, 'video_id': item['videoRenderer']['videoId']} for item in featured]
        return livestream_ids

    return []  # To return if no livestream at the moment


def check_if_live(service: googleapiclient.discovery, videos_list: list):
    """Get broadcast status with YouTube video IDs
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param videos_list: list of YouTube video IDs
    :return items: playlist items (videos) as a list.
    """
    items = []

    # Split task in chunks of size 50 to request on a maximum of 50 videos at each iteration.
    videos_chunks = [videos_list[i:i + min(50, len(videos_list))] for i in range(0, len(videos_list), 50)]

    for chunk in videos_chunks:
        try:
            request = get_videos(service=service, videos_list=chunk)

            # Keep necessary data
            items += [{'video_id': item['id'],
                       'live_status': item['snippet']['liveBroadcastContent']} for item in request['items']]

        except googleapiclient.errors.HttpError:
            print('googleapiclient.errors.HttpError')
            sys.exit()

    return items


def get_durations(service: googleapiclient.discovery, videos_list: list):
    """Get duration of YouTube video with their ID
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param videos_list: list of YouTube video IDs
    :return items: playlist items (videos) as a list.
    """
    items = []

    # Split task in chunks of size 50 to request on a maximum of 50 videos at each iteration.
    videos_ids = [video['video_id'] for video in videos_list]
    videos_chunks = [videos_ids[i:i + min(50, len(videos_ids))] for i in range(0, len(videos_ids), 50)]

    for chunk in videos_chunks:
        try:
            request = get_videos(service=service, videos_list=chunk)

            # Keep necessary data
            items += [{'video_id': item['id'],
                       'duration': isodate.parse_duration(item['contentDetails']['duration']).seconds / 60,
                       'live_status': item['snippet']['liveBroadcastContent']} for item in request['items']]

        except googleapiclient.errors.HttpError:
            print('googleapiclient.errors.HttpError')
            sys.exit()

    return items


def iter_livestreams(channel_list: list):
    """Apply 'find_livestreams' for a collection of YouTube channel
    :param channel_list: list of YouTube channel IDs
    :return: IDs of current live based on channels collection.
    """
    lives_it = [find_livestreams(chan_id) for chan_id in tqdm.tqdm(channel_list, desc='Looking for livestreams')]
    return list(itertools.chain.from_iterable(lives_it))


def iter_playlists(service: googleapiclient.discovery, playlists: list, day_ago: int = None,
                   ref_date: dt.datetime = NOW):
    """Apply 'get_playlist_items' for a collection of YouTube playlists
    :param playlists: list of YouTube channel IDs
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param day_ago: day difference with a reference date, delimits items' collection field
    :param ref_date: reference date (NOW by default)
    :return: videos retrieved in playlists.
    """
    item_it = [get_playlist_items(service=service, playlist_id=playlist_id, day_ago=day_ago, ref_date=ref_date)
               for playlist_id in tqdm.tqdm(playlists, desc='Looking for videos to add')]
    return list(itertools.chain.from_iterable(item_it))


def update_playlist(service: googleapiclient.discovery, playlist_id: str, videos_to_add: list, is_live: bool = False,
                    min_duration: int = 10, del_day_ago: int = 7, ref_date: dt.datetime = NOW):
    """Update a YouTube playlist with temporal criteria
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param videos_to_add: list of YouTube video IDs to potentially add to a specified playlist
    :param is_live: to update a list containing specifically livestreams only (or not)
    :param del_day_ago: day difference with NOW, to keep in playlist video published in the last 'del_day_ago' days
    :param ref_date: reference date (NOW by default)
    :param min_duration: minimal video duration filter.
    """
    # Pass playlist as pandas Dataframes (for easier filtering)
    already_in = pd.DataFrame(get_playlist_items(service=service, playlist_id=playlist_id))  # Get videos already in
    to_add_df = pd.DataFrame(videos_to_add)

    if not already_in.empty:  # If there is at least one video in the playlist
        to_add_df = to_add_df.loc[~to_add_df.video_id.isin(already_in.video_id)]  # Check if new videos are already in

        if is_live:  # If the update is done on a YouTube livestreams playlist
            # Retrieve live status
            live_status = pd.DataFrame(check_if_live(service=service, videos_list=already_in.video_id))
            already_in = already_in.merge(live_status)

            # Do not keep private videos. Do not keep upcoming and finished livestreams.
            to_delete_df = already_in.loc[(already_in.status == 'private') | (already_in.live_status != 'live')]

            if not to_add_df.empty:  # If there are videos to add
                add_to_playlist(service=service, playlist_id=playlist_id, videos_list=to_add_df.video_id)

            if not to_delete_df.empty:  # If there are videos to delete
                del_from_playlist(service=service, playlist_id=playlist_id, items_list=to_delete_df.item_id)

        else:
            date_delta = ref_date - dt.timedelta(days=del_day_ago)  # Days subtraction
            delete_cond = (already_in.status == 'private') | (already_in.release_date < date_delta)  # Delete condition
            to_delete_df = already_in.loc[delete_cond]  # To keep public and newest videos.

            # Get durations of videos to add
            durations = pd.DataFrame(get_durations(service=service, videos_list=videos_to_add))
            to_add_df = to_add_df.merge(durations)

            # Keep videos with duration above `min_duration` minutes and don't keep "Premiere" type videos
            to_add_df = to_add_df.loc[(to_add_df.duration >= min_duration) & (to_add_df.live_status != 'upcoming')]

            if not to_add_df.empty:  # If there are videos to add
                add_to_playlist(service=service, playlist_id=playlist_id, videos_list=to_add_df.video_id)

            if not to_delete_df.empty:  # If there are videos to delete
                del_from_playlist(service=service, playlist_id=playlist_id, items_list=to_delete_df.item_id)

    else:  # If there is no video in the playlist
        if is_live and to_add_df.empty:  # If there are livestreams to add
            add_to_playlist(service=service, playlist_id=playlist_id, videos_list=to_add_df.video_id)

        else:  # For regular videos
            # Get durations of videos to add
            durations = pd.DataFrame(get_durations(service=service, videos_list=videos_to_add))
            to_add_df = to_add_df.merge(durations)

            # Keep videos with duration above `min_duration` minutes and don't keep "Premiere" type videos
            to_add_df = to_add_df.loc[(to_add_df.duration >= min_duration) & (to_add_df.live_status != 'upcoming')]

            if not to_add_df.empty:  # If there are videos to add
                add_to_playlist(service=service, playlist_id=playlist_id, videos_list=to_add_df.video_id)


def add_to_playlist(service: googleapiclient.discovery, playlist_id: str, videos_list: list):
    """Add a list of video to a YouTube playlist
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param videos_list: list of YouTube video IDs.
    """
    for video_id in tqdm.tqdm(videos_list, desc=f'Adding videos to the playlist ({playlist_id})'):
        r_body = {'snippet': {'playlistId': playlist_id, 'resourceId': {'kind': 'youtube#video', 'videoId': video_id}}}
        request = service.playlistItems().insert(part="snippet", body=r_body)

        try:
            request.execute()

        except googleapiclient.errors.HttpError:
            print('googleapiclient.errors.HttpError')
            sys.exit()


def del_from_playlist(service: googleapiclient.discovery, playlist_id: str, items_list: list):
    """Delete a list of video from a YouTube playlist
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param items_list: list of YouTube playlist items.
    """
    for item_id in tqdm.tqdm(items_list, desc=f'Deleting videos from the playlist ({playlist_id})'):
        request = service.playlistItems().delete(id=item_id)

        try:
            request.execute()

        except googleapiclient.errors.HttpError:
            print('googleapiclient.errors.HttpError')
            sys.exit()
