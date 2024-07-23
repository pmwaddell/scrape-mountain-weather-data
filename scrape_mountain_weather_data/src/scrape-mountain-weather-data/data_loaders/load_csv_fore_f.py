from mage_ai.io.file import FileIO
if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_file(*args, **kwargs):
    """
    Loads the backed up final forecast data from the csv file.
    """
    filepath = 'forecast_data/scraped_forecasts_final.csv'

    return FileIO().load(filepath)


@test
def test_output(output, *args) -> None:
    """
    Checks that the output is not None.
    """
    assert output is not None, 'The output is undefined'
