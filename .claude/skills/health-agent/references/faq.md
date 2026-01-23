# Frequently Asked Questions

## General Usage

**Q: When should I use which skill?**

| Task | Recommended Approach |
|------|---------------------|
| Quick health status | `/health-dashboard` or session start |
| Understand a symptom/condition | `investigate-root-cause` |
| Prepare for doctor visit | `prepare-provider-visit` |
| Check a specific SNP | `genetics-snp-lookup` via natural language |
| Fill gaps in health data | `generate-questionnaire` |
| Track a biomarker over time | Natural language query (no skill needed) |

**Q: How do I add custom skills?**

Create a SKILL.md file in `.claude/skills/health-agent/your-skill/`:

```markdown
---
name: your-skill
description: "What it does and when to use it"
---

# Your Skill Name

Instructions for the skill...
```

Then document it in CLAUDE.md under "Built-in Skills" if it should be discoverable.

**Q: How is investigation confidence calculated?**

Confidence is calibrated from multiple factors:
1. **Raw agent agreement** (4 agents -> higher base confidence)
2. **Gap penalty** (missing diagnostic tests reduce confidence)
3. **Epidemiological priors** (rare conditions need stronger evidence)
4. **Evidence quality weights** (genetic confirmation > symptom report)
5. **Red Team survival** (did hypothesis survive adversarial testing?)

See `.claude/skills/health-agent/references/confidence-calibration.md` for formulas.

**Q: What if a SNP isn't found in 23andMe?**

1. Check SelfDecode (if configured) - it has imputed data for ~20M SNPs
2. Look for proxy SNPs in linkage disequilibrium
3. Note the gap in your investigation report
4. Consider clinical genetic testing for important variants

## Data Questions

**Q: How do I add new lab results?**

Update your labs-parser output, then:
1. Re-run labs-parser on new PDFs
2. The updated `all.csv` will be read automatically
3. State will update on next health check

**Q: Can I use health-agent without all data sources?**

Yes. Skills gracefully handle missing sources:
- No genetics -> genetics sections skipped
- No labs -> lab trends unavailable
- No health log -> timeline analysis limited
- Minimum: At least one data source recommended

**Q: How do I correct a wrong lab value?**

Options:
1. Fix in source PDF and re-run labs-parser
2. Add a correction note in health_log.csv
3. Manually flag in state file's `biomarker_baselines`

## Privacy Questions

**Q: Is my health data uploaded anywhere?**

No. All data stays local:
- Health data files remain on your machine
- Profile YAML paths point to local files
- API calls (SNPedia, PubMed) send only SNP IDs or search terms
- No PHI is sent to external services

**Q: Are profile files safe to commit to git?**

No - profile files are gitignored by default. Only `_template.yaml` is committed. Verify your `.gitignore` includes `profiles/*.yaml` before committing.

**Q: What about cache files?**

Cache files contain:
- SNPedia responses (public data, no PHI)
- SelfDecode genotypes (your data, gitignored)
- Literature search results (public data)

SNPedia cache can be committed if desired. SelfDecode cache should remain gitignored.
