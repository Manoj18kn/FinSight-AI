import pandas as pd

def monthly_analysis(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    result = df.groupby("month").agg(
        income=("amount", lambda x: x[x > 0].sum()),
        expenses=("amount", lambda x: abs(x[x < 0].sum())),
        net_cash_flow=("amount", "sum")
    ).reset_index()
    return result
