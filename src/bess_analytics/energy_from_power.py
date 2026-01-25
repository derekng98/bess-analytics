from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd


@dataclass(frozen=True)
class AllocationConfig:
    dc_input_power_regex: str
    battery_system_regex: str
    split_6: Tuple[int, int] = (3, 3)
    split_4: Tuple[int, int] = (2, 2)


def _localize(ts: pd.Series, timezone: str) -> pd.Series:
    ts = pd.to_datetime(ts, errors="coerce")
    if ts.isna().all():
        raise ValueError("All timestamps failed to parse. Check parsing.timestamp_col.")

    # If tz-naive, treat as local time in timezone.
    if ts.dt.tz is None:
        ts = ts.dt.tz_localize(timezone)
    else:
        ts = ts.dt.tz_convert(timezone)
    return ts


def infer_enclosure_map(columns: List[str], cfg: AllocationConfig) -> Dict[Tuple[str, int], List[str]]:
    """
    Build mapping: (inverter_group, dc_input) -> [enclosure_ids]
    inverter_group is like '1A1' from inverter '1APCS1' (remove 'PCS').
    battery systems are like '1A1BAT1', ... '1A1BAT6'
    """
    bs_pat = re.compile(cfg.battery_system_regex)

    eids = set()
    for c in columns:
        m = bs_pat.search(str(c))
        if m:
            eids.add(m.group("eid"))

    groups: Dict[str, List[str]] = {}
    for eid in eids:
        m = re.match(r"(?P<grp>\d[AB]\d)BAT(?P<n>\d+)$", eid)
        if not m:
            continue
        grp = m.group("grp")
        groups.setdefault(grp, []).append(eid)

    # sort BATs numerically within each group
    def bat_num(x: str) -> int:
        return int(re.search(r"BAT(\d+)$", x).group(1))

    for grp, lst in groups.items():
        lst.sort(key=bat_num)

    mapping: Dict[Tuple[str, int], List[str]] = {}
    for grp, lst in groups.items():
        if len(lst) == 6:
            a, b = cfg.split_6
            mapping[(grp, 1)] = lst[:a]
            mapping[(grp, 2)] = lst[a : a + b]
        elif len(lst) == 4:
            a, b = cfg.split_4
            mapping[(grp, 1)] = lst[:a]
            mapping[(grp, 2)] = lst[a : a + b]
        else:
            # best-effort split
            mid = len(lst) // 2
            mapping[(grp, 1)] = lst[:mid]
            mapping[(grp, 2)] = lst[mid:]
    return mapping


def daily_energy_by_enclosure_from_dc_input_power(
    df: pd.DataFrame,
    timestamp_col: str,
    timezone: str,
    cfg: AllocationConfig,
) -> pd.DataFrame:
    dc_pat = re.compile(cfg.dc_input_power_regex)

    meta = []
    for c in df.columns:
        m = dc_pat.match(str(c))
        if m:
            dc_input = int(m.group("input"))  # 1 or 2
            inv_code = m.group("inv")         # e.g. "1APCS1"
            inv_group = inv_code.replace("PCS", "")  # -> "1A1"
            meta.append((str(c), inv_group, dc_input))

    if not meta:
        raise ValueError("No DC input power columns matched power.dc_input_power_regex")

    if timestamp_col not in df.columns:
        raise KeyError(f"Timestamp column '{timestamp_col}' not found. (Did you reset parquet index?)")

    df2 = df.copy()
    df2["_ts"] = _localize(df2[timestamp_col], timezone)
    df2 = df2.sort_values("_ts")
    

    # compute dt in hours
    dt = df2["_ts"].diff().dt.total_seconds().div(3600.0)
    dt_median = float(dt.dropna().median()) if dt.notna().any() else 1.0 / 60.0

    # ignore large timestamp gaps 
    gap_threshold_h = max(5 / 60.0, 3 * dt_median)
    dt = dt.mask(dt > gap_threshold_h, 0.0)
    
    df2["_dt_h"] = dt.fillna(dt_median)

    df2["day"] = df2["_ts"].dt.floor("D").dt.date

    power_cols = [c for (c, _, _) in meta]
    P = df2[power_cols]

    # discharged: positive kW integrated -> kWh
    discharged = P.clip(lower=0).mul(df2["_dt_h"], axis=0).groupby(df2["day"]).sum()
    # charged: negative kW (make positive) integrated -> kWh
    charged = (-P.clip(upper=0)).mul(df2["_dt_h"], axis=0).groupby(df2["day"]).sum()

    rows = []
    for c, inv_group, dc_input in meta:
        for day, ch in charged[c].items():
            dis = float(discharged.loc[day, c])
            rows.append((day, inv_group, dc_input, float(ch), dis))

    daily_input = pd.DataFrame(rows, columns=["day", "inv_group", "dc_input", "charged_kwh", "discharged_kwh"])

    mapping = infer_enclosure_map(list(df.columns), cfg)

    out_rows = []
    for r in daily_input.itertuples(index=False):
        eids = mapping.get((r.inv_group, r.dc_input))
        if not eids:
            continue
        w = 1.0 / len(eids)
        for eid in eids:
            out_rows.append((r.day, eid, r.charged_kwh * w, r.discharged_kwh * w))

    out = pd.DataFrame(out_rows, columns=["day", "enclosure_id", "charged_kwh", "discharged_kwh"])
    out = out.groupby(["day", "enclosure_id"], as_index=False).sum()
    out = out.sort_values(["day", "enclosure_id"]).reset_index(drop=True)
    return out
