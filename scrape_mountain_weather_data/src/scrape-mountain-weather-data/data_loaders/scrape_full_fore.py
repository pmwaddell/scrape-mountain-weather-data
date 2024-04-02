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
            'Mount-Everest': [8850, 8000, 7000, 6000, 5000, 4000],
            'K2': [8612, 8000, 7000, 6000, 5000, 4000],
            'Kangchenjunga': [8586, 8000, 7000, 6000, 5000, 4000, 3000, 2000],
            'Lhotse': [8516, 8000, 7000, 6000, 5000, 4000],
            'Makalu': [8462, 7500, 6500, 4500, 3500, 2500],
            'Cho-Oyu': [8201, 7500, 6500, 5500, 4500],
            'Dhaulagiri': [8167, 7500, 6500, 5500, 4500, 3500, 2500, 1500],
            'Manaslu': [8156, 7500, 6500, 5500, 4500, 3500, 2500, 1500],
            'Nanga-Parbat': [8125, 7500, 6500, 5500, 4500, 3500, 2500],
            'Annapurna': [8091, 7500, 6500, 5500, 4500, 3500, 2500],
            'Gasherbrum': [8068, 7500, 6500, 5500, 4500],
            'Broad-Peak': [8047, 7500, 6500, 5500, 4500],
            'Gasherbrum-II': [8035, 7500, 6500, 5500, 4500],
            'Shisha-Pangma': [8013, 7500, 6500, 5500, 4500],
            'Ama-Dablam': [6856, 6000, 5000, 4000, 3000],
            'Imja-Tse': [6183, 5500, 4500, 3500],
            'Mount-McKinley': [6194, 5500, 4500, 3500, 2500, 1500, 500],
            'Mont-Blanc': [4807, 4000, 3000, 2000, 1000],
            'Vinson-Massif': [4897, 4000, 3000, 2000, 1000, 0],
            'Mount-Washington-2': [1917, 1000],
            'Flattop': [1067, 500],
            'Mount-Whitney': [4418, 3500, 2500, 1500],
            'Mount-Mitchell': [2037, 1500, 500]
        }
    )


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
