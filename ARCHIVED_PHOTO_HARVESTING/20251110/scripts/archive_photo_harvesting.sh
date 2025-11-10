#!/bin/bash
# Archive Photo-harvesting functionality before removal
# This script creates an archive of all Photo-harvesting related files

ARCHIVE_DIR="ARCHIVED_PHOTO_HARVESTING"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_DIR_WITH_TIMESTAMP="${ARCHIVE_DIR}_${TIMESTAMP}"

echo "Creating Photo-harvesting archive: ${ARCHIVE_DIR_WITH_TIMESTAMP}"

# Create archive structure
mkdir -p "${ARCHIVE_DIR_WITH_TIMESTAMP}"/{code/utils,code/blueprints,templates,static/js,static/css,migrations,data}

# Archive code files
echo "Archiving code files..."
if [ -f "utils/photo_apis.py" ]; then
    cp utils/photo_apis.py "${ARCHIVE_DIR_WITH_TIMESTAMP}/code/utils/"
    echo "  ✓ utils/photo_apis.py"
fi
if [ -f "utils/photo_apis_adapter.py" ]; then
    cp utils/photo_apis_adapter.py "${ARCHIVE_DIR_WITH_TIMESTAMP}/code/utils/"
    echo "  ✓ utils/photo_apis_adapter.py"
fi
if [ -f "utils/photo_harvesting_storage.py" ]; then
    cp utils/photo_harvesting_storage.py "${ARCHIVE_DIR_WITH_TIMESTAMP}/code/utils/"
    echo "  ✓ utils/photo_harvesting_storage.py"
fi
if [ -f "utils/photo_search_store.py" ]; then
    cp utils/photo_search_store.py "${ARCHIVE_DIR_WITH_TIMESTAMP}/code/utils/"
    echo "  ✓ utils/photo_search_store.py"
fi
if [ -f "blueprints/authoring_api_photography.py" ]; then
    cp blueprints/authoring_api_photography.py "${ARCHIVE_DIR_WITH_TIMESTAMP}/code/blueprints/"
    echo "  ✓ blueprints/authoring_api_photography.py"
fi

# Archive templates
echo "Archiving templates..."
if [ -f "templates/imaging/includes/photo_search_panel.html" ]; then
    cp templates/imaging/includes/photo_search_panel.html "${ARCHIVE_DIR_WITH_TIMESTAMP}/templates/"
    echo "  ✓ templates/imaging/includes/photo_search_panel.html"
fi
if [ -f "templates/authoring/includes/output_panel_photo_harvesting.html" ]; then
    cp templates/authoring/includes/output_panel_photo_harvesting.html "${ARCHIVE_DIR_WITH_TIMESTAMP}/templates/"
    echo "  ✓ templates/authoring/includes/output_panel_photo_harvesting.html"
fi
if [ -f "templates/imaging/sections/photo_selection.html" ]; then
    cp templates/imaging/sections/photo_selection.html "${ARCHIVE_DIR_WITH_TIMESTAMP}/templates/"
    echo "  ✓ templates/imaging/sections/photo_selection.html"
fi

# Archive static JS files
echo "Archiving JavaScript files..."
find static/js -name "*photo*.js" -o -name "*harvest*.js" | while read file; do
    cp "$file" "${ARCHIVE_DIR_WITH_TIMESTAMP}/static/js/"
    echo "  ✓ $file"
done

# Archive static CSS files
echo "Archiving CSS files..."
if [ -f "static/css/imaging/photo-selection.css" ]; then
    cp static/css/imaging/photo-selection.css "${ARCHIVE_DIR_WITH_TIMESTAMP}/static/css/"
    echo "  ✓ static/css/imaging/photo-selection.css"
fi

# Archive migrations
echo "Archiving migrations..."
find migrations -name "*photo*.sql" -o -name "*harvest*.sql" | while read file; do
    cp "$file" "${ARCHIVE_DIR_WITH_TIMESTAMP}/migrations/"
    echo "  ✓ $file"
done

# Create README
cat > "${ARCHIVE_DIR_WITH_TIMESTAMP}/README.md" << 'EOF'
# Photo-harvesting Archive

## What Was Archived
This directory contains Photo-harvesting functionality that was deprecated and removed.

## Why Archived
Photo-harvesting (Pexels/Unsplash integration) was deprecated to:
- Unify recipe and theme post processes
- Simplify image pipeline (LLM-generated images only)
- Reduce external dependencies
- Eliminate code duplication between recipe and theme posts

## When Archived
[Date will be filled in by script]

## Recovery
If Photo-harvesting functionality is needed:
1. Review archived files
2. Identify required functionality
3. Re-implement if necessary (don't just restore - code may be outdated)
4. Consider if LLM-generated images can meet the need instead

## Files Archived
- Code: Photo API clients, adapters, storage utilities
- Templates: Photo search and selection panels
- Static: JavaScript and CSS for Photo-harvesting UI
- Migrations: Database migrations related to Photo-harvesting
EOF

# Update README with timestamp
sed -i '' "s/\[Date will be filled in by script\]/$(date)/" "${ARCHIVE_DIR_WITH_TIMESTAMP}/README.md"

echo ""
echo "✅ Photo-harvesting files archived to ${ARCHIVE_DIR_WITH_TIMESTAMP}"
echo ""
echo "Next steps:"
echo "1. Review archived files"
echo "2. Remove Photo-harvesting code from active codebase"
echo "3. Test that system works without Photo-harvesting"
echo "4. Archive Photo-harvesting data files (JSON) separately"

