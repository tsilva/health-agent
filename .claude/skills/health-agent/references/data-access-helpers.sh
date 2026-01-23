#!/bin/bash

# Data Access Helper Functions
#
# Standardized extraction patterns for large health data files.
# These functions handle the common case of extracting filtered data
# from CSV files that exceed Claude's 256KB read limit.
#
# Usage:
#   source .claude/skills/health-agent/references/data-access-helpers.sh
#   recent_labs=$(get_recent_labs "$labs_path" "HbA1c" 10)
#   abnormal=$(get_abnormal_labs "$labs_path" "2025-01-01")

# Get recent lab values for a specific marker
# Args: $1 = labs_path, $2 = marker name/pattern, $3 = limit (default 10)
# Returns: CSV rows matching the marker, most recent first
get_recent_labs() {
    local labs_path="$1"
    local marker="$2"
    local limit="${3:-10}"
    local all_csv="${labs_path}/all.csv"

    if [ ! -f "$all_csv" ]; then
        echo "ERROR: Labs file not found: $all_csv" >&2
        return 1
    fi

    # Use lab_specs.json if available for better matching
    local specs_file="${labs_path}/lab_specs.json"
    local pattern="$marker"

    if [ -f "$specs_file" ]; then
        source .claude/skills/health-agent/references/lab-specs-helpers.sh 2>/dev/null
        local built_pattern
        built_pattern=$(build_grep_pattern "$specs_file" "$marker")
        if [ -n "$built_pattern" ]; then
            pattern="$built_pattern"
        fi
    fi

    # Extract matching rows, sort by date descending, limit results
    grep -iE "$pattern" "$all_csv" | sort -t',' -k1 -r | head -n "$limit"
}

# Get all abnormal lab values within a date range
# Args: $1 = labs_path, $2 = start_date (YYYY-MM-DD), $3 = end_date (optional, defaults to today)
# Returns: CSV rows where value is outside reference range
get_abnormal_labs() {
    local labs_path="$1"
    local start_date="$2"
    local end_date="${3:-$(date +%Y-%m-%d)}"
    local all_csv="${labs_path}/all.csv"

    if [ ! -f "$all_csv" ]; then
        echo "ERROR: Labs file not found: $all_csv" >&2
        return 1
    fi

    # Filter by date range and check if value is outside reference range
    # CSV columns: date,source_file,page_number,lab_name,value,unit,reference_min,reference_max,confidence
    awk -F',' -v start="$start_date" -v end="$end_date" '
        NR == 1 { next }  # Skip header
        $1 >= start && $1 <= end {
            if ($5 != "" && $7 != "" && $8 != "") {
                if ($5 < $7 || $5 > $8) {
                    print
                }
            }
        }
    ' "$all_csv"
}

# Get health log entries by category
# Args: $1 = health_log_path, $2 = category (medication, supplement, symptom, condition, etc.), $3 = limit (default 50)
# Returns: CSV rows for the specified category
get_health_log_by_category() {
    local health_log_path="$1"
    local category="$2"
    local limit="${3:-50}"
    local health_log_csv="${health_log_path}/health_log.csv"

    if [ ! -f "$health_log_csv" ]; then
        echo "ERROR: Health log not found: $health_log_csv" >&2
        return 1
    fi

    grep -i ",$category," "$health_log_csv" | tail -n "$limit"
}

# Get recent health events within date range
# Args: $1 = health_log_path, $2 = days_back (default 7)
# Returns: CSV rows from the last N days
get_recent_health_events() {
    local health_log_path="$1"
    local days_back="${2:-7}"
    local health_log_csv="${health_log_path}/health_log.csv"

    if [ ! -f "$health_log_csv" ]; then
        echo "ERROR: Health log not found: $health_log_csv" >&2
        return 1
    fi

    local start_date
    # macOS date syntax
    start_date=$(date -v-${days_back}d +%Y-%m-%d 2>/dev/null || date -d "-${days_back} days" +%Y-%m-%d)

    awk -F',' -v start="$start_date" 'NR==1 || $1 >= start' "$health_log_csv" | tail -50
}

# Get active medications from health log
# Args: $1 = health_log_path
# Returns: Most recent medication entries (use status-keywords.md to determine active status)
get_medications() {
    local health_log_path="$1"
    local health_log_csv="${health_log_path}/health_log.csv"

    if [ ! -f "$health_log_csv" ]; then
        echo "ERROR: Health log not found: $health_log_csv" >&2
        return 1
    fi

    grep -E ",medication," "$health_log_csv" | tail -50
}

# Get active supplements from health log
# Args: $1 = health_log_path
# Returns: Most recent supplement entries
get_supplements() {
    local health_log_path="$1"
    local health_log_csv="${health_log_path}/health_log.csv"

    if [ ! -f "$health_log_csv" ]; then
        echo "ERROR: Health log not found: $health_log_csv" >&2
        return 1
    fi

    grep -E ",supplement," "$health_log_csv" | tail -50
}

