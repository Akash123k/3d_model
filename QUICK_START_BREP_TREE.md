# Quick Start Guide - B-Rep Tree Display

## 🚀 How to Use (For End Users)

### Step 1: Upload STEP File
1. Open application at `http://localhost:3000`
2. Click "Upload STEP File" button
3. Select your `.step` or `.stp` file
4. Wait for processing to complete

### Step 2: View B-Rep Tree
**Method 1: From Dashboard**
- After upload completes, look for green "B-Rep Tree" button in header
- Click it to open dedicated viewer page

**Method 2: Direct URL**
- Navigate to `http://localhost:3000/brep-geometry`
- Select model from dropdown (if multiple uploaded)

### Step 3: Explore the Tree
- **Expand nodes**: Click on items with ▶ arrow
- **Collapse nodes**: Click on items with ▼ arrow  
- **View coordinates**: Shown inline as `(X, Y, Z)` for spatial entities
- **Scroll**: Use mouse wheel or scrollbar for long lists

---

## 👨‍💻 For Developers

### API Endpoint
```http
GET /api/models/{model_id}/brep-geometry
```

**Response:**
```json
{
  "model_id": "uuid",
  "entities_count": 1234,
  "total_components": 2,
  "brep_tree": [
    {
      "id": "#123",
      "type": "MANIFOLD_SOLID_BREP",
      "label": "#123 [MANIFOLD_SOLID_BREP]",
      "children": [...],
      "depth": 0,
      "coords": [10.5, 20.3, 5.0]
    }
  ],
  "bounding_box": {
    "min": [0, 0, 0],
    "max": [100, 100, 100],
    "dimensions": [100, 100, 100]
  }
}
```

### Frontend Usage
```typescript
import { getBRepGeometry } from './utils/api';

// In your component
const data = await getBRepGeometry(modelId);
console.log(data.brep_tree); // Array of tree roots
console.log(data.entities_count); // Total entities parsed
```

### Component Usage
```tsx
import GeometryExplorer from './components/geometry/GeometryExplorer';

// Automatically fetches B-Rep data when currentModel changes
<GeometryExplorer />
```

---

## 🔧 Configuration

### Adjust Limits

**Backend** (`backend/app/services/brep_geometry_parser.py`):
```python
# Line ~36: Limit number of components processed
for comp_id in components[:5]:  # Change 5 to desired limit

# Line ~89: Limit tree depth
def _build_tree(self, root_id: str, max_depth: int = 10):
    # Change 10 to desired depth
```

**Frontend** - No limits applied, shows all data received

---

## 🐛 Troubleshooting

### "Loading..." Forever
**Cause:** Backend not responding or parsing error  
**Fix:** Check browser console for errors, verify backend is running

### "No B-Rep Data Available"
**Cause:** Model not fully processed yet  
**Fix:** Wait for processing to complete, refresh page

### Coordinates Not Showing
**Cause:** Entity doesn't have CARTESIAN_POINT references  
**Fix:** This is normal - only spatial point entities have coordinates

### Tree Too Large/Slow
**Cause:** Very complex STEP file with 10k+ entities  
**Fix:** 
1. Increase component limit in parser
2. Reduce max_depth parameter
3. Implement lazy loading (future enhancement)

---

## 📊 What Each Entity Type Means

| Entity Type | Description | Shows Coordinates? |
|------------|-------------|-------------------|
| MANIFOLD_SOLID_BREP | Complete 3D solid object | ❌ |
| CLOSED_SHELL | Sealed surface boundary | ❌ |
| OPEN_SHELL | Unsealed surface boundary | ❌ |
| ADVANCED_FACE | Complex surface with boundaries | ❌ |
| PLANE | Flat surface | ❌ |
| CYLINDRICAL_SURFACE | Cylindrical curved surface | ❌ |
| CONICAL_SURFACE | Conical tapered surface | ❌ |
| SPHERICAL_SURFACE | Spherical curved surface | ❌ |
| EDGE_CURVE | Boundary edge curve | ❌ |
| LINE | Straight line segment | ❌ |
| CIRCLE | Circular arc | ❌ |
| VERTEX_POINT | Point in 3D space | ✅ YES |
| CARTESIAN_POINT | XYZ coordinate definition | ✅ YES |
| DIRECTION | Vector direction | ❌ |
| AXIS2_PLACEMENT_3D | Coordinate system axis | ❌ |

---

## 📁 File Structure

```
backend/
├── app/
│   ├── services/
│   │   └── brep_geometry_parser.py       ← NEW: Parser service
│   └── api/routes/
│       └── model.py                       ← MODIFIED: Added endpoint

frontend/
├── src/
│   ├── utils/
│   │   └── api.ts                         ← MODIFIED: Added types + function
│   ├── components/
│   │   └── geometry/
│   │       └── GeometryExplorer.tsx       ← MODIFIED: Enhanced with brep.py data
│   ├── pages/
│   │   └── BRepGeometryPage.tsx           ← NEW: Dedicated page
│   └── App.tsx                            ← MODIFIED: Added route
└── dist/                                  ← Built after npm run build
```

---

## 🎯 Key Features

✅ **Complete Entity Display** - Shows ALL STEP entities, not just B-Rep hierarchy  
✅ **Coordinate Visualization** - Inline XYZ display for spatial points  
✅ **Bidirectional Traversal** - Follows both forward and backward references  
✅ **Performance Optimized** - Configurable limits prevent browser crash  
✅ **Error Handling** - Graceful fallback if parsing fails  
✅ **Loading States** - User feedback during data fetch  
✅ **Responsive UI** - Works on desktop and mobile  
✅ **Type Safe** - Full TypeScript support  

---

## 📞 Support

If you encounter issues:
1. Check browser console for errors
2. Verify backend logs: `docker-compose logs backend`
3. Test parser directly: `python3 test_brep_parser.py your_file.step`
4. Ensure model is fully processed before viewing

---

## 🎉 Success Indicators

You'll know it's working when you see:
- ✅ Tree structure with `#ID [TYPE]` labels
- ✅ Coordinates like `(10.50, 20.30, 5.00)` next to points
- ✅ Expandable/collapsible nodes
- ✅ Multiple entity types (not just "Unknown")
- ✅ Bounding box dimensions displayed
- ✅ Entity count matches expected complexity

Example of working output:
```
📦 B-Rep Model (2 Components, 1234 Entities)
  └─ #123 [MANIFOLD_SOLID_BREP]
      └─ #456 [CLOSED_SHELL] (10.50, 20.30, 5.00)
          └─ #789 [ADVANCED_FACE]
              └─ #101 [EDGE_CURVE]
                  └─ #102 [VERTEX_POINT] (10.50, 20.30, 5.00)
```

Happy exploring! 🚀
