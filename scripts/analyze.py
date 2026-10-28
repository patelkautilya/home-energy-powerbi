"""Prepare and reconcile UCI home-energy records for the Power BI case study."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
SOURCE = DATA / "source.zip"
SOURCE_URL = "https://archive.ics.uci.edu/static/public/374/appliances%2Benergy%2Bprediction.zip"


def main() -> None:
    DATA.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    if not SOURCE.exists():
        urlretrieve(SOURCE_URL, SOURCE)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with ZipFile(SOURCE) as archive:
        raw = pd.read_csv(archive.open("energydata_complete.csv"))
    if raw.shape != (19735, 29) or raw.isna().any().any():
        raise ValueError(f"Unexpected source shape or nulls: {raw.shape}")
    raw["timestamp"] = pd.to_datetime(raw["date"], errors="raise")
    if raw["timestamp"].duplicated().any() or not raw["timestamp"].is_monotonic_increasing:
        raise ValueError("Duplicate or unordered timestamps")
    interval = raw["timestamp"].diff().dropna()
    if not interval.eq(pd.Timedelta(minutes=10)).all():
        raise ValueError("The series is not uniformly spaced at ten minutes")
    if (raw[["Appliances", "lights"]] < 0).any().any():
        raise ValueError("Negative metered energy")

    df = pd.DataFrame({
        "Timestamp": raw["timestamp"],
        "Date": raw["timestamp"].dt.strftime("%Y-%m-%d"),
        "YearMonth": raw["timestamp"].dt.strftime("%Y-%m"),
        "Month": raw["timestamp"].dt.month,
        "Day": raw["timestamp"].dt.day,
        "Hour": raw["timestamp"].dt.hour,
        "WeekdayNumber": raw["timestamp"].dt.dayofweek + 1,
        "Weekday": raw["timestamp"].dt.day_name(),
        "DayType": np.where(raw["timestamp"].dt.dayofweek >= 5, "Weekend", "Weekday"),
        "ApplianceWh": raw["Appliances"],
        "LightingWh": raw["lights"],
        "MeteredWh": raw["Appliances"] + raw["lights"],
        "ApplianceKWh": raw["Appliances"] / 1000,
        "LightingKWh": raw["lights"] / 1000,
        "MeteredKWh": (raw["Appliances"] + raw["lights"]) / 1000,
        "KitchenTempC": raw["T1"].round(2),
        "LivingTempC": raw["T2"].round(2),
        "OutdoorTempC": raw["T_out"].round(2),
        "OutdoorHumidityPct": raw["RH_out"].round(2),
        "RowCount": 1,
    })
    counts = df.groupby("Date")["RowCount"].transform("sum")
    df["CompleteDay"] = (counts == 144).astype(int)
    threshold = float(df["ApplianceWh"].quantile(0.95))
    df["HighUseInterval"] = (df["ApplianceWh"] >= threshold).astype(int)
    df.to_csv(DATA / "events.csv", index=False, float_format="%.3f")

    full = df[df["CompleteDay"] == 1]
    daily = full.groupby("Date", as_index=False).agg(
        ApplianceKWh=("ApplianceKWh", "sum"),
        LightingKWh=("LightingKWh", "sum"),
        MeteredKWh=("MeteredKWh", "sum"),
        MeanOutdoorTempC=("OutdoorTempC", "mean"),
        HighUseIntervals=("HighUseInterval", "sum"),
    )
    daily.to_csv(REPORTS / "daily-full-days.csv", index=False, float_format="%.3f")
    hourly = full.groupby("Hour", as_index=False).agg(
        MeanApplianceWh=("ApplianceWh", "mean"),
        MeanLightingWh=("LightingWh", "mean"),
        Intervals=("RowCount", "sum"),
    )
    hourly.to_csv(REPORTS / "hourly-profile.csv", index=False, float_format="%.3f")
    daytype = full.groupby("DayType", as_index=False).agg(
        ApplianceKWh=("ApplianceKWh", "sum"),
        Intervals=("RowCount", "sum"),
        Days=("Date", "nunique"),
    )
    daytype["ApplianceKWhPerDay"] = daytype["ApplianceKWh"] / daytype["Days"]
    daytype.to_csv(REPORTS / "daytype.csv", index=False, float_format="%.3f")
    monthly = full.groupby("YearMonth", as_index=False).agg(
        ApplianceKWh=("ApplianceKWh", "sum"),
        Days=("Date", "nunique"),
    )
    monthly["ApplianceKWhPerDay"] = monthly["ApplianceKWh"] / monthly["Days"]
    monthly.to_csv(REPORTS / "monthly-full-days.csv", index=False, float_format="%.3f")

    metrics = {
        "source_sha256": source_hash,
        "records": len(df),
        "first_timestamp": str(df["Timestamp"].min()),
        "last_timestamp": str(df["Timestamp"].max()),
        "missing_intervals": 0,
        "complete_days": int(daily.shape[0]),
        "partial_days": int(df["Date"].nunique() - daily.shape[0]),
        "appliance_kwh_all_intervals": round(float(df["ApplianceKWh"].sum()), 3),
        "lighting_kwh_all_intervals": round(float(df["LightingKWh"].sum()), 3),
        "metered_kwh_all_intervals": round(float(df["MeteredKWh"].sum()), 3),
        "appliance_kwh_full_days": round(float(full["ApplianceKWh"].sum()), 3),
        "mean_appliance_wh_per_interval": round(float(df["ApplianceWh"].mean()), 3),
        "median_appliance_wh_per_interval": round(float(df["ApplianceWh"].median()), 3),
        "p95_appliance_wh_per_interval": threshold,
        "high_use_intervals": int(df["HighUseInterval"].sum()),
        "top_daily_kwh_date": daily.loc[daily["ApplianceKWh"].idxmax(), "Date"],
        "top_daily_kwh": round(float(daily["ApplianceKWh"].max()), 3),
        "lowest_daily_kwh_date": daily.loc[daily["ApplianceKWh"].idxmin(), "Date"],
        "lowest_daily_kwh": round(float(daily["ApplianceKWh"].min()), 3),
    }
    (REPORTS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
