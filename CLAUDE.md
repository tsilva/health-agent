# Health Agent

A Claude Code-based health analysis agent that ingests data from three parsers and provides analytical capabilities through direct file reads and custom skills.

## Quick Start

At the start of each session, prompt the user to select a profile:

```
Which health profile would you like to use? (Check profiles/ directory for available profiles)
```

Then load the profile YAML to get data source paths.

## Profile System

### Loading a Profile

1. List available profiles: `ls profiles/*.yaml` (exclude `_template.yaml`)
2. Read the selected profile: `profiles/{name}.yaml`
3. Extract data source paths from the YAML
4. Use those paths to access health data throughout the session

### Profile Schema

```yaml
name: "User Name"
demographics:
  date_of_birth: "YYYY-MM-DD"  # For age-based reference ranges
  gender: "male|female"         # For gender-specific reference ranges

data_sources:
  labs_path: "/path/to/labs-parser/output/"
  exams_path: "/path/to/medical-exams-parser/output/"
  health_log_path: "/path/to/health-log-parser/output/"
  genetics_23andme_path: "/path/to/23andme_raw_data.txt"  # Optional
```

## Data Source Schemas

### Labs Data (labs-parser)

**File**: `{labs_path}/all.csv`

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Date of lab test (YYYY-MM-DD) |
| `source_file` | string | Original PDF filename |
| `page_number` | int | Page number in source PDF |
| `lab_name` | string | Name of the test/marker |
| `value` | float | Measured value |
| `unit` | string | Unit of measurement |
| `reference_min` | float | Lower bound of reference range |
| `reference_max` | float | Upper bound of reference range |
| `confidence` | float | OCR confidence score (0-1) |

**Example queries**:
- Track a specific marker over time: filter by `lab_name`
- Find out-of-range values: compare `value` to `reference_min`/`reference_max`
- Review recent labs: sort by `date` descending

### Lab Specifications (labs-parser)

**File**: `{labs_path}/lab_specs.json`

Machine-readable lab marker specifications for accurate matching and unit standardization. This file is **optional** - skills gracefully fall back to manual patterns when it's not present.

