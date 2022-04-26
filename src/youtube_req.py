# -*- coding: utf-8 -*-

import ast
import bs4
import datetime as dt
import google.auth
import googleapiclient.discovery
import googleapiclient.errors
import isodate
import itertools
import json
import logging
import os
import pandas as pd
import random
import re
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


def last_exe_date():
    """Extract last execution datetime from a log file (supposing first line is containing the right datetime).
    :return date: last execution date.
    """
    with open('../log/last_exe.log', 'r', encoding='utf8') as log_file:
        first_log = log_file.readlines()[0]  # Get first log

    d_str = re.search(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})\+(\d{4})', first_log).group()  # Extract date
    date = dt.datetime.strptime(d_str, '%Y-%m-%d %H:%M:%S%z')  # Parse to datetime object
    return date


with open('../data/ignore.json') as ignore_file:
    TO_IGNORE = json.load(ignore_file)

NOW = dt.datetime.now(tz=tzlocal.get_localzone())
LAST_EXE = last_exe_date()

"LOGGERS"

# Create loggers
history = logging.Logger(name='history', level=0)
last_exe = logging.Logger(name='last_exe', level=0)

# Create file handlers
history_file = logging.FileHandler(filename='../log/history.log')  # mode='a'
last_exe_file = logging.FileHandler(filename='../log/last_exe.log')

# Create formatter
formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S%z')

# Set file handlers' level
history_file.setLevel(logging.DEBUG)
last_exe_file.setLevel(logging.DEBUG)

# Assign file handlers and formatter to loggers
history_file.setFormatter(formatter)
history.addHandler(history_file)
last_exe_file.setFormatter(formatter)
last_exe.addHandler(last_exe_file)

"FUNCTIONS"


