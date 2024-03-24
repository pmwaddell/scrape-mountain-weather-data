import re
import pandas as pd
from urllib.request import urlopen
from scrape_mountain_weather_data import find_forecast_table
from scrape_mountain_weather_data import scrape_mtn_full_forecast_table_at_elev, scrape_mtn_current_weather_at_elev


scrape_mtn_full_forecast_table_at_elev('Nanga-Parbat', 8125).to_excel('full-forecast.xlsx')
scrape_mtn_current_weather_at_elev('Nanga-Parbat', 8125).to_excel('current-weather.xlsx')
