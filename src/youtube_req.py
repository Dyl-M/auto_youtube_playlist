# -*- coding: utf-8 -*-

import ast
import base64
import bs4
import datetime as dt
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

# Create file handlers
history_file = logging.FileHandler(filename='../log/history.log')  # mode='a'

# Create formatter
formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S%z')

# Set file handlers' level
history_file.setLevel(logging.DEBUG)

# Assign file handlers and formatter to loggers
history_file.setFormatter(formatter)
history.addHandler(history_file)

"FUNCTIONS"


def encode_key(json_path: str, export_dir: str = None, export_name: str = None):
    """Encode a JSON authentication file to base64
    :param json_path: file path to authentication JSON file
    :param export_dir: export directory
    :param export_name: export file name.
    """
    path_split = json_path.split('/')
    file_name = path_split[-1].removesuffix('.json')

    if export_dir is None:
        export_dir = json_path.removesuffix(f'{file_name}.json')

    if export_name is None:
        export_name = f'{file_name}_b64.txt'

    if 'tokens' not in json_path:
        history.critical('FORBIDDEN ACCESS. Invalid file path.')
        sys.exit()

    elif not os.path.exists(json_path):
        history.error(f'{json_path} file does not exist.')
        sys.exit()

    else:
        with open(json_path, 'r', encoding='utf8') as json_file:
            key_dict = json.load(json_file)

        key_str = json.dumps(key_dict).encode('utf-8')
        key_b64 = base64.urlsafe_b64encode(key_str)

        with open(export_dir + export_name, 'wb') as key_file:
            key_file.write(key_b64)


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

        return service

    except Exception as error:  # skipcq: PYL-W0703 - No known errors at the moment.
        if log:
            history.critical(f'({error}) {instance_fail_message}')

        sys.exit()


def create_service_workflow():
    """Retrieve authentication credentials from dedicated repository secrets
    :return service: a Google API service object build with 'googleapiclient.discovery.build'.
    """

    def import_env_var(var_name: str):
        """Import variable environment and perform base64 decoding
        :param var_name: environment variable name
        :return value: decoded value
        """
        v_b64 = os.environ.get(var_name)  # Get environment variable
        v_str = base64.urlsafe_b64decode(v_b64).decode(encoding='utf8')  # Decode
        value = ast.literal_eval(v_str)  # Eval
        return value

    creds_dict = import_env_var(var_name='CREDS_B64')  # Import pre-registered credentials
    creds = Credentials.from_authorized_user_info(creds_dict)  # Conversion to suitable object
    instance_fail_message = 'Failed to create service instance for YouTube'

    if not creds.valid:  # Cover outdated credentials
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh token

            # Get refreshed token as JSON-like string
            creds_str = json.dumps(ast.literal_eval(creds.to_json())).encode('utf-8')

            creds_b64 = str(base64.urlsafe_b64encode(creds_str))[2:-1]  # Encode token
            os.environ["CREDS_B64"] = creds_b64  # Update environment variable value
            history.info('API credentials refreshed.')

        else:
            history.critical('ERROR: Unable to refresh credentials. Check Google API OAUTH parameter.')
            sys.exit()

    try:
        service = googleapiclient.discovery.build('youtube', 'v3', credentials=creds)  # Build service.
        history.info('YouTube service created successfully.')
        return service

    except Exception as error:  # skipcq: PYL-W0703 - No known errors at the moment.
        history.critical(f'({error}) {instance_fail_message}')
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
                break

            history.error(f'[{playlist_id}] Unknown error: {error_reason}')
            sys.exit()

    return p_items


def get_videos(service: googleapiclient.discovery, videos_list: list):
    """Get information from YouTube videos
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param videos_list: list of YouTube video IDs
    :return: request results.
    """
    return service.videos().list(part=['snippet', 'contentDetails', 'statistics'],
                                 id=",".join(videos_list),
                                 maxResults=50).execute()


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
            sys.exit()

    return items


