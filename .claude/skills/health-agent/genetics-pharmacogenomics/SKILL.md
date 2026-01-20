---
name: genetics-pharmacogenomics
description: Analyze drug metabolism genetic variants and their clinical implications. Use when user asks "drug metabolism", "CYP2D6 status", "pharmacogenomics", "medication genetics", "how do I metabolize drugs", "warfarin genetics", or wants to understand how genetics affects their medications.
---

# Pharmacogenomics Analysis

Comprehensive analysis of genetic variants affecting drug metabolism, efficacy, and safety.

## Prerequisites

- Profile must have `genetics_23andme_path` configured
- Reference: `references/genetics-pharmacogenomics.md`
- Index: `references/genetics-snp-index.md`

## Workflow

1. Get `genetics_23andme_path` from the loaded profile
2. Optionally get current medications from health_log if available
3. Extract all pharmacogenomics SNPs using batch grep
4. Parse genotypes for each gene/enzyme
5. Determine metabolizer status for each pathway
6. Cross-reference with current medications if available
7. Generate comprehensive report

## Efficient Data Access

### Extract All Pharmacogenomics SNPs
```bash
grep -E "^(rs3892097|rs1065852|rs5030655|rs28371725|rs4244285|rs4986893|rs12248560|rs1799853|rs1057910|rs9923231|rs4149056|rs1800460|rs1142345|rs3918290|rs55886062|rs67376798|rs75017182)" "{genetics_23andme_path}"
```

### Get Current Medications (Optional)
```bash
head -1 "{health_log_path}/health_log.csv" && grep -iE ",(medication)," "{health_log_path}/health_log.csv" | sort -t',' -k1 -r
```

## Genes Analyzed

| Gene | Function | Key SNPs |
|------|----------|----------|
| CYP2D6 | Opioids, antidepressants, antipsychotics | rs3892097, rs1065852, rs5030655, rs28371725 |
| CYP2C19 | Clopidogrel, PPIs, antidepressants | rs4244285, rs4986893, rs12248560 |
| CYP2C9 | Warfarin, NSAIDs | rs1799853, rs1057910 |
| VKORC1 | Warfarin sensitivity | rs9923231 |
| SLCO1B1 | Statin transport | rs4149056 |
| TPMT | Thiopurines | rs1800460, rs1142345 |
| DPYD | Fluoropyrimidines | rs3918290, rs55886062, rs67376798, rs75017182 |

## Metabolizer Status Determination

See `references/genetics-pharmacogenomics.md` for detailed genotype-to-phenotype mappings.

### Key Patterns

**CYP2D6**:
- Any variant allele (*4, *6, *41) reduces function
- Two non-functional → Poor Metabolizer
- One non-functional + one reduced → Intermediate Metabolizer

**CYP2C19**:
- *2, *3 → non-functional
- *17 → increased function
- *17/*17 → Ultra-rapid Metabolizer

**VKORC1**:
- A/A → High warfarin sensitivity
- G/G → Normal sensitivity

## Output Format

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

{Continue for each gene with variants...}

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
```

## Cross-Reference with Current Medications

If `health_log_path` is available:

1. Extract current medications from health_log.csv
2. For each active medication, check if it's metabolized by tested enzymes
3. Highlight any potential interactions or dosing considerations

### Medication-Gene Mappings

| Medication Class | Relevant Gene | Notes |
|-----------------|---------------|-------|
| Codeine, Tramadol | CYP2D6 | Prodrugs - avoid in PM |
| Clopidogrel | CYP2C19 | Reduced efficacy in PM |
| Warfarin | CYP2C9 + VKORC1 | Combined dosing algorithm |
| Simvastatin | SLCO1B1 | Myopathy risk |
| Omeprazole | CYP2C19 | Efficacy varies |
| Metoprolol | CYP2D6 | Dose adjustment may be needed |

## Special Considerations

- **Warfarin**: Requires both CYP2C9 and VKORC1 for dosing guidance
- **Opioids**: CYP2D6 status critical for prodrug efficacy and safety
- **Clopidogrel**: CYP2C19 PM status is a serious efficacy concern
- **Chemotherapy (DPYD)**: Any risk allele requires dose reduction or avoidance
