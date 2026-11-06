# FinSight — Bank Statement Analysis & Financial Health Monitoring

A learning-project starter application built with Flask, MySQL, HTML/CSS/JavaScript, Pandas and Scikit-learn.

## Features
- User registration and login (password hashes, Flask sessions)
- PDF and CSV statement upload
- Transaction extraction and storage
- Rule-assisted expense categorization
- Dashboard for income, expenses, net savings and category breakdown
- Indicative financial health score
- Random Forest monthly expense estimate (average baseline when history is short)
- Isolation Forest unusual-transaction flags (when enough transactions exist)
- Sample CSV for testing

## Requirements
- Python 3.10+
- MySQL Server 8+
- VS Code and Python extension

## Setup in VS Code (Windows)
1. Install Python 3.10+ and MySQL Server. Start the MySQL service.
2. Extract this project ZIP and open the `bank_finance_monitor` folder in VS Code.
3. Open Terminal > New Terminal.
4. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again.
5. Install packages:
   ```powershell
   pip install -r requirements.txt
   ```
6. In MySQL Workbench, open `schema.sql` and execute it. Or run:
   ```bash
   mysql -u root -p < schema.sql
   ```
7. Copy `.env.example` to `.env` and enter your MySQL password and a long random Flask secret key.
8. Start the application:
   ```powershell
   python app.py
   ```
9. Open `http://127.0.0.1:5000` in your browser.
10. Register, sign in, then upload `sample_transactions.csv` to test the dashboard.

## CSV format
Supported preferred columns:
- `Date`
- `Description` (also accepts Narration, Particulars, Details)
- Either `Amount` (positive=income, negative=expense; optional Type/Dr-Cr column) OR `Debit` and `Credit`

The CSV parser is flexible with common bank export headers. For best results, export the bank statement as CSV and review the column names first.

## PDF limitations
Bank PDFs have different layouts and sometimes contain scanned images. This starter parser handles text-based PDFs with rows resembling:
`01/02/2026 Grocery Store 1,250.00`
It cannot reliably parse every bank's PDF layout or scanned PDF. A production version needs bank-specific parsers and OCR (for example Tesseract) for scanned files. Do not silently assume an unrecognized PDF was imported; this app shows an error when it cannot recognize rows.

## Important project improvements before deployment
- Add CSRF protection, rate limiting, secure cookie settings and email verification.
- Add duplicate-transaction detection and statement reconciliation.
- Add bank-specific PDF parsers and OCR for scanned statements.
- Add pagination, date filters, exportable reports and user-controlled category corrections.
- Add stronger ML evaluation, minimum-data checks and explainability.
- Use HTTPS, private file handling, encryption at rest, backups and audit logging.
- Never collect bank login passwords, OTPs, UPI PINs or card PINs.
- Do not use real customer statements for demos. Use synthetic or anonymized data.

## ML notes
- Isolation Forest identifies statistical outliers, not confirmed fraud.
- Random Forest is a basic forecasting demonstration. Reliable forecasting needs more history, backtesting and comparison against baseline models.
- Financial health score is a transparent educational heuristic, not a credit score or financial advice.

## Database tables
`users`, `statements`, `transactions`, `monthly_analysis` (reserved for storing precomputed monthly summaries in a future enhancement).
