# Findings and limits

The [UCI Appliances Energy Prediction dataset](https://archive.ics.uci.edu/dataset/374/appliances%2Benergy%2Bprediction) contains 19,735 consecutive ten-minute observations from **one low-energy home** between 11 January and 27 May 2016. The raw source has no missing cells, duplicate timestamps, or gaps in the ten-minute sequence. Its first and last dates are partial; the 136 intervening days each have 144 intervals.

## Reconciled KPIs

| Measure | Result | Basis |
|---|---:|---|
| Appliance energy | 1,928.01 kWh | Sum of `Appliances` Wh / 1,000 across all intervals |
| Lighting energy | 75.03 kWh | Sum of `lights` Wh / 1,000 across all intervals |
| Metered appliances + lights | 2,003.04 kWh | Sum of the two above; **not total household energy** |
| Mean appliance energy | 97.695 Wh per ten-minute interval | All 19,735 intervals |
| Median appliance energy | 60 Wh per interval | All intervals |
| High-use threshold | 330 Wh per interval | 95th percentile, including ties |
| High-use intervals | 1,001 | Appliance Wh ≥ 330; ties make this 5.07% of records |

## Pattern review

- On 136 complete days, appliance energy totals 1,907.41 kWh. The highest complete day is **4 April 2016, 27.15 kWh**; the lowest is **28 January 2016, 5.40 kWh**.
- The mean ten-minute appliance reading peaks at **18:00 (190.17 Wh)** and reaches its lowest hourly mean at **03:00 (48.16 Wh)** on complete days. This is a descriptive within-home pattern, not a tariff or occupancy estimate.
- Complete-day appliance use averages **13.85 kWh per weekday** (98 days) and **14.48 kWh per weekend day** (38 days), a roughly 4.6% higher weekend mean. No control for weather, occupancy, holidays, or season is applied.
- The complete-day monthly mean ranges from **13.39 kWh/day in May** (26 complete days) to **14.54 kWh/day in February** (29 days). Comparing raw monthly totals would be misleading because months have different numbers of observed days.

## Interpretation limits

The source covers a single building over roughly 4.5 months. It does not contain total whole-home energy, energy prices, household occupancy, or intervention records. The weather-station variables were merged from a nearby airport and some are interpolated. Associations between weather, time, and appliance energy should not be described as causal effects or generalized to other homes. The two random variables `rv1` and `rv2` are excluded from the reporting table because they are non-predictive test columns in the source.