def get_stats(service: googleapiclient.discovery, videos_list: list):
    """Get duration, views and live status of YouTube video with their ID
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param videos_list: list of YouTube video IDs
    :return items: playlist items (videos) as a list.
    """
    items = []

    try:
        videos_ids = [video['video_id'] for video in videos_list]

    except TypeError:
        videos_ids = videos_list

    # Split task in chunks of size 50 to request on a maximum of 50 videos at each iteration.
    videos_chunks = [videos_ids[i:i + min(50, len(videos_ids))] for i in range(0, len(videos_ids), 50)]

    for chunk in videos_chunks:
        try:
            request = get_videos(service=service, videos_list=chunk)

            # Keep necessary data
            items += [{'video_id': item['id'],
                       'views': item['statistics']['viewCount'],
                       'duration': isodate.parse_duration(item['contentDetails']['duration']).seconds / 60,
                       'live_status': item['snippet']['liveBroadcastContent']} for item in request['items']]

        except googleapiclient.errors.HttpError as http_error:
            history.error(http_error.error_details)
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
                    min_duration: int = 10, del_day_ago: int = 7, ref_date: dt.datetime = NOW, prog_bar: bool = True,
                    log: bool = True):
    """Update a YouTube playlist with temporal criteria
    :param service: a YouTube service build with 'googleapiclient.discovery'
    :param playlist_id: a YouTube playlist ID
    :param videos_to_add: list of YouTube video IDs to potentially add to a specified playlist
    :param is_live: to update a list containing specifically livestreams only (or not)
    :param del_day_ago: day difference with NOW, to keep in playlist video published in the last 'del_day_ago' days
    :param ref_date: reference date (NOW by default)
    :param min_duration: minimal video duration filter
    :param prog_bar: to use tqdm progress bar or not
    :param log: to apply logging or not.
    """

    def add_and_remove(_service, _playlist_id, _to_add_df, _to_delete_df, _is_live: bool, _log: bool = True):
        """Perform a playlist update, avoid code duplication
        :param _service: a YouTube service build with 'googleapiclient.discovery'
        :param _playlist_id: a YouTube playlist ID
        :param _to_add_df: pd.DataFrame of videos to add to the playlist
        :param _to_delete_df: pd.DataFrame of videos to remove from the playlist
        :param _is_live: specify if the updated playlist contains specifically livestreams only (or not)
        :param _log: to apply logging or not.
        """
        _type = 'video'

        if _is_live:
            _type = 'livestream'

        if not _to_add_df.empty:  # If there are videos to add
            add_to_playlist(service=_service, playlist_id=_playlist_id, videos_list=_to_add_df.video_id,
                            prog_bar=prog_bar)
            if _log:
                history.info(f'{_to_add_df.shape[0]} new {_type}(s) added.')

        if not _to_delete_df.empty:  # If there are videos to delete
            del_from_playlist(service=_service, playlist_id=_playlist_id, items_list=_to_delete_df.item_id,
                              prog_bar=prog_bar)
            if _log:
                history.info(f'{_to_delete_df.shape[0]} {_type}(s) removed.')

        if _to_add_df.empty and _to_delete_df.empty and _log:
            history.info(f'No {_type} added or removed.')

    # Pass playlist as pandas Dataframes (for easier filtering)
    in_playlist = pd.DataFrame(get_playlist_items(service=service, playlist_id=playlist_id))  # Get videos already in
    to_del = pd.DataFrame()  # In case there is no video to remove from the playlist

    if not in_playlist.empty:  # If there is at least one video in the playlist
        if is_live:  # If the update is done on a YouTube livestreams playlist
            live_status = pd.DataFrame(check_if_live(service=service, videos_list=in_playlist.video_id))  # Get status
            in_playlist = in_playlist.merge(live_status)
            del_cond = (in_playlist.status == 'private') | (in_playlist.live_status != 'live')  # Delete condition
            to_del = in_playlist.loc[del_cond]  # Keep active and public livestreams

        else:
            video_stats = pd.DataFrame(get_stats(service=service, videos_list=in_playlist.video_id))  # Get stats
            in_playlist = in_playlist.merge(video_stats)
            date_delta = ref_date - dt.timedelta(days=del_day_ago)  # Days subtraction
            del_cond = (in_playlist.status == 'private') | (in_playlist.release_date < date_delta)  # Delete condition
            to_del = in_playlist.loc[del_cond]  # Keep public and newest videos.

            if not to_del.empty:  # Save deleted videos as CSV
                if not os.path.exists('../data/mix_history.csv'):
                    to_del.to_csv('../data/mix_history.csv', encoding='utf8', index=False)

                else:
                    mix_history = pd.read_csv('../data/mix_history.csv', encoding='utf8', low_memory=False)
                    mix_history = pd.concat([mix_history, to_del], ignore_index=True)
                    mix_history.to_csv('../data/mix_history.csv', encoding='utf8', index=False)

    to_add = pd.DataFrame(videos_to_add)

    if not to_add.empty:  # Check if there are videos to add
        if not is_live:  # If the update is done on a YouTube livestreams playlist
            add_stats = pd.DataFrame(get_stats(service=service, videos_list=videos_to_add))  # Get stats of new videos
            to_add = to_add.merge(add_stats)
            # Keep videos with duration above `min_duration` minutes and don't keep "Premiere" type videos
            to_add = to_add.loc[(to_add.duration >= min_duration) & (to_add.live_status != 'upcoming')]

        to_add = to_add.loc[~to_add.video_id.isin(in_playlist.video_id)]  # Keep videos not already in playlist

    add_and_remove(_service=service, _playlist_id=playlist_id, _to_add_df=to_add, _to_delete_df=to_del, _log=log,
                   _is_live=is_live)


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

        except googleapiclient.errors.HttpError as error:  # skipcq: PYL-W0703
            history.error(f'({video_id}) - {error}')


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

        except googleapiclient.errors.HttpError as error:  # skipcq: PYL-W0703
            history.error(f'({item_id}) - {error}')