**Schema**:
```json
{
  "markers": [
    {
      "canonical_name": "HbA1c",
      "aliases": ["Hemoglobin A1c", "Glycated Hemoglobin", "A1C"],
      "primary_unit": "%",
      "conversion_factors": { "mmol/mol": 10.93 },
      "reference_range": { "min": 4.0, "max": 5.6 }
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `canonical_name` | string | Standardized marker name for consistent reporting |
| `aliases` | array | All alternative names/aliases for the marker |
| `primary_unit` | string | Standard unit of measurement |
| `conversion_factors` | object | Conversion factors from primary unit to alternatives |
| `reference_range` | object | Typical reference range (min/max) |

**Usage**:
- Skills check for this file when performing marker lookups
- Helper functions in `.claude/skills/health-agent/references/lab-specs-helpers.sh` provide:
  - `get_canonical_name()` - Get standard name from any alias
  - `build_grep_pattern()` - Build grep pattern from all aliases
  - `get_primary_unit()` - Get standard unit for marker
  - `get_conversion_factor()` - Convert between units
- If lab_specs.json is missing, skills use case-insensitive fuzzy matching on lab_name values

**Benefits**:
- More accurate marker matching (captures all aliases automatically)
- Consistent naming across reports (all variants display as canonical name)
- Unit standardization for cross-report comparisons
- Easier maintenance (add markers in labs-parser without updating skills)

### Health Timeline (health-log-parser)

**File**: `{health_log_path}/health_log.csv`

| Column | Type | Description |
|--------|------|-------------|
| `Date` | date | Event date (YYYY-MM-DD) |
| `EpisodeID` | string | Links related events (e.g., "episode_001") |
| `Item` | string | Brief item name |
| `Category` | string | Event category (symptom, medication, condition, etc.) |
| `Event` | string | Event description |
| `Details` | string | Additional context |

**Episode IDs**: Events with the same `EpisodeID` are related (e.g., a cold's symptoms, treatment, and resolution).

### Health Log Narrative (health-log-parser)

**File**: `{health_log_path}/health_log.md`

Markdown journal with chronological health entries. Use for:
- Full context around timeline events
- Detailed symptom descriptions
- Treatment responses and outcomes

### Medical Exam Summaries (medical-exams-parser)

**Directory**: `{exams_path}/*/*.summary.md`

Each exam produces a markdown summary with YAML frontmatter:

```markdown
---
exam_type: "ultrasound|mri|ct|xray|etc"
exam_date: "YYYY-MM-DD"
body_region: "abdomen|chest|etc"
provider: "facility name"
---

# Exam Summary

[Structured transcription of findings]
```

**Finding exam files**:
- List all summaries: `find {exams_path} -name "*.summary.md"`
- Filter by type: read frontmatter and check `exam_type`

### 23andMe Genetics Data (optional)

**File**: `{genetics_23andme_path}` (typically `23andme_raw_data.txt`)

Tab-separated file with ~631,000 SNPs:

| Column | Description |
|--------|-------------|
| `rsid` | Reference SNP identifier (e.g., rs12345) |
| `chromosome` | Chromosome number (1-22, X, Y, MT) |
| `position` | Base pair position |
| `genotype` | Unphased genotype (e.g., AG, CC, TT) |

**File format**:
```
# rsid  chromosome  position  genotype
rs12345  1  12345678  AG
```

**Efficient data access** (file is too large to read directly):
```bash
# Single SNP lookup
grep "^rs12345" "{genetics_23andme_path}"

# Multiple SNPs (batch)
grep -E "^(rs123|rs456|rs789)" "{genetics_23andme_path}"
```

**Key variant categories**:
- Pharmacogenomics: Drug metabolism (CYP2D6, CYP2C19, CYP2C9, VKORC1, SLCO1B1)
- Health risks: APOE, Factor V Leiden, HFE hemochromatosis, MTHFR
- Limited BRCA testing: Only 3 Ashkenazi founder mutations

## Common Analysis Patterns

This section provides query patterns for common health data analysis tasks. These patterns can be combined and adapted based on user questions.

### Tracking Lab Trends Over Time

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

### Finding Abnormal Lab Values

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

### Investigating Health Episodes

When user asks about a specific episode (e.g., "Tell me about my headache episode"):

```bash
# 1. Find episode by searching health_log.csv
grep -i "headache" "{health_log_path}/health_log.csv" | head -20

# 2. Extract all events from identified episode_id
grep ",episode_042," "{health_log_path}/health_log.csv"

# 3. Get narrative context from health_log.md
grep -A10 -B10 "episode_042\|headache" "{health_log_path}/health_log.md"

# 4. Find temporally related labs (within episode date range)
awk -F',' -v start="2025-10-15" -v end="2025-10-20" \
  'NR==1 || ($1 >= start && $1 <= end)' \
  "{labs_path}/all.csv"
```

**Synthesis approach**:
- Group events by category (symptoms, treatments, outcomes)
- Identify temporal sequence
- Note what worked/didn't work
- Look for patterns across similar episodes

### Listing Current Medications & Supplements

When user asks about medications (e.g., "What am I currently taking?"):

```bash
# Extract all medication and supplement events
grep -E ",medication,|,supplement," "{health_log_path}/health_log.csv" | \
  awk -F',' '{print $1","$3","$5","$6}' | \
  tail -100  # Recent entries
```

**Status determination** (use `.claude/skills/health-agent/references/status-keywords.md`):

1. **Active**: Latest mention has active keywords ("taking", "continuing", "started", "prescribed")
2. **Discontinued**: Latest mention has stop keywords ("discontinued", "stopped", "ended")
3. **As-needed**: Mentioned with PRN keywords ("as needed", "when", "if")

**Analysis approach**:
- Group by medication/supplement name
- Find latest status for each
- Note start dates and dosages
- Flag potential interactions or duplicates

### Cataloging Medical Exams

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

### Generating Health Summaries

When user asks for overall health summary:

**Systematic approach**:

1. **Demographics**: Extract from profile YAML (age, gender)

2. **Active Conditions**:
```bash
grep ",condition," "{health_log_path}/health_log.csv" | tail -50
```
Apply status determination to identify active vs resolved.

3. **Current Medications**: Use pattern above

4. **Recent Labs** (last 6-12 months):
```bash
awk -F',' -v start="$(date -v-12m +%Y-%m-%d)" 'NR==1 || $1 >= start' \
  "{labs_path}/all.csv" | head -100
```

5. **Recent Health Events**:
```bash
awk -F',' -v start="$(date -v-6m +%Y-%m-%d)" 'NR==1 || $1 >= start' \
  "{health_log_path}/health_log.csv"
```

6. **Recent Exams**: Use catalog pattern above

7. **Genetics** (if configured): Key findings from pharmacogenomics and health risks

**Synthesis**: Create narrative connecting findings across sources.

### Finding Temporal Correlations

When user asks about patterns (e.g., "Does X correlate with Y?"):

**Systematic approach**:

1. **Extract both variables across same timeframe**:
```bash
# Variable 1 (e.g., stress events)
grep -i "stress" "{health_log_path}/health_log.csv"

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
   - Use `scientific-literature-search` skill for authoritative citations

### Understanding Biological Mechanisms

When user asks "what's the connection between X and Y?" or "why does X cause Y?":

**Reasoning approach**:

1. **Classify observation types**: lab value, symptom, event, condition
2. **Propose known pathways**: Based on medical knowledge
3. **Check for intermediate markers**: Are there measurable steps between X and Y?
4. **Verify temporal sequence**: Does X consistently precede Y?
5. **Assess plausibility**: High (well-established) / Moderate (plausible) / Low (speculative)

**IMPORTANT**: Always use `scientific-literature-search` skill to find authoritative citations for proposed mechanisms. Don't rely solely on general knowledge.

Example query: "Find papers on the mechanism linking chronic stress to elevated cortisol"

### Cross-Source Integration

When analyzing any health concern, systematically check all data sources:

**Standard workflow**:
```
1. Health Timeline (health_log.csv)
   - Search by category for relevant events
   - Identify episode_id for related events

2. Health Narrative (health_log.md)
   - Get detailed context around dates
   - Find subjective descriptions

3. Labs (all.csv)
   - Find relevant markers near event dates
   - Check for abnormalities

4. Exams (*/summary.md)
   - Search for related findings
   - Note imaging results

