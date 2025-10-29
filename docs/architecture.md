# Architecture Overview

This document outlines the data flows for the short-form video engagement analytics platform.

## Pipelines
- **Ingestion:** Daily pulls from the YouTube Trending dataset combined with simulated watch event logs.
- **Data Cleaning Layer:** Standardizes timestamps, creator metadata, and filters bot-like behavior.
- **Feature Engine:** Sessionizes watch streams, calculates retention cohorts, and computes engagement KPIs.
- **Modeling:** Cohort survival and churn classification models estimate D1/D7/D30 retention probabilities.
- **Insights Delivery:** Streamlit and Tableau dashboards highlight drop-off points, creator contribution, and retention lift opportunities.

## Data Contracts
Refer to `src/data_contracts.py` for schemas and validators applied during ingestion.
