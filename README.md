<div align="center">
  <img src="https://raw.githubusercontent.com/tsilva/health-agent/main/logo.png" alt="health-agent" width="512"/>

  # health-agent

  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Documentation](https://img.shields.io/badge/Docs-AGENTS.md-2d6cdf)](AGENTS.md)
  [![Data Sources](https://img.shields.io/badge/Data_Sources-4-orange)](#data-sources)

  **A central health-autopilot hub for diagnosis support, root-cause analysis, prescription-path suggestions, and longitudinal health reasoning.**

  [Documentation](AGENTS.md) · [Profile Template](profiles/template.yaml.example)

</div>

## Features

- **Health-autopilot workflow**: support longitudinal analysis, diagnostic reasoning, root-cause investigation, and quality-of-life optimization.
- **Concrete next-step planning**: suggest the right specialist path, likely prescription discussions, and evidence-backed follow-up actions.
- **Profile-based runtime config**: point the agent at external health-data exports without storing the raw data in this repo.
- **Cross-source analysis**: correlate lab trends, exam findings, journal entries, symptoms, medications, experiments, and genetics over time.
- **Privacy-first layout**: live runtime config stays under `~/.config/health-agent/`, external data sources are read-only, and generated `.output/` artifacts stay repo-local.

## Quick Start

### 1. Create Your Config Directory

```bash
mkdir -p ~/.config/health-agent/profiles
cp profiles/template.yaml.example ~/.config/health-agent/profiles/myname.yaml
```

Edit `~/.config/health-agent/profiles/myname.yaml`:

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

### 2. Optional: Add API Keys

```bash
cp .env.example ~/.config/health-agent/.env
```

Edit `~/.config/health-agent/.env` if you want features like the higher PubMed rate limit.

### 3. Start a Session

Open your local AI coding assistant in this directory and have it follow [AGENTS.md](AGENTS.md) or `CLAUDE.md`.

The runtime workflow is:

1. Read a profile from `~/.config/health-agent/profiles/*.yaml`.
2. If no live profile exists, stop and ask for one. Do not fall back to repo-local `profiles/*.yaml`.
3. Extract the data-source paths from that profile.
4. Validate each source as `available`, `missing`, `unreadable`, or `not configured`.
5. Optionally load environment variables from `~/.config/health-agent/.env`.
6. Query those external parser outputs directly.

### 4. Ask Natural Questions

```text
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

| Source | Output | Description |
|--------|--------|-------------|
| [labs-parser](https://github.com/tsilva/labs-parser) | `all.csv`, `lab_specs.json`, dated source folders | Canonical lab index plus per-document verification artifacts |
| Standalone exams parser | profile-configured directory | Independent exam corpus; must be validated before use and may be unavailable |
| [health-log-parser](https://github.com/tsilva/health-log-parser) | `health_log.md`, `.state.json`, `entries/*.raw.md`, `entries/*.processed.md`, `entries/*.labs.md`, `entries/*.exams.md` | Chronological overview, parser state, and day-level journal/lab/exam context |
| 23andMe | Raw data download | Genetic variants for pharmacogenomics and health-risk interpretation |

## How It Works

This repository is a lightweight instruction layer around external health-data exports. The agent reads a live profile from `~/.config/health-agent/profiles/`, validates each configured source, optionally loads `~/.config/health-agent/.env`, and performs analysis directly against the exported files.

## Directory Structure

```text
health-agent/
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
├── LICENSE
├── README.md
├── health-agent.code-workspace
├── logo.png
└── profiles/
    └── template.yaml.example
```

```text
~/.config/health-agent/
├── .env
└── profiles/
    └── {name}.yaml
```

## Output Files

Generated notes or reports should be written under `.output/` so they stay local and ignored by git.

## Read-Only Sources

All profile-linked external sources are read-only. The agent should never modify files under configured `labs_path`, `exams_path`, `health_log_path`, or `genetics_23andme_path`.

## Data Privacy

- Runtime profiles live in `~/.config/health-agent/profiles/`, outside this repository.
- Optional API keys live in `~/.config/health-agent/.env`.
- `profiles/template.yaml.example` is the committed example file.
- No health data is stored in this repository by design, only paths to external sources.
- 23andMe raw data should be processed locally.
- Demographics such as date of birth and gender enable age- and sex-aware interpretation.

## Requirements

- A local AI coding assistant or workflow that can follow [AGENTS.md](AGENTS.md)
- Output from one or more supported parsers:
  - [labs-parser](https://github.com/tsilva/labs-parser)
  - [medical-exams-parser](https://github.com/tsilva/medical-exams-parser)
  - [health-log-parser](https://github.com/tsilva/health-log-parser)
- Optional: 23andMe raw data download

## License

[MIT](LICENSE)
