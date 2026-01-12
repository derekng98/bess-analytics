from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def make_outliers_table(daily: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Returns a tidy table of bottom-N enclosures by charged and discharged energy
    across the whole dataset (sum over days).
    """
    totals = (
        daily.groupby("enclosure_id", as_index=False)[["charged_kwh", "discharged_kwh"]]
        .sum()
        .rename(columns={"charged_kwh": "total_charged_kwh", "discharged_kwh": "total_discharged_kwh"})
    )

    low_charge = totals.nsmallest(n, "total_charged_kwh").assign(metric="lowest_charged")
    low_discharge = totals.nsmallest(n, "total_discharged_kwh").assign(metric="lowest_discharged")

    out = pd.concat([low_charge, low_discharge], ignore_index=True)
    out = out[["metric", "enclosure_id", "total_charged_kwh", "total_discharged_kwh"]]
    return out


def save_discharged_heatmap(daily: pd.DataFrame, out_path: Path) -> None:
    """
    Heatmap: rows=enclosures, cols=day, values=discharged_kwh
    """
    # pivot to matrix
    mat = daily.pivot(index="enclosure_id", columns="day", values="discharged_kwh").fillna(0)

    # Make it look good:
    # - larger figure if many enclosures
    # - use seaborn's default colormap (no hardcoded colors)
    fig_w = max(10, 0.9 * len(mat.columns))
    fig_h = max(10, 0.03 * len(mat.index))  # 342 rows -> ~10+
    plt.figure(figsize=(fig_w, fig_h))

    ax = sns.heatmap(
        mat,
        linewidths=0.0,
        cbar_kws={"label": "Discharged energy (kWh)"},
    )
    ax.set_title("Daily Discharged Energy by BESS Enclosure")
    ax.set_xlabel("Day")
    ax.set_ylabel("Enclosure")

    # tighten layout for saving
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close()
