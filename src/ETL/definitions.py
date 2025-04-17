import dagster as dg
from ETL.assets.border_crossing import border_crossing_csv

defs = dg.Definitions(
  assets=[border_crossing_csv],
  resources={},
)