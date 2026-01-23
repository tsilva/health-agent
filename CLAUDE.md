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

For the full protocol details, see **Session Start Protocol** below.

## Health State System

The health state system transforms health-agent from a reactive analysis tool into a proactive Health OS with persistent understanding across sessions.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 INTERACTIVE DASHBOARD                        │
│  /health-dashboard or session start                          │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ AskUserQuestion │───▶│ Profile Select  │                 │
│  └─────────────────┘    └────────┬────────┘                 │
│                                  ▼                           │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ AskUserQuestion │───▶│ State Init?     │                 │
│  └─────────────────┘    └────────┬────────┘                 │
│                                  ▼                           │
│  ┌────────────────────────────────────────┐                 │
│  │        VISUAL DASHBOARD                 │                 │
│  │  • Conditions & confidence             │                 │
│  │  • Top actions (prioritized)           │                 │
│  │  • Medications / Supplements           │                 │
│  │  • Goals & progress                    │                 │
│  │  • Recent activity                     │                 │
│  └────────────────────┬───────────────────┘                 │
│                       ▼                                      │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │ AskUserQuestion │───▶│ Action Menu     │                 │
│  └─────────────────┘    │ • Review data   │                 │
│                         │ • Investigate   │                 │
│                         │ • Track labs    │                 │
│                         │ • Provider visit│                 │
│                         └─────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   .state/{profile}/           │
              │   health-state.yaml           │
              │                               │
              │   • Conditions & hypotheses   │
              │   • Biomarker baselines       │
              │   • Active actions            │
              │   • Intervention outcomes     │
              │   • Last sync timestamps      │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Continuous Interaction      │
              │                               │
              │   "What should I do next?"    │
              │   "I completed the EMA test"  │
              │   "Update my ferritin result" │
              └───────────────────────────────┘
