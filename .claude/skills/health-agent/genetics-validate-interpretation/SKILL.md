---
name: genetics-validate-interpretation
description: Validate genetic variant interpretations against SNPedia and clinical databases. Use when interpreting unknown SNPs, verifying allele orientation, or cross-checking risk assessments.
---

# Genetics Interpretation Validation

Validate genetic variant interpretations by cross-referencing with SNPedia and clinical databases.

## When to Use

- Interpreting SNPs NOT in reference files
- Verifying allele orientation (which genotype is risk allele)
- Cross-checking genetic risk assessments
- Investigating novel or rare variants
- Confirming Gilbert syndrome, pharmacogenomics, or health risk interpretations

## Workflow

1. Receive SNP rsID and observed genotype
2. Fetch SNPedia page for that SNP
3. Extract genotype interpretations and clinical significance
4. Compare observed genotype to reported risk/protective genotypes
5. Return validated interpretation with confidence level

## SNPedia Lookup

SNPedia URL format: `https://www.snpedia.com/index.php/{rsid}`

Example: `https://www.snpedia.com/index.php/rs887829`

### Information to Extract

- **Genotype interpretations**: (C;C), (C;T), (T;T) meanings
- **Risk allele**: Which allele increases risk
- **Clinical significance**: Magnitude and penetrance
- **Population frequency**: How common is each genotype
- **Related conditions**: Associated diseases/traits

## Output Format

```markdown
## SNP Validation: {rsid}

**Observed Genotype**: {genotype} (from 23andMe)

**SNPedia Interpretation**:
- **{genotype}**: {interpretation from SNPedia}
- **Risk Allele**: {allele}
- **Clinical Significance**: {description}

**Validation Status**: ✅ CONFIRMED / ⚠️ UNCERTAIN / ❌ CONTRADICTS

**Confidence**: HIGH / MODERATE / LOW

**Recommendation**:
{Any follow-up actions or caveats}

---

**Sources**:
- SNPedia: https://www.snpedia.com/index.php/{rsid}
```

## Example Use Cases

### Validate Gilbert Syndrome Interpretation

Input: rs887829 = CC
Output:
```
✅ CONFIRMED: CC genotype is normal/wild-type
❌ INCORRECT prior interpretation as risk allele
Correct interpretation: TT = Gilbert syndrome risk
```

### Check Unknown Pharmacogenomics SNP

Input: rs12345 = AG (not in reference files)
Output:
```
⚠️ MODERATE CONFIDENCE: AG = intermediate metabolizer for CYP2C19
Recommend: Cross-check with clinical pharmacogenomics database
```

## Integration Points

### In investigate-root-cause skill

Add validation step after genetics analysis:

```markdown
7. **Validate Genetics** (if genetics used): Use `genetics-validate-interpretation`
   skill to cross-check any SNP interpretations not in reference files
```

### In genetics-snp-lookup skill

Add note to interpretation section:

```markdown
⚠️ **If SNP not in reference files**: Use `genetics-validate-interpretation`
skill to fetch interpretation from SNPedia before making assumptions about allele orientation.
```

## Error Handling

- **SNPedia page not found**: Report "No SNPedia entry - interpretation uncertain"
- **Ambiguous results**: Report "Multiple interpretations found - recommend clinical genetic testing"
- **Web fetch fails**: Fallback to reference files only, note validation unavailable

## Execution Instructions

1. **Receive input**: rsID and genotype from user or calling skill
2. **Use WebFetch tool** to fetch SNPedia page:
   ```
   WebFetch(url="https://www.snpedia.com/index.php/{rsid}", prompt="Extract genotype interpretations, risk alleles, clinical significance, and population frequencies for this SNP")
   ```
3. **Parse response**: Extract key information from SNPedia content
4. **Compare**: Match observed genotype against SNPedia interpretations
5. **Format output**: Use standard output format above
6. **Return**: Validation status with confidence level

## Key Validation Checks

### Allele Orientation
- Verify which allele is the risk allele (major vs minor)
- Confirm genotype notation matches 23andMe format
- Check for strand orientation issues (+ vs - strand)

### Clinical Significance
- Is this SNP clinically actionable?
- What is the magnitude of effect?
- What is the penetrance (how often does genotype cause phenotype)?

### Population Context
- How common is this genotype in the population?
- Are there ethnic-specific interpretations?

## Limitations

- SNPedia coverage varies by SNP
- Some SNPs have conflicting research findings
- 23andMe genotyping may miss important variants (e.g., UGT1A1*28)
- Tag SNPs may not be the functional variant
- Recommend clinical genetic testing for diagnostic confirmation
