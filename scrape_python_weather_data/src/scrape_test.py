import requests
import re
import pandas as pd
import openpyxl
from bs4 import BeautifulSoup
from urllib.request import urlopen


def find_forecast_table(html):
    forecast_table_regex = re.compile(
        fr"""
        (<div\ class="js-vis-forecast\ forecast-table"\ data-scroll-fade=""\ id="forecast-table">)  
        # above: start of the forecast table
        (.*?)                           # all contents of the forecast table
        (<div\ class="c-container">)    # beginning of the next secction
        """, flags=re.VERBOSE | re.DOTALL
    )
    return forecast_table_regex.search(html).group(2)


    # TODO: ADD WAY TO FIND TIMES, timestamps for pandas, whatever, etc.


def find_forecast_phrase(forecast_table):
    forecast_phrase_regex = re.compile(
        fr"""
        (<span\ class="forecast-table__phrase\ forecast-table__phrase--en">)
        # above: start of the container with the forecast phrase
        (.*?)       # forecast phrase
        (<\/span>)  # end of the container
        """, flags=re.VERBOSE
    )
    return forecast_phrase_regex.search(forecast_table).group(2)


def find_wind_speed(forecast_table):
    wind_speed_regex = re.compile(
        fr"""
        (<text\ class="wind-icon__val"\ fill="rgb\(.*?\)"\ text-anchor="middle"\ x="0"\ y="5">)
        # above: beginning of the container with the wind speed value; rgb varies depending on the speed
        ([0-9]*)    # wind speed
        (<\/text>)  # end of the container
        """, flags=re.VERBOSE
    )
    return wind_speed_regex.search(forecast_table).group(2)


def find_snow(forecast_table):
    snow_regex = re.compile(
        fr"""
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
        fr"""
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
        fr"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch\ forecast-table__container--max)
        # above: start of the container with the max temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]")              # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?\.[0-9]?")?  # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # max temperature datum
        (<\/div>)                                       # end of the container
        """, flags=re.VERBOSE
    )
    return max_temp_regex.search(forecast_table).group(6)


def find_min_temp(forecast_table):
    min_temp_regex = re.compile(
        fr"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch\ forecast-table__container--min)
        # above: start of the container with the max temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]")              # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?\.[0-9]?")?  # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # min temperature datum
        (<\/div>)                                       # end of the container
        """, flags=re.VERBOSE
    )
    return min_temp_regex.search(forecast_table).group(6)


def find_chill(forecast_table):
    chill_regex = re.compile(
        fr"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch)
        # above: start of the container with the chill temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]")              # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?\.[0-9]?")?  # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # chill temperature datum
        (<\/div>)                                       # end of the container
        """, flags=re.VERBOSE
    )
    return chill_regex.search(forecast_table).group(6)


def find_freezing_level(forecast_table):
    freezing_level_regex = re.compile(
        fr"""
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
        fr"""
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


def scrape_mtn_current_weather(mtn_name, elevation):
    url = f"http://www.mountain-forecast.com/peaks/" \
          f"{mtn_name}/forecasts/{elevation}"
    # TODO: change back to scraping form for real data
    html = urlopen(url).read().decode("utf-8")
    # html = open('np_html.txt', 'r').read()
    forecast_table = find_forecast_table(html)

    df = pd.DataFrame(
        {
            'mtn_name': [mtn_name],
            'elevation': [elevation],
            'forecast_phrase': [find_forecast_phrase(forecast_table)],
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
    df.to_excel(f'{mtn_name}_{elevation}m.xlsx')
    return df


df1 = scrape_mtn_current_weather('Nanga-Parbat', 8125)
df2 = scrape_mtn_current_weather('Nanga-Parbat', 7500)
df3 = pd.concat([df1, df2])
df3.to_excel(f'FINAL.xlsx')

