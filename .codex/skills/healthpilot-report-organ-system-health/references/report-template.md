# Organ and Bodily-System Health Report — {profile_name}

**Report generated:** {YYYY-MM-DD HH:MM TZ}
**Profile:** {profile_name}
**Record cutoff:** {latest evidence date reviewed}
**Evidence snapshot:** {snapshot_id} at {snapshot_generated_at}
**Previous comparable report:** {filename or none}
**Source-gap severity:** {none | minor | material | critical}

> Scores use a nonvalidated Healthpilot prioritization rubric. They are not diagnoses, probabilities, clinical grades, or comparisons with other people.

## Lowest-scoring systems

| Rank | System | Score | Plausible range | Confidence frame | Evidence confidence | Driver | Urgency | Next useful data point |
|---:|---|---:|---:|---|---|---|---|---|
| 1 | {system} | {N.N}/10 | {L–H} | {frame} | {high/moderate/low} | {impairment/uncertainty/mixed} | {urgency} | {test or reconciliation} |

## Changes since previous report

{For a baseline, use the exact baseline statement. Otherwise classify Added, Changed, Resolved, and Unchanged score changes with current evidence IDs.}

## Score meaning

- `10` = exceptional directly evidenced health across structure, function, symptoms, disease control, and trajectory.
- `5` = neutral/indeterminate midpoint when evidence is missing or mixed; it does not mean 50% healthy.
- `0` = directly evidenced acute critical failure.
- Read every score with its plausible range and evidence confidence.

## Current status context

### Active conditions

{Active or monitoring conditions with confidence frames.}

### Current medications and treatments considered

{Reconciled current regimen or evidence needing reconciliation.}

## Ranked system scores

| Rank | Organ/system | Health score | Plausible range | Evidence confidence | Driver | Main evidence or gap |
|---:|---|---:|---:|---|---|---|
| 1 | {lowest canonical system} | {N.N}/10 | {L–H} | {confidence} | {driver} | {safe citation or gap} |
| … | {all 16 canonical systems in ascending score order} | {N.N}/10 | {L–H} | {confidence} | {driver} | {evidence} |
| 16 | {highest canonical system} | {N.N}/10 | {L–H} | {confidence} | {driver} | {evidence} |

## Detailed organ and subsystem scores

| Parent system | Organ or subsystem | Health score | Plausible range | Evidence confidence | Driver | Main evidence or gap |
|---|---|---:|---:|---|---|---|
| {parent} | {required organ/subsystem} | {N.N}/10 | {L–H} | {confidence} | {driver} | {evidence} |

## Five lowest systems

### 1. {System} — {N.N}/10 ({L–H})

- **Working conclusion:** {conclusion}
- **Confidence frame:** {clear conclusion | likely diagnosis | differential | open question}
- **Evidence confidence:** {high | moderate | low}
- **Urgency:** {immediate | soon | routine | monitoring}
- **Driver:** {impairment-driven | uncertainty-driven | mixed | healthy-evidenced}
- **Dimension scores:** structure {N}/2; function {N}/2; symptoms/impact {N}/2; disease/control {N}/2; trajectory/reserve {N}/2
- **Observed supporting evidence:** {dated evidence IDs}
- **Reassuring or contradicting evidence:** {dated evidence IDs}
- **Missing data that would change the score:** {data}
- **Next step:** {test, monitoring step, or specialist discussion}
- **Result that would most change the score:** {result}

{Repeat for ranks 2–5.}

## Cross-system findings

- {Systemic signal, primary scoring location, downstream relevance, and double-counting control.}

## Evidence gaps

1. {Highest-impact gap and affected systems.}

## Evidence appendix

### Source coverage

| Source | Status | Freshness / span | Systems informed | Limitation or uncertainty impact |
|---|---|---|---|---|
| {source} | {available/missing/unreadable/not configured} | {date or span} | {systems} | {limitation} |

**Unavailable sources:** {list, or `None`}

### Safety notes

- {Urgent red flag, or `No acute organ-failure signal was identified in the available record.`}

### Limitations

- {Missing evidence, uncertainty scoring, current-health horizon, and noncomparability across people.}

### Evidence references

- {Report-safe evidence ID}: {dated evidence label; never an absolute path}
