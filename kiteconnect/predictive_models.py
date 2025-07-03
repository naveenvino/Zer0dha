import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def train_price_prediction_model(df: pd.DataFrame, features: list, target: str = 'close'):
    """
    Trains a simple linear regression model for price prediction.

    :param df: Pandas DataFrame with historical data.
    :param features: List of column names to be used as features.
    :param target: The target column for prediction (default: 'close').
    :return: A trained LinearRegression model.
    """
    X = df[features]
    y = df[target]

    # Drop rows with NaN values that might result from feature engineering (e.g., SMA)
    X = X.dropna()
    y = y[X.index] # Align y with X after dropping NaNs

    if X.empty:
        raise ValueError("No valid data after dropping NaNs for training.")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Mean Squared Error: {mse}")

    return model

def predict_price(model: LinearRegression, new_data: pd.DataFrame):
    """
    Predicts price using a trained linear regression model.

    :param model: Trained LinearRegression model.
    :param new_data: DataFrame with new data for prediction. Must have the same features as training data.
    :return: Predicted price.
    """
    return model.predict(new_data)
