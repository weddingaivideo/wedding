#!/bin/bash
# Align all language blog filenames to English slugs
# Each language folder should have the same 50 filenames as en/

BASE="/home/work/.openclaw/workspace/weddingai-blogs"
EN_DIR="$BASE/en"

# Get the list of canonical English slugs
CANONICAL=$(ls "$EN_DIR" | sort)

echo "=== Canonical EN slugs (50 files) ==="
echo "$CANONICAL" | wc -l

# For each language, check which files are missing and which are extra
for lang in zh es fr de pt ja ko ar th; do
    LANG_DIR="$BASE/$lang"
    echo ""
    echo "=== Checking $lang ==="
    
    # Check which canonical files exist
    MISSING=0
    for slug in $CANONICAL; do
        if [ ! -f "$LANG_DIR/$slug" ]; then
            MISSING=$((MISSING + 1))
        fi
    done
    
    # Check which files are non-canonical (extra)
    EXTRA=0
    for f in "$LANG_DIR"/*.md; do
        fname=$(basename "$f")
        if ! echo "$CANONICAL" | grep -qx "$fname"; then
            EXTRA=$((EXTRA + 1))
        fi
    done
    
    TOTAL=$(ls "$LANG_DIR" | wc -l)
    echo "  Total: $TOTAL | Missing canonical: $MISSING | Extra (non-canonical): $EXTRA"
done
