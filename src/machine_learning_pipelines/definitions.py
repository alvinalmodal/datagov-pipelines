import dagster as dg

from machine_learning_pipelines.assets.sentiment_analysis import sentiment_data, data_transformation, model_training, \
    evaluate_sentiment_data, data_transformation_with_emoji

defs = dg.Definitions(
    assets=[sentiment_data, data_transformation, model_training, evaluate_sentiment_data,
            data_transformation_with_emoji],
    resources={},
)
