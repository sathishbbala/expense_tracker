import sqlite3, random
from datetime import datetime, timedelta
from collections import defaultdict
from contextlib import closing
import argparse


dict_category_merchant = {
    "Food": ["Swiggy", "Zomato"], 
    "Shopping": ["Flipkart", "Myntra", "Amazon", "Blinkit", "Instamart", "Zepto" ],
    "RentalCar": ["Avis", "Hertz", "Zoomcar", "Saavari"],
    "Transportation": ["Rapido", "Uber", "Ola"],
    "HotelStay": ["Marriott", "Fairfield", "Hilton"], 
    "Travel": ["Indigo", "AirIndia","IRCTC"],
    "Entertainment": ["Netflix", "Amazon Prime", "Spotify", "SunNXT", "Jio"],
    "Pharmacy": ["Apollo Pharmacy", "MedPlus", "Ramkumar Medicals"],
    "Groceries": ["Spar Hypermart", "Lulu Hypermart", "Grace Supermarket"]
}

def run_query(query, params=None):
    """
    Executes a query safely using a context manager and guarantees closure.
    """
    if params is None:
        params = ()
        
    try:
        # Opens connection and automatically manages closing/commits
        with closing(sqlite3.connect("expensetracker.db")) as conn:       # closes the connection
            cursor = conn.cursor()
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount  
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        raise
        # return 0 if not query.strip().upper().startswith("SELECT") else []

def create_table():
    run_query("""
                CREATE TABLE IF NOT EXISTS expense_transactions 
              ( transaction_id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_dt DATE,merchant TEXT, 
               category TEXT, amount DECIMAL(6,2))
               """)

def create_transaction(number_of_transactions):
    tuple_params=[]
    insert_query ="""INSERT INTO expense_transactions(transaction_dt, merchant, category, amount) VALUES (?,?,?,?)"""
    for i in range(number_of_transactions):
        random_date = (datetime.now().date() - timedelta(days=random.randint(0,365))).isoformat()
        random_category = random.choice(list(dict_category_merchant.keys()))
        random_merchant = random.choice(dict_category_merchant[random_category])
        random_amount = format(random.uniform(200, 9999),".2f")
        tuple_params.append((random_date, random_merchant, random_category, random_amount))

    run_many(insert_query, tuple_params)

def run_many(query, params_list):
    with closing(sqlite3.connect("expensetracker.db")) as conn:
        with conn:
            conn.executemany(query, params_list)

    
def get_transaction(transaction_id):
    select_query = """SELECT transaction_id, transaction_dt, merchant, category, amount FROM expense_transactions WHERE transaction_id = ?"""
    select_query_params = (transaction_id,)       # comma is needed so params is a tuple
    rows = run_query(select_query, select_query_params)

    if not rows:
        print(f"No transaction with ID {transaction_id} exists")
        return False
    row = rows[0]
    print(f"ID: {row[0]} | Date: {row[1]} | Merchant: {row[2]} | Category: {row[3]} | Amount: ₹{row[4]}")
    return True
        
def list_all_transactions():
    rows = run_query("""SELECT * FROM expense_transactions""")
    print("\n--- All Transactions ---")
    for row in rows: # row is a tuple 
        print(f"ID: {row[0]} | Date: {row[1]} | Merchant: {row[2]} | Category: {row[3]} | Amount: ₹{row[4]}")

def update_transaction(transaction_id, transaction_amount):
    found = get_transaction(transaction_id)
    if found:
        update_query = """UPDATE expense_transactions SET amount = ? WHERE transaction_id = ?"""
        update_query_params = (transaction_amount,transaction_id)
        rowcount = run_query(update_query, update_query_params)
        if rowcount > 0:
            print(f"Transaction {transaction_id} updated successfully.")
            get_transaction(transaction_id)
        else:
            print(f"Transaction {transaction_id} could not be updated.")

def delete_transaction(transaction_id):
    found = get_transaction(transaction_id)
    if found:
        confirm = input("Do you really want to delete(Y|N):").strip().upper()
        if confirm == "Y":
            delete_query = """DELETE FROM expense_transactions WHERE transaction_id = ?"""
            delete_query_params = (transaction_id,)
            rowcount = run_query(delete_query, delete_query_params)
            if rowcount > 0:
                print(f"Transaction {transaction_id} deleted successfully.")
            else:
                print(f"Transaction {transaction_id} could not be deleted.")
        else:
            print("Delete action cancelled")

def delete_all_data():
    rowcount = run_query("""DELETE FROM expense_transactions""")
    rowcount = run_query("""UPDATE sqlite_sequence SET seq=0 WHERE name='expense_transactions'""")

def run_analytics():
    totals = {}
    
    for key in ["Merchant", "Category", "Monthly"]: 
        totals[key] = defaultdict(float)

    select_query = """SELECT strftime('%Y-%m', transaction_dt), merchant, category, amount FROM expense_transactions order by transaction_dt asc"""
    rows = run_query(select_query)   # this is a list of tuples, each record is a tuple

    for row in rows:
        totals["Monthly"][row[0]] += row[3]
        totals["Merchant"][row[1]] += row[3]
        totals["Category"][row[2]] += row[3]
    return totals 

def print_analytics():
    totals = run_analytics()
    for key, value in totals.items():
        print(f"\n{key} spend\n" + "-" * 15)
        for inner_key, inner_value in sorted(value.items()):
            print(f"{inner_key}: {inner_value:.2f}")

