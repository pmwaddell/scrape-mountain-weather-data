if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data(*args, **kwargs):
    """
    Template code for loading data from any source.

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    from scrape_mountain_weather_data import scrape_weather
    return scrape_weather(
        {
            'Nanga-Parbat': [8125, 7500, 6500, 5500, 4500, 3500, 2500],
            'Mount-McKinley': [6194, 5500, 4500, 3500, 2500, 1500, 500],
            'Mont-Blanc': [4807, 4000, 3000, 2000, 1000],
            'Vinson-Massif': [4897, 4000, 3000, 2000, 1000, 0],
            'Mount-Washington-2': [1917, 1000],
            'Flattop': [1067, 500]
        }
    )


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
