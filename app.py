import streamlit as st
import pandas as pd
import plotly.express as px
from ml.categorize import categorize_transaction
from ml.anomaly_detection import detect_anomalies

st.set_page_config(page_title="FinSight AI", page_icon="💰", layout="wide")
st.title("FinSight AI")
st.subheader("Smart Bank Statement Analysis")
profile = st.sidebar.selectbox("User Type", ["Employee", "Business Owner"])
upload = st.sidebar.file_uploader("Upload bank CSV", type=["csv"])
if upload:
    df = pd.read_csv(upload)
    if not {"description", "amount"}.issubset(df.columns):
        st.error("CSV must contain description and amount columns")
        st.stop()
else:
    st.info("Demo data is being shown. Upload a sample CSV to test your data.")
    df = pd.DataFrame({"description": ["Monthly salary", "House rent", "Swiggy food", "Uber ride", "Electricity bill", "Amazon shopping", "Client payment", "Petrol", "Restaurant", "Office supplies"], "amount": [30000, -8000, -450, -300, -1200, -2500, 12000, -1500, -700, -900]})
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df = df.dropna(subset=["description", "amount"]).copy()
df["category"] = df.apply(lambda row: categorize_transaction(row["description"], row["amount"]), axis=1)
income = df.loc[df.amount > 0, "amount"].sum()
expenses = abs(df.loc[df.amount < 0, "amount"].sum())
net = income - expenses
c1, c2, c3 = st.columns(3)
c1.metric("Total Income", f"₹{income:,.2f}")
c2.metric("Total Expenses", f"₹{expenses:,.2f}")
c3.metric("Net Cash Flow", f"₹{net:,.2f}")
st.subheader("Spending by Category")
expense_df = df[df.amount < 0].copy()
if not expense_df.empty:
    expense_df["spent"] = expense_df["amount"].abs()
    fig = px.pie(expense_df, names="category", values="spent", title="Expense Distribution")
    st.plotly_chart(fig, use_container_width=True)
st.subheader("Transactions")
st.dataframe(df, use_container_width=True)
st.subheader("Unusual Transaction Review")
if len(df) >= 5:
    try:
        result = detect_anomalies(df)
        st.dataframe(result[result.anomaly == "Review"], use_container_width=True)
        st.caption("Review flags are unusual patterns, not proof of fraud.")
    except Exception as e:
        st.warning(str(e))
else:
    st.info("At least 5 transactions are needed for anomaly review.")
