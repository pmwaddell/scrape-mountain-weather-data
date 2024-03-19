import requests
import re
from bs4 import BeautifulSoup
from urllib.request import urlopen


def scrape_mtn_current_weather(mtn_name, elevation):
    url = f"http://www.mountain-forecast.com/peaks/" \
          f"{mtn_name}/forecasts/{elevation}"
    # TODO: change back to scraping form for real data
    # html = urlopen(url).read().decode("utf-8")
    html = open('np_html.txt', 'r').read()
    forecast_table = find_forecast_table(html)
    print(find_max_temp(forecast_table))
    print(find_min_temp(forecast_table))


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


def find_max_temp(forecast_table):
    max_temp_regex = re.compile(
        fr"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch\ forecast-table__container--max)
        # above: start of the container with the max temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]")               # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?.[0-9]?")?   # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # max temperature datum
        (<\/div>)                                       # end of the cell
        """, flags=re.VERBOSE
    )
    return max_temp_regex.search(forecast_table).group(6)


def find_min_temp(forecast_table):
    min_temp_regex = re.compile(
        fr"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch\ forecast-table__container--min)
        # above: start of the container with the max temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]")               # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?.[0-9]?")?   # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # min temperature datum
        (<\/div>)                                       # end of the cell
        """, flags=re.VERBOSE
    )
    return min_temp_regex.search(forecast_table).group(6)


scrape_mtn_current_weather('Nanga-Parbat', 8125)

