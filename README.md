<div align="center">
  <img src="logo.png" alt="health-agent" width="300"/>

  # health-agent

  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

  **Unify lab results, medical exams, and health journals into actionable insights with Claude Code**

</div>

## Features

- **Unified Health Data Access** — Query labs, exams, and health journals from a single conversational interface
- **Profile-Based Configuration** — Support multiple users with separate data sources and demographics
- **Cross-Source Correlation** — Connect lab results with symptoms, treatments, and imaging findings across time
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
```

### 2. Start a Session

Open Claude Code in this directory. You'll be prompted to select a profile.

### 3. Query Your Health Data

```
"Show me my cholesterol trends over the past year"
"Find all symptoms related to episode_003"
"What did my last ultrasound show?"
"Correlate my fatigue entries with my iron levels"
```

## Data Sources

| Parser | Output | Description |
|--------|--------|-------------|
| [labs-parser](https://github.com/tsilva/labs-parser) | `all.csv` | Lab test results with values, units, reference ranges |
| [medical-exams-parser](https://github.com/tsilva/medical-exams-parser) | `*.summary.md` | Imaging and exam transcriptions with YAML metadata |
| [health-log-parser](https://github.com/tsilva/health-log-parser) | `health_log.md` + `health_timeline.csv` | Health journal entries and structured timeline |

## Built-in Skills

Health Agent includes 7 analysis skills that activate automatically based on your queries:

| Skill | Trigger Phrases | Description |
|-------|-----------------|-------------|
| **lab-trend** | "track my glucose", "cholesterol trend", "how has my TSH changed" | Analyze longitudinal trends for specific biomarkers |
| **out-of-range-labs** | "abnormal labs", "which labs are out of range", "labs that need attention" | Identify and prioritize abnormal lab values by severity |
| **exam-catalog** | "list my exams", "find my MRI", "show ultrasounds" | Index and search medical imaging records |
| **episode-investigation** | "tell me about episode_001", "investigate my cold", "what happened with my back pain" | Deep-dive into health episodes across all data sources |
| **health-summary** | "summarize my health", "doctor visit prep", "health overview for 2024" | Generate comprehensive reports for provider visits |
| **cross-temporal-correlation** | "correlation between X and Y", "patterns in my data", "do symptoms affect labs" | Discover patterns between events and biomarkers |
| **medication-supplements** | "my medications", "medication list", "what supplements am I taking", "current meds" | Generate medication and supplement reports with active/discontinued status |

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
│           ├── lab-trend/SKILL.md
│           ├── out-of-range-labs/SKILL.md
│           ├── exam-catalog/SKILL.md
│           ├── episode-investigation/SKILL.md
│           ├── health-summary/SKILL.md
│           ├── cross-temporal-correlation/SKILL.md
│           ├── medication-supplements/SKILL.md
│           └── references/
│               └── common-markers.md  # Lab marker aliases and ranges
└── README.md
```

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

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- Output from one or more supported parsers:
  - [labs-parser](https://github.com/tsilva/labs-parser)
  - [medical-exams-parser](https://github.com/tsilva/medical-exams-parser)
  - [health-log-parser](https://github.com/tsilva/health-log-parser)

## License

[MIT](LICENSE)
