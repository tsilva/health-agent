# Common Analysis Patterns

This document provides query patterns for common health data analysis tasks. These patterns can be combined and adapted based on user questions.

## Tracking Lab Trends Over Time

When user asks to track a marker (e.g., "How has my HbA1c changed?"):

```bash
# 1. Get canonical name and build pattern (if lab_specs.json exists)
source .claude/skills/health-agent/references/lab-specs-helpers.sh
pattern=$(build_grep_pattern "{labs_path}/lab_specs.json" "HbA1c")

# 2. Extract all measurements for this marker
head -1 "{labs_path}/all.csv" && grep -iE "$pattern" "{labs_path}/all.csv" | sort -t',' -k1

# 3. Analyze the results:
# - Calculate min/max/mean values
# - Identify trend direction (compare first 3 to last 3 measurements)
# - Flag out-of-range values (value > reference_max or value < reference_min)
# - Note low confidence scores (< 0.8)
# - Calculate rate of change if appropriate
```

**If lab_specs.json doesn't exist**, use case-insensitive grep:
```bash
head -1 "{labs_path}/all.csv" && grep -i "hba1c" "{labs_path}/all.csv" | sort -t',' -k1
```

## Finding Abnormal Lab Values

When user asks about abnormal labs (e.g., "What labs are out of range?"):

```bash
# All abnormal values in last 12 months
awk -F',' -v start="$(date -v-12m +%Y-%m-%d)" \
  'NR==1 || ($1 >= start && ($5 > $7 || $5 < $6))' \
  "{labs_path}/all.csv"

# Or for specific timeframe
awk -F',' 'NR==1 || ($1 >= "2025-01-01" && ($5 > $7 || $5 < $6))' \
  "{labs_path}/all.csv"
```

**Analysis approach**:
1. Group by marker name (use canonical names if lab_specs.json exists)
2. For each abnormal value:
   - Note direction (High/Low)
   - Check severity (how far from reference range)
   - Look for trends (improving/worsening over time)
   - Consider clinical significance

## Investigating Health Episodes

When user asks about a specific episode (e.g., "Tell me about my headache episode"):

```bash
# 1. Find episode by searching history.csv
grep -i "headache" "{health_log_path}/history.csv" | head -20

# 2. Extract all events from identified EntityID
grep ",entity_042," "{health_log_path}/history.csv"

# 3. Get entity details from entities.json
grep -A 20 "entity_042" "{health_log_path}/entities.json"

# 4. Get narrative context from health_log.md
grep -A10 -B10 "entity_042\|headache" "{health_log_path}/health_log.md"

# 5. Find temporally related labs (within episode date range)
awk -F',' -v start="2025-10-15" -v end="2025-10-20" \
  'NR==1 || ($1 >= start && $1 <= end)' \
  "{labs_path}/all.csv"
```

**Synthesis approach**:
- Group events by Type column (symptoms, treatments, outcomes)
- Use EntityID to track related events
- Check RelatedEntity column for linked entities
- Identify temporal sequence
- Note what worked/didn't work
- Look for patterns across similar episodes

## Listing Current Medications & Supplements

When user asks about medications (e.g., "What am I currently taking?"):

**Preferred: Use current.yaml (source of truth for current state)**:
```bash
# Get current medications directly from current.yaml
grep -A 100 "^medications:" "{health_log_path}/current.yaml" | grep -B 100 -m 1 "^[a-z]" | head -n -1

# Get current supplements
grep -A 100 "^supplements:" "{health_log_path}/current.yaml" | grep -B 100 -m 1 "^[a-z]" | head -n -1
```

**Alternative: Use history.csv (for timeline analysis)**:
```bash
# Extract medication and supplement events from history
grep -E ",medication,|,supplement," "{health_log_path}/history.csv" | \
  awk -F',' '{print $1","$2","$3","$4","$5","$6}' | \
  tail -100  # Recent entries
```

**Status determination** (use `.claude/skills/health-agent/references/status-keywords.md`):

1. **Active**: Listed in current.yaml, or latest mention in history.csv has active keywords ("taking", "continuing", "started", "prescribed")
2. **Discontinued**: Not in current.yaml, and latest mention has stop keywords ("discontinued", "stopped", "ended")
3. **As-needed**: Mentioned with PRN keywords ("as needed", "when", "if")

**Analysis approach**:
- First check current.yaml for definitive current state
- Use history.csv for timeline and change tracking
- Group by EntityID in history.csv
- Note start dates and dosages
- Flag potential interactions or duplicates

## Cataloging Medical Exams

When user asks about exams (e.g., "What imaging have I had?"):

```bash
# List all exam summaries
find "{exams_path}" -name "*.summary.md" | sort

# Filter by type (after reading frontmatter)
for file in $(find "{exams_path}" -name "*.summary.md"); do
  exam_type=$(grep "^exam_type:" "$file" | cut -d'"' -f2)
  exam_date=$(grep "^exam_date:" "$file" | cut -d'"' -f2)
  echo "$exam_date,$exam_type,$file"
done | sort -t',' -k1 -r
```

**Analysis approach**:
- Group by body region or exam type
- Note temporal progression (follow-up exams)
- Identify significant findings
- Cross-reference with symptoms/labs from similar dates

## Generating Health Summaries

When user asks for overall health summary:

**Systematic approach**:

1. **Demographics**: Extract from profile YAML (age, gender)

