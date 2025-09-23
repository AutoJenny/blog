#!/bin/bash

# Test script for auto-replenish functionality
# This simulates what the cron job will do

echo "Testing auto-replenish at $(date)"
echo "=================================="

# Call the auto-replenish endpoint
response=$(curl -s -X POST http://localhost:5000/launchpad/api/auto-replenish-all)

echo "Response:"
echo "$response" | python3 -m json.tool

echo ""
echo "Test completed at $(date)"
echo "=================================="
