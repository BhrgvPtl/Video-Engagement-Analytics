from __future__ import annotations
import os
import pandas as pd
from .utils import path_proc

def main():
    src = path_proc("videos_clean_min.parquet")
    dst = path_proc("videos_clean.parquet")

    if not os.path.exists(src):
        print(f"[clean] {src} missing. Run ingest first.")
        return

    df = pd.read_parquet(src)
    # Normalize timestamps
    if "publish_time" in df.columns:
        df["publish_time"] = pd.to_datetime(df["publish_time"], errors="coerce", utc=True)

    # Drop empties & dupes
    df = df.dropna(subset=["video_id"]).drop_duplicates(subset=["video_id","publish_time"])

    # Keep only positive numeric counts when present
    for col in ["views","likes","comment_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
            df = df[df[col] >= 0]

    df.to_parquet(dst, index=False)
    print(f"[clean] wrote {dst} ({len(df):,} rows)")

if __name__ == "__main__":
    main()
