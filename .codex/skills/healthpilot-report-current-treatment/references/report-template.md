# Current Medications and Treatments — {profile_name}

**Report generated:** {YYYY-MM-DD HH:MM TZ}
**Profile:** {profile_name}
**Record cutoff:** {latest evidence date reviewed}
**Snapshot confidence:** {high | moderate | low, with one-line reason}

> This report reconciles what the available record supports as current. It does not instruct the person to start, stop, taper, or change treatment.

## Reconciliation summary

### Clear conclusion

- {Count and summarize confirmed or likely current medications, supplements, and other treatments.}

### Open question

- {State the most important current-status, dose, adherence, or stop-date uncertainty.}

## Source coverage

| Source | Status | Freshness / span | Current-treatment evidence used | Limitation |
|---|---|---|---|---|
| Live profile / demographics | {status} | {date} | {evidence or none} | {limitation} |
| Labs | {status} | {span} | {monitoring or response evidence, or none} | {limitation} |
| Standalone exams | {status} | {span} | {evidence or none} | {limitation} |
| Health log | {status} | {span} | {evidence or none} | {limitation} |
| Genetics / SelfDecode cache | {status} | {date} | {treatment-linked evidence or none} | {limitation} |
| Schedule | {status} | {date} | {evidence or none} | {limitation} |
| Nutrition | {status} | {date} | {evidence or none} | {limitation} |
| Exercise | {status} | {date} | {evidence or none} | {limitation} |
| Lifestyle constraints | {status} | {date} | {evidence or none} | {limitation} |
| Prior Healthpilot state | {status} | {date} | {lead used or none} | {limitation} |

## Current medications

| Medication | Status | How taken | Origin | Indication / target | Latest confirmation | Response / adverse effects | Evidence / uncertainty |
|---|---|---|---|---|---|---|---|
| {generic name (brand if recorded)} | {confirmed active | likely active | active PRN/intermittent} | {dose, form, route, schedule} | {origin} | {stated or inferred target} | {date} | {evidence or not recorded} | {source citation and uncertainty} |

{If empty, write: `No current medications were identified in the available record.`}

## Current supplements

| Supplement | Status | How taken | Origin | Purpose / target | Latest confirmation | Response / adverse effects | Evidence / uncertainty |
|---|---|---|---|---|---|---|---|
| {name and ingredients when relevant} | {status} | {dose, form, schedule} | {origin} | {purpose} | {date} | {evidence or not recorded} | {source citation and uncertainty} |

{If empty, write: `No current supplements were identified in the available record.`}

## Current non-medication treatments

| Treatment | Category | Status | Protocol / schedule | Origin | Target | Latest confirmation | Response / evidence / uncertainty |
|---|---|---|---|---|---|---|---|
| {treatment} | {therapy, device, rehabilitation, nutrition, exercise, sleep, behavioral, monitoring, or self-experiment} | {status} | {protocol} | {origin} | {target} | {date} | {source citation and notes} |

{If empty, write: `No current non-medication treatments were identified in the available record.`}

## Current monitoring and follow-up

| Monitoring or care activity | Frequency / next date | Linked treatment or condition | Latest confirmation | Evidence / uncertainty |
|---|---|---|---|---|
| {lab monitoring, surveillance, specialist follow-up, or measurement protocol} | {schedule} | {link} | {date} | {source citation and notes} |

{If empty, write: `No current monitoring or follow-up regimen was identified in the available record.`}

## Planned or recommended—not confirmed started

| Item | Plan / intended target | Evidence date | Why it is not classified as current |
|---|---|---|---|
| {item} | {plan} | {date and source} | {missing start confirmation} |

## Unclear or conflicting current status

| Item | Latest supporting evidence | Conflicting or missing evidence | Reconciliation needed |
|---|---|---|---|
| {item} | {evidence} | {conflict} | {specific question} |

## Recently stopped or completed

| Item | Prior regimen | Stop / completion evidence | Reason or outcome if recorded |
|---|---|---|---|
| {item} | {regimen} | {date and source} | {reason or not recorded} |

## Reconciliation flags

- {Dose conflict, duplicate listing, ingredient overlap, documented adverse effect, missed monitoring, ambiguous instruction, or `None identified from the available record`.}

## Evidence notes

- {Explain synonym merges, brand/generic normalization, indication inference, template-versus-adherence distinctions, and source precedence decisions.}
