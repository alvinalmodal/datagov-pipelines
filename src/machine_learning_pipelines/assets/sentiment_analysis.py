from dagster import AssetExecutionContext, asset
import pandas as pd
from pandas import DataFrame
import emoji
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from pydantic import BaseModel, ConfigDict
from typing import Any, Optional


class ModelTrainingResult(BaseModel):
    x_train: Optional[Any]
    x_test: Optional[Any]
    y_train: Optional[Any]
    y_test: Optional[Any]
    df: Optional[DataFrame]
    model: Optional[Pipeline]

    model_config = ConfigDict(arbitrary_types_allowed=True)


def preprocess_text(text):
    return emoji.demojize(str(text), delimiters=(" ", " ")).strip()


@asset
def sentiment_data(context: AssetExecutionContext) -> DataFrame:
    context.log.info('Extraction of data')
    df = pd.read_csv("/app/src/data/sentimentdataset.csv")
    return df


@asset
def data_transformation(context: AssetExecutionContext, sentiment_data: DataFrame) -> DataFrame:
    context.log.info('Transformation of data')
    sentiment_data["CleanText"] = sentiment_data["Text"].apply(preprocess_text)
    sentiment_data["Sentiment"] = sentiment_data["Sentiment"].str.strip()
    context.log.info(sentiment_data)
    return sentiment_data

@asset
def data_transformation_with_emoji(context: AssetExecutionContext, sentiment_data: DataFrame) -> DataFrame:
    context.log.info('Transformation of data')
    sentiment_data["CleanText"] = sentiment_data["Text"].apply(preprocess_text)
    sentiment_data["Sentiment"] = sentiment_data["Sentiment"].str.strip()
    context.log.info(sentiment_data)
    return sentiment_data


@asset
def model_training(context: AssetExecutionContext, data_transformation: DataFrame) -> ModelTrainingResult:
    context.log.info('Training of models')
    X = data_transformation["CleanText"]
    y = data_transformation["Sentiment"]

    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
        ("clf", LogisticRegression(max_iter=1000))
    ])

    model.fit(x_train, y_train)

    model_traning_result = ModelTrainingResult(x_train=x_train, x_test=x_test, y_train=y_train, y_test=y_test,
                                               model=model, df=data_transformation)

    return model_traning_result


@asset
def evaluate_sentiment_data(context: AssetExecutionContext, model_training: ModelTrainingResult):
    context.log.info('Evaluation of models')
    y_pred = model_training.model.predict(model_training.x_test)
    report = classification_report(model_training.y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).transpose()
    context.log.info(report_df)