5. Genetics (if configured)
   - Check relevant SNPs via genetics-snp-lookup skill
   - Consider pharmacogenomic implications
```

### Generating Provider Documentation

When user needs documentation for healthcare visits, use the **`prepare-provider-visit` skill** instead of manual assembly.

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

### Efficient Data Access Notes

All large files (`all.csv`, `health_log.csv`, `health_log.md`) typically exceed Claude's read limits. Always use:

- **Filtered extraction**: grep, awk, head/tail commands
- **Date ranges**: Filter by relevant timeframe first
- **Targeted queries**: Search for specific terms before broad reads
- **Incremental reading**: Start narrow, expand if needed

**Never** attempt to read these files entirely - use the extraction patterns above.

## Built-in Skills

Six core skills provide specialized capabilities in `.claude/skills/health-agent/`:

### External Integrations (APIs + Caching)

| Skill | Use When |
|-------|----------|
| `genetics-snp-lookup` | User asks to look up specific SNPs (e.g., "rs12345"), check pharmacogenomics genes (CYP2D6, CYP2C19, etc.), or query health risk variants (APOE, Factor V Leiden, etc.). Queries SNPedia API with 30-day caching. |
| `genetics-validate-interpretation` | User wants to validate genetic interpretations against SNPedia or cross-reference allele orientation. |
| `scientific-literature-search` | User asks to find research papers, verify biological mechanisms, or needs authoritative citations. Queries PubMed + Semantic Scholar with 30-day caching. Used automatically in root cause investigations. |

### Orchestration Workflows

| Skill | Use When |
|-------|----------|
| `investigate-root-cause` | User asks "investigate root cause of [condition]", "why do I have [condition]", "find the cause of [symptom]", or "what's causing my [condition]". Performs multi-turn hypothesis investigation with evidence gathering, mechanism validation via literature search, and comprehensive genetic analysis. |
| `prepare-provider-visit` | User asks to "prepare for doctor visit", "generate provider summary", or "create medical documentation". Intelligently orchestrates data gathering based on visit type (annual/specialist/follow-up/urgent) and generates coherent provider-appropriate narratives. |
| `generate-questionnaire` | User asks to create questionnaire or systematically augment health log data with structured gap analysis. |

### Analysis Patterns (Not Skills)

All health data analysis (lab trends, abnormal values, episodes, correlations, medications, health summaries, exams) is performed naturally using query patterns documented in the "Common Analysis Patterns" section above. These patterns combine bash commands (grep, awk) with Claude's reasoning to answer user questions directly.

### Shared References

`.claude/skills/health-agent/references/` contains shared resources:

**`lab-specs-helpers.sh`**:
- Helper functions for querying `{labs_path}/lab_specs.json`
- `get_canonical_name()` - Get standard name from any alias
- `build_grep_pattern()` - Build grep pattern from all aliases
- `get_primary_unit()` - Get standard unit for marker
- `get_conversion_factor()` - Convert between units

**`status-keywords.md`**:
- Status determination keywords (active, discontinued, suspected, resolved)
- Status classification algorithm for medications, supplements, conditions, and episodes
- Used when analyzing medication timelines and condition status

### Genetics Data Sources

All genetics interpretations come from **SNPedia** via the `genetics-snp-lookup` skill:
- **Centralized lookup mechanism**: Single skill handles all genetic queries
- **Online data source**: Queries SNPedia MediaWiki API for up-to-date interpretations
- **Caching**: 30-day TTL to minimize API calls and improve performance
- **Coverage**: 631k+ SNPs from 23andMe data
- **Drug metabolism**: CYP2D6, CYP2C19, CYP2C9, VKORC1, SLCO1B1, TPMT, DPYD
- **Health risks**: APOE, Factor V Leiden, HFE hemochromatosis, MTHFR, BRCA founder mutations

When users ask about genetics, use `genetics-snp-lookup` directly with natural language queries like:
- "Look up rs12345"
- "Check my CYP2D6 status"
- "What's my APOE genotype?"
- "Search for Factor V Leiden"

## Creating Custom Skills

Users can create additional skills in `~/.claude/skills/` for custom analyses:

```markdown
---
name: my-analysis
description: "What it does and trigger phrases"
---

