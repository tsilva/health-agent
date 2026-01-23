# Troubleshooting Guide

Common issues and solutions for health-agent.

## Profile Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| Profile not loading | "Profile not found" error | Verify file exists in `profiles/` and ends with `.yaml` |
| Missing data sources | "Labs file not found" warning | Check paths in profile YAML are absolute and correct |
| Demographics missing | Age-specific ranges not applied | Add `date_of_birth` and `gender` to profile |

**Debug profile paths**:
```bash
# Verify all paths in profile
cat profiles/your_profile.yaml | grep "_path"
# Test each path
test -f "/your/labs/path/all.csv" && echo "Labs OK" || echo "Labs MISSING"
```

## State File Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| State file corrupted | YAML parse errors | See "State File Corruption Handling" in health-dashboard skill |
| State not persisting | Changes lost between sessions | Check `.state/{profile}/` directory exists and is writable |
| Stale state | Dashboard shows old data | Delete `.state/{profile}/health-state.yaml` and re-initialize |

**Reset state**:
```bash
# Backup and remove state file
mv .state/{profile}/health-state.yaml .state/{profile}/health-state.backup.yaml
# Re-run health-dashboard to initialize fresh state
```

## API and Network Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| SNPedia unavailable | Genetics lookups fail | Check network; skill will use cached data if available |
| SelfDecode auth error | "JWT expired" message | Follow token refresh instructions in error message |
| PubMed rate limited | Literature search incomplete | Wait 60 seconds and retry; results are cached |
| Timeout errors | "Request timed out after 30s" | Network may be slow; retry or check connectivity |

**Check cache status**:
```bash
# List cached SNPedia data
ls -la .claude/skills/health-agent/genetics-snp-lookup/.cache/

# List cached SelfDecode data
ls -la .claude/skills/health-agent/genetics-selfdecode-lookup/.cache/{profile}/
```

**Clear cache to force refresh**:
```bash
# Clear specific SNP cache
rm .claude/skills/health-agent/genetics-snp-lookup/.cache/rs12345.json

# Clear all SNPedia cache (forces fresh lookups)
rm -rf .claude/skills/health-agent/genetics-snp-lookup/.cache/
```

## Investigation Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| Investigation stalls | Agent doesn't complete | Check for network issues; restart investigation |
| Low confidence results | All hypotheses <30% | May indicate insufficient data; check for missing labs |
| No genetics analysis | Genetics section empty | Verify `genetics_23andme_path` in profile |
| Missing literature | No PubMed citations | Check network; mechanism validation will be limited |

## Data Quality Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| Labs not recognized | Marker trends incomplete | Check `lab_specs.json` has aliases; use canonical names |
| Low OCR confidence | Values flagged for verification | Re-process source PDFs or manually verify |
| Missing episodes | Timeline gaps | Check health_log.csv for date coverage |

## Cache Management

All API responses are cached for 30 days. To manage cache:

**View cache age**:
```bash
# Check SNPedia cache
find .claude/skills/health-agent/genetics-snp-lookup/.cache -type f -mtime +30
```

**Prune old cache**:
```bash
# Remove cache files older than 30 days
find .claude/skills/health-agent/genetics-snp-lookup/.cache -type f -mtime +30 -delete
```

**Force cache refresh for specific data**:
```bash
# Delete specific cache entry
rm .claude/skills/health-agent/genetics-snp-lookup/.cache/{rsid}.json
# Next lookup will fetch fresh data
```
