# Health Agent

A Claude Code-based health analysis agent that ingests data from three parsers and provides analytical capabilities through direct file reads and custom skills.

## Quick Start

**At session start, invoke the Health Dashboard** by reading and following `.claude/skills/health-agent/health-dashboard/SKILL.md`.

The dashboard provides an interactive experience using `AskUserQuestion`:
1. Profile selection (interactive menu)
2. State initialization check (with guided setup if needed)
3. Visual dashboard display (conditions, actions, medications, goals)
4. Action menu (investigate, review data, prepare visit, track labs)

**Slash command**: When user types `/health-dashboard`, read and follow `.claude/skills/health-agent/health-dashboard/SKILL.md`.

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

  # SelfDecode API (optional - for imputed SNP coverage beyond 23andMe)
  selfdecode:
    enabled: false
    profile_id: ""
    jwt_token: ""
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

### Lab Specifications (labs-parser)

**File**: `{labs_path}/lab_specs.json` (optional)

Machine-readable lab marker specifications for accurate matching and unit standardization.

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

Helper functions: `.claude/skills/health-agent/references/lab-specs-helpers.sh`

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

**Episode IDs**: Events with the same `EpisodeID` are related.

### Health Log Narrative (health-log-parser)

**File**: `{health_log_path}/health_log.md`

Markdown journal with chronological health entries for full context.

### Medical Exam Summaries (medical-exams-parser)

**Directory**: `{exams_path}/*/*.summary.md`

Each exam produces a markdown summary with YAML frontmatter containing `exam_type`, `exam_date`, `body_region`, and `provider`.

### 23andMe Genetics Data (optional)

**File**: `{genetics_23andme_path}` (typically `23andme_raw_data.txt`)

Tab-separated file with ~631,000 SNPs: `rsid`, `chromosome`, `position`, `genotype`.

**Efficient data access** (file is too large to read directly):
```bash
grep "^rs12345" "{genetics_23andme_path}"  # Single SNP
grep -E "^(rs123|rs456|rs789)" "{genetics_23andme_path}"  # Batch
```

## Common Analysis Patterns

Query patterns for health data analysis are documented in:
`.claude/skills/health-agent/references/analysis-patterns.md`

Read this file when performing data analysis tasks.

## Skills

### When to Use Each Skill

| User Says | Use Skill | Path |
|-----------|-----------|------|
| Session start, "show dashboard", "health status" | `health-dashboard` | `.claude/skills/health-agent/health-dashboard/SKILL.md` |
| "Investigate root cause of X", "why do I have X" | `investigate-root-cause` | `.claude/skills/health-agent/investigate-root-cause/SKILL.md` |
| "Prepare for doctor visit", "generate provider summary" | `prepare-provider-visit` | `.claude/skills/health-agent/prepare-provider-visit/SKILL.md` |
| "Look up rs12345", "check my CYP2D6", "APOE genotype" | `genetics-snp-lookup` | `.claude/skills/health-agent/genetics-snp-lookup/SKILL.md` |
| "Check SelfDecode for X", "imputed genotype" | `genetics-selfdecode-lookup` | `.claude/skills/health-agent/genetics-selfdecode-lookup/SKILL.md` |
| "Validate interpretation", "cross-reference allele" | `genetics-validate-interpretation` | `.claude/skills/health-agent/genetics-validate-interpretation/SKILL.md` |
| "Find research on X", "PubMed search" | `scientific-literature-search` | `.claude/skills/health-agent/scientific-literature-search/SKILL.md` |
| "Create questionnaire", "augment health log" | `generate-questionnaire` | `.claude/skills/health-agent/generate-questionnaire/SKILL.md` |

### How to Use Skills

**IMPORTANT**: These are project-local skill instruction files, NOT globally-installed skills.

**To use a skill:**
1. Read the SKILL.md file for the skill you need
2. Follow the instructions in the skill file

Skills typically instruct you to:
- Execute specific commands/queries directly
- Spawn a Task agent with a detailed prompt template
- Follow a multi-step workflow

### Skill Categories

**External Integrations** (APIs + 30-day caching):
- `genetics-snp-lookup` - SNPedia API for SNP interpretations
- `genetics-selfdecode-lookup` - SelfDecode for imputed SNPs (~20M vs 631k)
- `scientific-literature-search` - PubMed + Semantic Scholar

**Orchestration Workflows**:
- `health-dashboard` - Interactive session entry point
- `investigate-root-cause` - 4 parallel agents with adversarial validation
- `prepare-provider-visit` - Coherent provider documentation
- `generate-questionnaire` - Structured gap analysis

### Shared References

`.claude/skills/health-agent/references/` contains shared resources:

| File | Purpose |
|------|---------|
| `data-access-helpers.sh` | Extraction functions for large data files |
| `lab-specs-helpers.sh` | Lab marker canonical names and unit conversion |
| `status-keywords.md` | Active/discontinued/resolved status determination |
| `analysis-patterns.md` | Query patterns for health data analysis |
| `confidence-calibration.md` | Investigation confidence calculation formulas |
| `interpretation-validation.md` | Evidence interpretation validation rules |
| `troubleshooting.md` | Common issues and solutions |
| `known-limitations.md` | Technical limitations of data sources |
| `faq.md` | Frequently asked questions |

### Genetics Lookup Strategy

1. **First**: Check 23andMe raw data via `genetics-snp-lookup` (directly genotyped = most reliable)
2. **Second**: If SNP not found and SelfDecode configured, check `genetics-selfdecode-lookup` (imputed)
3. **Always**: Use SNPedia for interpretation context

## Creating Custom Skills

Users can create additional skills in `.claude/skills/health-agent/your-skill/`:

```markdown
---
name: your-skill
description: "What it does and trigger phrases"
---

# Your Skill Name

Instructions for performing the analysis...
```

## Important Notes

- **Privacy**: Profile YAML files contain paths to sensitive health data. They are gitignored except for the template.
- **No Scripts**: This agent reads data files directly - no Python preprocessing required.
- **Demographics**: Use `date_of_birth` and `gender` when interpreting reference ranges.
- **Confidence Scores**: Lab values with confidence <0.8 should be flagged for manual verification.
- **Large File Handling**: Data files exceed read limits. Use filtered extraction (grep/head) rather than direct reads.
- **Lab Specifications**: If `lab_specs.json` exists, use it for accurate marker matching via canonical names.
- **Genetics Data**: Primary source is SNPedia via `genetics-snp-lookup`. SelfDecode is optional for imputed coverage.
- **Sandbox Compliance**: Use the `Write` tool (not Bash heredocs) to create files in `.output/`.

## Troubleshooting

See `.claude/skills/health-agent/references/troubleshooting.md` for common issues and solutions.

## Known Limitations

See `.claude/skills/health-agent/references/known-limitations.md` for technical limitations.

## FAQ

See `.claude/skills/health-agent/references/faq.md` for frequently asked questions.

## Maintenance

Keep README.md updated with any significant project changes.
