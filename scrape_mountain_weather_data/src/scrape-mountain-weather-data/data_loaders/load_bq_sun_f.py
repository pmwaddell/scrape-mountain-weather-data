from mage_ai.settings.repo import get_repo_path
from mage_ai.io.bigquery import BigQuery
from mage_ai.io.config import ConfigFileLoader
from os import path
if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_big_query(*args, **kwargs):
    """
    Loads final (i.e., upserted) sunrise and sunset data from Bigquery.
    """
    # For some reason, the interval data type gives problems when trying to save it as a parquet.
    # Therefore, I have decided to wrap the whole thing by converting/deconverting it to string.
    query = 'SELECT mtn_name, timeanddate_url_end, time_zone, utc_diff, scrape_date, sunrise_time, sunset_time, CAST(total_daylight AS string) AS total_daylight_str FROM `mountain-weather-data.sun_data.sun_and_time_zone_data`'
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'

    return BigQuery.with_config(ConfigFileLoader(config_path, config_profile)).load(query)


@test
def test_output(output, *args) -> None:
    """
    Checks that the output is not None.
    """
    assert output is not None, 'The output is undefined'