def create_service_local(log: bool = True):
    """Retrieve authentication credentials at specified path or create new ones, mostly inspired by this source
    code: https://learndataanalysis.org/google-py-file-source-code/
    :param log: to apply logging or not
    :return service: a Google API service object build with 'googleapiclient.discovery.build'.
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
            cred = flow.run_local_server()  # Run authentication process

        with open('../tokens/credentials.json', 'w') as cred_file:  # Save credentials as a JSON file
            json.dump(ast.literal_eval(cred.to_json()), cred_file, ensure_ascii=False, indent=4)

    try:
        service = googleapiclient.discovery.build('youtube', 'v3', credentials=cred)
        if log:
            history.info('YouTube service created successfully.')
            last_exe.info('YouTube Service created successfully.')

        return service

    except Exception as error:  # skipcq: PYL-W0703 - No known errors at the moment.
        if log:
            history.critical(f'({error}) {instance_fail_message}')
            last_exe.critical(f'({error}) {instance_fail_message}')

        sys.exit()


def create_service_workflow():
    """Retrieve authentication credentials"""
    instance_fail_message = 'Failed to create service instance for YouTube'

    try:
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        credentials, _ = google.auth.default(scopes=scopes)
        service = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
        history.info('YouTube service created successfully.')
        last_exe.info('YouTube Service created successfully.')
        return service

    except Exception as error:  # skipcq: PYL-W0703 - No known errors at the moment.
        history.critical(f'({error}) {instance_fail_message}')
        last_exe.critical(f'({error}) {instance_fail_message}')
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

        except googleapiclient.errors.HttpError as http_error:
            history.error(http_error.error_details)
            last_exe.error(http_error.error_details)
            sys.exit()

    information = sorted(information, key=lambda dic: dic['title'].lower())  # Sort by channel name alphabetical order

    if save:  # If you choose to save the requests results
        with open(f'../data/{save_name}.json', 'w', encoding='utf-8') as save_file:  # Export as JSON file
            json.dump(information, save_file, indent=2, ensure_ascii=False)

    return information


def get_playlist_items(service: googleapiclient.discovery, playlist_id: str, day_ago: int = None,
                       with_last_exe: bool = False, latest_d: dt.datetime = NOW):
    """Get the videos in a YouTube playlist
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param day_ago: day difference with a reference date, delimits items' collection field
    :param latest_d: latest reference date
    :param with_last_exe: to use last execution date extracted from log or not
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

            if with_last_exe:  # In case we want to keep videos published between last exe date and your latest_d
                oldest_d = LAST_EXE.replace(minute=0, second=0, microsecond=0)  # Round hour to XX:00:00.0
                latest_d = latest_d.replace(minute=0, second=0, microsecond=0)  # Round hour to XX:00:00.0
                p_items = [item for item in p_items if latest_d > item['release_date'] > oldest_d]  # Filtering

                if len(p_items) <= 50:  # No need for more requests (the playlist must be ordered chronologically!)
                    break

            elif day_ago is not None:  # In case we want to keep videos published x days ago from your latest_d
                latest_d = latest_d.replace(minute=0, second=0, microsecond=0)  # Round hour to XX:00:00.0
                date_delta = latest_d - dt.timedelta(days=day_ago)  # Days subtraction
                p_items = [item for item in p_items if latest_d > item['release_date'] > date_delta]  # Filtering

                if len(p_items) <= 50:  # No need for more requests (the playlist must be ordered chronologically!)
                    break

            next_page_token = request.get('nextPageToken')

            if next_page_token is None:
                break

        except googleapiclient.errors.HttpError as http_error:
            error_reason = http_error.error_details[0]['reason']

            if error_reason == 'playlistNotFound':
                if playlist_id not in TO_IGNORE:
                    history.warning(f'Playlist not found: {playlist_id}')
                    last_exe.warning(f'Playlist not found: {playlist_id}')
                break

            history.error(f'[{playlist_id}] Unknown error: {error_reason}')
            last_exe.error(f'[{playlist_id}] Unknown error: {error_reason}')
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
    try:
        cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(random.randint(100, 999))}  # Cookies settings
        url = f'https://www.youtube.com/channel/{channel_id}'
        web_page = requests.get(url, cookies=cookies, timeout=(5, 5))  # Page request
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
            livestream_ids = [{'channel_id': channel_id, 'video_id': item['videoRenderer']['videoId']} for item in
                              featured]
            return livestream_ids

    except requests.exceptions.ConnectionError:
        history.warning(f'ConnectionError with this channel: {channel_id}')
        last_exe.warning(f'ConnectionError with this channel: {channel_id}')

    return []  # Return if no livestream at the moment or in case of ConnectionError


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

        except googleapiclient.errors.HttpError as http_error:
            history.error(http_error.error_details)
            last_exe.error(http_error.error_details)
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

        except googleapiclient.errors.HttpError as http_error:
            history.error(http_error.error_details)
            last_exe.error(http_error.error_details)
            sys.exit()

    return items


def iter_livestreams(channel_list: list, prog_bar: bool = True):
    """Apply 'find_livestreams' for a collection of YouTube channel
    :param channel_list: list of YouTube channel IDs
    :param prog_bar: to use tqdm progress bar or not
    :return: IDs of current live based on channels collection.
    """
    if prog_bar:
        lives_it = [find_livestreams(chan_id) for chan_id in tqdm.tqdm(channel_list, desc='Looking for livestreams')]
    else:
        lives_it = [find_livestreams(chan_id) for chan_id in channel_list]

    return list(itertools.chain.from_iterable(lives_it))


