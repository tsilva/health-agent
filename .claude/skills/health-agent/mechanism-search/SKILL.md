---
name: mechanism-search
description: Search for biological mechanisms linking two observations. Use when user asks "what mechanism could link X to Y", "how does X affect Y", "what's the biological pathway between X and Y", "why would X cause Y", or wants to understand causal pathways between health observations.
---

# Mechanism Search

Identify potential biological mechanisms linking two health observations.

## Workflow

1. Get all data paths from profile
2. Check if `{labs_path}/lab_specs.json` exists for canonical marker names
3. Parse the two observations to link (event/symptom/lab marker)
4. Extract relevant biomarkers from labs using canonical names when available
5. Check genetics for related variants (if configured)
6. Search timeline for intermediate events
7. Consult references for known pathways
8. Propose mechanisms with supporting data points

## Efficient Data Access

Data files often exceed Claude's 256KB read limit. Use these extraction patterns:

### Labs: Using lab_specs.json (Preferred)

If `{labs_path}/lab_specs.json` exists, use it for more accurate marker matching:

```bash
# Source helper functions
source .claude/skills/health-agent/references/lab-specs-helpers.sh

# Build patterns for mechanism-specific marker groups
# Example: Get glucose-related markers
glucose_pattern=$(build_grep_pattern "{labs_path}/lab_specs.json" "glucose")
insulin_pattern=$(build_grep_pattern "{labs_path}/lab_specs.json" "insulin")
hba1c_pattern=$(build_grep_pattern "{labs_path}/lab_specs.json" "hba1c")

# Combine patterns for mechanism category
head -1 "{labs_path}/all.csv" && grep -iE "$glucose_pattern|$insulin_pattern|$hba1c_pattern" "{labs_path}/all.csv" | sort -t',' -k1
```

**Benefit**: Matches all aliases automatically (e.g., "A1C", "Hemoglobin A1c", "Glycated Hemoglobin" all captured).

### Labs: Extract Relevant Biomarkers (Fallback Patterns)

If `lab_specs.json` is not available, use these manual patterns:

For metabolic mechanisms (glucose, insulin, HbA1c):
```bash
head -1 "{labs_path}/all.csv" && grep -iE "(glucose|insulin|a1c|hba1c)" "{labs_path}/all.csv" | sort -t',' -k1
```

For cardiovascular mechanisms (BP, cholesterol, inflammatory markers):
```bash
head -1 "{labs_path}/all.csv" && grep -iE "(cholesterol|triglyceride|ldl|hdl|crp|homocysteine)" "{labs_path}/all.csv" | sort -t',' -k1
```

For hormonal mechanisms (thyroid, cortisol, sex hormones):
```bash
head -1 "{labs_path}/all.csv" && grep -iE "(tsh|t3|t4|cortisol|testosterone|estrogen|dhea)" "{labs_path}/all.csv" | sort -t',' -k1
```

For inflammatory mechanisms (CRP, ESR, WBC):
```bash
head -1 "{labs_path}/all.csv" && grep -iE "(crp|esr|wbc|neutrophil|lymphocyte)" "{labs_path}/all.csv" | sort -t',' -k1
```

For nutritional mechanisms (vitamins, minerals):
```bash
head -1 "{labs_path}/all.csv" && grep -iE "(vitamin|b12|folate|iron|ferritin|magnesium|zinc)" "{labs_path}/all.csv" | sort -t',' -k1
```

### Timeline: Search for Intermediate Events

Extract events between observation A and observation B dates:
```bash
head -1 "{health_log_path}/health_log.csv" && awk -F',' -v start="{start_date}" -v end="{end_date}" '$1 >= start && $1 <= end' "{health_log_path}/health_log.csv"
```

### Timeline: Filter by Category

```bash
head -1 "{health_log_path}/health_log.csv" && grep ",{category}," "{health_log_path}/health_log.csv"
```
Categories: symptom, medication, condition, provider, supplement, watch, todo

### Genetics: Check Relevant Variants (Optional)

If genetics is configured in profile, check for relevant variants:

For metabolic mechanisms:
```bash
grep -E "^(rs1801282|rs5219|rs7903146)" "{genetics_23andme_path}"
```
(PPARG, KCNJ11, TCF7L2 - diabetes risk)

For cardiovascular mechanisms:
```bash
grep -E "^(rs429358|rs7412|rs662799|rs1800588)" "{genetics_23andme_path}"
```
(APOE, APOA5, LIPC - lipid metabolism)

For inflammatory mechanisms:
```bash
grep -E "^(rs1800795|rs1205)" "{genetics_23andme_path}"
```
(IL6, CRP - inflammation)

## Mechanism Identification Process

### Step 1: Classify Observations

Determine the type of each observation:
- **Lab marker**: Specific biomarker (e.g., glucose, cholesterol)
- **Symptom**: Subjective experience (e.g., headache, fatigue)
- **Event**: Discrete occurrence (e.g., stress episode, poor sleep)
- **Condition**: Diagnosed or suspected condition (e.g., hypertension, diabetes)

### Step 2: Identify Potential Pathways

Based on observation types, consider common pathways:

**Stress → Blood Pressure**
- HPA axis activation → cortisol → vasoconstriction
- Sympathetic activation → catecholamines → heart rate/BP increase
- Check: cortisol levels, heart rate data, sleep quality

**Poor Sleep → Metabolic Changes**
- Sleep deprivation → insulin resistance → glucose elevation
- Circadian disruption → leptin/ghrelin imbalance → appetite changes
- Check: glucose, insulin, HbA1c trends

