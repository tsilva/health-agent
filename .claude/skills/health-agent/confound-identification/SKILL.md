---
name: confound-identification
description: Identify potential confounding factors for an observed correlation. Use when user asks "what could confound X and Y", "what else changed during that time", "could something else explain this correlation", "what factors might interfere", or wants to rule out alternative explanations for observed patterns.
---

# Confound Identification

Identify potential confounding factors that could explain an observed correlation.

## Workflow

1. Get all data paths from profile
2. Parse the observed correlation (factor A → factor B)
3. Determine the time period of the correlation
4. Extract all timeline events overlapping with correlation period
5. Identify medications/supplements that changed
6. Check for environmental or lifestyle factors
7. Flag temporal clustering of multiple changes
8. Assess each potential confound's plausibility

## Efficient Data Access

Data files often exceed Claude's 256KB read limit. Use these extraction patterns:

### Timeline: Extract Events in Date Range

```bash
head -1 "{health_log_path}/health_log.csv" && awk -F',' -v start="{start_date}" -v end="{end_date}" '$1 >= start && $1 <= end' "{health_log_path}/health_log.csv"
```

### Timeline: Medication/Supplement Changes

```bash
head -1 "{health_log_path}/health_log.csv" && grep -E ",(medication|supplement)," "{health_log_path}/health_log.csv" | awk -F',' -v start="{start_date}" -v end="{end_date}" '$1 >= start && $1 <= end'
```

### Timeline: All Events by Category

```bash
head -1 "{health_log_path}/health_log.csv" && grep ",{category}," "{health_log_path}/health_log.csv"
```
Categories: symptom, medication, condition, provider, supplement, watch, todo

### Labs: Identify Other Lab Changes in Same Period

```bash
head -1 "{labs_path}/all.csv" && awk -F',' -v start="{start_date}" -v end="{end_date}" '$1 >= start && $1 <= end' "{labs_path}/all.csv" | sort -t',' -k1
```

## Confound Detection Process

### Step 1: Define Correlation Window

For the observed correlation "A → B":
1. Identify all instances of A
2. Identify all instances of B
3. Determine the typical lag time (A to B)
4. Define search window: [first A - buffer] to [last B + buffer]
   - Buffer typically 14-30 days to catch changes before/after

### Step 2: Extract Overlapping Events

Within the correlation window, extract:
- **Medication changes**: New medications, dosage changes, discontinuations
- **Supplement changes**: New supplements, dosage changes, discontinuations
- **Lifestyle changes**: Sleep pattern changes, stress events, exercise changes
- **Environmental changes**: Travel, season changes, location changes
- **Other health events**: New symptoms, conditions, procedures

### Step 3: Assess Temporal Overlap

For each potential confound:
- **Complete overlap**: Confound present in ALL correlation instances → HIGH risk
- **Partial overlap**: Confound present in SOME instances → MODERATE risk
- **No overlap**: Confound absent from correlation instances → LOW risk

### Step 4: Assess Plausibility

For each confound, consider:
- **Biological plausibility**: Could this confound directly affect A or B?
- **Temporal sequence**: Did confound start before or concurrent with correlation?
- **Dose-response**: Do stronger confound exposures correlate with stronger A-B association?
- **Known mechanisms**: Is this a known confounder in medical literature?

## Confound Categories

### Type 1: Medication Confounds

**High Risk Confounds**:
- Medications affecting the same physiological system as A or B
- Medications with known side effects matching B
- Medication timing coincides with every A-B correlation instance

**Example**: User observes "fatigue correlates with poor sleep"
- Confound: Started antihistamine (causes drowsiness) at same time as sleep problems began
- Assessment: HIGH risk - antihistamine directly causes fatigue, complete temporal overlap

### Type 2: Supplement Confounds

