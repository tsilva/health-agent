---
name: prepare-provider-visit
description: "Intelligently orchestrate provider visit documentation by gathering relevant health data and generating coherent provider-appropriate narratives. Use when user asks to 'prepare for doctor visit', 'generate provider summary', 'create medical summary', or needs documentation for healthcare appointments."
---

# Prepare Provider Visit

Generate comprehensive, coherent provider documentation by intelligently selecting and presenting relevant health data based on visit type and context.

## When to Use This Skill

Trigger when user asks:
- "Prepare a summary for my doctor"
- "Generate documentation for my appointment"
- "Create a provider visit summary"
- "I have a doctor's appointment, what should I bring?"
- "Summarize my health for my specialist"

## Workflow

### Step 1: Gather Context (Minimal Questions)

Ask the user for essential context:

1. **Visit type**: Annual physical / Specialist consult / Follow-up / Urgent care
2. **Specific concerns** (optional): Any particular issues to highlight?
3. **For follow-ups only**: Date of last visit (to determine "since last visit" timeframe)

Use the AskUserQuestion tool with clear options for visit type.

### Step 2: Determine Content Strategy (Smart Defaults)

Based on visit type, automatically determine what to include:

**Annual Physical**:
- Time period: Last 12 months
- Include: Current medications, recent health events, abnormal labs, active conditions
- Include genetics: Only if `genetics_23andme_path` is configured AND relevant findings exist
- Tone: Comprehensive overview

**Specialist Consult**:
- Time period: Last 6 months (focus on specialty-relevant recent changes)
- Include: Medications (specialty-relevant), recent events (related to specialty), targeted labs
- Include genetics: Only if relevant to specialty (e.g., cardiology → APOE, Factor V)
- Tone: Focused on specialist's domain

**Follow-up Visit**:
- Time period: Since last visit date (user provides)
- Include: Changes since last visit, monitored markers, new events, medication adjustments
- Include genetics: Only if new interpretation or relevant to follow-up reason
- Tone: Delta-focused (what changed)

**Urgent Care**:
- Time period: Last 3-6 months (recent context only)
- Include: Chief complaint details, recent relevant events, pertinent labs
- Include genetics: Rarely (only if directly relevant to acute issue)
- Tone: Focused on presenting problem

### Step 3: Gather Data

For each content area, gather data naturally (NOT by invoking deleted skills):

**Current Medications & Supplements**:
```bash
# Extract active medications and supplements
grep -E ",medication,|,supplement," "{health_log_path}/health_log.csv" | \
  awk -F',' '{print $1","$3","$5","$6}' | \
  tail -50  # Recent 50 entries
```

Then apply status determination logic from `.claude/skills/health-agent/references/status-keywords.md` to identify:
- Active (currently taking)
- Discontinued (explicitly stopped)
- Suspected (temporary/as-needed)

**Recent Health Events**:
```bash
# Events in timeframe
awk -F',' -v start="YYYY-MM-DD" 'NR==1 || $1 >= start' "{health_log_path}/health_log.csv"
```

Group by category and episode_id for coherent presentation.

**Abnormal Labs**:
```bash
# Out-of-range labs in timeframe
awk -F',' -v start="YYYY-MM-DD" 'NR==1 || ($1 >= start && ($5 > $7 || $5 < $6))' "{labs_path}/all.csv"
```

Use lab_specs.json (via helpers in `.claude/skills/health-agent/references/lab-specs-helpers.sh`) for canonical names if available.

**Active Conditions**:
```bash
# Extract conditions
grep ",condition," "{health_log_path}/health_log.csv" | \
  awk -F',' '{print $1","$3","$5","$6}'
```

Apply status keywords to determine active vs resolved.

**Genetics** (ONLY if `genetics_23andme_path` is configured):

For specialist visits or when relevant, use `genetics-snp-lookup` skill to check:
- Pharmacogenomics (if new medications discussed)
- Relevant health risks (e.g., cardiology → APOE, Factor V)

**Do NOT include comprehensive genetics reports** unless specifically relevant to visit purpose.

### Step 4: Generate Coherent Narrative

**CRITICAL**: Generate a NARRATIVE, not concatenated sections.

Use this structure:

