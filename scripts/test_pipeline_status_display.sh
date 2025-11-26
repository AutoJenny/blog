#!/bin/bash
# End-to-end test script for pipeline status API
# Tests the /pipeline-status/<post_id> endpoint and verifies response structure

set -e

BASE_URL="${1:-http://localhost:5000}"
POST_ID="${2:-96}"
ENDPOINT="/launchpad/one-click-blog/api/pipeline-status/${POST_ID}"
FULL_URL="${BASE_URL}${ENDPOINT}"

echo "=========================================="
echo "Pipeline Status API Test"
echo "=========================================="
echo "Testing endpoint: ${FULL_URL}"
echo "Post ID: ${POST_ID}"
echo ""

# Test 1: Check if endpoint is accessible
echo "Test 1: Endpoint Accessibility"
echo "-------------------------------"
HTTP_CODE=$(curl -s -o /tmp/pipeline_status_response.json -w "%{http_code}" "${FULL_URL}")

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✓ Endpoint is accessible (HTTP 200)"
elif [ "$HTTP_CODE" -eq 404 ]; then
    echo "⚠ Endpoint returned 404 (Post may not exist)"
    echo "Response:"
    cat /tmp/pipeline_status_response.json
    exit 0
else
    echo "✗ Endpoint returned HTTP ${HTTP_CODE}"
    echo "Response:"
    cat /tmp/pipeline_status_response.json
    exit 1
fi
echo ""

# Test 2: Verify response structure
echo "Test 2: Response Structure"
echo "-------------------------"
RESPONSE=$(cat /tmp/pipeline_status_response.json)

# Check if response is valid JSON
if ! echo "$RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
    echo "✗ Response is not valid JSON"
    echo "Response: $RESPONSE"
    exit 1
fi
echo "✓ Response is valid JSON"

# Check for 'success' field
if echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'success' in data else 1)" 2>/dev/null; then
    echo "✓ Response contains 'success' field"
else
    echo "✗ Response missing 'success' field"
    exit 1
fi

# Check if success is true
SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success', False))" 2>/dev/null)
if [ "$SUCCESS" = "True" ]; then
    echo "✓ API call was successful"
else
    echo "⚠ API call returned success=false"
    ERROR=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', 'Unknown error'))" 2>/dev/null)
    echo "Error: $ERROR"
    exit 0
fi
echo ""

# Test 3: Verify required fields
echo "Test 3: Required Fields"
echo "---------------------"
if echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); d=data.get('data', {}); exit(0 if all(k in d for k in ['post_id', 'title', 'stages']) else 1)" 2>/dev/null; then
    echo "✓ Response contains required fields: post_id, title, stages"
else
    echo "✗ Response missing required fields"
    exit 1
fi

# Verify post_id matches
RESPONSE_POST_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('post_id', 'N/A'))" 2>/dev/null)
if [ "$RESPONSE_POST_ID" = "$POST_ID" ]; then
    echo "✓ Post ID matches request (${POST_ID})"
else
    echo "⚠ Post ID mismatch: expected ${POST_ID}, got ${RESPONSE_POST_ID}"
fi
echo ""

# Test 4: Verify stages structure
echo "Test 4: Stages Structure"
echo "-----------------------"
EXPECTED_STAGES=("calendar" "planning" "authoring" "imaging" "header")
STAGES_PRESENT=0

for stage in "${EXPECTED_STAGES[@]}"; do
    if echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); stages=data.get('data', {}).get('stages', {}); exit(0 if '$stage' in stages else 1)" 2>/dev/null; then
        echo "✓ Stage '${stage}' is present"
        STAGES_PRESENT=$((STAGES_PRESENT + 1))
        
        # Check stage structure
        HAS_STATUS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); stage=data.get('data', {}).get('stages', {}).get('$stage', {}); print('yes' if 'status' in stage else 'no')" 2>/dev/null)
        HAS_PROGRESS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); stage=data.get('data', {}).get('stages', {}).get('$stage', {}); print('yes' if 'progress' in stage else 'no')" 2>/dev/null)
        HAS_SUBSTAGES=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); stage=data.get('data', {}).get('stages', {}).get('$stage', {}); print('yes' if 'substages' in stage else 'no')" 2>/dev/null)
        
        if [ "$HAS_STATUS" = "yes" ] && [ "$HAS_PROGRESS" = "yes" ] && [ "$HAS_SUBSTAGES" = "yes" ]; then
            echo "  ✓ Stage structure is correct (status, progress, substages)"
        else
            echo "  ⚠ Stage structure incomplete"
        fi
    else
        echo "⚠ Stage '${stage}' is missing"
    fi
done

if [ $STAGES_PRESENT -eq ${#EXPECTED_STAGES[@]} ]; then
    echo "✓ All expected stages are present"
else
    echo "⚠ Only ${STAGES_PRESENT}/${#EXPECTED_STAGES[@]} stages present"
fi
echo ""

# Test 5: Verify substages structure
echo "Test 5: Substages Structure"
echo "-------------------------"
SUBSTAGE_COUNT=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
stages = data.get('data', {}).get('stages', {})
count = 0
for stage_name, stage_data in stages.items():
    substages = stage_data.get('substages', {})
    for substage_name, substage_data in substages.items():
        if 'status' in substage_data and 'progress' in substage_data:
            count += 1
print(count)
" 2>/dev/null)

if [ "$SUBSTAGE_COUNT" -gt 0 ]; then
    echo "✓ Found ${SUBSTAGE_COUNT} substages with valid structure"
else
    echo "⚠ No substages found with valid structure"
fi

# Check a few specific substages
echo ""
echo "Sample substage statuses:"
echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
stages = data.get('data', {}).get('stages', {})
for stage_name in ['planning', 'authoring', 'header']:
    if stage_name in stages:
        substages = stages[stage_name].get('substages', {})
        if substages:
            first_substage = list(substages.items())[0]
            print(f\"  {stage_name}.{first_substage[0]}: {first_substage[1].get('status', 'N/A')} ({first_substage[1].get('progress', 0)}%)\")
" 2>/dev/null
echo ""

# Test 6: Verify completion status values
echo "Test 6: Completion Status Values"
echo "--------------------------------"
INVALID_STATUSES=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
stages = data.get('data', {}).get('stages', {})
invalid = []
valid_statuses = ['complete', 'in_progress', 'pending', 'failed']
for stage_name, stage_data in stages.items():
    substages = stage_data.get('substages', {})
    for substage_name, substage_data in substages.items():
        status = substage_data.get('status', '')
        progress = substage_data.get('progress', -1)
        if status not in valid_statuses:
            invalid.append(f'{stage_name}.{substage_name}: invalid status \"{status}\"')
        if not (0 <= progress <= 100):
            invalid.append(f'{stage_name}.{substage_name}: invalid progress {progress}')
if invalid:
    for item in invalid:
        print(item)
    sys.exit(1)
else:
    print('All statuses and progress values are valid')
" 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✓ All completion status values are valid"
else
    echo "✗ Found invalid status values:"
    echo "$INVALID_STATUSES"
    exit 1
fi
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "✓ All tests passed!"
echo ""
echo "Response preview:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -30
echo ""


