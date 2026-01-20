#!/bin/bash

# Lab Specs JSON Helper Functions
#
# These functions provide a centralized interface for querying lab_specs.json
# when it exists in the labs-parser output directory. All functions gracefully
# handle missing files by returning empty strings, allowing skills to fall back
# to manual patterns.
#
# Usage:
#   source .claude/skills/health-agent/references/lab-specs-helpers.sh
#   canonical=$(get_canonical_name "$labs_path/lab_specs.json" "HbA1c")
#   pattern=$(build_grep_pattern "$labs_path/lab_specs.json" "glucose")

# Check if lab_specs.json exists and is readable
# Args: $1 = path to lab_specs.json
# Returns: 0 if exists and readable, 1 otherwise
has_lab_specs() {
    local specs_file="$1"
    [ -f "$specs_file" ] && [ -r "$specs_file" ]
}

# Get canonical name for a marker by name or alias
# Args: $1 = path to lab_specs.json, $2 = marker name or alias
# Returns: canonical name, or empty string if not found or file missing
get_canonical_name() {
    local specs_file="$1"
    local search_term="$2"

    if ! has_lab_specs "$specs_file"; then
        return
    fi

    # Search for marker where canonical_name or any alias matches (case-insensitive)
    jq -r --arg term "${search_term,,}" '
        .markers[]?
        | select(
            (.canonical_name // "" | ascii_downcase | contains($term)) or
            (.aliases[]? // "" | ascii_downcase | contains($term))
        )
        | .canonical_name // empty
    ' "$specs_file" 2>/dev/null | head -n1
}

# Get all aliases for a marker (including canonical name)
# Args: $1 = path to lab_specs.json, $2 = marker name or alias
# Returns: newline-separated list of aliases, or empty if not found
get_aliases() {
    local specs_file="$1"
    local search_term="$2"

    if ! has_lab_specs "$specs_file"; then
        return
    fi

    # First get canonical name, then get all aliases for that marker
    local canonical
    canonical=$(get_canonical_name "$specs_file" "$search_term")

    if [ -z "$canonical" ]; then
        return
    fi

    jq -r --arg canon "$canonical" '
        .markers[]?
        | select(.canonical_name == $canon)
        | (.canonical_name, .aliases[]?)
    ' "$specs_file" 2>/dev/null
}

# Build grep pattern from marker aliases (pipe-separated, for grep -E)
# Args: $1 = path to lab_specs.json, $2 = marker name or alias
# Returns: grep pattern like "HbA1c|Hemoglobin A1c|A1C", or empty if not found
build_grep_pattern() {
    local specs_file="$1"
    local search_term="$2"

    if ! has_lab_specs "$specs_file"; then
        return
    fi

    # Get aliases and join with pipe for grep -E pattern
    local aliases
    aliases=$(get_aliases "$specs_file" "$search_term")

    if [ -z "$aliases" ]; then
        return
    fi

    # Convert newlines to pipes, escape special regex chars
    echo "$aliases" | sed 's/[.^$*+?()[{\\|]/\\&/g' | paste -sd'|' -
}

# Get primary unit for a marker
# Args: $1 = path to lab_specs.json, $2 = marker name or alias
# Returns: primary unit (e.g., "%", "mg/dL"), or empty if not found
get_primary_unit() {
    local specs_file="$1"
    local search_term="$2"

    if ! has_lab_specs "$specs_file"; then
        return
    fi

    local canonical
    canonical=$(get_canonical_name "$specs_file" "$search_term")

    if [ -z "$canonical" ]; then
        return
    fi

    jq -r --arg canon "$canonical" '
        .markers[]?
        | select(.canonical_name == $canon)
        | .primary_unit // empty
    ' "$specs_file" 2>/dev/null
}

# Get conversion factor from one unit to another
# Args: $1 = path to lab_specs.json, $2 = marker name, $3 = from_unit, $4 = to_unit
# Returns: conversion factor (multiply by this to convert), or empty if not found
# Note: Returns 1.0 if from_unit == to_unit, empty if conversion not available
get_conversion_factor() {
    local specs_file="$1"
    local search_term="$2"
    local from_unit="$3"
    local to_unit="$4"

    if ! has_lab_specs "$specs_file"; then
        return
    fi

    # If units are the same, return 1.0
    if [ "$from_unit" = "$to_unit" ]; then
        echo "1.0"
        return
    fi

    local canonical
    canonical=$(get_canonical_name "$specs_file" "$search_term")

    if [ -z "$canonical" ]; then
        return
    fi

    # Check if from_unit is primary and to_unit is in conversion_factors
    local primary_unit
    primary_unit=$(get_primary_unit "$specs_file" "$search_term")

    if [ "$from_unit" = "$primary_unit" ]; then
        # Converting from primary to other: use conversion factor directly
        jq -r --arg canon "$canonical" --arg to "$to_unit" '
            .markers[]?
            | select(.canonical_name == $canon)
            | .conversion_factors[$to] // empty
        ' "$specs_file" 2>/dev/null
    elif [ "$to_unit" = "$primary_unit" ]; then
        # Converting from other to primary: use 1/conversion_factor
        jq -r --arg canon "$canonical" --arg from "$from_unit" '
            .markers[]?
            | select(.canonical_name == $canon)
            | (.conversion_factors[$from] // empty) as $factor
            | if $factor != "" then 1 / $factor else empty end
        ' "$specs_file" 2>/dev/null
    else
        # Converting between two non-primary units: not supported
        return
    fi
}

# Get reference range for a marker
# Args: $1 = path to lab_specs.json, $2 = marker name or alias
# Returns: "min max" as space-separated values, or empty if not found
get_reference_range() {
    local specs_file="$1"
    local search_term="$2"

    if ! has_lab_specs "$specs_file"; then
        return
    fi

    local canonical
    canonical=$(get_canonical_name "$specs_file" "$search_term")

    if [ -z "$canonical" ]; then
        return
    fi

    jq -r --arg canon "$canonical" '
        .markers[]?
        | select(.canonical_name == $canon)
        | "\(.reference_range.min // "") \(.reference_range.max // "")"
    ' "$specs_file" 2>/dev/null | grep -v "^[[:space:]]*$"
}

# Example usage patterns:
#
# # Check if lab_specs.json is available
# if has_lab_specs "$labs_path/lab_specs.json"; then
#     pattern=$(build_grep_pattern "$labs_path/lab_specs.json" "hba1c")
#     grep -iE "$pattern" "$labs_path/all.csv"
# else
#     # Fall back to manual pattern
#     grep -i "hemoglobin a1c\|glycated hemoglobin\|a1c" "$labs_path/all.csv"
# fi
#
# # Get canonical name for display
# canonical=$(get_canonical_name "$labs_path/lab_specs.json" "a1c")
# echo "Tracking marker: $canonical"
#
# # Convert units
# factor=$(get_conversion_factor "$labs_path/lab_specs.json" "glucose" "mg/dL" "mmol/L")
# if [ -n "$factor" ]; then
#     converted=$(echo "$value * $factor" | bc -l)
# fi