2. **Active Conditions** (prefer current.yaml):
```bash
# From current.yaml (source of truth)
grep -A 100 "^conditions:" "{health_log_path}/current.yaml" | grep -B 100 -m 1 "^[a-z]" | head -n -1

# Or from history.csv for timeline analysis
grep ",condition," "{health_log_path}/history.csv" | tail -50
```
Use current.yaml for definitive current state; history.csv for timeline analysis.

3. **Current Medications**: Use pattern above

4. **Recent Labs** (last 6-12 months):
```bash
awk -F',' -v start="$(date -v-12m +%Y-%m-%d)" 'NR==1 || $1 >= start' \
  "{labs_path}/all.csv" | head -100
```

5. **Recent Health Events**:
```bash
awk -F',' -v start="$(date -v-6m +%Y-%m-%d)" 'NR==1 || $1 >= start' \
  "{health_log_path}/history.csv"
```

6. **Recent Exams**: Use catalog pattern above

7. **Genetics** (if configured): Key findings from pharmacogenomics and health risks

**Synthesis**: Create narrative connecting findings across sources.

## Finding Temporal Correlations

When user asks about patterns (e.g., "Does X correlate with Y?"):

**Systematic approach**:

1. **Extract both variables across same timeframe**:
```bash
# Variable 1 (e.g., stress events)
grep -i "stress" "{health_log_path}/history.csv"

# Variable 2 (e.g., blood pressure)
grep -i "blood pressure" "{labs_path}/all.csv"
```

2. **Temporal analysis**:
   - Look for clustering (events occur together)
   - Check time windows (X precedes Y by consistent interval)
   - Assess frequency (how often they co-occur)
   - Identify dose-response (stronger X → stronger Y)

3. **Confound identification**:
   - List alternative explanations
   - Check for common causes
   - Consider temporal sequence (correlation vs causation)
   - Look for contradictory instances

4. **Biological plausibility**:
   - Propose mechanisms linking observations
   - Check for intermediate biomarkers
   - Assess strength of evidence (high/moderate/low)
   - Use `scientific-literature-search` skill for authoritative citations (read `.claude/skills/health-agent/scientific-literature-search/SKILL.md` first)

## Understanding Biological Mechanisms

When user asks "what's the connection between X and Y?" or "why does X cause Y?":

**Reasoning approach**:

1. **Classify observation types**: lab value, symptom, event, condition
2. **Propose known pathways**: Based on medical knowledge
3. **Check for intermediate markers**: Are there measurable steps between X and Y?
4. **Verify temporal sequence**: Does X consistently precede Y?
5. **Assess plausibility**: High (well-established) / Moderate (plausible) / Low (speculative)

**IMPORTANT**: Always use the `scientific-literature-search` skill to find authoritative citations for proposed mechanisms. Read `.claude/skills/health-agent/scientific-literature-search/SKILL.md` and follow its instructions to query PubMed/Semantic Scholar.

Example query: "Find papers on the mechanism linking chronic stress to elevated cortisol"

## Cross-Source Integration

When analyzing any health concern, systematically check all data sources:

**Standard workflow**:
```
1. Current State (current.yaml) - Start here for current state
   - Check conditions, medications, supplements, experiments
   - This is the source of truth for "what's active now"

2. Health Timeline (history.csv) - For historical context
   - Search by Type column for relevant events
   - Use EntityID to track related events
   - Check RelatedEntity for linked items

3. Entity Registry (entities.json)
   - Look up EntityID for metadata
   - Find relationships between entities

4. Health Narrative (health_log.md)
   - Get detailed context around dates
   - Find subjective descriptions

5. Labs (all.csv)
   - Find relevant markers near event dates
   - Check for abnormalities

6. Exams (*/summary.md)
   - Search for related findings
   - Note imaging results

7. Genetics (if configured)
   - Check relevant SNPs via genetics-snp-lookup skill (read `.claude/skills/health-agent/genetics-snp-lookup/SKILL.md` first)
   - Consider pharmacogenomic implications
```

## Generating Provider Documentation

When user needs documentation for healthcare visits, use the **`prepare-provider-visit` skill** instead of manual assembly. Read `.claude/skills/health-agent/prepare-provider-visit/SKILL.md` and follow its instructions.

The skill intelligently selects relevant sections based on visit type (annual/specialist/follow-up/urgent) and generates coherent narratives rather than concatenated fragments.

**When to use the skill**:
- "Prepare summary for my doctor"
- "Generate documentation for my appointment"
- "Create a provider visit summary"

**For custom reports** not covered by the skill, gather data using patterns above and format as markdown with:
- Clear section headers
- Tables for structured data
- Bullet points for narrative
- Data citations (file:line references + dates)
- Medical disclaimers

## Efficient Data Access Notes

All large files (`all.csv`, `history.csv`, `health_log.md`) typically exceed Claude's read limits. Always use:

- **Current state**: Read `current.yaml` directly for medications, conditions, supplements (small file)
- **Filtered extraction**: grep, awk, head/tail commands for history.csv and all.csv
- **Date ranges**: Filter by relevant timeframe first
- **Targeted queries**: Search for specific terms before broad reads
- **Entity lookups**: Use EntityID to get related events from history.csv
- **Incremental reading**: Start narrow, expand if needed

**Never** attempt to read large files entirely - use the extraction patterns above.
