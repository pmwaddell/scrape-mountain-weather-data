import re
import time

import pandas as pd
from urllib.request import urlopen


def find_forecast_table(html):
    forecast_table_regex = re.compile(
        r"""
        (<div\ class="js-vis-forecast\ forecast-table"\ data-scroll-fade=""\ id="forecast-table">)  
        # above: start of the forecast table
        (.*?)                           # all contents of the forecast table
        (<div\ class="c-container">)    # beginning of the next secction
        """, flags=re.VERBOSE | re.DOTALL
    )
    return forecast_table_regex.search(html).group(2)


def find_full_forecast_table_data(regex, forecast_table, data_group, data_type):
    findall_result = re.findall(regex, forecast_table)
    all_table_values = []
    for i in range(len(findall_result)):
        all_table_values.append(data_type(findall_result[i][data_group - 1]))
    return all_table_values


def find_elev_feature(mtn_name, elev, html):
    elev_feature_regex = re.compile(
        fr"""
        (<a\ class="forecast-table-elevation__link\ forecast-table-elevation__link--is-active"\ data-elevation-level="{elev}"\ data-elevation-group="[a-z]*"\ href="/peaks/{mtn_name}/forecasts/{elev}">)
        # above: should only match the elevation feature at the searched elevation
        (<span\ class="forecast-table-elevation__prefix"\ data-elevation-prefix=".*?">)
        ([a-zA-Z]*)     # name of the elevation feature (e.g. base, peak...)
        (:</span>)      # end of container
        """, flags=re.VERBOSE
    )
    try:
        return elev_feature_regex.search(html).group(3)
    except AttributeError:
        return None


def get_time_of_scrape():
    return pd.Timestamp.now().round('min')


def find_time_issued(html):
    time_issued_regex = re.compile(
        r"""
        (<span\ class="issued__time">)  # class for issued time
        (.*)                            # description of the issued time
        (\ Local\ Time<\/span>)         # end of container
        """, flags=re.VERBOSE
    )
    result = time_issued_regex.search(html).group(2)

    result_split = result.split()
    # Format the hour:
    hour = int(result_split[0])
    if result_split[1] == 'pm' and hour != 12:
        hour += 12
    hour = str(hour)
    if len(hour) == 1:
        hour = '0' + hour
    # Format the date:
    date = result_split[3]
    if len(date) == 1:
        date = '0' + date
    # Format the month:
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
    month = month_abbrev_to_number[result_split[4]]
    # Determine the correct year:
    # Since the year is not given on the site, it must be manually determined.
    # There could be an issue when the local time of the scraper and the time
    # at the mountain are different years, i.e. on Dec 31/Jan 1.
    # Therefore, if the scraper's month is Dec and the issued month is Jan,
    # then the correct year is 1 + the scraper's year.
    # This also works the other way around if the scraper's time is ahead of
    # the issued time.
    # Otherwise, the issued and local years are the same.
    scraper_month = pd.Timestamp.now().month
    scraper_year = pd.Timestamp.now().year
    issued_month = int(month)
    if scraper_month == 12 and issued_month == 1:
        year = scraper_year + 1
    elif scraper_month == 1 and issued_month == 12:
        year = scraper_year - 1
    else:
        year = scraper_year

    timestamp_str = f'{year}-{month}-{date} {hour}'
    return pd.to_datetime(timestamp_str, format='%Y-%m-%d %H')


def determine_forecast_statuses(l):
    return ['actual'] + ['forecast'] * (l - 1)


def approximate_forecast_times(html, forecast_table):
    forecast_date_regex = re.compile(
        r"""
        (<td\ class="forecast-table-days__cell\ forecast-table__cell\ forecast-table__cell--day-[a-z -=]*"\ colspan="[0-9]*"\ data-column-head=""\ data-date=")
        ([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])
        """, flags=re.VERBOSE
    )
    time_issued = find_time_issued(html)
    forecast_dates = \
        find_full_forecast_table_data(forecast_date_regex,
                                      forecast_table, 2, str)
    time_names = find_time_names(forecast_table)
    result = []
    date_index = 0
    for time_name in time_names:
        result.append(convert_table_forecast_time_to_datetime(
            forecast_dates[date_index],
            time_issued,
            time_name
        ))
        # To match the "time names" and scraped dates up correctly, since
        # there are up to three "time names" for each date, the date must
        # advanced after each "night" appears.
        if time_name == 'night':
            date_index += 1
    return result


