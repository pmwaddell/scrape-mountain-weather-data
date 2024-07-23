#!/usr/bin/env python3
"""
A script which scrapes weather forecast data from mountain-forecast.com.

Given a map of mountain names to elevations, data from mountain-forecast.com is
scraped and compiled into a Dataframe, containing temperature, wind speed,
rain, snow data and more. Both the current conditions on the mountain and
forecasts of future weather can be obtained.
"""
__author__ = "Peter Waddell"
__copyright__ = "Copyright 2024"
__credits__ = ["Peter Waddell"]
__version__ = "0.0.1"
__date__ = "2024/07/22"
__maintainer__ = "Peter Waddell"
__email__ = "pmwaddell9@gmail.com"
__status__ = "Prototype"

import re
import time
import pandas as pd
from urllib.request import urlopen


def find_forecast_table(html):
    """
    Extracts the html corresponding to the forecast table out of the html of a
    page from mountain-forecast.com.

    Parameters
    ----------
    html : str
        When true, only the current weather data is scraped, so no forecasted
        data is included.

    Returns
    -------
    str
        String containing the html for the forecast table.
    """
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
    """
    Searches the full forecast table for one kind of data, given a regular
    expression.

    Parameters
    ----------
    regex : str
        Regular expression used to search the table.

    forecast_table : str
        String containing the html for the forecast table.

    data_group : int
        Indicates which "group" of the Match contains the desired data, based
        on the regular expression.

    data_type
        Class of the data being extracted from the table, used to cast it from
        the string which the Match returns.

    Returns
    -------
    List
        List containing the sequence of values for the specified type of data,
        as they appear in the table left-to-right.
    """
    findall_result = re.findall(regex, forecast_table)
    all_table_values = []
    for i in range(len(findall_result)):
        all_table_values.append(data_type(findall_result[i][data_group - 1]))
    return all_table_values


def find_elev_feature(mtn_name, elev, html):
    """
    On mountain-forecast.com, certain elevations are given designations. The
    lowest is called the "base" and the highest is the "peak". In addition, in
    some cases a middle elevation is also called "mid". I refer to these as
    "elevation features", and this function finds the feature on the given
    page, if there is one.

    Parameters
    ----------
    mtn_name : str
        String of the name of the mountain, as it appears in the url on
        mountain-forecast.com.

    elev : int
        Represents the elevation on the mountain, based on the pages on
        mountain-forecast.com.

    html : str
        String containing the html for the page on mountain-forecast.com

    Returns
    -------
    str
        String of the elevation feature ("base", "mid", or "peak") if it is
        present for this mountain at the given elevation, None otherwise.
    """
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
    """
    Gets the time of scrape, aka the current time.

    Returns
    -------
    Timestamp
        Current timestamp.
    """
    return pd.Timestamp.now().round('min')


def find_time_issued(html):
    """
    On mountain-forecast.com, each forecast table has a time when it is said to
    have been issued. This function translates this time into the proper time
    and date.

    Parameters
    ----------
    html : str
        String containing the html of the page on mountain-forecast.com.

    Returns
    -------
    Datetime
        Datetime corresponding to the time the forecast table was issued.
    """
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
    """
    In the forecast table, the first (i.e. leftmost) cell contains the current,
    or "actual", data (meaning, presumably it represents the weather on the
    mountain at that time) and the remainder are forecasts for times in the
    future. So, this function returns a list of strings with length equal to
    the number of cells in the table. The first is 'actual' and the remainder
    are 'forecast', so they correspond to the cells in the table.

    Parameters
    ----------
    l : int
        Equal to the number of cells in a row of the forecast table.

    Returns
    -------
    List
        List of strings with length l, the first being 'actual' and the
        remainder being 'forecast', corresponding to the cells in the table.
    """
    return ['actual'] + ['forecast'] * (l - 1)


def approximate_forecast_times(html, forecast_table):
    """
    On mountain-forecast.com, each date is subdivided into "AM", "PM" and
    "night". For the purposes of this study, I have arbitrarily pegged these
    "time names" to 7:00, 15:00 and 23:00 respectively. This function gives the
    sequences of these times, derived from the sequence of dates and time names
    in the forecast table.

    Parameters
    ----------
    html : str
        String of the html of the page on mountain-forecast.com.

    forecast_table : str
        String of the html for the forecast table on mountain-forecast.com

    Returns
    -------
    List
        List of Datetimes corresponding to the forecasts in the table, based on
        the date and "time name".
    """
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
            forecast_dates[date_index], time_name
        ))
        # To match the "time names" and scraped dates up correctly, since
        # there are up to three "time names" for each date, the date must
        # advanced after each "night" appears.
        if time_name == 'night':
            date_index += 1
    return result


