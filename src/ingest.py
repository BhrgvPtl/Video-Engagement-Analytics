from __future__ import annotations
import os
import pandas as pd
from .utils import path_raw, path_proc

def main():
    src_csv = path_raw("USvideos.csv")
    if not os.path.exists(src_csv):
        print(f"[ingest] {src_csv} not found. Place the Kaggle CSV there.")
        return

    df = pd.read_csv(src_csv, low_memory=False)

    keep = [c for c in [
        "video_id","title","channel_title","category_id",
        "publish_time","views","likes","comment_count"
    ] if c in df.columns]
    if not keep:
        print("[ingest] no expected columns found; check CSV.")
        return

    out_min = path_proc("videos_clean_min.parquet")
    df[keep].to_parquet(out_min, index=False)
    print(f"[ingest] wrote {out_min} ({len(df):,} rows)")

if __name__ == "__main__":
    main()
