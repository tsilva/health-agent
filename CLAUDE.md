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
| `source_file` | string | Original PDF filename |
| `lab_date` | date | Date of lab test (YYYY-MM-DD) |
| `lab_name` | string | Name of the test/marker |
| `lab_value` | float | Measured value |
| `lab_unit` | string | Unit of measurement |
| `lab_reference_range` | string | Reference range (e.g., "70-100") |
| `confidence` | float | OCR confidence score (0-1) |

**Example queries**:
- Track a specific marker over time: filter by `lab_name`
- Find out-of-range values: parse `lab_reference_range` and compare to `lab_value`
- Review recent labs: sort by `lab_date` descending

### Health Timeline (health-log-parser)

**File**: `{health_log_path}/health_timeline.csv`

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Event date (YYYY-MM-DD) |
| `category` | string | Event category (symptom, medication, condition, etc.) |
| `event` | string | Brief event description |
| `episode_id` | string | Links related events (e.g., "episode_001") |
| `notes` | string | Additional context |

**Episode IDs**: Events with the same `episode_id` are related (e.g., a cold's symptoms, treatment, and resolution).

### Health Log Narrative (health-log-parser)

**File**: `{health_log_path}/health_log.md`

Markdown journal with chronological health entries. Use for:
- Full context around timeline events
- Detailed symptom descriptions
- Treatment responses and outcomes

### Medical Exam Summaries (medical-exams-parser)

**Directory**: `{exams_path}/*.summary.md`

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
- List all summaries: `ls {exams_path}/*.summary.md`
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
1. Search health_timeline.csv for related events by category
2. Find linked events via episode_id
3. Check health_log.md for detailed context around those dates
4. Look for relevant lab values near those dates
5. Search exam summaries for related findings
```

## Creating Analysis Skills

Users can create custom skills in `~/.claude/skills/` for common analyses:

```markdown
---
description: "Analyze trends for a specific lab marker"
---

# Lab Trend Analysis Skill

When analyzing lab trends:
1. Load the active profile's labs_path
2. Read all.csv and filter for the requested marker
3. Sort by lab_date
4. Calculate: min, max, mean, trend direction
5. Identify out-of-range values
6. Present findings with dates and context
```

## Important Notes

- **Privacy**: Profile YAML files contain paths to sensitive health data. They are gitignored except for the template.
- **No Scripts**: This agent reads data files directly - no Python preprocessing required.
- **Demographics**: Use `date_of_birth` and `gender` when interpreting reference ranges, as many vary by age and sex.
- **Confidence Scores**: Lab values with low confidence (<0.8) should be flagged for manual verification.

## Maintenance

Keep README.md updated with any significant project changes.
