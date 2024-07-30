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
    Loads dbt production table fact_forecasts_actual from Bigquery.
    """
    # Note that total_daylight is cast as a string because the interval
    # data type doesn't play well with the loader here.

    # Also, for some reason running this block on its own appears to fail,
    # but running it by calling "Execute w all upstream blocks" from the
    # exporter appears to work. 
    query = """
    SELECT 
    fact_forecasts_actual_key,
    mtn_name,
    region_group_key,
    mtn_range,
    subrange,
    latitude,
    longitude,
    geo_dimension,
    time_zone,
    utc_diff,
    sunrise_time,
    sunset_time,
    CAST(total_daylight AS STRING) AS total_daylight_str,
    wiki_peak_elevation,
    elevation_rank,
    prominence,
    prominence_rank,
    isolation,
    isolation_rank,
    first_ascent,
    ascents,
    fatalities,
    fatalities_per_summit_rate,
    elevation,
    elevation_feature,
    local_time_of_forecast,
    forecast_time_name,
    wind_speed,
    snow,
    rain,
    max_temp,
    min_temp,
    chill,
    freezing_level,
    cloud_base,
    air_pressure,
    p_o2,
    in_death_zone
    FROM `mountain-weather-data.prod.fact_forecasts_actual`
    """
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'

    return BigQuery.with_config(ConfigFileLoader(config_path, config_profile)).load(query)


@test
def test_output(output, *args) -> None:
    """
    Checks that the output is not None.
    """
    assert output is not None, 'The output is undefined'
