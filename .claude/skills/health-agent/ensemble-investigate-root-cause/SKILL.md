---
name: ensemble-investigate-root-cause
description: High-confidence root cause investigation using 4 parallel agents with different reasoning strategies, mandatory adversarial validation, evidence verification, and blind spot detection. Use when user asks for "high-confidence investigation", "maximum diagnostic accuracy", "ensemble investigation", or when standard investigate-root-cause results are inconclusive.
---

# Ensemble Root Cause Investigation

Maximize diagnostic accuracy through independent reasoning paths, mandatory adversarial validation, evidence verification, and blind spot detection.

## Objective: Maximize Diagnostic Accuracy

Simple consensus can fail if all agents make the same error. This skill incorporates techniques to maximize accuracy:

1. **Independent reasoning paths** - Different starting points reduce correlated errors
2. **Mandatory adversarial validation** - Red team agent actively tries to disprove top hypotheses
3. **Evidence verification** - Verify cited evidence actually exists and supports claims
4. **Blind spot detection** - Identify hypotheses ALL agents may have missed
5. **Calibrated confidence** - Weight by evidence quality, not just agreement count

## Architecture Overview

```
Phase 1: Spawn 4 investigators in parallel (single message)
    ├─ Agent 1: Bottom-Up (data-driven, no preconceptions)
    ├─ Agent 2: Top-Down (differential diagnosis, then seek evidence)
    ├─ Agent 3: Genetics-First (genetic etiology prioritized)
    └─ Agent 4: RED TEAM (actively disprove emerging hypotheses) [MANDATORY]

Phase 2: Wait for all agents to complete

Phase 3: Evidence Verification Agent
    └─ Verify all cited evidence exists and supports claims

Phase 4: Consensus & Blind Spot Agent
    ├─ Merge verified findings
    ├─ Detect hypotheses ALL agents missed
    ├─ Query literature for other known causes
    └─ Produce calibrated final ranking

Phase 5: Return final consensus report path
```

## When to Use This Skill

Use ensemble investigation when:
- User asks for "high-confidence investigation"
- User asks for "maximum diagnostic accuracy"
- User explicitly requests "ensemble" or "parallel" investigation
- Standard `investigate-root-cause` results are inconclusive or conflicting
- Condition is complex with multiple possible etiologies
- High stakes require thorough investigation (treatment decisions)

For routine investigations, use standard `investigate-root-cause` which is faster and sufficient for most cases.

---

## Phase 1: Spawn 4 Investigation Agents

**CRITICAL**: Spawn ALL agents in a SINGLE MESSAGE for parallel execution. Do NOT spawn sequentially.

### Agent Spawning Instructions

Spawn four Task agents in one message:

```
Task tool call 1:
- subagent_type: "general-purpose"
- description: "Bottom-up investigate {condition}"
- prompt: [Agent 1 Bottom-Up Prompt Template]
- run_in_background: true

Task tool call 2:
- subagent_type: "general-purpose"
- description: "Top-down investigate {condition}"
- prompt: [Agent 2 Top-Down Prompt Template]
- run_in_background: true

Task tool call 3:
- subagent_type: "general-purpose"
- description: "Genetics-first investigate {condition}"
- prompt: [Agent 3 Genetics-First Prompt Template]
- run_in_background: true

Task tool call 4:
- subagent_type: "general-purpose"
- description: "Red team attack {condition}"
- prompt: [Agent 4 Red Team Prompt Template]
- run_in_background: true
```

### Why Different Reasoning Strategies?

| Agent | Reasoning Strategy | Why It Improves Accuracy |
|-------|-------------------|--------------------------|
| **Bottom-Up** | Start with raw data, let patterns emerge, form hypotheses from observations | Avoids anchoring bias; finds unexpected connections |
| **Top-Down** | Start with differential diagnosis list, then seek/refute evidence for each | Ensures common causes aren't missed; systematic coverage |
| **Genetics-First** | Comprehensive genetic analysis before other evidence; genetic etiology prioritized | Catches hereditary conditions that explain chronic patterns |
| **RED TEAM** | Given preliminary hypotheses, actively try to DISPROVE them | Catches confirmation bias; finds fatal contradictions |

---

## Agent Prompt Templates

### Common Preamble (Include in All Agent Prompts)