```

### State File Location

State files are stored at `.state/{profile}/health-state.yaml`. The template at `.state/_template/health-state.yaml` documents the schema.

### Key State Components

| Component | Purpose |
|-----------|---------|
| `conditions` | Active health conditions with hypotheses and confidence |
| `biomarker_baselines` | Personal "normal" values vs population reference |
| `genetics` | Key genetic findings cached from investigations |
| `medications` / `supplements` | Current medications with monitoring markers |
| `actions` | Prioritized next steps (recommended/accepted/in_progress) |
| `completed_actions` | What was tried and outcomes (keeps last 20) |
| `declined_actions` | Actions user declined (don't re-recommend) |
| `goals` | Health goals with progress tracking |
| `last_sync` | Timestamps of last processed data from each source |

### Relationship to health_log.csv

**These are complementary, not redundant:**

| Aspect | health_log.csv | health-state.yaml |
|--------|----------------|-------------------|
| **Purpose** | Record events | Synthesize understanding |
| **Content** | "What happened" | "What it means + what to do" |
| **Maintained by** | User | Agent |
| **Update pattern** | Append events | Revise current state |
| **Time scope** | Full history | Current snapshot |

**health_log.csv** = raw input (events as they happen)
**health-state.yaml** = derived output (synthesized understanding)

Data flows one direction:
```
health_log.csv  ─┐
labs/all.csv    ─┼──→ Agent reasoning ──→ health-state.yaml
exams/*.md      ─┤
genetics        ─┘
```

## Session Start Protocol

**Recommended**: Use the interactive `health-dashboard` skill which handles all of this with `AskUserQuestion` for a guided experience.

If implementing manually, after profile selection:

1. **Profile Selection** (use AskUserQuestion):
   ```json
   {
     "questions": [{
       "question": "Which health profile would you like to use?",
       "header": "Profile",
       "options": [/* dynamically populate from profiles/*.yaml */],
       "multiSelect": false
     }]
   }
   ```

2. **Check if state file exists**:
   ```bash
   test -f ".state/{profile}/health-state.yaml" && echo "EXISTS" || echo "MISSING"
   ```

3. **If state file missing**: Use AskUserQuestion to offer initialization:
   ```json
   {
     "questions": [{
       "question": "Your health state hasn't been initialized. Set it up now?",
       "header": "Setup",
       "options": [
         {"label": "Yes, initialize (Recommended)", "description": "Create state from existing data"},
         {"label": "Skip for now", "description": "Proceed without persistent tracking"}
       ],
       "multiSelect": false
     }]
   }
   ```

4. **If state file exists**: Use AskUserQuestion for health check:
   ```json
   {
     "questions": [{
       "question": "Run health check to review your status?",
       "header": "Check",
       "options": [
         {"label": "Yes, run check (Recommended)", "description": "Check for new data and review status"},
         {"label": "Skip", "description": "Go directly to your request"}
       ],
       "multiSelect": false
     }]
   }
   ```
   - If yes: Run Health Check Routine, then display dashboard
   - If skip: Proceed to user's request

### Health Check Routine

1. **Load state file**: Read `.state/{profile}/health-state.yaml`

2. **Check data freshness**:
   ```bash
   # Get last modified times of data sources
   stat -f "%Sm" "{labs_path}/all.csv"
   stat -f "%Sm" "{health_log_path}/health_log.csv"
   ```
   Compare to `last_sync` timestamps in state file.

3. **If new data detected**:
   - Extract new entries since last sync
   - Check for anomalies (out of reference range, trend changes)
   - Report findings

4. **Present status summary**:
   - Active conditions with confidence levels
   - Top 3 pending actions (prioritized)
   - Goal progress
   - Any actions past due date

5. **Update last_sync timestamps** after processing

### State Initialization (Bootstrap)

When `.state/{profile}/health-state.yaml` doesn't exist:

1. **Ask user**: "Would you like to initialize your health state? This will create a persistent record of your health understanding."

2. **If yes, gather from existing data**:

   **Conditions**: Read recent investigations in `.output/{profile}/` → extract conditions and hypotheses
   ```bash
   find .output/{profile} -name "consensus-final.md" | head -5
   ```

   **Biomarker baselines**: Query labs for markers with 3+ values → calculate personal baseline (median of recent values)

   **Medications/supplements**: Query health_log.csv for active medications (use `.claude/skills/health-agent/references/status-keywords.md`)

   **Genetics**: Read any previous SNP lookups from investigation reports

   **Actions**: Extract "Recommended follow-up" from most recent investigation consensus

3. **Create state file** at `.state/{profile}/health-state.yaml` using Write tool

4. **Create directory first**:
   ```bash
   mkdir -p .state/{profile}
   ```

5. **Confirm**: "Health state initialized with X conditions, Y active actions. Run health check?"

## State Maintenance

### Update Behavior: Proactive with Confirmation

The agent should **proactively offer** to update state, not wait for explicit requests:

- After discussion implies state change → "Should I update your health state to reflect [X]?"
- User says "I did X" → Offer to record it
- Investigation completes → "I'll add these actions to your health state"

This keeps state current without requiring user to remember to ask.

### When to Update State

Update `.state/{profile}/health-state.yaml` when:

| Trigger | State Update |
|---------|--------------|
| Investigation completes | Add/update condition, generate actions |
| User reports completing action | Move to completed_actions with outcome |
| New lab results discussed | Update biomarker_baselines if significant |
| User starts/stops medication | Update medications/supplements |
| Goal progress changes | Update goals.progress |
| User declines an action | Add to declined_actions |

### Action Lifecycle

```
recommended → accepted → in_progress → completed
      │                                    │
      ▼                                    ▼
  declined                          outcome recorded
      │                                    │
      ▼                                    ▼
(don't re-recommend               confidence updated
 unless reconsider_if met)        new actions generated
