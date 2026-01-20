# Health Risk Variants Reference

## Overview

This reference covers genetic variants associated with health conditions that can be detected in 23andMe raw data. These variants have varying levels of clinical significance and penetrance.

## Cardiovascular & Metabolic

### APOE (rs429358, rs7412)

**Function**: Apolipoprotein E - affects lipid metabolism and Alzheimer's risk.

**Haplotype Determination**:
| rs429358 | rs7412 | APOE Isoform |
|----------|--------|--------------|
| T/T | T/T | ε2/ε2 |
| T/T | C/T | ε2/ε3 |
| T/C | T/T | ε2/ε4 |
| T/T | C/C | ε3/ε3 |
| T/C | C/T | ε3/ε4 |
| C/C | C/C | ε4/ε4 |

**Health Implications**:
| Genotype | Cardiovascular | Alzheimer's Risk | Interpretation |
|----------|---------------|------------------|----------------|
| ε2/ε2 | Lower LDL | Reduced risk | Protective; rare type III hyperlipoproteinemia risk |
| ε2/ε3 | Lower LDL | Slightly reduced | Generally favorable |
| ε3/ε3 | Baseline | Baseline | Most common (60-70% of population) |
| ε3/ε4 | Higher LDL | 2-3x increased | One risk allele |
| ε4/ε4 | Higher LDL | 8-15x increased | Two risk alleles; highest risk |
| ε2/ε4 | Variable | Intermediate | Mixed effects |

**Clinical Notes**:
- ε4 is a risk factor, not deterministic - many carriers never develop Alzheimer's
- ε4 carriers may benefit more from lifestyle interventions (exercise, diet, sleep)
- Cardiovascular risk management (statins, lifestyle) especially important for ε4 carriers

### Factor V Leiden (rs6025)

**Function**: Coagulation factor - affects blood clotting.

| Genotype | Risk |
|----------|------|
| G/G | Normal clotting |
| G/A | Heterozygous - 5-7x increased VTE risk |
| A/A | Homozygous - 25-80x increased VTE risk |

**Clinical Implications**:
- Increased risk of venous thromboembolism (DVT, PE)
- Higher risk during pregnancy, oral contraceptive use, surgery, immobilization
- May warrant prophylactic anticoagulation in high-risk situations
- Combined with other clotting disorders increases risk multiplicatively

### Prothrombin G20210A (rs1799963)

**Function**: Prothrombin gene variant - elevated prothrombin levels.

| Genotype | Risk |
|----------|------|
| G/G | Normal |
| G/A | 2-4x increased VTE risk |
| A/A | Higher VTE risk (rare) |

**Combined with Factor V Leiden**: Significantly elevated thrombosis risk.

## Iron Metabolism

### HFE - Hereditary Hemochromatosis (rs1800562, rs1799945)

**C282Y Mutation (rs1800562)**:
| Genotype | Interpretation |
|----------|----------------|
| G/G | Normal |
| G/A | Carrier - usually no iron overload |
| A/A | Homozygous - high risk of iron overload |

**H63D Mutation (rs1799945)**:
| Genotype | Interpretation |
|----------|----------------|
| C/C | Normal |
| C/G | Carrier - mild increased risk |
| G/G | Homozygous - moderate increased risk |

**Compound Heterozygote** (C282Y + H63D): Moderate risk of iron overload.

**Clinical Action**:
- Homozygous C282Y: Regular iron/ferritin monitoring recommended
- Consider phlebotomy if iron studies elevated
- Avoid iron supplements and vitamin C with meals (enhances absorption)

## Methylation & Homocysteine

### MTHFR (rs1801133, rs1801131)

**C677T (rs1801133)**:
| Genotype | Enzyme Activity |
|----------|----------------|
| C/C | Normal (100%) |
| C/T | Reduced (~65%) |
| T/T | Significantly reduced (~30%) |

**A1298C (rs1801131)**:
| Genotype | Enzyme Activity |
|----------|----------------|
| A/A | Normal |
| A/C | Mildly reduced |
| C/C | Moderately reduced |

**Clinical Significance**:
- Affects folate metabolism and homocysteine levels
- T/T genotype associated with elevated homocysteine
- Clinical significance is debated; most people compensate with adequate folate intake
- Supplementation with methylfolate may benefit some T/T individuals
- Not routinely actionable - ensure adequate folate/B12 intake

## Cancer Predisposition

### BRCA1/BRCA2 Founder Mutations

**Note**: 23andMe tests only 3 specific founder mutations common in Ashkenazi Jewish populations, not comprehensive BRCA screening.

**BRCA1 (rs80357906, rs80357914)**:
- 185delAG (rs80357906)
- 5382insC (rs80357914)

**BRCA2 (rs80359550)**:
- 6174delT (rs80359550)

| Result | Interpretation |
|--------|----------------|
| Negative for all 3 | NOT cleared - only 3 of thousands of possible mutations tested |
| Positive for any | Confirmed founder mutation carrier - high cancer risk |

**If Positive**:
- Significantly increased risk of breast and ovarian cancer
- Genetic counseling strongly recommended
- Enhanced screening and risk-reduction options available
- Family members should be offered testing

**If Negative**:
- Does NOT rule out BRCA mutations
- Comprehensive genetic testing recommended if family history suggests hereditary cancer
- 23andMe misses >97% of BRCA mutations

### APC I1307K (rs1801155)

**Function**: Associated with colorectal cancer risk in Ashkenazi Jewish populations.

| Genotype | Interpretation |
|----------|----------------|
| T/T | Normal |
| T/A | Carrier - ~2x increased colorectal cancer risk |
| A/A | Rare - increased risk |

**Clinical Action**: Enhanced colorectal cancer screening may be recommended.

## Batch Extraction Pattern

Extract all health risk SNPs at once from 23andMe raw data:

```bash
grep -E "^(rs429358|rs7412|rs6025|rs1799963|rs1800562|rs1799945|rs1801133|rs1801131|rs80357906|rs80357914|rs80359550|rs1801155)" "{genetics_23andme_path}"
```

## Interpretation Guidelines

### Risk Communication Framework

1. **Absolute vs Relative Risk**: Always contextualize relative risk with baseline population risk
2. **Penetrance**: Many variants have incomplete penetrance - not everyone with risk allele develops condition
3. **Polygenic Nature**: Most conditions involve many genes plus environment
4. **Actionability**: Focus on variants with clear clinical actions available

### Sensitivity Notes

- **Alzheimer's (APOE)**: Consider whether patient wants to know; no current preventive treatment
- **BRCA**: Incomplete testing - emphasize limitations; recommend genetic counseling
- **Carrier status**: Relevant for family planning discussions

## Important Caveats

- 23andMe is NOT a diagnostic test
- Positive results should be confirmed by clinical testing before medical decisions
- Negative results do NOT rule out conditions (limited SNPs tested)
- Genetic counseling recommended for significant findings
- Results should be interpreted in context of personal and family medical history