```markdown
**Profile Data Sources**:
- Labs: {labs_path}/all.csv
- Health Timeline: {health_log_path}/health_log.csv
- Health Log Narrative: {health_log_path}/health_log.md
- Medical Exams: {exams_path}/*/*.summary.md
- Genetics (optional): {genetics_23andme_path}

**IMPORTANT - Evidence Citation Format**:

You MUST cite all evidence in this structured format for verification:

## Evidence Citations

| # | Claim | Source | Location | Exact Quote/Value | Interpretation |
|---|-------|--------|----------|-------------------|----------------|
| 1 | "Patient has elevated bilirubin" | all.csv | 2025-03-15 | "bilirubin,2.8,mg/dL" | Supports Hypothesis A |
| 2 | "Reticulocytes consistently elevated" | all.csv | 2024-01 to 2025-12 | "Range: 2.1-3.8%" | Supports Hypothesis B |

This format enables the verification agent to check each claim.

**Data Access Patterns**:
Use efficient extraction commands from CLAUDE.md "Common Analysis Patterns":
- Labs: `grep -iE "(marker1|marker2)" "{labs_path}/all.csv" | sort -t',' -k1`
- Timeline: `grep -i "{term}" "{health_log_path}/health_log.csv" | head -50`
- Genetics: `grep -E "^(rs123|rs456)" "{genetics_23andme_path}"`

**Skills Available**:
- `genetics-snp-lookup` - Read `.claude/skills/health-agent/genetics-snp-lookup/SKILL.md` first
- `scientific-literature-search` - Read `.claude/skills/health-agent/scientific-literature-search/skill.md` first

**Output Location**:
Save report to: `.output/{profile}/ensemble-{condition}-{date}/agent-{strategy}.md`

Create directory first: `mkdir -p .output/{profile}/ensemble-{condition}-{date}`
Use Write tool (NOT bash heredocs) to create report file.
```

---

### Agent 1: Bottom-Up (Data-Driven) Prompt Template

```markdown
Investigate the root cause of {condition} using a BOTTOM-UP data-driven approach.

{Common Preamble}

---

## YOUR STRATEGY: Bottom-Up Investigation

**DO NOT** start with hypotheses. Start with raw data exploration:

### Step 1: Extract ALL Abnormal Findings (No Filtering)

Search ALL data sources without preconceptions:

1. **All abnormal labs** (last 2 years):
   ```bash
   awk -F',' 'NR==1 || ($5 > $7 || $5 < $6)' "{labs_path}/all.csv" | head -100
   ```

2. **All health timeline events related to {condition}**:
   ```bash
   grep -i "{condition}" "{health_log_path}/health_log.csv" | head -50
   ```

3. **All symptoms and conditions**:
   ```bash
   grep -E ",symptom,|,condition," "{health_log_path}/health_log.csv" | tail -100
   ```

4. **All medications and supplements**:
   ```bash
   grep -E ",medication,|,supplement," "{health_log_path}/health_log.csv" | tail -100
   ```

5. **Medical exam findings**:
   ```bash
   find "{exams_path}" -name "*.summary.md" | xargs grep -l "{relevant_terms}"
   ```

### Step 2: Look for Patterns and Correlations

Analyze the raw data for:
- Temporal clustering (events that occur together)
- Dose-response relationships (stronger X → stronger Y)
- Consistent patterns across time
- Unexpected associations

Let hypotheses EMERGE from data patterns. Do NOT impose expected diagnoses.

### Step 3: Generate Hypotheses from Patterns

Only AFTER finding patterns, propose 3-5 explanations:
- Base each hypothesis on observed data patterns
- Note which specific data points support each hypothesis
- Rank by how strongly data patterns support them

### Step 4: Test Hypotheses Against Data

For each hypothesis:
- Search for contradicting evidence
- Identify confounding factors
- Assess temporal sequence
- Query scientific literature for mechanisms

### Step 5: Genetics Analysis (If Configured)

If genetics data is available:
- Read `.claude/skills/health-agent/genetics-snp-lookup/SKILL.md`
- Query condition-relevant genes
- Include both positive AND negative genetic findings

### Step 6: Literature Validation

For each proposed mechanism:
- Read `.claude/skills/health-agent/scientific-literature-search/skill.md`
- Query PubMed/Semantic Scholar for biological pathways
- Include PMIDs in your mechanism descriptions

---

## Output Format

```markdown
---
agent: bottom-up
condition: {condition}
generated: {YYYY-MM-DD}
profile: {profile}
---

# Bottom-Up Investigation: {Condition}

## Strategy
Data-driven approach: Extract all abnormal findings, identify patterns, let hypotheses emerge.

## Raw Data Findings

### Abnormal Lab Values
[Table of all abnormal labs found]

### Timeline Events
[Table of relevant events]

### Patterns Identified
1. **Pattern A**: [Description with data citations]
2. **Pattern B**: [Description with data citations]

## Evidence Citations
[Required structured citation table - see format above]

## Hypotheses (Emerged from Data)

