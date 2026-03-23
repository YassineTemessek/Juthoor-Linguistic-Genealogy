#!/bin/bash
# Check for new Codex commits and trigger Claude review tasks
cd "/c/Users/yassi/AI Projects/Juthoor-Linguistic-Genealogy"

LAST_KNOWN=$(git rev-parse HEAD)
git pull origin main --quiet 2>/dev/null
CURRENT=$(git rev-parse HEAD)

if [ "$LAST_KNOWN" != "$CURRENT" ]; then
    echo "NEW_COMMITS_FOUND"
    git log --oneline ${LAST_KNOWN}..${CURRENT}

    # Check what changed
    CHANGED=$(git diff --name-only ${LAST_KNOWN}..${CURRENT})

    if echo "$CHANGED" | grep -q "nucleus_score_matrix.json"; then
        echo "TRIGGER: New score matrix — run Method A re-calibration"
    fi
    if echo "$CHANGED" | grep -q "golden_rule_report.json"; then
        echo "TRIGGER: New Golden Rule data — review"
    fi
    if echo "$CHANGED" | grep -q "root_predictions.json\|root_score_matrix.json"; then
        echo "TRIGGER: Root predictions — run Method A on roots"
    fi
    if echo "$CHANGED" | grep -q "feature_decomposition.py\|composition_models.py\|scoring.py"; then
        echo "TRIGGER: Scoring code changed — verify tests"
    fi
else
    echo "NO_NEW_COMMITS"
fi
