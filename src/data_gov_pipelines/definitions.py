import dagster as dg
from data_gov_pipelines.assets.border_crossing import bronze_borders_crossing, silver_borders_crossing
from data_gov_pipelines.job.customer_order_workflow import customer_order_workflow
from data_gov_pipelines.schedule.customer_order_workflow_schedule import customer_order_workflow_schedule

defs = dg.Definitions(
    assets=[bronze_borders_crossing, silver_borders_crossing],
    schedules=[customer_order_workflow_schedule],
    resources={},
)
