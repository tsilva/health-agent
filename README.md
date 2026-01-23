<div align="center">
  <img src="logo.png" alt="health-agent" width="512"/>

  # health-agent

  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Claude Code](https://img.shields.io/badge/Claude_Code-Agent-8A2BE2)](https://claude.ai/code)
  [![Skills](https://img.shields.io/badge/Skills-6-green)](CLAUDE.md)
  [![Data Sources](https://img.shields.io/badge/Data_Sources-4-orange)](#data-sources)

  **🩺 Unify lab results, medical exams, and health journals into actionable insights with Claude Code 📊**

  [Documentation](CLAUDE.md) · [Profile Template](profiles/_template.yaml)

</div>

## Features

- **Natural Language Health Queries** — Ask questions in plain English; no need to memorize skill names or commands
- **Unified Health Data Access** — Query labs, exams, health journals, and genetic data from a single conversational interface
- **23andMe Genetics Integration** — SNP lookups, pharmacogenomics analysis, and health risk variant interpretation via SNPedia
- **Profile-Based Configuration** — Support multiple users with separate data sources and demographics
- **Cross-Source Correlation** — Connect lab results, genetics, symptoms, treatments, and imaging findings across time
- **Literature-Backed Analysis** — Root cause investigations include authoritative citations from PubMed and Semantic Scholar
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

### 3. Ask Natural Questions

```
"Show me my cholesterol trends over the past year"
"What abnormal labs do I have in the last 6 months?"
"Find all symptoms related to episode_003"
"What did my last ultrasound show?"
"Does my fatigue correlate with my iron levels?"
"What's my CYP2D6 metabolizer status?"
"Look up my APOE genotype"
"Investigate the root cause of my elevated bilirubin"
"Prepare a summary for my doctor's appointment next week"
```

## Data Sources

| Parser | Output | Description |
|--------|--------|-------------|
| [labs-parser](https://github.com/tsilva/labs-parser) | `all.csv` | Lab test results with values, units, reference ranges |
| [medical-exams-parser](https://github.com/tsilva/medical-exams-parser) | `*.summary.md` | Imaging and exam transcriptions with YAML metadata |
| [health-log-parser](https://github.com/tsilva/health-log-parser) | `health_log.md` + `health_log.csv` | Health journal entries and structured timeline |
| 23andMe | Raw data download | Genetic variants for pharmacogenomics and health risks |

## Core Capabilities

Health Agent provides 6 specialized skills for complex workflows, plus natural language analysis for everyday queries.

### External Integrations (APIs + Caching)

| Capability | When It's Used | Description |
|------------|----------------|-------------|
| **genetics-snp-lookup** | "Look up rs12345", "Check my CYP2D6 status", "What's my APOE genotype?" | Queries SNPedia API for genetic variant interpretations. Handles SNP lookups, pharmacogenomics genes (CYP2D6, CYP2C19, etc.), and health risk variants (APOE, Factor V Leiden, etc.). Results cached for 30 days. |
| **genetics-validate-interpretation** | Validating genetic interpretations or cross-referencing allele orientation | Validates genetic findings against SNPedia and verifies allele orientation for accuracy. |
| **scientific-literature-search** | "Find papers on X mechanism", automatic use in root cause investigations | Queries PubMed and Semantic Scholar for authoritative research citations. Used automatically to validate biological mechanisms in hypothesis investigations. Results cached for 30 days. |

### Orchestration Workflows

| Capability | When It's Used | Description |
|------------|----------------|-------------|
| **investigate-root-cause** | "Investigate root cause of [condition]", "Why do I have [symptom]?", "What's causing my [abnormal finding]?" | Multi-turn hypothesis investigation with evidence gathering, literature-backed mechanism validation, comprehensive genetic analysis, and ranked competing explanations. Saves detailed reports to `.output/`. |
| **prepare-provider-visit** | "Prepare for my doctor visit", "Generate a summary for my appointment", "Create medical documentation" | Intelligent orchestration of medications, labs, health events, conditions, and genetics (when relevant) into coherent provider-appropriate narratives. Adapts content based on visit type (annual/specialist/follow-up/urgent). |
| **generate-questionnaire** | "Create questionnaire", "Systematically augment health log data" | Generates comprehensive questionnaires to identify gaps in health log data and systematically collect missing information. |

### Natural Language Analysis

All other health data analysis is performed naturally through conversational queries:

- **Lab trends** — "How has my HbA1c changed over time?"
- **Abnormal values** — "What labs are out of range?"
- **Episode investigation** — "Tell me about my headache episode"
- **Temporal correlations** — "Does stress correlate with my blood pressure?"
- **Medication tracking** — "What am I currently taking?"
- **Health summaries** — "Summarize my health in 2024"
- **Exam searches** — "List my imaging studies"

These queries use bash patterns (grep, awk) combined with Claude's reasoning—no separate skills required.

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
│           ├── genetics-snp-lookup/SKILL.md
│           ├── genetics-validate-interpretation/SKILL.md
│           ├── investigate-root-cause/SKILL.md
│           ├── prepare-provider-visit/SKILL.md
│           ├── scientific-literature-search/SKILL.md
│           └── references/
│               ├── data-access-helpers.sh         # Standardized data extraction functions
│               ├── lab-specs-helpers.sh           # Helper functions for lab_specs.json
│               └── status-keywords.md             # Status determination keywords
└── README.md
```

## Output Directory Structure

Generated reports and analyses are saved to `.output/{profile}/`:

```
.output/{profile}/
├── provider-visit-{visit_type}-YYYY-MM-DD.md     # Provider summaries
├── hypothesis-investigation-{condition}-YYYY-MM-DD.md  # Root cause analyses
└── health-log-augmentation-YYYY-MM-DD.md         # Questionnaires
```

The `.output/` directory is gitignored to protect sensitive health data.

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

- [Claude Code](https://claude.ai/code) CLI
- Output from one or more supported parsers:
  - [labs-parser](https://github.com/tsilva/labs-parser)
  - [medical-exams-parser](https://github.com/tsilva/medical-exams-parser)
  - [health-log-parser](https://github.com/tsilva/health-log-parser)
- Optional: 23andMe raw data download (Settings > 23andMe Data > Download Raw Data)

## License

[MIT](LICENSE)
