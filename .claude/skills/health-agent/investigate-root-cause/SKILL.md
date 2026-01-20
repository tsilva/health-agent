---
name: investigate-root-cause
description: Orchestrate comprehensive root cause investigation of a health condition through iterative hypothesis generation, evidence gathering, and testing. Use when user asks "investigate root cause of [condition]", "why do I have [condition]", "find the cause of [symptom]", "diagnose the underlying issue", "explain my [condition]", "what's causing my [condition]", or wants competing hypotheses ranked by evidence.
---

# Root Cause Investigation

Automate comprehensive hypothesis generation and testing for health conditions through multi-turn iterative investigation.

## Workflow

This skill orchestrates a multi-phase investigation by spawning a general-purpose agent that performs the following steps:

1. **Profile Loading**: Load the selected profile YAML and extract data source paths
2. **Condition Parsing**: Parse the condition or symptom to investigate from user input
3. **Agent Spawning**: Immediately spawn a Task agent with complete investigation instructions
4. **Evidence Gathering**: Agent uses analysis skills to collect relevant data across all sources
5. **Hypothesis Generation**: Agent generates 3-5 competing hypotheses with biological mechanisms
6. **Hypothesis Testing**: Agent tests each hypothesis against data for contradictions and confounds
7. **Refinement**: Agent iterates and refines hypotheses based on evidence strength
8. **Report Generation**: Agent produces comprehensive hypothesis investigation report

## Agent Spawning

**CRITICAL**: When this skill is invoked, you MUST IMMEDIATELY spawn a Task agent using the following pattern:

```
Task tool with:
- subagent_type: "general-purpose"
- description: "Investigate root cause of {condition}"
- prompt: [See Agent Prompt Template below]
```

### Agent Prompt Template

```markdown
Investigate the root cause of {condition} in the health data for profile {profile}.

**Profile Data Sources**:
- Labs: {labs_path}/all.csv
- Health Timeline: {health_log_path}/health_log.csv
- Health Log Narrative: {health_log_path}/health_log.md
- Medical Exams: {exams_path}/*/*.summary.md
- Genetics (optional): {genetics_23andme_path}

**Investigation Workflow**:

### Phase 1: Evidence Gathering (Use Analysis Skills)

Gather comprehensive data about the condition:

1. **Timeline Events**: Use `episode-investigation` skill to extract all events related to {condition}
2. **Temporal Patterns**: Use `cross-temporal-correlation` skill to find correlations and patterns
3. **Lab Trends**: Use `lab-trend` skill to track relevant biomarkers over time
4. **Abnormal Labs**: Use `out-of-range-labs` skill to identify flagged values
5. **Medical Exams**: Use `exam-catalog` skill to search for relevant imaging findings
6. **Medications**: Use `medication-supplements` skill to identify medication timeline
7. **Genetics** (if configured): Perform COMPREHENSIVE genetic analysis - see Genetics Analysis Protocol below

**Important**: Use efficient data access commands from each skill's documentation. Do NOT read large files directly.

### Genetics Analysis Protocol (CRITICAL)

If genetics data is configured, you MUST perform comprehensive genetic analysis:

**Step 1: Use Available Genetics Skills**
- `genetics-snp-lookup`: For specific SNPs you want to check
- `genetics-pharmacogenomics`: For drug metabolism genes (CYP2D6, CYP2C19, CYP2C9, VKORC1, SLCO1B1)
- `genetics-health-risks`: For health risk variants (APOE, Factor V Leiden, HFE, MTHFR, BRCA)

**Step 2: Identify Condition-Relevant Genes**

For the condition being investigated, use `genetics-snp-lookup` to identify and query relevant genes:

1. **Search SNPedia** for condition-related genes via genetics-snp-lookup
2. **Query genes** using genetics-snp-lookup's gene/condition lookup modes
3. **Review findings** from SNPedia for both positive AND negative results
4. **Consider genetics** as evidence for/against hypotheses

**Example workflow for investigating elevated bilirubin:**
```
Call genetics-snp-lookup with: "look up UGT1A1 for Gilbert's syndrome"
Call genetics-snp-lookup with: "look up hemochromatosis" (covers HFE genes)
Call genetics-snp-lookup with: "look up G6PD deficiency"
```

genetics-snp-lookup will query SNPedia for condition-relevant rsIDs automatically - no need to hardcode SNP lists.

**Step 3: Direct SNP Lookup via Bash (If Needed)**

For genes not covered by genetics skills, use direct grep commands:

```bash
# Single gene SNPs
grep -E "^(rs123|rs456|rs789)" "{genetics_23andme_path}"

