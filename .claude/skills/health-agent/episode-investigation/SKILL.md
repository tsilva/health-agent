---
name: episode-investigation
description: Deep-dive into a health episode by gathering all related events, labs, exams, and narrative context. Use when user asks to "tell me about episode_001", "investigate my cold", "what happened with my back pain", "analyze that infection", or wants comprehensive context around a health event.
---

# Episode Investigation

Comprehensive investigation of a health episode across all data sources.

## Workflow

1. Get all data paths from the loaded profile
2. Identify the episode:
   - By `episode_id` (e.g., "episode_001")
   - By keyword search in timeline events
3. Gather related data from all sources
4. Build chronological narrative
5. Synthesize findings

## Efficient Data Access

Data files often exceed Claude's 256KB read limit. Use these extraction patterns:

### Timeline: Extract by Episode ID
```bash
head -1 "{health_log_path}/health_log.csv" && grep "{episode_id}" "{health_log_path}/health_log.csv"
```

### Timeline: Search by Keyword
```bash
head -1 "{health_log_path}/health_log.csv" && grep -i "{keyword}" "{health_log_path}/health_log.csv"
```

### Narrative: Extract Date Range
```bash
grep -A 20 "^# {YYYY-MM-DD}" "{health_log_path}/health_log.md"
```
Repeat for each date in the episode range.

### Labs: Extract Date Range (±7 days)
```bash
head -1 "{labs_path}/all.csv" && grep "^{YYYY-MM}" "{labs_path}/all.csv"
```

## Data Gathering

### Timeline Events
1. Read `{health_log_path}/health_timeline.csv`
2. Find events matching `episode_id` OR search `event` column
3. Note date range of the episode

### Health Log Narrative
1. Read `{health_log_path}/health_log.md`
2. Extract entries from the episode date range
3. Pull detailed context and subjective descriptions

### Related Labs
1. Read `{labs_path}/all.csv`
2. Find labs within ±7 days of episode events
3. Highlight any abnormal values during this period

### Related Exams
1. List `{exams_path}/*.summary.md`
2. Find exams with dates within the episode range
3. Include relevant findings

## Output Format

```
## Episode Investigation: {episode_id or description}

**Date Range**: {start_date} to {end_date}
**Categories**: {list of event categories involved}

### Timeline
| Date       | Category   | Event                      |
|------------|------------|----------------------------|
| 2024-03-01 | symptom    | Sore throat onset          |
| 2024-03-02 | medication | Started amoxicillin        |
| 2024-03-07 | symptom    | Symptoms resolved          |

### Narrative Context
{Relevant excerpts from health_log.md}

### Labs During Episode (±7 days)
| Date       | Marker | Value | Status |
|------------|--------|-------|--------|
| 2024-03-02 | WBC    | 12.5  | HIGH   |

### Related Exams
- 2024-03-02: Throat culture (positive for strep)

### Analysis
{Synthesized narrative of the episode:
- What triggered it
- How it progressed
- Treatment response
- Outcome
- Any lingering concerns}
```

## Search Strategies

When user provides a description instead of episode_id:
1. Search `event` column for keywords
2. Search `category` for related types
3. Look for clustered events in date range
4. Check health_log.md for matching narrative
