#!/bin/bash
# Black Screen Diagnostic Script

echo "=========================================="
echo "🔍 Black Screen Diagnosis"
echo "=========================================="
echo ""

# Check 1: Is backend running?
echo "✅ Check 1: Backend Container Status"
docker ps | grep step-cad-backend
if [ $? -eq 0 ]; then
    echo "   ✅ Backend is running"
else
    echo "   ❌ Backend is NOT running"
    echo "   Fix: docker restart step-cad-backend"
    exit 1
fi
echo ""

# Check 2: Is database table created?
echo "✅ Check 2: Database Mesh Table"
docker exec step-cad-db psql -U postgres -d step_cad_viewer -c "\dt model_meshes" 2>&1 | grep -q "model_meshes"
if [ $? -eq 0 ]; then
    echo "   ✅ model_meshes table exists"
else
    echo "   ❌ model_meshes table NOT found"
    echo "   Fix: Run migration script"
    exit 1
fi
echo ""

# Check 3: Are meshes in database?
echo "✅ Check 3: Mesh Count in Database"
MESH_COUNT=$(docker exec step-cad-db psql -U postgres -d step_cad_viewer -t -c "SELECT COUNT(*) FROM model_meshes;" 2>/dev/null | tr -d ' ')
if [ -n "$MESH_COUNT" ] && [ "$MESH_COUNT" -gt 0 ]; then
    echo "   ✅ Found $MESH_COUNT meshes in database"
else
    echo "   ⚠️  No meshes in database (0)"
    echo "   This might be the issue - no data to display"
fi
echo ""

# Check 4: Get recent models
echo "✅ Check 4: Recent Models"
docker exec step-cad-db psql -U postgres -d step_cad_viewer -c \
  "SELECT id, original_filename, status, entities_count FROM models ORDER BY created_at DESC LIMIT 3;" 2>&1 | head -10
echo ""

# Check 5: Test API endpoint
echo "✅ Check 5: Test Mesh API"
MODEL_ID="5e60c990-615e-4e5b-8905-695ac175a939"
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/models/$MODEL_ID/mesh)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    MESH_COUNT=$(echo "$RESPONSE" | head -n-1 | jq '.meshes | length' 2>/dev/null)
    if [ -n "$MESH_COUNT" ]; then
        echo "   ✅ API returned $MESH_COUNT meshes (HTTP $HTTP_CODE)"
    else
        echo "   ⚠️  API returned data but no meshes (HTTP $HTTP_CODE)"
    fi
elif [ "$HTTP_CODE" = "404" ]; then
    echo "   ❌ API returned 404 - Model not found or no mesh data"
else
    echo "   ❌ API error: HTTP $HTTP_CODE"
fi
echo ""

# Check 6: Check for processing errors
echo "✅ Check 6: Backend Error Logs"
ERROR_COUNT=$(docker logs step-cad-backend 2>&1 | grep -i "error\|failed\|exception" | tail -20 | wc -l)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "   ⚠️  Found $ERROR_COUNT error messages in logs"
    echo "   Last 3 errors:"
    docker logs step-cad-backend 2>&1 | grep -i "error\|failed\|exception" | tail -3
else
    echo "   ✅ No obvious errors in backend logs"
fi
echo ""

# Check 7: Frontend connectivity
echo "✅ Check 7: Frontend Service"
docker ps | grep step-cad-frontend
if [ $? -eq 0 ]; then
    echo "   ✅ Frontend container is running"
    # Try to access frontend
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8283 2>/dev/null | grep -q "200"
    if [ $? -eq 0 ]; then
        echo "   ✅ Frontend accessible on port 8283"
    else
        echo "   ⚠️  Frontend not responding on port 8283"
    fi
else
    echo "   ❌ Frontend container NOT running"
fi
echo ""

echo "=========================================="
echo "📋 Summary & Recommendations"
echo "=========================================="
echo ""

if [ "$MESH_COUNT" = "0" ] || [ -z "$MESH_COUNT" ]; then
    echo "⚠️  ISSUE: No mesh data in database"
    echo ""
    echo "Solutions:"
    echo "1. Upload a new STEP file through the UI"
    echo "2. Wait for processing to complete"
    echo "3. Check if processing completes successfully"
    echo ""
    echo "Or run manually:"
    echo "   curl -X POST http://localhost:8000/api/upload -F 'file=@/path/to/file.step'"
else
    echo "✅ Mesh data exists in database"
    echo ""
    echo "If screen is still black, check:"
    echo "1. Browser console for JavaScript errors (F12)"
    echo "2. Network tab - verify /mesh API returns data"
    echo "3. Three.js rendering issues"
fi
echo ""
echo "Quick fixes to try:"
echo "1. Refresh browser page (Ctrl+R)"
echo "2. Clear browser cache"
echo "3. Select a different model from the list"
echo "4. Upload a new STEP file"
echo ""