# All SNPs for a gene region (if you know chromosome and position range)
awk -F'\t' '$2 == "10" && $3 >= 101500000 && $3 <= 101700000' "{genetics_23andme_path}"
```

**Step 4: Report All Genetic Findings**

In the report genetics section, include:
1. All checked SNPs (both positive and negative findings)
2. Genotypes and their clinical interpretation
3. What genes were NOT available in 23andMe data
4. Recommendations for clinical sequencing if relevant

**NEVER skip genetic analysis or assume SNPs aren't available without checking first.**

### Phase 2: Hypothesis Generation

Based on gathered evidence, generate 3-5 competing hypotheses:

1. **Formulate hypotheses**: Propose distinct explanations for the condition
2. **Biological mechanisms**: Use `mechanism-search` skill to propose pathways for each hypothesis
3. **Initial likelihood**: Classify each hypothesis as High/Moderate/Low plausibility based on:
   - Temporal sequence (does timeline support causation?)
   - Biological plausibility (is mechanism known/feasible?)
   - Data support (how much evidence supports this?)
   - Evidence strength (quality and directness of supporting data)
   - Prior probability (how common is this explanation?)

### Phase 2.5: Competing Mechanism Analysis

For any abnormal finding, consider BOTH mechanisms before choosing:

**Mechanism A: Primary Defect**
- The clearance/transport system itself is defective
- Example: ABCC2 mutation causing Dubin-Johnson syndrome

**Mechanism B: System Overload**
- The clearance/transport system is NORMAL but overwhelmed by high load
- Example: Normal ABCC2 saturated by massive bilirubin production from hemolysis

**Analysis steps**:
1. Is there evidence of HIGH PRODUCTION of the metabolite? (Check upstream markers)
2. Is the clearance/transport organ functioning normally? (Check organ function markers)
3. Is there confirmatory evidence for a PRIMARY DEFECT? (Genetics, pathognomonic findings)

**Generate hypotheses for BOTH mechanisms**:
- Do NOT dismiss either mechanism prematurely
- Rank based on supporting evidence, NOT assumptions
- Both mechanisms can coexist (e.g., mild defect + moderate overload)

**Example - Elevated Bilirubin**:
- Mechanism A: Dubin-Johnson (ABCC2 defect) - Check: ABCC2 genetics, urine coproporphyrin
- Mechanism B: Hemolysis overload (normal ABCC2) - Check: Reticulocytes, haptoglobin, spherocytosis genetics

Generate BOTH hypotheses and let evidence determine ranking.

### Phase 3: Hypothesis Testing

For each hypothesis, rigorously test against data:

1. **Find contradictions**: Use `evidence-contradiction-check` skill to search for counter-examples
2. **Identify confounds**: Use `confound-identification` skill to find alternative explanations
3. **Quantify support**: Calculate support rate (% of instances supporting hypothesis)
4. **Assess contradictions**: Determine if contradictions are fatal or explainable
5. **Handle missing data correctly**: Distinguish between:
   - **Negative test result**: Test performed, result is negative → Evidence AGAINST hypothesis
   - **Missing test**: Test not performed → NEUTRAL, does NOT count as evidence against hypothesis

**Examples**:
- ❌ "No haptoglobin data available → hemolysis unlikely" (WRONG: missing data treated as negative)
- ✅ "No haptoglobin data available → hemolysis likelihood UNCERTAIN, recommend testing" (CORRECT: missing data is neutral)

**Ranking impact**:
- Missing confirmatory tests should NOT downgrade hypothesis
- Instead, list missing test as "recommended follow-up" to resolve uncertainty

### Phase 4: Refinement and Ranking

Iteratively refine hypotheses:

1. **Revise hypotheses**: Adjust based on contradictions and confounds
2. **Re-rank by evidence**: Order by supporting evidence strength:
   - 🟢 **HIGH (80-95%)**: Strong evidence, few contradictions, clear mechanism
   - 🟡 **MODERATE (40-60%)**: Partial evidence, some contradictions, plausible mechanism
   - 🔴 **LOW (<20%)**: Weak evidence, major contradictions, unclear mechanism
3. **Identify data gaps**: Note what additional data would strengthen/weaken hypotheses
4. **Propose follow-up**: Recommend investigations to discriminate between hypotheses

### Phase 5: Report Generation

Generate a comprehensive report following the Output Format below and save to:

`.output/{profile}/sections/hypothesis-investigation-{condition}-{YYYY-MM-DD}.md`

**Directory Creation**: Use `mkdir -p .output/{profile}/sections` before writing
**File Writing**: Use Write tool (NOT bash heredocs) to create the report

---

**Available Skills**: You have access to all 19 health-agent skills. Use them extensively throughout the investigation.

**Iteration**: If initial hypotheses are weak, iterate and generate alternative explanations. Aim for at least 3 distinct hypotheses.

**Medical Disclaimers**: Include all required disclaimers in the final report (see Output Format).

**Data Citations**: Cite specific dates, lab values, and timeline events for all evidence.

**Time Windows**: Consider appropriate time windows for different mechanisms:
- Acute effects: Hours to days
- Subacute effects: Days to weeks
- Chronic effects: Weeks to months

**Genetics Requirement**: If genetics data is configured, you MUST perform comprehensive genetic analysis following the Genetics Analysis Protocol. Check ALL condition-relevant genes using both genetics skills AND direct grep commands. Report both positive and negative genetic findings in the genetics section of the report.
```