# My Analysis Skill

Instructions for performing the analysis...
```

## Provider Documentation System

Provider documentation is generated via the **`prepare-provider-visit` skill**, which intelligently orchestrates data gathering and generates coherent narratives based on visit type.

### Using prepare-provider-visit

When user asks to prepare documentation for a healthcare visit, invoke the `prepare-provider-visit` skill. The skill:

1. **Asks minimal questions**: Visit type (annual/specialist/follow-up/urgent) and specific concerns
2. **Smart defaults**: Automatically determines relevant sections based on visit type
3. **Intelligent data gathering**: Uses analysis patterns to extract medications, labs, events, conditions, and genetics (if relevant)
4. **Coherent narrative**: Generates connected prose, not concatenated sections
5. **Provider-appropriate**: Professional medical documentation style

### Output Structure

```
.output/{profile}/
├── provider-visit-{visit_type}-{YYYY-MM-DD}.md  # Generated by prepare-provider-visit
├── hypothesis-investigation-{condition}-{YYYY-MM-DD}.md  # Generated by investigate-root-cause
└── health-log-augmentation-{YYYY-MM-DD}.md  # Generated by generate-questionnaire
```

### Report Format

Provider visit summaries follow this structure:

```markdown
---
document_type: provider_visit_summary
visit_type: {annual|specialist|follow_up|urgent}
generated: {YYYY-MM-DD}
profile: {profile_name}
timeframe: {description}
---

# Provider Visit Summary
**Patient**: {name}
**Visit Type**: {type}
**Generated**: {date}

## Visit Context
{2-3 sentences on reason for visit and overall status}

## Current Medications & Supplements
{Narrative + table of active medications}

## Recent Health Events
{Grouped by category with narrative synthesis}

## Laboratory Results
{Abnormal values with interpretation}

## Active Medical Conditions
{Bulleted list with status}

## Relevant Genetic Findings (if applicable)
{Only included when directly relevant to visit purpose}

## Summary & Considerations
{2-4 key discussion points for provider}

---
*Generated by health-agent to support clinical decision-making.*
```

### Creating Output Directories

**Directory Creation** - Use Bash (works in sandbox):
```bash
mkdir -p .output/{profile}
```

**File Writing** - Use the `Write` tool, NOT Bash heredocs:
```
# CORRECT: Use Write tool for report files
Write tool with file_path=".output/{profile}/provider-visit-annual-2026-01-21.md"

