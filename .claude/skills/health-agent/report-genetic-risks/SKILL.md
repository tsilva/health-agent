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
- Reference: `references/genetics-health-risks.md`

## Workflow

1. Load profile and extract `genetics_23andme_path`
2. Extract all health risk SNPs
3. Determine APOE isoform and other risk statuses
4. Format into standardized section
5. Save to `.output/{profile}/sections/genetic-risks-{date}.md`

## Efficient Data Access

### Extract Health Risk SNPs
```bash
grep -E "^(rs429358|rs7412|rs6025|rs1799963|rs1800562|rs1799945|rs1801133|rs1801131|rs80357906|rs80357914|rs80359550|rs1801155)" "{genetics_23andme_path}"
```

## Output Format

The section must follow this exact format for composability:

```markdown
---
section: genetic-risks
generated: {YYYY-MM-DD}
source: 23andMe raw data (consumer genetic test)
---

# Genetic Health Risks Summary

## Risk Summary

| Category | Finding | Clinical Significance |
|----------|---------|----------------------|
| APOE (Alzheimer's/CVD) | {isoform} | {significance} |
| Clotting Disorders | {status} | {significance} |
| Hemochromatosis (HFE) | {status} | {significance} |
| MTHFR | {status} | {significance} |
| BRCA1/2 (3 mutations only) | {status} | See limitations |

---

## Detailed Findings

### APOE Status

**Isoform**: {ε2/ε3/ε4 combination}

| SNP | Genotype |
|-----|----------|
| rs429358 | {genotype} |
| rs7412 | {genotype} |

**Interpretation**: {interpretation based on isoform}

**Clinical Relevance**:
- Cardiovascular: {LDL tendency, CVD risk}
- Neurological: {Alzheimer's risk context}

**Cross-Reference**: See Abnormal Labs section for lipid panel values.

---

### Clotting Disorders

**Factor V Leiden (rs6025)**: {genotype} - {interpretation}
**Prothrombin G20210A (rs1799963)**: {genotype} - {interpretation}

**Clinical Relevance**: {VTE risk assessment}

**Provider Considerations**:
- {relevant for surgery, pregnancy, estrogen therapy if positive}

---

### HFE - Hereditary Hemochromatosis

**C282Y (rs1800562)**: {genotype} - {interpretation}
**H63D (rs1799945)**: {genotype} - {interpretation}

**Compound Status**: {assessment}

**Clinical Relevance**: {iron overload risk}

**Cross-Reference**: See Abnormal Labs section for iron studies.

---

### MTHFR

**C677T (rs1801133)**: {genotype}
**A1298C (rs1801131)**: {genotype}

**Clinical Relevance**: {limited clinical significance for most patients}

---

### BRCA1/BRCA2 - Founder Mutations Only

**CRITICAL LIMITATION**: 23andMe tests only 3 specific founder mutations common in Ashkenazi Jewish populations. This represents <3% of known BRCA mutations. A negative result does NOT rule out BRCA mutations.

| Mutation | rsID | Result |
|----------|------|--------|
| BRCA1 185delAG | rs80357906 | {result} |
| BRCA1 5382insC | rs80357914 | {result} |
| BRCA2 6174delT | rs80359550 | {result} |

**Recommendation**: If family history suggests hereditary breast/ovarian cancer, comprehensive genetic testing is recommended regardless of these results.

---

## Recommended Actions

{Personalized based on findings:}

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

## APOE Isoform Determination

Calculate from rs429358 and rs7412:

| rs429358 | rs7412 | Isoform |
|----------|--------|---------|
| T/T | T/T | ε2/ε2 |
| T/T | C/T | ε2/ε3 |
| T/C | T/T | ε2/ε4 |
| T/T | C/C | ε3/ε3 |
| T/C | C/T | ε3/ε4 |
| C/C | C/C | ε4/ε4 |

## Lab Correlation

Reference the Abnormal Labs section for relevant biomarkers:
- **APOE**: Lipid panel (LDL, HDL, triglycerides)
- **HFE**: Iron, ferritin, TIBC, transferrin saturation
- **MTHFR**: Homocysteine, folate, B12

## Sensitivity Handling

- **APOE ε4**: Include but note it's a risk factor, not deterministic
- **BRCA**: Always emphasize severe testing limitations
- **Frame positively**: Focus on actionable prevention when possible

## Combining with Other Reports

This section is designed to combine with:
- `report-pharmacogenomics` - Drug metabolism variants
- `report-medication-list` - Current medications

Provider visit package:
1. All three = comprehensive genetics + medications review
