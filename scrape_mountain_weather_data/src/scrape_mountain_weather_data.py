import re
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


def approximate_forecast_time(html, forecast_table):
    time_issued = find_time_issued(html)
    # TODO: in future we will need to reconcile the fact that this date applies to multiple cells and coordinate matching them up properly
    # Note: a regex pattern must be used here that finds the right date even if
    # it is not displayed in the cell, which happens when the first date is
    # only one column wide in the table.
    forecast_date_regex = re.compile(
        r"""
        (<td\ class="forecast-table-days__cell\ forecast-table__cell\ forecast-table__cell--day-even"\ colspan="[0-9]*"\ data-column-head=""\ data-date="[0-9][0-9][0-9][0-9]-[0-9][0-9]-)
        ([0-9][0-9])
        """, flags=re.VERBOSE
    )
    forecast_date = forecast_date_regex.search(forecast_table).group(2)

    # TODO: for getting the entire table, we may need to split this section off and apply it to every element of the list
    # and just the one value for the current weather
    # however, we will need to handle the time_names too
    # in this case, we will pass that to the split off function I guess, find it up here instead or whatever

    # Determine correct month for the forecast:
    if int(forecast_date) == 1 and time_issued.day > 1:
        forecast_month = time_issued.month + 1
    else:
        forecast_month = time_issued.month
    # Determine correct year for the forecast:
    # Here I am assuming that the dates in the cells will always be AHEAD of
    # the time when the data was issued.
    if time_issued.month == 12 and forecast_month == 1:
        forecast_year = time_issued.year + 1
    else:
        forecast_year = time_issued.year
    # Determine the correct hour for the forecast:
    # Here, I am basing this value on the "time name", such that "AM" means
    # 7 AM, "PM" means 3 PM, and "night" means 11 PM.
    # This is arbitrary on my part, and is done to ease calculation.

    time_name = find_time_name(forecast_table)
    if time_name == "AM":
        forecast_hour = 7
    elif time_name == "PM":
        forecast_hour = 15
    elif time_name == "night":
        forecast_hour = 23
    else:
        forecast_hour = 12

    # Format the hour:
    forecast_hour = str(forecast_hour)
    if len(forecast_hour) == 1:
        forecast_hour = '0' + forecast_hour
    # Format the date:
    if len(forecast_date) == 1:
        forecast_date = '0' + forecast_date
    # Format the month:
    forecast_month = str(forecast_month)
    if len(forecast_month) == 1:
        forecast_month = '0' + forecast_month

    timestamp_str = \
        f'{forecast_year}-{forecast_month}-{forecast_date} {forecast_hour}'
    return pd.to_datetime(timestamp_str, format='%Y-%m-%d %H')


def find_time_name(forecast_table, find_full_table_data=False):
    time_name_regex = re.compile(
        r"""
        (forecast-table__time.*?><span\ class="en">)  
        # above: text that comes right before the "time name"
        ([a-zA-Z]*)     # "time name" (i.e., "AM", "PM" or "night")
        (<\/span>)      # end of the container
        """, flags=re.VERBOSE
    )
    if find_full_table_data:
        return find_full_forecast_table_data(time_name_regex, forecast_table, 2, str)
    return time_name_regex.search(forecast_table).group(2)


def find_forecast_phrase(forecast_table, find_full_table_data=False):
    forecast_phrase_regex = re.compile(
        r"""
        (<span\ class="forecast-table__phrase\ forecast-table__phrase--en">)
        # above: start of the container with the forecast phrase
        (.*?)           # forecast phrase
        (<\/span>)      # end of the container
        """, flags=re.VERBOSE
    )
    if find_full_table_data:
        return find_full_forecast_table_data(forecast_phrase_regex, forecast_table, 2, str)
    return forecast_phrase_regex.search(forecast_table).group(2)


def find_wind_speed(forecast_table, find_full_table_data=False):
    wind_speed_regex = re.compile(
        r"""
        (<text\ class="wind-icon__val"\ fill="rgb\(.*?\)"\ text-anchor="middle"\ x="0"\ y="5">)
        # above: beginning of the container with the wind speed value; rgb varies depending on the speed
        ([0-9]*)        # wind speed
        (<\/text>)      # end of the container
        """, flags=re.VERBOSE
    )
    if find_full_table_data:
        return find_full_forecast_table_data(wind_speed_regex, forecast_table, 2, int)
    return int(wind_speed_regex.search(forecast_table).group(2))


def find_snow(forecast_table, find_full_table_data=False):
    snow_regex = re.compile(
        r"""
        (<div\ class="snow-amount".*?><span.*?>)
        # above: start of the container with snow datum
        (—?[0-9]*\.?[0-9]?)     # amount of snow, or "em dash" if no snow
        # note: for some reason, the "em dash" becomes "â€”" in the string, so this is what must be searched for
        (<\/span>)              # end of container
        """, flags=re.VERBOSE
    )
    if find_full_table_data:
        snow_table_data = find_full_forecast_table_data(snow_regex,forecast_table, 2, str)
        for i in range(len(snow_table_data)):
            if snow_table_data[i] == "—":
                snow_table_data[i] = float(0.0)
            else:
                snow_table_data[i] = float(snow_table_data[i])
        return snow_table_data

    result = snow_regex.search(forecast_table).group(2)
    if result == "—":
        return float(0.0)
    else:
        return float(result)


