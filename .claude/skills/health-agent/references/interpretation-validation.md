# Interpretation Validation Checklist

This document provides validation rules for the Evidence Verification Agent to check not just that cited evidence exists, but that interpretations are reasonable.

## Overview

Citation verification alone is insufficient. An agent can cite accurate data but draw incorrect conclusions. Interpretation validation catches:

1. Unit inconsistencies
2. Reference range misinterpretation
3. Invalid pattern claims
4. Temporal logic errors
5. Statistical overreach
6. Causal overclaiming

---

## 1. Unit Consistency Check

### Rule

All citations of the same marker must use consistent units, or conversions must be correct.

### Validation Steps

1. Extract all citations for the same lab marker across agent reports
2. Compare units used in each citation
3. If different units appear, verify conversion is correct

### Common Unit Conversions

| Marker | Primary Unit | Alternative | Conversion |
|--------|-------------|-------------|------------|
| Glucose | mg/dL | mmol/L | ÷ 18 |
| HbA1c | % | mmol/mol | × 10.93 |
| Bilirubin | mg/dL | μmol/L | × 17.1 |
| Creatinine | mg/dL | μmol/L | × 88.4 |
| Cholesterol | mg/dL | mmol/L | ÷ 38.67 |
| Hemoglobin | g/dL | g/L | × 10 |

### Example Validation

**Citation 1**: "Bilirubin 2.8 mg/dL"
**Citation 2**: "Bilirubin 47.88 μmol/L"

**Check**: 2.8 × 17.1 = 47.88 ✓ Conversion correct

### Failure Example

**Citation 1**: "Glucose 180 mg/dL (elevated)"
**Citation 2**: "Glucose 10 mmol/L (elevated)"

**Check**: 180 ÷ 18 = 10 ✓ Conversion correct
**But**: If agent used wrong reference range for mmol/L, that's a separate error

---

## 2. Reference Range Accuracy

### Rule

When an agent claims a value is "abnormal," "elevated," or "low," verify against actual reference range.

### Validation Steps

1. Extract the cited value
2. Look up actual reference range from data source
3. Verify the direction (high/low) is correct
4. Check if margin is significant

### Margin Significance Guidelines

| Deviation | Classification |
|-----------|---------------|
| <5% outside range | Borderline (should note) |
| 5-20% outside range | Mildly abnormal |
| 20-50% outside range | Moderately abnormal |
| >50% outside range | Severely abnormal |

### Example Validation

**Citation**: "Reticulocytes significantly elevated at 2.1%"
**Actual data**: Value: 2.1%, Reference: 0.5-2.0%

**Check**: 2.1 is 5% above upper limit (2.0)
**Verdict**: ⚠️ "Significantly elevated" is overstatement for borderline value

### Failure Examples

| Claim | Actual Value | Reference | Verdict |
|-------|--------------|-----------|---------|
| "Bilirubin elevated" | 0.9 mg/dL | 0.1-1.2 | ❌ Within range |
| "Iron deficiency" | Ferritin 25 ng/mL | 15-150 | ❌ Within range |
| "Normal creatinine" | 1.8 mg/dL | 0.7-1.3 | ❌ Actually elevated |

---

## 3. Pattern Validity

### Rule

When an agent claims a "trend," "pattern," or "consistent" finding, verify the claim with statistical rigor.

### Validation Steps

1. Extract all data points cited as part of the pattern
2. Check if pattern actually exists:
   - Trend: Is direction consistent?
   - Pattern: Do most points fit?
   - Consistency: Are there contradicting points?
3. Flag patterns based on too few data points

### Minimum Data Points for Claims

| Claim Type | Minimum Points | Notes |
|------------|----------------|-------|
| "Trend" (increasing/decreasing) | 3 | Must be monotonic or near-monotonic |
| "Consistently elevated" | 4 | >75% of points above range |
| "Pattern of" | 3 | Related observations |
| "Correlation between" | 5 | Co-occurring pairs |

### Trend Validation

**Claim**: "HbA1c trending downward"

**Data**:
- 2024-01: 7.2%
- 2024-06: 6.8%
- 2024-12: 7.0%
- 2025-06: 6.5%

**Analysis**:
- Direction: Overall downward (7.2 → 6.5)
- But: Not monotonic (reversal 6.8 → 7.0)
- Verdict: ⚠️ General downward trend, but not consistent

