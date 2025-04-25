import dagster as dg
from job_search_pipelines.assets.job_searches import job_searches

defs = dg.Definitions(
  assets=[job_searches],
  resources={},
)