def find_rain(forecast_table, find_full_table_data=False):
    rain_regex = re.compile(
        r"""
        (<div\ class="rain-amount\ forecast-table__container\ forecast-table__container--rain.*?><span.*?>)
        # above: start of the container with rain data
        (—?[0-9]*\.?[0-9]?)     # amount of rain, or "em dash" if no rain
        (<\/span>)              # end of container
        """, flags=re.VERBOSE
    )
    if find_full_table_data:
        rain_table_data = find_full_forecast_table_data(rain_regex, forecast_table, 2, str)
        for i in range(len(rain_table_data)):
            if rain_table_data[i] == "—":
                rain_table_data[i] = float(0.0)
            else:
                rain_table_data[i] = float(rain_table_data[i])
        return rain_table_data

    result = rain_regex.search(forecast_table).group(2)
    if result == "—":
        return float(0.0)
    else:
        return float(result)


def find_max_temp(forecast_table, find_full_table_data=False):
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
    if find_full_table_data:
        return find_full_forecast_table_data(max_temp_regex, forecast_table, 6, int)
    return int(max_temp_regex.search(forecast_table).group(6))


def find_min_temp(forecast_table, find_full_table_data=False):
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
    if find_full_table_data:
        return find_full_forecast_table_data(min_temp_regex, forecast_table, 6, int)
    return int(min_temp_regex.search(forecast_table).group(6))


def find_chill(forecast_table, find_full_table_data=False):
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
    if find_full_table_data:
        return find_full_forecast_table_data(chill_regex, forecast_table, 6, int)
    return int(chill_regex.search(forecast_table).group(6))


def find_freezing_level(forecast_table, find_full_table_data=False):
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
    if find_full_table_data:
        return find_full_forecast_table_data(freezing_level_regex, forecast_table, 5, int)
    return int(freezing_level_regex.search(forecast_table).group(5))


def find_cloud_base(forecast_table, find_full_table_data=False):
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
    if find_full_table_data:
        cloud_base_table_data = find_full_forecast_table_data(cloud_base_regex, forecast_table, 7, str)
        for i in range(len(cloud_base_table_data)):
            if cloud_base_table_data[i] == '':
                cloud_base_table_data[i] = None
            else:
                cloud_base_table_data[i] = int(cloud_base_table_data[i])
        return cloud_base_table_data

    result = cloud_base_regex.search(forecast_table).group(7)
    if result == '':
        return None
    else:
        return int(result)


def scrape_mtn_current_weather_at_elev(mtn_name, elev):
    url = f"http://www.mountain-forecast.com/peaks/{mtn_name}/forecasts/{elev}"
    html = urlopen(url).read().decode("utf-8")
    forecast_table = find_forecast_table(html)

    df = pd.DataFrame(
        {
            'mtn_name': [format_strings(mtn_name)],
            'elevation': [elev],
            'elev_feature': [format_strings(
                find_elev_feature(mtn_name, elev, html))],
            'time_of_scrape': [get_time_of_scrape()],
            'time_issued': [find_time_issued(html)],
            'forecast_time': [approximate_forecast_time(html, forecast_table)],
            'time_name': [find_time_name(forecast_table)],
            'forecast_phrase': [format_strings(
                find_forecast_phrase(forecast_table))],
            'wind_speed': [find_wind_speed(forecast_table)],
            'snow': [find_snow(forecast_table)],
            'rain': [find_rain(forecast_table)],
            'max_temp': [find_max_temp(forecast_table)],
            'min_temp': [find_min_temp(forecast_table)],
            'chill': [find_chill(forecast_table)],
            'freezing_level': [find_freezing_level(forecast_table)],
            'cloud_base': [find_cloud_base(forecast_table)]
        }
    )
    return df


def scrape_mtn_full_forecast_table_at_elev(mtn_name, elev):
    url = f"http://www.mountain-forecast.com/peaks/{mtn_name}/forecasts/{elev}"
    html = urlopen(url).read().decode("utf-8")
    forecast_table = find_forecast_table(html)

    wind_speed_lst = find_wind_speed(forecast_table, find_full_table_data=True)
    col_len = len(wind_speed_lst)
    # TODO: add rain back 'rain': find_rain(forecast_table, find_full_table_data=True),
    df = pd.DataFrame(
        {
            'mtn_name': [format_strings(mtn_name)] * col_len,
            'elevation': [elev] * col_len,
            'elev_feature': [format_strings(
                find_elev_feature(mtn_name, elev, html))] * col_len,
            'time_of_scrape': [get_time_of_scrape()] * col_len,
            'time_issued': [find_time_issued(html)] * col_len,
            'time_name': format_strings(
                find_time_name(forecast_table, find_full_table_data=True)),
            'forecast_phrase': format_strings(
                find_forecast_phrase(forecast_table,
                                     find_full_table_data=True)),
            'wind_speed': wind_speed_lst,
            'snow': find_snow(forecast_table, find_full_table_data=True),
            'rain': find_rain(forecast_table, find_full_table_data=True),
            'max_temp': find_max_temp(forecast_table, find_full_table_data=True),
            'min_temp': find_min_temp(forecast_table, find_full_table_data=True),
            'chill': find_chill(forecast_table, find_full_table_data=True),
            'freezing_level': find_freezing_level(forecast_table, find_full_table_data=True),
            'cloud_base': find_cloud_base(forecast_table, find_full_table_data=True)
        }
    )
    return df


def format_strings(s):
    if s is None:
        return None
    if type(s) is list:
        for i in range(len(s)):
            s[i] = s[i].lower().replace('-', '_').replace(' ', '_')
        return s
    else:
        return s.lower().replace('-', '_').replace(' ', '_')


def scrape_current_weather(mtns_to_elevs):
    dfs = []
    for mtn_name in mtns_to_elevs.keys():
        for elev in mtns_to_elevs[mtn_name]:
            print(f'Scraping weather for {mtn_name} at {elev}: ', end='')
            dfs.append(scrape_mtn_current_weather_at_elev(mtn_name, elev))
            print('complete.')
    return pd.concat(dfs, ignore_index=True)