# WRONG: Bash heredocs fail in sandbox mode
cat > file.md << 'EOF'  # This will fail with "operation not permitted"
```

The Write tool works in sandboxed mode for files within the project directory. Bash heredocs and redirections are blocked by sandbox restrictions.

## Root Cause Investigation

The `investigate-root-cause` skill automates comprehensive hypothesis generation and testing for health conditions.

### Invocation

Use when user asks:
- "Investigate root cause of [condition]"
- "Why do I have [condition]?"
- "Find the cause of [symptom]"
- "What's causing my [condition]?"

### How It Works

1. **Invocation**: User triggers the skill
2. **Process**: Skill spawns a general-purpose agent that:
   - Gathers evidence using analysis patterns from CLAUDE.md (timeline events, lab trends, abnormal values, medications, exams)
   - Performs comprehensive genetic analysis via `genetics-snp-lookup` (checks ALL condition-relevant genes)
   - Generates 3-5 competing hypotheses with biological mechanisms
   - **Queries scientific literature** via `scientific-literature-search` for ALL proposed mechanisms (MANDATORY)
   - Tests hypotheses against data (searches for contradictions, identifies confounds)
   - Ranks hypotheses by supporting evidence
   - Iterates and refines based on contradictions
3. **Output**: Saved to `.output/{profile}/hypothesis-investigation-{condition}-YYYY-MM-DD.md`

### Output Format

Hypothesis investigation reports include:
- **Ranked hypotheses** (High/Medium/Low likelihood with percentages)
- **Supporting evidence** with data citations (dates, lab values, timeline events, genetics findings)
- **Contradictory evidence** with explanations or acknowledgment
- **Genetic analysis** (comprehensive check of condition-relevant genes with both positive and negative findings)
- **Biological mechanisms** with literature citations from PubMed/Semantic Scholar
- **Confounding factors** that could explain observations
- **Testable predictions** (what should be true if hypothesis is correct)
- **Recommended follow-up investigations** (what data to collect next)

### Available Tools for Investigation Agent

The hypothesis investigation agent has access to:
- **Analysis patterns** from CLAUDE.md "Common Analysis Patterns" section (bash queries for all data sources)
- **Genetics**: `genetics-snp-lookup` for comprehensive genetic analysis
- **Literature**: `scientific-literature-search` for mechanism validation (MANDATORY - used automatically)
- **Data sources**: All profile data (labs, timeline, exams, health log narrative, genetics)

### Example Workflow

**User**: "Investigate root cause of my recurring headaches"

**Agent Process**:
1. Gathers all headache events from health_log.csv via grep
2. Finds temporal patterns via correlation analysis
3. Identifies potential triggers: poor sleep (5 instances), stress (3 instances), caffeine changes (2 instances)
4. Proposes biological pathways for each mechanism
5. **Queries PubMed** for citations on "sleep deprivation headache mechanism", "caffeine withdrawal mechanism", "stress headache pathway"
6. Identifies confounds (caffeine changes during poor sleep)
7. Searches for contradictory evidence
8. Ranks hypotheses: HIGH (sleep deprivation - 85%), MODERATE (caffeine withdrawal - 55%), LOW (stress - 30%)
9. Recommends follow-up: Track caffeine intake separately from sleep to discriminate between hypotheses

**Output**: Markdown report saved to `.output/{profile}/hypothesis-investigation-headaches-2026-01-21.md`

### Key Improvements

- **Literature-backed mechanisms**: Every biological pathway includes authoritative citations
- **Natural data analysis**: Uses bash query patterns instead of invoking multiple skills
- **Comprehensive genetics**: Checks all condition-relevant genes via SNPedia
- **Iterative refinement**: Multi-turn investigation with evidence-based ranking

## Important Notes

- **Privacy**: Profile YAML files contain paths to sensitive health data. They are gitignored except for the template.
- **No Scripts**: This agent reads data files directly - no Python preprocessing required.
- **Demographics**: Use `date_of_birth` and `gender` when interpreting reference ranges, as many vary by age and sex.
- **Confidence Scores**: Lab values with low confidence (<0.8) should be flagged for manual verification.
- **Large File Handling**: Data files (`all.csv`, `health_log.csv`, `health_log.md`) typically exceed Claude's 256KB/25000 token read limits. Skills include "Efficient Data Access" sections with extraction commands. Always use filtered extraction (grep/head) rather than direct reads for these files.
- **Lab Specifications**: If `{labs_path}/lab_specs.json` exists, skills use it for more accurate marker matching via canonical names and aliases. Helper functions are in `.claude/skills/health-agent/references/lab-specs-helpers.sh`. If the file is missing, skills use case-insensitive fuzzy matching on lab_name values. This file is optional and generated by labs-parser.
- **Genetics Data**: All genetics interpretations come from SNPedia via the `genetics-snp-lookup` skill. Data is cached for 30 days. Skills delegate to genetics-snp-lookup rather than using hardcoded reference files.
- **Sandbox Compliance**: Always use the `Write` tool (not Bash heredocs/redirects) to create files in `.output/`. Bash `mkdir -p` works for directories, but file writing via `cat > file` or heredocs is blocked by sandbox. This ensures reports generate without permission errors.

## Maintenance

Keep README.md updated with any significant project changes.
