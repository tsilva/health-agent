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

# Example usage patterns:
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
