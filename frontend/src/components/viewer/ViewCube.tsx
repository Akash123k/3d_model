import React from 'react';
import * as THREE from 'three';

interface ViewCubeProps {
  camera: THREE.PerspectiveCamera | null;
  controls: any | null;
  onResetView: () => void;
  onFitModel: () => void;
}

const ViewCube: React.FC<ViewCubeProps> = ({ 
  camera, 
  controls, 
  onResetView,
  onFitModel 
}) => {
  
  // Get current view direction label
  const getViewLabel = () => {
    if (!camera) return '';
    
    const dir = new THREE.Vector3();
    camera.getWorldDirection(dir);
    
    // Determine primary view direction
    const absDir = {
      x: Math.abs(dir.x),
      y: Math.abs(dir.y),
      z: Math.abs(dir.z)
    };
    
    let primary = '';
    let vertical = '';
    
    // Find dominant axis
    if (absDir.x > absDir.y && absDir.x > absDir.z) {
      primary = dir.x > 0 ? 'RIGHT' : 'LEFT';
    } else if (absDir.y > absDir.x && absDir.y > absDir.z) {
      primary = dir.y > 0 ? 'TOP' : 'BOTTOM';
    } else {
      primary = dir.z > 0 ? 'FRONT' : 'BACK';
    }
    
    // Add vertical angle
    if (dir.y > 0.3) vertical = ' (Top)';
    else if (dir.y < -0.3) vertical = ' (Bottom)';
    
    return primary + vertical;
  };

  const handleFront = () => {
    if (!camera || !controls) return;
    const target = controls.target.clone();
    const distance = camera.position.distanceTo(target);
    camera.position.set(target.x, target.y, target.z + distance);
    camera.lookAt(target);
    controls.target.copy(target);
    controls.update();
  };

  const handleBack = () => {
    if (!camera || !controls) return;
    const target = controls.target.clone();
    const distance = camera.position.distanceTo(target);
    camera.position.set(target.x, target.y, target.z - distance);
    camera.lookAt(target);
    controls.target.copy(target);
    controls.update();
  };

  const handleTop = () => {
    if (!camera || !controls) return;
    const target = controls.target.clone();
    const distance = camera.position.distanceTo(target);
    camera.position.set(target.x, target.y + distance, target.z);
    camera.lookAt(target);
    controls.target.copy(target);
    controls.update();
  };

  const handleBottom = () => {
    if (!camera || !controls) return;
    const target = controls.target.clone();
    const distance = camera.position.distanceTo(target);
    camera.position.set(target.x, target.y - distance, target.z);
    camera.lookAt(target);
    controls.target.copy(target);
    controls.update();
  };

  const handleLeft = () => {
    if (!camera || !controls) return;
    const target = controls.target.clone();
    const distance = camera.position.distanceTo(target);
    camera.position.set(target.x - distance, target.y, target.z);
    camera.lookAt(target);
    controls.target.copy(target);
    controls.update();
  };

  const handleRight = () => {
    if (!camera || !controls) return;
    const target = controls.target.clone();
    const distance = camera.position.distanceTo(target);
    camera.position.set(target.x + distance, target.y, target.z);
    camera.lookAt(target);
    controls.target.copy(target);
    controls.update();
  };

  const handleIso = () => {
    if (!camera || !controls) return;
    const target = controls.target.clone();
    const distance = camera.position.distanceTo(target);
    const offset = distance * 0.57735;
    camera.position.set(target.x + distance, target.y + offset, target.z + offset);
    camera.lookAt(target);
    controls.target.copy(target);
    controls.update();
  };

  return (
    <div className="absolute bottom-4 right-4 bg-gray-800 bg-opacity-90 backdrop-blur rounded-lg p-3 shadow-xl border border-gray-700">
      {/* View Label */}
      <div className="text-center mb-2 pb-2 border-b border-gray-700">
        <div className="text-xs text-gray-400 uppercase font-semibold">Current View</div>
        <div className="text-sm font-bold text-blue-400">{getViewLabel() || 'Custom'}</div>
      </div>

      {/* View Cube Navigation */}
      <div className="grid grid-cols-3 gap-1 mb-2">
        {/* Top row */}
        <button
          onClick={handleTop}
          className="w-10 h-10 bg-gray-700 hover:bg-blue-600 rounded flex items-center justify-center transition"
          title="Top View"
        >
          <span className="text-white font-bold text-xs">TOP</span>
        </button>
        <button
          onClick={handleIso}
          className="w-10 h-10 bg-blue-700 hover:bg-blue-500 rounded flex items-center justify-center transition"
          title="Isometric View"
        >
          <span className="text-white font-bold text-xs">ISO</span>
        </button>
        <button
          onClick={handleFront}
          className="w-10 h-10 bg-gray-700 hover:bg-blue-600 rounded flex items-center justify-center transition"
          title="Front View"
        >
          <span className="text-white font-bold text-xs">FRONT</span>
        </button>

        {/* Middle row */}
        <button
          onClick={handleLeft}
          className="w-10 h-10 bg-gray-700 hover:bg-blue-600 rounded flex items-center justify-center transition"
          title="Left View"
        >
          <span className="text-white font-bold text-xs">L</span>
        </button>
        <div className="w-10 h-10 bg-gray-900 rounded flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-gray-600 rounded opacity-50"></div>
        </div>
        <button
          onClick={handleRight}
          className="w-10 h-10 bg-gray-700 hover:bg-blue-600 rounded flex items-center justify-center transition"
          title="Right View"
        >
          <span className="text-white font-bold text-xs">R</span>
        </button>

        {/* Bottom row */}
        <button
          onClick={handleBottom}
          className="w-10 h-10 bg-gray-700 hover:bg-blue-600 rounded flex items-center justify-center transition"
          title="Bottom View"
        >
          <span className="text-white font-bold text-xs">BOT</span>
        </button>
        <button
          onClick={handleBack}
          className="w-10 h-10 bg-gray-700 hover:bg-blue-600 rounded flex items-center justify-center transition"
          title="Back View"
        >
          <span className="text-white font-bold text-xs">BACK</span>
        </button>
        <button
          onClick={onResetView}
          className="w-10 h-10 bg-green-700 hover:bg-green-600 rounded flex items-center justify-center transition"
          title="Reset View"
        >
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-1 mt-2 pt-2 border-t border-gray-700">
        <button
          onClick={onFitModel}
          className="flex-1 px-2 py-1.5 bg-purple-700 hover:bg-purple-600 rounded text-xs text-white transition"
          title="Fit model to screen"
        >
          📐 Fit Model
        </button>
        <button
          onClick={onResetView}
          className="flex-1 px-2 py-1.5 bg-orange-700 hover:bg-orange-600 rounded text-xs text-white transition"
          title="Reset camera position"
        >
          🔄 Reset
        </button>
      </div>

      {/* Instructions */}
      <div className="mt-2 pt-2 border-t border-gray-700 text-xs text-gray-500 text-center">
        <div>🖱️ Scroll: Zoom In/Out</div>
        <div>🖱️ Drag: Rotate View</div>
        <div>🖱️ Right-drag: Pan</div>
      </div>
    </div>
  );
};

export default ViewCube;
