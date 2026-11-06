
# FinSight AI - Transaction Categorization

CATEGORY_RULES = {
    "Salary": ["salary", "payroll", "monthly pay"],
    "Food": ["restaurant", "swiggy", "zomato", "food", "cafe"],
    "Rent": ["rent", "house rent"],
    "Transport": ["uber", "ola", "petrol", "fuel", "bus", "metro"],
    "Shopping": ["amazon", "flipkart", "shopping", "myntra"],
    "Utilities": ["electricity", "water bill", "recharge", "internet"],
    "Loan": ["loan", "emi", "repayment"],
    "Business Income": ["customer payment", "sales", "client payment"],
    "Business Expense": ["supplier", "wholesale", "inventory"]
}


def categorize_transaction(description, amount=0):
    """
    Categorize a bank transaction using its description.
    Assumption: positive amount = credit, negative = debit.
    """

    description = str(description).lower().strip()

    for category, keywords in CATEGORY_RULES.items():
        for keyword in keywords:
            if keyword in description:
                return category

    if amount > 0:
        return "Other Income"

    if amount < 0:
        return "Other Expense"

    return "Uncategorized"