# Get conditions from health log
# Args: $1 = health_log_path
# Returns: Recent condition entries
get_conditions() {
    local health_log_path="$1"
    local health_log_csv="${health_log_path}/health_log.csv"

    if [ ! -f "$health_log_csv" ]; then
        echo "ERROR: Health log not found: $health_log_csv" >&2
        return 1
    fi

    grep -E ",condition," "$health_log_csv" | tail -50
}

# Validate data source paths from profile
# Args: $1 = labs_path, $2 = health_log_path, $3 = exams_path
# Returns: 0 if all valid, 1 if any missing (prints warnings)
validate_data_sources() {
    local labs_path="$1"
    local health_log_path="$2"
    local exams_path="$3"
    local valid=0

    if [ ! -f "${labs_path}/all.csv" ]; then
        echo "WARNING: Labs file not found: ${labs_path}/all.csv" >&2
        valid=1
    fi

    if [ ! -f "${health_log_path}/health_log.csv" ]; then
        echo "WARNING: Health log not found: ${health_log_path}/health_log.csv" >&2
        valid=1
    fi

    if [ ! -d "$exams_path" ]; then
        echo "WARNING: Exams directory not found: $exams_path" >&2
        valid=1
    fi

    return $valid
}

# Get file modification date (cross-platform)
# Args: $1 = file_path
# Returns: YYYY-MM-DD of last modification
get_file_mod_date() {
    local file_path="$1"

    if [ ! -f "$file_path" ]; then
        echo "N/A"
        return 1
    fi

    # Try macOS format first, fall back to Linux
    stat -f "%Sm" -t "%Y-%m-%d" "$file_path" 2>/dev/null || \
    stat -c "%y" "$file_path" 2>/dev/null | cut -d' ' -f1
}

# =============================================================================
# Network Error Handling Functions
# =============================================================================

# Retry a command with exponential backoff
# Args: $1 = max_retries, $2+ = command to run
# Returns: 0 on success, 1 on failure after all retries
# Example: retry_with_backoff 3 curl -s "https://api.example.com/data"
retry_with_backoff() {
    local max_retries="$1"
    shift
    local cmd="$@"
    local attempt=1
    local delay=1  # Start with 1 second delay

    while [ $attempt -le $max_retries ]; do
        if eval "$cmd"; then
            return 0
        fi

        local exit_code=$?

        if [ $attempt -lt $max_retries ]; then
            echo "Attempt $attempt failed (exit code $exit_code), retrying in ${delay}s..." >&2
            sleep $delay
            delay=$((delay * 2))  # Exponential backoff: 1, 2, 4, 8...
            attempt=$((attempt + 1))
        else
            echo "All $max_retries attempts failed" >&2
            return 1
        fi
    done
}

# Execute a command with timeout
# Args: $1 = timeout_seconds, $2+ = command to run
# Returns: 0 on success, 124 on timeout, other on command failure
# Example: handle_timeout 30 curl -s "https://api.example.com/data"
handle_timeout() {
    local timeout_seconds="$1"
    shift
    local cmd="$@"

    # Check if 'timeout' command is available (GNU coreutils)
    if command -v timeout >/dev/null 2>&1; then
        timeout "$timeout_seconds" bash -c "$cmd"
        return $?
    # Check if 'gtimeout' is available (macOS with coreutils)
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout "$timeout_seconds" bash -c "$cmd"
        return $?
    else
        # Fallback: use background process with kill
        eval "$cmd" &
        local pid=$!
        local count=0

        while [ $count -lt $timeout_seconds ]; do
            if ! kill -0 $pid 2>/dev/null; then
                wait $pid
                return $?
            fi
            sleep 1
            count=$((count + 1))
        done

        # Timeout reached, kill the process
        kill -9 $pid 2>/dev/null
        wait $pid 2>/dev/null
        echo "Command timed out after ${timeout_seconds}s" >&2
        return 124
    fi
}

# Validate JSON response from API
# Args: $1 = json_file or json_string (use - for stdin)
# Returns: 0 if valid JSON, 1 if invalid or empty
# Example: echo '{"key": "value"}' | validate_json_response -
# Example: validate_json_response "/tmp/response.json"
validate_json_response() {
    local input="$1"
    local json_content

    if [ "$input" = "-" ]; then
        json_content=$(cat)
    elif [ -f "$input" ]; then
        json_content=$(cat "$input")
    else
        json_content="$input"
    fi

    # Check if empty
    if [ -z "$json_content" ]; then
        echo "ERROR: Empty JSON response" >&2
        return 1
    fi

    # Try to parse with Python (most reliable)
    if command -v python3 >/dev/null 2>&1; then
        if echo "$json_content" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
            return 0
        else
            echo "ERROR: Invalid JSON format" >&2
            return 1
        fi
    # Fallback to jq if available
    elif command -v jq >/dev/null 2>&1; then
        if echo "$json_content" | jq . >/dev/null 2>&1; then
            return 0
        else
            echo "ERROR: Invalid JSON format" >&2
            return 1
        fi
    else
        # Basic check: starts with { or [ and ends with } or ]
        if echo "$json_content" | grep -qE '^\s*[\[{].*[\]}]\s*$'; then
            return 0
        else
            echo "ERROR: JSON validation unavailable and basic check failed" >&2
            return 1
        fi
    fi
}