```markdown
---
document_type: provider_visit_summary
visit_type: {annual|specialist|follow_up|urgent}
generated: {YYYY-MM-DD}
profile: {profile_name}
timeframe: {description of time period covered}
---

# Provider Visit Summary
**Patient**: {profile_name}
**Visit Type**: {visit_type}
**Generated**: {YYYY-MM-DD}
**Timeframe**: {description}

## Visit Context

{2-3 sentences describing reason for visit, any specific concerns, and overall health status}

## Current Medications & Supplements

{Narrative intro: "Currently taking the following medications:"}

| Medication/Supplement | Dosage/Frequency | Started | Status |
|----------------------|------------------|---------|--------|
| ... | ... | ... | Active |

{Brief commentary on recent changes, if any}

## Recent Health Events

{Narrative intro describing event categories and any patterns}

**[Category Name]** ({count} events):
- {Date}: {Event} - {Brief detail}
- {Date}: {Event} - {Brief detail}

{Narrative synthesis: "Notable patterns include..." or "No concerning patterns identified"}

## Laboratory Results

{Narrative intro describing lab monitoring and any trends}

**Abnormal Values**:

| Date | Test | Value | Reference Range | Status |
|------|------|-------|-----------------|--------|
| ... | ... | ... | ... | High/Low |

{Brief interpretation: "HbA1c trending upward, may warrant discussion of medication adjustment"}

## Active Medical Conditions

{If none: "No active chronic conditions documented in health log."}
{If present: Bulleted list with onset dates and current status}

- **{Condition}** (since {date}): {Brief status note}

{FOR SPECIALIST/RELEVANT VISITS ONLY}
## Relevant Genetic Findings

{ONLY include if genetics configured AND directly relevant to visit}

{Brief narrative on findings relevant to visit purpose}

## Summary & Considerations

{2-4 bullet points synthesizing key discussion points for provider:}
- {Synthesis point 1}
- {Synthesis point 2}
- {Potential discussion topic}

---
*This summary was generated by health-agent to support clinical decision-making. All data is patient-reported or extracted from personal health records. Please verify critical information.*
```

### Step 5: Save Output

Save the generated document to:
```
.output/{profile}/provider-visit-{visit_type}-{YYYY-MM-DD}.md
```

Use the `Write` tool (NOT Bash heredocs - they fail in sandbox mode).

Before writing, ensure directory exists:
```bash
mkdir -p .output/{profile}
```

### Step 6: Confirm Completion

Tell the user:
```
Provider visit summary generated and saved to:
.output/{profile}/provider-visit-{visit_type}-{YYYY-MM-DD}.md

The summary includes:
- {List of sections included}
- Covers timeframe: {timeframe description}

You can review, edit, or print this document for your appointment.
```

## Key Principles

1. **Smart Defaults**: Visit type determines everything - don't over-question the user
2. **Coherent Narrative**: Write connected prose, not isolated sections
3. **Provider-Appropriate Tone**: Professional medical documentation style
4. **Selective Genetics**: Only include if configured AND relevant - avoid overwhelming providers
5. **Data Citations**: Include dates and source references for verifiability
6. **Actionable Synthesis**: End with discussion points, not just data dumps

## Efficient Data Access

All data files are large (>256KB). Use filtered extraction commands (shown above) rather than direct reads.

If `{labs_path}/lab_specs.json` exists, use helper functions for canonical marker names:
```bash
source .claude/skills/health-agent/references/lab-specs-helpers.sh
canonical_name=$(get_canonical_name "{labs_path}/lab_specs.json" "HbA1c")
pattern=$(build_grep_pattern "{labs_path}/lab_specs.json" "HbA1c")
```

## Error Handling

- If genetics_23andme_path not configured: Skip genetics section entirely
- If no abnormal labs in timeframe: Note "All recent labs within reference ranges"
- If no recent events: Note "No significant health events documented in timeframe"
- If data source missing: Note in output which sources were unavailable

## Example User Interaction

**User**: "I have my annual physical next week, can you prepare a summary?"

**Assistant**:
1. Uses AskUserQuestion: "What date range should I cover? (Last 12 months / Last 6 months / Custom)"
2. Gathers all relevant data sources
3. Applies status determination to medications/conditions
4. Checks for abnormal labs
5. Reviews recent health events and groups by category
6. IF genetics configured: Checks for relevant findings
7. Generates coherent narrative document
8. Saves to `.output/{profile}/provider-visit-annual-2026-01-21.md`
9. Confirms completion with summary of included sections

**What NOT to do**:
- ❌ Don't invoke deleted skills like `report-medication-list` (they don't exist)
- ❌ Don't generate separate section files then concatenate (not coherent)
- ❌ Don't include genetics by default (only when relevant)
- ❌ Don't ask excessive questions (smart defaults based on visit type)
- ❌ Don't use Bash heredocs for file writing (use Write tool)

## Integration with Other Skills

- **genetics-snp-lookup**: Call directly when genetics relevant to visit
- **scientific-literature-search**: Generally NOT needed for provider summaries (use for investigations only)
- **investigate-root-cause**: If user mentions specific health concern, suggest running investigation separately before visit

Provider visit summaries are for DATA PRESENTATION, not hypothesis generation.
