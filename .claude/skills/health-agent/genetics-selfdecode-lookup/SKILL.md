---
name: genetics-selfdecode-lookup
description: Look up SNP genotypes and interpretations from SelfDecode (imputed genetics data). Requires authentication. Use for expanded SNP coverage beyond 23andMe raw data. Triggers on "check selfdecode for rs...", "selfdecode lookup", "imputed genotype for...", or when SNP not found in 23andMe data.
---

# SelfDecode SNP Lookup

**Authenticated genetics lookup** for SelfDecode's imputed SNP data. SelfDecode provides:
- **Imputed SNPs**: More coverage than raw 23andMe data (~20M+ vs 631k SNPs)
- **Health interpretations**: Risk assessments and recommendations
- **Gene-based reports**: Comprehensive gene analysis

## Prerequisites

- Profile must have `selfdecode` credentials configured
- Environment variables must be set for authentication
- SelfDecode account with uploaded genetic data

## Configuration

### Profile Setup

Add to your profile YAML:

```yaml
data_sources:
  # Existing genetics source
  genetics_23andme_path: "/path/to/23andme_raw_data.txt"

  # SelfDecode (optional - for imputed SNP coverage)
  selfdecode:
    enabled: true
    username_env: "SELFDECODE_USERNAME"   # Environment variable containing email
    password_env: "SELFDECODE_PASSWORD"   # Environment variable containing password
```

### Environment Variables

Set before running health-agent:

```bash
export SELFDECODE_USERNAME="your-email@example.com"
export SELFDECODE_PASSWORD="your-password"
```

## Authentication Flow

### Step 1: Login and Obtain Session

```bash
# Read credentials from environment
username="${SELFDECODE_USERNAME}"
password="${SELFDECODE_PASSWORD}"

# Check credentials are set
if [ -z "$username" ] || [ -z "$password" ]; then
  echo "Error: SELFDECODE_USERNAME and SELFDECODE_PASSWORD must be set"
  exit 1
fi

# Create cookie jar in temp directory
cookie_jar="/tmp/claude/selfdecode-cookies.txt"
mkdir -p /tmp/claude

# Login to SelfDecode
# NOTE: Actual login endpoint and form fields need verification
# This is a placeholder - update after inspecting actual login flow
curl -c "$cookie_jar" -s \
  -d "email=${username}" \
  -d "password=${password}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  "https://selfdecode.com/api/auth/login/" \
  > /tmp/claude/selfdecode-login-response.json

# Verify login success
if grep -q "error\|invalid\|failed" /tmp/claude/selfdecode-login-response.json 2>/dev/null; then
  echo "Error: SelfDecode login failed. Check credentials."
  cat /tmp/claude/selfdecode-login-response.json
  exit 1
fi

echo "SelfDecode session established"
```

### Step 2: Verify Session

```bash
# Test session is valid by fetching dashboard or profile
curl -b "$cookie_jar" -s \
  "https://selfdecode.com/api/user/profile/" \
  > /tmp/claude/selfdecode-session-check.json

if grep -q "unauthorized\|login" /tmp/claude/selfdecode-session-check.json 2>/dev/null; then
  echo "Session expired or invalid. Re-authenticate."
  exit 1
fi

echo "Session valid"
```

## SNP Lookup Workflow

### Single SNP Lookup

