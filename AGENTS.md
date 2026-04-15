# Health Agent

A local health analysis agent that ingests data from three parser outputs and optional 23andMe raw data, then answers questions by reading those files directly.

## Session Start

At the start of a health-analysis session:

1. List available profiles with `ls ~/.config/health-agent/profiles/*.yaml`.
2. If the user has not already named a profile, ask which profile to use.
3. Read the selected profile and extract the `data_sources` paths.
4. If `~/.config/health-agent/.env` exists and the task may need API credentials, load it.
5. Use those paths as the source of truth for the rest of the session.

`profiles/template.yaml.example` is a committed example file, not a live profile. Active profiles belong in `~/.config/health-agent/profiles/`.

## Profile Schema

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

### Labs Data

**File**: `{labs_path}/all.csv`

| Column | Type | Description |
|--------|------|-------------|
| `date` | date | Date of lab test (`YYYY-MM-DD`) |
| `source_file` | string | Original PDF filename |
| `page_number` | int | Page number in the source PDF |
| `lab_name` | string | Name of the test or marker |
| `value` | float | Measured value |
| `unit` | string | Unit of measurement |
| `reference_min` | float | Lower bound of the reference range |
| `reference_max` | float | Upper bound of the reference range |
| `confidence` | float | OCR confidence score (`0-1`) |

Optional file: `{labs_path}/lab_specs.json`

If present, use it to normalize marker names, aliases, units, and reference ranges.

### Health Log

**Current state**: `{health_log_path}/current.yaml`

Use `current.yaml` as the authoritative source for active conditions, current medications, supplements, experiments, and open todos.

```yaml
conditions:
  - name: "Condition Name"
    status: active|monitoring|resolved
    onset: "YYYY-MM-DD"

medications:
  - name: "Medication Name"
    dose: "10mg"
    frequency: "daily"
    started: "YYYY-MM-DD"

supplements:
  - name: "Supplement Name"
    dose: "1000IU"
    frequency: "daily"

experiments:
  - name: "Experiment Name"
    status: active|completed|paused
    started: "YYYY-MM-DD"

todos:
  - item: "Todo item"
    priority: high|medium|low
```

**History timeline**: `{health_log_path}/history.csv`

| Column | Type | Description |
|--------|------|-------------|
| `Date` | date | Event date (`YYYY-MM-DD`) |
| `EntityID` | string | Identifier that links related events |
| `Name` | string | Entity name |
| `Type` | string | Event type such as medication, supplement, condition, or symptom |
| `Event` | string | Event description |
| `Details` | string | Additional context |
| `RelatedEntity` | string | Optional reference to another entity |

Use `history.csv` for longitudinal analysis, change tracking, and event correlation.

**Entity registry**: `{health_log_path}/entities.json`

Use it to resolve entity IDs and metadata quickly.

**Daily entries**: `{health_log_path}/entries/`

Use per-date entry files for granular inspection of specific days.

**Narrative log**: `{health_log_path}/health_log.md`

Use the markdown journal for full chronological context and free-text details.

### Medical Exam Summaries

**Directory**: `{exams_path}/*/*.summary.md`

Each exam summary includes YAML frontmatter such as `exam_type`, `exam_date`, `body_region`, and `provider`.

### 23andMe Genetics Data

**File**: `{genetics_23andme_path}` (typically `23andme_raw_data.txt`)

This is a tab-separated file with roughly 631,000 SNPs: `rsid`, `chromosome`, `position`, `genotype`.

Efficient access patterns:

```bash
grep "^rs12345" "{genetics_23andme_path}"
grep -E "^(rs123|rs456|rs789)" "{genetics_23andme_path}"
```

## Direct Analysis Workflow

Use direct file reads and filtered extraction.

- For labs, read `all.csv` and optionally `lab_specs.json` for canonicalization.
- For current status, use `current.yaml` first.
- For historical context, add `history.csv`, `entities.json`, `entries/`, and `health_log.md`.
- For imaging or exam questions, inspect matching `*.summary.md` files.
- For genetics, check the 23andMe raw file first, then use optional `selfdecode` credentials only if the selected profile includes them and the task requires imputed coverage.
- For tasks that require external APIs, use credentials from `~/.config/health-agent/.env` when available.

## Important Notes

- **Privacy**: Profile files contain paths to sensitive health data. Store them in `~/.config/health-agent/profiles/`; the repo only commits `profiles/template.yaml.example`.
- **Runtime env**: Optional API credentials belong in `~/.config/health-agent/.env`, not in the repo.
- **Demographics**: Use `date_of_birth` and `gender` when interpreting age- or sex-specific ranges.
- **Confidence scores**: Flag lab values with `confidence < 0.8` for manual verification.
- **Large files**: Prefer filtered extraction (`grep`, `rg`, `awk`, `head`) over reading large files wholesale.
- **Local-only outputs**: Write generated analyses under `.output/`.

## Maintenance

Keep [`README.md`](/Users/tsilva/repos/tsilva/health-agent/README.md) aligned with the current repo layout and supported workflow.
