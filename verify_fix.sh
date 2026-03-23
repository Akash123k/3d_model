#!/bin/bash
# Fix verification script

echo "🔍 Verifying Mesh Persistence Fix..."
echo ""

# Check 1: Verify repositories.py has all classes
echo "✅ Check 1: Verifying repositories.py..."
if grep -q "class ModelRepository" backend/app/db/repositories.py && \
   grep -q "class MeshRepository" backend/app/db/repositories.py; then
    echo "   ✅ All repository classes present"
else
    echo "   ❌ Missing repository classes"
    exit 1
fi

# Check 2: Verify __init__.py exports
echo "✅ Check 2: Verifying __init__.py exports..."
if grep -q "MeshRepository" backend/app/db/__init__.py && \
   grep -q "ModelMesh" backend/app/db/__init__.py; then
    echo "   ✅ All exports present"
else
    echo "   ❌ Missing exports"
    exit 1
fi

# Check 3: Verify models.py has ModelMesh
echo "✅ Check 3: Verifying models.py has ModelMesh..."
if grep -q "class ModelMesh" backend/app/db/models.py; then
    echo "   ✅ ModelMesh class present"
else
    echo "   ❌ ModelMesh class missing"
    exit 1
fi

# Check 4: Test Python imports (outside Docker)
echo "✅ Check 4: Testing Python imports..."
cd backend
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from app.db import ModelRepository, MeshRepository, ModelMesh
    print('   ✅ Python imports successful')
except ImportError as e:
    print(f'   ❌ Import error: {e}')
    sys.exit(1)
" 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ Imports working correctly"
else
    echo "   ❌ Import failed"
    exit 1
fi
cd ..

# Check 5: Verify model_processor.py calls MeshRepository
echo "✅ Check 5: Verifying model_processor.py..."
if grep -q "MeshRepository.bulk_create" backend/app/services/model_processor.py; then
    echo "   ✅ Mesh saving code present"
else
    echo "   ❌ Mesh saving code missing"
    exit 1
fi

# Check 6: Verify API route uses database first
echo "✅ Check 6: Verifying API route..."
if grep -q "Try database first" backend/app/api/routes/model.py; then
    echo "   ✅ API updated to use database first"
else
    echo "   ❌ API not properly updated"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All verification checks passed!"
echo "=========================================="
echo ""
echo "Next step: Restart backend container"
echo "Command: docker restart step-cad-backend"
echo ""