**High Risk Confounds**:
- Supplements with pharmacological effects (e.g., St. John's Wort, high-dose vitamins)
- Supplements affecting same pathway as A or B
- Dosage changes coinciding with correlation

**Example**: User observes "anxiety episodes correlate with elevated heart rate"
- Confound: Increased caffeine intake (coffee + energy drinks) during stress periods
- Assessment: HIGH risk - caffeine directly affects heart rate and anxiety

### Type 3: Lifestyle Confounds

**Common Confounds**:
- **Sleep**: Poor sleep affects stress, mood, immune function, metabolism
- **Stress**: Stress affects sleep, eating, exercise, immune function
- **Diet**: Dietary changes affect energy, mood, inflammation, labs
- **Exercise**: Exercise affects mood, sleep, cardiovascular markers, metabolism

**Clustering Risk**: Lifestyle factors often cluster (stress → poor sleep → poor diet → low exercise)

### Type 4: Environmental Confounds

**Common Confounds**:
- **Season**: Vitamin D (winter), allergies (spring), heat stress (summer)
- **Travel**: Time zones, diet changes, stress, infection exposure
- **Location**: Air quality, altitude, allergen exposure
- **Work**: Job changes, schedule changes, stress levels

### Type 5: Comorbid Condition Confounds

**High Risk Confounds**:
- New diagnosis or condition onset during correlation period
- Condition affects same system as A or B
- Condition requires treatment that could affect B

**Example**: User observes "fatigue correlates with elevated CRP"
- Confound: Developed hypothyroidism during same period
- Assessment: HIGH risk - hypothyroidism directly causes fatigue and can elevate CRP

## Output Format

```
## Confound Analysis: {Factor A} → {Factor B}

**Observed Correlation**: {Description of A-B correlation}
**Correlation Period**: {start_date} to {end_date}
**Number of Instances**: {count}

---

### Potential Confounds

#### High Risk Confounds

##### Confound 1: {Name} (COMPLETE OVERLAP)

**Type**: Medication / Supplement / Lifestyle / Environmental / Comorbid Condition

**Temporal Overlap**:
- Started: {date}
- Present in correlation instances: {X}/{total} ({percentage}%)
- Temporal relationship: {Started before / Concurrent with / After} first correlation instance

**Biological Plausibility**: {Why this confound could directly affect A or B}

**Supporting Evidence**:
- {health_log_path}/health_log.csv: {date}, {event}
- {labs_path}/all.csv: {marker} changed from {baseline} to {new_value}

**Assessment**: This confound has COMPLETE temporal overlap and DIRECT biological plausibility. It could fully or partially explain the observed correlation.

---

##### Confound 2: {Name} (PARTIAL OVERLAP)

**Type**: {type}

**Temporal Overlap**:
- Present in correlation instances: {X}/{total} ({percentage}%)

**Biological Plausibility**: {Why this confound could affect A or B}

**Assessment**: This confound has PARTIAL overlap. It may contribute to some instances but does not explain all observations.

---

#### Moderate Risk Confounds

##### Confound 3: {Name}

**Type**: {type}

**Temporal Overlap**: {description}

**Biological Plausibility**: {description}

**Assessment**: Moderate plausibility, worth monitoring but unlikely to fully explain correlation.

---

#### Low Risk Confounds

##### Confound 4: {Name}

**Why This Is Unlikely**: {Reason this confound does not explain the correlation}

---

### Clustering Analysis

**Multiple Changes Detected**: {Yes/No}

{If yes, describe temporal clustering}:
During the period {date_range}, the following changes occurred within {X} days of each other:
1. {Change 1} on {date}
2. {Change 2} on {date}
3. {Change 3} on {date}

**Assessment**: Multiple simultaneous changes make it difficult to isolate which factor is responsible for the observed correlation. Consider this a HIGH risk confound scenario.

---

### Differential Testing

To determine if confounds explain the correlation:

#### Test 1: Temporal Separation
**Method**: Wait for instances of A WITHOUT the confound present
**Prediction**: If confound explains correlation, B should NOT occur when confound is absent
**Data needed**: Continue tracking A, B, and confound status

#### Test 2: Confound Removal
**Method**: Remove the confound (if safe/feasible)
**Prediction**: If confound explains correlation, A-B association should weaken or disappear
**Example**: If medication is confound, discuss with provider about trial off medication

#### Test 3: Dose-Response
**Method**: Track confound intensity/dosage
**Prediction**: If confound explains correlation, stronger confound → stronger A-B association
**Example**: If caffeine is confound, track daily intake and correlate with symptom severity

---

### Recommendations

Based on this analysis:
1. **High priority**: {Confound to investigate or remove}
2. **Monitor**: {Confounds to track going forward}
3. **Unlikely**: {Confounds that can be ruled out}

**Next Steps**:
- {Specific action to test confound hypothesis}
- {Data to collect to strengthen or weaken confound case}
- {Provider discussion points if confound is medication-related}

---

### Disclaimer

Confound identification helps distinguish correlation from causation. Important notes:
- Confounds may coexist with true causal relationships
- Removing a confound is not always safe or feasible (consult provider for medications)
- Multiple confounds may interact in complex ways
- This analysis is based on available data, which may be incomplete
- Always consult a healthcare provider before making changes based on this analysis
```

## Special Considerations

### Medication Confounds Require Provider Consultation

If medications are identified as high-risk confounds:
- **Never recommend discontinuing medications** without provider consultation
- Emphasize that correlation analysis cannot replace clinical judgment
- Suggest discussing findings with prescribing provider
- Note that medication benefits may outweigh confounding effects

### Genetics as Confound (Optional)

If genetics is configured, consider:
- Pharmacogenomics variants as confounds for medication effects
- Health risk variants as confounds for disease development
- Use genetics-snp-lookup skill for gene/SNP lookups and interpretations

### Temporal Clustering Is Common

Many health changes occur in clusters:
- Stress → poor sleep → poor diet → low exercise
- New medication → side effect → second medication for side effect
- Illness → antibiotic → gut dysbiosis → digestive symptoms

Flag clustering explicitly and note that it makes confound identification difficult.

### Absence of Confounds Strengthens Correlation

If NO significant confounds are found:
- This strengthens the case for a direct A-B relationship
- Note this explicitly in the output
- Still emphasize correlation vs causation

## Example Invocations

User: "What could confound the correlation between stress and my blood pressure?"
→ Extract stress events and BP measurements
→ Search for medication changes, caffeine intake, sleep changes
→ Assess temporal overlap and biological plausibility

User: "I noticed my energy improved when I started exercising, but could something else explain it?"
→ Define exercise start date and energy improvement period
→ Search for concurrent medication changes, supplement additions, sleep improvements
→ Identify clustering of multiple lifestyle changes

User: "Could my new medication explain why my labs changed?"
→ Define medication start date and lab change timing
→ Search for other medications, supplements, lifestyle changes in same period
→ Assess pharmacological effects and pharmacogenomics (if genetics configured)
