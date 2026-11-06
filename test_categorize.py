
from ml.categorize import categorize_transaction

transactions = [
    ("Monthly salary credited", 40000),
    ("Swiggy food order", -500),
    ("House rent payment", -10000),
    ("Uber ride", -250),
    ("Amazon shopping", -1500),
    ("Unknown transaction", -200)
]

for description, amount in transactions:
    category = categorize_transaction(description, amount)
    print(description, "->", category)