### Hypothesis 1: {Name}
**Data Pattern Supporting This**: [Description]
**Mechanism**: [Biological pathway with literature citations]
**Likelihood**: HIGH/MODERATE/LOW ({XX}%)

### Hypothesis 2: {Name}
[Same structure]

### Hypothesis 3: {Name}
[Same structure]

## Contradictions Found
[List any evidence that contradicts proposed hypotheses]

## Genetic Findings
[If genetics configured, include all checked SNPs with results]

## Confidence Assessment
- Primary Hypothesis: {name} - {likelihood}
- Confidence Basis: [What data patterns support this confidence]
```

**AVOID**: Anchoring on obvious diagnoses. The goal is to find what the data shows, not confirm what you expect.
```

---

### Agent 2: Top-Down (Differential Diagnosis) Prompt Template

```markdown
Investigate the root cause of {condition} using a TOP-DOWN differential diagnosis approach.

{Common Preamble}

---

## YOUR STRATEGY: Top-Down Differential Diagnosis

Start with systematic differential diagnosis, then seek evidence:

### Step 1: Generate Differential Diagnosis List

Query scientific literature for known causes:
- Read `.claude/skills/health-agent/scientific-literature-search/skill.md`
- Search: "differential diagnosis of {condition}"
- Search: "causes of {condition}"
- List the top 10 known causes of this condition

### Step 2: For EACH Cause, Systematically Search Evidence

For each cause in your differential:

1. **Search for SUPPORTING evidence**:
   - Labs that would confirm this cause
   - Timeline events consistent with this cause
   - Exam findings that support this cause
   - Genetic variants associated with this cause

2. **Search for REFUTING evidence**:
   - Labs that should be abnormal but aren't
   - Timeline inconsistencies
   - Exam findings that contradict this cause
   - Genetic protection factors

3. **Calculate evidence balance**:
   - Supporting evidence count and quality
   - Refuting evidence count and quality
   - Likelihood = Support / (Support + Refutation)

### Step 3: Genetics Analysis (If Configured)

For each differential diagnosis:
- Read `.claude/skills/health-agent/genetics-snp-lookup/SKILL.md`
- Query genes associated with that cause
- Include both positive AND negative findings

### Step 4: Rank by Differential Diagnosis Probability

Combine:
- Base rate (how common is this cause?)
- Evidence support (what data confirms it?)
- Evidence refutation (what data contradicts it?)

Final Likelihood = Base Rate × Evidence Support × (1 - Evidence Refutation)

---

## Output Format

```markdown
---
agent: top-down
condition: {condition}
generated: {YYYY-MM-DD}
profile: {profile}
---

# Top-Down Differential Diagnosis: {Condition}

## Strategy
Systematic differential diagnosis: List known causes, then seek/refute evidence for each.

## Differential Diagnosis List (from Literature)

1. {Cause 1} - Base rate: {X}%
2. {Cause 2} - Base rate: {X}%
3. {Cause 3} - Base rate: {X}%
...
10. {Cause 10} - Base rate: {X}%

**Literature Source**: [PMID citations for differential diagnosis]

## Evidence Citations
[Required structured citation table - see format above]

## Systematic Evidence Review

### 1. {Cause 1}

**Supporting Evidence**:
- ✅ [Evidence with citation]
- ✅ [Evidence with citation]

**Refuting Evidence**:
- ❌ [Evidence with citation]

**Genetic Findings**:
- [SNP results if relevant]

**Likelihood**: {XX}% (Base rate × Support × (1 - Refutation))

---

### 2. {Cause 2}
[Same structure]

---

[Continue for all differential diagnoses]

## Final Ranking

| Rank | Cause | Base Rate | Support | Refutation | Final Likelihood |
|------|-------|-----------|---------|------------|------------------|
| 1 | {Name} | X% | Y% | Z% | {Final}% |
| 2 | {Name} | X% | Y% | Z% | {Final}% |

## Causes Ruled Out
[List causes with strong refuting evidence]

## Confidence Assessment
- Primary Diagnosis: {name} - {likelihood}%
- Confidence Basis: [Systematic evidence review supports this]
```

**GOAL**: Ensure common causes aren't missed. Systematic coverage over insight.
```

---

### Agent 3: Genetics-First Prompt Template

