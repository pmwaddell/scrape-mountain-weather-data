import re
import pandas as pd
from urllib.request import urlopen
from scrape_mountain_weather_data import scrape_weather


scrape_weather(
    {
        'Nanga-Parbat': [8125, 7500, 6500, 5500, 4500, 3500, 2500],
        'Mount-McKinley': [6194, 5500, 4500, 3500, 2500, 1500, 500],
        'Mont-Blanc': [4807, 4000, 3000, 2000, 1000],
        'Vinson-Massif': [4897, 4000, 3000, 2000, 1000, 0],
        'Mount-Washington-2': [1917, 1000],
        'Flattop': [1067, 500]
    }
).to_excel('tstt.xlsx')
# scrape_mtn_current_weather_at_elev('Nanga-Parbat', 8125).to_excel('current-weather.xlsx')
