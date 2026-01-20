---
name: genetics-health-risks
description: Analyze genetic variants associated with health conditions. Use when user asks "APOE status", "genetic risks", "BRCA results", "Alzheimer's genetics", "clotting disorder genetics", "Factor V Leiden", "MTHFR status", "hemochromatosis risk", or wants to understand health-related genetic variants.
---

# Genetic Health Risks Analysis

Analyze genetic variants associated with disease risk and health conditions.

## Prerequisites

- Profile must have `genetics_23andme_path` configured
- Uses `genetics-snp-lookup` skill for all SNP interpretations

## Workflow

1. Get `genetics_23andme_path` from the loaded profile
2. **Delegate to genetics-snp-lookup**: Request health risk analysis for all relevant conditions:
   - APOE (Alzheimer's disease, cardiovascular disease)
   - Factor V Leiden (thrombophilia)
   - Prothrombin G20210A (thrombophilia)
   - Hemochromatosis (HFE - iron overload)
   - MTHFR (folate metabolism)
   - BRCA founder mutations (limited - 3 Ashkenazi variants only)
   - APC I1307K (colorectal cancer risk)
3. Receive genotypes, risk interpretations, and clinical significance from genetics-snp-lookup
4. Format results into provider-friendly report (see Output Format below)
5. Cross-reference with relevant labs if available (lipids for APOE, iron for HFE, etc.)

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

genetics-snp-lookup is the centralized lookup mechanism for all genetics queries.

## Conditions Analyzed

genetics-snp-lookup provides interpretation for these conditions via SNPedia:

| Condition | Primary Genes/SNPs | Inheritance Pattern |
|-----------|-------------------|---------------------|
| APOE (Alzheimer's/CVD) | rs429358, rs7412 | Complex (ε2, ε3, ε4 isoforms) |
| Factor V Leiden | rs6025 | Autosomal dominant |
| Prothrombin G20210A | rs1799963 | Autosomal dominant |
| Hemochromatosis (HFE) | rs1800562 (C282Y), rs1799945 (H63D) | Autosomal recessive |
| MTHFR Variants | rs1801133 (C677T), rs1801131 (A1298C) | Autosomal recessive |
| BRCA1/2 Founder Mutations | rs80357906, rs80357914, rs80359550 | Autosomal dominant |
| APC I1307K | rs1801155 | Autosomal dominant |

## Output Format

Format the genetics-snp-lookup results into this provider-friendly structure:

```markdown
## Genetic Health Risk Report

**Generated**: {date}
**Profile**: {name}

---

### Summary

| Condition | Variant Status | Risk Level | Actionability |
|-----------|---------------|------------|---------------|
| APOE | ε3/ε4 | Elevated | Lifestyle modifications |
| Factor V Leiden | Negative | Normal | None |
| Hemochromatosis | Carrier (H63D) | Low | Monitor iron |
| MTHFR | C677T Heterozygous | Minimal | Adequate folate |
| BRCA1/2 (Limited) | Not detected | See caveats | Genetic counseling if FHx |

---

### Detailed Findings

#### APOE - Cardiovascular & Neurological

**Genotype**: ε3/ε4
- rs429358: T/C
- rs7412: C/C

**Interpretation**:
- One copy of the ε4 allele
- ~2-3x increased Alzheimer's risk vs ε3/ε3
- Elevated LDL cholesterol tendency

**Clinical Considerations**:
- Cardiovascular risk management particularly important
- Lifestyle factors (exercise, sleep, diet) may have enhanced benefit
- APOE ε4 is a risk factor, not deterministic

**Relevant Lab Correlation**:
{If labs available: recent lipid panel results}

---

#### Clotting Disorders

**Factor V Leiden (rs6025)**: G/G - Normal
**Prothrombin G20210A (rs1799963)**: G/G - Normal

**Interpretation**: No increased clotting risk detected from these common variants.

---

#### HFE - Hereditary Hemochromatosis

**C282Y (rs1800562)**: G/G - Normal
**H63D (rs1799945)**: C/G - Heterozygous carrier

**Interpretation**:
- H63D carrier status
- Low risk of iron overload (typically requires two C282Y copies)
- Compound heterozygosity (C282Y + H63D) not present

**Recommendation**:
- Routine iron monitoring reasonable
- No dietary iron restriction needed

**Relevant Lab Correlation**:
{If labs available: recent ferritin, iron, TIBC results}

---

#### MTHFR - Methylation

**C677T (rs1801133)**: C/T - Heterozygous
**A1298C (rs1801131)**: A/A - Normal

**Interpretation**:
- One copy of C677T variant
- Mild reduction in enzyme activity (~65% of normal)
- Generally not clinically significant

**Recommendation**:
- Ensure adequate dietary folate and B12
- Methylfolate supplementation not typically necessary for heterozygotes
- Clinical significance is debated

---

#### BRCA1/2 - Cancer Predisposition (Founder Mutations Only)

**IMPORTANT CAVEAT**: 23andMe tests only 3 specific founder mutations common in Ashkenazi Jewish populations. This is NOT comprehensive BRCA screening.

**185delAG (rs80357906)**: Not detected
**5382insC (rs80357914)**: Not detected
**6174delT (rs80359550)**: Not detected

**Interpretation**:
- Three tested founder mutations not detected
- **This does NOT rule out BRCA mutations**
- >97% of known BRCA mutations are NOT tested

**Recommendation**:
- If family history suggests hereditary breast/ovarian cancer, seek comprehensive genetic testing
- Genetic counseling recommended for concerning family history regardless of these results

---

### Risk Communication Notes

- **Relative vs Absolute Risk**: A 2-3x relative risk increase may represent a small absolute risk change
- **Penetrance**: Many genetic variants have incomplete penetrance
- **Gene-Environment**: Lifestyle factors significantly modify genetic risks
- **Polygenic Conditions**: Most diseases involve many genes plus environment

---

### Recommended Actions

1. **APOE ε4 carriers**: Discuss cardiovascular risk management with provider
2. **Clotting variants (if present)**: Inform providers before surgery, pregnancy, or estrogen therapy
3. **HFE variants**: Periodic iron monitoring if symptomatic or compound heterozygote
4. **Concerning family history**: Seek comprehensive genetic testing regardless of 23andMe results

---

### Important Limitations

- 23andMe is a consumer genetic test, NOT a diagnostic test
- Results should be confirmed by clinical testing before medical decisions
- Negative results do NOT rule out conditions (limited SNPs tested)
- These results represent a snapshot; genetic counseling recommended for significant findings

**Data Source**: SNPedia via genetics-snp-lookup skill (cached interpretations)
```

## Cross-Reference with Labs

When relevant, check for related biomarkers:

| Genetic Finding | Related Lab Tests | Extraction Command |
|-----------------|-------------------|-------------------|
| APOE ε4 | Lipid panel (LDL, HDL, TG) | `grep -iE "(ldl|hdl|cholesterol|triglyceride)" "{labs_path}/all.csv"` |
| HFE variants | Ferritin, iron, TIBC, transferrin saturation | `grep -iE "(ferritin|iron|transferrin|tibc)" "{labs_path}/all.csv"` |
| MTHFR | Homocysteine, folate, B12 | `grep -iE "(homocysteine|folate|b12|cobalamin)" "{labs_path}/all.csv"` |

**Workflow**:
1. Identify genetic findings from genetics-snp-lookup
2. Extract relevant lab markers from `{labs_path}/all.csv`
3. Sort by date, show most recent values
4. Include in report under "Relevant Lab Correlation" sections

## Sensitivity Considerations

- **Alzheimer's (APOE ε4)**: Users may not want to know; results can cause anxiety without current preventive treatments
- **BRCA**: Incomplete testing requires careful communication about limitations
- **Encourage genetic counseling** for actionable findings

**Important**: Always present genetic risk findings with appropriate context:
- Emphasize modifiable risk factors
- Clarify relative vs absolute risk
- Note limitations of consumer genetic testing
- Recommend professional genetic counseling for high-risk findings

## Special Handling

- **BRCA Results**: Always emphasize the severe limitations of 23andMe BRCA testing
- **APOE ε4/ε4**: High-risk finding; encourage professional genetic counseling
- **Factor V Leiden homozygous**: Clinically significant; recommend hematology consultation
- **HFE C282Y homozygous**: Clinical hemochromatosis risk; recommend iron studies and medical evaluation

## Integration with Other Skills

- **report-genetic-risks**: Generates provider-ready markdown section saved to .output/
- **health-summary**: May include genetics summary if genetics data is configured
- **investigate-root-cause**: Can reference genetic findings when investigating conditions

## Notes

- All SNP interpretations come from SNPedia via genetics-snp-lookup (cached, 30-day TTL)
- genetics-snp-lookup handles SNP extraction, API calls, caching, and error handling
- This skill focuses on formatting and clinical context for health risk findings
- For individual SNP lookups, use genetics-snp-lookup directly
- APOE isoform determination (ε2/ε3/ε4) is handled by genetics-snp-lookup using SNPedia's algorithms
