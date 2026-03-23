import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface CoordinateIndicatorProps {
  // No props needed - component is self-contained
}

const CoordinateIndicator: React.FC<CoordinateIndicatorProps> = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const groupRef = useRef<THREE.Group | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Scene setup - Pure black background
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000); // Pure black
    sceneRef.current = scene;

    // Camera setup
    const size = 120; // Small indicator size
    const camera = new THREE.PerspectiveCamera(50, size / size, 0.1, 1000);
    camera.position.set(3, 2, 3);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(size, size);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Create coordinate axes with labels
    const group = new THREE.Group();

    // Axes lines
    const axisLength = 1.5;
    const lineGeometry = new THREE.BufferGeometry();
    
    // X-axis (Red) - Right direction
    const xVertices = new Float32Array([0, 0, 0, axisLength, 0, 0]);
    lineGeometry.setAttribute('position', new THREE.BufferAttribute(xVertices, 3));
    const xLine = new THREE.Line(lineGeometry, new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 2 }));
    group.add(xLine);

    // Y-axis (Green) - Up direction
    const yVertices = new Float32Array([0, 0, 0, 0, axisLength, 0]);
    const yLine = new THREE.Line(lineGeometry.clone(), new THREE.LineBasicMaterial({ color: 0x00ff00, linewidth: 2 }));
    yLine.geometry.setAttribute('position', new THREE.BufferAttribute(yVertices, 3));
    group.add(yLine);

    // Z-axis (Blue) - Forward direction
    const zVertices = new Float32Array([0, 0, 0, 0, 0, axisLength]);
    const zLine = new THREE.Line(lineGeometry.clone(), new THREE.LineBasicMaterial({ color: 0x0000ff, linewidth: 2 }));
    zLine.geometry.setAttribute('position', new THREE.BufferAttribute(zVertices, 3));
    group.add(zLine);

    // Axis labels
    const createLabel = (text: string, color: string, position: [number, number, number]) => {
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      if (!context) return null;
      
      canvas.width = 64;
      canvas.height = 64;
      context.font = 'Bold 40px Arial';
      context.fillStyle = color;
      context.textAlign = 'center';
      context.textBaseline = 'middle';
      context.fillText(text, 32, 32);
      
      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
      const sprite = new THREE.Sprite(material);
      sprite.scale.set(0.5, 0.5, 1);
      sprite.position.set(...position);
      return sprite;
    };

    const labelX = createLabel('X', '#ff0000', [axisLength + 0.3, 0, 0]);
    const labelY = createLabel('Y', '#00ff00', [0, axisLength + 0.3, 0]);
    const labelZ = createLabel('Z', '#0000ff', [0, 0, axisLength + 0.3]);
    
    if (labelX) group.add(labelX);
    if (labelY) group.add(labelY);
    if (labelZ) group.add(labelZ);

    // Grid helper for reference
    const gridHelper = new THREE.GridHelper(2, 4, 0x4b5563, 0x374151);
    gridHelper.rotation.x = Math.PI / 2;
    gridHelper.position.z = -axisLength / 2;
    group.add(gridHelper);

    scene.add(group);
    groupRef.current = group;

    // Animation loop
    let animationId: number;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    // Cleanup
    return () => {
      if (animationId) cancelAnimationFrame(animationId);
      if (rendererRef.current && containerRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement);
      }
      if (groupRef.current) {
        scene.remove(groupRef.current);
      }
      groupRef.current = null;
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
    };
  }, []);

  return (
    <div className="absolute top-4 right-4 flex flex-col items-end gap-2">
      {/* Coordinate System Indicator - Small & Minimal */}
      <div 
        ref={containerRef}
        className="border-2 border-gray-600 rounded-lg shadow-xl overflow-hidden"
        style={{ width: 80, height: 80 }}
        title="Coordinate System (X=Red, Y=Green, Z=Blue)"
      />
      
      {/* Mouse Controls Guide - Simple */}
      <div className="bg-gray-800 bg-opacity-95 backdrop-blur px-3 py-2 rounded text-xs text-white shadow-lg">
        <div className="font-bold mb-1 text-yellow-400">🖱️ Controls</div>
        <div className="space-y-0.5 text-gray-300">
          <div>Scroll: Zoom</div>
          <div>Left: Rotate</div>
          <div>Right: Pan</div>
        </div>
      </div>
    </div>
  );
};

export default CoordinateIndicator;
