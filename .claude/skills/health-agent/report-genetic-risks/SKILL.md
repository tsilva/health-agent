---
name: report-genetic-risks
description: Generate genetic health risks report section for provider visits. Use when user asks "genetic risks summary for provider", "genetic risks report for doctor", "APOE report for appointment", or needs a saveable genetic risks document for healthcare providers.
---

# Report: Genetic Health Risks Summary

Generate a standardized genetic health risks section suitable for provider visits and medical records.

## Purpose

This report section provides:
- Summary of health-related genetic variants
- Risk interpretations with clinical context
- Relevant lab correlations where applicable
- Format optimized for sharing with healthcare providers
- Appropriate caveats for consumer genetic testing

## Prerequisites

- Profile must have `genetics_23andme_path` configured
- Uses `genetics-snp-lookup` skill for all SNP interpretations

## Workflow

1. Load profile and extract `genetics_23andme_path`
2. **Delegate to genetics-snp-lookup**: Call for all health risk conditions (APOE, Factor V Leiden, Hemochromatosis, MTHFR, BRCA, Prothrombin)
3. Receive genotypes, risk interpretations, and clinical significance from genetics-snp-lookup
4. Format into standardized provider-ready section
5. Save to `.output/{profile}/sections/genetic-risks-{date}.md`

## Calling genetics-snp-lookup

Use genetics-snp-lookup in **condition-based health risk mode**:

```
For each condition in [APOE, Factor V Leiden, Hemochromatosis, MTHFR, BRCA, Prothrombin]:
  Call genetics-snp-lookup with: "look up {condition} health risk"

genetics-snp-lookup will:
1. Query SNPedia for condition's relevant rsIDs
2. Extract those SNPs from 23andMe data
3. Fetch risk interpretations from SNPedia
4. Return risk level, clinical significance, recommendations
```

**Do NOT**:
- Duplicate SNP extraction logic
- Hardcode rsID lists
- Reimplement risk determination algorithms (e.g., APOE isoform table)
- Query SNPedia directly

genetics-snp-lookup is the centralized lookup mechanism - this skill focuses on formatting for providers.

## Output Format

The section must follow this exact format for composability:

```markdown
---
section: genetic-risks
generated: {YYYY-MM-DD}
source: 23andMe raw data (consumer genetic test)
profile: {profile_name}
---

# Genetic Health Risks Summary

## Risk Summary

| Category | Finding | Clinical Significance |
|----------|---------|----------------------|
| APOE (Alzheimer's/CVD) | {isoform from genetics-snp-lookup} | {significance} |
| Clotting Disorders | {status from genetics-snp-lookup} | {significance} |
| Hemochromatosis (HFE) | {status from genetics-snp-lookup} | {significance} |
| MTHFR | {status from genetics-snp-lookup} | {significance} |
| BRCA1/2 (3 mutations only) | {status from genetics-snp-lookup} | See limitations |

---

## Detailed Findings

### APOE Status

**Isoform**: {ε2/ε3/ε4 combination from genetics-snp-lookup}

| SNP | Genotype |
|-----|----------|
| rs429358 | {genotype} |
| rs7412 | {genotype} |

**Interpretation**: {interpretation from genetics-snp-lookup}

**Clinical Relevance**:
- Cardiovascular: {LDL tendency, CVD risk}
- Neurological: {Alzheimer's risk context}

**Cross-Reference**: See Abnormal Labs section for lipid panel values.

---

### Clotting Disorders

**Factor V Leiden (rs6025)**: {genotype} - {interpretation from genetics-snp-lookup}
**Prothrombin G20210A (rs1799963)**: {genotype} - {interpretation from genetics-snp-lookup}

**Clinical Relevance**: {VTE risk assessment}

**Provider Considerations**:
- {relevant for surgery, pregnancy, estrogen therapy if positive}

---

### HFE - Hereditary Hemochromatosis

**C282Y (rs1800562)**: {genotype} - {interpretation from genetics-snp-lookup}
**H63D (rs1799945)**: {genotype} - {interpretation from genetics-snp-lookup}

**Compound Status**: {assessment from genetics-snp-lookup}

**Clinical Relevance**: {iron overload risk}

**Cross-Reference**: See Abnormal Labs section for iron studies.

---

### MTHFR

**C677T (rs1801133)**: {genotype from genetics-snp-lookup}
**A1298C (rs1801131)**: {genotype from genetics-snp-lookup}

**Clinical Relevance**: {limited clinical significance for most patients}

---

### BRCA1/BRCA2 - Founder Mutations Only

**CRITICAL LIMITATION**: 23andMe tests only 3 specific founder mutations common in Ashkenazi Jewish populations. This represents <3% of known BRCA mutations. A negative result does NOT rule out BRCA mutations.

| Mutation | rsID | Result |
|----------|------|--------|
| BRCA1 185delAG | rs80357906 | {result from genetics-snp-lookup} |
| BRCA1 5382insC | rs80357914 | {result from genetics-snp-lookup} |
| BRCA2 6174delT | rs80359550 | {result from genetics-snp-lookup} |

**Recommendation**: If family history suggests hereditary breast/ovarian cancer, comprehensive genetic testing is recommended regardless of these results.

---

## Recommended Actions

{Personalized based on findings from genetics-snp-lookup:}

1. {Action item based on APOE if relevant}
2. {Action item based on clotting if relevant}
3. {Action item based on HFE if relevant}
4. {General: comprehensive testing if family history concerning}

---

## Genotype Reference Table

| Condition | SNP | Genotype | Risk Allele | Patient Status |
|-----------|-----|----------|-------------|----------------|
| APOE | rs429358 | {gt} | C (ε4) | {status} |
| APOE | rs7412 | {gt} | T (ε2) | {status} |
| Factor V Leiden | rs6025 | {gt} | A | {status} |
| Prothrombin | rs1799963 | {gt} | A | {status} |
| HFE C282Y | rs1800562 | {gt} | A | {status} |
| HFE H63D | rs1799945 | {gt} | G | {status} |
| MTHFR C677T | rs1801133 | {gt} | T | {status} |
| MTHFR A1298C | rs1801131 | {gt} | C | {status} |

---

## Provider Notes

1. **BRCA testing is severely limited**: Only 3 of thousands of mutations tested
2. **Confirmation testing**: Recommend clinical testing for actionable findings
3. **Consumer test**: Not a diagnostic test; results should guide clinical evaluation
4. **Data source**: Interpretations from SNPedia (genetics-snp-lookup skill with 30-day cache)

---

## Genetic Counseling

Genetic counseling is recommended if:
- APOE ε4/ε4 detected
- Any clotting disorder variant detected
- Homozygous HFE C282Y detected
- Any BRCA founder mutation detected
- Family history suggests hereditary conditions despite negative results

---
*Section generated by health-agent report-genetic-risks skill*
```

