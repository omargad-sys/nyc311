# NYC311 Pulse

A relational database and Power BI case study built on real NYC 311 service
request data, with an automated Python and SQL pipeline behind it.

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