```markdown
Investigate the root cause of {condition} using a GENETICS-FIRST approach.

{Common Preamble}

---

## YOUR STRATEGY: Genetics-First Investigation

Prioritize genetic etiology before other explanations:

### Step 1: Identify ALL Genes Associated with {Condition}

1. Read `.claude/skills/health-agent/genetics-snp-lookup/SKILL.md`
2. Query SNPedia for condition-associated genes:
   - Search: "{condition}" to find relevant genes
   - Search: specific gene names known to cause {condition}
3. Create comprehensive list of genes to check

### Step 2: Check EVERY Relevant Gene in 23andMe Data

For each identified gene:
- Query all relevant SNPs
- Document genotype and interpretation
- Note any pathogenic or risk variants
- Note protective variants

**Do NOT skip genes or assume SNPs aren't available without checking.**

### Step 3: Genetic Etiology Assessment

If positive genetic findings:
- Make genetics your PRIMARY hypothesis
- Assess penetrance (does genotype always cause phenotype?)
- Check if genetic findings explain observed phenotype
- Look for gene-environment interactions

If negative genetic findings:
- Document which genes were checked and ruled out
- Note limitations of 23andMe coverage
- Proceed to environmental/acquired causes

### Step 4: Secondary Evidence Gathering

Only AFTER genetic analysis, consider:
- Lab trends that support/refute genetic hypothesis
- Timeline events consistent with genetic etiology
- Environmental factors that might modify genetic risk

### Step 5: Pharmacogenomics Consideration

Check if {condition} is related to medication response:
- Query CYP2D6, CYP2C19, CYP2C9, VKORC1, SLCO1B1
- Check if current medications might be causing or worsening {condition}

---

## Output Format

```markdown
---
agent: genetics-first
condition: {condition}
generated: {YYYY-MM-DD}
profile: {profile}
---

# Genetics-First Investigation: {Condition}

## Strategy
Comprehensive genetic analysis before other explanations. Genetic etiology prioritized.

## Genetic Analysis (COMPREHENSIVE)

### Genes Associated with {Condition}

| Gene | SNPs Checked | Genotypes | Interpretation |
|------|--------------|-----------|----------------|
| {Gene1} | rs123, rs456 | AA, CT | {Interpretation} |
| {Gene2} | rs789 | GG | {Interpretation} |

### Positive Genetic Findings

**{Gene/Variant}**:
- Genotype: {X}
- Clinical Significance: {Description}
- Penetrance: {X}%
- Supports {condition} etiology: YES/NO

### Negative Genetic Findings (Ruled Out)

| Gene | SNPs Checked | Result | Condition Ruled Out |
|------|--------------|--------|---------------------|
| {Gene1} | rs123 | Normal | {Associated condition} |

### Genes NOT Available in 23andMe

[List any relevant genes not covered by 23andMe genotyping]

### Pharmacogenomics Findings

[If medication-related, include CYP enzyme status]

## Evidence Citations
[Required structured citation table - see format above]

## Hypotheses (Genetics-Prioritized)

### Hypothesis 1: {Genetic Cause}
**Genetic Evidence**: [Specific variants found]
**Supporting Lab/Clinical Evidence**: [Additional support]
**Likelihood**: HIGH/MODERATE/LOW ({XX}%)

### Hypothesis 2: {Acquired/Environmental Cause}
**Why Genetics Didn't Explain**: [What was checked and negative]
**Alternative Explanation**: [Description]
**Likelihood**: {XX}%

## Genetic Recommendations

If genetic testing gaps exist:
- Recommend clinical genetic testing for {genes}
- Note: 23andMe covers ~631k SNPs, may miss rare variants

## Confidence Assessment
- Primary Hypothesis: {name} - {likelihood}%
- Genetic Confidence: [Based on coverage and findings]
```

**RATIONALE**: Genetic causes explain chronic, persistent patterns better than environmental factors. If there's a genetic explanation, it should be top-ranked.
```

---

### Agent 4: RED TEAM (Adversarial Validation) Prompt Template

