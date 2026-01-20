# SNP Master Index

## Overview

This index provides quick lookup for all clinically relevant SNPs supported by the genetics skills, organized by category with batch extraction patterns.

## 23andMe Raw Data Format

```
# rsid  chromosome  position  genotype
rs12345  1  12345678  AG
```

- Tab-separated values
- Lines starting with `#` are comments
- Genotype is unphased (AG same as GA)
- Approximately 631,000 SNPs in typical file

## Single SNP Lookup

```bash
grep "^{rsid}" "{genetics_23andme_path}"
```

## Pharmacogenomics SNPs

### CYP2D6 - Drug Metabolism
| rsID | Gene | Variant | Effect |
|------|------|---------|--------|
| rs3892097 | CYP2D6 | *4 | Non-functional |
| rs1065852 | CYP2D6 | 100C>T | Reduced function |
| rs5030655 | CYP2D6 | *6 | Non-functional |
| rs28371725 | CYP2D6 | *41 | Reduced function |

### CYP2C19 - Clopidogrel, PPIs, Antidepressants
| rsID | Gene | Variant | Effect |
|------|------|---------|--------|
| rs4244285 | CYP2C19 | *2 | Non-functional |
| rs4986893 | CYP2C19 | *3 | Non-functional |
| rs12248560 | CYP2C19 | *17 | Increased function |

### CYP2C9 - Warfarin, NSAIDs
| rsID | Gene | Variant | Effect |
|------|------|---------|--------|
| rs1799853 | CYP2C9 | *2 | Reduced function |
| rs1057910 | CYP2C9 | *3 | Reduced function |

### VKORC1 - Warfarin Target
| rsID | Gene | Variant | Effect |
|------|------|---------|--------|
| rs9923231 | VKORC1 | -1639G>A | Warfarin sensitivity |

### SLCO1B1 - Statin Transport
| rsID | Gene | Variant | Effect |
|------|------|---------|--------|
| rs4149056 | SLCO1B1 | *5 | Reduced transport |

### TPMT - Thiopurines
| rsID | Gene | Variant | Effect |
|------|------|---------|--------|
| rs1800460 | TPMT | *3B | Reduced activity |
| rs1142345 | TPMT | *3C | Reduced activity |

### DPYD - Fluoropyrimidines
| rsID | Gene | Variant | Effect |
|------|------|---------|--------|
| rs3918290 | DPYD | *2A | Non-functional |
| rs55886062 | DPYD | *13 | Non-functional |
| rs67376798 | DPYD | D949V | Reduced function |
| rs75017182 | DPYD | HapB3 | Reduced function |

### Batch Extraction - All Pharmacogenomics
```bash
grep -E "^(rs3892097|rs1065852|rs5030655|rs28371725|rs4244285|rs4986893|rs12248560|rs1799853|rs1057910|rs9923231|rs4149056|rs1800460|rs1142345|rs3918290|rs55886062|rs67376798|rs75017182)" "{genetics_23andme_path}"
```

## Health Risk SNPs

### APOE - Alzheimer's, Cardiovascular
| rsID | Gene | Notes |
|------|------|-------|
| rs429358 | APOE | ε4 determining SNP |
| rs7412 | APOE | ε2 determining SNP |

### Clotting Disorders
| rsID | Gene | Condition |
|------|------|-----------|
| rs6025 | F5 | Factor V Leiden |
| rs1799963 | F2 | Prothrombin G20210A |

### Iron Metabolism
| rsID | Gene | Mutation |
|------|------|----------|
| rs1800562 | HFE | C282Y |
| rs1799945 | HFE | H63D |

### MTHFR - Methylation
| rsID | Gene | Variant |
|------|------|---------|
| rs1801133 | MTHFR | C677T |
| rs1801131 | MTHFR | A1298C |

### Cancer Predisposition (Founder Mutations)
| rsID | Gene | Mutation |
|------|------|----------|
| rs80357906 | BRCA1 | 185delAG |
| rs80357914 | BRCA1 | 5382insC |
| rs80359550 | BRCA2 | 6174delT |
| rs1801155 | APC | I1307K |

### Batch Extraction - All Health Risk
```bash
grep -E "^(rs429358|rs7412|rs6025|rs1799963|rs1800562|rs1799945|rs1801133|rs1801131|rs80357906|rs80357914|rs80359550|rs1801155)" "{genetics_23andme_path}"
```

## Combined Batch - All Clinically Relevant SNPs

```bash
grep -E "^(rs3892097|rs1065852|rs5030655|rs28371725|rs4244285|rs4986893|rs12248560|rs1799853|rs1057910|rs9923231|rs4149056|rs1800460|rs1142345|rs3918290|rs55886062|rs67376798|rs75017182|rs429358|rs7412|rs6025|rs1799963|rs1800562|rs1799945|rs1801133|rs1801131|rs80357906|rs80357914|rs80359550|rs1801155)" "{genetics_23andme_path}"
```

## Common Ancestry/Trait SNPs

For general SNP lookups beyond pharmacogenomics and health risks:

### Eye Color
| rsID | Gene | Trait |
|------|------|-------|
| rs12913832 | HERC2 | Blue/brown eye color |
| rs1800407 | OCA2 | Eye color modifier |

### Lactose Tolerance
| rsID | Gene | Trait |
|------|------|-------|
| rs4988235 | MCM6 | Lactase persistence (European) |

### Caffeine Metabolism
| rsID | Gene | Effect |
|------|------|--------|
| rs762551 | CYP1A2 | Fast/slow caffeine metabolism |

### Alcohol Flush
| rsID | Gene | Effect |
|------|------|--------|
| rs671 | ALDH2 | Alcohol flush reaction |

## SNP Naming Notes

- **rs numbers** (Reference SNP): Standard dbSNP identifiers
- Some variants have multiple rs numbers for the same position
- 23andMe raw data uses forward strand orientation
- Genotype orientation may differ from literature (check reference allele)

## Lookup Tips

1. **Case sensitivity**: Use exact rsID match (lowercase 'rs')
2. **Multiple SNPs**: Use `grep -E` with pipe-separated patterns
3. **Missing SNPs**: Not all SNPs are tested by 23andMe
4. **Performance**: Grep is fast even on 600K+ line files

## Cross-Reference with Other Data

When correlating genetics with health data:
- **Labs**: Check relevant biomarkers (e.g., iron studies for HFE variants)
- **Medications**: Match current meds against pharmacogenomics findings
- **Timeline**: Note when genetic testing was performed
