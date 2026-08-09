# Probability Estimation Method

Use this reference to keep a mortality report numerically coherent and explicit about uncertainty.

## 1. Choose the estimand

Default estimand:

`P(underlying cause = i over remaining lifetime | alive on report date, current evidence and assumptions)`

This is a competing-risk distribution. Across every mutually exclusive cause, it sums to 100% because eventual death is the conditioned endpoint. It is not a probability of dying soon.

For a user-selected horizon, define one of these instead:

- absolute risk: `P(death from cause i before horizon)`
- conditional cause share: `P(cause i | death before horizon)`

Label the choice. The second can look large even when the absolute chance of death is small.

## 2. Prefer a competing-risk life-table calculation

Obtain matched period life-table death probabilities and cause shares by age interval, sex, and geography. For interval `t`:

- `q_all(t)`: probability of death from any cause during the interval, conditional on being alive at its start
- `s_i(t)`: share of deaths assigned to mutually exclusive cause `i`; shares must sum to 1
- `h_all(t) = -ln(1 - q_all(t))`
- `h_i(t) = h_all(t) * s_i(t)`

Represent conservative personalized modifiers as cause-specific hazard multipliers `m_i(t)`. Then:

- `h'_i(t) = h_i(t) * m_i(t)`
- `h'_all(t) = sum_i h'_i(t)`
- `q'_all(t) = 1 - exp(-h'_all(t))`
- `q'_i(t) = q'_all(t) * h'_i(t) / h'_all(t)`

If `S(t)` is survival to the interval start, add `S(t) * q'_i(t)` to cause `i`, then update `S(t+1) = S(t) * (1 - q'_all(t))`.

Use `scripts/estimate_competing_risks.py` for this arithmetic. The terminal open-ended interval may use `q_all = 1`; the script assigns remaining survival across that interval's adjusted cause shares.

Document that period rates and constant or approximate multipliers assume future hazards resemble the selected baseline and that current risk relationships persist. Those assumptions are material limitations.

## 3. Build modifiers conservatively

Use this evidence hierarchy:

1. directly diagnosed disease, pathology, or major prior event
2. validated clinical risk-model output with complete inputs and matching population
3. repeated objective risk-factor trends and well-established treatment status
4. consistent family history, behavior, and longitudinal symptoms
5. single or ambiguous measurements
6. common genetic variants with small effects

Prefer explicit age-specific effect estimates. If only a relative risk or hazard ratio is available:

- verify that the endpoint is cause-specific mortality, not incidence or a composite
- verify applicability to age, sex, geography, diagnosis, and treatment status
- avoid directly multiplying overlapping effects
- shrink imprecise or poorly matched effects toward 1.0
- preserve a wide plausible range

Never invent quantitative multipliers merely to produce personalization. Retaining the population baseline with wider uncertainty is preferable.

## 4. Handle incomplete baseline data

If full age-specific future data are unavailable:

1. use the closest official age/sex/geography cause distribution
2. adjust conservatively with the modifier ledger
3. normalize across all modeled causes
4. label the result `baseline-calibrated heuristic lifetime distribution`, not an actuarial estimate
5. explain how age-band substitution could change the ranking

Do not treat a current-age cause distribution as a true lifetime distribution without this caveat. Do not use worldwide all-age shares when a closer official baseline exists.

## 5. Prevent taxonomy and denominator errors

- Use underlying causes, not risk factors or contributing conditions.
- Keep categories mutually exclusive.
- Do not rank both an aggregate and its component.
- Normalize across every modeled cause before selecting the top 10.
- Show exactly 10 causes and an unranked residual.
- Require `sum(top 10 point estimates) + residual = 100%` after rounding.
- Treat plausible intervals as sensitivity bounds, not formal confidence intervals unless a source provides formal intervals.

## 6. Calibrate language

Use one of these method labels:

- `validated model output`: only for the exact endpoint produced by a named applicable model
- `competing-risk life-table estimate`: matched life-table and age-specific cause data were integrated
- `baseline-calibrated heuristic estimate`: the baseline or modifiers required material approximation

Describe a point estimate as a useful center of a wide uncertainty range. State which single missing input would most change the estimate.
