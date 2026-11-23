# Food Management System

A DBMS project with a Flask application, server-rendered HTML/CSS, and MySQL. HTML forms go directly to Flask routes. Flask reads and writes MySQL, then renders the page.

## Run in VS Code

On Windows, open this folder in VS Code. Install Python and MySQL Server 8 for a new machine. From the project terminal, set up the Python environment once:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the app:

```powershell
python .\run_local.py
```

Open `http://127.0.0.1:5173`. Keep the terminal open. Press Ctrl+C to stop Flask and its local MySQL instance. You can also select **Terminal → Run Task → Run food management locally** in VS Code.

The launcher starts a loopback-only MySQL instance on port 3307, initializes the database when needed, and reuses the existing project database when present. Set `MYSQL_BIN` if MySQL is installed in another directory. For an already-running MySQL instance, set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and optionally `DB_NAME` in your terminal, then run `python run_local.py --external-mysql`. First-time setup needs permission to create the project schema, views, procedures and triggers.

## Demonstrate the project

Demo accounts are `farmer_1@demo.com`, `wholesaler_1@demo.com`, and `retailer_1@demo.com`. The demo password is `password123`. You can also register your own accounts.

1. Sign in as a farmer and add an unexpired crop batch.
2. Sign in as a wholesaler, buy some of that crop, and check the wholesaler inventory.
3. Sign in as a retailer and buy from the corresponding wholesaler batch.
4. Open **SQL analysis** to compare current prices, review expiring stock, and see recent farmer-to-wholesaler transactions.

## Where the SQL lives

| File | What to show |
| --- | --- |
| `database/schema.sql` | Tables, primary keys, foreign keys, and constraints |
| `database/schema_updates.sql` | Pricing and expiry views, add and purchase procedures, and purchase-alert triggers |
| `database/analysis.sql` | Lowest current price by crop at each supply chain stage |
| `app.py` | Flask form handling and the queries for the inventory and analysis pages |
| `db.py` | The MySQL connection and helpers for running parameterized queries and procedures |
