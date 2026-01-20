<div align="center">
  <img src="logo.png" alt="health-agent" width="300"/>

  # health-agent

  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

  **Unify lab results, medical exams, and health journals into actionable insights with Claude Code**

</div>

## Features

- **Unified Health Data Access** — Query labs, exams, health journals, and genetic data from a single conversational interface
- **23andMe Genetics Integration** — Pharmacogenomics analysis and health risk variant interpretation
- **Profile-Based Configuration** — Support multiple users with separate data sources and demographics
- **Cross-Source Correlation** — Connect lab results, genetics, symptoms, treatments, and imaging findings across time
- **Skill-Extensible** — Create custom analysis skills for recurring health queries
- **Privacy-First Design** — No health data stored in repo; profile paths are gitignored by default

## Quick Start

### 1. Create a Profile

```bash
cp profiles/_template.yaml profiles/myname.yaml
```

Edit `profiles/myname.yaml`:

```yaml
name: "Your Name"
demographics:
  date_of_birth: "1990-01-15"
  gender: "male"

data_sources:
  labs_path: "/path/to/labs-parser/output/"
  exams_path: "/path/to/medical-exams-parser/output/"
  health_log_path: "/path/to/health-log-parser/output/"
  genetics_23andme_path: "/path/to/23andme_raw_data.txt"  # Optional
```

### 2. Start a Session

Open Claude Code in this directory. You'll be prompted to select a profile.

### 3. Query Your Health Data

```
"Show me my cholesterol trends over the past year"
"Find all symptoms related to episode_003"
"What did my last ultrasound show?"
"Correlate my fatigue entries with my iron levels"
"What's my CYP2D6 metabolizer status?"
"Look up my APOE genotype"
```

## Data Sources

