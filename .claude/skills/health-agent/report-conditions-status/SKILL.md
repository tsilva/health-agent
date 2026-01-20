---
name: report-conditions-status
description: Generate conditions status document showing active and resolved conditions. Use when user asks "generate conditions report", "what conditions do I have", "active diagnoses", "medical conditions list", or needs a conditions summary for provider visits.
---

# Report: Conditions Status

Generate a standardized section documenting the status of all health conditions, diagnoses, and symptoms for provider visits.

## Purpose

This report section provides:
- Active conditions (chronic, stable, being monitored)
- Suspected/under investigation conditions
- Recently resolved conditions (last 12 months)
- Historical resolved conditions
- Provider discussion points

## Workflow

1. Load profile and extract `health_log_path`
2. Extract condition and symptom entries from health_log.csv
3. Group events by EpisodeID to track condition lifecycle
4. Classify each condition by status
5. Categorize into active vs resolved
6. Format into standardized section
7. Save to `.output/{profile}/sections/conditions-status-{date}.md`

## Efficient Data Access

### Extract All Condition/Symptom Events
```bash
head -1 "{health_log_path}/health_log.csv" && grep -iE ",condition,|,symptom,|,diagnosis," "{health_log_path}/health_log.csv" | sort -t',' -k1 -r
```

### Extract Events by Category
```bash
head -1 "{health_log_path}/health_log.csv" && grep -i ",condition," "{health_log_path}/health_log.csv"
```

### Extract Events by Episode
```bash
head -1 "{health_log_path}/health_log.csv" && grep "{episode_id}" "{health_log_path}/health_log.csv"
```

### Search for Active/Ongoing Keywords
```bash
grep -iE "(chronic|ongoing|stable|monitoring|active|diagnosed|persistent)" "{health_log_path}/health_log.csv"
```

### Search for Resolution Keywords
```bash
grep -iE "(resolved|recovered|cleared|healed|ended|negative|remission|cured)" "{health_log_path}/health_log.csv"
```

### Extract Context from Narrative
```bash
grep -B 2 -A 5 "{condition_name}" "{health_log_path}/health_log.md"
```

## Status Classification

### Active Status Keywords
Conditions are **active** when events contain:
- started, noted, diagnosed, confirmed
- stable, monitoring, managed, controlled
- ongoing, chronic, persistent, recurring
- flare, worsening, progressing

### Suspected Status Keywords
Conditions are **suspected** when events contain:
- suspected, possible, probable, likely
- rule out, r/o, investigate, workup
- differential, consider, evaluate
- pending confirmation, awaiting results

### Resolved Status Keywords
Conditions are **resolved** when events contain:
- resolved, recovered, cleared, healed
- ended, finished, completed, cured
- remission, negative, normal
- no longer present, discontinued

## Condition Classification Logic

1. **Gather all events** for each EpisodeID related to conditions/symptoms
2. **Find most recent event** for each episode
3. **Classify by most recent event**:
   - If contains active keywords → Active
   - If contains suspected keywords → Suspected
   - If contains resolved keywords → Resolved
   - If no keywords but recent (< 90 days) → Active (assume ongoing)
   - If no keywords and old (> 90 days with no updates) → Resolved (assume resolved)

4. **Sub-classify active conditions**:
   - **Chronic**: Contains "chronic", "long-term", or diagnosed > 1 year ago with ongoing management
   - **Stable**: Contains "stable", "controlled", "managed"
   - **Monitoring**: Contains "monitor", "watch", "follow", "track"
   - **Under Treatment**: Contains "treating", "treatment", "therapy"

## Output Format

The section must follow this exact format for composability:

```markdown
---
section: conditions-status
generated: {YYYY-MM-DD}
profile: {profile_name}
---

# Conditions Status

## Active Conditions

### Confirmed Diagnoses

| Condition | Status | Since | Last Updated | Notes |
|-----------|--------|-------|--------------|-------|
| {condition} | {Chronic/Stable/Monitoring/Under Treatment} | {start_date} | {last_date} | {brief notes} |

*No confirmed diagnoses* (if none)

### Suspected / Under Investigation

| Condition | Status | First Noted | Last Updated | Investigation |
|-----------|--------|-------------|--------------|---------------|
| {condition} | Suspected | {date} | {date} | {workup notes} |

*No conditions under investigation* (if none)

---

## Inactive / Resolved Conditions

### Resolved (Last 12 Months)

| Condition | Resolution | Period | Outcome |
|-----------|------------|--------|---------|
| {condition} | {resolved/recovered/cleared} | {start} - {end} | {outcome} |

*No recently resolved conditions* (if none)

### Resolved (Historical)

| Condition | Year | Outcome |
|-----------|------|---------|
| {condition} | {year} | {brief outcome} |

*No historical resolved conditions* (if none)

---

## Provider Discussion Points

- **Review needed**: {conditions requiring discussion}
- **Status updates**: {conditions with recent changes}
- **Pending workups**: {suspected conditions awaiting confirmation}

---
*Section generated by health-agent report-conditions-status skill*
```

## Output File

- **Directory**: `.output/{profile}/sections/`
- **Filename**: `conditions-status-YYYY-MM-DD.md`
- **Create directory if needed**: `mkdir -p .output/{profile}/sections`

## Section Header Requirements

For composability with other report sections:
1. Include YAML frontmatter with section name, date, and profile
2. Use consistent H1 header format
3. Separate major sections with horizontal rules
4. End with attribution line

## Distinguishing from Health Events Report

- **report-health-events**: Focus on recent episodes and timeline, includes all event types
- **report-conditions-status**: Focus specifically on conditions/diagnoses with status classification

The conditions report is useful for:
- New provider intake forms
- Annual wellness visits
- Insurance or disability documentation
- Condition-specific specialist referrals

## Episode vs Standalone Conditions

Some conditions may not have EpisodeIDs. Handle these by:
1. Grouping by condition name/Item field
2. Tracking the earliest and latest mention
3. Applying the same status classification logic

## Condition Name Normalization

When grouping, normalize condition names:
- "cold" / "common cold" / "viral URI" → group together
- Look for similar names in adjacent entries
- Use Item field as primary identifier, Event field for context

## Special Considerations

- **Privacy**: Use clinical terminology appropriately
- **Accuracy**: Only include conditions explicitly documented
- **Recency**: Clearly distinguish recent vs historical
- **Provider Focus**: Highlight items needing discussion or follow-up
- **Chronic Conditions**: Always include in active section even if stable
