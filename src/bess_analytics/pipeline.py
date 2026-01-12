from __future__ import annotations
from pathlib import Path
from .config import AppConfig
from .energy_from_power import AllocationConfig, daily_energy_by_enclosure_from_dc_input_power
from .io import expand_globs, load_files
from .viz import make_outliers_table, save_discharged_heatmap

def run_daily(cfg: AppConfig) -> Path:
    files = expand_globs(cfg.data_paths)
    df = load_files(files)

    alloc = AllocationConfig(
        dc_input_power_regex=cfg.dc_input_power_regex,
        battery_system_regex=cfg.battery_system_regex,
        split_6=cfg.split_6,
        split_4=cfg.split_4,
    )

    daily = daily_energy_by_enclosure_from_dc_input_power(
        df=df,
        timestamp_col=cfg.timestamp_col,
        timezone=cfg.timezone,
        cfg=alloc,
    )

    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Save the daily table
    daily_path = out_dir / cfg.daily_table_file
    daily.to_csv(daily_path, index=False)

    # 2) Outliers table
    outliers = make_outliers_table(daily, n=5)
    outliers_path = out_dir / cfg.outliers_file
    outliers.to_csv(outliers_path, index=False)

    # 3) Heatmap
    heatmap_path = out_dir / cfg.heatmap_file
    save_discharged_heatmap(daily, heatmap_path)

    return daily_path