## Output Format

The agent MUST generate a report with the following structure:

```markdown
---
section: hypothesis-investigation-{condition}
generated: {YYYY-MM-DD}
profile: {profile_name}
condition: {condition}
---

# Root Cause Investigation: {Condition}

## Executive Summary

**Diagnosis/Condition Status**: {Current status if known}

**Investigation Period**: {start_date} to {end_date}

**Primary Hypothesis (HIGH/MODERATE/LOW LIKELIHOOD)**: **{Hypothesis name}**

{2-3 sentence summary of investigation findings and primary conclusion}

---

## Evidence Summary

{Concise summary of key evidence gathered from all data sources}

### {Data Source 1} (e.g., Lab Markers Timeline)

{Table or structured summary of relevant lab findings}

### {Data Source 2} (e.g., Timeline Events)

{Table or structured summary of relevant timeline events}

### {Data Source 3} (e.g., Genetics Findings - if applicable)

{Summary of relevant genetic variants}

---

## Competing Hypotheses

### 🟢 HIGH LIKELIHOOD (80-95%)

#### **Hypothesis 1: {Name}**

**Mechanism**:
{Description of proposed biological pathway}

**Supporting Evidence**:
1. ✅ {Evidence point 1 with data citation}
2. ✅ {Evidence point 2 with data citation}
3. ✅ {Evidence point 3 with data citation}

**Contradictory Evidence**:
1. ⚠️ {Contradiction 1 with explanation if explainable}
2. ❌ {Contradiction 2 if fatal}

**Testable Predictions**:
- {What should be true if this hypothesis is correct}
- {What data would strengthen or weaken this hypothesis}

**Biological Mechanism**:
```
{Step-by-step pathway diagram using text/arrows}
```

**Clinical Likelihood**: **{XX}%**

---

### 🟡 MODERATE LIKELIHOOD (40-60%)

#### **Hypothesis 2: {Name}**

{Same structure as above}

---

### 🔴 LOW LIKELIHOOD (<20%)

#### **Hypothesis 3: {Name}**

{Same structure as above, emphasizing why this is unlikely}

---

## Confounding Factors

### 1. {Confound Name}

**Confound**: {Description}

**Impact**: {How this confound affects hypothesis interpretation}

**Resolution**: {How to discriminate between confound and true cause}

{Repeat for each major confound}

---

## Recommended Follow-Up Investigations

### High Priority (Next 3-6 Months)

1. **{Investigation 1}**: {Description and expected result}
2. **{Investigation 2}**: {Description and expected result}

### Moderate Priority (6-12 Months)

3. **{Investigation 3}**: {Description and expected result}

### Low Priority (Research/Academic Interest)

4. **{Investigation 4}**: {Description and expected result}

---

## Clinical Management Recommendations

### Current Status: **{Assessment}**

1. **{Recommendation 1}**: {Details}
2. **{Recommendation 2}**: {Details}

### Monitoring Plan

- **{Marker/Test 1}**: {Frequency}
- **{Marker/Test 2}**: {Frequency}

---

## Conclusion

**Primary Diagnosis**: **{Conclusion}**

**Clinical Likelihood**: **{XX}%**

**Mechanism**: {1-2 sentence summary of most likely causal pathway}

**Key Supporting Evidence**:
- {Evidence point 1}
- {Evidence point 2}
- {Evidence point 3}

**Key Contradictory Evidence**:
- {Contradiction 1}
- {Contradiction 2}

**Next Steps**:
1. {Action 1}
2. {Action 2}

**Prognosis**: {Brief prognosis statement}

---

## Medical Disclaimer

This hypothesis investigation report is a data-driven analysis based on available laboratory findings, health timeline events, and genetic data. **This is not medical advice and should not be used for clinical decision-making without consultation with a qualified healthcare provider.**

Key limitations:
- Correlation does not imply causation
- Multiple mechanisms may coexist
- Genetics analysis is limited to 23andMe data (does not include comprehensive sequencing)
- Diagnosis relies on available data; clinical correlation required
- Recommendations for follow-up testing should be discussed with appropriate specialists

**Always consult a healthcare provider for clinical interpretation and treatment decisions.**

---

*Investigation completed by health-agent investigate-root-cause skill*
*Generated: {YYYY-MM-DD}*
*Profile: {profile_name}*
```