def convert_table_forecast_time_to_datetime(forecast_date, time_name):
    """
    Considering that each day in the forecast is subdivided vaguely into three
    ("AM", "PM", and "night"), for the purposes of this investigation I have
    arbitrarily pegged each of these to a specific time: AM is 7:00, PM is
    15:00, and night is 23:00. This function gives Timestamp corresponding to
    the given time name.

    Parameters
    ----------
    forecast_date : str
        String representing the date of the forecast.

    time_name : str
        The "time name" of the forecast ("AM", "PM" or "night).

    Returns
    -------
    Datetime
        Approximated datetime of the forecast.
    """
    if time_name == 'AM':
        forecast_hour = '07'
    elif time_name == 'PM':
        forecast_hour = '15'
    elif time_name == 'night':
        forecast_hour = '23'
    else:
        forecast_hour = '12'

    timestamp_str = f'{forecast_date} {forecast_hour}'
    return pd.to_datetime(timestamp_str, format='%Y-%m-%d %H')


def find_time_names(forecast_table):
    """
    The forecast tables on mountain-forecast.com are divided by days, which
    themselves are subdivided into "AM", "PM", and "night", which I refer to as
    "forecast time names". This function gives the sequence of time names in
    the table.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the "time names" from the forecast table (i.e., "AM",
        "PM" or "night").
    """
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
    """
    Each forecast in the table has a short phrase that describes the weather
    conditions briefly, i.e. 'clear', 'some clouds', 'mod. snow', etc. This
    function gives the sequence of forecast phrases in the table.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the forecast phrases from the forecast table.
    """
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
    """
    This function gives the sequence of forecasted wind speeds in the table,
    in km/h.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the forecasted wind speeds from the forecast table.
    """
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
    """
    This function gives the sequence of snow forecasts in the table, in cm.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the snow forecasts from the forecast table.
    """
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
    """
    This function gives the sequence of rain forecasts in the table, in mm.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the rain forecasts from the forecast table.
    """
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
    """
    This function gives the sequence of max. temp. forecasts in the table, in C.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the max. temp. forecasts from the forecast table.
    """
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
    """
    This function gives the sequence of min. temp. forecasts in the table, in C.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the min. temp. forecasts from the forecast table.
    """
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
    """
    This function gives the sequence of chill forecasts in the table, in C.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the chill forecasts from the forecast table.
    """
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
    """
    This function gives the sequence of freezing level forecasts in the table,
    in m.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the freezing level forecasts from the forecast table.
    """
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
    """
    This function gives the sequence of cloud base forecasts in the table,
    in m.

    Parameters
    ----------
    forecast_table : str
        String containing the html of the forecast table.

    Returns
    -------
    List
        List containing the cloud base forecasts from the forecast table.
    """
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
    """
    Scrapes data from mountain-forecast.com to find forecast data from a
    specific page, i.e. a mountain at one elevation.

    Parameters
    ----------
    mtn_name : str
        Name of the desired mountain, formatted the way it is in the url
        on mountain-forecast.com.

    elev : int
        Indicates which elevation should be scraped, based on the available
        data from mountain-forecast.com.

    Returns
    -------
    Dataframe
        Dataframe containing weather forecast data from the mountain at this
        elevation.
    """
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
    """
    Gets the current, "actual" weather for a particular mountain at a
    particular elevation from mountain-forecast.com.

    Parameters
    ----------
    mtn_name : str
        String of the name of the desired mountain, formatted according to how
        it appears in the url on mountain-forecast.com.

    elev : int
        Indicates the desired elevation for the scrape, based on the available
        options on mountain-forecast.com.

    Returns
    -------
    Dataframe
        Dataframe containing the current, "actual" weather for the given
        mountain at the given elevation.
    """
    return scrape_mtn_full_forecast_table_at_elev(mtn_name, elev).iloc[:1]


def format_strings(s):
    """
    Formats strings for the dataframe.

    Parameters
    ----------
    s : str
        String to be formatted.

    Returns
    -------
    str
        Formatted string.
    """
    if s is None:
        return None
    if type(s) is list:
        for i in range(len(s)):
            s[i] = s[i].lower().replace('-', '_').replace(' ', '_')
        return s
    else:
        return s.lower().replace('-', '_').replace(' ', '_')


def scrape_weather(mtns_to_elevs, current_only=False):
    """
    Scrapes data from mountain-forecast.com to find forecast data for the
    specified elevations of the specified mountains. Both current weather data
    and forecasted data can be scraped.

    Parameters
    ----------
    mtns_to_elevs : dict
        Dictionary mapping the names (entered the way they appear in the urls
        for their pages on mountain-forecast.com) to elevations, indicating
        which pages will be scraped.

    current_only : bool
        When true, only the current weather data is scraped, so no forecasted
        data is included.

    Returns
    -------
    Dataframe
        Dataframe containing columns: mtn_name, timeanddate_url_end, time_zone,
        UTC_diff, scrape_date, sunrise_time, and sunset_time.
    """
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