def is_valid_year_month(date_string):
    try:
        datetime.strptime(date_string, "%Y-%m")
        return True
    except ValueError:
        return False

def check_merchants(prev_month, current_month):
    
    select_query = """SELECT strftime('%Y-%m', transaction_dt), merchant FROM expense_transactions order by transaction_dt"""
    rows = run_query(select_query)  # rows is a list of tuples

    dict_month_merchants = defaultdict(set)             # initialize a dictionary
    for month, merchant in rows:                        # loop through the resultset 
        dict_month_merchants[month].add(merchant)       # adding merchants for that month into a set
    return dict_month_merchants[current_month].difference(
        dict_month_merchants[prev_month]    
    )

def spend_reports():
# 1. Top 3 merchants by # of transactions 
# 2. Category with the highest spend
# 3. Month with the lowest spend 
    select_query = """SELECT strftime('%Y-%m', transaction_dt), merchant, category, amount FROM expense_transactions order by transaction_dt asc"""
    rows = run_query(select_query)  # this is a list of tuples, each record is a tuple

    totals = {}
    totals["MerchantTransactions"] = defaultdict(int)
    totals["Category"] = defaultdict(float)
    totals["Monthly"] = defaultdict(float)

    for row in rows:
        totals["Monthly"][row[0]] += row[3]
        totals["MerchantTransactions"][row[1]] += 1
        totals["Category"][row[2]] += row[3]
    return totals 


if __name__ == "__main__":

    create_table() # Ensure the table exists before any operations
    parser = argparse.ArgumentParser(description="Expense Tracker")
    parser.add_argument(
        "action", 
        choices=["seed-data","list-data","update-transaction","delete-transaction",
                    "delete-all-data","run-analytics","check-merchants","spend-reports"],
        help="Pick an action to execute"
        )
    REQUIRED = {
    "seed-data": ["number_of_transactions"],
    "update-transaction": ["transaction_id", "transaction_amount"],
    "delete-transaction": ["transaction_id"],
    "check-merchants": ["current_year_month"],
    }
    parser.add_argument("--number-of-transactions", type=int, help="Number of transactions to create")
    parser.add_argument("--transaction-id", type=int, help="Transaction ID for update or delete")
    parser.add_argument("--transaction-amount", type=float, help="New transaction amount for update")
    parser.add_argument("--current-year-month", type=str, help="Current year-month in YYYY-MM format for checking merchants")

    args = parser.parse_args()
    missing = [name for name in REQUIRED.get(args.action, []) if getattr(args, name) is None]
    if missing:
        parser.error(f"{args.action} requires: " + ", ".join("--" + n.replace("_", "-") for n in missing))

    if args.action == "create-table":
        create_table()
        print("Table created successfully.")
    elif args.action == "seed-data":
        number_of_transactions = args.number_of_transactions 
        create_transaction(number_of_transactions)
        print(f"{number_of_transactions} transactions created successfully.")
    elif args.action == "list-data":
        list_all_transactions()
        print("Data listed successfully.")
    elif args.action == "update-transaction":
        transaction_id = args.transaction_id
        transaction_amount = args.transaction_amount
        update_transaction(transaction_id, transaction_amount)
    elif args.action == "delete-transaction":
        transaction_id = args.transaction_id
        delete_transaction(transaction_id)
    elif args.action == "delete-all-data":
        confirm = input("Do you really want to delete all data(Y|N):").strip().upper()
        if confirm == "Y":
            delete_all_data()
            print("All data deleted successfully.")
        else:
            print("Delete action cancelled")
    elif args.action == "run-analytics":
        print_analytics()
    elif args.action == "check-merchants":
        # current_year_month = args.current_year_month
        current_year_month = (datetime.strptime(args.current_year_month, "%Y-%m")).strftime("%Y-%m")

        if not is_valid_year_month(current_year_month):
            print(f"❌ Invalid date format: {current_year_month}. Expected format is YYYY-MM.")
        else:
            prev_year_month = (datetime.strptime(current_year_month, "%Y-%m") - timedelta(days=1)).strftime("%Y-%m")
            print(f"Merchants in {current_year_month} but not in {prev_year_month}: {check_merchants(prev_year_month,current_year_month)}")
    elif args.action == "spend-reports":
        spend_reports_totals = spend_reports()
        if not spend_reports_totals["MerchantTransactions"]:
            print("No transactions found for spend reports...Run seed-data to create some transactions first.")
        else:
            top_3_merchant_transactions = sorted(spend_reports_totals["MerchantTransactions"].items(), key=lambda item: item[1], reverse=True)[:3]
            print(f"Top 3 Merchant Transactions: {dict(top_3_merchant_transactions)}")
            highest_category_spend = sorted(spend_reports_totals["Category"].items(), key=lambda item: item[1], reverse=True)[:1]
            category, amount = highest_category_spend[0]
            print(f"Highest Category Spend: {category} with amount: {format(amount,'.2f')}")
            lowest_monthly_spend = sorted(spend_reports_totals["Monthly"].items(), key=lambda item: item[1])[:1]
            month, amount = lowest_monthly_spend[0]
            print(f"Lowest Monthly Spend: {month} with amount: {format(amount,'.2f')}")