## Output File

- **Directory**: `.output/{profile}/sections/`
- **Filename**: `genetic-risks-YYYY-MM-DD.md`
- **Create directory if needed**: `mkdir -p .output/{profile}/sections`

**IMPORTANT**: Use the `Write` tool to create the report file, NOT Bash heredocs/redirects. Bash file writing (`cat > file` or heredocs) is blocked by sandbox restrictions. Directory creation via `mkdir -p` is permitted.

## Lab Correlation

Reference the Abnormal Labs section for relevant biomarkers:
- **APOE**: Lipid panel (LDL, HDL, triglycerides)
- **HFE**: Iron, ferritin, TIBC, transferrin saturation
- **MTHFR**: Homocysteine, folate, B12

**Cross-referencing workflow**:
1. Identify genetic findings from genetics-snp-lookup
2. Note which lab tests would be relevant
3. Refer reader to "Abnormal Labs" section for actual values
4. Provider can correlate genetic risk with lab trends

## Sensitivity Handling

- **APOE ε4**: Include but note it's a risk factor, not deterministic
- **BRCA**: Always emphasize severe testing limitations
- **Frame positively**: Focus on actionable prevention when possible

**Important**: Always present genetic risk findings with appropriate context:
- Emphasize modifiable risk factors
- Clarify relative vs absolute risk
- Note limitations of consumer genetic testing
- Recommend professional genetic counseling for high-risk findings

## Combining with Other Reports

This section is designed to combine with:
- `report-pharmacogenomics` - Drug metabolism variants
- `report-medication-list` - Current medications
- `report-labs-abnormal` - Relevant biomarkers

Provider visit package:
1. All three genetics sections = comprehensive genetics review
2. Genetics + medications + labs = complete provider visit summary

## Integration with Other Skills

- **genetics-health-risks**: Non-report version for interactive analysis
- **report-pharmacogenomics**: Companion genetics report section
- **report-labs-abnormal**: Provides lab values for correlation

## Notes

- All SNP interpretations come from SNPedia via genetics-snp-lookup (cached, 30-day TTL)
- genetics-snp-lookup handles SNP extraction, API calls, caching, and error handling
- This skill focuses on formatting for provider consumption and saving to .output/
- For interactive health risk analysis, use the genetics-health-risks skill
- APOE isoform determination (ε2/ε3/ε4) is handled by genetics-snp-lookup using SNPedia's algorithms