```

**When completing an action**:
1. Record outcome (positive/negative/inconclusive)
2. Note impact on hypotheses
3. Generate follow-up actions if needed
4. Update condition confidence if outcome changes understanding

**When declining an action**:
1. Record reason
2. Note "reconsider_if" conditions
3. Don't re-recommend unless conditions change

### Biomarker Baselines

Personal baselines differ from population references when:
- Chronic condition causes stable deviation (e.g., elevated bilirubin in hemolysis)
- User has consistently different "normal" (e.g., naturally low BP)

Update baselines when:
- Pattern established over 3+ measurements
- Investigation confirms cause of deviation

### State File Maintenance

Keep state file manageable:

- **completed_actions**: Keep last 20 entries
- **Archive annually**: Move completed_actions older than 1 year to `.state/{profile}/archive/completed-{year}.yaml`
- **Prune declined_actions**: Remove if `reconsider_if` conditions met, or after 2 years

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
    profile_id: ""  # Your SelfDecode profile UUID
    jwt_token: ""  # eyJhbGciOiJSUzI1NiIs... (from authorization header, without "JWT " prefix)
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
- If lab_specs.json is missing, skills use case-insensitive fuzzy matching on lab_name values

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

## Common Analysis Patterns

Query patterns for health data analysis (lab trends, abnormal values, episodes, medications, correlations, health summaries, exams, provider documentation) are documented in:
`.claude/skills/health-agent/references/analysis-patterns.md`

Read this file when performing data analysis tasks.

## Built-in Skills

Eight core skills provide specialized capabilities in `.claude/skills/health-agent/`.

### How to Use Skills

**IMPORTANT**: These are project-local skill instruction files, NOT globally-installed skills invocable via the `Skill` tool.

**To use a skill:**

1. **Read the SKILL.md file** for the skill you need:
   ```
   Read .claude/skills/health-agent/{skill-name}/SKILL.md
   ```

2. **Follow the instructions** in the skill file. Skills typically instruct you to either:
   - Execute specific commands/queries directly
   - Spawn a Task agent with a detailed prompt template
   - Follow a multi-step workflow

3. **For orchestration skills** (investigate-root-cause, prepare-provider-visit, generate-questionnaire):
   - The SKILL.md contains a prompt template for spawning `general-purpose` Task agents
   - Read the skill, then spawn the Tasks with the provided prompt structure

**Example - Using investigate-root-cause:**
```
1. Read .claude/skills/health-agent/investigate-root-cause/SKILL.md
2. Follow instructions to spawn 4 parallel Task agents (Phase 1), refinement agents (Phase 2.5), verification (Phase 3), consensus (Phase 4), and state update (Phase 5)
3. The skill provides complete prompt templates for each agent type
4. Investigation findings persist to .state/{profile}/health-state.yaml with prioritized actions
```

**Example - Using genetics-snp-lookup:**
```
1. Read .claude/skills/health-agent/genetics-snp-lookup/SKILL.md
2. Follow instructions to query SNPedia API for specific SNPs
3. Cache results as instructed
```

### Skill Locations

| Skill | Path |
|-------|------|
| `health-dashboard` | `.claude/skills/health-agent/health-dashboard/SKILL.md` |
| `genetics-snp-lookup` | `.claude/skills/health-agent/genetics-snp-lookup/SKILL.md` |
| `genetics-selfdecode-lookup` | `.claude/skills/health-agent/genetics-selfdecode-lookup/SKILL.md` |
| `genetics-validate-interpretation` | `.claude/skills/health-agent/genetics-validate-interpretation/SKILL.md` |
| `scientific-literature-search` | `.claude/skills/health-agent/scientific-literature-search/skill.md` |
| `investigate-root-cause` | `.claude/skills/health-agent/investigate-root-cause/SKILL.md` |
| `prepare-provider-visit` | `.claude/skills/health-agent/prepare-provider-visit/skill.md` |
| `generate-questionnaire` | `.claude/skills/health-agent/generate-questionnaire/SKILL.md` |

### External Integrations (APIs + Caching)

| Skill | Use When |
|-------|----------|
| `genetics-snp-lookup` | User asks to look up specific SNPs (e.g., "rs12345"), check pharmacogenomics genes (CYP2D6, CYP2C19, etc.), or query health risk variants (APOE, Factor V Leiden, etc.). Queries SNPedia API with 30-day caching. |
| `genetics-selfdecode-lookup` | User asks for imputed SNP data, SNP not found in 23andMe, or specifically requests SelfDecode lookup. Requires authenticated web scraping with 30-day caching. Provides ~20M+ imputed SNPs vs 631k raw. |
| `genetics-validate-interpretation` | User wants to validate genetic interpretations against SNPedia or cross-reference allele orientation. |
| `scientific-literature-search` | User asks to find research papers, verify biological mechanisms, or needs authoritative citations. Queries PubMed + Semantic Scholar with 30-day caching. Used automatically in root cause investigations. |

### Orchestration Workflows

| Skill | Use When |
|-------|----------|
| `health-dashboard` | Session start, `/health-dashboard` command, or user asks "show my health dashboard" or "health status". Interactive entry point using `AskUserQuestion` for profile selection, state initialization, dashboard display, and action menus. Primary session entry point. |
| `investigate-root-cause` | User asks "investigate root cause of [condition]", "why do I have [condition]", "find the cause of [symptom]", or "what's causing my [condition]". Runs 4 parallel agents (bottom-up, top-down, genetics-first, red team) with cross-agent refinement, interpretation validation, diagnostic gap penalties, epidemiological priors, and calibrated confidence with falsification criteria. |
| `prepare-provider-visit` | User asks to "prepare for doctor visit", "generate provider summary", or "create medical documentation". Intelligently orchestrates data gathering based on visit type (annual/specialist/follow-up/urgent) and generates coherent provider-appropriate narratives. |
| `generate-questionnaire` | User asks to create questionnaire or systematically augment health log data with structured gap analysis. |

### Analysis Patterns (Not Skills)

All health data analysis (lab trends, abnormal values, episodes, correlations, medications, health summaries, exams) is performed naturally using query patterns documented in the "Common Analysis Patterns" section above. These patterns combine bash commands (grep, awk) with Claude's reasoning to answer user questions directly.

### Shared References

`.claude/skills/health-agent/references/` contains shared resources:

**`lab-specs-helpers.sh`**:
- Helper functions for querying `{labs_path}/lab_specs.json`
- `get_canonical_name()` - Get standard name from any alias
- `build_grep_pattern()` - Build grep pattern from all aliases
- `get_primary_unit()` - Get standard unit for marker
- `get_conversion_factor()` - Convert between units

**`status-keywords.md`**:
- Status determination keywords (active, discontinued, suspected, resolved)
- Status classification algorithm for medications, supplements, conditions, and episodes
- Used when analyzing medication timelines and condition status

### Genetics Data Sources

Two genetics data sources are available:

**SNPedia** via `genetics-snp-lookup`:
- **Primary source**: Public API, no authentication required
- **Coverage**: 631k+ SNPs from 23andMe raw data
- **Interpretations**: Community-curated research summaries
- **Caching**: 30-day TTL

**SelfDecode** via `genetics-selfdecode-lookup` (optional):
- **Secondary source**: Authenticated web scraping
- **Coverage**: ~20M+ imputed SNPs (more than raw 23andMe)
- **Interpretations**: SelfDecode's health effect assessments
- **Caching**: 30-day TTL
- **Requires**: SelfDecode account + credentials in environment variables

**Lookup strategy**:
1. **First**: Check 23andMe raw data via `genetics-snp-lookup` (most reliable, directly genotyped)
2. **Second**: If SNP not found and SelfDecode is configured, check `genetics-selfdecode-lookup` for imputed data
3. **Always**: Use SNPedia for interpretation context (research citations, mechanisms)

**Supported variants**:
- **Drug metabolism**: CYP2D6, CYP2C19, CYP2C9, VKORC1, SLCO1B1, TPMT, DPYD
- **Health risks**: APOE, Factor V Leiden, HFE hemochromatosis, MTHFR, BRCA founder mutations

**Example user queries**:
- "Look up rs12345" → `genetics-snp-lookup`
- "Check my CYP2D6 status" → `genetics-snp-lookup`
- "What's my APOE genotype?" → `genetics-snp-lookup`
- "Check selfdecode for rs12345" → `genetics-selfdecode-lookup`
- "Look up imputed genotype for rs..." → `genetics-selfdecode-lookup`

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

## Provider Documentation System

Provider documentation is generated via the **`prepare-provider-visit` skill**, which intelligently orchestrates data gathering and generates coherent narratives based on visit type.

### Using prepare-provider-visit

When user asks to prepare documentation for a healthcare visit:
1. Read `.claude/skills/health-agent/prepare-provider-visit/skill.md`
2. Follow the skill instructions (typically spawns a Task agent with the provided prompt template)

The skill:

1. **Asks minimal questions**: Visit type (annual/specialist/follow-up/urgent) and specific concerns
2. **Smart defaults**: Automatically determines relevant sections based on visit type
3. **Intelligent data gathering**: Uses analysis patterns to extract medications, labs, events, conditions, and genetics (if relevant)
4. **Coherent narrative**: Generates connected prose, not concatenated sections
5. **Provider-appropriate**: Professional medical documentation style

### Output Structure

```
.output/{profile}/
├── provider-visit-{visit_type}-{YYYY-MM-DD}.md  # Generated by prepare-provider-visit
├── hypothesis-investigation-{condition}-{YYYY-MM-DD}.md  # Generated by investigate-root-cause
└── health-log-augmentation-{YYYY-MM-DD}.md  # Generated by generate-questionnaire
```

### Report Format

Provider visit summaries follow this structure:

```markdown
---
document_type: provider_visit_summary
visit_type: {annual|specialist|follow_up|urgent}
generated: {YYYY-MM-DD}
profile: {profile_name}
timeframe: {description}
---

