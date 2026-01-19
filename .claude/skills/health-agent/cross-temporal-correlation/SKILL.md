---
name: cross-temporal-correlation
description: Find patterns and correlations between health events and lab values over time. Use when user asks about "correlation between X and Y", "patterns in my data", "do symptoms affect labs", "relationship between stress and blood pressure", "what triggers my migraines", or wants to discover connections in their health data.
---

# Cross-Temporal Correlation Analysis

Discover patterns between health events and biomarker changes.

## Workflow

1. Get all data paths from profile
2. Build unified timeline (events + labs)
3. Identify correlation targets (user-specified or auto-detect)
4. Search for temporal patterns
5. Assess significance
6. Present findings with appropriate caveats

## Unified Timeline Construction

1. Read `{health_log_path}/health_timeline.csv`
2. Read `{labs_path}/all.csv`
3. Merge into single timeline sorted by date
4. Tag each entry as `event` or `lab`

## Pattern Detection

### Event → Lab Correlation
Find if specific events precede lab changes:
1. Identify all instances of the event type
2. Find labs within 1-14 days after each event
3. Calculate average change vs baseline
4. Require 3+ occurrences for significance

### Lab → Event Correlation
Find if abnormal labs precede events:
1. Identify abnormal lab occurrences
2. Find events within 7 days after
3. Look for recurring patterns

### Significance Thresholds
- Minimum occurrences: 3
- Minimum change: >10% from baseline
- Consistent direction (same increase/decrease pattern)

## Output Format

```
## Correlation Analysis: {factor_A} ↔ {factor_B}

**Analysis Period**: {date_range}
**Data Points**: {count} events, {count} labs

---

### Findings

#### Pattern 1: {description}
**Confidence**: Moderate (4 occurrences, consistent direction)

After "{event_type}" events, {lab_marker} shows:
- Average change: +15% within 7 days
- Observed instances:
  | Event Date | Event         | Lab Date   | Lab Value | Change |
  |------------|---------------|------------|-----------|--------|
  | 2024-03-01 | High stress   | 2024-03-05 | 145       | +12%   |
  | 2024-04-15 | High stress   | 2024-04-20 | 152       | +18%   |
  | 2024-06-01 | High stress   | 2024-06-07 | 148       | +14%   |
  | 2024-07-20 | High stress   | 2024-07-25 | 150       | +16%   |

#### Pattern 2: {description}
**Confidence**: Low (2 occurrences, needs more data)
...

---

### No Significant Correlation Found
The following relationships were analyzed but showed no consistent pattern:
- {factor_X} and {factor_Y}: Only 1 occurrence
- {factor_A} and {factor_B}: Inconsistent direction

---

### Disclaimer

This analysis identifies temporal associations, not causation. Patterns found:
- May be coincidental
- May have confounding factors
- Should be discussed with a healthcare provider
- Are based on limited personal data, not clinical studies

Always consult a medical professional before making health decisions based on these findings.
```

## Auto-Detection Mode

When user asks for general patterns without specifying factors:
1. Find all abnormal labs
2. Find events within ±14 days of each
3. Group by event category
4. Report categories with 3+ co-occurrences

## User-Specified Analysis

When user asks about specific correlation:
1. Parse the two factors (e.g., "stress" and "blood pressure")
2. Map to data columns:
   - Events: search `category` and `event` columns
   - Labs: search `lab_name` column (use marker aliases)
3. Run targeted correlation analysis

## Confidence Levels

- **High**: 5+ occurrences, >15% consistent change
- **Moderate**: 3-4 occurrences, >10% consistent change
- **Low**: 2 occurrences or inconsistent pattern
- **Insufficient**: <2 occurrences
