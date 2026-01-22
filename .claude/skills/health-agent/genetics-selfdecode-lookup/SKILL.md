---
name: genetics-selfdecode-lookup
description: Look up SNP genotypes from SelfDecode (imputed genetics data). Requires JWT token from browser. Use for expanded SNP coverage beyond 23andMe raw data. Triggers on "check selfdecode for rs...", "selfdecode lookup", "imputed genotype for...", or when SNP not found in 23andMe data.
---

# SelfDecode SNP Lookup

**Authenticated genetics lookup** for SelfDecode's imputed SNP data. SelfDecode provides:
- **Imputed SNPs**: More coverage than raw 23andMe data (~20M+ vs 631k SNPs)
- **Direct API**: Clean JSON responses with genotype data

## Prerequisites

- SelfDecode account with uploaded genetic data
- JWT token copied from browser (see "Getting Your JWT Token" below)
- Profile ID from SelfDecode (see "Getting Your Profile ID" below)

## Configuration

### Profile Setup

Add to your profile YAML:

```yaml
data_sources:
  # Existing genetics source
  genetics_23andme_path: "/path/to/23andme_raw_data.txt"

  # SelfDecode API credentials
  selfdecode:
    enabled: true
    profile_id: "your-profile-uuid"  # From URL: ?profile_id=xxx
    jwt_token: "eyJhbGciOiJSUzI1NiIs..."  # From authorization header (without "JWT " prefix)
```

### Getting Your Credentials

