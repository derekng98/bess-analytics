# BESS Analytics

A small CLI-based analytics pipeline to turn raw BESS telemetry exports into daily enclosure-level energy metrics and a few sanity-check outputs.

The goal is to take messy, wide-format data and produce something that’s easy to reason about and review.

---

## What this does

Given time-series telemetry from a Battery Energy Storage Station, the pipeline produces:

- Daily charged energy per battery enclosure (kWh)
- Daily discharged energy per battery enclosure (kWh)
- A heatmap of discharged energy by day and enclosure
- An outlier table identifying the lowest-performing enclosures

All outputs are written to disk and are reproducible from configuration alone.

---

## Why this exists

The raw exports are wide (thousands of columns) and don’t include a clean `enclosure_id` field.  
They also expose power at the inverter DC input level, not at the individual battery enclosure level.

This repo handles:

- Parsing and loading the raw files
- Converting power to energy
- Allocating energy to enclosures
- Producing tidy outputs for further analysis

---

## Energy calculation approach

The dataset provides DC input power (kW) per inverter input.

Daily energy is calculated by integrating power over time:

- **discharged_kwh**: integration of positive DC power  
- **charged_kwh**: integration of negative DC power (absolute value)

Battery enclosures are not metered individually in the raw data.  
Energy is therefore allocated evenly across enclosures connected to the same DC input.

### Allocation rules

- Inverter groups with 6 enclosures → split 3 + 3  
- Inverter groups with 4 enclosures → split 2 + 2  

Enclosure grouping is inferred from column names such as:

```
[Battery system 1A1BAT1]
```

This logic is config-driven and can be changed if a different allocation model is required.

---

## Installation

Python 3.10 or newer is recommended.

```bash
pip install -e .
```

This installs the package in editable mode and registers the `bess-analytics` CLI.

---

## Running the pipeline

Create a local `config.yaml` (not committed to the repo) and point it at your data files.

```bash
bess-analytics run -c config.yaml
```

Outputs are written to the directory defined in the config.

---

## Example `config.yaml`

```yaml
data:
  paths:
    - "C:/path/to/data/*.parquet"

parsing:
  timestamp_col: "Timestamp"
  timezone: "Australia/Sydney"

power:
  # Matches: BESS1 DC Input Power (kW) [Battery Inverter 1APCS1]
  dc_input_power_regex: "^BESS(?P<input>[12]) DC Input Power \(kW\) \[Battery Inverter (?P<inv>[^\]]+)\]$"

allocation:
  # Matches: [Battery system 1A1BAT1]
  battery_system_regex: "\[Battery system (?P<eid>[^\]]+)\]"
  split_6: [3, 3]
  split_4: [2, 2]

output:
  dir: "out"
  daily_table_file: "daily_energy_by_enclosure.csv"
  outliers_file: "outliers_bottom5.csv"
  heatmap_file: "discharged_heatmap.png"
```

---

## Outputs

After a successful run, the following files are produced:

### `daily_energy_by_enclosure.csv`
Daily charged and discharged energy per enclosure

### `outliers_bottom5.csv`
Bottom 5 enclosures by total charged energy and total discharged energy

### `discharged_heatmap.png`
Heatmap of daily discharged energy (enclosures × days)

---

## Project structure

```
src/bess_analytics/
├── cli.py               # CLI entrypoint
├── pipeline.py          # Orchestration layer
├── io.py                # File loading (parquet / CSV)
├── energy_from_power.py # Power → energy logic and allocation
├── viz.py               # Outlier analysis and heatmap
└── config.py            # Config parsing and validation
```

---

## Packaging

The project follows a standard Python package layout and can be built into a wheel:

```bash
python -m build
```

Build artifacts are intentionally not committed.

---

## Notes

- Raw data files, outputs, and `config.yaml` are excluded from version control
- The pipeline is deterministic and reproducible
- The focus is on clarity and explicit assumptions rather than abstraction or optimisation