### Pattern Validation

**Claim**: "Reticulocytes consistently elevated"

**Data**: 2.1%, 3.5%, 1.8%, 2.8%, 3.2% (reference: 0.5-2.0%)

**Analysis**:
- 4/5 values elevated (80%)
- 1 value within range (1.8%)
- Verdict: ✓ Valid claim (>75% fit pattern)

### Failure Examples

| Claim | Data Points | Verdict |
|-------|-------------|---------|
| "Trending upward" | 2 values | ❌ Need ≥3 points |
| "Consistently high" | 2/4 elevated | ❌ Only 50% fit |
| "Pattern of fatigue correlating with low iron" | 2 co-occurrences | ❌ Need ≥5 pairs |

---

## 4. Temporal Logic

### Rule

Causes must precede effects in cited evidence. Proposed mechanisms must respect temporal sequence.

### Validation Steps

1. Identify claimed cause-effect relationships
2. Extract dates for both cause and effect
3. Verify cause date < effect date
4. Check if time gap is plausible for mechanism

### Temporal Plausibility Guidelines

| Mechanism Type | Expected Time Gap |
|----------------|-------------------|
| Drug effect (acute) | Hours to days |
| Drug effect (chronic) | Weeks to months |
| Nutritional deficiency effect | Months |
| Genetic condition expression | Persistent/lifelong |
| Infection → lab change | Days to weeks |
| Inflammation → CRP elevation | Hours to days |

### Example Validation

**Claim**: "Iron supplementation resolved anemia"
**Start supplement**: 2025-03-15
**Hemoglobin normalized**: 2025-04-20

**Analysis**:
- Gap: ~5 weeks
- Expected for iron supplementation: 4-12 weeks
- Verdict: ✓ Temporally plausible

### Failure Examples

| Claim | Cause Date | Effect Date | Verdict |
|-------|------------|-------------|---------|
| "Infection caused elevated WBC" | 2025-03-20 | 2025-03-15 | ❌ Effect before cause |
| "Starting statin immediately lowered cholesterol" | 2025-01-01 | 2025-01-07 | ❌ Too fast (need 4-6 weeks) |
| "Vitamin D supplementation fixed deficiency" | Day 1 | Day 3 | ❌ Too fast (need months) |

---

## 5. Statistical Reasonableness

### Rule

Claims about significance, correlation, or probability must be statistically reasonable given data quantity.

### Validation Steps

1. Identify statistical claims
2. Count available data points
3. Assess if claim is supportable

### Statistical Claim Guidelines

| Claim | Minimum Requirement |
|-------|---------------------|
| "Correlated" | n ≥ 5, consistent direction |
| "Significant difference" | n ≥ 10 each group, clear separation |
| "Normal/abnormal" | n ≥ 3 for pattern |
| "XX% confidence" | Based on multiple evidence types |
| "Risk factor" | Epidemiological data cited |

### Confidence Claim Validation

**Claim**: "85% confidence in hereditary spherocytosis"

**Required for 85%**:
- Multiple evidence types (genetics, labs, clinical)
- Survived Red Team scrutiny
- No major contradictions
- Most agents agree

**If based on single lab pattern**: ⚠️ Overconfident

### Failure Examples

| Claim | Data | Verdict |
|-------|------|---------|
| "Strong correlation" | 3 data points | ❌ Insufficient for correlation |
| "90% confidence" | Single agent, no verification | ❌ Overconfident |
| "Statistically significant" | No statistical test performed | ❌ Unsupported claim |

---

## 6. Causal Overclaiming

### Rule

Distinguish between correlation (A and B occur together) and causation (A causes B). Agents often overclaim causation.

### Causal Language Hierarchy

| Language | Strength | Requirements |
|----------|----------|--------------|
| "May contribute to" | Weak | Plausible mechanism |
| "Associated with" | Correlation | Co-occurrence data |
| "Likely contributes to" | Moderate | Mechanism + temporal + literature |
| "Causes" | Strong | RCT or overwhelming evidence |
| "Definitively causes" | Strongest | Established medical fact |

### Validation Steps

1. Identify causal claims
2. Assess strength of claim language
3. Check if evidence supports that strength

### Example Validation

**Claim**: "Sleep deprivation causes the patient's headaches"

