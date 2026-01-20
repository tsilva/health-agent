---
name: evidence-contradiction-check
description: Find evidence contradicting a hypothesis. Use when user asks "find evidence against hypothesis X", "what contradicts the idea that X causes Y", "test whether X is true", "what counter-examples exist", or wants to verify or falsify a health hypothesis.
---

# Evidence Contradiction Check

Test a hypothesis by searching for contradictory evidence in health data.

## Workflow

1. Get all data paths from profile
2. Parse the hypothesis to test
3. Define what should be true if hypothesis is correct (predictions)
4. Search data for counter-examples (contradictions)
5. Quantify frequency of contradictions
6. Assess whether contradictions are fatal or explainable
7. Update hypothesis likelihood based on evidence

## Efficient Data Access

Data files often exceed Claude's 256KB read limit. Use these extraction patterns:

### Timeline: Extract All Events of Type

```bash
head -1 "{health_log_path}/health_log.csv" && grep -i "{event_keyword}" "{health_log_path}/health_log.csv" | sort -t',' -k1
```

### Timeline: Extract Events in Date Range

```bash
head -1 "{health_log_path}/health_log.csv" && awk -F',' -v start="{start_date}" -v end="{end_date}" '$1 >= start && $1 <= end' "{health_log_path}/health_log.csv"
```

### Timeline: Filter by Category

```bash
head -1 "{health_log_path}/health_log.csv" && grep ",{category}," "{health_log_path}/health_log.csv"
```
Categories: symptom, medication, condition, provider, supplement, watch, todo

### Labs: Extract All Measurements of Marker

```bash
head -1 "{labs_path}/all.csv" && grep -i "{marker}" "{labs_path}/all.csv" | sort -t',' -k1
```

### Labs: Find Out-of-Range Values

```bash
head -1 "{labs_path}/all.csv" && awk -F',' 'NR==1 || ($5 != "" && $6 != "" && $7 != "" && ($5 < $6 || $5 > $7))' "{labs_path}/all.csv"
```

(Assumes columns: date, source_file, page_number, lab_name, value, reference_min, reference_max)

## Hypothesis Testing Process

### Step 1: Define Testable Predictions

For hypothesis "X causes Y", define what must be true:

**Necessary Predictions**:
- **Temporal requirement**: X must precede Y (not after)
- **Consistency requirement**: Every time X occurs, Y should follow (or most times)
- **Absence requirement**: When X is absent, Y should be rare or absent

**Supporting Predictions**:
- **Dose-response**: Stronger X → stronger Y
- **Mechanism markers**: Intermediate biomarkers should change
- **Reversibility**: Removing X should reduce Y

### Step 2: Search for Contradictions

For each prediction, search data for counter-examples:

#### Contradiction Type 1: Temporal Violations

**Prediction**: X precedes Y
**Contradiction**: Y occurs without X, or Y occurs before X

**Search method**:
1. Extract all Y instances
2. For each Y, check if X occurred in preceding window (e.g., 1-14 days before)
3. Flag Y instances with no preceding X

#### Contradiction Type 2: Consistency Violations

**Prediction**: X is followed by Y
**Contradiction**: X occurs without subsequent Y

**Search method**:
1. Extract all X instances
2. For each X, check if Y occurred in following window (e.g., 1-14 days after)
3. Flag X instances with no following Y

#### Contradiction Type 3: Absence Violations

**Prediction**: Y requires X (Y should be rare/absent when X is absent)
**Contradiction**: Y occurs frequently even when X is absent

**Search method**:
1. Identify periods when X is absent
2. Search for Y instances during those periods
3. Calculate Y frequency during X-absent vs X-present periods

#### Contradiction Type 4: Dose-Response Violations

**Prediction**: Stronger X → stronger Y
**Contradiction**: Weak X → strong Y, or strong X → weak Y

**Search method**:
1. Categorize X instances by intensity (if quantifiable)
2. Categorize Y instances by severity (if quantifiable)
3. Check if correlation exists between X intensity and Y severity

### Step 3: Quantify Contradiction Frequency

Calculate:
- **Support rate**: % of instances supporting hypothesis
- **Contradiction rate**: % of instances contradicting hypothesis
- **Ambiguous rate**: % of instances unclear

**Thresholds**:
- **Strong support**: >80% support, <10% contradiction
- **Moderate support**: 60-80% support, 10-30% contradiction
- **Weak support**: 40-60% support, 30-50% contradiction
- **No support**: <40% support, >50% contradiction

### Step 4: Assess Contradiction Severity

Not all contradictions are equal:

**Fatal Contradictions** (hypothesis likely false):
- Temporal violations (Y before X)
- Mechanistic impossibility (hypothesis violates known biology)
- High contradiction rate (>50%) with no explainable pattern

**Explainable Contradictions** (hypothesis may still be true):
- Insufficient lag time (searched too soon after X)
- Confounding factors (other variables explain exceptions)
- Measurement error (low confidence data)
- Threshold effects (X must exceed threshold to cause Y)

## Output Format