| Parser | Output | Description |
|--------|--------|-------------|
| [labs-parser](https://github.com/tsilva/labs-parser) | `all.csv` | Lab test results with values, units, reference ranges |
| [medical-exams-parser](https://github.com/tsilva/medical-exams-parser) | `*.summary.md` | Imaging and exam transcriptions with YAML metadata |
| [health-log-parser](https://github.com/tsilva/health-log-parser) | `health_log.md` + `health_log.csv` | Health journal entries and structured timeline |
| 23andMe | Raw data download | Genetic variants for pharmacogenomics and health risks |

## Built-in Skills

Health Agent includes 21 skills that activate automatically based on your queries:

### Data Collection Skills

| Skill | Trigger Phrases | Description |
|-------|-----------------|-------------|
| **generate-questionnaire** | "create questionnaire", "generate questionnaire", "augment health log", "systematically fill gaps" | Generate comprehensive questionnaires to systematically augment health log data |

### Core Analysis Skills

| Skill | Trigger Phrases | Description |
|-------|-----------------|-------------|
| **lab-trend** | "track my glucose", "cholesterol trend", "how has my TSH changed" | Analyze longitudinal trends for specific biomarkers |
| **out-of-range-labs** | "abnormal labs", "which labs are out of range", "labs that need attention" | Identify and prioritize abnormal lab values by severity |
| **exam-catalog** | "list my exams", "find my MRI", "show ultrasounds" | Index and search medical imaging records |
| **episode-investigation** | "tell me about episode_001", "investigate my cold", "what happened with my back pain" | Deep-dive into health episodes across all data sources |
| **health-summary** | "summarize my health", "doctor visit prep", "health overview for 2024" | Generate comprehensive reports for provider visits |
| **cross-temporal-correlation** | "correlation between X and Y", "patterns in my data", "do symptoms affect labs" | Discover patterns between events and biomarkers |
| **medication-supplements** | "my medications", "medication list", "what supplements am I taking", "current meds" | Generate medication and supplement reports with active/discontinued status |

### Genetics Skills

| Skill | Trigger Phrases | Description |
|-------|-----------------|-------------|
| **genetics-snp-lookup** | "look up rs12345", "my genotype for...", "check SNP" | Query specific genetic variants from 23andMe data |
| **genetics-pharmacogenomics** | "drug metabolism", "CYP2D6 status", "how do I metabolize medications" | Analyze variants affecting drug metabolism (CYP2D6, CYP2C19, etc.) |
| **genetics-health-risks** | "APOE status", "genetic risks", "Factor V Leiden", "MTHFR" | Interpret health risk variants with clinical context |

### Hypothesis Investigation Skills

| Skill | Trigger Phrases | Description |
|-------|-----------------|-------------|
| **investigate-root-cause** | "investigate root cause of...", "why do I have...", "find the cause of...", "what's causing my..." | Automated hypothesis generation and testing for health conditions with multi-turn iterative exploration |
| **mechanism-search** | "biological mechanism linking...", "how does X cause Y", "pathway between..." | Identify biological pathways and mechanisms connecting observations |
| **confound-identification** | "what could confound...", "alternative explanations for...", "what else could cause..." | Identify confounding factors that could explain correlations |
| **evidence-contradiction-check** | "test hypothesis against data", "contradictions to...", "evidence against..." | Search for counter-examples and contradictory evidence |

### Report Skills

| Skill | Trigger Phrases | Description |
|-------|-----------------|-------------|
| **report-medication-list** | "medication list for doctor", "generate med report" | Generate provider-ready medication and supplement list |
| **report-labs-abnormal** | "abnormal labs report", "labs summary for provider" | Generate provider-ready abnormal labs summary |
| **report-health-events** | "health events report", "recent health timeline" | Generate provider-ready health events timeline |
| **report-pharmacogenomics** | "pharmacogenomics report for doctor" | Generate provider-ready pharmacogenomics summary |
| **report-genetic-risks** | "genetic risks for provider" | Generate provider-ready health risks summary |
| **report-conditions-status** | "conditions report", "active diagnoses", "medical conditions list" | Generate provider-ready active/resolved conditions summary |

## Directory Structure

```
health-agent/
├── CLAUDE.md                          # Agent instructions and data schemas
├── profiles/
│   ├── _template.yaml                 # Profile template
│   └── {name}.yaml                    # User profiles (gitignored)
├── .claude/
│   └── skills/
│       └── health-agent/
│           ├── generate-questionnaire/SKILL.md
│           ├── lab-trend/SKILL.md
│           ├── out-of-range-labs/SKILL.md
│           ├── exam-catalog/SKILL.md
│           ├── episode-investigation/SKILL.md
│           ├── health-summary/SKILL.md
│           ├── cross-temporal-correlation/SKILL.md
│           ├── medication-supplements/SKILL.md
│           ├── genetics-snp-lookup/SKILL.md
│           ├── genetics-pharmacogenomics/SKILL.md
│           ├── genetics-health-risks/SKILL.md
│           ├── investigate-root-cause/SKILL.md
│           ├── mechanism-search/SKILL.md
│           ├── confound-identification/SKILL.md
│           ├── evidence-contradiction-check/SKILL.md
│           ├── report-medication-list/SKILL.md
│           ├── report-labs-abnormal/SKILL.md
│           ├── report-health-events/SKILL.md
│           ├── report-pharmacogenomics/SKILL.md
│           ├── report-genetic-risks/SKILL.md
│           ├── report-conditions-status/SKILL.md
│           └── references/
│               ├── common-markers.md              # Lab marker aliases and ranges
│               ├── genetics-pharmacogenomics.md   # Drug metabolism variants
│               ├── genetics-health-risks.md       # Health risk variants
│               ├── genetics-snp-index.md          # Master SNP lookup
│               └── status-keywords.md             # Status determination keywords
└── README.md
```

## Output Directory Structure

Generated reports, questionnaires, and analyses are saved to `.output/{profile}/`:

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

**Note**: The `.output/` directory is gitignored to protect sensitive health data.

## Creating Custom Skills

Create additional skills in `~/.claude/skills/` or `.claude/skills/` for custom analyses:

```markdown
---
name: my-custom-analysis
description: "Describe what this skill does and trigger phrases"
---

# My Custom Analysis

Instructions for performing the analysis...
```

## Data Privacy

- Profile YAML files contain paths to sensitive health data
- All profiles except `_template.yaml` are gitignored
- No health data is stored in this repository—only paths to external sources
- Demographics (DOB, gender) enable age/sex-specific reference range interpretation
- 23andMe raw data files are processed locally; genetic data never leaves your machine

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- Output from one or more supported parsers:
  - [labs-parser](https://github.com/tsilva/labs-parser)
  - [medical-exams-parser](https://github.com/tsilva/medical-exams-parser)
  - [health-log-parser](https://github.com/tsilva/health-log-parser)
- Optional: 23andMe raw data download (Settings > 23andMe Data > Download Raw Data)

## License

[MIT](LICENSE)
