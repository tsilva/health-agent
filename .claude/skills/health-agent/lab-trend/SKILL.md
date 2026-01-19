---
name: lab-trend
description: Analyze trends for specific lab markers over time. Use when user asks to "track my glucose", "cholesterol trend", "how has my TSH changed", "vitamin D over time", "show my A1C history", or wants to see how a biomarker has changed.
---

# Lab Trend Analysis

Analyze longitudinal trends for a specific lab marker.

## Workflow

1. Get `labs_path` from the loaded profile
2. Read `{labs_path}/all.csv`
3. Identify the marker (use fuzzy matching, see `references/common-markers.md` for aliases)
4. Filter rows where `lab_name` matches
5. Sort by `lab_date` ascending
6. Calculate statistics and trend
7. Present findings

## Efficient Data Access

Data files often exceed Claude's 256KB read limit. Use these extraction patterns:

### Check File Size First
```bash
wc -l "{labs_path}/all.csv"
```
If >3000 lines, use filtered extraction below instead of direct read.

### Extract Specific Marker (Recommended)
```bash
head -1 "{labs_path}/all.csv" && grep -i "{marker_name}" "{labs_path}/all.csv" | sort -t',' -k1
```

### Extract by Date Range
```bash
head -1 "{labs_path}/all.csv" && grep "^202[45]-" "{labs_path}/all.csv" | grep -i "{marker_name}"
```

Replace `{marker_name}` with search term (e.g., "TSH", "glucose", "vitamin d").

## Statistics to Calculate

- **Count**: Total number of measurements
- **Date range**: First and last measurement dates
- **Min/Max**: Lowest and highest values with dates
- **Mean**: Average value
- **Trend**: Direction of change (improving, worsening, stable)
  - Compare first 3 values average to last 3 values average
  - >10% change = trending; otherwise stable

## Output Format

```
## {Marker Name} Trend Analysis

**Summary**
- Measurements: {count} over {date_range}
- Range: {min} - {max} {unit}
- Average: {mean} {unit}
- Trend: {trend_direction}

**Reference Range**: {reference_range}

**Timeline**
| Date       | Value  | Status        | Confidence |
|------------|--------|---------------|------------|
| 2024-06-15 | 95     | Normal        | 0.95       |
| 2024-03-10 | 110    | HIGH          | 0.92       |
| 2023-12-01 | 102    | Borderline    | 0.88*      |

*Values with confidence <0.8 flagged for verification
```

## Confidence Handling

- Flag values with `confidence < 0.8` with asterisk
- Add note suggesting manual verification for flagged values

## Reference Range Interpretation

1. Parse `lab_reference_range` (formats: "70-100", "<100", ">50", "70-100 mg/dL")
2. Classify each value:
   - **Normal**: Within range
   - **Borderline**: Within 10% of boundary
   - **HIGH/LOW**: Outside range

## Marker Matching

Use case-insensitive fuzzy matching. See `../references/common-markers.md` for:
- Alias mappings (e.g., "A1C" → "HbA1c")
- Age/gender-specific ranges
