# E-Commerce Sales & Customer Analytics

A recruiter-ready, end-to-end data analytics portfolio project inspired by the Target/Olist e-commerce analytics workflow.

The original tutorial structure covers:
1. E-commerce dataset acquisition
2. Loading relational data into SQL
3. A sequence of business questions
4. Query-based analysis
5. Publishing/reporting

This version is adapted for a fast Windows setup:
- Python + Pandas for preparation
- SQLite for a zero-server SQL workflow
- SQL file containing 16 business questions
- Streamlit + Plotly for a polished interactive dashboard
- Built-in synthetic sample data so the project runs immediately
- Optional full Olist/Target CSVs can be dropped into `data/raw/`

## 1. Recommended software

Use **VS Code**.

Install:
- Python 3.11+ if available
- VS Code + Python extension

You do NOT need MySQL for the quick-start version.

For the dashboard:
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open the local URL shown by Streamlit, usually:
`http://localhost:8501`

## 2. Quick start on Windows

Open this folder in VS Code.

Open Terminal → PowerShell.

Create a virtual environment:
```powershell
py -m venv .venv
```

Activate it:
```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Install packages:
```powershell
python -m pip install -r requirements.txt
```

Run:
```powershell
python -m streamlit run app.py
```

## 3. What happens automatically

On first launch the application:
- reads the built-in sample CSVs
- creates `data/analytics.db`
- joins orders, customers, items, products, payments and reviews
- shows interactive KPIs and charts

## 4. Use the full public dataset

The tutorial uses the Target e-commerce dataset, which is a Brazilian relational e-commerce dataset with customer, order, product, payment and seller tables. Public examples of this dataset describe roughly 100K orders and the same core CSV structure. citeturn153612search0turn153612search4

Dataset source:
https://www.kaggle.com/datasets/devarajv88/target-dataset

Download the public dataset, extract the CSV files, then place them in:
```text
data/raw/
```

Use the exact files:
```text
customers.csv
orders.csv
order_items.csv
payments.csv
reviews.csv
products.csv
sellers.csv
geolocation.csv
category_translation.csv
```

The app now accepts both the simplified filenames in this repo and the original Olist-style filenames, so you do not need to rename the downloaded files.

The application automatically prefers `data/raw/` when all required files are present. Otherwise it uses the bundled sample data.

## 5. SQL practice

Open:
`sql/business_analysis.sql`

It contains 16 business questions/analyses including:
- unique customer cities
- 2017 orders
- revenue by category
- installment payment share
- state-level performance
- monthly order trends
- category revenue share
- average products per order
- pricing vs purchase volume
- top sellers
- delivery time vs review score
- payment-method mix
- monthly revenue growth
- repeat-customer proxy
- state/category performance
- seller ranking with a window function

Run the SQL after the SQLite database exists.

## 6. Dashboard

The dashboard has:
- Executive Dashboard
- Business Insights
- Data Quality
- interactive date/state/category filters
- KPI cards
- monthly revenue trend
- category revenue ranking
- state performance
- payment mix
- analyst takeaways
- missing/duplicate checks

## 7. How to publish for recruiters

### GitHub
Create a public GitHub repository and upload:
- `app.py`
- `src/`
- `sql/`
- `data/sample/`
- `docs/`
- `requirements.txt`
- `README.md`

Do NOT upload:
- `.venv`
- `data/analytics.db`
- large raw datasets

### Live dashboard
Deploy the GitHub repository using Streamlit Community Cloud:
1. Push the project to GitHub.
2. Sign in to Streamlit Community Cloud with GitHub.
3. Create/select the repository.
4. Select `app.py` as the main file.
5. Deploy.

The final recruiter-facing link will look like:
`https://your-project-name.streamlit.app`

## 8. Interview story

Be ready to explain:
- why you chose the business questions
- how the relational tables connect
- why canceled orders are excluded from revenue
- how you calculated revenue and average order value
- how window functions help rank sellers
- what you checked for missing/duplicate data
- which insight changed when you changed filters

## 9. Before you publish this project

The bundled `data/sample/` files are synthetic and exist only so the dashboard can run immediately. For a stronger portfolio project, download the public dataset, run the project with the full data, inspect the outputs yourself, and then publish the code plus screenshots. Do not claim the 100K+ dataset scale unless you actually ran the full dataset.

## 10. Resume wording

Use the resume bullets only after you have run the project and can explain the workflow.

Suggested project title:
**E-Commerce Sales & Customer Analytics | Python, SQL, Pandas, Streamlit**

Suggested bullets:
- Built an end-to-end e-commerce analytics workflow using Python, Pandas and SQL to clean, join and analyze customer, order, product, payment and review data.
- Wrote SQL analyses using aggregations, CTEs and window functions to evaluate revenue, category performance, customer behavior, payments, seller rankings and monthly trends.
- Developed an interactive Streamlit dashboard with KPI cards, filters and Plotly visualizations to communicate business insights.