```markdown
Perform RED TEAM adversarial validation for hypotheses about {condition}.

{Common Preamble}

---

## YOUR STRATEGY: Red Team / Devil's Advocate

Your job is to DISPROVE the likely hypotheses, NOT support them.

### Step 1: Identify Likely Hypotheses

Based on {condition}, the most commonly proposed hypotheses are typically:
- {Common hypothesis 1 for this condition}
- {Common hypothesis 2 for this condition}
- {Common hypothesis 3 for this condition}

Your goal: Try to DESTROY each one.

### Step 2: For Each Hypothesis, Attack Systematically

For each plausible hypothesis:

1. **Search for CONTRADICTING evidence**:
   - Labs that should be abnormal but are normal
   - Labs that should be normal but are abnormal
   - Timeline events that don't fit the hypothesis
   - Exam findings that contradict

2. **Find TEMPORAL violations**:
   - Did the proposed effect appear BEFORE the proposed cause?
   - Is the time course inconsistent with the mechanism?

3. **Identify ALTERNATIVE explanations**:
   - Could the same evidence support a different hypothesis?
   - Is there a simpler explanation?
   - Are there confounding factors?

4. **Check for CHERRY-PICKING**:
   - Did proponents of this hypothesis ignore contradictory data?
   - Are they only citing supportive evidence?

5. **Assess MECHANISM plausibility**:
   - Is the proposed biological pathway well-established?
   - Are there missing intermediate steps?

### Step 3: Rate Hypothesis Survival

For each hypothesis tested:
- **SURVIVED**: No fatal flaws found. Hypothesis is strengthened.
- **WEAKENED**: Minor contradictions found. Hypothesis still possible but less likely.
- **DESTROYED**: Fatal contradiction found. Hypothesis should be abandoned.

### Step 4: Identify What Would Change Your Mind

For each hypothesis that survived:
- What evidence would definitively disprove it?
- What tests could discriminate between competing hypotheses?

---

## Output Format

```markdown
---
agent: red-team
condition: {condition}
generated: {YYYY-MM-DD}
profile: {profile}
---

# Red Team Attack Report: {Condition}

## Strategy
Adversarial validation: Actively try to DISPROVE likely hypotheses. A hypothesis that survives Red Team scrutiny is more likely correct.

## Hypotheses Under Attack

### Attack 1: {Hypothesis Name}

**Hypothesis Statement**: {Description}

**Contradictions Found**:
| # | Contradiction | Source | Impact |
|---|---------------|--------|--------|
| 1 | {Evidence that contradicts} | {Source:date} | FATAL/MINOR |
| 2 | {Evidence that contradicts} | {Source:date} | FATAL/MINOR |

**Temporal Violations**:
- {Any cause-effect timing issues}

**Alternative Explanations**:
- {Simpler or equally valid alternatives}

**Cherry-Picking Assessment**:
- {Did proponents ignore this contradictory evidence?}

**SURVIVAL RATING**: SURVIVED / WEAKENED / DESTROYED

**Attack Summary**: {Why this hypothesis survived or was destroyed}

---

### Attack 2: {Hypothesis Name}
[Same structure]

---

### Attack 3: {Hypothesis Name}
[Same structure]

## Evidence Citations
[Required structured citation table - see format above]

## Discriminating Tests

To distinguish between surviving hypotheses:

| Test | Expected if Hypothesis A True | Expected if Hypothesis B True |
|------|------------------------------|-------------------------------|
| {Test 1} | {Result A} | {Result B} |
| {Test 2} | {Result A} | {Result B} |

## Red Team Conclusion

**Hypotheses That Survived**:
1. {Name} - Survival confidence: {X}%
2. {Name} - Survival confidence: {X}%

**Hypotheses Destroyed**:
1. {Name} - Fatal flaw: {Description}

**Strongest Hypothesis Post-Attack**: {Name}

**Confidence**: {X}% (based on survival of adversarial testing)
```

**SUCCESS CRITERIA**: A hypothesis that survives Red Team scrutiny is more likely correct. You WANT to find fatal flaws. If you can't, that strengthens the hypothesis.
```

---

## Phase 2: Wait for Agent Completion

After spawning all 4 agents, wait for completion:

```bash
# Check if all output files exist
ls -la .output/{profile}/ensemble-{condition}-{date}/
# Expected: agent-bottomup.md, agent-topdown.md, agent-genetics.md, agent-redteam.md
```

If any agent fails or times out (>15 minutes):
- Note the failure in the consensus report
- Proceed with available agent outputs
- Reduce confidence in final assessment

---

## Phase 3: Evidence Verification Agent

Spawn verification agent AFTER Phase 2 completes:

```
Task tool with:
- subagent_type: "general-purpose"
- description: "Verify evidence citations for {condition}"
- prompt: [Evidence Verification Prompt Template]
```

### Evidence Verification Prompt Template

