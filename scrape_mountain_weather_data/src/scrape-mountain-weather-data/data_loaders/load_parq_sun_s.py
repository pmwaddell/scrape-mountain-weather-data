from mage_ai.io.file import FileIO
if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_file(*args, **kwargs):
    """
    Load the backed up sunrise/sunset staging data from its parquet file.
    """
    filepath = 'forecast_data/sun_and_time_zone_staging.parquet'

    return FileIO().load(filepath)


@test
def test_output(output, *args) -> None:
    """
    Checks that the output is not None.
    """
    assert output is not None, 'The output is undefined'
