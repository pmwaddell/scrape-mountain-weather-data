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


def find_forecast_table(html):
    forecast_table_regex = re.compile(
        fr"""
        (<div\ class="js-vis-forecast\ forecast-table"\ data-scroll-fade=""\ id="forecast-table">)  # start of the forecast table
        (.*?)                           # all contents of the forecast table
        (<div\ class="c-container">)     # beginning of the next secction
        """, flags=re.VERBOSE | re.DOTALL
    )
    return forecast_table_regex.search(html).group(2)


scrape_mtn_current_weather('Nanga-Parbat', 8125)

