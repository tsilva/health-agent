---
name: lab-trend
description: Analyze trends for specific lab markers over time. Use when user asks to "track my glucose", "cholesterol trend", "how has my TSH changed", "vitamin D over time", "show my A1C history", or wants to see how a biomarker has changed.
---

# Lab Trend Analysis

Analyze longitudinal trends for a specific lab marker.

## Workflow

1. Get `labs_path` from the loaded profile
2. Check if `{labs_path}/lab_specs.json` exists for canonical name lookup
3. Read `{labs_path}/all.csv`
4. Identify the marker using lab_specs.json (canonical names and aliases)
5. Filter rows where `lab_name` matches
6. Sort by `lab_date` ascending
7. Calculate statistics and trend
8. Present findings

## Efficient Data Access

Data files often exceed Claude's 256KB read limit. Use these extraction patterns:

### Check File Size First
```bash
wc -l "{labs_path}/all.csv"
```
If >3000 lines, use filtered extraction below instead of direct read.

### Extract Specific Marker (Recommended)

**With lab_specs.json** (more accurate):
```bash
# Source helper functions
source .claude/skills/health-agent/references/lab-specs-helpers.sh

# Check if lab_specs.json exists and build pattern
if has_lab_specs "{labs_path}/lab_specs.json"; then
    pattern=$(build_grep_pattern "{labs_path}/lab_specs.json" "{marker_name}")
    if [ -n "$pattern" ]; then
        head -1 "{labs_path}/all.csv" && grep -iE "$pattern" "{labs_path}/all.csv" | sort -t',' -k1
    else
        # Marker not in lab_specs.json, fall back to manual pattern
        head -1 "{labs_path}/all.csv" && grep -i "{marker_name}" "{labs_path}/all.csv" | sort -t',' -k1
    fi
else
    # No lab_specs.json, use manual pattern
    head -1 "{labs_path}/all.csv" && grep -i "{marker_name}" "{labs_path}/all.csv" | sort -t',' -k1
fi
```

**Without lab_specs.json** (fallback):
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

### With lab_specs.json (Preferred)
If `{labs_path}/lab_specs.json` exists:
1. Use `build_grep_pattern()` from lab-specs-helpers.sh
2. Get canonical name with `get_canonical_name()` for display
3. Get primary unit with `get_primary_unit()` for reporting
4. Provides most accurate matching via canonical names + aliases

### Without lab_specs.json (Fallback)
Use case-insensitive fuzzy matching directly on lab_name values in all.csv:
- Try variations: "A1C", "HbA1c", "Hemoglobin A1c", "Glycated Hemoglobin"
- Use grep with `-iE` for case-insensitive pattern matching
- May miss some aliases without lab_specs.json

**Note**: lab_specs.json (from labs-parser) is the authoritative source for canonical names, aliases, reference ranges, and unit conversions.
