import dagster as dg
from data_gov_pipelines.assets.border_crossing import border_crossing_csv

defs = dg.Definitions(
  assets=[border_crossing_csv],
  resources={},
)