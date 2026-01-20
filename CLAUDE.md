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

## Analysis Patterns

### Cross-Source Correlation

When analyzing health patterns, consider data from all three sources:

1. **Labs** - Objective biomarker data with timestamps
2. **Timeline** - Structured event tracking with episode linking
3. **Exams** - Imaging and procedure findings
4. **Health Log** - Narrative context and subjective symptoms

### Example: Investigating a Health Concern

```
1. Search health_log.csv for related events by category
2. Find linked events via episode_id
3. Check health_log.md for detailed context around those dates
4. Look for relevant lab values near those dates
5. Search exam summaries for related findings
```

## Built-in Skills

Ten skills are available in `.claude/skills/health-agent/`:

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

### Report Skills

Report skills generate saveable markdown sections to `.output/{profile}/sections/`:

| Skill | Use When |
|-------|----------|
| `report-medication-list` | User needs medication list for provider visit |
| `report-labs-abnormal` | User needs abnormal labs summary for provider |
| `report-health-events` | User needs recent health timeline for provider |

### Shared Reference

`references/common-markers.md` contains:
- Marker name aliases (e.g., "A1C" = "HbA1c")
- Age-specific range adjustments
- Gender-specific range adjustments
- Critical value thresholds

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

### Output Structure

```
.output/{profile}/
├── sections/                    # Individual report sections
│   ├── medication-list-YYYY-MM-DD.md
│   ├── labs-abnormal-YYYY-MM-DD.md
│   └── health-events-YYYY-MM-DD.md
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
- **Provider Visit** = medication-list + labs-abnormal + health-events
- **Annual Review** = all sections + exam summaries + trends

### Creating Report Directories

Report skills should create the output directory if it doesn't exist:
```bash
mkdir -p .output/{profile}/sections
```

## Important Notes

- **Privacy**: Profile YAML files contain paths to sensitive health data. They are gitignored except for the template.
- **No Scripts**: This agent reads data files directly - no Python preprocessing required.
- **Demographics**: Use `date_of_birth` and `gender` when interpreting reference ranges, as many vary by age and sex.
- **Confidence Scores**: Lab values with low confidence (<0.8) should be flagged for manual verification.
- **Large File Handling**: Data files (`all.csv`, `health_log.csv`, `health_log.md`) typically exceed Claude's 256KB/25000 token read limits. Skills include "Efficient Data Access" sections with extraction commands. Always use filtered extraction (grep/head) rather than direct reads for these files.

## Maintenance

Keep README.md updated with any significant project changes.