def iter_playlists(service: googleapiclient.discovery, playlists: list, day_ago: int = None,
                   with_last_exe: bool = True, latest_d: dt.datetime = NOW, prog_bar: bool = True):
    """Apply 'get_playlist_items' for a collection of YouTube playlists
    :param playlists: list of YouTube channel IDs
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param day_ago: day difference with a reference date, delimits items' collection field
    :param latest_d: latest reference date
    :param with_last_exe: to use last execution date extracted from log or not
    :param prog_bar: to use tqdm progress bar or not
    :return: videos retrieved in playlists.
    """
    if prog_bar:
        item_it = [get_playlist_items(service=service, playlist_id=playlist_id, day_ago=day_ago, latest_d=latest_d,
                                      with_last_exe=with_last_exe)
                   for playlist_id in tqdm.tqdm(playlists, desc='Looking for videos to add')]
    else:
        item_it = [get_playlist_items(service=service, playlist_id=playlist_id, day_ago=day_ago, latest_d=latest_d,
                                      with_last_exe=with_last_exe) for playlist_id in playlists]
    return list(itertools.chain.from_iterable(item_it))


def update_playlist(service: googleapiclient.discovery, playlist_id: str, videos_to_add: list, is_live: bool = False,
                    min_duration: int = 10, del_day_ago: int = 7, ref_date: dt.datetime = NOW, prog_bar: bool = True):
    """Update a YouTube playlist with temporal criteria
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param videos_to_add: list of YouTube video IDs to potentially add to a specified playlist
    :param is_live: to update a list containing specifically livestreams only (or not)
    :param del_day_ago: day difference with NOW, to keep in playlist video published in the last 'del_day_ago' days
    :param ref_date: reference date (NOW by default)
    :param min_duration: minimal video duration filter
    :param prog_bar: to use tqdm progress bar or not.
    """

    def add_and_remove(_service, _playlist_id, _to_add_df, _to_delete_df, _type: str = 'video'):
        """Perform a playlist update, avoid code duplication
        :param _service: a YouTube service build with 'googleapiclient.discovery'
        :param _playlist_id: a YouTube playlist ID
        :param _to_add_df: pd.DataFrame of videos to add to the playlist
        :param _to_delete_df: pd.DataFrame of videos to remove from the playlist
        :param _type: content type (livestream or video).
        """
        if not _to_add_df.empty:  # If there are videos to add
            add_to_playlist(service=_service, playlist_id=_playlist_id, videos_list=_to_add_df.video_id,
                            prog_bar=prog_bar)
            history.info(f'{_to_add_df.shape[0]} new {_type}(s) added.')
            last_exe.info(f'{_to_add_df.shape[0]} new {_type}(s) added.')

        if not _to_delete_df.empty:  # If there are videos to delete
            del_from_playlist(service=_service, playlist_id=_playlist_id, items_list=_to_delete_df.item_id,
                              prog_bar=prog_bar)
            history.info(f'{_to_delete_df.shape[0]} {_type}(s) removed.')
            last_exe.info(f'{_to_delete_df.shape[0]} {_type}(s) removed.')

        if _to_add_df.empty and _to_delete_df.empty:
            history.info(f'No {_type} added or removed.')
            last_exe.info(f'No {_type} added or removed.')

    # Pass playlist as pandas Dataframes (for easier filtering)
    already_in = pd.DataFrame(get_playlist_items(service=service, playlist_id=playlist_id))  # Get videos already in
    to_add_df = pd.DataFrame(videos_to_add)

    if not already_in.empty:  # If there is at least one video in the playlist
        if not to_add_df.empty:  # Check if there are some new videos and new videos are already in
            to_add_df = to_add_df.loc[~to_add_df.video_id.isin(already_in.video_id)]

        if is_live:  # If the update is done on a YouTube livestreams playlist
            # Retrieve live status
            live_status = pd.DataFrame(check_if_live(service=service, videos_list=already_in.video_id))
            already_in = already_in.merge(live_status)

            # Do not keep private videos. Do not keep upcoming and finished livestreams.
            to_delete_df = already_in.loc[(already_in.status == 'private') | (already_in.live_status != 'live')]

            # Perform update
            add_and_remove(_service=service, _playlist_id=playlist_id, _to_add_df=to_add_df,
                           _to_delete_df=to_delete_df, _type='livestream')

        else:
            date_delta = ref_date - dt.timedelta(days=del_day_ago)  # Days subtraction
            delete_cond = (already_in.status == 'private') | (already_in.release_date < date_delta)  # Delete condition
            to_delete_df = already_in.loc[delete_cond]  # To keep public and newest videos.

            if not to_add_df.empty:  # Check if there are videos to add
                # Get durations of videos to add
                durations = pd.DataFrame(get_durations(service=service, videos_list=videos_to_add))
                to_add_df = to_add_df.merge(durations)

                # Keep videos with duration above `min_duration` minutes and don't keep "Premiere" type videos
                to_add_df = to_add_df.loc[(to_add_df.duration >= min_duration) & (to_add_df.live_status != 'upcoming')]

            # Perform update
            add_and_remove(_service=service, _playlist_id=playlist_id, _to_add_df=to_add_df, _to_delete_df=to_delete_df)

    else:  # If there is no video in the playlist
        if is_live and to_add_df.empty:  # If there are livestreams to add
            add_to_playlist(service=service, playlist_id=playlist_id, videos_list=to_add_df.video_id, prog_bar=prog_bar)
            history.info(f'{to_add_df.shape[0]} new livestream(s) added.')
            last_exe.info(f'{to_add_df.shape[0]} new livestream(s) added.')

        else:  # For regular videos
            if not to_add_df.empty:  # Check if there are videos to add
                # Get durations of videos to add
                durations = pd.DataFrame(get_durations(service=service, videos_list=videos_to_add))
                to_add_df = to_add_df.merge(durations)

                # Keep videos with duration above `min_duration` minutes and don't keep "Premiere" type videos
                to_add_df = to_add_df.loc[(to_add_df.duration >= min_duration) & (to_add_df.live_status != 'upcoming')]

            if not to_add_df.empty:  # Check again if there are videos to add
                add_to_playlist(service=service, playlist_id=playlist_id, videos_list=to_add_df.video_id,
                                prog_bar=prog_bar)
                history.info(f'{to_add_df.shape[0]} new video(s) added.')
                last_exe.info(f'{to_add_df.shape[0]} new video(s) added.')

            else:
                history.info('No video added.')
                last_exe.info('No video added.')


