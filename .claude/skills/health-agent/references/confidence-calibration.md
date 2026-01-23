# Confidence Calibration for Ensemble Investigations

This document provides formulas and examples for calculating calibrated confidence scores in ensemble root cause investigations.

## Overview

Raw confidence scores often overestimate certainty. Calibrated confidence adjusts for:

1. **Diagnostic gaps** - Missing tests that could confirm/refute hypotheses
2. **Epidemiological priors** - Base rates of conditions in population
3. **Evidence quality** - Not all evidence types are equal
4. **Adversarial survival** - Whether hypothesis survived Red Team scrutiny

---

## 1. Diagnostic Gap Penalty

### Rationale

High confidence is inappropriate when key diagnostic tests are unavailable. A 78% confidence with untested possibilities should be lower than 78% confidence with all tests performed.

### Formula

```
Gap-Adjusted Confidence = Raw Confidence × (1 - Gap Penalty)

Gap Penalty = min(Σ Individual Penalties, 0.30)  # Capped at 30%
```

### Individual Penalty Calculation

For each missing diagnostic test:

```
Individual Penalty = P(test would change diagnosis) × 0.10
```

| Missing Test Type | Typical Penalty |
|-------------------|-----------------|
| Gold standard diagnostic test | 10-15% |
| Confirmatory genetic test | 8-12% |
| Definitive lab test | 5-10% |
| Imaging that would confirm | 3-8% |
| Supportive but not definitive test | 2-5% |

### Worked Example: Hemolysis Investigation

**Scenario**: Investigation concludes hereditary spherocytosis with 78% raw confidence.

**Missing Tests**:
| Test | Why Important | P(would change dx) | Penalty |
|------|---------------|-------------------|---------|
| EMA binding test | Gold standard for HS | 30% | 3% |
| Osmotic fragility | Confirmatory for HS | 20% | 2% |
| Bone marrow biopsy | Would rule out CDA | 15% | 1.5% |
| Direct Coombs test | Rule out autoimmune | 40% | 4% |

**Calculation**:
```
Total Gap Penalty = 3% + 2% + 1.5% + 4% = 10.5%
Gap-Adjusted Confidence = 78% × (1 - 0.105) = 78% × 0.895 = 69.8%
```

**Interpretation**: Confidence drops from 78% to ~70% because several tests that could confirm or refute the diagnosis haven't been performed.

---

## 2. Epidemiological Priors

### Rationale

Rare conditions should require stronger evidence than common ones. Without priors, a rare genetic disorder might be ranked equally with a common acquired condition when both have similar evidence support.

### Bayesian Adjustment Formula

```
Posterior = (Likelihood × Prior) / Σ(Likelihood_i × Prior_i)

Where:
- Likelihood = Evidence support for hypothesis (0-1)
- Prior = Population prevalence adjusted for demographics
```

### Obtaining Priors

1. **Literature search**: Query "epidemiology [condition]" or "prevalence [condition]"
2. **Demographics adjustment**: Adjust for patient's age, gender, ancestry
3. **Use log scale for very rare conditions** to prevent prior dominance

### Prior Prevalence Categories

| Category | Prevalence | Example Conditions |
|----------|-----------|-------------------|
| Very common | >1:100 | Iron deficiency anemia, vitamin D deficiency |
| Common | 1:100 - 1:1000 | Hypothyroidism, Gilbert syndrome |
| Uncommon | 1:1000 - 1:10000 | Hereditary spherocytosis, hemochromatosis |
| Rare | 1:10000 - 1:100000 | G6PD deficiency (varies by ancestry) |
| Very rare | <1:100000 | Congenital dyserythropoietic anemia |

### Worked Example: Hemolysis Differential

**Scenario**: Two hypotheses with similar evidence support

| Hypothesis | Evidence Likelihood | Raw Prior | Demo-Adjusted Prior |
|------------|--------------------|-----------|--------------------|
| Hereditary spherocytosis | 0.75 | 1:2000 | 1:2000 (no adjustment) |
| Congenital dyserythropoietic anemia | 0.70 | 1:100000 | 1:100000 |

**Calculation**:
```
HS Posterior = (0.75 × 0.0005) / [(0.75 × 0.0005) + (0.70 × 0.00001)]
            = 0.000375 / (0.000375 + 0.000007)
            = 0.000375 / 0.000382
            = 98.2%

CDA Posterior = (0.70 × 0.00001) / 0.000382
             = 1.8%
```