```bash
rsid="rs429358"
cookie_jar="/tmp/claude/selfdecode-cookies.txt"
cache_dir=".claude/skills/health-agent/genetics-selfdecode-lookup/.cache"

# 1. Check cache first
cache_file="${cache_dir}/${rsid}.json"
if [ -f "$cache_file" ]; then
  # Check cache age (30-day TTL)
  fetched=$(cat "$cache_file" | python3 -c "import sys, json; print(json.load(sys.stdin).get('fetched', ''))" 2>/dev/null)
  if [ -n "$fetched" ]; then
    fetched_ts=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$fetched" "+%s" 2>/dev/null || echo 0)
    current_ts=$(date "+%s")
    age=$((current_ts - fetched_ts))

    if [ "$age" -lt 2592000 ]; then
      echo "Using cached SelfDecode data for $rsid (age: $((age/86400)) days)"
      cat "$cache_file"
      exit 0
    fi
  fi
fi

# 2. Ensure authenticated
if [ ! -f "$cookie_jar" ]; then
  echo "Error: No SelfDecode session. Run authentication first."
  exit 1
fi

# 3. Fetch SNP page from SelfDecode
# NOTE: URL pattern needs verification - update after inspecting actual site
snp_url="https://selfdecode.com/snp/${rsid}/"

curl -b "$cookie_jar" -s \
  -H "Accept: text/html,application/xhtml+xml" \
  "$snp_url" \
  > "/tmp/claude/${rsid}_selfdecode.html"

# Check if SNP exists
if grep -q "not found\|404\|doesn't exist" "/tmp/claude/${rsid}_selfdecode.html" 2>/dev/null; then
  echo "SNP $rsid not found in SelfDecode"
  exit 1
fi

# 4. Parse HTML for relevant data
# NOTE: Selectors need updating based on actual HTML structure
# These are placeholder patterns - refine after inspecting actual pages

# Extract genotype
genotype=$(grep -oP 'genotype["\s:]+\K[ACGT]{1,2}' "/tmp/claude/${rsid}_selfdecode.html" | head -1)

# Extract interpretation/effect
interpretation=$(grep -oP '(?<=interpretation">)[^<]+' "/tmp/claude/${rsid}_selfdecode.html" | head -1)

# Extract risk level if present
risk_level=$(grep -oP '(?<=risk-level">)[^<]+' "/tmp/claude/${rsid}_selfdecode.html" | head -1)

# 5. Save to cache
mkdir -p "$cache_dir"
cat > "$cache_file" << EOF
{
  "rsid": "$rsid",
  "fetched": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "ttl_seconds": 2592000,
  "source": "selfdecode",
  "imputed": true,
  "data": {
    "genotype": "$genotype",
    "interpretation": "$interpretation",
    "risk_level": "$risk_level",
    "url": "$snp_url"
  }
}
EOF

echo "Cached SelfDecode data for $rsid"
cat "$cache_file"
```

### Batch SNP Lookup

```bash
rsids=("rs429358" "rs7412" "rs1801133")
cookie_jar="/tmp/claude/selfdecode-cookies.txt"

for rsid in "${rsids[@]}"; do
  # Rate limiting - 2 second delay between requests
  sleep 2

  # Use single SNP lookup logic (check cache, fetch, parse, cache)
  # ... (same as single SNP workflow above)

  echo "Processed $rsid"
done
```

## Caching Layer

**Cache directory**: `.claude/skills/health-agent/genetics-selfdecode-lookup/.cache/`

**Cache TTL**: 30 days (2,592,000 seconds)

### Cache File Format

Each rsID gets a JSON cache file: `.cache/{rsid}.json`

```json
{
  "rsid": "rs429358",
  "fetched": "2026-01-22T10:00:00Z",
  "ttl_seconds": 2592000,
  "source": "selfdecode",
  "imputed": true,
  "data": {
    "genotype": "CT",
    "interpretation": "Elevated Alzheimer's risk",
    "risk_level": "moderate",
    "health_effects": [
      "2-3x increased Alzheimer's risk",
      "Consider cognitive health measures"
    ],
    "recommendations": [
      "Regular cognitive assessment",
      "Cardiovascular health focus"
    ],
    "url": "https://selfdecode.com/snp/rs429358/"
  }
}
```

### Cache Fallback

If SelfDecode is unavailable, use stale cache with warning:

```bash
if ! curl_output=$(curl -b "$cookie_jar" -s -f "$snp_url"); then
  if [ -f "$cache_file" ]; then
    echo "Warning: SelfDecode unavailable, using stale cache (age: $((age/86400)) days)"
    cat "$cache_file"
    exit 0
  else
    echo "Error: SelfDecode unavailable and no cache for $rsid"
    exit 1
  fi
fi
```

## Rate Limiting

- **Request delay**: 2 seconds between requests (be respectful)
- **Batch limit**: Max 10 SNPs per session recommended
- **Session reuse**: Reuse authenticated session for multiple lookups

```bash
# Between each SNP lookup
sleep 2
```

## Output Format

### Single SNP Result

