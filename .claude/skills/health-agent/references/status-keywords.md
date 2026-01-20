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

1. **Group events** by Item (medication/supplement/condition name)
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
- Consider episode linkage via EpisodeID

## Notes

- **Case insensitive**: Keyword matching should be case-insensitive
- **Partial matching**: Check if keyword appears anywhere in Event or Details text
- **Precedence**: Discontinued/Resolved keywords take precedence over Active keywords
- **Recency**: Most recent event determines status (don't apply retrospective logic)
