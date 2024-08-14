import sys
import os
import logging
import joblib
from typing import Tuple, Union, List

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.exceptions import NotFittedError
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Set the root path of your project
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

logger.info(
    f"ROOT_DIR: {ROOT_DIR}",
)


class DelayModel:
    def __init__(self):
        # Initialize the model with Logistic Regression and specified class weights
        logger.info("Initializing the DelayModel.")
        class_weight = {0: 0.18381548426626987, 1: 0.8161845157337302}
        self._model = LogisticRegression(class_weight=class_weight, random_state=42)

        # Define the columns to be one-hot encoded
        self.categorical_columns = ["OPERA", "TIPOVUELO", "MES"]

        # Define the top 10 features to keep after one-hot encoding
        self.top_10_features = [
            "OPERA_Latin American Wings",
            "MES_7",
            "MES_10",
            "OPERA_Grupo LATAM",
            "MES_12",
            "TIPOVUELO_I",
            "MES_4",
            "MES_11",
            "OPERA_Sky Airline",
            "OPERA_Copa Air",
        ]

        # Initialize the OneHotEncoder
        self.encoder = OneHotEncoder(sparse=False, handle_unknown="ignore")

        # The preprocessing pipeline
        # Define a pipeline for categorical features
        categorical_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                ("onehot", OneHotEncoder(sparse=False, handle_unknown="ignore")),
            ]
        )

        # Update the preprocessing pipeline
        self.preprocessor = Pipeline(
            steps=[
                (
                    "preprocessor",
                    ColumnTransformer(
                        transformers=[
                            ("cat", categorical_transformer, self.categorical_columns)
                        ],
                        remainder="drop",
                    ),
                ),
                ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
            ]
        )

        logger.info("DelayModel initialized successfully.")

    def get_min_diff(self, row):
        """Calculate the difference in minutes between 'Fecha-O' and 'Fecha-I'."""
        logger.debug(f"Calculating min_diff for row: {row.name}")
        fecha_o = datetime.strptime(row["Fecha-O"], "%Y-%m-%d %H:%M:%S")
        fecha_i = datetime.strptime(row["Fecha-I"], "%Y-%m-%d %H:%M:%S")
        min_diff = ((fecha_o - fecha_i).total_seconds()) / 60
        logger.debug(f"min_diff calculated: {min_diff}")
        return min_diff

    def preprocess(
        self, data: pd.DataFrame, target_column: str = None
    ) -> Union[Tuple[pd.DataFrame, pd.DataFrame], pd.DataFrame]:
        """
        Prepare raw data for training or prediction.

        Args:
            data (pd.DataFrame): raw data.
            target_column (str, optional): if set, the target is returned.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: features and target.
            or
            pd.DataFrame: features.
        """
        logger.info("Starting preprocessing.")
        if target_column:
            # Calculate 'min_diff' and 'delay'
            logger.info("Calculating 'min_diff' and 'delay' columns.")
            data["min_diff"] = data.apply(self.get_min_diff, axis=1)
            threshold_in_minutes = 15
            data["delay"] = np.where(data["min_diff"] > threshold_in_minutes, 1, 0)
            features = data.drop(columns=[target_column])
            target = data.loc[:, [target_column]]
        else:
            features = data
            target = None

        # Apply the preprocessing pipeline
        logger.info("Applying preprocessing pipeline.")
        features_transformed = self.preprocessor.fit_transform(features)
        self.encoder = (
            self.preprocessor.named_steps["preprocessor"]
            .transformers_[0][1]
            .named_steps["onehot"]
        )
        feature_names = self.encoder.get_feature_names_out(self.categorical_columns)

        features_transformed_df = pd.DataFrame(
            features_transformed, columns=feature_names
        )

        # Filter only top 10 features
        logger.info("Filtering top 10 features.")
        filtered_features = features_transformed_df[self.top_10_features]

        logger.info("Preprocessing completed.")
        if target is not None:
            return filtered_features, target
        else:
            return filtered_features

    def fit(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        """
        Fit model with preprocessed data.

        Args:
            features (pd.DataFrame): preprocessed data.
            target (pd.DataFrame): target.
        """
        logger.info("Fitting the model.")
        self._model.fit(features, target)
        self.save_artifact(self._model, f"{ROOT_DIR}/artifacts/model.pkl")
        logger.info("Model fitting completed.")

    def predict(self, features: pd.DataFrame) -> List[int]:
        """
        Predict delays for new flights.

        Args:
            features (pd.DataFrame): preprocessed data.

        Returns:
            (List[int]): predicted targets.
        """
        logger.info("Making predictions.")
        try:
            # Attempt to make predictions
            predictions = self._model.predict(features)
        except NotFittedError:
            # If the model is not fitted, fit the model and then predict
            logger.warning("Model is not fitted. Loaded fitted model.")
            self._model = self.load_artifact(f"{ROOT_DIR}/artifacts/model.pkl")
            predictions = self._model.predict(features)
        logger.info("Predictions completed.")
        return predictions.tolist()

    def save_artifact(self, artifact: object, path: str) -> None:
        """
        Save any object (artifact) to disk.

        Args:
            artifact (object): The object to save (e.g., model, preprocessor).
            path (str): Path to save the artifact.
        """
        logger.info(f"Saving artifact to {path}.")
        joblib.dump(artifact, path)
        logger.info(f"Artifact saved to {path}.")

    def load_artifact(self, path: str) -> object:
        """
        Load any object (artifact) from disk.

        Args:
            path (str): Path to load the artifact from.

        Returns:
            object: The loaded artifact.
        """
        logger.info(f"Loading artifact from {path}.")
        artifact = joblib.load(path)
        logger.info(f"Artifact loaded from {path}.")
        return artifact