def add_to_playlist(service: googleapiclient.discovery, playlist_id: str, videos_list: list, prog_bar: bool = True):
    """Add a list of video to a YouTube playlist
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param videos_list: list of YouTube video IDs
    :param prog_bar: to use tqdm progress bar or not.
    """
    if prog_bar:
        add_iterator = tqdm.tqdm(videos_list, desc=f'Adding videos to the playlist ({playlist_id})')

    else:
        add_iterator = videos_list

    for video_id in add_iterator:
        r_body = {'snippet': {'playlistId': playlist_id, 'resourceId': {'kind': 'youtube#video', 'videoId': video_id}}}
        request = service.playlistItems().insert(part="snippet", body=r_body)

        try:
            request.execute()

        except googleapiclient.errors.HttpError:
            history.error(f'(HttpError) Something went wrong with this video: {video_id}')
            last_exe.error(f'(HttpError) Something went wrong with this video: {video_id}')


def del_from_playlist(service: googleapiclient.discovery, playlist_id: str, items_list: list, prog_bar: bool = True):
    """Delete a list of video from a YouTube playlist
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param items_list: list of YouTube playlist items
    :param prog_bar: to use tqdm progress bar or not.
    """
    if prog_bar:
        del_iterator = tqdm.tqdm(items_list, desc=f'Deleting videos from the playlist ({playlist_id})')

    else:
        del_iterator = items_list

    for item_id in del_iterator:
        request = service.playlistItems().delete(id=item_id)

        try:
            request.execute()

        except googleapiclient.errors.HttpError:
            history.error(f'(HttpError) Something went wrong with this item: {item_id}')
            last_exe.error(f'(HttpError) Something went wrong with this item: {item_id}')
