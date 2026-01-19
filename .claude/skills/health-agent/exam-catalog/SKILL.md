---
name: exam-catalog
description: Index and search medical exam summaries (MRI, CT, ultrasound, X-ray, etc.). Use when user asks to "list my exams", "find my MRI", "show ultrasounds", "exam history", "what imaging have I had", or wants to browse/filter medical imaging and procedure records.
---

# Exam Catalog

Index and search medical exam summaries from the exams_path.

## Workflow

1. Get `exams_path` from the loaded profile
2. List all `*.summary.md` files in that directory
3. Parse YAML frontmatter from each file to extract:
   - `exam_type` (ultrasound, mri, ct, xray, etc.)
   - `exam_date` (YYYY-MM-DD)
   - `body_region` (abdomen, chest, etc.)
   - `provider` (facility name)
4. Apply user filters (type, region, date range, keyword)
5. Present results as a summary table

## Output Format

### Summary Table

```
| Date       | Type       | Region   | Provider        |
|------------|------------|----------|-----------------|
| 2024-03-15 | ultrasound | abdomen  | City Radiology  |
| 2024-01-10 | xray       | chest    | Regional Med    |
```

### Detail View

When user requests details on a specific exam:
1. Read the full `.summary.md` file
2. Present frontmatter metadata
3. Present the findings section

## Filter Examples

- "show all MRIs" → filter by `exam_type: mri`
- "abdominal imaging" → filter by `body_region: abdomen`
- "exams from 2024" → filter by `exam_date` year
- "find kidney" → keyword search in file content
