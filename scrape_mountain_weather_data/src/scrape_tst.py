import openpyxl
from scrape_mountain_weather_data import scrape_current_weather


result_df = scrape_current_weather(
    {
        'Nanga-Parbat': [8125, 7500, 6500, 5500, 4500, 3500, 2500],
        'Mount-McKinley': [6194, 5500, 4500, 3500, 2500, 1500, 500],
        'Mont-Blanc': [4807, 4000, 3000, 2000, 1000],
        'Vinson-Massif': [4897, 4000, 3000, 2000, 1000, 0],
        'Mount-Washington-2': [1917, 1000],
        'Flattop': [1067, 500]
    }
)
# result_df = scrape_current_weather(
#     {
#         'Nanga-Parbat': [8125]
#     }
# )
result_df.to_excel(f'../data/FINAL.xlsx')


# TODO: try writing to parquet? since for some reason mage seems to need to do that and it is giving us issues
# I expect that I may need to explicitly set the schema or something
