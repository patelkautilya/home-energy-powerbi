# Field guide and report definitions

Each row in `data/events.csv` is one ten-minute interval. `Timestamp` is local timestamp as provided by the source, with no timezone specified. `Date`, `YearMonth`, `Hour`, `Weekday`, and `DayType` are derived from it. `CompleteDay=1` identifies dates with all 144 ten-minute readings; 136 dates are complete and two edge dates are partial.

`ApplianceWh` and `LightingWh` are measured energy in Wh **for each ten-minute interval**. `ApplianceKWh`, `LightingKWh`, and `MeteredKWh` divide their corresponding Wh fields by 1,000, so sums yield kWh. `MeteredKWh` covers appliances and lights, not heating or other unmetered loads. `RowCount=1` counts intervals.

`KitchenTempC`, `LivingTempC`, `OutdoorTempC`, and `OutdoorHumidityPct` are descriptive conditions. `HighUseInterval=1` marks `ApplianceWh >= 330` Wh, the sample's 95th percentile including ties. `rv1` and `rv2` are dropped.

The Power BI KPI page uses `SUM(ApplianceKWh)`, `SUM(LightingKWh)`, `SUM(MeteredKWh)`, and `SUM(RowCount)` across all intervals. `AVERAGE(ApplianceWh)` by `Hour`, `DayType`, or the Date hierarchy gives a per-ten-minute mean, which remains comparable despite the two partial edge days. The `reports/monthly-full-days.csv` reconciliation instead shows kWh **per complete day**. Do not compare raw monthly kWh totals without accounting for the differing number of observed days. The high-use chart uses `SUM(HighUseInterval)` by `Hour`. A slicer selection changes the filter context; the report's Day Type slicer was verified against the independent weekend total.
