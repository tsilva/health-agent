---
name: health-dashboard
description: "Interactive Health OS dashboard using AskUserQuestion for profile selection, state initialization, and action menus. Invoke with /health-dashboard or at session start."
invocable: true
---

# Health Dashboard

Interactive entry point for Health OS that guides users through profile selection, state checking, and presents an actionable dashboard with next steps.

## When to Use This Skill

**Automatic triggers**:
- Session start (user initiates conversation)
- User types `/health-dashboard`
- User asks "show my health dashboard" or "health status"

**Manual invocation**:
```
/health-dashboard
```

## Workflow

### Phase 1: Profile Selection

Use AskUserQuestion to let the user select their profile:

```
First, list available profiles:
ls profiles/*.yaml (exclude _template.yaml)

Then use AskUserQuestion:
{
  "questions": [{
    "question": "Which health profile would you like to use?",
    "header": "Profile",
    "options": [
      // Dynamically populate from profiles/*.yaml
      {"label": "{profile_name}", "description": "Load {profile_name}'s health data"}
    ],
    "multiSelect": false
  }]
}
```

After selection, read the profile YAML and extract data source paths.

### Phase 2: State Check

Check if health state exists:

```bash
PROFILE="{selected_profile}"
test -f ".state/${PROFILE}/health-state.yaml" && echo "EXISTS" || echo "MISSING"
```

**If state MISSING**, use AskUserQuestion:
```json
{
  "questions": [{
    "question": "Your health state hasn't been initialized yet. Would you like to set it up now?",
    "header": "Setup",
    "options": [
      {"label": "Yes, initialize (Recommended)", "description": "Create health state from existing data (conditions, medications, actions)"},
      {"label": "Skip for now", "description": "Proceed without persistent state tracking"}
    ],
    "multiSelect": false
  }]
}
```

If user selects "Yes, initialize":
1. Run State Initialization Bootstrap (see CLAUDE.md "State Initialization" section)
2. Continue to Phase 3

If user selects "Skip":
1. Continue to Phase 3 without state features

### Phase 3: Data Freshness Check

If state exists, check for new data:

```bash
# Get last modified times
LABS_MOD=$(stat -f "%Sm" -t "%Y-%m-%d" "{labs_path}/all.csv" 2>/dev/null || echo "N/A")
LOG_MOD=$(stat -f "%Sm" -t "%Y-%m-%d" "{health_log_path}/health_log.csv" 2>/dev/null || echo "N/A")

# Read last_sync from state
grep -A3 "last_sync:" ".state/${PROFILE}/health-state.yaml"
```

Compare timestamps. If new data detected, flag for dashboard display.

### Phase 4: Render Dashboard

Present a formatted dashboard to the user. Use this template:

```
┌─────────────────────────────────────────────────────────────┐
│                    HEALTH DASHBOARD                         │
│                    {Profile Name}                           │
│                    {Date}                                   │
└─────────────────────────────────────────────────────────────┘

{If new data detected}
📊 NEW DATA AVAILABLE
   • Labs updated: {labs_mod_date}
   • Health log updated: {log_mod_date}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACTIVE CONDITIONS                                    CONFIDENCE
──────────────────────────────────────────────────────────────
{condition_1}                                        {XX%}
  └─ Primary: {hypothesis}
{condition_2}                                        {XX%}
  └─ Primary: {hypothesis}
{If no conditions: "No active conditions tracked"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOP ACTIONS                                          PRIORITY
──────────────────────────────────────────────────────────────
{If actions exist}
1. {action_1}                                        {HIGH/MED/LOW}
   Status: {recommended/accepted/in_progress}
   {If due date: "Due: {date}"}
2. {action_2}                                        {priority}
3. {action_3}                                        {priority}

{If no actions: "No pending actions"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CURRENT MEDICATIONS                 SUPPLEMENTS
─────────────────────────          ─────────────────────────
{med_1} ({dose})                   {supp_1} ({dose})
{med_2} ({dose})                   {supp_2} ({dose})
{If none: "None tracked"}          {If none: "None tracked"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GOALS                                                PROGRESS
──────────────────────────────────────────────────────────────
{goal_1}                                             {XX%}
{goal_2}                                             {XX%}
{If no goals: "No active goals"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RECENT ACTIVITY (Last 7 days)
──────────────────────────────────────────────────────────────
{date}: {brief_event_summary}
{date}: {brief_event_summary}
{If none: "No recent activity logged"}
```

### Phase 5: Interactive Menu

After displaying dashboard, use AskUserQuestion to offer next actions:

```json
{
  "questions": [{
    "question": "What would you like to do?",
    "header": "Action",
    "options": [
      {"label": "Review new data", "description": "Analyze recent labs and health events"},
      {"label": "Investigate condition", "description": "Run root cause investigation on a condition"},
      {"label": "Check lab trends", "description": "Track specific biomarker over time"},
      {"label": "Prepare provider visit", "description": "Generate documentation for doctor appointment"}
    ],
    "multiSelect": false
  }]
}
```

**Option handlers**:

**"Review new data"**:
- Show new lab values with reference ranges
- Highlight out-of-range values
- Summarize new health log entries
- Ask: "Any of these need further investigation?"

**"Investigate condition"**:
- If conditions exist, ask which to investigate
- If no conditions, ask what symptom/concern to investigate
- Then invoke `investigate-root-cause` skill