```markdown
Verify evidence citations from the ensemble investigation of {condition}.

**Input Files**:
- .output/{profile}/ensemble-{condition}-{date}/agent-bottomup.md
- .output/{profile}/ensemble-{condition}-{date}/agent-topdown.md
- .output/{profile}/ensemble-{condition}-{date}/agent-genetics.md
- .output/{profile}/ensemble-{condition}-{date}/agent-redteam.md

**Profile Data Sources**:
- Labs: {labs_path}/all.csv
- Health Timeline: {health_log_path}/health_log.csv
- Genetics: {genetics_23andme_path}

---

## YOUR TASK: Verify All Evidence Citations

### Step 1: Extract All Evidence Citations

Read each agent report and extract the "Evidence Citations" table.

### Step 2: Verify Each Citation

For each citation:

1. **Check file exists**:
   ```bash
   test -f "{source_file}" && echo "EXISTS" || echo "MISSING"
   ```

2. **Check claimed value matches actual data**:
   ```bash
   # For labs
   grep -i "{claimed_marker}" "{labs_path}/all.csv" | grep "{claimed_date}"

   # For timeline
   grep -i "{claimed_event}" "{health_log_path}/health_log.csv" | grep "{claimed_date}"

   # For genetics
   grep "^{rsid}" "{genetics_23andme_path}"
   ```

3. **Verify interpretation is reasonable**:
   - Does the actual value support the claimed interpretation?
   - Is the direction (high/low/normal) correct?

### Step 3: Cherry-Picking Detection

For each hypothesis:
- Search for CONTRADICTORY evidence the agent may have ignored
- Flag hypotheses with unaddressed contradictions

Example:
```bash
# If agent claims "all bilirubin values elevated"
# Check for any normal bilirubin values
grep -i "bilirubin" "{labs_path}/all.csv" | awk -F',' '$5 <= $7 && $5 >= $6'
```

### Step 4: Completeness Check

For each agent, assess:
- What % of relevant data sources did they query?
- Did they check labs? Timeline? Genetics? Exams?
- Flag agents that skipped major data sources

---

## Output Format

Save to: `.output/{profile}/ensemble-{condition}-{date}/evidence-verification.md`

```markdown
---
phase: evidence-verification
condition: {condition}
generated: {YYYY-MM-DD}
---

# Evidence Verification Report

## Citation Verification Results

### Agent: Bottom-Up

| # | Claim | Verified | Actual Value | Status |
|---|-------|----------|--------------|--------|
| 1 | "Bilirubin 2.8" | YES | 2.8 mg/dL | ✓ Verified |
| 2 | "Reticulocytes 3.5%" | NO | 2.1% | ⚠️ Misquoted |
| 3 | "Episode in March" | YES | 2025-03-15 | ✓ Verified |

**Verified**: X/Y citations (Z%)
**Flagged**: [List any misquotes or errors]

---

### Agent: Top-Down

[Same structure]

---

### Agent: Genetics-First

[Same structure]

---

### Agent: Red-Team

[Same structure]

---

## Cherry-Picking Detection

### Hypothesis: {Name}

**Unaddressed Contradictions Found**:
| Evidence | Source | Impact on Hypothesis |
|----------|--------|---------------------|
| {Contradictory finding} | {Source} | WEAKENS/FATAL |

---

## Completeness Scores

| Agent | Labs | Timeline | Genetics | Exams | Overall |
|-------|------|----------|----------|-------|---------|
| Bottom-Up | ✓ | ✓ | ✓ | ✗ | 75% |
| Top-Down | ✓ | ✓ | ✗ | ✓ | 75% |
| Genetics | ✓ | ✗ | ✓ | ✗ | 50% |
| Red-Team | ✓ | ✓ | ✓ | ✓ | 100% |

---

## Verification Summary

**Total Citations**: X
**Verified**: Y (Z%)
**Flagged**: W citations

**High-Confidence Findings**: [List citations all agents agreed on AND verified]
**Questionable Findings**: [List citations with verification issues]
```
```

---

## Phase 4: Consensus & Blind Spot Agent

Spawn consensus agent AFTER Phase 3 completes:

```
Task tool with:
- subagent_type: "general-purpose"
- description: "Generate consensus for {condition}"
- prompt: [Consensus & Blind Spot Prompt Template]
```

### Consensus & Blind Spot Prompt Template

```markdown
Generate calibrated consensus from ensemble investigation of {condition}.

**Input Files**:
- .output/{profile}/ensemble-{condition}-{date}/agent-bottomup.md
- .output/{profile}/ensemble-{condition}-{date}/agent-topdown.md
- .output/{profile}/ensemble-{condition}-{date}/agent-genetics.md
- .output/{profile}/ensemble-{condition}-{date}/agent-redteam.md
- .output/{profile}/ensemble-{condition}-{date}/evidence-verification.md

**Skills Available**:
- Read `.claude/skills/health-agent/scientific-literature-search/skill.md` for blind spot detection

---

## YOUR TASK: Generate Calibrated Consensus

### Step 1: Hypothesis Inventory

List ALL unique hypotheses across all 4 agent reports:

| Hypothesis | Bottom-Up | Top-Down | Genetics | Red-Team |
|------------|-----------|----------|----------|----------|
| {Name 1} | ✓ 80% | ✓ 75% | ✗ | SURVIVED |
| {Name 2} | ✗ | ✓ 40% | ✓ 90% | WEAKENED |

### Step 2: Verified Agreement Scoring

Only count VERIFIED evidence (from evidence-verification.md):

```
Raw Agreement Score = (Agents proposing hypothesis) / 4

