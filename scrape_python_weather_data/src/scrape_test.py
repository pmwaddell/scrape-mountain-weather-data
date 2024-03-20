import re
import pandas as pd
import openpyxl
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
    if result_split[1] == 'pm':
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
    forecast_date_regex = re.compile(
        fr"""
        (<td\ class="forecast-table-days__cell\ forecast-table__cell\ forecast-table__cell--day-even"\ colspan="[0-9]*"\ data-column-head=""\ data-date="[0-9][0-9][0-9][0-9]-[0-9][0-9]-)
        ([0-9][0-9])
        """, flags=re.VERBOSE
    )
    forecast_date = forecast_date_regex.search(forecast_table).group(2)
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

    timestamp_str = \
        f'{forecast_year}-{forecast_month}-{forecast_date} {forecast_hour}'
    return pd.to_datetime(timestamp_str, format='%Y-%m-%d %H')


def find_time_name(forecast_table):
    time_name_regex = re.compile(
        r"""
        (forecast-table__time"><span\ class="en">)  
        # above: text that comes right before the "time name"
        ([a-zA-Z]*)     # "time name" (i.e., "AM", "PM" or "night")
        (<\/span>)      # end of the container
        """, flags=re.VERBOSE
    )
    return time_name_regex.search(forecast_table).group(2)


def find_forecast_phrase(forecast_table):
    forecast_phrase_regex = re.compile(
        r"""
        (<span\ class="forecast-table__phrase\ forecast-table__phrase--en">)
        # above: start of the container with the forecast phrase
        (.*?)           # forecast phrase
        (<\/span>)      # end of the container
        """, flags=re.VERBOSE
    )
    return forecast_phrase_regex.search(forecast_table).group(2)


def find_wind_speed(forecast_table):
    wind_speed_regex = re.compile(
        r"""
        (<text\ class="wind-icon__val"\ fill="rgb\(.*?\)"\ text-anchor="middle"\ x="0"\ y="5">)
        # above: beginning of the container with the wind speed value; rgb varies depending on the speed
        ([0-9]*)        # wind speed
        (<\/text>)      # end of the container
        """, flags=re.VERBOSE
    )
    return wind_speed_regex.search(forecast_table).group(2)


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
    result = snow_regex.search(forecast_table).group(2)
    if result == "—":
        return 0
    else:
        return result


def find_rain(forecast_table):
    rain_regex = re.compile(
        r"""
        (<div\ class="rain-amount\ forecast-table__container\ forecast-table__container--rain".*?><span.*?>)
        # above: start of the container with rain datum
        (—?[0-9]*\.?[0-9]?)     # amount of rain, or "em dash" if no rain
        (<\/span>)              # end of container
        """, flags=re.VERBOSE
    )
    result = rain_regex.search(forecast_table).group(2)
    if result == "—":
        return 0
    else:
        return result


def find_max_temp(forecast_table):
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
    return max_temp_regex.search(forecast_table).group(6)


def find_min_temp(forecast_table):
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
    return min_temp_regex.search(forecast_table).group(6)


def find_chill(forecast_table):
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
    return chill_regex.search(forecast_table).group(6)


def find_freezing_level(forecast_table):
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
    return freezing_level_regex.search(forecast_table).group(5)


def find_cloud_base(forecast_table):
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
    result = cloud_base_regex.search(forecast_table).group(7)
    if result == '':
        return None
    else:
        return result


def scrape_mtn_current_weather_at_elev(mtn_name, elev):
    url = f"http://www.mountain-forecast.com/peaks/" \
          f"{mtn_name}/forecasts/{elev}"
    html = urlopen(url).read().decode("utf-8")
    forecast_table = find_forecast_table(html)

    df = pd.DataFrame(
        {
            'mtn_name': [format_string(mtn_name)],
            'elevation': [elev],
            'elev_feature': [format_string(find_elev_feature(mtn_name, elev, html))],
            'time_of_scrape': [get_time_of_scrape()],
            'time_issued': [find_time_issued(html)],
            'forecast_time': [approximate_forecast_time(html, forecast_table)],
            'time_name': [find_time_name(forecast_table)],
            'forecast_phrase': [format_string(find_forecast_phrase(forecast_table))],
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


def format_string(s):
    if s is None:
        return None
    else:
        return s.lower().replace('-', '_').replace(' ', '_')


def scrape_current_weather(mtns_to_elevs):
    dfs = []
    for mtn_name in mtns_to_elevs.keys():
        for elev in mtns_to_elevs[mtn_name]:
            dfs.append(scrape_mtn_current_weather_at_elev(mtn_name, elev))
            print(f'{mtn_name} at {elev}: complete.')
    return pd.concat(dfs, ignore_index=True)


result_df = scrape_current_weather(
    {
        'Nanga-Parbat': [8125, 7500, 6500, 5500, 4500, 3500, 2500],
        'Dhaulagiri': [8167, 7500, 6500, 5500, 4500, 3500, 2500, 1500]
    }
)
# result_df = scrape_current_weather(
#     {
#         'Nanga-Parbat': [8125]
#     }
# )
result_df.to_excel(f'FINAL.xlsx')
