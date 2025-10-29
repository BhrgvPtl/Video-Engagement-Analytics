# Short-Form Video Engagement Analytics

End-to-end analytics workspace for modeling short-form video retention, aligned with Meta's KPI framework. The project unifies YouTube trending data, simulated watch events, and interaction metrics to build actionable retention insights.

## 📂 Dataset Sources
- **YouTube Trending Videos (Kaggle):** Title, category, tags, and publish metadata for trending content.
- **Simulated Watch Event Logs:** Session-level play events with watch duration, completion, and drop-off markers.
- **Interaction Metrics:** Aggregated likes, shares, and comments mapped to engagement cohorts.

## 📌 Key KPIs
- **Retention:** D1 / D7 / D30 curves and churn risk.
- **Session Time:** Average minutes per session.
- **Completion Rate (%):** Share of plays reaching full completion.
- **Drop-Off Position (%):** Median point where viewers churn.
- **DAU / WAU:** Active user cadence.
- **Creator Contribution (% watch share):** Time watched by top creators.

## 🧩 Architecture Overview
```
YouTube Data + Simulated Logs
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

## 🗂 Repository Structure
```
reels-analytics/
 ├─ data/
 │   ├─ raw/
 │   └─ processed/
 ├─ notebooks/
 │   ├─ 01_explore_videos.ipynb
 │   ├─ 02_user_sessions.ipynb
 │   └─ 03_churn_model.ipynb
 ├─ src/
 │   ├─ features.py
 │   └─ churn_model.py
 ├─ dashboards/
 ├─ docs/
 │   └─ retention_strategy_slide.pdf
 └─ streamlit_app.py
```

## 🚀 Getting Started
1. Place the Kaggle trending CSV under `data/raw/youtube_trending_sample.csv`.
2. Export simulated watch events to `data/raw/watch_events_sample.csv`.
3. Run the feature engineering notebook or use `src/features.py` to build session-level aggregations into `data/processed/session_features.parquet`.
4. Train churn models and review performance via `src/churn_model.py` or the `03_churn_model.ipynb` notebook.
5. Launch the Streamlit dashboard:
   ```bash
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```

## 📊 Dashboards & Insights
- **Streamlit App:** Interactive retention command center with KPIs, session insights, and churn model summaries.
- **Docs:** Executive-ready `docs/retention_strategy_slide.pdf` summarizing retention strategy recommendations.

## 🧪 Testing
- Unit tests can be added under a future `tests/` directory to validate feature engineering and model pipelines.

## 📄 License
MIT