**"Check lab trends"**:
- Ask which marker to track (common options + Other)
- Query and display trend data
- Calculate direction (improving/stable/worsening)

**"Prepare provider visit"**:
- Invoke `prepare-provider-visit` skill

After each action completes, loop back to Phase 5 (show menu again) unless user indicates they're done.

### Phase 6: Continuous Interaction

After each action, offer follow-up:

```json
{
  "questions": [{
    "question": "What's next?",
    "header": "Continue",
    "options": [
      {"label": "Back to dashboard", "description": "Return to main dashboard view"},
      {"label": "Another action", "description": "Choose a different action"},
      {"label": "I'm done", "description": "End this session"}
    ],
    "multiSelect": false
  }]
}
```

## Dashboard Data Extraction

### Extract Conditions from State

```bash
# If state exists
grep -A20 "^conditions:" ".state/${PROFILE}/health-state.yaml" | \
  grep -E "^\s+-\s+name:|confidence:|primary_hypothesis:"
```

### Extract Actions from State

```bash
grep -A30 "^actions:" ".state/${PROFILE}/health-state.yaml" | \
  grep -E "^\s+-\s+id:|action:|priority:|status:|due:"
```

### Extract Medications/Supplements

```bash
grep -A20 "^medications:" ".state/${PROFILE}/health-state.yaml"
grep -A20 "^supplements:" ".state/${PROFILE}/health-state.yaml"
```

### Extract Goals

```bash
grep -A15 "^goals:" ".state/${PROFILE}/health-state.yaml"
```

### Recent Activity (from health_log)

```bash
# Last 7 days
awk -F',' -v start="$(date -v-7d +%Y-%m-%d)" \
  'NR==1 || $1 >= start' "{health_log_path}/health_log.csv" | \
  tail -10
```

## State Update Triggers

During dashboard interactions, proactively offer state updates:

| User Action | Offer to Update |
|-------------|-----------------|
| Marks action complete | Move to completed_actions |
| Reports taking new medication | Add to medications |
| Mentions stopping supplement | Update supplement status |
| Discusses new symptom | Offer to add to health_log |
| Completes investigation | Update conditions, add actions |

Use pattern:
```json
{
  "questions": [{
    "question": "Should I update your health state to reflect this change?",
    "header": "Update",
    "options": [
      {"label": "Yes, update it", "description": "Add this to your persistent health state"},
      {"label": "No, skip", "description": "Don't record this change"}
    ],
    "multiSelect": false
  }]
}
```

## Profile Caching

To improve UX, the dashboard caches the last selected profile:

### Check for cached profile

```bash
LAST_PROFILE=""
if [ -f ".state/.last-profile" ]; then
    LAST_PROFILE=$(cat .state/.last-profile)
fi
```

### Phase 1 with caching

If a cached profile exists, offer it as the first option:

```json
{
  "questions": [{
    "question": "Which health profile would you like to use?",
    "header": "Profile",
    "options": [
      {"label": "{last_profile} (Recommended)", "description": "Continue with your last session's profile"},
      // Other profiles...
    ],
    "multiSelect": false
  }]
}
```

### Save selected profile

After profile selection:

```bash
mkdir -p .state
echo "{selected_profile}" > .state/.last-profile
```

## Atomic State Updates

When writing to health-state.yaml, use atomic operations to prevent corruption:

### Safe State Write Pattern

```bash
PROFILE="{selected_profile}"
STATE_FILE=".state/${PROFILE}/health-state.yaml"
BACKUP_FILE=".state/${PROFILE}/health-state.yaml.bak"
TEMP_FILE=".state/${PROFILE}/health-state.yaml.tmp"

# 1. Create backup of existing state
if [ -f "$STATE_FILE" ]; then
    cp "$STATE_FILE" "$BACKUP_FILE"
fi

# 2. Write to temp file first (use Write tool)
# Write tool writes to $TEMP_FILE

# 3. Validate the new file (basic YAML check)
if python3 -c "import yaml; yaml.safe_load(open('$TEMP_FILE'))" 2>/dev/null; then
    # 4. Atomic move (rename is atomic on most filesystems)
    mv "$TEMP_FILE" "$STATE_FILE"
    echo "State updated successfully"
else
    echo "ERROR: Invalid YAML in new state file"
    rm -f "$TEMP_FILE"
    # State file unchanged, backup still available
fi
```

### Rollback on Error

If state update fails mid-session:

```bash
if [ -f "$BACKUP_FILE" ]; then
    cp "$BACKUP_FILE" "$STATE_FILE"
    echo "Rolled back to previous state"
fi
```

## Data Source Validation

Before loading data, validate all paths exist:

```bash
# Source the helper functions
source .claude/skills/health-agent/references/data-access-helpers.sh

# Validate paths (will print warnings for missing sources)
if ! validate_data_sources "$labs_path" "$health_log_path" "$exams_path"; then
    echo "WARNING: Some data sources are missing"
fi
```

## Error Handling

**Profile not found**:
- List available profiles
- Offer to create new profile (link to _template.yaml)

**State file corrupted**:
- Offer to re-initialize from scratch
- Backup corrupted file first (to `.state/{profile}/health-state.corrupted.{timestamp}`)
- Validate new state with schema before saving

**Data sources missing**:
- Show which sources are unavailable
- Proceed with available data
- Note limitations in dashboard

## Example Session

```
User: /health-dashboard