**Inflammation → Fatigue**
- Cytokine release → sickness behavior → fatigue
- Nutrient depletion → mitochondrial dysfunction → energy deficit
- Check: CRP, ESR, WBC, ferritin, vitamin B12

**Medication → Lab Change**
- Direct pharmacological effect
- Drug-drug interaction
- Genetic metabolism variation (pharmacogenomics)
- Check: medication start date vs lab change timing, CYP variants

### Step 3: Search for Supporting Evidence

For each potential pathway:
1. Check if intermediate biomarkers are measured
2. Verify temporal sequence (A precedes B)
3. Look for dose-response (stronger A → stronger B)
4. Search for intermediate events (A → X → B)
5. Check genetics for predisposition (if configured)

### Step 4: Assess Plausibility

Rate each mechanism:
- **High plausibility**: Well-established pathway, supporting biomarker data, correct temporal sequence
- **Moderate plausibility**: Known pathway, partial data support, plausible timing
- **Low plausibility**: Speculative pathway, weak data support, inconsistent timing

## Output Format

```
## Mechanism Search: {Observation A} → {Observation B}

**Analysis Period**: {date_range}
**Data Sources**: Labs, Timeline, Genetics (if configured)

---

### Proposed Mechanisms

#### Mechanism 1: {Pathway Name} (High Plausibility)

**Biological Pathway**:
{Observation A} → {Intermediate Step 1} → {Intermediate Step 2} → {Observation B}

**Supporting Evidence**:
- **Temporal sequence**: {Observation A} occurred on {date}, {Observation B} observed {X} days later
- **Biomarker support**: {Marker} changed from {baseline} to {new_value} ({change}%)
  - {Date}: {Marker} = {Value} {Unit} (reference: {ref_min}-{ref_max})
- **Intermediate events**: {Event} occurred on {date} (between A and B)
- **Genetic predisposition**: {rsID} genotype = {genotype} ({interpretation})

**Data Citations**:
- {labs_path}/all.csv: {specific_rows}
- {health_log_path}/health_log.csv: {specific_dates}
- {genetics_23andme_path}: {rsIDs} (if applicable)

---

#### Mechanism 2: {Pathway Name} (Moderate Plausibility)

**Biological Pathway**:
{Description}

**Supporting Evidence**:
- {Evidence items}

**Missing Data**:
- {What biomarkers or events would strengthen this hypothesis}

---

#### Mechanism 3: {Pathway Name} (Low Plausibility)

**Biological Pathway**:
{Description}

**Why This Is Unlikely**:
- {Reasons this mechanism is not well-supported}

---

### Data Gaps

The following biomarkers would help confirm or rule out mechanisms:
- {Marker 1}: Would confirm {pathway}
- {Marker 2}: Would rule out {alternative pathway}

---

### Recommended Follow-Up

To test these mechanisms:
1. **Track additional data**: {What to monitor going forward}
2. **Test specific predictions**: {What should happen if mechanism is correct}
3. **Consider lab tests**: {What tests could confirm mechanism}

---

### Disclaimer

This analysis proposes potential biological mechanisms based on available data. These are hypotheses, not diagnoses:
- Mechanisms may be speculative or incomplete
- Multiple mechanisms may coexist
- Genetics analysis (if included) is limited to 23andMe data
- Always consult a healthcare provider for clinical interpretation
- This is not medical advice
```

## Special Considerations

### Genetics Integration (Optional)

If `genetics_23andme_path` is configured in profile:
- Include genetics in mechanism search (especially for pharmacogenomics and metabolic pathways)
- Use genetics-snp-lookup skill for gene/SNP lookups and interpretations
- Cite specific rsIDs and genotypes as supporting evidence

If genetics is NOT configured:
- Mechanism search works without genetics
- Omit genetics sections from output
- Focus on biomarker and timeline data

### Common Pitfalls to Avoid

1. **Correlation vs Causation**: Always emphasize temporal sequence, not just co-occurrence
2. **Confounding Factors**: Note when multiple changes occurred simultaneously
3. **Biological Plausibility**: Don't propose mechanisms that violate basic physiology
4. **Data Gaps**: Clearly state when mechanisms are speculative due to missing data

### Consultation with Lab Specifications

Use `{labs_path}/lab_specs.json` (from labs-parser) for:
- Marker name aliases and canonical names (e.g., "A1C" = "HbA1c")
- Reference ranges and unit conversions
- Clinical significance thresholds

### Time Windows for Mechanisms

Different mechanisms have different time scales:
- **Acute stress response**: Minutes to hours
- **Inflammatory response**: Hours to days
- **Metabolic adaptation**: Days to weeks
- **Chronic condition development**: Weeks to months

Adjust search windows based on mechanism type.

## Example Invocations

User: "What mechanism could link stress to my elevated blood pressure?"
→ Search for stress events, BP labs, intermediate markers (cortisol, heart rate)
→ Propose HPA axis and sympathetic activation pathways
→ Check for supporting biomarker data

User: "How does poor sleep affect my glucose levels?"
→ Search for sleep events, glucose labs, insulin data
→ Propose insulin resistance and circadian disruption pathways
→ Check temporal sequence and dose-response

User: "Why would my medication cause liver enzyme elevation?"
→ Search for medication start date, liver enzyme labs
→ Check pharmacogenomics variants (CYP metabolism)
→ Propose direct hepatotoxicity or metabolic pathway
