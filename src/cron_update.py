# -*- coding: utf-8 -*-

import datetime as dt
import pandas as pd
import re
import tzlocal

"""File Information
@file_name: cron_update.py
@author: Dylan "dyl-m" Monfret
Script to adjust playlist update
"""

"FUNCTIONS"


def get_weekday(date: dt.datetime):
    """Get day of the week out of a datetime
    :param date: date as datetime.datetime object.
    :return: weekday label.
    """
    weekday_list = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    week_day_num = dt.datetime.isoweekday(date)
    return weekday_list[week_day_num - 1]


def make_update_pattern(n_update: int):
    """Create update pattern in CRON format
    :param n_update: Number of updates desired
    :return up_pattern: pattern in CRON format.
    """
    if n_update == 0:
        return '0 0 * * '

    if n_update > 12:
        n_update = 12

    step = int(12 / n_update)
    up_hours = list(range(12, 24, step))[-n_update:]
    up_pattern = '0 0,' + ','.join(map(str, up_hours)) + ' * *'
    return up_pattern


"MAIN"

if __name__ == '__main__':
    # Data import and reformat
    data = pd.read_csv('../data/mix_history.csv', encoding='utf-8', low_memory=False).loc[:, ['video_id',
                                                                                              'release_date']]
    weekday_categories = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

    data.release_date = pd.to_datetime(data.loc[:, 'release_date'])
    data['release_week'] = data.loc[:, 'release_date'].dt.isocalendar().week
    data['release_weekday'] = data.loc[:, 'release_date'].apply(get_weekday)
    data.release_weekday = pd.Categorical(data.release_weekday, categories=weekday_categories)
    data.sort_values('release_weekday', inplace=True)

    # Get date 5 weeks ago and filter out 5 weeks old data
    five_weeks_ago = dt.datetime.now(tz=tzlocal.get_localzone()) - dt.timedelta(weeks=5)
    data = data.loc[data.release_date > five_weeks_ago]

    # Get average update per weekday
    data_agg = data.groupby(['release_weekday', 'release_week'], as_index=False) \
                   .count() \
                   .loc[:, ['release_weekday', 'video_id']] \
        .groupby(['release_weekday'], as_index=False) \
        .mean() \
        .rename(columns={'video_id': 'avg_amount'})

    data_agg.avg_amount = data_agg.avg_amount.round().astype(int)
    data_agg['day_index'] = data_agg.avg_amount.index
    data_agg = data_agg.to_dict('records')

    # Build schedules in cron format
    new_schedules = [f'        -   cron: "{make_update_pattern(record["avg_amount"])} {record["day_index"]}"'
                     for record in data_agg]

    new_schedules_str = '\n'.join(new_schedules)

    # Open current workflow file
    with open('../.github/workflows/update_workflow.yml', 'r', encoding='utf-8') as update_yaml_file:
        update_yaml = update_yaml_file.read()

    # Replace current schedule with the new one
    schedule = re.sub(' {4}schedule:.*?jobs:',
                      f'    schedule:\n{new_schedules_str}\n\njobs:',
                      update_yaml,
                      flags=re.DOTALL)

    # Write new YAML file
    with open('../.github/workflows/update_workflow.yml', 'w', encoding='utf-8') as updated_yaml_file:
        updated_yaml_file.write(schedule)