```markdown
## SelfDecode SNP Lookup: rs429358

**Source**: SelfDecode (imputed)
**Genotype**: C;T
**URL**: https://selfdecode.com/snp/rs429358/

### Interpretation

**Risk Level**: Moderate

Elevated Alzheimer's risk associated with APOE e4 allele carrier status.

### Health Effects
- 2-3x increased Alzheimer's disease risk compared to non-carriers
- May affect lipid metabolism and cardiovascular health

### Recommendations
- Regular cognitive health monitoring after age 50
- Focus on cardiovascular health (exercise, diet)
- Consider discussing with healthcare provider

**Data Retrieved**: 2026-01-22 (cached)
```

### Comparison with 23andMe/SNPedia

When both sources have data:

```markdown
## SNP Comparison: rs429358

| Source | Genotype | Notes |
|--------|----------|-------|
| 23andMe (raw) | C;T | Directly genotyped |
| SelfDecode (imputed) | C;T | Matches raw data |
| SNPedia | C;T | APOE e3/e4 carrier |

**Concordance**: All sources agree on genotype.
```

## Error Handling

| Scenario | Response |
|----------|----------|
| **Credentials not configured** | Error: "SelfDecode credentials not configured. Add selfdecode config to profile." |
| **Environment variables not set** | Error: "SELFDECODE_USERNAME and SELFDECODE_PASSWORD must be set" |
| **Login failed** | Error: "SelfDecode login failed. Check credentials." |
| **Session expired** | Warning: "Session expired. Re-authenticating..." (then retry) |
| **SNP not found** | Note: "SNP {rsid} not found in SelfDecode database" |
| **Rate limited** | Warning: "Rate limited. Waiting 60s before retry..." |
| **Site unavailable (with cache)** | Warning: "SelfDecode unavailable, using stale cache" |
| **Site unavailable (no cache)** | Error: "SelfDecode unavailable and no cached data for {rsid}" |

## Session Management

### Session Lifetime

SelfDecode sessions typically last several hours. The skill should:

1. Check if existing cookie jar is present
2. Verify session is still valid before making requests
3. Re-authenticate if session expired

```bash
# Check and refresh session if needed
cookie_jar="/tmp/claude/selfdecode-cookies.txt"

if [ -f "$cookie_jar" ]; then
  # Test session validity
  response=$(curl -b "$cookie_jar" -s -w "%{http_code}" -o /dev/null \
    "https://selfdecode.com/api/user/profile/")

  if [ "$response" != "200" ]; then
    echo "Session expired, re-authenticating..."
    rm "$cookie_jar"
    # Run authentication flow
  fi
else
  echo "No session found, authenticating..."
  # Run authentication flow
fi
```

## When to Use This Skill

**Use SelfDecode lookup when**:
- SNP not found in 23andMe raw data
- User specifically asks for SelfDecode data
- Need imputed genotypes for comprehensive coverage
- Comparing genotypes across multiple sources

**Use SNPedia lookup (genetics-snp-lookup) when**:
- SNP is available in 23andMe raw data
- Need research citations and detailed mechanisms
- Public interpretation without authentication needed

## Integration Notes

### Fallback Chain

For comprehensive SNP lookup:

1. **First**: Check 23andMe raw data (most reliable, directly genotyped)
2. **Second**: Check SelfDecode (imputed, more coverage)
3. **Third**: Check SNPedia for interpretation (public reference)

### Investigation Workflow

When investigating conditions:

```markdown
1. genetics-snp-lookup (23andMe + SNPedia) for primary data
2. genetics-selfdecode-lookup for SNPs not in 23andMe
3. Cross-reference both sources when available
```

## HTML Parsing Notes

**IMPORTANT**: The HTML parsing patterns in this skill are placeholders. After authenticating and viewing actual SelfDecode pages, update the grep/sed patterns to match the real HTML structure.

To inspect page structure:

```bash
# After authentication, save a sample page
curl -b "$cookie_jar" -s "https://selfdecode.com/snp/rs429358/" > sample-page.html

# Inspect for relevant elements
grep -i "genotype\|interpretation\|risk" sample-page.html | head -20
```

Common patterns to look for:
- JSON embedded in script tags (`<script type="application/json">`)
- Data attributes (`data-genotype="CT"`)
- Specific CSS classes for genotype/interpretation display
- API responses if using client-side rendering

## Security Considerations

- Credentials stored in environment variables (not in profile YAML)
- Cookie files stored in `/tmp/claude/` (ephemeral)
- Session cookies are not persisted between health-agent sessions
- Never log or cache passwords
- Rate limit to avoid account restrictions