**Interpretation**: Despite similar evidence likelihood, HS gets much higher posterior because it's 50× more common. CDA would need much stronger evidence to overcome its rarity.

### When NOT to Use Priors

- When evidence is overwhelming (likelihood >0.95)
- When patient has known risk factors that change their prior
- When dealing with rare disease specialist referral (selection bias)

---

## 3. Evidence Quality Weights

### Weight by Evidence Type

| Evidence Type | Weight | Rationale |
|---------------|--------|-----------|
| Genetic confirmation (pathogenic variant) | 1.0 | Definitive when present |
| Gold standard diagnostic test | 0.95 | Near-definitive |
| Multiple consistent lab markers | 0.80 | Strong pattern |
| Single diagnostic lab value | 0.70 | Suggestive |
| Multiple timeline correlations | 0.60 | Pattern support |
| Single timeline correlation | 0.50 | Weak support |
| Exam finding consistent with diagnosis | 0.65 | Supportive |
| Symptom report only | 0.40 | Subjective |
| Inference/mechanism speculation | 0.30 | Weakest |

### Calculating Combined Evidence Quality

```
Combined Evidence Quality = Weighted Average of Evidence Types

Quality = Σ(Evidence_i × Weight_i) / Σ(Weight_i)
```

### Worked Example

**Evidence for Hereditary Spherocytosis**:
| Evidence | Type | Weight | Contribution |
|----------|------|--------|--------------|
| ANK1/SPTB variant found | Genetic | 1.0 | 1.0 |
| Elevated reticulocytes | Lab pattern | 0.8 | 0.8 |
| Elevated bilirubin | Lab pattern | 0.8 | 0.8 |
| Family history | Timeline | 0.5 | 0.5 |

**Calculation**:
```
Quality = (1.0 + 0.8 + 0.8 + 0.5) / 4 = 3.1 / 4 = 0.775
```

---

## 3b. Genetic Evidence Weighting (Extended)

Genetic evidence requires special consideration because a variant's presence alone doesn't guarantee disease expression. This section provides detailed guidance for weighting genetic findings.

### The Spectrum of Genetic Evidence

Not all genetic findings are equally probative. Weight them on this spectrum:

| Evidence Level | Weight | Description | Example |
|----------------|--------|-------------|---------|
| **Pathogenic variant + biochemical confirmation** | 1.0 | Gold standard | APOE ε4/ε4 + elevated CSF tau |
| **Known pathogenic variant (high penetrance)** | 0.90 | Very strong | BRCA1 185delAG |
| **Known pathogenic variant (moderate penetrance)** | 0.80 | Strong | Factor V Leiden heterozygous |
| **Likely pathogenic variant (functional data)** | 0.75 | Strong | Variant with in vitro functional studies |
| **Known pathogenic variant (low penetrance)** | 0.65 | Moderate | MTHFR C677T homozygous |
| **Variant of uncertain significance (VUS)** | 0.40 | Weak | Novel variant in known gene |
| **Benign or likely benign variant** | 0.10 | Very weak | Should not support hypothesis |
| **Variant NOT found** | Variable | Depends on coverage | See "Negative Genetic Evidence" below |

### Worked Example: Variant Found vs Variant + Biochemical Confirmation

**Scenario**: Investigating hereditary hemochromatosis in patient with elevated ferritin.

#### Case A: Variant Found Only

Patient has HFE C282Y homozygous genotype (rs1800562 GG).

| Evidence | Weight | Rationale |
|----------|--------|-----------|
| C282Y homozygous | 0.85 | Known pathogenic, but penetrance is 28% for clinical disease |

**Quality Score**: 0.85

**Interpretation**: Genotype is necessary but not sufficient. Many C282Y homozygotes never develop iron overload.

#### Case B: Variant + Biochemical Confirmation

Same patient, but we also have:
- Transferrin saturation: 62% (elevated, >45% threshold)
- Ferritin: 850 ng/mL (elevated)
- Liver iron concentration elevated on MRI

