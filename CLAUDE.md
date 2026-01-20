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
- If file is missing, skills fall back to manual patterns from `references/common-markers.md`

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

## Analysis Patterns

### Cross-Source Correlation

When analyzing health patterns, consider data from all sources:

1. **Labs** - Objective biomarker data with timestamps
2. **Timeline** - Structured event tracking with episode linking
3. **Exams** - Imaging and procedure findings
4. **Health Log** - Narrative context and subjective symptoms
5. **Genetics** - Pharmacogenomics and health risk variants (if configured)

### Example: Investigating a Health Concern

```
1. Search health_log.csv for related events by category
2. Find linked events via episode_id
3. Check health_log.md for detailed context around those dates
4. Look for relevant lab values near those dates
5. Search exam summaries for related findings
```

## Built-in Skills

Twenty-one skills are available in `.claude/skills/health-agent/`:

### Data Collection Skills

| Skill | Use When |
|-------|----------|
| `generate-questionnaire` | User asks to create questionnaire or systematically augment health log data |

### Analysis Skills

| Skill | Use When |
|-------|----------|
| `lab-trend` | User asks to track a specific marker over time |
| `out-of-range-labs` | User asks for abnormal or flagged lab values |
| `exam-catalog` | User asks to list or search medical exams |
| `episode-investigation` | User asks about a specific health episode |
| `health-summary` | User needs a comprehensive health overview |
| `cross-temporal-correlation` | User asks about patterns or correlations |
| `medication-supplements` | User asks for medication list or supplement tracking |

### Genetics Skills

| Skill | Use When |
|-------|----------|
| `genetics-snp-lookup` | User asks to look up a specific SNP (e.g., "rs12345") |
| `genetics-pharmacogenomics` | User asks about drug metabolism or CYP status |
| `genetics-health-risks` | User asks about APOE, Factor V Leiden, or genetic risks |

### Hypothesis Investigation Skills

| Skill | Use When |
|-------|----------|
| `investigate-root-cause` | User asks to investigate root cause of a condition |
| `mechanism-search` | User asks about biological mechanisms linking observations |
| `confound-identification` | User asks what could confound a correlation |
| `evidence-contradiction-check` | User asks to test hypothesis against data |

### Report Skills

Report skills generate saveable markdown sections to `.output/{profile}/sections/`:

| Skill | Use When |
|-------|----------|
| `report-medication-list` | User needs medication list for provider visit |
| `report-labs-abnormal` | User needs abnormal labs summary for provider |
| `report-health-events` | User needs recent health timeline for provider |
| `report-pharmacogenomics` | User needs pharmacogenomics summary for provider |
| `report-genetic-risks` | User needs genetic risks summary for provider |
| `report-conditions-status` | User needs active/resolved conditions list for provider |

### Shared References

`references/common-markers.md` contains:
- Marker name aliases (e.g., "A1C" = "HbA1c")
- Age-specific range adjustments
- Gender-specific range adjustments
- Critical value thresholds

`references/genetics-pharmacogenomics.md` contains:
- Drug metabolism gene variants (CYP2D6, CYP2C19, CYP2C9, VKORC1, SLCO1B1, TPMT, DPYD)
- Metabolizer status determination
- Affected medications and dosing implications

`references/genetics-health-risks.md` contains:
- Health risk variants (APOE, Factor V Leiden, HFE, MTHFR, BRCA founder mutations)
- Risk interpretations and clinical significance
- Limitations of 23andMe testing

`references/genetics-snp-index.md` contains:
- Master rsID lookup table
- Batch grep patterns for variant categories
- 23andMe data format reference

`references/status-keywords.md` contains:
- Status determination keywords (active, discontinued, suspected, resolved)
- Status classification algorithm for medications, supplements, conditions, and episodes
- Used by: medication-supplements, report-medication-list, report-conditions-status, report-health-events

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

## Report Skills System

Report skills are a special category of skills that generate **composable** markdown sections for provider visits or personal records.

### Design Philosophy

Reports are **building blocks**. Each report skill generates a focused section that:
1. Can be generated independently
2. Can be combined with other report sections into comprehensive documents
3. Has a consistent header/format for easy concatenation

### Naming Convention

Report skills use the `report-*` prefix:
- `report-medication-list`
- `report-labs-abnormal`
- `report-health-events`
- `report-pharmacogenomics`
- `report-genetic-risks`
- `report-conditions-status`

### Output Structure

```
.output/{profile}/
├── sections/                    # Individual report sections
│   ├── medication-list-YYYY-MM-DD.md
│   ├── labs-abnormal-YYYY-MM-DD.md
│   ├── health-events-YYYY-MM-DD.md
│   ├── pharmacogenomics-YYYY-MM-DD.md
│   ├── genetic-risks-YYYY-MM-DD.md
│   └── conditions-status-YYYY-MM-DD.md
├── hypothesis/                  # Hypothesis investigation reports
│   ├── hemolysis-YYYY-MM-DD.md
│   ├── headaches-YYYY-MM-DD.md
│   └── fatigue-YYYY-MM-DD.md
├── questionnaires/              # Health log augmentation questionnaires
│   └── health-log-augmentation-YYYY-MM-DD.md
└── combined/                    # Assembled reports (future)
    └── provider-visit-YYYY-MM-DD.md
```

### Section Format

Each report section follows a consistent format for composability:

```markdown
---
section: {section-name}
generated: {YYYY-MM-DD}
profile: {profile_name}
---

# {Section Title}

{Content with tables and structured data}

---
*Section generated by health-agent {skill-name} skill*
```