## Special Considerations

### Genetics Integration (MANDATORY When Configured)

If `genetics_23andme_path` is configured in profile:
- **ALWAYS perform comprehensive genetic analysis** following the Genetics Analysis Protocol
- Include genetics in hypothesis generation (pharmacogenomics, health risks, condition-specific genes)
- Use genetics skills PLUS direct grep commands for condition-relevant genes
- Check ALL relevant genes for the condition (e.g., for bilirubin: UGT1A1, ABCC2, SLCO1B1, G6PD, HFE)
- Cite specific rsIDs and genotypes as supporting evidence
- Report both positive findings AND negative findings (e.g., "Gilbert's ruled out by rs4148323 = GG")
- Note limitations of 23andMe data in disclaimers (common SNPs only, not comprehensive sequencing)
- **NEVER skip genetic analysis or assume SNPs aren't available without checking**

If genetics is NOT configured:
- Investigation works without genetics
- Focus on labs, timeline, and exam data
- Omit genetics sections from output
- Note in limitations section that genetics data was not available

### Evidence Strength Requirements

Different types of evidence have different strengths:

**Direct/Confirmatory Evidence** (strongest):
- Pathognomonic findings (unique to specific condition)
- Genetic confirmation (pathogenic variant identified)
- Tissue diagnosis (biopsy, histology)
- Specialized functional tests

**Indirect/Circumstantial Evidence** (moderate):
- Pattern recognition (constellation of findings fits condition)
- Biomarker abnormalities (consistent with but not diagnostic of condition)
- Response to treatment (improvement with specific therapy)

**Absence of Evidence** (weakest):
- Lack of contradictory findings
- Assumption based on prevalence alone

**Ranking principle**:
- Hypotheses supported by DIRECT evidence can reach HIGH likelihood
- Hypotheses supported only by INDIRECT evidence should be ranked MODERATE unless:
  - Multiple lines of indirect evidence converge
  - AND there's no contradictory evidence
  - AND temporal sequence is correct
