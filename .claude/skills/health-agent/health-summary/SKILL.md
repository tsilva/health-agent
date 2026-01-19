---
name: health-summary
description: Generate comprehensive health overview combining all data sources for a time period. Use when user asks to "summarize my health", "doctor visit prep", "health overview for 2024", "annual health summary", "prepare for my appointment", or needs a consolidated view of their health status.
---

# Health Summary

Comprehensive health report combining labs, timeline, exams, and narrative.

## Workflow

1. Get all data paths and demographics from profile
2. Determine date range (default: last 12 months)
3. Aggregate data from all sources
4. Organize by category
5. Generate discussion points

## Data Aggregation

### Labs Overview
1. Read `{labs_path}/all.csv`
2. Filter by date range
3. Identify:
   - Most recent value for each marker
   - Any abnormal values
   - Significant trends

### Health Events
1. Read `{health_log_path}/health_timeline.csv`
2. Filter by date range
3. Group by category:
   - Symptoms
   - Conditions
   - Medications
   - Procedures
   - Other

### Medical Exams
1. List `{exams_path}/*.summary.md`
2. Filter by date range
3. Extract key findings from each

### Narrative Highlights
1. Read `{health_log_path}/health_log.md`
2. Extract significant entries from date range

## Output Format

```
## Health Summary: {start_date} to {end_date}

**Profile**: {name}, {age}yo {gender}

---

### Lab Results Overview

**Most Recent Values**
| Marker      | Value | Date       | Status   |
|-------------|-------|------------|----------|
| Glucose     | 98    | 2024-06-01 | Normal   |
| HbA1c       | 5.8   | 2024-06-01 | Normal   |
| Cholesterol | 210   | 2024-06-01 | HIGH     |

**Abnormal Labs This Period**
- Cholesterol elevated on 2024-06-01, 2024-01-15
- LDL trending upward

---

### Health Events

**Conditions**
- Hypertension (ongoing, managed with medication)

**Symptoms**
- 2024-03-01: Upper respiratory infection (resolved)
- 2024-05-15: Knee pain (under investigation)

**Medications**
- Lisinopril 10mg daily (started 2023-06-01)
- Ibuprofen PRN for knee pain

**Procedures**
- 2024-05-20: Knee X-ray

---

### Medical Exams

| Date       | Type  | Region | Key Findings           |
|------------|-------|--------|------------------------|
| 2024-05-20 | xray  | knee   | Mild osteoarthritis    |
| 2024-01-15 | echo  | chest  | Normal cardiac function|

---

### Discussion Points for Provider

1. **Cholesterol management**: LDL elevated, discuss statin therapy
2. **Knee pain**: X-ray shows osteoarthritis, discuss treatment options
3. **Preventive care**: Due for colonoscopy screening (age-based)

---

### Questions to Ask

- Should I start cholesterol medication?
- What are options for knee pain management?
- Are there any additional tests needed?
```

## Date Range Handling

- Default: Last 12 months
- User can specify: "2024", "last 6 months", "since January"
- Parse natural language date expressions

## Discussion Points Generation

Automatically flag:
1. Abnormal labs needing follow-up
2. Unresolved symptoms
3. Medication reviews
4. Age-appropriate screenings due
5. Trends requiring attention
