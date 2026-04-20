#!/bin/bash
# Architecture boundary enforcement hook
# Blocks banned imports in engine/ and api/ files
# Reads tool input from stdin (JSON with file_path and new_string/content)

set -e

INPUT=$(cat)

# Extract file path from tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if [ -z "$FILE_PATH" ]; then
    exit 0  # No file path — not a file edit, allow
fi

# Extract the content being written/edited
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty')
if [ -z "$CONTENT" ]; then
    exit 0  # No content to check, allow
fi

# Check engine/ files for banned imports
if echo "$FILE_PATH" | grep -q "/engine/"; then
    VIOLATIONS=""
    if echo "$CONTENT" | grep -qE "^(from |import )(sqlalchemy|litestar|celery)"; then
        VIOLATIONS="$VIOLATIONS sqlalchemy/litestar/celery"
    fi
    if echo "$CONTENT" | grep -qE "^from app\.(models|services)"; then
        VIOLATIONS="$VIOLATIONS app.models/app.services"
    fi
    if [ -n "$VIOLATIONS" ]; then
        echo "BLOCKED: engine/ files cannot import:$VIOLATIONS. Engine must be pure computation with no DB/framework dependencies." >&2
        exit 2
    fi
fi

# Check api/ files for direct sqlalchemy imports
if echo "$FILE_PATH" | grep -q "/api/"; then
    if echo "$CONTENT" | grep -qE "^(from |import )sqlalchemy"; then
        echo "BLOCKED: api/ controllers cannot import sqlalchemy directly. Use services for DB access." >&2
        exit 2
    fi
fi

exit 0
