from dagster import ScheduleDefinition

from data_gov_pipelines.job.customer_order_workflow import customer_order_workflow

customer_order_workflow_schedule = ScheduleDefinition(
    job=customer_order_workflow,  # <-- reference to your Job
    cron_schedule="* * * * *",  # every minute
    execution_timezone="Asia/Manila",  # optional but recommended
    name="customer_order_workflow_schedule",
)