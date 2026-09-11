# NYC311 Pulse

A relational database and Power BI case study built on real NYC 311 service
request data, with an automated Python and SQL pipeline behind it.

**Live site:** add your Porkbun domain here once DNS is set up
**Live dashboard:** add your Power BI "Publish to web" link here

## What this project demonstrates

- **Relational database design.** A star schema in PostgreSQL: one fact
  table (`fact_311_requests`) plus four dimension tables (agency, complaint
  type, borough, date).
- **SQL.** Real analytical queries using CTEs and window functions
  (`RANK`, `LAG`, `ROW_NUMBER`), see `sql/analysis_queries.sql`.
- **Python.** An ETL script that pulls from the NYC Open Data Socrata API,
  transforms it, and upserts it into Postgres, see `etl/fetch_311.py`.
- **Automation.** A GitHub Actions workflow refreshes the data on a weekly
  schedule with no manual step, see `.github/workflows/refresh_data.yml`.
- **Power BI.** Data modeling (relationships between fact and dimension
  tables), DAX measures, and a published interactive dashboard.
- **Data visualization and deployment.** A GitHub Pages case study site,
  deployed by its own GitHub Actions workflow, served on a custom domain.

## Architecture

```
NYC Open Data (Socrata API)
        │
        ▼
Python ETL script  ──────►  scheduled weekly by GitHub Actions
        │
        ▼
PostgreSQL (star schema, hosted on Supabase or Neon)
        │
        ▼
Power BI Desktop  ──────►  published with "Publish to web"
        │
        ▼
GitHub Pages case study site (this repo's docs/ folder, custom domain)
```

GitHub Pages only serves static files, it cannot run a database or Power BI
itself. The Pages site is the case study and the embed of the dashboard.
Power BI's own servers host the live report.

## Repo structure

```
etl/fetch_311.py                    Python ETL script
sql/schema.sql                      Star schema DDL
sql/analysis_queries.sql            Example CTE / window function queries
docs/index.html                     GitHub Pages case study site
.github/workflows/refresh_data.yml  Scheduled data refresh
.github/workflows/deploy_pages.yml  Deploys docs/ to GitHub Pages
requirements.txt                    Python dependencies
.env.example                        Template for local environment variables
```

## Setup

1. **Get a Socrata app token.** Free, from a data.cityofnewyork.us account
   (My Profile > Edit Apps). Not strictly required but avoids rate limits.

2. **Create a free Postgres database.** Supabase or Neon both work and have
   a free tier. Copy the connection string.

3. **Run the schema.**
   ```
   psql "$DATABASE_URL" -f sql/schema.sql
   ```

4. **Run the ETL locally to test it.**
   ```
   pip install -r requirements.txt
   cp .env.example .env   # fill in your real values, then export them
   python etl/fetch_311.py
   ```

5. **Add GitHub repo secrets** (Settings > Secrets and variables > Actions):
   `SOCRATA_APP_TOKEN` and `DATABASE_URL`. The scheduled workflow needs
   these to run without you.

6. **Connect Power BI Desktop** to the same Postgres database (Get Data >
   PostgreSQL database), build the model and report, then use
   File > Publish > Publish to web to get a public embed link. Paste that
   link into the iframe placeholder in `docs/index.html`.

7. **Turn on GitHub Pages.** Repo Settings > Pages > Source: GitHub Actions.
   The `deploy_pages.yml` workflow handles the rest on every push to `docs/`.

8. **Point your domain at it.** In Porkbun's DNS settings, add four A
   records for the apex domain pointing to `185.199.108.153`,
   `185.199.109.153`, `185.199.110.153`, and `185.199.111.153`, plus a
   CNAME for `www` pointing to `YOUR-USERNAME.github.io`. Then add the
   domain under repo Settings > Pages > Custom domain.

## Findings

Fill this in once you've explored the data. Aim for one or two specific,
numeric findings, not a general summary. That's what actually gets read.

## Resume keywords this project supports

SQL, PostgreSQL, relational database design, star schema, data modeling,
Python, ETL pipeline, REST API integration, GitHub Actions, CI/CD, Power
BI, DAX, data visualization, dashboard design, KPI reporting, data
analysis.
