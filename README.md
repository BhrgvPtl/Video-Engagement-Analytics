# Reels Engagement Analytics

Forecast retention and surface watch-behavior "what-ifs" to inform creator and product decisions.

## KPIs (Meta-aligned)
- **Retention:** D1 / D7 / D30 viewer return ratios
- **Session Time:** Average watch session duration per cohort
- **Completion Rate:** Percent of short-form videos completed
- **Drop-off Position:** Percent of watch time lost per video quartile
- **DAU / WAU:** Active audience coverage
- **Creator Contribution:** Share of watch time driven by top creators

## Architecture
```
YouTube Trending + Simulated Watch Logs
            ↓
      Data Cleaning Layer
            ↓
     Feature Engine (sessions)
            ↓
    Cohort + Churn Modeling
            ↓
   Insights & Recs Dashboard
            ↓
 Exec Summary: Retention Strategy
```

## Getting Started
1. The analytics toolkit uses the Python standard library, so no dependency installation is required for the core CLI and tests.
2. Generate processed features from the bundled samples:
   ```bash
   make build
<<<<<<< Updated upstream
   ```
3. Launch the Streamlit dashboard (optional, requires installing Streamlit and Plotly):
=======
   ```  
3. Launch the Streamlit dashboard:
>>>>>>> Stashed changes
   ```bash
   make run
   ```
4. Run unit tests before opening a pull request:
   ```bash
   make test
   ```

## Repo Structure
```
reels-analytics/
├─ data/
│  ├─ raw/              # bundled csvs for watch events and metadata
│  └─ processed/        # outputs from feature engineering
├─ notebooks/
│  ├─ 01_explore_videos.ipynb
│  ├─ 02_user_sessions.ipynb
│  └─ 03_churn_model.ipynb
├─ src/
│  ├─ data_contracts.py
│  ├─ features.py
│  ├─ churn_model.py
│  ├─ metrics.py
│  └─ utils.py
├─ dashboards/
│  ├─ retention_insights.twb
│  └─ streamlit_app.py
├─ docs/
│  ├─ retention_strategy_slide.pdf
│  └─ architecture.md
├─ tests/
│  ├─ test_features.py
│  ├─ test_churn_model.py
│  └─ test_metrics.py
├─ pyproject.toml
├─ Makefile
└─ README.md
```

## Dataset Reference
This project layers the [YouTube Trending Videos dataset](https://www.kaggle.com/datasets/datasnaek/youtube-new?resource=download) with simulated watch event logs (`data/raw/watch_events.csv`) to demonstrate how to orchestrate retention analytics.

## Contributing
Please review the [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md) and [CONTRIBUTING](CONTRIBUTING.md) guides before submitting a change. Automated tests run on every pull request via GitHub Actions.