| Evidence | Weight | Rationale |
|----------|--------|-----------|
| C282Y homozygous | 0.85 | Known pathogenic |
| Elevated transferrin sat | 0.90 | Biochemical confirmation |
| Elevated ferritin | 0.80 | Supporting lab |
| Elevated liver iron | 0.95 | Imaging confirmation |

**Combined Quality Score**:
```
Quality = (0.85 + 0.90 + 0.80 + 0.95) / 4 = 3.50 / 4 = 0.875
```

**Interpretation**: With biochemical confirmation, confidence rises significantly. This is clinical hemochromatosis, not just genetic susceptibility.

### Penetrance-Adjusted Genetic Weights

When calculating weights, adjust for known penetrance:

```
Adjusted Weight = Base Weight × Penetrance Factor

Penetrance Factor:
- Complete penetrance (>90%): 1.0
- High penetrance (70-90%): 0.95
- Moderate penetrance (30-70%): 0.85
- Low penetrance (10-30%): 0.70
- Very low penetrance (<10%): 0.50
```

**Examples**:

| Condition | Variant | Base Weight | Penetrance | Adjusted Weight |
|-----------|---------|-------------|------------|-----------------|
| Huntington disease | HTT CAG repeat >40 | 0.95 | ~100% | 0.95 × 1.0 = 0.95 |
| Hereditary spherocytosis | ANK1 pathogenic | 0.90 | ~90% | 0.90 × 0.95 = 0.86 |
| Hemochromatosis | HFE C282Y/C282Y | 0.85 | ~28% | 0.85 × 0.70 = 0.60 |
| MTHFR | C677T homozygous | 0.65 | ~10-15% | 0.65 × 0.50 = 0.33 |
| APOE | ε4 homozygous | 0.85 | ~50-60% | 0.85 × 0.85 = 0.72 |

### Negative Genetic Evidence

When a variant is NOT found, interpretation depends on coverage:

| Scenario | Evidence Value | Weight Adjustment |
|----------|----------------|-------------------|
| **SNP tested, variant absent** | Rules out that variant | Reduces hypothesis confidence |
| **SNP not on genotyping array** | No information | No adjustment either way |
| **Gene fully sequenced, no pathogenic variants** | Strong negative evidence | Significantly reduces hypothesis |

**Example**: Investigating hereditary spherocytosis

