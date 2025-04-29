from dagster import op, job
from dagster import OpExecutionContext


@op
def take_customer_order(context: OpExecutionContext) -> str:
    context.log.info("This will simulate taking of customer order")
    return "Customer Order"


@op
def give_customer_order_to_kitchen(context: OpExecutionContext, customer_order: str) -> str:
    context.log.info("This will simulate giving of order to the kitchen and meal preparation")
    return "Kitchen Order"


@op
def serve_customer_order(context: OpExecutionContext, actual_order: str):
    context.log.info("This will simulate serving of order to the customer")
    context.log.info("This will simulate serving customer order")


@job
def customer_order_workflow():
    customer_order = take_customer_order()
    actual_order = give_customer_order_to_kitchen(customer_order)
    serve_customer_order(actual_order)
