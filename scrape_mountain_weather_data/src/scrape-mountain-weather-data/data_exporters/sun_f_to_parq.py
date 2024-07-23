from mage_ai.io.file import FileIO
from pandas import DataFrame

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_file(df: DataFrame, **kwargs) -> None:
    """
    Saves the final sunrise and sunset data as a local parquet file.
    """
    df.to_parquet('forecast_data/sun_and_time_zone_data.parquet')
    print('Saved as sun_and_time_zone_data.parquet')
