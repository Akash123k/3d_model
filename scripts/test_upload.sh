#!/bin/bash

# Test script for STEP file upload

echo "🧪 Testing STEP File Upload"
echo "=========================="
echo ""

# Check if test file exists
TEST_FILE="/home/venom/akash/3d_model/test_files/3 DOFs Robot Arm.STEP"

if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Test file not found: $TEST_FILE"
    echo "Please place '3 DOFs Robot Arm.STEP' in test_files directory"
    exit 1
fi

echo "✅ Test file found: $TEST_FILE"
FILE_SIZE=$(ls -lh "$TEST_FILE" | awk '{print $5}')
echo "   File size: $FILE_SIZE"
echo ""

# Get backend URL
BACKEND_URL="http://localhost:8283"
echo "📡 Backend URL: $BACKEND_URL"
echo ""

# Test health endpoint
echo "1️⃣ Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "✅ Health check passed (HTTP $HEALTH_RESPONSE)"
else
    echo "❌ Health check failed (HTTP $HEALTH_RESPONSE)"
    exit 1
fi
echo ""

# Test file upload
echo "2️⃣ Uploading STEP file..."
UPLOAD_RESPONSE=$(curl -s -X POST \
  "$BACKEND_URL/api/upload" \
  -F "file=@$TEST_FILE" \
  -H "Content-Type: multipart/form-data")

echo "Response: $UPLOAD_RESPONSE" | jq '.'

# Extract model_id from response
MODEL_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.model_id')

if [ "$MODEL_ID" = "null" ] || [ -z "$MODEL_ID" ]; then
    echo "❌ Upload failed - no model_id returned"
    exit 1
fi

echo ""
echo "✅ Upload successful!"
echo "   Model ID: $MODEL_ID"
echo ""

# Wait for processing
echo "3️⃣ Waiting for processing (5 seconds)..."
sleep 5
echo ""

# Get model details
echo "4️⃣ Fetching model details..."
MODEL_RESPONSE=$(curl -s "$BACKEND_URL/api/models/$MODEL_ID")

echo "Model Response:"
echo "$MODEL_RESPONSE" | jq '.'

STATUS=$(echo "$MODEL_RESPONSE" | jq -r '.status')
echo ""
echo "📊 Model Status: $STATUS"
echo ""

# Get statistics
echo "5️⃣ Fetching statistics..."
STATS_RESPONSE=$(curl -s "$BACKEND_URL/api/models/$MODEL_ID/statistics")

echo "Statistics:"
echo "$STATS_RESPONSE" | jq '.'
echo ""

# Get dependency graph
echo "6️⃣ Fetching dependency graph info..."
GRAPH_RESPONSE=$(curl -s "$BACKEND_URL/api/models/$MODEL_ID/dependency-graph")

NODES=$(echo "$GRAPH_RESPONSE" | jq -r '.total_nodes')
EDGES=$(echo "$GRAPH_RESPONSE" | jq -r '.total_edges')

echo "📈 Dependency Graph:"
echo "   Total Nodes: $NODES"
echo "   Total Edges: $EDGES"
echo ""

echo "=========================="
echo "✅ All tests completed!"
echo "=========================="
