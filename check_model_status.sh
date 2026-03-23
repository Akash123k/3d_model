#!/bin/bash
# Check if model exists and has meshes

echo "=========================================="
echo "🔍 Checking Model & Mesh Data"
echo "=========================================="
echo ""

MODEL_ID="84144667-4238-4a11-96f6-6795eba87bd5"

# Check 1: Does model exist?
echo "✅ Check 1: Model Exists?"
docker exec step-cad-db psql -U postgres -d step_cad_viewer <<EOF
SELECT id, original_filename, status, entities_count 
FROM models 
WHERE id = '$MODEL_ID';
EOF

if [ $? -eq 0 ]; then
    echo "   ✅ Model found in database"
else
    echo "   ❌ Model NOT found!"
fi
echo ""

# Check 2: Does it have meshes?
echo "✅ Check 2: Mesh Count?"
docker exec step-cad-db psql -U postgres -d step_cad_viewer <<EOF
SELECT COUNT(*) as mesh_count 
FROM model_meshes 
WHERE model_id = '$MODEL_ID';
EOF

if [ $? -eq 0 ]; then
    echo "   Query completed"
else
    echo "   ❌ Query failed"
fi
echo ""

# Check 3: All models with mesh counts
echo "✅ Check 3: All Models with Mesh Counts"
docker exec step-cad-db psql -U postgres -d step_cad_viewer <<EOF
SELECT 
    m.id,
    m.original_filename,
    m.status,
    COUNT(mm.id) as mesh_count
FROM models m
LEFT JOIN model_meshes mm ON m.id = mm.model_id
GROUP BY m.id, m.original_filename, m.status
ORDER BY m.created_at DESC
LIMIT 5;
EOF

echo ""

# Check 4: Test API directly
echo "✅ Check 4: Test Mesh API"
curl -s http://localhost:8000/api/models/$MODEL_ID/mesh | python3 -m json.tool | head -20

echo ""
echo "=========================================="
echo "Recommendations:"
echo "=========================================="
echo ""

# Get latest model ID
LATEST_MODEL=$(docker exec step-cad-db psql -U postgres -d step_cad_viewer -t -c \
  "SELECT id FROM models ORDER BY created_at DESC LIMIT 1;" 2>/dev/null | tr -d ' ')

if [ -n "$LATEST_MODEL" ]; then
    echo "Latest model ID: $LATEST_MODEL"
    echo ""
    echo "Try this model instead:"
    echo "curl http://localhost:8000/api/models/$LATEST_MODEL/mesh | jq"
else
    echo "No models found in database!"
    echo "Upload a new STEP file first."
fi