def convert_table_forecast_time_to_datetime(forecast_date, time_issued,
                                            time_name):
    if time_name == "AM":
        forecast_hour = 7
    elif time_name == "PM":
        forecast_hour = 15
    elif time_name == "night":
        forecast_hour = 23
    else:
        forecast_hour = 12

    timestamp_str = f'{forecast_date} {forecast_hour}'
    return pd.to_datetime(timestamp_str, format='%Y-%m-%d %H')


def find_time_names(forecast_table):
    time_name_regex = re.compile(
        r"""
        (forecast-table__time.*?><span\ class="en">)  
        # above: text that comes right before the "time name"
        ([a-zA-Z]*)     # "time name" (i.e., "AM", "PM" or "night")
        (<\/span>)      # end of the container
        """, flags=re.VERBOSE
    )
    return find_full_forecast_table_data(time_name_regex,
                                         forecast_table, 2, str)


def find_forecast_phrases(forecast_table):
    forecast_phrase_regex = re.compile(
        r"""
        (<span\ class="forecast-table__phrase\ forecast-table__phrase--en">)
        # above: start of the container with the forecast phrase
        (.*?)           # forecast phrase
        (<\/span>)      # end of the container
        """, flags=re.VERBOSE
    )
    return find_full_forecast_table_data(forecast_phrase_regex,
                                         forecast_table, 2, str)


def find_wind_speeds(forecast_table):
    wind_speed_regex = re.compile(
        r"""
        (<text\ class="wind-icon__val"\ fill="rgb\(.*?\)"\ text-anchor="middle"\ x="0"\ y="5">)
        # above: beginning of the container with the wind speed value; rgb varies depending on the speed
        ([0-9]*)        # wind speed
        (<\/text>)      # end of the container
        """, flags=re.VERBOSE
    )
    return find_full_forecast_table_data(wind_speed_regex,
                                         forecast_table, 2, int)


def find_snow(forecast_table):
    snow_regex = re.compile(
        r"""
        (<div\ class="snow-amount".*?><span.*?>)
        # above: start of the container with snow datum
        (—?[0-9]*\.?[0-9]?)     # amount of snow, or "em dash" if no snow
        # note: for some reason, the "em dash" becomes "â€”" in the string, so this is what must be searched for
        (<\/span>)              # end of container
        """, flags=re.VERBOSE
    )
    snow_table_data = find_full_forecast_table_data(snow_regex,
                                                    forecast_table, 2, str)
    for i in range(len(snow_table_data)):
        if snow_table_data[i] == "—":
            snow_table_data[i] = float(0.0)
        else:
            snow_table_data[i] = float(snow_table_data[i])
    return snow_table_data


def find_rain(forecast_table):
    rain_regex = re.compile(
        r"""
        (<div\ class="rain-amount\ forecast-table__container\ forecast-table__container--rain.*?><span.*?>)
        # above: start of the container with rain data
        (—?[0-9]*\.?[0-9]?)     # amount of rain, or "em dash" if no rain
        (<\/span>)              # end of container
        """, flags=re.VERBOSE
    )
    rain_table_data = find_full_forecast_table_data(rain_regex,
                                                    forecast_table, 2, str)
    for i in range(len(rain_table_data)):
        if rain_table_data[i] == "—":
            rain_table_data[i] = float(0.0)
        else:
            rain_table_data[i] = float(rain_table_data[i])
    return rain_table_data


def find_max_temps(forecast_table):
    max_temp_regex = re.compile(
        r"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch\ forecast-table__container--max)
        # above: start of the container with the max temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]*")             # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?\.[0-9]?")?  # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # max temperature datum
        (<\/div>)                                       # end of the container
        """, flags=re.VERBOSE
    )
    return find_full_forecast_table_data(max_temp_regex, forecast_table, 6, int)


def find_min_temps(forecast_table):
    min_temp_regex = re.compile(
        r"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch\ forecast-table__container--min)
        # above: start of the container with the max temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]*")             # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?\.[0-9]?")?  # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # min temperature datum
        (<\/div>)                                       # end of the container
        """, flags=re.VERBOSE
    )
    return find_full_forecast_table_data(min_temp_regex, forecast_table, 6, int)


