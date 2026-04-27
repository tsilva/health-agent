<div align="center">
  <img src="https://raw.githubusercontent.com/tsilva/health-agent/main/logo.png" alt="health-agent" width="512"/>

  # health-agent

  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Documentation](https://img.shields.io/badge/Docs-AGENTS.md-2d6cdf)](AGENTS.md)
  [![Data Sources](https://img.shields.io/badge/Data_Sources-8-orange)](#data-sources)

  **A skill-first health-autopilot layer: invoke the agent, let it read the parsed data, and have it write the current next-step plan.**

  [Documentation](AGENTS.md) · [Profile Template](profiles/template.yaml.example)

</div>

## Core Loop

`health-agent` assumes the real-world record is maintained outside this repo:

1. update the health log, labs, or exams in the upstream systems
2. run the parser repos so their output folders are current
3. tell the agent to use the `what-next-report` skill for your live profile
4. read the refreshed plan in `.output/<profile_slug>/`

This repo never asks the user to separately encode the same event again in repo-local JSON.

## Features

- **Skill-first autopilot**: the normal path is to invoke the repo skill through the agent and let it handle profile loading, source validation, reasoning, and report writing.
- **Concrete next-step planning**: rank the highest-value specialist, test, and treatment-path discussions.
- **Minimal repo-local memory**: keep per-profile derived state under `.state/profiles/<profile_slug>/` and rebuild or refresh it from current sources when helpful.
- **Profile-based runtime config**: point the agent at external parser outputs without storing raw health data in this repo.
- **Cross-source analysis**: correlate labs, exams, journal entries, symptoms, medications, experiments, and genetics over time.

## Quick Start

### 1. Create Your Runtime Profile

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
  schedule_md_path: "/path/to/daily-schedule.md"  # Optional
  nutrition_md_path: "/path/to/nutrition-plan.md"  # Optional
  exercise_md_path: "/path/to/exercise-plan.md"  # Optional
  lifestyle_constraints_md_path: "/path/to/lifestyle-constraints.md"  # Optional
```

### 2. Optional: Add API Keys

```bash
cp .env.example ~/.config/health-agent/.env
```

### 3. Invoke The Skill Through The Agent

From your AI coding assistant in this repo, use a prompt like:

```text
Use the what-next-report skill for profile myname and write the refreshed next-steps report.
```

For a probability-ranked differential, use:

```text
Use the root-cause-analysis skill for profile myname to find the top 5 most likely causes of recurring fatigue.
```

That is the primary interface for this repo.

### 4. Optional: Install The Local Helper

```bash
python3 -m pip install -e .[dev]
```

### 5. Keep Parser Outputs Current

When you add a health-log entry or new labs/exams, rerun the relevant parser repos so the configured output folders contain the latest parsed data.

### 6. Optional: Refresh The Deterministic Helper State Directly

```bash
health-agent plan --profile myname
```

The command:

- loads the live profile from `~/.config/health-agent/profiles/`
- validates each configured source as `available`, `missing`, `unreadable`, or `not configured`
- builds a compact evidence snapshot from the parsed outputs
- refreshes per-profile derived state
- writes the current action plan to `.output/<profile_slug>/`

Use the CLI only when you specifically want the internal deterministic helper path. Deprecated aliases `health-agent intake`, `health-agent review`, and `health-agent outcome-update` still route to `plan` temporarily, but they are not the primary workflow.

To build only the factual evidence-prep packet that the agent can use before reasoning:

```bash
health-agent evidence-packet --profile myname
```

This writes `.state/profiles/<profile_slug>/evidence-packet.json`. It captures source status, freshness, changed files, factual lab/log/exam extracts, medication and supplement mention lines, lifestyle summaries, and current issue/action memory. It does not generate diagnoses; the agent still does the reasoning.

To render a draft daily lifestyle plan from profile-linked Markdown sources:

```bash
health-agent daily-plan --profile myname --date 2026-04-16
```

This writes `.output/<profile_slug>/<YYYY-MM-DD>-<profile_slug>-daily-plan.md`. It reads the source Markdown files and applies the sidecar constraint file, but it does not edit any source file.

## Data Sources

| Source | Output | Description |
|--------|--------|-------------|
| [labs-parser](https://github.com/tsilva/labs-parser) | `all.csv`, `lab_specs.json`, dated source folders | Canonical lab index plus per-document verification artifacts |
| Standalone exams parser | profile-configured directory | Independent exam corpus; must be validated before use and may be unavailable |
| [health-log-parser](https://github.com/tsilva/health-log-parser) | `health_log.md`, `.state.json`, `entries/*.raw.md`, `entries/*.processed.md`, `entries/*.labs.md`, `entries/*.exams.md` | Chronological overview, parser state, and day-level journal/lab/exam context |
| 23andMe | Raw data download | Genetic variants for pharmacogenomics and health-risk interpretation |
| Lifestyle schedule | `schedule_md_path` Markdown file | Default daily schedule template, including wake/sleep, work, gym, meal, and supplement timing |
| Lifestyle nutrition | `nutrition_md_path` Markdown file | Default food plan template used for draft meal-plan regeneration |
| Lifestyle exercise | `exercise_md_path` Markdown file | Default exercise plan template used for draft workout regeneration |
| Lifestyle constraints | `lifestyle_constraints_md_path` Markdown file | Durable constraints, food triggers, targets, conflict precedence, and regeneration rules |

Lifestyle Markdown files are read-only source inputs. Keep stable rules in the sidecar constraints file instead of duplicating them into every generated plan. Generated drafts belong under `.output/`.

## Primary Interface

The canonical interface is the `what-next-report` skill through the agent.

For targeted probability-ranked differentials, use the `root-cause-analysis` skill.

The CLI exists only as an internal support tool for deterministic rescans and state rendering. It is not the main product surface.

## Repo-Local State

`.output/` is the product. `.state/` is internal engine memory.

The main per-profile derived artifacts are:

- `.state/profiles/<profile_slug>/sources.json`
- `.state/profiles/<profile_slug>/evidence-packet.json`
- `.state/profiles/<profile_slug>/issues.json`
- `.state/profiles/<profile_slug>/actions.json`
- `.output/<profile_slug>/<YYYY-MM-DD>-<profile_slug>-action-plan.md`
- `.output/<profile_slug>/<YYYY-MM-DD>-<profile_slug>-daily-plan.md`

The current plan report is the primary deliverable. The state files exist to support reranking, continuity, and deterministic rescans.

## Project Skills

This repo includes project-local Codex skills under `.codex/skills/`:

- `what-next-report`: canonical workflow for having the agent read the parsed record, produce the updated next-steps plan, and refresh per-profile issue/action memory when useful
- `root-cause-analysis`: generate a probability-ranked root-cause differential for a symptom, condition, abnormal marker, episode, or pattern, with probabilities adding to 100%
- `profile-question-report`: interactively ask high-yield unanswered questions and draft a paste-ready health-log entry
- `medication-history-report`: generate a dated medication and supplement history report

## Directory Structure

```text
health-agent/
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
├── .codex/
│   └── skills/
├── .output/
├── .state/
│   └── profiles/
│       └── <profile_slug>/
│           ├── actions.json
│           ├── issues.json
│           └── sources.json
├── profiles/
│   └── template.yaml.example
├── src/
│   └── health_agent/
├── tests/
│   └── test_cli.py
└── README.md
```

## Read-Only Sources

All profile-linked external sources are read-only. The agent should never modify files under configured `labs_path`, `exams_path`, `health_log_path`, or `genetics_23andme_path`.

## Data Privacy

- Runtime profiles live in `~/.config/health-agent/profiles/`, outside this repository.
- Optional API keys live in `~/.config/health-agent/.env`.
- No health data is stored in this repository by design, only paths to external sources plus derived repo-local state.
- 23andMe raw data should be processed locally.

## Requirements

- A local AI coding assistant or workflow that can follow [AGENTS.md](AGENTS.md)
- Output from one or more supported parsers:
  - [labs-parser](https://github.com/tsilva/labs-parser)
  - [medical-exams-parser](https://github.com/tsilva/medical-exams-parser)
  - [health-log-parser](https://github.com/tsilva/health-log-parser)
- Optional: 23andMe raw data download

## License

[MIT](LICENSE)
