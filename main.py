
from fastmcp import FastMCP
import os
import sqlite3
import json

mcp = FastMCP("ExpenseTracker")

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)
        conn.commit()

init_db()


@mcp.tool()
def add_expense(date,amount,category,subcategory="",note=""):
    """Adds a new expense to the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor= conn.execute("""
            INSERT INTO expenses (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
        """, (date, amount, category, subcategory, note))
        return {"status":"ok","id":cursor.lastrowid}

@mcp.tool()
def list_expenses():
    """Lists all expenses in the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT id, date, amount, category, subcategory, note FROM expenses ORDER BY id ASC")
        columns=[description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

@mcp.tool()
def delete_expense(amount, date=None, category=None):
    """Delete expense using amount with date and/or category."""

    if not date and not category:
        return {
            "status": "error",
            "message": "Provide either date or category with amount"
        }

    query = "DELETE FROM expenses WHERE amount = ?"
    params = [amount]

    if date:
        query += " AND date = ?"
        params.append(date)

    if category:
        query += " AND category = ?"
        params.append(category)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(query, params)
        conn.commit()

        return {
            "status": "ok",
            "deleted_rows": cursor.rowcount
        }

@mcp.tool()
def update_expense(
    amount,
    date=None,
    category=None,
    new_amount=None,
    new_date=None,
    new_category=None,
    new_subcategory=None,
    new_note=None
):
    """Updates an expense using amount with date and/or category."""

    if not date and not category:
        return {
            "status": "error",
            "message": "Provide either date or category with amount"
        }

    update_fields = []
    update_values = []

    if new_amount is not None:
        update_fields.append("amount = ?")
        update_values.append(new_amount)

    if new_date is not None:
        update_fields.append("date = ?")
        update_values.append(new_date)

    if new_category is not None:
        update_fields.append("category = ?")
        update_values.append(new_category)

    if new_subcategory is not None:
        update_fields.append("subcategory = ?")
        update_values.append(new_subcategory)

    if new_note is not None:
        update_fields.append("note = ?")
        update_values.append(new_note)

    if not update_fields:
        return {
            "status": "error",
            "message": "Provide at least one field to update"
        }

    query = "UPDATE expenses SET "
    query += ", ".join(update_fields)

    query += " WHERE amount = ?"
    params = update_values + [amount]

    if date:
        query += " AND date = ?"
        params.append(date)

    if category:
        query += " AND category = ?"
        params.append(category)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(query, params)
        conn.commit()

        return {
            "status": "ok",
            "updated_rows": cursor.rowcount
        }

@mcp.tool()
def summarize(start_date, end_date,category=None):
    """summarize expenses by category within an inclusive date range"""

    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cursor = conn.execute(query, params)
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


@mcp.resource(
    uri="expenses://categories",
    name="Expense Categories",
    description="Available expense categories",
    mime_type="application/json",
)
def categories_resource():
    """Returns available expense categories as a JSON resource."""
    if not os.path.exists(CATEGORIES_PATH):
        return "[]"
    try:
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return json.dumps({"error": f"Error reading categories: {str(e)}"})

# Run the MCP server
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
 