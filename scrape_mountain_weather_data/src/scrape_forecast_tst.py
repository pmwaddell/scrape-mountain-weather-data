import re
import pandas as pd
from urllib.request import urlopen
from scrape_mountain_weather_data import find_forecast_table


def find_max_temp(forecast_table):
    max_temp_regex = re.compile(
        fr"""
        (<div\ class="forecast-table__container\ forecast-table__container--stretch\ forecast-table__container--max)
        # above: start of the container with the max temp. datum
        (\ forecast-table__container--border)?          # this bit of text appears only when the cell is on the edge
        (\ temp-value\ temp-value--[0-9]*")             # temp-value-- seems to be followed by a single integer
        (\ data-value="-?[0-9]?[0-9]?[0-9]?\.[0-9]?")?  # I believe this will always occur for our use cases but added ? just in case
        (>)                                             # I've separated the above group out in case data is absent from the cell
        (-?[0-9]?[0-9]?[0-9]?)                          # max temperature datum
        (<\/div>)                                       # end of the container
        (.*?)
        """, flags=re.VERBOSE
    )
    # TODO: probably split this part off as its own function
    # take an argument like full_table with default as False
    findall_result = re.findall(max_temp_regex, forecast_table)
    all_table_values = []
    for i in range(len((findall_result))):
        all_table_values.append(int(findall_result[i][5]))
    return all_table_values


def find_wind_speed(forecast_table):
    wind_speed_regex = re.compile(
        r"""
        (<text\ class="wind-icon__val"\ fill="rgb\(.*?\)"\ text-anchor="middle"\ x="0"\ y="5">)
        # above: beginning of the container with the wind speed value; rgb varies depending on the speed
        ([0-9]*)        # wind speed
        (<\/text>)      # end of the container
        """, flags=re.VERBOSE
    )
    findall_result = re.findall(wind_speed_regex, forecast_table)
    all_table_values = []
    for i in range(len((findall_result))):
        all_table_values.append(int(findall_result[i][1]))
    return all_table_values


# url = f"http://www.mountain-forecast.com/peaks/Nanga-Parbat/forecasts/7500"
# html = urlopen(url).read().decode("utf-8")
# forecast_table = find_forecast_table(html)
#
# wind_speed_lst = find_wind_speed(forecast_table)
# cols = {
#     'mtn': ['Nanga-Parbat'] * len(wind_speed_lst),
#     'max_temp': find_max_temp(forecast_table),
#     'wind_speed': wind_speed_lst
# }
# df = pd.DataFrame(cols)
#
# print(df)

from scrape_mountain_weather_data import scrape_mtn_full_forecast_table_at_elev

scrape_mtn_full_forecast_table_at_elev('Nanga-Parbat', 8125).to_excel('full-forecast.xlsx')
