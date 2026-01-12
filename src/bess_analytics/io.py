from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import pandas as pd


def expand_globs(paths: Iterable[str]) -> List[Path]:
    """
    Expand file globs, including absolute globs on Windows.
    """
    expanded: List[Path] = []
    for p in paths:
        pth = Path(p)
        if any(ch in str(pth) for ch in ["*", "?", "["]):
            parent = pth.parent
            pattern = pth.name
            expanded.extend(sorted(parent.glob(pattern)))
        else:
            expanded.append(pth)
    return expanded


def load_files(paths: Iterable[Path]) -> pd.DataFrame:
    frames = []
    for p in paths:
        suffix = p.suffix.lower()
        if suffix in {".parquet", ".pq"}:
            df = pd.read_parquet(p)
            # Your dataset stores Timestamp as the index; convert it to a column
            if isinstance(df.index, pd.DatetimeIndex) and df.index.name:
                df = df.reset_index()
            frames.append(df)
        elif suffix == ".csv":
            df = pd.read_csv(p)
            frames.append(df)
        else:
            raise ValueError(f"Unsupported file type: {p} (supported: .parquet/.pq/.csv)")

    if not frames:
        raise FileNotFoundError("No input files found. Check config data.paths.")

    return pd.concat(frames, ignore_index=True)