# Provider Visit Summary
**Patient**: {name}
**Visit Type**: {type}
**Generated**: {date}

## Visit Context
{2-3 sentences on reason for visit and overall status}

## Current Medications & Supplements
{Narrative + table of active medications}

## Recent Health Events
{Grouped by category with narrative synthesis}

## Laboratory Results
{Abnormal values with interpretation}

## Active Medical Conditions
{Bulleted list with status}

## Relevant Genetic Findings (if applicable)
{Only included when directly relevant to visit purpose}

## Summary & Considerations
{2-4 key discussion points for provider}

---
*Generated by health-agent to support clinical decision-making.*
```

### Creating Output Directories

**Directory Creation** - Use Bash (works in sandbox):
```bash
mkdir -p .output/{profile}
```

**File Writing** - Use the `Write` tool, NOT Bash heredocs:
```
# CORRECT: Use Write tool for report files
Write tool with file_path=".output/{profile}/provider-visit-annual-2026-01-21.md"

# WRONG: Bash heredocs fail in sandbox mode
cat > file.md << 'EOF'  # This will fail with "operation not permitted"
```

The Write tool works in sandboxed mode for files within the project directory. Bash heredocs and redirections are blocked by sandbox restrictions.

## Root Cause Investigation

The `investigate-root-cause` skill automates comprehensive hypothesis generation and testing for health conditions using an ensemble of 4 parallel agents with different reasoning strategies.

### Invocation

**When to use** - User asks:
- "Investigate root cause of [condition]"
- "Why do I have [condition]?"
- "Find the cause of [symptom]"
- "What's causing my [condition]?"

**How to invoke**:
1. Read `.claude/skills/health-agent/investigate-root-cause/SKILL.md`
2. Follow the skill instructions to spawn agents across 7 phases

### How It Works

The investigation uses 4 parallel agents with different reasoning strategies, followed by refinement, verification, and state persistence:

**Phase 1**: Spawn 4 investigation agents in parallel:
- **Bottom-Up**: Data-driven pattern discovery (no preconceptions)
- **Top-Down**: Systematic differential diagnosis
- **Genetics-First**: Genetic etiology prioritization
- **Red Team**: Adversarial testing with alternative proposals

**Phase 2.5**: Cross-agent refinement - each agent reviews others' findings and revises

**Phase 3**: Evidence verification + interpretation validation (unit consistency, temporal logic, statistical reasonableness)

**Phase 4**: Consensus with calibrated confidence calculation including:
- Diagnostic gap penalty (reduces confidence for missing tests)
- Epidemiological priors (Bayesian adjustment for condition prevalence)
- Falsification criteria (what would confirm/refute each hypothesis)

**Phase 5**: Update Health State - persist findings to `.state/{profile}/health-state.yaml`:
- Add/update condition with hypotheses and confidence
- Generate prioritized actions from recommended follow-up
- Create/update goal for identifying root cause

**Output**: Saved to `.output/{profile}/investigation-{condition}-{date}/consensus-final.md`
**State**: Updated in `.state/{profile}/health-state.yaml`

### Output Format

Investigation reports include:
- **Ranked hypotheses** with fully calibrated confidence (±uncertainty)
- **Diagnostic gap assessment** (missing tests and their impact on confidence)
- **Epidemiological prior analysis** (prevalence-adjusted probabilities)
- **Supporting evidence** (verified citations with interpretation validation)
- **Contradictions addressed** (from cross-agent refinement)
- **Genetic analysis** (comprehensive check via SNPedia)
- **Biological mechanisms** with literature citations
- **Falsification criteria** (what would confirm/refute each hypothesis)
- **Counter-hypotheses** from Red Team
- **Blind spots detected** (causes no agent investigated)
- **Recommended follow-up** (ordered by cost/invasiveness)

### Key Features

- **4 independent reasoning strategies**: Reduces correlated errors
- **Cross-agent refinement**: Agents learn from each other's insights
- **Adversarial validation**: Red Team proposes alternatives, not just contradictions
- **Interpretation validation**: Catches unit errors, temporal violations, statistical overclaiming
- **Health state persistence**: Findings persist across sessions via health-state.yaml
- **Action generation**: Creates prioritized next steps from investigation recommendations
- **Diagnostic gap penalty**: Honest confidence when key tests unavailable
- **Epidemiological priors**: Rare conditions need stronger evidence
- **Falsification criteria**: Actionable next steps to confirm/refute
- **Calibrated confidence**: Calculated from metrics, not subjective assessment

### Example Output Summary

```
## Ensemble Investigation Complete

