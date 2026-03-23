import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { useModelStore } from '../../store';
import apiClient from '../../utils/api';
import CoordinateIndicator from './CoordinateIndicator';
import ViewCube from './ViewCube';

const Viewer3D: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { currentModel } = useModelStore();
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const animationFrameRef = useRef<number>(0);
  const meshesRef = useRef<Map<string, THREE.Mesh>>(new Map());

  useEffect(() => {
    if (containerRef.current && !sceneRef.current) {
      initThreeJS();
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (rendererRef.current && containerRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement);
      }
      // Dispose controls
      if (controlsRef.current) {
        controlsRef.current.dispose();
      }
      // Clear meshes
      clearMeshes();
    };
  }, []);

  // Load mesh data when currentModel changes
  useEffect(() => {
    console.log('[Viewer] useEffect triggered - currentModel:', currentModel ? currentModel.filename : 'null');
    console.log('[Viewer] Scene exists:', !!sceneRef.current);
    
    if (currentModel && sceneRef.current) {
      console.log('[Viewer] Starting loadMeshData...');
      loadMeshData();
    } else {
      if (!currentModel) {
        console.warn('[Viewer] No currentModel available');
      }
      if (!sceneRef.current) {
        console.warn('[Viewer] Scene not initialized yet');
      }
    }
  }, [currentModel]);

  const initThreeJS = () => {
    if (!containerRef.current) return;

    // Scene - Dark gray background (not pure black) to catch rendering issues
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a1a); // Dark gray instead of pure black
    sceneRef.current = scene;

    // Camera - Initial conservative settings with wider range
    const aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
    const camera = new THREE.PerspectiveCamera(75, aspect, 0.001, 1000000);
    camera.position.set(100, 100, 100); // Isometric view
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer - Enhanced settings for guaranteed visibility
    const renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Cap at 2x for performance
    renderer.setClearColor(0x1a1a1a, 1); // Explicit clear color
    renderer.localClippingEnabled = false; // Disable clipping that can hide geometry
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // OrbitControls for CAD navigation - Enhanced with adaptive limits
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = true;
    controls.minDistance = 0.1;
    controls.maxDistance = 100000;
    controls.enableRotate = true;
    controls.enableZoom = true;
    controls.enablePan = true;
    controls.zoomSpeed = 1.5;
    controls.panSpeed = 1.2;
    controls.rotateSpeed = 1.0;
    // Standard CAD mouse controls: Left=Rotate, Right=Pan, Scroll=Zoom
    controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.DOLLY,
      RIGHT: THREE.MOUSE.PAN
    };
    controlsRef.current = controls;

    console.log('[Viewer] OrbitControls initialized with mouse buttons:', controls.mouseButtons);
    
    // Debug: Verify canvas is receiving pointer events
    const canvas = renderer.domElement;
    canvas.style.pointerEvents = 'auto';
    canvas.style.touchAction = 'none';
    console.log('[Viewer] Canvas pointer events set to:', canvas.style.pointerEvents);

    // Enhanced Lighting System - GUARANTEED visibility regardless of model size
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0); // Very bright ambient (doubled)
    scene.add(ambientLight);

    // Hemispheric light for natural sky/ground illumination
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 1.5);
    hemiLight.position.set(0, 200, 0);
    scene.add(hemiLight);

    // Main directional light - will be repositioned dynamically
    const directionalLight = new THREE.DirectionalLight(0xffffff, 2.0);
    directionalLight.position.set(100, 100, 100);
    scene.add(directionalLight);

    // Fill light from opposite side
    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 1.5);
    directionalLight2.position.set(-100, -100, -100);
    scene.add(directionalLight2);

    // Top light for better illumination
    const directionalLight3 = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight3.position.set(0, 200, 0);
    scene.add(directionalLight3);

    // Add point light at center to illuminate from inside
    const pointLight = new THREE.PointLight(0xffffff, 1.0, 0);
    pointLight.position.set(0, 0, 0);
    scene.add(pointLight);

    // Grid helper - Adaptive size
    const gridHelper = new THREE.GridHelper(200, 20, 0x4444ff, 0x222244);
    scene.add(gridHelper);

    // Axes helper
    const axesHelper = new THREE.AxesHelper(50);
    scene.add(axesHelper);

    // Animation loop with controls update
    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);

      if (controlsRef.current) {
        controlsRef.current.update();
      }

      renderer.render(scene, camera);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      if (!containerRef.current || !cameraRef.current || !rendererRef.current) return;

      const width = containerRef.current.clientWidth;
      const height = containerRef.current.clientHeight;

      cameraRef.current.aspect = width / height;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(width, height);
    };

    window.addEventListener('resize', handleResize);

    // Expose Three.js objects for debugging
    (window as any).viewerDebug = {
      scene,
      camera,
      controls,
      renderer,
      getCanvasInfo: () => ({
        pointerEvents: canvas.style.pointerEvents,
        touchAction: canvas.style.touchAction,
        width: canvas.width,
        height: canvas.height
      })
    };
    console.log('[Viewer] Debug helpers exposed. Use window.viewerDebug in console.');
  };

  const loadMeshData = async () => {
    if (!sceneRef.current || !currentModel) {
      console.log('[Viewer] Cannot load mesh - missing scene or model');
      return;
    }

    console.log('[Viewer] Starting to load mesh data for:', currentModel.model_id);
    const startTime = performance.now();

    try {
      // Clear existing meshes
      clearMeshes();

      // Fetch mesh data from backend
      console.log('[Viewer] Fetching mesh data from API...');
      const fetchStart = performance.now();
      const response = await apiClient.get(`/models/${currentModel.model_id}/mesh`);
      const fetchTime = ((performance.now() - fetchStart) / 1000).toFixed(2);
      
      const meshes = response.data.meshes;

      console.log('[Viewer] Received mesh data:', meshes?.length || 0, 'meshes', `(fetch: ${fetchTime}s)`);

      if (!meshes || meshes.length === 0) {
        console.log('[Viewer] No mesh data available, using placeholder');
        loadPlaceholderGeometry();
        return;
      }

      console.log(`[Viewer] Loading ${meshes.length} meshes`);
      const renderStart = performance.now();

      // Create Three.js meshes - OPTIMIZED batch processing with comprehensive validation
      const geometries: THREE.BufferGeometry[] = [];
      const materials: THREE.Material[] = [];
      let totalVertices = 0;
      let validMeshCount = 0;
      
      meshes.forEach((meshData: any, index: number) => {
        const geometry = new THREE.BufferGeometry();

        // CRITICAL: Validate vertex data
        if (!meshData.vertices || meshData.vertices.length === 0) {
          console.warn(`[Viewer] Mesh ${index} has NO vertices - skipping`);
          return;
        }

        // Check for NaN or Infinity in vertices
        const hasInvalidValues = meshData.vertices.some((v: number) => 
          !isFinite(v) || isNaN(v)
        );
        
        if (hasInvalidValues) {
          console.error(`[Viewer] Mesh ${index} contains NaN/Infinity values - skipping`);
          return;
        }

        // Set vertices with validation
        geometry.setAttribute(
          'position',
          new THREE.Float32BufferAttribute(meshData.vertices, 3)
        );

        // DEBUG: Log vertex count and bounding box
        const vertexCount = meshData.vertices.length / 3;
        totalVertices += vertexCount;
        validMeshCount++;
        
        console.log(`[Viewer] Mesh ${index} (${meshData.face_id}): ${vertexCount} vertices`);

        // Compute bounding box for debugging
        geometry.computeBoundingBox();
        const bbox = geometry.boundingBox;
        if (bbox) {
          console.log(`[Viewer] Mesh ${index} bounding box:`, {
            min: { x: bbox.min.x.toFixed(2), y: bbox.min.y.toFixed(2), z: bbox.min.z.toFixed(2) },
            max: { x: bbox.max.x.toFixed(2), y: bbox.max.y.toFixed(2), z: bbox.max.z.toFixed(2) }
          });
        }

        // Set normals - use provided normals or compute from geometry
        if (meshData.normals && meshData.normals.length > 0) {
          geometry.setAttribute(
            'normal',
            new THREE.Float32BufferAttribute(meshData.normals, 3)
          );
        } else {
          // Compute normals if not provided
          geometry.computeVertexNormals();
        }

        // Set indices
        if (meshData.indices && meshData.indices.length > 0) {
          geometry.setIndex(meshData.indices);
        }

        // Create material based on surface type
        const material = getMaterialForSurfaceType(meshData.surface_type || 'UNKNOWN');

        const mesh = new THREE.Mesh(geometry, material);
        mesh.userData.faceId = meshData.face_id || 'unknown';
        mesh.userData.surfaceType = meshData.surface_type || 'UNKNOWN';

        // Add wireframe overlay for better CAD visibility
        const wireframeMaterial = new THREE.LineBasicMaterial({ 
          color: 0x000000, // Black wireframe for contrast
          transparent: true,
          opacity: 0.5
        });
        const wireframe = new THREE.LineSegments(
          new THREE.WireframeGeometry(geometry),
          wireframeMaterial
        );
        mesh.add(wireframe);

        sceneRef.current?.add(mesh);
        meshesRef.current.set(meshData.face_id || 'unknown', mesh);
        
        geometries.push(geometry);
        materials.push(material);
      });

      // CRITICAL: Validate that we have geometry to render
      if (validMeshCount === 0 || totalVertices === 0) {
        console.error('[Viewer] GEOMETRY VALIDATION FAILED: No valid meshes created!');
        console.error('[Viewer] Check backend API - vertices may be empty or invalid');
        loadPlaceholderGeometry();
        return;
      }

      console.log(`[Viewer] MESH LOADING SUCCESS: ${validMeshCount} meshes, ${totalVertices} total vertices`);

      const renderTime = ((performance.now() - renderStart) / 1000).toFixed(2);
      const totalTime = ((performance.now() - startTime) / 1000).toFixed(2);
      
      console.log(`[Viewer] Mesh loading completed - Render: ${renderTime}s, Total: ${totalTime}s`);
      console.log(`[Viewer] meshesRef.current.size = ${meshesRef.current.size}`);

      // CRITICAL: Ensure camera frames the model - multiple attempts guarantee visibility
      console.log('[Viewer] Starting camera framing sequence...');
      
      // First attempt: Fit to meshes immediately
      fitCameraToMeshes(false); // instant
      
      // Second attempt: Force fit after short delay
      setTimeout(() => {
        if (meshesRef.current && meshesRef.current.size > 0) {
          console.log('[Viewer] Force-fitting camera to meshes (attempt 2)');
          fitCameraToMeshes(false);
        } else if (currentModel?.statistics?.bounding_box) {
          console.log('[Viewer] Force-fitting camera to bounding box (attempt 2)');
          fitCameraToModel(false);
        }
      }, 100);
      
      // Third attempt: Final force fit
      setTimeout(() => {
        if (meshesRef.current && meshesRef.current.size > 0) {
          console.log('[Viewer] FINAL camera fit to meshes');
          fitCameraToMeshes(false);
        } else if (currentModel?.statistics?.bounding_box) {
          console.log('[Viewer] FINAL camera fit to bounding box');
          fitCameraToModel(false);
        } else {
          console.error('[Viewer] WARNING: No geometry available for camera framing!');
        }
      }, 500);

      console.log('[Viewer] Mesh loading completed - camera framing sequence initiated');
    } catch (error) {
      console.error('[Viewer] Failed to load mesh data:', error);
      loadPlaceholderGeometry();
    }
  };

  const getMaterialForSurfaceType = (surfaceType: string): THREE.Material => {
    // Bright, vibrant colors that stand out against dark background
    const colorMap: Record<string, number> = {
      'PLANE': 0x00ff00,        // Bright green
      'CYLINDRICAL_SURFACE': 0xff00ff,  // Bright magenta
      'CONICAL_SURFACE': 0xffff00,     // Bright yellow
      'SPHERICAL_SURFACE': 0x00ffff,   // Bright cyan
      'TOROIDAL_SURFACE': 0xff8800,    // Bright orange
      'B_SPLINE_SURFACE_WITH_KNOTS': 0xff4444, // Bright red
      'UNKNOWN': 0x88ff88         // Light green
    };

    const color = colorMap[surfaceType] || colorMap['UNKNOWN'];

    // Use MeshBasicMaterial for guaranteed visibility (no lighting required)
    // with wireframe overlay for better CAD visualization
    return new THREE.MeshBasicMaterial({
      color: color,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.9, // Slightly transparent for depth perception
      wireframe: false, // Solid surface first
      polygonOffset: true,
      polygonOffsetFactor: -1
    });
  };

  const clearMeshes = () => {
    if (!sceneRef.current) return;

    // Remove all meshes from scene
    meshesRef.current.forEach((mesh) => {
      sceneRef.current?.remove(mesh);
      
      // Dispose of wireframe children first
      mesh.children.forEach(child => {
        if (child instanceof THREE.LineSegments) {
          child.geometry.dispose();
          if (Array.isArray(child.material)) {
            child.material.forEach(m => m.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
      
      // Dispose main mesh
      mesh.geometry.dispose();
      if (Array.isArray(mesh.material)) {
        mesh.material.forEach(m => m.dispose());
      } else {
        mesh.material.dispose();
      }
    });

    meshesRef.current.clear();
    console.log('[Viewer] All meshes and wireframes disposed');
  };

  /**
   * Core camera framing system - guarantees object visibility
   */
  const frameObject = (center: THREE.Vector3, size: THREE.Vector3, animate: boolean = true) => {
    if (!cameraRef.current || !controlsRef.current || !rendererRef.current) return;

    const maxDim = Math.max(size.x, size.y, size.z);
    const minDim = Math.min(size.x, size.y, size.z);
    
    // Handle edge cases
    if (maxDim < 0.001) {
      console.warn('[Viewer] Object is extremely small, using minimum size');
      size.setScalar(1);
    } else if (maxDim > 10000) {
      console.warn('[Viewer] Object is extremely large, scaling down');
      const scale = 1000 / maxDim;
      size.multiplyScalar(scale);
      center.multiplyScalar(scale);
    }

    // Calculate optimal camera distance
    const fov = cameraRef.current.fov * (Math.PI / 180);
    const fitHeightDistance = size.y / (2 * Math.tan(fov / 2));
    const fitWidthDistance = size.x / (2 * Math.tan(fov / 2) * cameraRef.current.aspect);
    const baseDistance = Math.max(fitHeightDistance, fitWidthDistance) * 1.5;
    
    // Ensure minimum and maximum distance constraints
    const distance = Math.max(Math.min(baseDistance, 5000), 10);

    // Adaptive clipping planes - DISABLED for better visibility
    const nearPlane = 0.01; // Fixed small value
    const farPlane = 100000; // Fixed large value
    
    cameraRef.current.near = nearPlane;
    cameraRef.current.far = farPlane;
    cameraRef.current.updateProjectionMatrix();
    
    // DISABLE renderer clipping planes to avoid cutting off model
    // rendererRef.current.clippingPlanes = [];

    // Update controls
    controlsRef.current.minDistance = Math.max(0.1, minDim / 10);
    controlsRef.current.maxDistance = farPlane * 0.9;

    if (animate) {
      // Smooth transition
      animateCamera(center, distance);
    } else {
      // Instant positioning
      const offset = distance * 0.57735; // 1/sqrt(3) for isometric view
      cameraRef.current.position.set(
        center.x + distance,
        center.y + offset,
        center.z + offset
      );
      cameraRef.current.lookAt(center);
      controlsRef.current.target.copy(center);
      controlsRef.current.update();
    }

    // Update lighting to focus on object
    updateLighting(center, size);

    console.log('[Viewer] Object framed successfully:', {
      center: { x: center.x.toFixed(2), y: center.y.toFixed(2), z: center.z.toFixed(2) },
      size: { x: size.x.toFixed(2), y: size.y.toFixed(2), z: size.z.toFixed(2) },
      distance: distance.toFixed(2),
      near: nearPlane.toFixed(2),
      far: farPlane.toFixed(2)
    });
  };

  /**
   * Smooth camera animation with easing
   */
  const animateCamera = (targetCenter: THREE.Vector3, targetDistance: number) => {
    if (!cameraRef.current || !controlsRef.current) return;

    const startPos = cameraRef.current.position.clone();
    const startTarget = controlsRef.current.target.clone();
    const startTime = Date.now();
    const duration = 1000; // 1 second animation

    const easeInOutCubic = (t: number): number => {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    };

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeInOutCubic(progress);

      // Interpolate target (orbit controls focus point)
      controlsRef.current!.target.lerpVectors(
        startTarget,
        targetCenter,
        easedProgress
      );

      // Calculate camera position maintaining isometric angle
      const currentDistance = startPos.length() + (targetDistance - startPos.length()) * easedProgress;
      const offset = currentDistance * 0.57735;
      
      cameraRef.current!.position.lerpVectors(
        startPos,
        new THREE.Vector3(
          targetCenter.x + currentDistance,
          targetCenter.y + offset,
          targetCenter.z + offset
        ),
        easedProgress
      );

      cameraRef.current!.lookAt(controlsRef.current!.target);
      controlsRef.current!.update();

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  };

  /**
   * Dynamic lighting adjustment based on object position and size
   * NOTE: With MeshBasicMaterial, lighting is less critical but still helpful for depth perception
   */
  const updateLighting = (_center: THREE.Vector3, size: THREE.Vector3) => {
    if (!sceneRef.current) return;

    const maxDim = Math.max(size.x, size.y, size.z);
    const lightDistance = maxDim * 2;

    // Update existing lights to focus on object
    sceneRef.current.children.forEach(child => {
      if (child instanceof THREE.DirectionalLight) {
        // Reposition lights to illuminate from multiple angles
        const positions = [
          new THREE.Vector3(lightDistance, lightDistance, lightDistance),
          new THREE.Vector3(-lightDistance, -lightDistance, -lightDistance),
          new THREE.Vector3(0, lightDistance * 2, 0)
        ];
        
        positions.forEach((pos, idx) => {
          if (idx === 0) child.position.copy(pos);
        });
      } else if (child instanceof THREE.PointLight) {
        // Move point light to center of object
        child.position.set(_center.x, _center.y, _center.z);
      }
    });

    console.log('[Viewer] Lighting adjusted for object size:', maxDim.toFixed(2));
  };

  const fitCameraToModel = (animate: boolean = true) => {
    if (!currentModel?.statistics?.bounding_box || !cameraRef.current || !controlsRef.current) return;

    const bbox = currentModel.statistics.bounding_box;
    const dimensions = bbox.dimensions;

    // Calculate center
    const centerX = (bbox.min_point.x + bbox.max_point.x) / 2;
    const centerY = (bbox.min_point.y + bbox.max_point.y) / 2;
    const centerZ = (bbox.min_point.z + bbox.max_point.z) / 2;
    
    const center = new THREE.Vector3(centerX, centerY, centerZ);
    const size = new THREE.Vector3(dimensions.x, dimensions.y, dimensions.z);

    console.log('[Viewer] Fitting camera to model using bounding box statistics');
    
    // Use the robust framing system
    frameObject(center, size, animate);
  };

  const fitCameraToMeshes = (animate: boolean = true) => {
    if (!sceneRef.current || !meshesRef.current || meshesRef.current.size === 0) return;

    // Calculate bounding box from actual mesh vertices
    const bbox = new THREE.Box3();
    meshesRef.current.forEach((mesh) => {
      if (mesh.geometry && 'boundingBox' in mesh.geometry) {
        mesh.geometry.computeBoundingBox();
        if (mesh.geometry.boundingBox) {
          const meshBBox = mesh.geometry.boundingBox.clone();
          meshBBox.applyMatrix4(mesh.matrixWorld);
          bbox.union(meshBBox);
        }
      }
    });

    if (!bbox.isEmpty()) {
      const center = bbox.getCenter(new THREE.Vector3());
      const size = bbox.getSize(new THREE.Vector3());
      
      console.log('[Viewer] Fitting camera to mesh bounds:', {
        center: { x: center.x.toFixed(2), y: center.y.toFixed(2), z: center.z.toFixed(2) },
        size: { x: size.x.toFixed(2), y: size.y.toFixed(2), z: size.z.toFixed(2) }
      });

      // Frame the object with animation
      frameObject(center, size, animate);
    }
  };

  const loadPlaceholderGeometry = () => {
    if (!sceneRef.current || !currentModel) return;

    console.log('[Viewer] Creating FALLBACK placeholder geometry to verify rendering pipeline...');

    // ALWAYS create a test cube FIRST to verify Three.js is working
    const testCubeSize = 50;
    const testCubeGeometry = new THREE.BoxGeometry(testCubeSize, testCubeSize, testCubeSize);
    const testCubeMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ff00, // Bright green
      wireframe: true,
      transparent: true,
      opacity: 1.0
    });
    const testCube = new THREE.Mesh(testCubeGeometry, testCubeMaterial);
    testCube.position.set(0, 0, 0);
    
    // Add edges to test cube for better visibility
    const edges = new THREE.EdgesGeometry(testCubeGeometry);
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0x00ff00, linewidth: 2 });
    const wireframe = new THREE.LineSegments(edges, lineMaterial);
    testCube.add(wireframe);
    
    sceneRef.current.add(testCube);
    meshesRef.current.set('test_cube', testCube);
    
    console.log('[Viewer] TEST CUBE created - if you see this green wireframe box, Three.js is working!');

    // Also create bounding box placeholder if statistics available
    if (currentModel.statistics?.bounding_box) {
      const stats = currentModel.statistics;
      const geometry = new THREE.BoxGeometry(
        stats.bounding_box.dimensions.x || 50,
        stats.bounding_box.dimensions.z || 50,
        stats.bounding_box.dimensions.y || 50
      );

      // Use MeshBasicMaterial for guaranteed visibility without lighting
      const material = new THREE.MeshBasicMaterial({
        color: 0x00ffff, // Cyan - different from test cube
        wireframe: false,
        transparent: true,
        opacity: 0.7,
        side: THREE.DoubleSide
      });

      const mesh = new THREE.Mesh(geometry, material);
      // Center the placeholder
      mesh.position.set(
        stats.bounding_box.center.x || 0,
        stats.bounding_box.center.y || 0,
        stats.bounding_box.center.z || 0
      );
      
      // Add wireframe overlay
      const wireframeMaterial = new THREE.LineBasicMaterial({ 
        color: 0xffffff,
        transparent: true,
        opacity: 0.8
      });
      const wireframe = new THREE.LineSegments(
        new THREE.WireframeGeometry(geometry),
        wireframeMaterial
      );
      mesh.add(wireframe);
      
      sceneRef.current.add(mesh);
      meshesRef.current.set('placeholder', mesh);

      console.log('[Viewer] Bounding box placeholder created');
      
      // Frame camera on placeholder
      fitCameraToMeshes(false);
    } else {
      console.warn('[Viewer] No bounding box available - only showing test cube');
      // Position camera to see test cube at origin
      if (cameraRef.current) {
        cameraRef.current.position.set(100, 100, 100);
        cameraRef.current.lookAt(0, 0, 0);
      }
    }
  };

  /**
   * Manual view controls for ViewCube component
   */
  const handleResetView = () => {
    if (!cameraRef.current || !controlsRef.current) return;
    
    // Reset to isometric view at origin
    const startPos = cameraRef.current.position.clone();
    const startTarget = controlsRef.current.target.clone();
    const targetPos = new THREE.Vector3(100, 100, 100);
    const targetCenter = new THREE.Vector3(0, 0, 0);
    
    // Simple lerp for smooth reset
    const startTime = Date.now();
    const duration = 800;
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const t = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
      
      controlsRef.current!.target.lerpVectors(startTarget, targetCenter, t);
      cameraRef.current!.position.lerpVectors(startPos, targetPos, t);
      cameraRef.current!.lookAt(controlsRef.current!.target);
      controlsRef.current!.update();
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    animate();
    console.log('[Viewer] View reset to default');
  };

  const handleFitModel = () => {
    console.log('[Viewer] Manual fit model triggered');
    // Try to fit to meshes first, then fallback to bounding box
    if (meshesRef.current && meshesRef.current.size > 0) {
      fitCameraToMeshes(true);
    } else if (currentModel?.statistics?.bounding_box) {
      fitCameraToModel(true);
    }
  };

  return (
    <div className="w-full h-full relative">
      <div ref={containerRef} className="w-full h-full" />

      {/* Coordinate System Indicator */}
      {currentModel && <CoordinateIndicator />}

      {/* View Cube Navigation Controls */}
      {currentModel && cameraRef.current && controlsRef.current && (
        <ViewCube
          camera={cameraRef.current}
          controls={controlsRef.current}
          onResetView={handleResetView}
          onFitModel={handleFitModel}
        />
      )}

      {!currentModel && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center text-gray-500 bg-gray-900 bg-opacity-75 p-6 rounded-lg">
            <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <p className="text-lg font-medium">3D Viewer Canvas</p>
            <p className="text-sm mt-2">Upload a STEP file to view 3D model</p>
          </div>
        </div>
      )}

      {currentModel && (
        <>
          <div className="absolute top-4 left-4 bg-gray-800 bg-opacity-75 backdrop-blur px-3 py-2 rounded text-sm">
            <div className="font-semibold">{currentModel.filename}</div>
            <div className="text-xs text-gray-400">
              {(currentModel.file_size / 1024 / 1024).toFixed(2)} MB
            </div>
          </div>
          
          {/* Debug Info - Shows mesh count and camera position */}
          <div className="absolute bottom-4 left-4 bg-gray-800 bg-opacity-75 backdrop-blur px-3 py-2 rounded text-xs text-green-400">
            <div className="font-mono">
              Meshes: {meshesRef.current?.size || 0} | 
              Camera: ({cameraRef.current?.position.x?.toFixed(1) || '---'}, {cameraRef.current?.position.y?.toFixed(1) || '---'}, {cameraRef.current?.position.z?.toFixed(1) || '---'})
            </div>
          </div>

          {/* Debug Button - Force reload meshes */}
          <button
            onClick={() => {
              console.log('[DEBUG] Manual mesh reload triggered');
              console.log('[DEBUG] currentModel:', currentModel);
              console.log('[DEBUG] scene exists:', !!sceneRef.current);
              console.log('[DEBUG] meshesRef size:', meshesRef.current?.size);
              if (sceneRef.current) {
                console.log('[DEBUG] Scene children:', sceneRef.current.children.length);
                const meshesInScene = sceneRef.current.children.filter(c => c instanceof THREE.Mesh);
                console.log('[DEBUG] Actual meshes in scene:', meshesInScene.length);
              }
              loadMeshData();
            }}
            className="absolute bottom-4 right-4 bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-xs font-bold"
          >
            DEBUG: Reload Meshes
          </button>
        </>
      )}
    </div>
  );
};

export default Viewer3D;
