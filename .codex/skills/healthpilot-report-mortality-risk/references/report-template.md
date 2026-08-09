# Mortality Risk Report — {profile_name}

**Report generated:** {YYYY-MM-DD, timezone}
**Profile:** {profile_name}
**Age / profile sex:** {age} / {sex}
**Geographic baseline:** {geography, population, data year}
**Modeling horizon:** {remaining lifetime or user-specified horizon}
**Method label:** {validated model output | competing-risk life-table estimate | baseline-calibrated heuristic estimate}

> This is a decision-support estimate based on current records and population data, not a prediction of how or when this person will die. The estimates are uncertain and modifiable.

## Executive interpretation

{Briefly state the leading risk pattern, largest uncertainty, and most important modifiable cross-cause risk.}

## Probability definition

{Define the exact estimand and denominator. State whether this is a lifetime distribution, an absolute horizon risk, or a conditional share among deaths in a horizon.}

## Current status used

### Active conditions and major risk modifiers

{Separate observed diagnoses/findings from inference and apply Healthpilot confidence frames.}

### Current medication and supplement evidence

{List a reconciled current stack if supported, or identify the latest evidence that still needs reconciliation.}

## Source coverage

| Source | Status | Freshness / span | Evidence used | Limitation or impact on uncertainty |
|---|---|---|---|---|
| Live profile / demographics | {status} | {date} | {evidence} | {limitation} |
| Labs | {status} | {span} | {evidence} | {limitation} |
| Standalone exams | {status} | {span} | {evidence} | {limitation} |
| Health log | {status} | {span} | {evidence} | {limitation} |
| Genetics / SelfDecode cache | {status} | {date} | {evidence} | {limitation} |
| Schedule | {status} | {date} | {evidence} | {limitation} |
| Nutrition | {status} | {date} | {evidence} | {limitation} |
| Exercise | {status} | {date} | {evidence} | {limitation} |
| Lifestyle constraints | {status} | {date} | {evidence} | {limitation} |
| Prior Healthpilot state | {status} | {date} | {evidence} | {limitation} |

## Population baseline and method

{Cite official baseline sources with data year, release/access date, population strata, cause taxonomy, and direct links. Explain life-table integration or heuristic adjustment. Name any validated model and its exact endpoint.}

### Modifier ledger

| Modifier | Observed evidence | Affected causes | Direction / bounded magnitude | Evidence quality | Double-counting control |
|---|---|---|---|---|---|
| {modifier} | {dated evidence} | {causes} | {direction or multiplier} | {quality} | {handling} |

## Ranked top 10 causes

| Rank | Cause category | Best estimate | Plausible range | Confidence frame | Main reason for rank |
|---:|---|---:|---:|---|---|
| 1 | {mutually exclusive underlying cause} | {N}% | {L–H}% | {frame} | {reason} |
| 2 | {cause} | {N}% | {L–H}% | {frame} | {reason} |
| 3 | {cause} | {N}% | {L–H}% | {frame} | {reason} |
| 4 | {cause} | {N}% | {L–H}% | {frame} | {reason} |
| 5 | {cause} | {N}% | {L–H}% | {frame} | {reason} |
| 6 | {cause} | {N}% | {L–H}% | {frame} | {reason} |
| 7 | {cause} | {N}% | {L–H}% | {frame} | {reason} |
| 8 | {cause} | {N}% | {L–H}% | {frame} | {reason} |
| 9 | {cause} | {N}% | {L–H}% | {frame} | {reason} |
| 10 | {cause} | {N}% | {L–H}% | {frame} | {reason} |

**Residual probability for all other causes:** {N}%

The 10 point estimates plus the residual equal 100%. Plausible ranges are sensitivity bounds and do not need to sum to 100%.

## Cause-by-cause evidence

### 1. {Cause} — {N}% ({L–H}%)

- **Confidence frame:** {frame applied to present risk characterization}
- **Matched baseline:** {share/rank and source}
- **Observed evidence:** {dated profile evidence}
- **Personalized inference:** {why probability moves or stays near baseline}
- **Protective or contradicting evidence:** {evidence}
- **Missing data that would change this estimate:** {data}
- **Best prevention or clarification step:** {specific action}
- **Specialist / discussion:** {specialist type and exact test or treatment discussion, if appropriate}

{Repeat for causes 2–10.}

## Important risks outside the top 10

{Mention only clinically important near-misses, acute flags, or hard-to-quantify risks. Do not turn this into a second ranking.}

## Highest-leverage prevention priorities

1. **{Priority}:** {why it reduces one or more leading risks; exact action; specialist type if needed; result to return with.}
2. **{Priority}:** {details.}
3. **{Priority}:** {details.}

## Data that would most change the ranking

1. {Missing or stale input and affected causes.}
2. {Input.}
3. {Input.}

## Limitations

- {Population-data and period-rate limitation.}
- {Profile completeness and source availability limitation.}
- {Model applicability and modifier uncertainty.}
- {Clarify that estimates are modifiable and not a deterministic forecast.}

## Sources

- {Direct local source citations with dates/paths where appropriate.}
- {Direct links to official mortality tables, life tables, validated models, and primary evidence.}