**Primary Hypothesis**: Hereditary Spherocytosis
**Calibrated Confidence**: 54% (±10%)
**Gap Penalty Applied**: -10.5% (missing EMA, Coombs, bone marrow)

### Key Falsification Criteria
**Would confirm**: Positive EMA binding test, clinical gene panel confirms ANK1/SPTB
**Would refute**: Positive direct Coombs (autoimmune), normal osmotic fragility
```

## Important Notes

- **Privacy**: Profile YAML files contain paths to sensitive health data. They are gitignored except for the template.
- **No Scripts**: This agent reads data files directly - no Python preprocessing required.
- **Demographics**: Use `date_of_birth` and `gender` when interpreting reference ranges, as many vary by age and sex.
- **Confidence Scores**: Lab values with low confidence (<0.8) should be flagged for manual verification.
- **Large File Handling**: Data files (`all.csv`, `health_log.csv`, `health_log.md`) typically exceed Claude's 256KB/25000 token read limits. Skills include "Efficient Data Access" sections with extraction commands. Always use filtered extraction (grep/head) rather than direct reads for these files.
- **Lab Specifications**: If `{labs_path}/lab_specs.json` exists, skills use it for more accurate marker matching via canonical names and aliases. Helper functions are in `.claude/skills/health-agent/references/lab-specs-helpers.sh`. If the file is missing, skills use case-insensitive fuzzy matching on lab_name values. This file is optional and generated by labs-parser.
- **Genetics Data**: Primary genetics interpretations come from SNPedia via `genetics-snp-lookup`. SelfDecode provides optional imputed SNP coverage via `genetics-selfdecode-lookup` (requires authentication). Both skills cache for 30 days.
- **Sandbox Compliance**: Always use the `Write` tool (not Bash heredocs/redirects) to create files in `.output/`. Bash `mkdir -p` works for directories, but file writing via `cat > file` or heredocs is blocked by sandbox. This ensures reports generate without permission errors.

## Maintenance

Keep README.md updated with any significant project changes.