**Evidence**:
- 5 headaches correlated with poor sleep
- 2 headaches without poor sleep
- Biological plausibility (literature supports)

**Analysis**:
- Correlation present but not universal (5/7 = 71%)
- Mechanism plausible
- But: 2 counterexamples exist
- Verdict: ⚠️ Should say "likely contributes to" not "causes"

### Common Overclaiming Patterns

| Overclaim | Should Be | Why |
|-----------|-----------|-----|
| "Genetic mutation causes disease" | "Associated with increased risk" | Incomplete penetrance |
| "Supplement fixed deficiency" | "Deficiency improved after supplementation" | Correlation, might be coincidence |
| "Stress causes symptoms" | "Symptoms associated with stress periods" | Common confounder: both from same root cause |

---

## 7. Verification Checklist Template

### For Each Agent Report

```markdown
## Interpretation Validation: {Agent Name}

### Unit Consistency
- [ ] All marker units consistent or properly converted
- Markers checked: {list}
- Issues found: {none / list issues}

### Reference Range Accuracy
- [ ] All "abnormal" claims verified against actual ranges
- [ ] Severity descriptions match deviation magnitude
- Claims checked: {count}
- Issues found: {none / list issues}

### Pattern Validity
- [ ] All trend claims have ≥3 data points
- [ ] All "consistent" claims have ≥75% fit
- [ ] All correlations have ≥5 paired observations
- Pattern claims checked: {count}
- Issues found: {none / list issues}

### Temporal Logic
- [ ] All cause-effect relationships respect time sequence
- [ ] Time gaps are plausible for claimed mechanisms
- Causal claims checked: {count}
- Issues found: {none / list issues}

### Statistical Reasonableness
- [ ] Confidence claims match evidence strength
- [ ] No overclaiming from small samples
- Statistical claims checked: {count}
- Issues found: {none / list issues}

### Causal Overclaiming
- [ ] Causal language matches evidence strength
- [ ] Correlations not presented as causation
- Causal claims checked: {count}
- Issues found: {none / list issues}

### Summary
- Total interpretations validated: {count}
- Passed: {count} ({percentage}%)
- Flagged for review: {count}
- Major errors requiring correction: {count}
```

---

## 8. Common Interpretation Errors

### Error Patterns to Watch For

| Error Pattern | Example | Correct Interpretation |
|---------------|---------|----------------------|
| **Borderline = Abnormal** | "MCV 101 fL is elevated" (range 80-100) | "MCV borderline elevated at 101 fL" |
| **Single point = Trend** | "Creatinine trending up" (one value) | "Creatinine elevated in most recent test" |
| **Correlation = Causation** | "B12 deficiency caused fatigue" | "Fatigue temporally associated with low B12" |
| **Absence = Normal** | "No thyroid disease (TSH not tested)" | "Thyroid status unknown (not tested)" |
| **Genetic = Definitive** | "Has HS gene, therefore has HS" | "Genetic variant associated with HS risk" |
| **Normal = Ruled Out** | "Normal ferritin rules out iron deficiency" | "Ferritin can be normal despite functional deficiency" |

### Red Flags in Agent Reports

1. **Confidence without evidence count**: "85% confident" without listing evidence
2. **"Clearly" or "definitely"**: Overconfident language
3. **Ignoring counterexamples**: Not addressing contradictory evidence
4. **Cherry-picked timeframes**: Only citing data from supportive periods
5. **Mechanism without citation**: Proposed pathway without literature support

---

## 9. Severity Classification

### Interpretation Error Severity

| Severity | Definition | Action |
|----------|------------|--------|
| **Minor** | Imprecise language, doesn't affect conclusion | Note in report |
| **Moderate** | Overstatement that could mislead | Flag and correct |
| **Major** | Factually incorrect interpretation | Requires correction before consensus |
| **Critical** | Could lead to wrong diagnosis | Block hypothesis from consensus |

### Examples by Severity

| Error | Severity | Rationale |
|-------|----------|-----------|
| "Elevated" for borderline value | Minor | Direction correct, magnitude overstated |
| "Consistent pattern" with 2/5 fit | Moderate | Could mislead about evidence strength |
| "Normal" for abnormal value | Major | Factually wrong |
| "Ruled out" when not tested | Critical | Could miss actual diagnosis |
