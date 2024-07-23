if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data(*args, **kwargs):
    """
    Scrape sunrise and sunset data from timeanddate.com.
    """
    from scrape_sun_data import find_sun_data
    return find_sun_data('sun_data/mtns_for_timeanddate.csv')


@test
def test_output(output, *args) -> None:
    """
    Checks that the output is not None
    """
    assert output is not None, 'The output is undefined'
