from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import yaml


@dataclass(frozen=True)
class AppConfig:
    # inputs
    data_paths: List[str]

    # parsing
    timestamp_col: str
    timezone: str

    # power columns (wide format)
    dc_input_power_regex: str  # must contain named groups: input, inv

    # enclosure inference + allocation
    battery_system_regex: str  # must contain named group: eid
    split_6: Tuple[int, int]   # e.g. (3,3)
    split_4: Tuple[int, int]   # e.g. (2,2)

    # output
    output_dir: str
    daily_table_file: str
    outliers_file: str
    heatmap_file: str


def _require(cfg: dict, path: str):
    cur = cfg
    for part in path.split("."):
        if part not in cur:
            raise KeyError(f"Missing config key: '{path}'")
        cur = cur[part]
    return cur


def load_config(path: str | Path) -> AppConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    data_paths = list(_require(cfg, "data.paths"))

    timestamp_col = str(_require(cfg, "parsing.timestamp_col"))
    timezone = str(_require(cfg, "parsing.timezone"))

    dc_input_power_regex = str(_require(cfg, "power.dc_input_power_regex"))

    battery_system_regex = str(_require(cfg, "allocation.battery_system_regex"))
    split_6_raw = _require(cfg, "allocation.split_6")
    split_4_raw = _require(cfg, "allocation.split_4")

    split_6 = (int(split_6_raw[0]), int(split_6_raw[1]))
    split_4 = (int(split_4_raw[0]), int(split_4_raw[1]))
    if len(split_6_raw) != 2 or len(split_4_raw) != 2:
        raise ValueError("allocation.split_6 and allocation.split_4 must be length-2 lists")

    output_dir = str(_require(cfg, "output.dir"))
    daily_table_file = str(_require(cfg, "output.daily_table_file"))
    outliers_file = _require(cfg, "output.outliers_file")
    heatmap_file = _require(cfg, "output.heatmap_file")


    return AppConfig(
        data_paths=data_paths,
        timestamp_col=timestamp_col,
        timezone=timezone,
        dc_input_power_regex=dc_input_power_regex,
        battery_system_regex=battery_system_regex,
        split_6=split_6,
        split_4=split_4,
        output_dir=output_dir,
        daily_table_file=daily_table_file,
        outliers_file=outliers_file,
        heatmap_file=heatmap_file,
    )
