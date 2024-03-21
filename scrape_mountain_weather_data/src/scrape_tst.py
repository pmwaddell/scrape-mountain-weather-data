import openpyxl
from scrape_mountain_weather_data import scrape_current_weather


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