def find_chills(forecast_table):
    chill_regex = re.compile(
        r"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch)
        # above: start of the container with the chill temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]*")             # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?\.[0-9]?")?  # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # chill temperature datum
        (<\/div>)                                       # end of the container
        """, flags=re.VERBOSE
    )
    return find_full_forecast_table_data(chill_regex, forecast_table, 6, int)


def find_freezing_levels(forecast_table):
    freezing_level_regex = re.compile(
        r"""
        (<div\ class="forecast-table__container\ forecast-table__container--blue)
        # above: start of the container with freezing level datum
        (\ forecast-table__container--border)?              # this bit of text appears only when the cell is on the edge
        (">)                                                # ending the tag whether the prior group is present or not
        (<div\ class="level-value"\ data-value="[0-9]*">)   # I believe this will always occur
        ([0-9]*)                                            # freezing level
        (<\/div>)                                           # end of the container
        """, flags=re.VERBOSE
    )
    return find_full_forecast_table_data(freezing_level_regex,
                                         forecast_table, 5, int)


def find_cloud_bases(forecast_table):
    cloud_base_regex = re.compile(
        r"""
        (<div\ class="forecast-table__container\ forecast-table__container--cloud-base)
        # above: start of the container with freezing level datum
        (\ forecast-table__container--border)?  # this bit of text appears only when the cell is on the edge
        (">)                                    # ending the tag whether the prior group is present or not
        (<div\ class="level-value")
        (\ data-value="[0-9]*")?                # this part only occurs when there is data
        (>)                                     # ending the tag whether the prior group is present or not
        ([0-9]*?)                               # cloud base, which will give an empty string if there is no data
        (<\/div>)                               # end of the container
        """, flags=re.VERBOSE
    )
    cloud_base_table_data = \
        find_full_forecast_table_data(cloud_base_regex, forecast_table, 7, str)
    for i in range(len(cloud_base_table_data)):
        if cloud_base_table_data[i] == '':
            cloud_base_table_data[i] = None
        else:
            cloud_base_table_data[i] = int(cloud_base_table_data[i])
    return cloud_base_table_data


def scrape_mtn_full_forecast_table_at_elev(mtn_name, elev):
    url = f"http://www.mountain-forecast.com/peaks/{mtn_name}/forecasts/{elev}"
    html = urlopen(url).read().decode("utf-8")
    forecast_table = find_forecast_table(html)

    wind_speed_lst = find_wind_speeds(forecast_table)
    col_len = len(wind_speed_lst)
    return pd.DataFrame(
        {
            'mtn_name': [format_strings(mtn_name)] * col_len,
            'elevation': [elev] * col_len,
            'elev_feature': [format_strings(
                find_elev_feature(mtn_name, elev, html))] * col_len,
            'time_of_scrape': [get_time_of_scrape()] * col_len,
            'local_time_issued': [find_time_issued(html)] * col_len,
            'forecast_status': determine_forecast_statuses(col_len),
            'local_time_of_forecast': approximate_forecast_times(
                html, forecast_table),
            'forecast_time_name': format_strings(
                find_time_names(forecast_table)),
            'forecast_phrase': format_strings(
                find_forecast_phrases(forecast_table)),
            'wind_speed': wind_speed_lst,
            'snow': find_snow(forecast_table),
            'rain': find_rain(forecast_table),
            'max_temp': find_max_temps(forecast_table),
            'min_temp': find_min_temps(forecast_table),
            'chill': find_chills(forecast_table),
            'freezing_level': find_freezing_levels(forecast_table),
            'cloud_base': find_cloud_bases(forecast_table)
        }
    )


def scrape_mtn_current_weather_at_elev(mtn_name, elev):
    return scrape_mtn_full_forecast_table_at_elev(mtn_name, elev).iloc[:1]


def format_strings(s):
    if s is None:
        return None
    if type(s) is list:
        for i in range(len(s)):
            s[i] = s[i].lower().replace('-', '_').replace(' ', '_')
        return s
    else:
        return s.lower().replace('-', '_').replace(' ', '_')


def scrape_weather(mtns_to_elevs, current_only=False):
    dfs = []
    for mtn_name in mtns_to_elevs.keys():
        for elev in mtns_to_elevs[mtn_name]:
            print(f'Scraping weather for {mtn_name} at {elev}: ', end='')
            if current_only:
                dfs.append(scrape_mtn_current_weather_at_elev(mtn_name, elev))
            else:
                dfs.append(
                    scrape_mtn_full_forecast_table_at_elev(mtn_name, elev))
            print('complete.')
            time.sleep(5)
    return pd.concat(dfs, ignore_index=True)
