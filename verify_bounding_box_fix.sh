#!/bin/bash
# Verification script for bounding box fix

echo "=========================================="
echo "Bounding Box Fix Verification"
echo "=========================================="
echo ""

# Check if backend is running
echo "1. Checking backend status..."
HEALTH=$(curl -s http://localhost:8283/api/health | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
if [ "$HEALTH" = "healthy" ]; then
    echo "   ✅ Backend is healthy"
else
    echo "   ❌ Backend is not running or unhealthy"
    exit 1
fi

echo ""
echo "2. Getting uploaded models..."
MODELS=$(curl -s http://localhost:8283/api/models)
TOTAL=$(echo $MODELS | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null)
echo "   Found $TOTAL model(s)"

echo ""
echo "3. Checking bounding boxes for all models..."
echo ""

# Get all model IDs
MODEL_IDS=$(echo $MODELS | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    print(m['model_id'])
" 2>/dev/null)

HAS_VALID_BBOX=0
HAS_ZERO_BBOX=0

for MODEL_ID in $MODEL_IDS; do
    # Get statistics
    STATS=$(curl -s "http://localhost:8283/api/models/$MODEL_ID/statistics")
    
    # Extract bounding box dimensions
    BBOX_INFO=$(echo $STATS | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    bb = data.get('bounding_box', {})
    if bb and bb.get('dimensions'):
        dims = bb['dimensions']
        x = dims.get('x', 0)
        y = dims.get('y', 0)
        z = dims.get('z', 0)
        if x > 0 or y > 0 or z > 0:
            print(f'VALID:{x:.2f}x{y:.2f}x{z:.2f}')
        else:
            print('ZERO:0.00x0.00x0.00')
    else:
        print('MISSING')
except Exception as e:
    print(f'ERROR:{str(e)}')
" 2>/dev/null)
    
    # Get filename
    FILENAME=$(echo $STATS | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('filename', 'unknown'))" 2>/dev/null || echo "unknown")
    
    if [[ $BBOX_INFO == VALID:* ]]; then
        DIMENSIONS=${BBOX_INFO#VALID:}
        echo "   ✅ Model $MODEL_ID"
        echo "      File: $FILENAME"
        echo "      Dimensions: $DIMENSIONS"
        ((HAS_VALID_BBOX++))
    elif [[ $BBOX_INFO == ZERO:* ]]; then
        echo "   ❌ Model $MODEL_ID"
        echo "      File: $FILENAME"
        echo "      Dimensions: 0.00x0.00x0.00 (INVALID)"
        ((HAS_ZERO_BBOX++))
    else
        echo "   ⚠️  Model $MODEL_ID - $BBOX_INFO"
    fi
    
    echo ""
done

echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Models with valid bounding boxes: $HAS_VALID_BBOX"
echo "Models with zero bounding boxes:  $HAS_ZERO_BBOX"
echo ""

if [ $HAS_VALID_BBOX -gt 0 ] && [ $HAS_ZERO_BBOX -eq 0 ]; then
    echo "✅ SUCCESS: All models have valid bounding boxes!"
    exit 0
elif [ $HAS_VALID_BBOX -gt 0 ] && [ $HAS_ZERO_BBOX -gt 0 ]; then
    echo "⚠️  PARTIAL: Some models have valid bounding boxes"
    exit 1
else
    echo "❌ FAILURE: No models have valid bounding boxes"
    exit 1
fi