- Hypotheses based on ABSENCE of evidence should remain LOW-MODERATE

**Critical**: Strong direct evidence can support ANY hypothesis, common or rare. Do NOT downrank a hypothesis solely because the condition is rare if direct confirmatory evidence exists.

### Primary vs Secondary Phenomena

Distinguish between PRIMARY diseases and SECONDARY effects:

**Primary Phenomenon**: The disease process itself
- Example: ABCC2 mutation (Dubin-Johnson syndrome) - bilirubin elevation IS the disease
- Example: Essential thrombocytosis - platelet elevation IS the disease

**Secondary Phenomenon**: A manifestation of an underlying disease
- Example: Hemolysis - elevated bilirubin FROM red blood cell destruction
- Example: Reactive thrombocytosis - elevated platelets FROM inflammation or iron deficiency

**How to identify secondary phenomena**:
1. Look for upstream markers (e.g., reticulocytes for hemolysis, CRP for inflammation)
2. Check if the phenomenon resolves when upstream process is treated
3. Ask: "What's producing this abnormality?"

**Investigation approach**:
- If secondary phenomenon identified → Generate hypotheses for the underlying cause
- If primary disease suspected → Look for confirmatory evidence
- If uncertain → Generate hypotheses for BOTH possibilities

**Critical**: Do NOT assume all findings are primary diseases. Check for upstream drivers.

**Example**: Elevated bilirubin with elevated reticulocytes → Hemolysis is secondary phenomenon → Investigate: What's causing hemolysis? (hereditary spherocytosis, G6PD, thalassemia, autoimmune, etc.)

### Evidence Weighing Guidance

When evaluating contradictory evidence, weigh by:

**Quantity**: How many measurements support vs contradict?
- 50+ elevated reticulocytes + 1 normal LDH → Hypothesis still strong
- Pattern consistency matters more than single outliers

**Quality**: How reliable/specific is each measurement?
- Gold standard tests (biopsy, genetics) > biomarkers > screening tests
- Measurements during relevant clinical state > measurements at random times

**Temporal relevance**: When was the measurement taken?
- Recent measurements > old measurements for current state
- Chronic pattern (years) > acute variation (single time point)

**Clinical context**: Was the measurement appropriate for testing the hypothesis?
- LDH during acute hemolytic crisis > LDH during compensated state
- Fasting glucose for diabetes > random glucose

**Principle**: Consider the TOTALITY of evidence, not just individual contradictions. A single contradictory measurement should not override consistent chronic findings unless that measurement is:
1. A gold standard confirmatory test, OR
2. Taken during the clinically relevant state, OR
3. Part of a pattern of contradictions (not an isolated outlier)

### Medical Disclaimers (REQUIRED)

Every hypothesis investigation report MUST include:
- "This is not medical advice"
- "Correlation does not imply causation"
- "Multiple mechanisms may coexist"
- "Genetics analysis limited to 23andMe data" (if genetics used)
- "Consult healthcare provider for clinical interpretation"

### Time Windows for Different Mechanisms

Adjust search windows based on mechanism type:
- **Acute stress response**: Minutes to hours
- **Inflammatory response**: Hours to days
- **Medication effects**: Days to weeks
- **Metabolic adaptation**: Days to weeks
- **Chronic condition development**: Weeks to months

### Hypothesis Ranking Guidelines

**HIGH LIKELIHOOD (80-95%)**:
- >80% of instances support hypothesis
- <10% contradictions (and explainable)
- Well-established biological mechanism
- Correct temporal sequence
- No fatal contradictions

**MODERATE LIKELIHOOD (40-60%)**:
- 60-80% of instances support hypothesis
- 10-30% contradictions (some explainable)
- Plausible biological mechanism
- Mostly correct temporal sequence
- Confounds may explain some contradictions

**LOW LIKELIHOOD (<20%)**:
- <40% of instances support hypothesis
- >50% contradictions
- Speculative or unclear mechanism
- Temporal violations present
- Fatal contradictions exist

