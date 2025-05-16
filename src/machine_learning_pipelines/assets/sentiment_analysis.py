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
from dagster import asset, AutoMaterializePolicy

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def classify_sentiment(text: str) -> str:
    scores = analyzer.polarity_scores(text)
    if scores['compound'] >= 0.05:
        return "Positive"
    elif scores['compound'] <= -0.05:
        return "Negative"
    else:
        return "Neutral"


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


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def data_transformation(context: AssetExecutionContext, sentiment_data: DataFrame) -> DataFrame:
    context.log.info('Transformation of data')
    sentiment_data["CleanText"] = sentiment_data["Text"].apply(preprocess_text)
    sentiment_data["Sentiment"] = sentiment_data["Sentiment"].str.strip()
    sentiment_data["categorized_sentiment"] = sentiment_data["Sentiment"].apply(classify_sentiment)
    sentiment_clone = sentiment_data[["Text", "Sentiment","categorized_sentiment"]].copy()
    sentiment_clone.to_csv("/app/src/data/sentiment_categorized.csv", index=False)
    context.log.info(sentiment_data)
    return sentiment_data

@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def data_transformation_with_emoji(context: AssetExecutionContext, sentiment_data: DataFrame) -> DataFrame:
    context.log.info('Transformation of data')
    sentiment_data["CleanText"] = sentiment_data["Text"].apply(preprocess_text)
    sentiment_data["Sentiment"] = sentiment_data["Sentiment"].str.strip()
    sentiment_data["categorized_sentiment"] = sentiment_data["Sentiment"].apply(classify_sentiment)
    sentiment_data.to_csv("/app/src/data/sentiment_categorized.csv", index=False)

    context.log.info(sentiment_data)
    return sentiment_data


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def model_training(context: AssetExecutionContext, data_transformation: DataFrame) -> ModelTrainingResult:
    context.log.info('Training of models')
    x = data_transformation["CleanText"]
    y = data_transformation["categorized_sentiment"]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
        ("clf", LogisticRegression(max_iter=1000))
    ])

    model.fit(x_train, y_train)

    model_traning_result = ModelTrainingResult(x_train=x_train, x_test=x_test, y_train=y_train, y_test=y_test,
                                               model=model, df=data_transformation)

    return model_traning_result


@asset(auto_materialize_policy=AutoMaterializePolicy.eager())
def evaluate_sentiment_data(context: AssetExecutionContext, model_training: ModelTrainingResult):
    context.log.info('Evaluation of models')
    y_pred = model_training.model.predict(model_training.x_test)
    report = classification_report(model_training.y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).transpose()
    context.log.info(report_df)