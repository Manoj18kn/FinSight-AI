import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies(df):
    if df.empty or len(df) < 5:
        raise ValueError("At least 5 transactions are required.")
    df = df.copy()
    model = IsolationForest(contamination=0.1, random_state=42)
    df["anomaly"] = model.fit_predict(df[["amount"]])
    df["anomaly"] = df["anomaly"].map({1: "Normal", -1: "Review"})
    return df
