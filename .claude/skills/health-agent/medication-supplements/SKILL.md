---
name: medication-supplements
description: Generate comprehensive medication and supplement reports with active/discontinued status tracking. Use when user asks "my medications", "medication list", "what supplements am I taking", "current meds", "provider medication list", "what am I currently taking", or needs a list for a healthcare provider.
---

# Medication & Supplements Report

Generate a comprehensive report of all medications and supplements with current status tracking.

## Workflow

1. Get health_log_path from the loaded profile
2. Extract medication and supplement entries from health_log.csv
3. Determine active/discontinued status for each item
4. Parse dosage information from Details column
5. Generate formatted report with tables and provider summary

## Efficient Data Access

Data files often exceed Claude's 256KB read limit. Use this extraction pattern:

### Extract Medications and Supplements
```bash
head -1 "{health_log_path}/health_log.csv" && grep -iE ",(medication|supplement)," "{health_log_path}/health_log.csv" | sort -t',' -k1
```

This extracts the header row plus all medication/supplement entries, sorted by date.

## Status Determination Logic

Analyze the `Event` column to determine current status:

### Active Keywords (most recent event)
- started
- prescribed
- continued
- refilled
- increased
- decreased
- taking
- began

### Discontinued Keywords (most recent event)
- stopped
- discontinued
- finished
- completed
- replaced by
- switched to
- ended
- no longer

### Status Algorithm
1. Group events by `Item` (medication/supplement name)
2. Sort events by `Date` descending
3. Check the most recent event for status keywords
4. If most recent event contains discontinued keywords → Discontinued
5. If most recent event contains active keywords → Active
6. If ambiguous, check for a more recent "started" event for the same item

## Dosage Parsing

Extract dosage information from the `Details` column:

### Common Patterns
- `{dose} {unit}` - e.g., "500 mg"
- `{dose} {unit} {frequency}` - e.g., "500 mg twice daily"
- `{dose} {unit} {frequency} {timing}` - e.g., "10 mg daily at bedtime"

### Frequency Terms
- daily, once daily, twice daily, 2x daily
- weekly, twice weekly
- as needed, PRN
- with meals, before bed, morning

## Output Format

```markdown
## Medication & Supplements Report

**Generated**: {current_date}
**Profile**: {profile_name}

---

### Active Medications

| Medication | Dosage | Frequency | Started | Last Updated |
|------------|--------|-----------|---------|--------------|
| Lisinopril | 10 mg | daily | 2023-05-15 | 2024-01-10 |

### Active Supplements

| Supplement | Dosage | Frequency | Started | Last Updated |
|------------|--------|-----------|---------|--------------|
| Vitamin D3 | 2000 IU | daily | 2022-01-01 | 2024-02-20 |

---

### Medication History (Discontinued)

| Medication | Dosage | Started | Stopped | Reason |
|------------|--------|---------|---------|--------|
| Amoxicillin | 500 mg 3x daily | 2024-01-05 | 2024-01-15 | Course completed |

### Supplement History (Discontinued)

| Supplement | Dosage | Started | Stopped | Reason |
|------------|--------|---------|---------|--------|
| Iron | 65 mg daily | 2023-06-01 | 2023-12-01 | Levels normalized |

---

### Provider Summary

**Current Medications:**
- Lisinopril 10 mg daily (since 2023-05-15)

**Current Supplements:**
- Vitamin D3 2000 IU daily (since 2022-01-01)

**Recent Changes (last 90 days):**
- {any starts, stops, or dose changes}

**Allergies/Intolerances:**
- {if available from health log}
```

## Additional Context

When generating the report, also check:

1. **Health Log Narrative** (`health_log.md`) for:
   - Reasons for starting/stopping medications
   - Side effects experienced
   - Effectiveness notes

2. **Related Episodes** for:
   - Conditions being treated
   - Treatment responses

### Extracting Context from Narrative
```bash
grep -i "{medication_name}" "{health_log_path}/health_log.md" | head -20
```

## Special Considerations

- **Prescription vs OTC**: Note if mentioned in Details
- **PRN Medications**: Flag as-needed medications separately
- **Interactions**: If user asks, cross-reference active medications
- **Refill Dates**: Calculate approximate refill dates if frequency known

## Optional: Pharmacogenomics Cross-Reference

If `genetics_23andme_path` is configured in the profile, add a pharmacogenomics section highlighting any medications affected by genetic variants.

### Extraction
```bash
# Check if genetics data available
test -f "{genetics_23andme_path}" && echo "Genetics data available"

# Extract pharmacogenomics SNPs
grep -E "^(rs3892097|rs1065852|rs4244285|rs4986893|rs12248560|rs1799853|rs1057910|rs9923231|rs4149056)" "{genetics_23andme_path}"
```

### Medication-Gene Mapping

| Drug/Class | Gene | CYP2D6 Affected | CYP2C19 Affected | CYP2C9 Affected |
|------------|------|-----------------|------------------|-----------------|
| Codeine, Tramadol | CYP2D6 | ✓ | | |
| Metoprolol | CYP2D6 | ✓ | | |
| Paroxetine, Fluoxetine | CYP2D6 | ✓ | | |
| Clopidogrel | CYP2C19 | | ✓ | |
| Omeprazole, Esomeprazole | CYP2C19 | | ✓ | |
| Citalopram, Escitalopram | CYP2C19 | | ✓ | |
| Warfarin | CYP2C9/VKORC1 | | | ✓ |
| Simvastatin | SLCO1B1 | | | |

### Output Section (if genetics available)

Add after Provider Summary:

```
---

### Pharmacogenomics Considerations

{If any current medications match affected gene pathways:}

| Medication | Gene | Your Status | Note |
|------------|------|-------------|------|
| {med} | {gene} | {status} | {consideration} |

*For comprehensive pharmacogenomics analysis, use the genetics-pharmacogenomics skill*
```

### Integration Notes
- Only add this section if genetics data is available AND relevant medications are found
- Don't add if no current medications are affected by tested genes
- Keep brief - link to full pharmacogenomics skill for details
