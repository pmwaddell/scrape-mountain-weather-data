if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data(*args, **kwargs):
    """
    Scrapes only the current (aka "actual") weather data from weather-forecast.com.
    """
    from scrape_mountain_weather_data import scrape_weather
    return scrape_weather(
        'forecast_data/mtns_elevs_for_scraping.json', 
        current_only=True
    )


@test
def test_output(output, *args) -> None:
    """
    Checks that the output is not None.
    """
    assert output is not None, 'The output is undefined'
