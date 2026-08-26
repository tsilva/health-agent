# Medication sheet specification

The renderer accepts one UTF-8 JSON object. All rendered text must already be in European Portuguese (`pt-PT`). Do not place source paths, evidence citations, parser metadata, or secrets in the specification.

## Shape

```json
{
  "profile": {
    "slug": "profile-slug",
    "name": "Full Name",
    "date_of_birth": "YYYY-MM-DD"
  },
  "updated_on": "YYYY-MM-DD",
  "record_cutoff": "YYYY-MM-DD",
  "monitoring_alert": {
    "title": "Optional short heading",
    "text": "Optional concise instructions and thresholds"
  },
  "sections": [
    {
      "title": "DE MANHÃ / PEQUENO-ALMOÇO - CAIXA AMARELA",
      "color": "yellow",
      "items": [
        {
          "name": "Generic medicine name",
          "brand": "Optional brand",
          "form": "Optional formulation",
          "dose": "Administered dose",
          "instructions": "How and when to take it",
          "reason": "Recorded treatment target"
        }
      ]
    }
  ],
  "confirmations": [
    "Concise unresolved reconciliation question"
  ],
  "footer_note": "Optional neutral document-use note"
}
```

## Requirements

- `profile.slug`, `profile.name`, `profile.date_of_birth`, `updated_on`, `record_cutoff`, and at least one non-empty section are required.
- Dates use ISO `YYYY-MM-DD`. The renderer derives age from `date_of_birth` and `updated_on`.
- Each item requires non-empty `name`, `dose`, `instructions`, and `reason`. `brand` and `form` are optional.
- `monitoring_alert` is optional, but when present requires both `title` and `text`.
- `confirmations` is optional. Use it for current-strength, status, duplication, or stop-date uncertainties; do not put historical narrative there.
- `footer_note` is optional. The renderer otherwise uses a neutral medication-organisation disclaimer.

## Colours

`color` may be one of:

- `yellow`
- `pink`
- `blue`
- `grey`
- `green`
- `orange`
- `purple`

For an unusual schedule, `color` may instead be an object with hexadecimal `bar` and `background` values:

```json
{"bar": "#376E6F", "background": "#DCEDEC"}
```

Use high-contrast dark bars with light row backgrounds. A custom colour does not change medication semantics.

## Content rules

- Use the administered amount in `dose`, not merely the marketed tablet strength.
- Keep strength/fraction context in `instructions` when splitting a tablet.
- Repeat a medication in each relevant time section if that makes the daily schedule clearer.
- Exclude completed courses and planned-but-not-started items.
- Keep monitoring text concise enough for the one-page layout. Never abbreviate away a safety threshold or stop/contact criterion.