Verified Score = Raw Agreement × (Verified citations / Total citations)
```

Example:
- Hypothesis X: 3/4 agents proposed (75% agreement)
- But only 60% of citations verified
- Verified Score = 0.75 × 0.60 = 0.45 (45%)

### Step 3: Contradiction Weighting

Adjust scores based on Red Team results:

```
Contradiction Survival Factor:
- SURVIVED Red Team (no fatal flaws): × 1.0
- WEAKENED by Red Team (minor contradictions): × 0.8
- DESTROYED by Red Team (fatal contradiction): × 0.1
```

### Step 4: Blind Spot Detection (CRITICAL)

Query literature for known causes of {condition} NOT proposed by any agent:

1. Read `.claude/skills/health-agent/scientific-literature-search/skill.md`
2. Search: "causes of {condition}" or "differential diagnosis {condition}"
3. Compare literature causes against proposed hypotheses
4. For EACH known cause NOT investigated:
   - Flag as blind spot
   - Generate brief assessment (could this apply?)
   - Note if worth investigating

### Step 5: Calibrated Confidence Calculation

```
Final Confidence = Base × Agreement × Evidence_Quality × Contradiction_Survival

Evidence Quality Weights:
- Genetics confirmation: 1.0
- Gold standard test: 0.95
- Lab pattern (multiple markers): 0.8
- Single lab value: 0.6
- Timeline correlation only: 0.5
- Inference/speculation: 0.3

Contradiction Survival:
- Survived RED TEAM with no fatal flaws: 1.0
- Minor contradictions addressed: 0.9
- Unaddressed contradictions: 0.5
- Fatal contradiction found: 0.1
```

### Step 6: Generate Final Ranking

Order hypotheses by calibrated confidence with uncertainty ranges.

---

## Output Format

Save to: `.output/{profile}/ensemble-{condition}-{date}/consensus-final.md`

```markdown
---
document_type: ensemble_consensus
condition: {condition}
generated: {YYYY-MM-DD}
profile: {profile}
agents: 4
phases: 5
---

# Ensemble Root Cause Investigation: {Condition}

## Executive Summary

**Primary Hypothesis**: {Name}
**Calibrated Confidence**: {XX}% (±Y%)
**Agreement**: X/4 agents
**Red Team Status**: SURVIVED / WEAKENED

{2-3 sentence summary of investigation findings}

---

## Methodology

This investigation used 4 parallel agents with different reasoning strategies:
1. **Bottom-Up**: Data-driven pattern discovery
2. **Top-Down**: Systematic differential diagnosis
3. **Genetics-First**: Genetic etiology prioritization
4. **Red Team**: Adversarial hypothesis testing

All evidence citations were verified. Blind spot analysis checked for missed causes.

---

## Hypothesis Ranking (Calibrated)

### Rank 1: {Hypothesis Name}

**Calibrated Confidence**: {XX}% (±Y%)

| Metric | Value |
|--------|-------|
| Agent Agreement | X/4 |
| Verified Citations | Y% |
| Evidence Quality | {HIGH/MODERATE/LOW} |
| Red Team Status | SURVIVED/WEAKENED |
| Blind Spot Risk | LOW |

**Calculation**:
```
Base: {X}%
× Agreement (X/4): {Y}%
× Evidence Quality: {Z}%
× Red Team Survival: {W}%
= Final: {XX}%
```

**Supporting Evidence** (verified):
1. ✅ {Evidence 1 with citation}
2. ✅ {Evidence 2 with citation}

**Contradictions** (addressed):
1. ⚠️ {Contradiction 1 - explanation}

**Mechanism** (literature-supported):
{Biological pathway with PMID citations}

---

### Rank 2: {Hypothesis Name}

[Same structure]

---

### Rank 3: {Hypothesis Name}

[Same structure]

---

## Blind Spots Detected

### {Known Cause Not Investigated}

**Why Flagged**: Listed in literature as cause of {condition}, but no agent investigated.

**Quick Assessment**: {Could this apply to this patient? Brief analysis.}

**Recommendation**: {Investigate further / Unlikely / Ruled out by existing evidence}

---

## Unresolved Conflicts

Where agents disagreed:

| Topic | Bottom-Up | Top-Down | Genetics | Red-Team |
|-------|-----------|----------|----------|----------|
| {Issue 1} | {View} | {View} | {View} | {View} |

**Resolution**: {How to resolve this disagreement}

---

## Evidence Quality Assessment

