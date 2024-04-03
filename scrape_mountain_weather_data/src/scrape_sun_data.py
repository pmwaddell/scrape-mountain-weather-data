import datetime
import re
import pandas as pd
from urllib.request import urlopen


def find_date(html):
    date_regex = re.compile(
        r"""
        <th>Current\ Time:\ <\/th><td\ id=smct>
        (.*)
        <\/td><\/tr><tr><th>Sun\ Direction:
        """, flags=re.VERBOSE
    )
    date_info = date_regex.search(html).group(1).replace(',', '').split()[:3]

    year = date_info[2]

    month_abbrev_to_number = {
        'Jan': '01',
        'Feb': '02',
        'Mar': '03',
        'Apr': '04',
        'May': '05',
        'Jun': '06',
        'Jul': '07',
        'Aug': '08',
        'Sep': '09',
        'Oct': '10',
        'Nov': '11',
        'Dec': '12'
    }
    month = month_abbrev_to_number[date_info[0]]

    day = date_info[1]
    if len(day) == 1:
        day = '0' + day

    timestamp_str = f'{year}-{month}-{day}'
    return pd.to_datetime(timestamp_str, format='%Y-%m-%d')


def find_sun_event(html, event, date, time_zone):
    sun_event_regex = re.compile(
        rf"""
        Sun{event}\ Today:\ <\/th><td>
        ([0-9]?[0-9])
        :([0-9]?[0-9][0-9]?[0-9])
        \ ([a-z][a-z])
        <span
        """, flags=re.VERBOSE
    )
    sun_event_result = sun_event_regex.search(html)
    hours = int(sun_event_result.group(1))
    mins = int(sun_event_result.group(2))
    am_pm = sun_event_result.group(3)

    # Format the hours:
    if am_pm == 'pm' and hours != 12:
        hours += 12

    total_mins = 60 * hours + mins
    date = date + datetime.timedelta(minutes=total_mins)
    return date.tz_localize(time_zone)


def find_sun_data(csv_name):
    df = pd.read_csv(csv_name)
    dates, sunrises, sunsets = [], [], []
    for index, row in df.iterrows():
        url = 'https://www.timeanddate.com/sun/' + row['timeanddate_url_end']
        html = urlopen(url).read().decode("utf-8")
        date = find_date(html)
        dates.append(date)
        sunrises.append(find_sun_event(html, 'rise', date, row['time_zone']))
        sunsets.append(find_sun_event(html, 'set', date, row['time_zone']))

    df.insert(4, 'date', dates)
    df.insert(5, 'sunrise_time', sunrises)
    df.insert(6, 'sunset_time', sunsets)
    return df