# Validate YAML file structure
# Args: $1 = yaml_file_path
# Returns: 0 if valid YAML, 1 if invalid
# Example: validate_yaml_file ".state/profile/health-state.yaml"
validate_yaml_file() {
    local yaml_file="$1"

    if [ ! -f "$yaml_file" ]; then
        echo "ERROR: YAML file not found: $yaml_file" >&2
        return 1
    fi

    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import yaml; yaml.safe_load(open('$yaml_file'))" 2>/dev/null; then
            return 0
        else
            echo "ERROR: Invalid YAML in $yaml_file" >&2
            return 1
        fi
    else
        # Basic check: file is not empty and doesn't have obvious syntax errors
        if [ -s "$yaml_file" ]; then
            # Check for common YAML issues
            if grep -qE '^\s+[^\s].*:\s*$' "$yaml_file" 2>/dev/null; then
                return 0  # Has YAML-like structure
            fi
        fi
        echo "WARNING: YAML validation unavailable, basic check only" >&2
        return 0
    fi
}

# Safe atomic file write (prevents corruption on partial writes)
# Args: $1 = target_file, $2 = content (use - for stdin)
# Returns: 0 on success, 1 on failure
# Example: echo "new content" | safe_atomic_write "/path/to/file.yaml" -
safe_atomic_write() {
    local target_file="$1"
    local content_source="$2"
    local temp_file="${target_file}.tmp.$$"
    local backup_file="${target_file}.bak"

    # Get content
    local content
    if [ "$content_source" = "-" ]; then
        content=$(cat)
    else
        content="$content_source"
    fi

    # Ensure directory exists
    local dir=$(dirname "$target_file")
    mkdir -p "$dir" 2>/dev/null

    # Backup existing file if present
    if [ -f "$target_file" ]; then
        cp "$target_file" "$backup_file" 2>/dev/null
    fi

    # Write to temp file
    echo "$content" > "$temp_file"

    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to write temp file" >&2
        rm -f "$temp_file"
        return 1
    fi

    # Atomic rename
    mv "$temp_file" "$target_file"

    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to move temp file to target" >&2
        # Restore from backup if available
        if [ -f "$backup_file" ]; then
            cp "$backup_file" "$target_file"
        fi
        rm -f "$temp_file"
        return 1
    fi

    return 0
}

# Combined: Fetch URL with timeout, retry, and JSON validation
# Args: $1 = url, $2 = output_file, $3 = timeout (default 30), $4 = retries (default 3)
# Returns: 0 on success with valid JSON, 1 on failure
# Example: fetch_json_with_retry "https://api.example.com/data" "/tmp/output.json"
fetch_json_with_retry() {
    local url="$1"
    local output_file="$2"
    local timeout="${3:-30}"
    local retries="${4:-3}"

    local fetch_cmd="curl -A 'health-agent/1.0' -s -f '$url' > '$output_file'"

    if retry_with_backoff "$retries" "handle_timeout $timeout \"$fetch_cmd\""; then
        if validate_json_response "$output_file"; then
            return 0
        else
            echo "ERROR: Received invalid JSON from $url" >&2
            return 1
        fi
    else
        echo "ERROR: Failed to fetch $url after $retries attempts" >&2
        return 1
    fi
}

# =============================================================================
# Example usage patterns
# =============================================================================
#
# # Get recent HbA1c values
# recent=$(get_recent_labs "$labs_path" "HbA1c" 5)
# echo "$recent"
#
# # Get abnormal labs from last year
# abnormal=$(get_abnormal_labs "$labs_path" "2025-01-01")
# echo "$abnormal" | wc -l  # Count abnormal values
#
# # Get active medications
# meds=$(get_medications "$health_log_path")
# echo "$meds"
#
# # Validate paths before processing
# if validate_data_sources "$labs_path" "$health_log_path" "$exams_path"; then
#     echo "All data sources available"
# else
#     echo "Some data sources missing"
# fi
#
# # Fetch API data with retry and validation
# if fetch_json_with_retry "https://api.example.com/data" "/tmp/data.json" 30 3; then
#     echo "Successfully fetched and validated JSON"
#     cat /tmp/data.json
# else
#     echo "Failed to fetch valid JSON"
# fi
#
# # Atomic file write (prevents corruption)
# echo "new content" | safe_atomic_write "/path/to/file.yaml" -
