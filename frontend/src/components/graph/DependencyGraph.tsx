import React, { useEffect, useRef, memo, useState, useCallback } from 'react';
import { useModelStore } from '../../store';

const DependencyGraph: React.FC = memo(() => {
  const { currentModel } = useModelStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Use refs for zoom state to avoid React re-renders on every frame
  const zoomStateRef = useRef({
    scale: 1,
    offsetX: 0,
    offsetY: 0
  });
  
  // Only for UI updates (zoom indicator)
  const [zoomDisplay, setZoomDisplay] = useState(100);
  
  const [isDragging, setIsDragging] = useState(false);
  const [lastMousePos, setLastMousePos] = useState({ x: 0, y: 0 });
  const animationFrameRef = useRef<number>();

  // Zoom settings
  const MIN_ZOOM = 0.1;
  const MAX_ZOOM = 5;
  const ZOOM_SPEED = 0.002;
  
  // Performance optimization: LOD thresholds
  const LOD_THRESHOLDS = {
    HIDE_LABELS: 0.3,      // Show labels only when zoomed in enough
    SHOW_MEDIUM: 0.8,      // Show medium detail level
    SHOW_HIGH: 1.5,        // Show high detail level
    SHOW_EXTRA: 3.0        // Show extra metadata
  };

  // Optimized draw function - uses refs instead of state
  const drawGraph = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, width, height);

    // Apply zoom and pan transformations
    ctx.save();
    ctx.translate(zoomStateRef.current.offsetX, zoomStateRef.current.offsetY);
    ctx.scale(zoomStateRef.current.scale, zoomStateRef.current.scale);

    const graphData = currentModel?.dependency_graph;
    if (!graphData) {
      ctx.restore();
      return;
    }

    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];

    // PERFORMANCE: Render all nodes efficiently
    const displayNodes = nodes;
    const displayNodeIds = new Set(displayNodes.map((n: any) => n.id));
    
    // Only render edges between visible nodes
    const filteredEdges = edges.filter((e: any) => 
      displayNodeIds.has(e.source) && displayNodeIds.has(e.target)
    );

    // LOD based on current zoom
    const currentZoom = zoomStateRef.current.scale;
    const showLabels = currentZoom > LOD_THRESHOLDS.HIDE_LABELS;
    const showMediumDetail = currentZoom > LOD_THRESHOLDS.SHOW_MEDIUM;
    const showHighDetail = currentZoom > LOD_THRESHOLDS.SHOW_HIGH;
    const showExtraDetail = currentZoom > LOD_THRESHOLDS.SHOW_EXTRA;

    // Pre-calculate node positions (cached layout)
    const centerX = width / 2;
    const centerY = height / 2;
    const nodePositions: Record<string, { x: number; y: number }> = {};
    
    // Group nodes by type
    const typeGroups: Record<string, any[]> = {};
    displayNodes.forEach((node: any) => {
      const type = node.type || 'OTHER';
      if (!typeGroups[type]) typeGroups[type] = [];
      typeGroups[type].push(node);
    });

    // Arrange groups in sectors
    let currentAngle = 0;
    const groupAngles = Object.keys(typeGroups).map(key => ({
      type: key,
      count: typeGroups[key].length,
      startAngle: 0,
      endAngle: 0
    }));
    
    const totalNodes = displayNodes.length;
    groupAngles.forEach(group => {
      const angleSpan = (group.count / totalNodes) * 2 * Math.PI;
      group.startAngle = currentAngle;
      group.endAngle = currentAngle + angleSpan;
      currentAngle += angleSpan;
    });

    // Position nodes within groups
    groupAngles.forEach(group => {
      const nodesInGroup = typeGroups[group.type];
      const anglePerNode = (group.endAngle - group.startAngle) / Math.max(nodesInGroup.length, 1);
      
      nodesInGroup.forEach((node: any, idx: number) => {
        const angle = group.startAngle + anglePerNode * idx;
        const radius = Math.min(width, height) * 0.35;
        nodePositions[node.id] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle)
        };
      });
    });

    // Draw edges with LOD
    filteredEdges.forEach((edge: any) => {
      const source = nodePositions[edge.source];
      const target = nodePositions[edge.target];
      
      if (source && target) {
        ctx.strokeStyle = '#4b5563';
        ctx.lineWidth = showMediumDetail ? 1 : 0.5;
        ctx.globalAlpha = showMediumDetail ? 0.6 : 0.3;
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
        ctx.globalAlpha = 1.0;
      }
    });

    // Draw nodes with LOD
    displayNodes.forEach((node: any) => {
      const pos = nodePositions[node.id];
      if (!pos) return;

      let fillColor = '#6b7280';
      let baseRadius = 6;
      
      const nodeType = node.type || '';
      if (nodeType.includes('SOLID') || nodeType.includes('MANIFOLD')) {
        fillColor = '#3b82f6';
        baseRadius = 10;
      } else if (nodeType.includes('FACE') || nodeType.includes('ADVANCED')) {
        fillColor = '#8b5cf6';
        baseRadius = 8;
      } else if (nodeType.includes('EDGE') || nodeType.includes('CURVE')) {
        fillColor = '#f59e0b';
        baseRadius = 5;
      } else if (nodeType.includes('VERTEX') || nodeType.includes('POINT')) {
        fillColor = '#ec4899';
        baseRadius = 4;
      } else if (nodeType.includes('SURFACE') || nodeType.includes('PLANE')) {
        fillColor = '#10b981';
        baseRadius = 7;
      }
      
      const importance = node.properties?.importance || 0;
      const radius = baseRadius + Math.min(importance * 2, 8);

      ctx.fillStyle = fillColor;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
      ctx.fill();
      
      // Node border based on zoom
      if (showHighDetail && importance > 5) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Labels with LOD
      if (showLabels && radius >= 6) {
        ctx.fillStyle = '#ffffff';
        const fontSize = showHighDetail ? 11 : 9;
        ctx.font = `${fontSize}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        if (showExtraDetail) {
          ctx.fillText(node.label || node.id, pos.x, pos.y - radius - 6);
          if (node.properties?.importance) {
            ctx.fillStyle = '#9ca3af';
            ctx.font = '8px sans-serif';
            ctx.fillText(`Imp: ${importance}`, pos.x, pos.y + radius + 10);
          }
        } else {
          const shortLabel = node.label?.split('_')[0] || node.id;
          ctx.fillText(shortLabel, pos.x, pos.y - radius - 4);
        }
      }
    });

    ctx.restore();

    // Stats (always visible)
    ctx.fillStyle = '#9ca3af';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`Nodes: ${displayNodes.length}`, 10, 20);
    ctx.fillText(`Edges: ${filteredEdges.length}`, 10, 35);
    ctx.fillText(`Zoom: ${(currentZoom * 100).toFixed(0)}%`, 10, 50);
  }, [currentModel]);

  // Initial draw when model loads
  useEffect(() => {
    if (currentModel && currentModel.dependency_graph) {
      drawGraph();
    }
  }, [currentModel, drawGraph]);

  // Mouse wheel zoom handler - uses refs for instant updates
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Exponential zoom for smooth Google Maps feel
    const zoomFactor = Math.exp(-e.deltaY * ZOOM_SPEED);
    const newScale = Math.min(Math.max(zoomStateRef.current.scale * zoomFactor, MIN_ZOOM), MAX_ZOOM);

    // Zoom toward mouse position
    const scaleRatio = newScale / zoomStateRef.current.scale;
    const newX = mouseX - (mouseX - zoomStateRef.current.offsetX) * scaleRatio;
    const newY = mouseY - (mouseY - zoomStateRef.current.offsetY) * scaleRatio;

    // Update ref directly (no React re-render)
    zoomStateRef.current = {
      scale: newScale,
      offsetX: newX,
      offsetY: newY
    };

    // Update display state (throttled by React)
    setZoomDisplay(newScale * 100);

    // Redraw immediately using requestAnimationFrame for smooth 60fps
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    animationFrameRef.current = requestAnimationFrame(drawGraph);
  }, [drawGraph]);

  // Pan handler
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    setLastMousePos({ x: e.clientX, y: e.clientY });
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return;

    const dx = e.clientX - lastMousePos.x;
    const dy = e.clientY - lastMousePos.y;

    // Update ref directly
    zoomStateRef.current = {
      ...zoomStateRef.current,
      offsetX: zoomStateRef.current.offsetX + dx,
      offsetY: zoomStateRef.current.offsetY + dy
    };

    setLastMousePos({ x: e.clientX, y: e.clientY });

    // Redraw
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    animationFrameRef.current = requestAnimationFrame(drawGraph);
  }, [isDragging, lastMousePos, drawGraph]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Touch support
  const lastTouchDistance = useRef<number>(0);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      const touch1 = e.touches[0];
      const touch2 = e.touches[1];
      const distance = Math.sqrt(
        Math.pow(touch2.clientX - touch1.clientX, 2) +
        Math.pow(touch2.clientY - touch1.clientY, 2)
      );
      lastTouchDistance.current = distance;
    }
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      e.preventDefault();
      
      const touch1 = e.touches[0];
      const touch2 = e.touches[1];
      const distance = Math.sqrt(
        Math.pow(touch2.clientX - touch1.clientX, 2) +
        Math.pow(touch2.clientY - touch1.clientY, 2)
      );

      const zoomFactor = distance / lastTouchDistance.current;
      const newScale = Math.min(Math.max(zoomStateRef.current.scale * zoomFactor, MIN_ZOOM), MAX_ZOOM);

      zoomStateRef.current = {
        ...zoomStateRef.current,
        scale: newScale
      };

      setZoomDisplay(newScale * 100);
      lastTouchDistance.current = distance;

      // Redraw
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      animationFrameRef.current = requestAnimationFrame(drawGraph);
    }
  }, [drawGraph]);

  if (!currentModel || !currentModel.dependency_graph) {
    return (
      <div className="p-4">
        <h3 className="font-bold mb-2 text-lg">Dependency Graph</h3>
        <p className="text-sm text-gray-400">No dependency data available</p>
      </div>
    );
  }

  return (
    <div className="p-4 h-full relative">
      <h3 className="font-bold mb-2 text-lg">Dependency Graph</h3>
      <div className="text-xs text-gray-400 mb-2">
        Entity relationships visualization - Use mouse wheel to zoom, click and drag to pan
      </div>

      {/* Zoom Level Indicator */}
      <div className="absolute bottom-4 right-4 bg-gray-700 text-white px-3 py-1 rounded-lg text-sm shadow-lg">
        {zoomDisplay.toFixed(0)}%
      </div>

      <canvas
        ref={canvasRef}
        className="w-full h-full bg-gray-800 rounded cursor-move"
        style={{ minHeight: '200px' }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
      />
    </div>
  );
});

export default DependencyGraph;