```
## Hypothesis Test: {Hypothesis Statement}

**Hypothesis**: {X} causes {Y}

**Test Period**: {start_date} to {end_date}

---

### Testable Predictions

If this hypothesis is correct, the following should be true:

1. **Temporal prediction**: {X} should precede {Y}
2. **Consistency prediction**: Most {X} instances should be followed by {Y}
3. **Absence prediction**: {Y} should be rare when {X} is absent
4. **Dose-response prediction**: Stronger {X} → stronger {Y} (if applicable)

---

### Evidence Analysis

#### Supporting Evidence

**Instances Supporting Hypothesis**: {count}/{total} ({percentage}%)

| Date | Event X | Date | Event Y | Lag Time | Notes |
|------|---------|------|---------|----------|-------|
| {date} | {description} | {date} | {description} | {days} days | {notes} |
| ... | ... | ... | ... | ... | ... |

**Pattern**: {Description of supporting pattern}

---

#### Contradictory Evidence

**Instances Contradicting Hypothesis**: {count}/{total} ({percentage}%)

##### Contradiction Type 1: {Type} ({count} instances)

**Description**: {What contradiction was found}

| Date | Observation | Why This Contradicts | Possible Explanation |
|------|-------------|---------------------|---------------------|
| {date} | {description} | {reason} | {explanation or "unclear"} |
| ... | ... | ... | ... |

**Assessment**: {Are these contradictions fatal or explainable?}

---

##### Contradiction Type 2: {Type} ({count} instances)

**Description**: {What contradiction was found}

{Details as above}

---

#### Ambiguous Evidence

**Instances Where Evidence Is Unclear**: {count}/{total} ({percentage}%)

**Reasons for Ambiguity**:
- {Reason 1} ({count} instances)
- {Reason 2} ({count} instances)

---

### Quantitative Assessment

| Metric | Value |
|--------|-------|
| **Total instances analyzed** | {count} |
| **Supporting instances** | {count} ({percentage}%) |
| **Contradicting instances** | {count} ({percentage}%) |
| **Ambiguous instances** | {count} ({percentage}%) |
| **Support rate** | {percentage}% |

**Verdict**: {Strong support / Moderate support / Weak support / No support}

---

### Contradiction Severity Analysis

#### Fatal Contradictions (Hypothesis Likely False)

{If none, say "None identified"}

{If any, list them}:
- **{Contradiction}**: {Why this is fatal to the hypothesis}

---

#### Explainable Contradictions (Hypothesis May Still Be True)

{List contradictions that have plausible explanations}:
- **{Contradiction}**: Possible explanation: {explanation}
  - **How to test**: {What data would confirm/rule out this explanation}

---

### Revised Hypothesis

Based on contradictory evidence, the hypothesis should be revised:

**Original Hypothesis**: {X} causes {Y}

**Revised Hypothesis**: {Refined version based on evidence}

**Refinements**:
- {Refinement 1} (addresses {contradiction})
- {Refinement 2} (addresses {contradiction})

**Confidence Level**: {High / Moderate / Low}

**Remaining Questions**:
- {Question 1 that data cannot answer}
- {Question 2 that requires more data}

---

### Recommendations

#### To Strengthen Hypothesis

If hypothesis still seems plausible:
1. **Collect additional data**: {What to track going forward}
2. **Test specific predictions**: {What should happen if hypothesis is correct}
3. **Control for confounds**: {What factors to control or track}

#### To Falsify Hypothesis

If hypothesis seems weak:
1. **Alternative hypotheses to test**: {Other explanations to investigate}
2. **Discriminating tests**: {What data would distinguish between hypotheses}

---

### Disclaimer

This analysis tests a hypothesis against available data. Important notes:
- Absence of contradictions does not prove causation
- Contradictions may be due to incomplete data
- Biological systems are complex; multiple factors may interact
- This analysis is not a substitute for controlled scientific studies
- Always consult a healthcare provider before making decisions based on these findings
```

## Special Considerations

### Null Hypothesis Testing

Sometimes the goal is to test if X does NOT cause Y:
- Search for supporting evidence (X followed by Y)
- If strong evidence found, null hypothesis is rejected
- If little evidence found, null hypothesis is supported

### Confidence Scores in Lab Data

Labs have OCR confidence scores (0-1):
- Flag contradictions based on low-confidence data (<0.8)
- Note that some contradictions may be measurement errors

### Time Windows Matter

Different mechanisms have different lag times:
- **Acute effects**: Hours to days (e.g., caffeine → jitteriness)
- **Subacute effects**: Days to weeks (e.g., medication → side effect)
- **Chronic effects**: Weeks to months (e.g., poor diet → metabolic changes)

Adjust search windows based on hypothesized mechanism.

### Dose-Response Analysis

If X or Y are quantifiable:
- X: Medication dosage, stress intensity, sleep hours, exercise duration
- Y: Lab values, symptom severity (if tracked)

Perform correlation analysis between X intensity and Y severity.

### Genetics as Moderator (Optional)

If genetics is configured:
- Some hypotheses may only be true for specific genotypes
- Example: "Medication X causes side effect Y" may only be true for poor metabolizers
- Check pharmacogenomics variants to explain contradictions

Consult references/genetics-pharmacogenomics.md if relevant.

### Multiple Hypothesis Testing

If testing multiple hypotheses simultaneously:
- Risk of false positives increases
- Be more stringent with evidence requirements
- Consider Bonferroni correction (stricter thresholds)

## Example Invocations

User: "Find evidence against the hypothesis that sugar causes my headaches"
→ Extract all headache events and sugar intake events (if tracked)
→ Search for headaches without sugar, sugar without headaches
→ Quantify support vs contradiction rate

User: "Test whether my fatigue is caused by poor sleep"
→ Define prediction: poor sleep should precede fatigue
→ Search for fatigue episodes and check if poor sleep occurred 1-2 days prior
→ Search for poor sleep episodes and check if fatigue followed
→ Quantify correlation and identify contradictions

User: "Does the evidence support that my new medication improved my anxiety?"
→ Extract anxiety events before and after medication start
→ Compare anxiety frequency/severity pre vs post medication
→ Search for confounds (other changes concurrent with medication)
→ Assess if improvement is attributable to medication
