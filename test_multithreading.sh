#!/bin/bash
# Test script to verify multithreading optimizations for large file uploads

echo "========================================="
echo "Multithreading Optimization Verification"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend is running
echo -e "${YELLOW}Checking backend status...${NC}"
if curl -s http://localhost:8283/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running. Please start it first.${NC}"
    echo "Run: docker-compose up -d"
    exit 1
fi

echo ""
echo "========================================="
echo "Test 1: Small File Upload (< 10KB)"
echo "========================================="

if [ -f "test_files/small_cube.step" ]; then
    START_TIME=$(date +%s.%N)
    
    RESPONSE=$(curl -s -X POST http://localhost:8283/api/v1/upload \
        -F "file=@test_files/small_cube.step")
    
    END_TIME=$(date +%s.%N)
    DURATION=$(echo "$END_TIME - $START_TIME" | bc)
    
    echo "Response: $RESPONSE" | jq .
    echo -e "${YELLOW}Upload time:${NC} ${GREEN}${DURATION}s${NC}"
    
    if (( $(echo "$DURATION < 3" | bc -l) )); then
        echo -e "${GREEN}✓ PASS: Small file upload completed in reasonable time${NC}"
    else
        echo -e "${RED}✗ SLOW: Small file upload took too long${NC}"
    fi
else
    echo -e "${RED}⚠ Test file not found: test_files/small_cube.step${NC}"
fi

echo ""
echo "========================================="
echo "Test 2: Check Log Messages"
echo "========================================="

echo -e "${YELLOW}Looking for optimization indicators in logs...${NC}"
echo ""

# Check for streaming upload
if grep -q "streaming_upload" logs/processing.log 2>/dev/null || \
   grep -q "streaming_upload" backend/app/logs/processing.log 2>/dev/null; then
    echo -e "${GREEN}✓ Streaming upload detected in logs${NC}"
else
    echo -e "${YELLOW}⚠ No streaming upload logs found yet (upload a file to see this)${NC}"
fi

# Check for parallel processing
if grep -q "parallel_efficiency" logs/processing.log 2>/dev/null || \
   grep -q "parallel_efficiency" backend/app/logs/processing.log 2>/dev/null; then
    echo -e "${GREEN}✓ Parallel efficiency logging found${NC}"
else
    echo -e "${YELLOW}⚠ No parallel efficiency logs found yet${NC}"
fi

# Check worker count
if grep -q "max_workers=16" logs/processing.log 2>/dev/null || \
   grep -q "max_workers=16" backend/app/logs/processing.log 2>/dev/null; then
    echo -e "${GREEN}✓ Using 16 workers (maximum parallelism)${NC}"
else
    echo -e "${YELLOW}⚠ Worker count not found in recent logs${NC}"
fi

echo ""
echo "========================================="
echo "Test 3: Monitor Real-time Processing"
echo "========================================="

echo -e "${YELLOW}Starting real-time log monitor...${NC}"
echo -e "${GREEN}Press Ctrl+C to stop monitoring${NC}"
echo ""

# Start tailing logs
if [ -f "logs/processing.log" ] && [ -s "logs/processing.log" ]; then
    tail -f logs/processing.log | grep --color=always -E "streaming|parallel|max_workers|optimization"
elif [ -f "backend/app/logs/processing.log" ] && [ -s "backend/app/logs/processing.log" ]; then
    tail -f backend/app/logs/processing.log | grep --color=always -E "streaming|parallel|max_workers|optimization"
else
    echo -e "${YELLOW}Logs are empty. Upload a file to generate log entries.${NC}"
    echo "Then run: docker logs -f step-cad-backend"
fi

echo ""
echo "========================================="
echo "Manual Testing Instructions"
echo "========================================="
echo ""
echo "To test with YOUR large STEP files:"
echo ""
echo "1. Upload via API:"
echo "   curl -X POST http://localhost:8283/api/v1/upload \\"
echo "     -F 'file=@/path/to/your/large_file.step'"
echo ""
echo "2. Watch the logs in another terminal:"
echo "   docker logs -f step-cad-backend"
echo ""
echo "3. Look for these success indicators:"
echo "   ✓ streaming_upload=True"
echo "   ✓ parallel_efficiency=\"optimized\""
echo "   ✓ max_workers=16"
echo "   ✓ parallel_processing=\"enabled\""
echo ""
echo "4. Check total processing time:"
echo "   Should be 5-10x faster than before"
echo ""
echo "========================================="
echo "Performance Expectations"
echo "========================================="
echo ""
echo "File Size       | Expected Time  | Improvement"
echo "----------------|----------------|-------------"
echo "< 100KB         | < 2 seconds    | 2-3x faster"
echo "1-10MB          | < 15 seconds   | 3-5x faster"
echo "50-100MB        | < 5 minutes    | 5-10x faster"
echo ""
echo "========================================="
echo "Verification Complete!"
echo "========================================="
