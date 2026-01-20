---
name: out-of-range-labs
description: Identify abnormal lab values that fall outside reference ranges. Use when user asks for "abnormal labs", "which labs are out of range", "labs that need attention", "flagged results", "what's abnormal", or wants a prioritized view of concerning lab values.
---

# Out-of-Range Labs Analysis

Identify and prioritize abnormal lab values.

## Workflow

1. Get `labs_path` and demographics from the loaded profile
2. Check if `{labs_path}/lab_specs.json` exists for canonical names and units
3. Read `{labs_path}/all.csv`
4. Parse reference ranges for each lab
5. Classify values by severity
6. Apply age/gender context
7. Present prioritized results with canonical names (if available)

## Efficient Data Access

Data files often exceed Claude's 256KB read limit. Use these extraction patterns:

### Extract Abnormal Values Only (Most Efficient)
The CSV has `is_below_limit` and `is_above_limit` columns:
```bash
head -1 "{labs_path}/all.csv" && grep -E ",True," "{labs_path}/all.csv"
```

### Recent Abnormal Values (Last 12 Months)
```bash
head -1 "{labs_path}/all.csv" && grep "^202[56]-" "{labs_path}/all.csv" | grep -E ",True,"
```

### All Recent Labs for Context
```bash
head -1 "{labs_path}/all.csv" && grep "^202[56]-" "{labs_path}/all.csv" | sort -t',' -k1 -r | head -200
```

### Using lab_specs.json for Canonical Names
If `{labs_path}/lab_specs.json` exists:
```bash
# Source helper functions
source .claude/skills/health-agent/references/lab-specs-helpers.sh

# Get canonical name and primary unit for consistent reporting
canonical=$(get_canonical_name "{labs_path}/lab_specs.json" "{raw_marker_name}")
unit=$(get_primary_unit "{labs_path}/lab_specs.json" "{raw_marker_name}")

# Display: "{canonical} ({unit})" instead of raw lab_name from CSV
```

**Benefit**: Ensures consistent marker names across reports even when OCR variations exist.

## Severity Classification

### Critical (Immediate attention)
- Values in critical ranges (e.g., potassium <2.5 or >6.0, glucose <40)
- Far outside normal (>2x deviation from boundary)

### High/Low (Abnormal)
- Outside reference range but not critical

### Borderline (Monitor)
- Within 10% of reference range boundary

## Output Format

```
## Out-of-Range Labs Report

**Profile**: {name} ({age}yo {gender})

### Critical Values
| Date       | Marker    | Value | Range   | Status        |
|------------|-----------|-------|---------|---------------|
| 2024-06-01 | Potassium | 6.2   | 3.5-5.0 | CRITICAL HIGH |

### Abnormal Values
| Date       | Marker    | Value | Range   | Status |
|------------|-----------|-------|---------|--------|
| 2024-06-01 | Glucose   | 126   | 70-100  | HIGH   |
| 2024-05-15 | TSH       | 0.3   | 0.4-4.0 | LOW    |

### Borderline Values
| Date       | Marker    | Value | Range   | Status     |
|------------|-----------|-------|---------|------------|
| 2024-06-01 | LDL       | 128   | <130    | Borderline |

### Persistent Abnormalities
Markers abnormal on 2+ occasions:
- Glucose: HIGH on 2024-06-01, 2024-03-15, 2023-12-01
```

## Demographics Context

Use profile's `date_of_birth` and `gender` to:
1. Calculate current age
2. Apply age-specific adjustments (reference ranges vary by age for some markers)
3. Apply gender-specific ranges (reference ranges vary by gender for some markers)
4. Note when using adjusted ranges

## Reference Range Parsing

Handle formats:
- "70-100" → min=70, max=100
- "<100" → max=100, no min
- ">50" → min=50, no max
- "70-100 mg/dL" → strip unit, parse as range

## Persistent Abnormality Detection

Flag markers that are out of range on multiple occasions:
- Group by `lab_name`
- Identify markers with 2+ abnormal results
- List in separate section with all abnormal dates