### Combining Sections

To create a combined report:
1. Generate individual section reports
2. Concatenate sections in desired order
3. Add a cover page/header if needed
4. Save to `.output/{profile}/combined/`

Example combined reports:
- **Provider Visit** = medication-list + labs-abnormal + health-events + conditions-status
- **Genetics Review** = pharmacogenomics + genetic-risks
- **Comprehensive Visit** = medication-list + pharmacogenomics + labs-abnormal + health-events + conditions-status + genetic-risks
- **Annual Review** = all sections + exam summaries + trends

### Creating Report Directories and Files

**Directory Creation** - Use Bash (works in sandbox):
```bash
mkdir -p .output/{profile}/sections
```

**File Writing** - Use the `Write` tool, NOT Bash heredocs:
```
# CORRECT: Use Write tool for report files
Write tool with file_path=".output/{profile}/sections/report-name-YYYY-MM-DD.md"

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
   - Gathers evidence using analysis skills (episode-investigation, cross-temporal-correlation, lab-trend, etc.)
   - Performs comprehensive genetic analysis (checks ALL condition-relevant genes using both genetics skills AND direct SNP lookups)
   - Generates 3-5 competing hypotheses with biological mechanisms (mechanism-search)
   - Tests hypotheses against data (evidence-contradiction-check)
   - Identifies confounding factors (confound-identification)
   - Ranks hypotheses by supporting evidence
   - Iterates and refines based on contradictions
3. **Output**: Saved to `.output/{profile}/sections/hypothesis-investigation-{condition}-YYYY-MM-DD.md`

### Output Format

Hypothesis investigation reports include:
- **Ranked hypotheses** (High/Medium/Low likelihood)
- **Supporting evidence** with data citations (dates, lab values, timeline events, genetics findings)
- **Contradictory evidence** with explanations or acknowledgment
- **Genetic analysis** (comprehensive check of condition-relevant genes with both positive and negative findings)
- **Biological mechanisms** linking observations (if identifiable)
- **Confounding factors** that could explain observations
- **Testable predictions** (what should be true if hypothesis is correct)
- **Recommended follow-up investigations** (what data to collect next)

### Integration with Report Skills

Hypothesis investigation reports are saved to `.output/{profile}/sections/` (same directory as report sections), enabling future integration with provider visit summaries. For example:
- **Provider Visit** = conditions-status + hypothesis-investigation-fatigue + labs-abnormal + medication-list
- **Specialist Referral** = hypothesis-investigation-headaches + health-events + exam-catalog

### Available Tools for Hypothesis Agent

The hypothesis generation agent has access to all 20 health-agent skills:
- **Evidence gathering**: episode-investigation, cross-temporal-correlation, lab-trend, out-of-range-labs, exam-catalog
- **Mechanism exploration**: mechanism-search (identifies biological pathways)
- **Confound detection**: confound-identification (rules out alternative explanations)
- **Hypothesis testing**: evidence-contradiction-check (searches for counter-examples)
- **Supporting data**: health-summary, medication-supplements, genetics skills (if configured)

### Example Workflow

**User**: "Investigate root cause of my recurring headaches"

**Agent Process**:
1. Uses `episode-investigation` to gather all headache events
2. Uses `cross-temporal-correlation` to find temporal patterns
3. Identifies potential triggers: poor sleep (5 instances), stress (3 instances), caffeine changes (2 instances)
4. Uses `mechanism-search` to propose biological pathways
5. Uses `confound-identification` to check for confounds
6. Uses `evidence-contradiction-check` to test hypotheses
7. Ranks hypotheses by supporting evidence
8. Recommends follow-up: Track caffeine intake separately from sleep to discriminate between hypotheses

**Output**: Markdown report saved to `.output/{profile}/sections/hypothesis-investigation-headaches-2026-01-20.md`

### Differences from Analysis Skills

| Feature | Analysis Skills | Hypothesis Generation |
|---------|----------------|----------------------|
| **Execution** | Single-pass workflow | Multi-turn iterative exploration |
| **Output** | Report patterns found | Propose and test competing explanations |
| **Iteration** | No refinement loop | Refines hypotheses based on contradictions |

## Important Notes

- **Privacy**: Profile YAML files contain paths to sensitive health data. They are gitignored except for the template.
- **No Scripts**: This agent reads data files directly - no Python preprocessing required.
- **Demographics**: Use `date_of_birth` and `gender` when interpreting reference ranges, as many vary by age and sex.
- **Confidence Scores**: Lab values with low confidence (<0.8) should be flagged for manual verification.
- **Large File Handling**: Data files (`all.csv`, `health_log.csv`, `health_log.md`) typically exceed Claude's 256KB/25000 token read limits. Skills include "Efficient Data Access" sections with extraction commands. Always use filtered extraction (grep/head) rather than direct reads for these files.
- **Lab Specifications**: If `{labs_path}/lab_specs.json` exists, skills use it for more accurate marker matching via canonical names and aliases. Helper functions are in `.claude/skills/health-agent/references/lab-specs-helpers.sh`. If the file is missing, skills gracefully fall back to manual patterns from `references/common-markers.md`. This file is optional and generated by labs-parser.
- **Sandbox Compliance**: Always use the `Write` tool (not Bash heredocs/redirects) to create files in `.output/`. Bash `mkdir -p` works for directories, but file writing via `cat > file` or heredocs is blocked by sandbox. This ensures reports generate without permission errors.

## Maintenance

Keep README.md updated with any significant project changes.