### Iteration and Refinement

If initial hypotheses are weak:
1. Generate alternative explanations
2. Broaden search to include overlooked factors
3. Consider interaction effects (multiple causes)
4. Revisit data for missed patterns
5. Propose novel mechanisms if standard explanations fail

Aim for at least 3 distinct hypotheses to ensure comprehensive investigation.

### Data Citations

All evidence MUST include data citations:
- **Labs**: "{labs_path}/all.csv: {date}, {marker} = {value} {unit}"
- **Timeline**: "{health_log_path}/health_log.csv: {date}, {event}"
- **Exams**: "{exams_path}/{exam_type}/{date}: {finding}"
- **Genetics**: "{genetics_23andme_path}: {rsID} = {genotype}"

### Efficient Data Access

Large data files exceed Claude's read limits. Agent should use extraction commands from individual skills:
- Labs: `grep -iE "(marker1|marker2)" "{labs_path}/all.csv" | sort -t',' -k1`
- Timeline: `awk -F',' -v start="{start}" -v end="{end}" '$1 >= start && $1 <= end' "{health_log_path}/health_log.csv"`
- Genetics: `grep -E "^(rs123|rs456)" "{genetics_23andme_path}"`

Never read large files directly. Always use filtered extraction.

### Sandbox Compliance

**Directory Creation**: Use Bash `mkdir -p .output/{profile}/sections`
**File Writing**: Use Write tool (NOT bash heredocs or redirects)

Bash heredocs fail in sandbox mode. Always use Write tool for report generation.

## Example Invocations

**User**: "Investigate root cause of my recurring headaches"

**Assistant Process**:
1. Load profile and extract data source paths
2. Spawn Task agent with investigation prompt specifying "recurring headaches"
3. Agent uses episode-investigation to gather headache events
4. Agent uses cross-temporal-correlation to find patterns (poor sleep, stress, caffeine)
5. Agent uses mechanism-search to propose biological pathways
6. Agent uses confound-identification to check for confounds (caffeine changes during poor sleep)
7. Agent uses evidence-contradiction-check to test hypotheses
8. Agent ranks hypotheses: HIGH (sleep deprivation), MODERATE (caffeine withdrawal), LOW (stress)
9. Agent generates report saved to `.output/{profile}/sections/hypothesis-investigation-headaches-{date}.md`

---

**User**: "Why do I have elevated liver enzymes?"

**Assistant Process**:
1. Load profile and extract data source paths
2. Spawn Task agent with investigation prompt specifying "elevated liver enzymes"
3. Agent uses lab-trend to track AST/ALT over time
4. Agent uses medication-supplements to identify hepatotoxic medications
5. Agent uses health-summary to check for liver disease risk factors
6. Agent uses genetics-pharmacogenomics (if configured) to check CYP variants
7. Agent proposes hypotheses: medication-induced, NAFLD, alcohol, viral hepatitis
8. Agent tests each hypothesis and ranks by evidence
9. Agent generates comprehensive report with follow-up recommendations

---

**User**: "Find the cause of my chronic fatigue"

**Assistant Process**:
1. Load profile and extract data source paths
2. Spawn Task agent with investigation prompt specifying "chronic fatigue"
3. Agent uses episode-investigation to gather fatigue timeline
4. Agent uses out-of-range-labs to check thyroid, iron, vitamin B12, cortisol
5. Agent uses cross-temporal-correlation to find temporal associations
6. Agent proposes hypotheses: hypothyroidism, anemia, sleep apnea, chronic infection
7. Agent uses evidence-contradiction-check and confound-identification
8. Agent ranks hypotheses and proposes discriminating tests
9. Agent generates report with clinical management recommendations

---

**User**: "What's causing my abnormal labs?" (vague query)

**Assistant Response**: "I'd be happy to investigate the root cause of your abnormal labs. Could you specify which lab markers are abnormal? For example: 'elevated liver enzymes', 'low hemoglobin', 'high cholesterol', etc. This will help me focus the investigation."

{If user clarifies, then spawn agent with specific condition}
