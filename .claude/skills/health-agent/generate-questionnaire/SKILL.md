---
name: generate-questionnaire
description: Generate comprehensive health log augmentation questionnaires for systematic data collection. Use when user asks "create questionnaire", "generate questionnaire", "health log augmentation", or needs structured data collection forms.
---

# Generate Questionnaire

Generate comprehensive questionnaires to systematically augment existing health log data with additional context, patterns, and details.

## Purpose

This skill provides:
- Structured questionnaires tailored to profile's existing conditions and patterns
- Systematic data collection across 14 major health domains
- Gap analysis to identify missing information
- Actionable follow-up tasks for enriching health records

## Workflow

1. Load profile to get demographics and data source paths
2. Sample recent health log entries (last 100 rows of CSV, recent narrative entries)
3. Identify active conditions, medications, symptoms, and episodes
4. Generate questionnaire sections targeting identified patterns
5. Include follow-up recommendations
6. Save to `.output/{profile}/questionnaires/health-log-augmentation-{date}.md`

## Efficient Data Access

### Sample Recent Health Log Entries
```bash
# Last 100 CSV entries to identify recent patterns
tail -100 "{health_log_path}/health_log.csv"

# Recent narrative entries for context
tail -200 "{health_log_path}/health_log.md" | head -150
```

### Identify Active Conditions
```bash
grep -E ",(condition|symptom)," "{health_log_path}/health_log.csv" | tail -50
```

### Identify Current Medications/Supplements
```bash
grep -E ",(medication|supplement)," "{health_log_path}/health_log.csv" | tail -50
```

## Questionnaire Structure

The questionnaire should include these major sections:

### Core Sections (Always Include)
1. **Chronic Conditions Deep Dive** - Pattern analysis for persistent conditions
2. **Medication & Supplement Responses** - Why discontinued, PRN protocols, sensitivities
3. **Symptom Deep Dives** - Detailed characterization of recurring symptoms
4. **Family History** - First-degree relatives, specific condition screening
5. **Lab Work Correlations** - Patterns, missing tests, frequency
6. **Health Goals & Priorities** - Current focus areas, functional goals

### Conditional Sections (Include If Relevant)
7. **Infectious Disease History** - If URI or infections present in log
8. **Musculoskeletal Issues** - If orthopedic conditions present
9. **Environmental & Lifestyle** - Work, exercise, diet, sleep, stress
10. **Medical Provider Relationships** - Care team, coordination gaps
11. **Genetic Data** - If genetics_23andme_path configured in profile
12. **Exam & Imaging History** - If multiple imaging studies present
13. **Episode-Specific Deep Dives** - For significant episodes requiring more context
14. **Open-Ended Reflections** - Always include for uncaptured patterns

## Section Templates

### Chronic Condition Template
For each chronic condition identified, create a subsection with:
- **Temporal Patterns**: Seasonal, stress-related, activity-related
- **Symptom Correlations**: Associated symptoms, severity scales
- **Triggering Factors**: Foods, medications, activities
- **Family History**: Related conditions in relatives
- **Treatment Response Matrix**: Interventions tried, effectiveness ratings

### Medication/Supplement Template
For discontinued items:
- Start date, stop date, reason for discontinuation, would retry?

For PRN items:
- Specific triggers, typical relief timeline, decision criteria

For sensitivities:
- Dose-response details, time to symptoms, mitigation strategies

### Lab Work Template
- Patterns noticed across markers
- Frequency of testing
- Missing lab data (tests never done but potentially informative)

## Output Format

```markdown
# Health Log Augmentation Questionnaire
**Profile**: {name}
**Generated**: {YYYY-MM-DD}
**Purpose**: Systematic data collection to enrich existing health log entries

---

## Instructions

This questionnaire is designed to be completed iteratively...

[Instructions for use]

---

## Section 1: [Section Name]

### 1.1 [Subsection]

**[Question Category]:**
- [ ] Question 1
- [ ] Question 2

[Tables, forms, or structured data collection templates]

---

[Repeat for all sections]

---

## Next Steps

After completing relevant sections:

1. **Update health log entries** with new details
2. **Generate targeted analyses** using health-agent skills:
   - `/skill lab-trend` for markers with clarified patterns
   - `/skill episode-investigation` for episodes with added detail
   - `/skill cross-temporal-correlation` for newly identified patterns
   - `/skill investigate-root-cause` for conditions with new context
3. **Create provider reports** with augmented data
4. **Consider additional testing** based on gaps identified
5. **Set up prospective tracking** for patterns to monitor going forward

---

**Questionnaire Version**: 1.0
**Last Updated**: {YYYY-MM-DD}
**Status**: Initial draft for iterative completion
```

## Output File

- **Directory**: `.output/{profile}/questionnaires/`
- **Filename**: `health-log-augmentation-{YYYY-MM-DD}.md`
- **Create directory if needed**: `mkdir -p .output/{profile}/questionnaires`

## Questionnaire Design Principles

1. **Iterative Completion** - Don't require all-at-once completion
2. **Targeted Questions** - Base questions on actual conditions/patterns in the data
3. **Multiple Formats** - Use checkboxes, tables, scales, and open-ended questions
4. **Actionable Output** - Include specific next steps for using collected information
5. **Gap Analysis** - Explicitly identify missing information that would be valuable
6. **Mark Uncertainty** - Provide convention for uncertain information (e.g., `[UNCERTAIN]`)

## Integration with Other Skills

After questionnaire completion, recommend these follow-up skills:

- **Analysis Skills**: Use enriched data with `lab-trend`, `cross-temporal-correlation`, `episode-investigation`
- **Hypothesis Skills**: Better-informed `investigate-root-cause` with detailed patterns
- **Report Skills**: More comprehensive provider reports with augmented context
- **Genetics Skills**: Targeted genetic variant lookups based on conditions

## Special Considerations

- **Privacy**: Questionnaires should be saved locally and gitignored
- **Length**: Comprehensive but skippable - users should be able to work through in stages
- **Personalization**: Tailor sections to the individual's actual health patterns, not generic questions
- **Time Efficiency**: Prioritize high-value questions that fill genuine gaps in the data
- **Clinical Relevance**: Focus on information that would aid diagnosis, treatment, or pattern identification

## Example Triggers

User phrases that should invoke this skill:
- "Create a questionnaire for me"
- "Generate health log augmentation questionnaire"
- "I want to add more detail to my health data"
- "Help me systematically fill in gaps in my health records"
- "Questionnaire to enrich my health log"
