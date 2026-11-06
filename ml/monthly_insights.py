import pandas as pd

def generate_monthly_insights(monthly_df):
    df = monthly_df.copy()
    df = df.sort_values("month").reset_index(drop=True)
    df["cash_flow_rate_pct"] = (df["net_cash_flow"] / df["income"].replace(0, pd.NA) * 100).fillna(0).round(2)
    df["expense_change_pct"] = df["expenses"].pct_change().mul(100).round(2)

    def recommendation(row):
        if row["net_cash_flow"] < 0:
            return "Expenses exceeded income. Review spending."
        if pd.notna(row["expense_change_pct"]) and row["expense_change_pct"] > 10:
            return "Expenses increased by more than 10%. Review spending."
        if pd.notna(row["expense_change_pct"]) and row["expense_change_pct"] < -10:
            return "Expenses decreased. Keep tracking your spending."
        return "Positive cash flow. Keep monitoring your finances."

    df["recommendation"] = df.apply(recommendation, axis=1)
    return df
