import React from 'react';
import GeometryExplorer from '../components/geometry/GeometryExplorer';

const BRepGeometryPage: React.FC = () => {
  return (
    <div className="h-screen bg-gray-900 text-white overflow-auto">
      <div className="container mx-auto px-4 py-6">
        <h1 className="text-3xl font-bold mb-6">B-Rep Geometry Explorer</h1>
        <div className="bg-gray-800 rounded-lg shadow-lg">
          <GeometryExplorer />
        </div>
      </div>
    </div>
  );
};

export default BRepGeometryPage;
