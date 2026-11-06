CATEGORY_RULES = {
    "Salary": ["salary", "payroll"],
    "Food": ["restaurant", "swiggy", "zomato", "food", "cafe"],
    "Rent": ["rent"],
    "Transport": ["uber", "ola", "petrol", "fuel", "bus", "metro"],
    "Shopping": ["amazon", "flipkart", "shopping", "myntra"],
    "Utilities": ["electricity", "water bill", "recharge", "internet"],
    "Loan": ["loan", "emi", "repayment"]
}

def categorize_transaction(description, amount=0):
    description = str(description).lower().strip()

    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in description for keyword in keywords):
            return category

    if amount > 0:
        return "Other Income"
    elif amount < 0:
        return "Other Expense"
    return "Uncategorized"
