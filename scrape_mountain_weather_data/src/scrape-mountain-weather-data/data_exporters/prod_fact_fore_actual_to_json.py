from mage_ai.io.file import FileIO
from pandas import DataFrame

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_file(df: DataFrame, **kwargs) -> None:
    """
    Saves dbt production table fact_forecasts_actual as a local JSON file.
    """
    df.to_json('json_for_tableau/fact_forecasts_actual.json')
    print('Saved as fact_forecasts_actual.json')
