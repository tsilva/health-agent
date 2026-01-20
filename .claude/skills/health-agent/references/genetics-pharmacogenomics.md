# Pharmacogenomics Reference

## Overview

Pharmacogenomics analyzes genetic variants that affect drug metabolism, efficacy, and adverse reactions. This reference covers clinically actionable variants recognized by CPIC (Clinical Pharmacogenetics Implementation Consortium).

## Key Drug Metabolism Genes

### CYP2D6 (rs3892097, rs1065852, rs5030655, rs28371725)

**Function**: Metabolizes ~25% of medications including opioids, antidepressants, antipsychotics, and beta-blockers.

| Genotype Pattern | Metabolizer Status | Clinical Implication |
|------------------|-------------------|---------------------|
| Two functional alleles | Normal Metabolizer (NM) | Standard dosing |
| One reduced + one functional | Intermediate Metabolizer (IM) | May need dose reduction |
| Two non-functional alleles | Poor Metabolizer (PM) | Significantly reduced metabolism; avoid prodrugs |
| Multiple functional copies | Ultra-rapid Metabolizer (UM) | Rapid metabolism; prodrugs may cause toxicity |

**Key SNPs**:
| rsID | Variant | Effect |
|------|---------|--------|
| rs3892097 | *4 allele | Non-functional |
| rs1065852 | G>A | Reduced function |
| rs5030655 | *6 allele | Non-functional (frameshift) |
| rs28371725 | *41 allele | Reduced function |

**Affected Drugs**:
- **Opioids**: Codeine, tramadol, hydrocodone (prodrugs - avoid in PM/UM)
- **Antidepressants**: Paroxetine, fluoxetine, venlafaxine, amitriptyline
- **Antipsychotics**: Haloperidol, risperidone, aripiprazole
- **Beta-blockers**: Metoprolol, carvedilol
- **Antiemetics**: Ondansetron

### CYP2C19 (rs4244285, rs4986893, rs12248560)

**Function**: Metabolizes proton pump inhibitors, clopidogrel, some antidepressants and antiepileptics.

| rsID | Variant | Allele | Effect |
|------|---------|--------|--------|
| rs4244285 | G>A | *2 | Non-functional |
| rs4986893 | G>A | *3 | Non-functional |
| rs12248560 | C>T | *17 | Increased function |

**Metabolizer Status**:
| Genotype | Status | Clinical Action |
|----------|--------|-----------------|
| *1/*1 | Normal | Standard dosing |
| *1/*2, *1/*3 | Intermediate | Consider alternatives for clopidogrel |
| *2/*2, *2/*3, *3/*3 | Poor | Avoid clopidogrel; alternative PPIs |
| *1/*17, *17/*17 | Rapid/Ultra-rapid | Reduced PPI efficacy; clopidogrel works well |

**Affected Drugs**:
- **Antiplatelet**: Clopidogrel (prodrug - critical for PM patients)
- **PPIs**: Omeprazole, esomeprazole, lansoprazole
- **Antidepressants**: Citalopram, escitalopram, sertraline
- **Antifungals**: Voriconazole
- **Antiepileptics**: Diazepam, phenytoin

### CYP2C9 (rs1799853, rs1057910)

**Function**: Metabolizes warfarin, NSAIDs, and some oral hypoglycemics.

| rsID | Variant | Allele | Effect |
|------|---------|--------|--------|
| rs1799853 | C>T | *2 | Reduced function (~30% decrease) |
| rs1057910 | A>C | *3 | Reduced function (~80% decrease) |

**Clinical Impact**:
| Genotype | Warfarin Dose Adjustment |
|----------|-------------------------|
| *1/*1 | Standard dosing |
| *1/*2 | Reduce ~20% |
| *1/*3 | Reduce ~30% |
| *2/*2 | Reduce ~40% |
| *2/*3 | Reduce ~50% |
| *3/*3 | Reduce ~70% |

**Affected Drugs**:
- **Anticoagulants**: Warfarin (requires dose adjustment)
- **NSAIDs**: Celecoxib, ibuprofen, flurbiprofen
- **Hypoglycemics**: Glipizide, glimepiride

### VKORC1 (rs9923231)

**Function**: Vitamin K epoxide reductase - target of warfarin.

| rsID | Genotype | Warfarin Sensitivity |
|------|----------|---------------------|
| rs9923231 | G/G | Normal sensitivity |
| rs9923231 | G/A | Increased sensitivity (reduce dose ~25%) |
| rs9923231 | A/A | High sensitivity (reduce dose ~50%) |

**Combined Warfarin Dosing**: Use CYP2C9 + VKORC1 together for optimal warfarin dosing algorithms.

### SLCO1B1 (rs4149056)

**Function**: Hepatic transporter for statins.

| rsID | Genotype | Effect |
|------|----------|--------|
| rs4149056 | T/T | Normal statin transport |
| rs4149056 | T/C | Moderate myopathy risk |
| rs4149056 | C/C | High myopathy risk (5-17x increased) |

**Clinical Action**:
- C/C genotype: Avoid simvastatin >20mg; consider pravastatin or rosuvastatin
- T/C genotype: Use lower statin doses; monitor for muscle symptoms

### TPMT (rs1800460, rs1142345)

**Function**: Metabolizes thiopurine drugs (azathioprine, 6-mercaptopurine).

| Genotype | TPMT Activity | Thiopurine Dosing |
|----------|---------------|-------------------|
| Wild-type | Normal | Standard dosing |
| Heterozygous | Intermediate | Reduce dose 30-50% |
| Homozygous variant | Deficient | Avoid or reduce 90%; severe myelosuppression risk |

### DPYD (rs3918290, rs55886062, rs67376798, rs75017182)

**Function**: Metabolizes fluoropyrimidines (5-FU, capecitabine).

| Variant | Risk Level |
|---------|-----------|
| rs3918290 (DPYD*2A) | Very high toxicity risk - avoid fluoropyrimidines |
| rs55886062 (*13) | Very high toxicity risk |
| rs67376798 | Moderate toxicity risk - reduce dose 25-50% |
| rs75017182 (HapB3) | Moderate toxicity risk |

**Clinical Action**: Pre-treatment DPYD testing recommended before fluoropyrimidine chemotherapy.

## Batch Extraction Pattern

Extract all pharmacogenomics SNPs at once from 23andMe raw data:

```bash
grep -E "^(rs3892097|rs1065852|rs5030655|rs28371725|rs4244285|rs4986893|rs12248560|rs1799853|rs1057910|rs9923231|rs4149056|rs1800460|rs1142345|rs3918290|rs55886062|rs67376798|rs75017182)" "{genetics_23andme_path}"
```

## Interpretation Guidelines

1. **Always combine genotype with clinical context** - genetic variants are one factor among many
2. **Check for medications currently taken** by the patient before highlighting interactions
3. **Heterozygous carriers** often have intermediate phenotypes
4. **Population differences exist** - allele frequencies vary by ancestry
5. **Consult CPIC guidelines** for formal dosing recommendations: https://cpicpgx.org/guidelines/

## Important Caveats

- 23andMe tests limited SNPs; comprehensive pharmacogenomic panels test more variants
- Star allele (*) assignments may require additional SNPs not tested by 23andMe
- Copy number variations (especially CYP2D6) are not detected by 23andMe
- Results should be confirmed by clinical-grade testing before medical decisions
