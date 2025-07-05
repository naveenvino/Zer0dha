import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

class PredictiveModel:
    def __init__(self, model=None):
        self.model = model or RandomForestClassifier()

    def train(self, features: pd.DataFrame, target: pd.Series):
        """
        Trains the predictive model.

        Args:
            features (pd.DataFrame): A pandas DataFrame of features.
            target (pd.Series): A pandas Series representing the target variable.
        """
        X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        print(f"Model Accuracy: {accuracy_score(y_test, y_pred)}")

    def predict(self, features: pd.DataFrame) -> pd.Series:
        """
        Makes predictions using the trained model.

        Args:
            features (pd.DataFrame): A pandas DataFrame of features.

        Returns:
            pd.Series: A pandas Series of predictions.
        """
        return self.model.predict(features)
