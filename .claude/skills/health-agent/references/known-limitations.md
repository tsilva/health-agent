# Known Limitations

Technical limitations of the health-agent system and available data sources.

## 23andMe Genetics Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| **No CNV detection** | Can't detect copy number variations | Clinical genetic testing required |
| **Limited indels** | Insertions/deletions often missed | Some conditions undetectable |
| **~631k SNPs only** | Many clinically relevant SNPs not tested | Use SelfDecode for imputed coverage |
| **Unphased genotypes** | Can't determine maternal/paternal allele | Haplotype inference uncertain |
| **BRCA limited to 3 mutations** | Only Ashkenazi founder mutations tested | Full BRCA panel requires clinical test |
| **No UGT1A1*28** | Gilbert syndrome TA repeat not detectable | Proxy SNPs (rs887829) used instead |

## SelfDecode Imputation Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Imputed, not genotyped** | Lower accuracy than direct genotyping | Prefer 23andMe when both have SNP |
| **Population-specific accuracy** | Better for European ancestry | Note ancestry in interpretations |
| **JWT token expiration** | Requires periodic refresh | Follow auth error recovery workflow |
| **No direct validation** | Can't verify imputation accuracy | Cross-reference with 23andMe when possible |

## Lab Data Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **OCR confidence varies** | Values <0.8 confidence may be wrong | Flag for manual verification |
| **Unit standardization incomplete** | Some units may not convert properly | Use `lab_specs.json` for known conversions |
| **Reference ranges vary by lab** | Population-based, not personalized | Use `biomarker_baselines` in state for personal ranges |
| **Missing tests not detected** | Can't know what hasn't been tested | Diagnostic gap analysis in investigations |

## Health Log Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Self-reported data** | Subject to recall bias | Note uncertainty in interpretations |
| **Episode linking manual** | Related events may not be connected | Use `generate-questionnaire` to identify gaps |
| **Status inference imperfect** | May misclassify active/discontinued | Apply status-keywords.md algorithm |

## Investigation Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Not a diagnosis** | Agent findings are hypotheses, not diagnoses | Always consult healthcare provider |
| **Literature search scope** | May miss very recent or obscure research | Check publication dates in citations |
| **Confidence calibration** | Still experimental | Report uncertainty ranges |
| **English-only sources** | Non-English research may be missed | Note in literature sections |
