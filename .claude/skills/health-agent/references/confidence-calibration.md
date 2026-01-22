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