1. Log in to SelfDecode in your browser
2. Open Developer Tools (F12) → Network tab → filter by "genotype"
3. Navigate to any SNP page (e.g., https://selfdecode.com/app/snp/rs429358)
4. Find request to: `/service/health-analysis/genes/genotype/?...`
5. From the **Request URL**, copy the `profile_id` parameter value
6. From **Request Headers**, copy the `authorization` value (just the `eyJ...` part, without the `JWT ` prefix)

**Token lifetime**: JWT tokens expire after ~48 hours. Refresh when you get auth errors.

### Getting Your Profile ID

1. In the same Network request, look at the URL
2. Copy the `profile_id` parameter value (UUID format like `edbd7967-4c2f-45f3-95cf-4c45879d77a4`)
3. Add to your profile YAML

## API Reference

### Endpoint

```
GET https://selfdecode.com/service/health-analysis/genes/genotype/
```

### Required Parameters

| Parameter | Description |
|-----------|-------------|
| `profile_id` | Your SelfDecode profile UUID |
| `rsid` | SNP identifier (e.g., `rs429358`) or comma-separated list |

### Required Headers

| Header | Value |
|--------|-------|
| `authorization` | `JWT {token}` |

## Lookup Workflow

### Single SNP Lookup

```bash
# Set variables from profile (read from profiles/{name}.yaml)
profile_name="{profile name from profiles/{name}.yaml}"
profile_id="{from profile: selfdecode.profile_id}"
jwt_token="{from profile: selfdecode.jwt_token}"
rsid="rs429358"
cache_dir=".claude/skills/health-agent/genetics-selfdecode-lookup/.cache/${profile_name}"

# 1. Check cache first
cache_file="${cache_dir}/${rsid}.json"
if [ -f "$cache_file" ]; then
  # Check cache age (30-day TTL = 2592000 seconds)
  fetched=$(python3 -c "import json; print(json.load(open('$cache_file')).get('fetched', ''))" 2>/dev/null)
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

# 2. Query SelfDecode API
response=$(curl -s "https://selfdecode.com/service/health-analysis/genes/genotype/?profile_id=${profile_id}&rsid=${rsid}" \
  -H "authorization: JWT ${jwt_token}")

# 3. Check for authentication errors (requires user intervention)
if echo "$response" | grep -qE '"detail".*([Aa]uthentication|credentials|signature)'; then
  echo "AUTH_ERROR: JWT token expired or invalid"
  echo "Response: $response"
  echo ""
  echo "ACTION REQUIRED: Prompt user to update JWT token, wait for confirmation, then retry"
  exit 2  # Exit code 2 = auth error
fi

# 4. Check for other errors
if echo "$response" | grep -q '"detail"'; then
  echo "Error: $response"
  exit 1
fi

# 5. Parse and cache response
mkdir -p "$cache_dir"
genotypes=$(echo "$response" | python3 -c "import sys, json; r=json.load(sys.stdin); print(r[0]['genotypes'][0] + r[0]['genotypes'][1] if r else '')")

cat > "$cache_file" << EOF
{
  "rsid": "$rsid",
  "fetched": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "ttl_seconds": 2592000,
  "source": "selfdecode",
  "data": {
    "genotype": "$genotypes",
    "raw_response": $response
  }
}
EOF

echo "Cached SelfDecode data for $rsid: $genotypes"
cat "$cache_file"
```

### Batch SNP Lookup

SelfDecode supports comma-separated rsids for efficient batch queries:

```bash
# Batch query - up to ~50 SNPs per request
rsids="rs429358,rs7412,rs1801133"

response=$(curl -s "https://selfdecode.com/service/health-analysis/genes/genotype/?profile_id=${profile_id}&rsid=${rsids}" \
  -H "authorization: JWT ${jwt_token}")

# Returns array of results:
# [
#   {"profile_id":"...","rsid":"rs429358","variant_ids":["ref","ref"],"genotypes":["T","T"]},
#   {"profile_id":"...","rsid":"rs7412","variant_ids":["ref","ref"],"genotypes":["C","C"]},
#   ...
# ]
```

## Response Format

### Success Response

```json
[{
  "profile_id": "edbd7967-4c2f-45f3-95cf-4c45879d77a4",
  "rsid": "rs429358",
  "variant_ids": ["ref", "ref"],
  "genotypes": ["T", "T"]
}]
```

| Field | Description |
|-------|-------------|
| `profile_id` | Your SelfDecode profile UUID |
| `rsid` | The queried SNP |
| `variant_ids` | Allele types (`ref` = reference, or variant ID) |
| `genotypes` | The two alleles (diploid) |

### Error Responses

| Error | Meaning |
|-------|---------|
| `{"detail":"Incorrect authentication credentials."}` | JWT expired or invalid |
| `{"profile_id":"This field is required."}` | Missing profile_id parameter |
| `[]` | SNP not found in SelfDecode database |

## Caching Layer

**Cache directory**: `.claude/skills/health-agent/genetics-selfdecode-lookup/.cache/{profile_name}/`

**Cache TTL**: 30 days (2,592,000 seconds)

**Profile partitioning**: Cache is partitioned by profile name to prevent data leakage between profiles. Each profile's genotype data is stored in its own subdirectory.

### Cache File Format

Each rsID gets a JSON cache file: `.cache/{profile_name}/{rsid}.json`

```json
{
  "rsid": "rs429358",
  "fetched": "2026-01-22T17:00:00Z",
  "ttl_seconds": 2592000,
  "source": "selfdecode",
  "data": {
    "genotype": "TT",
    "raw_response": [{"profile_id":"...","rsid":"rs429358","variant_ids":["ref","ref"],"genotypes":["T","T"]}]
  }
}
```

## Output Format

### Single SNP Result

```markdown
## SelfDecode SNP Lookup: rs429358

**Source**: SelfDecode (imputed)
**Genotype**: T/T
**Variant IDs**: ref/ref (homozygous reference)

**Data Retrieved**: 2026-01-22 (fresh)
```

### Batch Result

```markdown
## SelfDecode Batch Lookup

| rsID | Genotype | Variant IDs |
|------|----------|-------------|
| rs429358 | T/T | ref/ref |
| rs7412 | C/C | ref/ref |
| rs1801133 | C/T | ref/alt |

**Data Retrieved**: 2026-01-22
```

## Error Handling

| Scenario | Response |
|----------|----------|
| **JWT not set** | Error: "jwt_token not configured in profile. Copy from browser." |
| **JWT expired** | Prompt user to update token (see Authentication Error Recovery below) |
| **Profile ID missing** | Error: "profile_id not configured in profile YAML" |
| **SNP not found** | Note: "SNP {rsid} not in SelfDecode database (empty response)" |
| **API unavailable (with cache)** | Warning: "SelfDecode unavailable, using stale cache (age: X days)" |

### Authentication Error Recovery

When a request fails due to authentication issues (JWT expired or invalid), follow this workflow:

**1. Detect authentication errors** - Check for these response patterns:
```json
{"detail":"Incorrect authentication credentials."}
{"detail":"Authentication credentials were not provided."}
{"detail":"Error decoding signature."}
```

**2. Prompt the user** with this message:

```
## SelfDecode Authentication Error

Your JWT token has expired or is invalid. To continue:

1. Log in to SelfDecode in your browser
2. Open Developer Tools (F12) → Network tab
3. Navigate to any SNP page (e.g., https://selfdecode.com/app/snp/rs429358)
4. Find request to `/service/health-analysis/genes/genotype/`
5. From Request Headers, copy the `authorization` value (just the `eyJ...` part)
6. Update your profile YAML with the new token:
   ```yaml
   data_sources:
     selfdecode:
       jwt_token: "eyJ..."  # Paste new token here
   ```

**Reply "done" or "updated" when you've refreshed the token**, and I'll retry the lookup.
```

**3. Wait for user confirmation** - Do not proceed until user confirms token update

**4. Re-read the profile** to get the new token:
```bash
# Re-read profile YAML to get updated jwt_token
cat profiles/{profile_name}.yaml | grep -A5 "selfdecode:"
```

**5. Retry the original request** with the new token

### Implementation Example

```bash
# After curl request, check for auth errors
if echo "$response" | grep -qE '"detail".*([Aa]uthentication|credentials|signature)'; then
  echo "AUTH_ERROR: JWT token expired or invalid"
  echo "Prompt user to update token and wait for confirmation before retrying"
  exit 2  # Exit code 2 = auth error (distinct from other errors)
fi
```

**Important**: When you detect an auth error:
1. **Stop the current operation** - don't continue with stale/invalid credentials
2. **Inform the user clearly** - explain what happened and how to fix it
3. **Wait for explicit confirmation** - user must say they've updated the token
4. **Re-read the profile** - don't use cached credentials, read fresh from YAML
5. **Retry the exact same operation** - resume from where you left off

## Integration Notes

### When to Use SelfDecode vs SNPedia

| Use SelfDecode | Use SNPedia (genetics-snp-lookup) |
|----------------|-----------------------------------|
| SNP not in 23andMe raw data | SNP is in 23andMe raw data |
| User specifically requests SelfDecode | Need research citations/mechanisms |
| Checking imputed genotypes | Need interpretation context |
| Batch lookups for efficiency | Public interpretation needed |

### Lookup Strategy

For comprehensive SNP investigation:

1. **First**: Check 23andMe raw data via `genetics-snp-lookup` (directly genotyped, most reliable)
2. **Second**: If not found and SelfDecode configured, check `genetics-selfdecode-lookup` for imputed data
3. **Third**: Always query SNPedia for interpretation (research citations, mechanisms)

### Cross-Referencing

When both sources have data for the same SNP:

```markdown
## SNP Comparison: rs429358

| Source | Genotype | Notes |
|--------|----------|-------|
| 23andMe (raw) | T;T | Directly genotyped |
| SelfDecode (imputed) | T;T | Matches raw data |

**Concordance**: Sources agree. High confidence.
```

**Note**: If sources disagree, prefer 23andMe raw data (directly genotyped) over SelfDecode (imputed).

## Security Notes

- JWT tokens are sensitive - never commit to git
- Store JWT in environment variable, not in profile YAML
- Tokens expire after 24-48 hours - refresh as needed
- Cache files contain only genotype data, not credentials