| Evidence Type | Count | Weight | Contribution |
|---------------|-------|--------|--------------|
| Genetics confirmation | X | 1.0 | {XX}% |
| Lab pattern | Y | 0.8 | {YY}% |
| Timeline correlation | Z | 0.5 | {ZZ}% |

---

## Recommended Follow-Up

### High Priority
1. {Test/Investigation 1}: Would confirm/refute primary hypothesis
2. {Test/Investigation 2}: Would resolve blind spot

### Moderate Priority
3. {Test/Investigation 3}: Additional confirmation

---

## Limitations

- Agent agreement ≠ correctness (all agents can make same error)
- 23andMe genetics limited to ~631k SNPs
- Timeline data depends on user's recording accuracy
- Literature search limited to PubMed/Semantic Scholar

---

## Medical Disclaimer

This ensemble investigation is a data-driven analysis using multiple reasoning strategies. **This is not medical advice**.

- Calibrated confidence reflects data support, not diagnostic certainty
- Multiple mechanisms may coexist
- Blind spots may still exist despite detection efforts
- Always consult healthcare provider for clinical decisions

---

*Ensemble investigation completed using 4 parallel agents + verification + consensus*
*Generated: {YYYY-MM-DD}*
*Profile: {profile}*
```
```

---

## Phase 5: Return Final Report Path

After consensus report is generated:

1. Verify all output files exist:
```bash
ls -la .output/{profile}/ensemble-{condition}-{date}/
```

Expected files:
- `agent-bottomup.md`
- `agent-topdown.md`
- `agent-genetics.md`
- `agent-redteam.md`
- `evidence-verification.md`
- `consensus-final.md`

2. Return summary to user:

```markdown
## Ensemble Investigation Complete

**Condition**: {condition}
**Output Directory**: `.output/{profile}/ensemble-{condition}-{date}/`

**Files Generated**:
- 4 agent investigation reports
- Evidence verification report
- Final consensus report

**Primary Hypothesis**: {Name} ({XX}% calibrated confidence)

**Read full consensus**: `.output/{profile}/ensemble-{condition}-{date}/consensus-final.md`
```

---

## Error Handling

| Scenario | Action |
|----------|--------|
| **Agent timeout (>15 min)** | Proceed with available agents; note gap in consensus |
| **Agent fails** | Log error; reduce consensus confidence |
| **No genetics data** | Genetics-first agent adapts; notes limitation |
| **All agents agree on wrong hypothesis** | Blind spot detection queries literature for alternatives |
| **Verification finds >30% citation errors** | Flag low-quality investigation; recommend re-run |
| **No clear consensus** | Report uncertainty; list discriminating tests needed |

---

## Example Invocation

**User**: "Run an ensemble investigation on my chronic hemolysis"

**Assistant Process**:

1. Load profile and extract data source paths

2. Spawn 4 agents in parallel (single message with 4 Task calls):
   - Bottom-Up: Start with all abnormal labs, find hemolysis patterns
   - Top-Down: Differential diagnosis of hemolysis (hereditary vs acquired)
   - Genetics-First: Check spherocytosis genes, G6PD, pyruvate kinase, etc.
   - Red Team: Try to disprove hemolysis hypotheses

3. Wait for all agents to complete (background)

4. Spawn Evidence Verification Agent:
   - Check all lab value citations
   - Verify genetic findings
   - Detect cherry-picking

5. Spawn Consensus Agent:
   - Merge verified findings
   - Calculate calibrated confidence
   - Check blind spots (query literature for other hemolysis causes)
   - Generate final ranking

6. Return:
   ```
   ## Ensemble Investigation Complete

   **Primary Hypothesis**: Hereditary Spherocytosis (85% calibrated confidence)
   - 4/4 agents proposed
   - Survived Red Team
   - Genetics confirmed

   **Output**: .output/{profile}/ensemble-chronic-hemolysis-2026-01-22/consensus-final.md
   ```

---

## Comparison: Standard vs Ensemble Investigation

| Aspect | Standard | Ensemble |
|--------|----------|----------|
| **Agents** | 1 | 4 parallel + 2 sequential |
| **Reasoning paths** | Single | 4 independent strategies |
| **Adversarial testing** | Optional | Mandatory |
| **Evidence verification** | No | Yes |
| **Blind spot detection** | No | Yes |
| **Confidence calibration** | Subjective | Calculated from metrics |
| **Execution time** | ~5-10 min | ~15-20 min |
| **Use case** | Routine investigation | High-stakes, complex cases |

Use standard `investigate-root-cause` for routine cases. Use ensemble for complex cases requiring maximum diagnostic accuracy.
