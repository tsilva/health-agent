---
name: genetics-pharmacogenomics
description: Analyze drug metabolism genetic variants and their clinical implications. Use when user asks "drug metabolism", "CYP2D6 status", "pharmacogenomics", "medication genetics", "how do I metabolize drugs", "warfarin genetics", or wants to understand how genetics affects their medications.
---

# Pharmacogenomics Analysis

Comprehensive analysis of genetic variants affecting drug metabolism, efficacy, and safety.

## Prerequisites

- Profile must have `genetics_23andme_path` configured
- Uses `genetics-snp-lookup` skill for all SNP interpretations

## Workflow

1. Get `genetics_23andme_path` from the loaded profile
2. Optionally get current medications from health_log if available
3. **Delegate to genetics-snp-lookup**: Request pharmacogenomics analysis for all relevant genes:
   - CYP2D6 (opioids, antidepressants, antipsychotics)
   - CYP2C19 (clopidogrel, PPIs, antidepressants)
   - CYP2C9 (warfarin, NSAIDs)
   - VKORC1 (warfarin sensitivity)
   - SLCO1B1 (statin transport)
   - TPMT (thiopurines)
   - DPYD (fluoropyrimidines)
4. Receive genotypes, metabolizer statuses, and clinical interpretations from genetics-snp-lookup
5. Format results into provider-friendly report (see Output Format below)
6. Cross-reference with current medications if available

## Genes Analyzed

genetics-snp-lookup provides interpretation for these genes via SNPedia:

| Gene | Function | Key Medications |
|------|----------|-----------------|
| CYP2D6 | Opioids, antidepressants, antipsychotics | Codeine, tramadol, paroxetine, metoprolol, tamoxifen |
| CYP2C19 | Clopidogrel, PPIs, antidepressants | Clopidogrel, omeprazole, citalopram |
| CYP2C9 | Warfarin, NSAIDs | Warfarin, ibuprofen, phenytoin |
| VKORC1 | Warfarin sensitivity | Warfarin (combined with CYP2C9) |
| SLCO1B1 | Statin transport | Simvastatin, atorvastatin |
| TPMT | Thiopurines | Azathioprine, 6-mercaptopurine |
| DPYD | Fluoropyrimidines | 5-fluorouracil, capecitabine |

## Calling genetics-snp-lookup

Use genetics-snp-lookup in **gene-based pharmacogenomics mode**:

```
For each gene in [CYP2D6, CYP2C19, CYP2C9, VKORC1, SLCO1B1, TPMT, DPYD]:
  Call genetics-snp-lookup with: "look up {gene} pharmacogenomics"

genetics-snp-lookup will:
1. Query SNPedia for gene's clinically relevant rsIDs
2. Extract those SNPs from 23andMe data
3. Fetch interpretations from SNPedia
4. Return metabolizer status, affected drugs, dosing guidance
```

**Do NOT**:
- Duplicate SNP extraction logic
- Hardcode rsID lists
- Reimplement metabolizer status determination
- Query SNPedia directly

genetics-snp-lookup is the centralized lookup mechanism for all genetics queries.

## Output Format

Format the genetics-snp-lookup results into this provider-friendly structure:

```markdown
## Pharmacogenomics Report

**Generated**: {date}
**Profile**: {name}

---

### Summary

| Gene | Genotype | Metabolizer Status | Clinical Significance |
|------|----------|-------------------|----------------------|
| CYP2D6 | *1/*4 | Intermediate | Reduced opioid/antidepressant metabolism |
| CYP2C19 | *1/*2 | Intermediate | Clopidogrel may have reduced efficacy |
| CYP2C9 | *1/*1 | Normal | Standard warfarin metabolism |
| VKORC1 | A/G | Increased sensitivity | Warfarin dose reduction may be needed |
| SLCO1B1 | T/C | Intermediate | Moderate statin myopathy risk |
| TPMT | Normal | Normal | Standard thiopurine dosing |
| DPYD | Normal | Normal | Standard fluoropyrimidine dosing |

---

### Detailed Findings

#### CYP2D6 - Drug Metabolism Enzyme

**Genotype**: *1/*4 (rs3892097 G/A)
**Status**: Intermediate Metabolizer

**Clinical Implications**:
- Opioids (codeine, tramadol): May have reduced pain relief from prodrugs
- Antidepressants (paroxetine, fluoxetine): May need dose adjustment
- Consider non-CYP2D6 alternatives when available

{Repeat for each gene with variants...}

---

### Current Medication Interactions

{If health_log available and medications found:}

| Current Medication | Relevant Gene | Your Status | Recommendation |
|-------------------|---------------|-------------|----------------|
| Metoprolol | CYP2D6 | Intermediate | Monitor for increased effect |

---

### Recommendations

1. **Share with providers**: This information may affect medication dosing
2. **Medication reviews**: Consider pharmacogenomic implications for new prescriptions
3. **Confirm results**: 23andMe is not a clinical test; confirm critical findings with clinical testing

---

### Limitations

- 23andMe tests limited SNPs; does not detect all variants
- Copy number variations (especially CYP2D6) not detected
- Star allele (*) assignments are approximations
- Results should be confirmed before medical decisions

**Data Source**: SNPedia via genetics-snp-lookup skill (cached interpretations)
```

## Cross-Reference with Current Medications

If `health_log_path` is available:

1. Extract current medications from health_log.csv:
   ```bash
   head -1 "{health_log_path}/health_log.csv" && \
   grep -iE ",(medication|supplement)," "{health_log_path}/health_log.csv" | \
   sort -t',' -k1 -r | head -50
   ```

2. For each active medication, check if it's metabolized by tested enzymes

3. Highlight any potential interactions or dosing considerations

### Medication-Gene Mappings

Use these to identify relevant genetics for current medications:

| Medication Class | Relevant Gene | Notes |
|-----------------|---------------|-------|
| Codeine, Tramadol | CYP2D6 | Prodrugs - avoid in PM |
| Clopidogrel | CYP2C19 | Reduced efficacy in PM |
| Warfarin | CYP2C9 + VKORC1 | Combined dosing algorithm |
| Simvastatin | SLCO1B1 | Myopathy risk |
| Omeprazole | CYP2C19 | Efficacy varies |
| Metoprolol | CYP2D6 | Dose adjustment may be needed |
| SSRIs (paroxetine, fluoxetine) | CYP2D6 | Plasma level variations |
| NSAIDs (ibuprofen) | CYP2C9 | Minor effect on metabolism |
| Azathioprine | TPMT | Critical - toxicity risk |
| 5-FU, Capecitabine | DPYD | Critical - toxicity risk |

## Special Considerations

- **Warfarin**: Requires both CYP2C9 and VKORC1 for dosing guidance
- **Opioids**: CYP2D6 status critical for prodrug efficacy and safety
- **Clopidogrel**: CYP2C19 PM status is a serious efficacy concern
- **Chemotherapy (DPYD)**: Any risk allele requires dose reduction or avoidance
- **TPMT**: Critical for thiopurine dosing; poor metabolizers at high risk for severe toxicity

## Integration with Other Skills

- **report-pharmacogenomics**: Generates provider-ready markdown section saved to .output/
- **medication-supplements**: Can reference pharmacogenomics findings for medication analysis
- **health-summary**: May include pharmacogenomics summary if genetics data is configured

## Notes

- All SNP interpretations come from SNPedia via genetics-snp-lookup (cached, 30-day TTL)
- genetics-snp-lookup handles SNP extraction, API calls, caching, and error handling
- This skill focuses on formatting and clinical context for pharmacogenomics findings
- For individual SNP lookups, use genetics-snp-lookup directly
