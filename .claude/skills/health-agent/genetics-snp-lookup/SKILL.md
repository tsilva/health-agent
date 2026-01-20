---
name: genetics-snp-lookup
description: Look up specific SNP genotypes from 23andMe raw data. Use when user asks "look up rs12345", "my genotype for rs...", "check SNP", "what's my genotype", or wants to find a specific genetic variant.
---

# SNP Lookup

Query individual SNPs or batches of SNPs from 23andMe raw data.

## Prerequisites

- Profile must have `genetics_23andme_path` configured
- 23andMe raw data file must exist at the specified path

## Workflow

1. Get `genetics_23andme_path` from the loaded profile
2. Verify the file exists
3. Extract requested SNP(s) using grep
4. Parse and format results
5. Provide interpretation if SNP is in reference files

## Efficient Data Access

23andMe raw data files contain ~631,000 SNPs. **Always use grep extraction** - never read the full file.

### Single SNP Lookup
```bash
grep "^{rsid}" "{genetics_23andme_path}"
```

### Multiple SNPs (Batch)
```bash
grep -E "^(rs123|rs456|rs789)" "{genetics_23andme_path}"
```

### Check File Exists
```bash
test -f "{genetics_23andme_path}" && echo "Found" || echo "Not found"
```

### Count Total SNPs (for context)
```bash
wc -l "{genetics_23andme_path}" | awk '{print $1}'
```

## 23andMe Raw Data Format

```
# rsid  chromosome  position  genotype
rs12345  1  12345678  AG
```

- Tab-separated: rsid, chromosome, position, genotype
- Lines starting with `#` are comments/headers
- Genotype is unphased (AG same as GA)

## Output Format

### Single SNP

```
## SNP Lookup: {rsid}

**Genotype**: {genotype}
**Chromosome**: {chromosome}
**Position**: {position}

{interpretation if known - see reference files}
```

### Multiple SNPs

```
## SNP Lookup Results

| rsID | Chromosome | Position | Genotype |
|------|------------|----------|----------|
| rs123 | 1 | 12345 | AG |
| rs456 | 2 | 67890 | CC |

### Interpretations

**rs123**: {interpretation if known}
**rs456**: {interpretation if known}
```

### Not Found

```
## SNP Lookup: {rsid}

**Result**: Not found in 23andMe data

This SNP may not be tested by 23andMe's genotyping array.
```

## Interpretation Sources

Check these reference files for known SNPs:

1. `references/genetics-pharmacogenomics.md` - Drug metabolism variants
2. `references/genetics-health-risks.md` - Health risk variants
3. `references/genetics-snp-index.md` - Master SNP index

If the SNP is in a reference file, include the relevant interpretation from that file.

## Common Requests

### Look up a specific variant
User: "What's my rs1801133 genotype?"
→ Single SNP lookup with MTHFR interpretation

### Check multiple related SNPs
User: "Look up my APOE SNPs"
→ Batch lookup of rs429358 and rs7412

### Verify a reported genotype
User: "Can you confirm I have the Factor V Leiden variant?"
→ Look up rs6025 and interpret

## Error Handling

- **File not found**: Prompt user to verify `genetics_23andme_path` in their profile
- **SNP not found**: Note that 23andMe doesn't test all SNPs; suggest alternative lookup methods
- **Invalid rsid format**: rsIDs should match pattern `rs[0-9]+`

## Batch Patterns for Common Panels

See `references/genetics-snp-index.md` for pre-built grep patterns for:
- All pharmacogenomics SNPs
- All health risk SNPs
- Combined clinically relevant SNPs

## Notes

- Genotypes are reported on the forward strand
- Literature may report on reverse strand - be aware of complementary bases (A↔T, C↔G)
- 23andMe does not detect insertions, deletions, or copy number variations
- Some SNPs have multiple rsIDs - check aliases if primary lookup fails
