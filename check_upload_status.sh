                                                          #!/bin/bash

echo "=========================================="
echo "  Upload Diagnostic Check"
echo "=========================================="
echo ""

# 1. Check if services are running
echo "1. Checking Docker containers..."
docker ps --filter "name=step-cad" --format "   {{.Names}}: {{.Status}}" || echo "   ❌ Containers not running!"
echo ""

# 2. Test backend health
echo "2. Testing backend health..."
HEALTH=$(curl -s http://localhost:8283/api/health 2>&1)
if [ $? -eq 0 ] && [ -n "$HEALTH" ]; then
    echo "   ✅ Backend responding"
    echo "   $HEALTH" | python3 -m json.tool 2>/dev/null | head -5
else
    echo "   ❌ Backend NOT responding"
fi
echo ""

# 3. Test frontend
echo "3. Testing frontend..."
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>&1)
if [ "$FRONTEND" = "200" ]; then
    echo "   ✅ Frontend accessible (HTTP $FRONTEND)"
else
    echo "   ⚠️  Frontend returned HTTP $FRONTEND"
fi
echo ""

# 4. Test direct upload (bypass browser)
echo "4. Testing direct file upload..."
TEST_FILE="/home/venom/akash/3d_model/test_files/small_cube.step"
if [ -f "$TEST_FILE" ]; then
    UPLOAD_RESULT=$(curl -s -w "\nHTTP:%{http_code}" -X POST http://localhost:8283/api/upload \
        -F "file=@$TEST_FILE" 2>&1)
    
    HTTP_CODE=$(echo "$UPLOAD_RESULT" | grep "HTTP:" | cut -d':' -f2)
    BODY=$(echo "$UPLOAD_RESULT" | grep -v "HTTP:")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "   ✅ Direct upload successful (HTTP $HTTP_CODE)"
        MODEL_ID=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('model_id', ''))" 2>/dev/null)
        echo "   Model ID: $MODEL_ID"
    else
        echo "   ❌ Direct upload failed (HTTP $HTTP_CODE)"
        echo "   Response: $BODY"
    fi
else
    echo "   ⚠️  Test file not found"
fi
echo ""

# 5. Check recent backend logs for upload activity
echo "5. Recent backend upload activity..."
LAST_UPLOAD=$(docker logs step-cad-backend 2>&1 | grep -i "upload" | tail -3)
if [ -n "$LAST_UPLOAD" ]; then
    echo "$LAST_UPLOAD" | while read line; do
        echo "   $line"
    done
else
    echo "   No recent upload activity found"
fi
echo ""

# 6. Check for errors
echo "6. Checking for errors in logs..."
ERRORS=$(docker logs step-cad-backend 2>&1 | grep -i "error\|exception" | tail -3)
if [ -n "$ERRORS" ]; then
    echo "$ERRORS" | while read line; do
        echo "   ⚠️  $line"
    done
else
    echo "   ✅ No recent errors"
fi
echo ""

echo "=========================================="
echo "  RECOMMENDATION:"
echo "=========================================="
echo ""
echo "Open Firefox and test upload:"
echo "  firefox /home/venom/akash/3d_model/test_simple.html"
echo ""
echo "In browser console (F12), look for:"
echo "  ✅ [API] POST /api/upload"
echo "  ✅ [Upload] File uploaded successfully"
echo "  ✅ [API] Response 200"
echo ""
echo "If still hanging:"
echo "  1. Open DevTools Network tab (F12)"
echo "  2. Clear all logs"
echo "  3. Try upload again"
echo "  4. Check if request is pending/stuck"
echo "  5. Screenshot and share the error"
echo ""