- ANK1 SNP not on 23andMe array → No adjustment (can't rule out)
- ANK1 SNP on array, variant absent → Reduces HS hypothesis by ~0.15 points
- Full ANK1 gene sequencing negative → Reduces HS hypothesis by ~0.30 points

### Combining Genetic with Non-Genetic Evidence

When multiple evidence types support the same hypothesis:

```
Final Quality = Weighted Average × Convergence Bonus

Convergence Bonus:
- Genetic + Biochemical + Clinical: ×1.15
- Genetic + Biochemical only: ×1.10
- Genetic only: ×1.00
- Biochemical + Clinical only: ×1.05
- Clinical only: ×1.00
```

**Worked Example: Full Hemochromatosis Workup**

| Evidence | Type | Base Weight | Convergence |
|----------|------|-------------|-------------|
| HFE C282Y homozygous | Genetic | 0.85 | |
| Transferrin sat 62% | Biochemical | 0.90 | |
| Ferritin 850 | Biochemical | 0.80 | |
| Liver iron elevated | Clinical/Imaging | 0.95 | |
| Joint pain | Clinical symptom | 0.50 | |

**Calculation**:
```
Base Quality = (0.85 + 0.90 + 0.80 + 0.95 + 0.50) / 5 = 0.80
Convergence: Genetic + Biochemical + Clinical = ×1.15
Final Quality = 0.80 × 1.15 = 0.92
```

### Pharmacogenomics Evidence

Pharmacogenomics findings have different weight implications:

| Finding | Weight | Clinical Impact |
|---------|--------|-----------------|
| Poor metabolizer confirmed (genotype + phenotype) | 0.95 | Dose adjustment required |
| Poor metabolizer genotype only | 0.80 | Dose adjustment recommended |
| Intermediate metabolizer | 0.70 | Monitor for response |
| Normal metabolizer | 0.50 | Standard dosing |
| Ultrarapid metabolizer | 0.80 | Dose increase may be needed |

**Example**: CYP2D6 for codeine response

| Scenario | Evidence | Weight | Recommendation |
|----------|----------|--------|----------------|
| *4/*4 genotype + no analgesia with codeine | Genetic + Clinical | 0.95 | Use alternative analgesic |
| *4/*4 genotype alone | Genetic only | 0.80 | Expect reduced response |
| *4/*1 genotype | Genetic | 0.70 | May have reduced response |

---

## 4. Adversarial Survival Factor

### Red Team Survival Adjustments

| Red Team Result | Survival Factor | Meaning |
|-----------------|-----------------|---------|
| SURVIVED (no fatal flaws) | 1.0 | Hypothesis withstood scrutiny |
| SURVIVED with minor notes | 0.95 | Minor issues noted but not fatal |
| WEAKENED (addressable contradictions) | 0.80 | Contradictions exist but may be explained |
| SEVERELY WEAKENED | 0.50 | Major contradictions, hypothesis questionable |
| DESTROYED (fatal contradiction) | 0.10 | Hypothesis should be abandoned |

---

## 5. Complete Calibrated Confidence Formula

### Full Calculation

```
Calibrated Confidence =
    Raw_Confidence
    × (1 - Gap_Penalty)
    × Evidence_Quality
    × Red_Team_Survival
    × Prior_Adjustment  # Optional, when priors available
```

### Worked Example: Full Calculation

**Scenario**: Hereditary spherocytosis hypothesis

| Component | Value | Rationale |
|-----------|-------|-----------|
| Raw Confidence | 78% | Agent average |
| Gap Penalty | 10.5% | Missing EMA, Coombs tests |
| Evidence Quality | 0.775 | Strong genetic + labs |
| Red Team Survival | 1.0 | Survived adversarial testing |
| Prior Adjustment | 1.0 | No adjustment (evidence strong enough) |

**Calculation**:
```
Calibrated = 0.78 × (1 - 0.105) × 0.775 × 1.0 × 1.0
           = 0.78 × 0.895 × 0.775
           = 0.541 = 54.1%
```

**Interpretation**: Despite high raw confidence (78%), calibrated confidence is 54% because:
- Gap penalty reduces for missing tests
- Evidence quality weight reflects mix of strong and weak evidence

---

## 6. Confidence Intervals

### Calculating Uncertainty Range

```
Uncertainty Range = ± (Base_Uncertainty × Complexity_Factor)

Base_Uncertainty:
- 4 agents agree: ±5%
- 3 agents agree: ±8%
- 2 agents agree: ±12%
- Split decision: ±15%

Complexity_Factor:
- Simple condition: 1.0
- Moderate complexity: 1.2
- High complexity: 1.5
- Very complex (multiple comorbidities): 2.0
```

### Worked Example

**Scenario**: 3/4 agents agree on HS diagnosis, moderate complexity

```
Uncertainty = ± (8% × 1.2) = ±9.6% ≈ ±10%

If calibrated confidence = 54%
Report as: 54% ±10% (range: 44-64%)
```

---

## 7. Reporting Guidelines

### Required Elements

1. **Raw confidence** with source (agent average, consensus, etc.)
2. **Gap penalty applied** with list of missing tests
3. **Evidence quality score** with evidence type breakdown
4. **Red Team survival status**
5. **Final calibrated confidence** with uncertainty range
6. **Calculation shown** for transparency

### Example Report Section

```markdown
## Confidence Calculation

**Raw Confidence**: 78% (average of 4 agents)

**Gap Penalty**: -10.5%
- Missing EMA binding test: -3%
- Missing osmotic fragility: -2%
- Missing bone marrow: -1.5%
- Missing direct Coombs: -4%

**Evidence Quality**: 0.775
- Genetic confirmation: 1.0 weight
- Lab patterns (2): 0.8 weight each
- Family history: 0.5 weight

**Red Team Status**: SURVIVED (1.0)

**Calibrated Confidence**: 54% ±10%

Calculation: 0.78 × 0.895 × 0.775 × 1.0 = 0.541
```

---

## 8. When to Override Calibration

### Increase Confidence Despite Formula

- Gold standard test positive (override to >90%)
- Genetic confirmation of pathogenic variant (override to >85%)
- Expert clinical diagnosis documented (note as supporting)

### Decrease Confidence Despite Formula

- Multiple red flags for alternative diagnosis
- Patient doesn't fit typical presentation
- Key contradictory evidence unexplained

Always document overrides with rationale.
