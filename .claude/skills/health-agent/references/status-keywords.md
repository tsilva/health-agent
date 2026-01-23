# Status Determination Keywords

Used by: medication-supplements, report-medication-list, report-health-events, report-conditions-status

## Keyword Lists

### Active Keywords

**For medications and supplements:**
- started, prescribed, continued, refilled
- increased, decreased, taking, began

**Additional for conditions:**
- stable, monitoring, managed, controlled
- ongoing, chronic, persistent, recurring

### Discontinued Keywords

**For medications and supplements:**
- stopped, discontinued, finished, completed
- replaced by, switched to, ended, no longer

### Suspected Keywords (conditions only)

- suspected, possible, probable, likely
- rule out, r/o, investigate, workup
- differential, consider, evaluate
- pending confirmation, awaiting results

### Resolved Keywords (conditions only)

- resolved, recovered, cleared, healed
- ended, finished, completed, cured
- remission, negative, normal
- no longer present

## Algorithm

### Primary Source: current.yaml

For **current state**, always use `{health_log_path}/current.yaml` as the source of truth:

1. **Read current.yaml** - This file explicitly lists active medications, supplements, conditions, experiments
2. **Trust the status** - Items in current.yaml are definitively active unless marked otherwise
3. **No keyword analysis needed** - The parser has already determined status

```bash
# Get current medications (always accurate)
grep -A 100 "^medications:" "{health_log_path}/current.yaml"

# Get current conditions
grep -A 100 "^conditions:" "{health_log_path}/current.yaml"
```

### Secondary Source: history.csv

For **historical analysis** (e.g., "when was this discontinued?", "what did I take last year?"), use `{health_log_path}/history.csv`:

1. **Group events** by EntityID (tracks same medication/supplement/condition)
2. **Sort events** by Date descending (most recent first)
3. **Check most recent event** for status keywords
4. **Classify**:
   - If contains discontinued keywords → Discontinued
   - If contains active keywords → Active
   - If contains suspected keywords → Suspected (conditions only)
   - If contains resolved keywords → Resolved (conditions only)
   - If ambiguous, check for more recent "started" event
   - For conditions: if no keywords and recent (<90 days) → Active
   - For conditions: if no keywords and old (>90 days) → Resolved

### When to Use Which Source

| Use Case | Source | Why |
|----------|--------|-----|
| "What medications am I taking?" | current.yaml | Source of truth for current state |
| "List my active conditions" | current.yaml | Source of truth for current state |
| "When did I stop taking X?" | history.csv | Need historical timeline |
| "What happened in episode Y?" | history.csv | Need timeline events |
| "Show changes since last visit" | history.csv | Need date-filtered events |

## Skill-Specific Usage

### medication-supplements
- Use Active/Discontinued only
- Apply to medications and supplements

### report-medication-list
- Use Active/Discontinued only
- Apply to medications and supplements
- Generate report section with active medications

### report-conditions-status
- Use Active/Suspected/Resolved
- Apply condition-specific keywords
- Apply 90-day recency rule for conditions without explicit keywords

### report-health-events
- Use Active/Resolved for episode classification
- Apply to health events and episodes
- Consider entity linkage via EntityID and RelatedEntity columns in history.csv

## Notes

- **Case insensitive**: Keyword matching should be case-insensitive
- **Partial matching**: Check if keyword appears anywhere in Event or Details text
- **Precedence**: Discontinued/Resolved keywords take precedence over Active keywords
- **Recency**: Most recent event determines status (don't apply retrospective logic)
