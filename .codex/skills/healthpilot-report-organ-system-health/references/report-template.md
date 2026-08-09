# Organ and Bodily-System Health Report — {profile_name}

**Report generated:** {YYYY-MM-DD HH:MM TZ}
**Profile:** {profile_name}
**Age / profile sex:** {age} / {sex}
**Record cutoff:** {latest evidence date reviewed}

> Scores use a nonvalidated Healthpilot prioritization rubric. They are not diagnoses, probabilities, clinical grades, or comparisons with other people. Low-confidence scores may represent missing evidence rather than impaired health.

## Executive summary

- **Lowest-scoring systems:** {three systems and scores}
- **Main impairment-driven finding:** {finding or none established}
- **Main uncertainty-driven score:** {system and missing evidence}
- **Most valuable next data point:** {test, exam, or reconciliation item}

## Score meaning

- `10` = exceptional directly evidenced health across structure, function, symptoms, disease control, and trajectory.
- `5` = neutral/indeterminate midpoint when evidence is missing or mixed; it does not mean 50% healthy.
- `0` = directly evidenced acute critical failure.
- Systems are sorted from lowest to highest health score. Confidence and plausible range must be read with the score.

## Current status context

### Active conditions

{List active/monitoring conditions with confidence frames.}

### Current medications and treatments considered

{Summarize the reconciled current regimen or the evidence needing reconciliation.}

## Source coverage

| Source | Status | Freshness / span | Systems informed | Limitation or uncertainty impact |
|---|---|---|---|---|
| Live profile / demographics | {status} | {date} | {systems} | {limitation} |
| Labs | {status} | {span} | {systems} | {limitation} |
| Standalone exams | {status} | {span} | {systems} | {limitation} |
| Health log | {status} | {span} | {systems} | {limitation} |
| Genetics / SelfDecode cache | {status} | {date} | {systems or none} | {limitation} |
| Schedule | {status} | {date} | {systems or none} | {limitation} |
| Nutrition | {status} | {date} | {systems or none} | {limitation} |
| Exercise | {status} | {date} | {systems or none} | {limitation} |
| Lifestyle constraints | {status} | {date} | {systems or none} | {limitation} |
| Prior Healthpilot state | {status} | {date} | {systems or none} | {limitation} |

## Ranked system scores

| Rank | Organ/system | Health score | Plausible range | Evidence confidence | Driver | Main evidence or gap |
|---:|---|---:|---:|---|---|---|
| 1 | {lowest canonical system} | {N.N}/10 | {L–H} | {High/Moderate/Low} | {driver} | {evidence} |
| … | {continue all 16 canonical systems in ascending score order} | {N.N}/10 | {L–H} | {confidence} | {driver} | {evidence} |
| 16 | {highest canonical system} | {N.N}/10 | {L–H} | {confidence} | {driver} | {evidence} |

## Detailed organ and subsystem scores

| Parent system | Organ or subsystem | Health score | Plausible range | Evidence confidence | Driver | Main evidence or gap |
|---|---|---:|---:|---|---|---|
| {parent} | {required organ/subsystem from inventory} | {N.N}/10 | {L–H} | {confidence} | {driver} | {evidence} |

{Include every required inventory row and add evidence-supported extra organs.}

## Five lowest systems

### 1. {System} — {N.N}/10 ({L–H})

- **Working conclusion:** {conclusion}
- **Confidence frame:** {clear conclusion | likely diagnosis | differential | open question}
- **Driver:** {impairment-driven | uncertainty-driven | mixed | healthy-evidenced}
- **Dimension scores:** structure {N}/2; function {N}/2; symptoms/impact {N}/2; disease/control {N}/2; trajectory/reserve {N}/2
- **Observed supporting evidence:** {dated evidence}
- **Reassuring or contradicting evidence:** {dated evidence}
- **Missing data that would change the score:** {data}
- **Next best test, monitoring step, or specialist discussion:** {specific action and specialist type if appropriate}
- **Result that would most change the score:** {result}

{Repeat for ranks 2–5.}

## Cross-system findings

- {Systemic signal, primary scoring location, downstream relevance, and how double-counting was avoided.}

## Evidence gaps

1. {Highest-impact gap and affected systems.}
2. {Gap.}
3. {Gap.}

## Safety notes

- {Urgent red flag if present, otherwise `No acute organ-failure signal was identified in the available record.`}

## Limitations

- {Unavailable or stale sources.}
- {Explain uncertainty-driven midpoint scores.}
- {Explain that this is current health, not lifetime risk or prognosis.}
- {Explain why scores should not be compared across people.}

## Sources

- {Direct local source citations with dates/paths.}
- {Current authoritative external sources used for high-impact interpretations, if any.}
